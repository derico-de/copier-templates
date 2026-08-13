"""Jinja2 extensions for the upgrade_step template."""

import sys
import tomllib
from pathlib import Path

from copier_template_extensions import ContextHook

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.hooks.legacy_context import find_legacy_addon_context  # noqa: E402
from shared.utils.xml_updater import MetadataXMLUpdater  # noqa: E402


class AddonContextHook(ContextHook):
    """Auto-fill package info from parent addon and read current profile version."""

    def hook(self, context):
        dest = Path(context.get("_copier_conf", {}).get("dst_path", "."))
        if not dest.is_absolute():
            dest = Path.cwd() / dest

        package_name = None
        package_folder = None

        pyproject_path = dest / "pyproject.toml"
        if pyproject_path.exists():
            try:
                with open(pyproject_path, "rb") as f:
                    doc = tomllib.load(f)
                settings = (
                    doc.get("tool", {})
                    .get("plone", {})
                    .get("backend_addon", {})
                    .get("settings", {})
                )
                if settings:
                    package_name = settings.get("package_name")
                    package_folder = settings.get("package_folder")
            except (tomllib.TOMLDecodeError, OSError):
                pass

        # Fallback: try legacy detection
        if not package_name:
            legacy = find_legacy_addon_context(dest)
            if legacy:
                package_name = legacy.get("package_name")
                package_folder = legacy.get("package_folder")

        if package_name:
            context["package_name"] = package_name
        if package_folder:
            context["package_folder"] = package_folder

        # Read current profile version from metadata.xml
        if not package_folder and package_name:
            package_folder = package_name.replace(".", "/")
        if package_folder:
            metadata_path = (
                dest
                / f"src/{package_folder}/profiles/default/metadata.xml"
            )
            updater = MetadataXMLUpdater(metadata_path)
            version = updater.get_version()
            if version:
                context["current_profile_version"] = version
