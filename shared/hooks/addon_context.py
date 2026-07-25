#!/usr/bin/env python3
"""Detect parent addon context for subtemplates."""
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from exceptions import AddonContextError
from hooks.legacy_context import find_legacy_addon_context


def find_addon_context(start_path: Path | None = None) -> dict[str, Any] | None:
    """
    Find parent addon context by looking for:
    1. .copier-answers.backend-addon.*.yml file in current directory
    2. [tool.plone.backend_addon.settings] section in pyproject.toml
    3. Legacy files: bobtemplate.cfg, setup.py, or older pyproject.toml

    Args:
        start_path: Directory to search in (defaults to current directory)

    Returns:
        Dictionary with addon settings or None if not found
    """
    start_path = start_path or Path.cwd()

    # Check for copier answers file pattern
    for f in start_path.glob(".copier-answers.backend-addon.*.yml"):
        # Found answers file, read pyproject.toml for settings
        pyproject_path = start_path / "pyproject.toml"
        if pyproject_path.exists():
            settings = _read_addon_settings(pyproject_path)
            if settings:
                return settings

    # Also check for the default copier answers file
    default_answers = start_path / ".copier-answers.yml"
    if default_answers.exists():
        pyproject_path = start_path / "pyproject.toml"
        if pyproject_path.exists():
            settings = _read_addon_settings(pyproject_path)
            if settings:
                return settings

    # Check pyproject.toml directly
    pyproject_path = start_path / "pyproject.toml"
    if pyproject_path.exists():
        settings = _read_addon_settings(pyproject_path)
        if settings:
            return settings

    # Fallback: try legacy detection (bobtemplate.cfg, setup.py, older pyproject.toml)
    legacy = find_legacy_addon_context(start_path)
    if legacy:
        source = legacy.pop("_legacy_source", "unknown")
        print(f"Detected legacy addon package from {source}.")
        print("Consider running the backend_addon template to modernize this package.")
        return legacy

    return None


def _read_addon_settings(pyproject_path: Path) -> dict[str, Any] | None:
    """
    Read addon settings from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Dictionary with addon settings or None if not found
    """
    try:
        with open(pyproject_path, "rb") as f:
            doc = tomllib.load(f)

        settings = doc.get("tool", {}).get("plone", {}).get("backend_addon", {}).get("settings", {})
        if settings:
            return dict(settings)
    except (tomllib.TOMLDecodeError, OSError):
        pass

    return None


def require_addon_context(start_path: Path | None = None) -> dict[str, Any]:
    """
    Raise AddonContextError if no parent addon found.

    Args:
        start_path: Directory to search in (defaults to current directory)

    Returns:
        Dictionary with addon settings

    Raises:
        AddonContextError: If no parent addon is detected
    """
    context = find_addon_context(start_path)
    if not context:
        raise AddonContextError(
            "No parent addon detected. This template must be run inside an existing backend_addon."
        )
    return context


@dataclass
class AddonContext:
    """Resolved addon context for use in post_copy hooks.

    Knows the addon's package_name/package_folder (whether discovered from
    a modern pyproject.toml or a legacy bobtemplate.cfg/setup.py), the
    resolved destination directory, and whether a pyproject.toml exists
    that we can write addon-settings into.
    """

    dest: Path
    package_name: str
    package_folder: str
    is_legacy: bool
    source: str
    pyproject_path: Optional[Path]

    def register_subtemplate(self, subtemplate_type: str, name: str) -> bool:
        """Register a subtemplate registration in addon metadata.

        Behavior depends on what configuration files are present:

        * pyproject.toml present: writes to
          ``[tool.plone.backend_addon.settings.subtemplates]`` (creating
          the section if missing).
        * pyproject.toml absent but bobtemplate.cfg present: writes to a
          ``[subtemplates]`` section in bobtemplate.cfg, matching the
          legacy bobtemplates.plone storage location.
        * neither present (e.g. setup.py-only): graceful no-op with note.

        Returns:
            True if registered (in pyproject.toml or bobtemplate.cfg),
            False if skipped because no suitable file was found.
        """
        if self.pyproject_path and self.pyproject_path.exists():
            from utils.pyproject_updater import PyprojectUpdater

            updater = PyprojectUpdater(self.pyproject_path)
            updater.register_subtemplate(subtemplate_type, name)
            updater.save()
            return True

        bobtemplate_cfg = self.dest / "bobtemplate.cfg"
        if bobtemplate_cfg.exists():
            from utils.bobtemplate_cfg import register_subtemplate as _reg

            added = _reg(bobtemplate_cfg, subtemplate_type, name)
            if added:
                print(
                    f"Registered {subtemplate_type}={name!r} in "
                    f"bobtemplate.cfg [subtemplates] section."
                )
            return True

        print(
            f"Note: Skipping subtemplate registration of {name!r} "
            f"(no pyproject.toml or bobtemplate.cfg; source: {self.source})."
        )
        return False

    def add_profile_dependency(self, dependency: str) -> None:
        """Idempotently declare ``dependency`` in profiles/default/metadata.xml."""
        if not self.package_folder:
            return
        from utils.xml_updater import MetadataXMLUpdater

        metadata_path = (
            self.dest / f"src/{self.package_folder}/profiles/default/metadata.xml"
        )
        if MetadataXMLUpdater(metadata_path).add_dependency(dependency):
            print(f"Added {dependency} dependency to metadata.xml.")
        else:
            print(f"{dependency} already in metadata.xml.")

    def browser_layer(self) -> Optional[str]:
        """Return the addon's browser-layer interface dotted path, or None.

        Uses the backend_addon naming convention
        (``I<TitleCasedPackageName>Layer`` in ``interfaces.py``) and only
        returns a path if that class actually exists in the package's
        ``interfaces.py``, so registrations never reference a missing layer.
        """
        if not self.package_name or not self.package_folder:
            return None
        klass = (
            "I"
            + self.package_name.replace(".", " ").replace("_", " ")
            .title()
            .replace(" ", "")
            + "Layer"
        )
        interfaces_py = self.dest / f"src/{self.package_folder}/interfaces.py"
        try:
            if klass not in interfaces_py.read_text():
                return None
        except OSError:
            return None
        return f"{self.package_name}.interfaces.{klass}"


def _looks_like_addon_root(path: Path) -> bool:
    """Path contains addon markers (pyproject.toml, setup.py, bobtemplate.cfg)."""
    return (
        (path / "pyproject.toml").exists()
        or (path / "setup.py").exists()
        or (path / "bobtemplate.cfg").exists()
    )


def resolve_post_copy_context(dest_path: str | Path) -> Optional[AddonContext]:
    """Resolve addon context for a post_copy hook.

    Picks the right destination directory (cwd if it looks like an addon root,
    otherwise the given dest_path) and detects modern (pyproject.toml with
    [tool.plone.backend_addon.settings]) or legacy (bobtemplate.cfg, setup.py,
    plain pyproject.toml) addons.

    Returns:
        AddonContext if a parent addon is found, None otherwise.
    """
    cwd = Path.cwd()
    dest = Path(dest_path)

    if _looks_like_addon_root(cwd):
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    pyproject_path = dest / "pyproject.toml"

    if pyproject_path.exists():
        settings = _read_addon_settings(pyproject_path)
        if settings:
            package_name = settings.get("package_name", "")
            package_folder = settings.get("package_folder") or (
                package_name.replace(".", "/") if package_name else ""
            )
            if package_name or package_folder:
                return AddonContext(
                    dest=dest,
                    package_name=package_name,
                    package_folder=package_folder,
                    is_legacy=False,
                    source="pyproject.toml",
                    pyproject_path=pyproject_path,
                )

    legacy = find_legacy_addon_context(dest)
    if legacy:
        legacy_name = legacy.get("package_name", "")
        legacy_folder = legacy.get("package_folder") or (
            legacy_name.replace(".", "/") if legacy_name else ""
        )
        return AddonContext(
            dest=dest,
            package_name=legacy_name,
            package_folder=legacy_folder,
            is_legacy=True,
            source=legacy.get("_legacy_source", "unknown"),
            pyproject_path=pyproject_path if pyproject_path.exists() else None,
        )

    return None


def get_package_folder(package_name: str) -> str:
    """
    Convert package name to folder path.

    Args:
        package_name: Python package name (e.g., 'collective.mypackage')

    Returns:
        Folder path (e.g., 'collective/mypackage')
    """
    return package_name.replace(".", "/")


if __name__ == "__main__":
    # Used as pre-copy hook by subtemplates
    try:
        require_addon_context()
    except AddonContextError as e:
        print("\n" + "=" * 60)
        print("ERROR: No parent addon detected!")
        print("=" * 60)
        print(f"\n{e}")
        print("\nFirst create an addon with:")
        print("  copier copy ~/.copier-templates/plone-copier-templates/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory.")
        print("=" * 60 + "\n")
        sys.exit(1)
