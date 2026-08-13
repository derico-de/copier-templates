"""Jinja2 extensions for the zope-setup template."""

import sys
import tomllib
from pathlib import Path

from copier_template_extensions import ContextHook
from jinja2.ext import Extension

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.hooks.legacy_context import find_legacy_addon_context  # noqa: E402
from shared.utils.jinja_filters import python_string, toml_string  # noqa: E402
from shared.utils.plone_versions import fetch_plone_versions, get_major_minor_versions  # noqa: E402


class SharedFiltersExtension(Extension):
    """Register serialization filters used by generated files."""

    def __init__(self, environment):
        super().__init__(environment)
        environment.filters["toml_string"] = toml_string
        environment.filters["python_string"] = python_string


class PloneVersionsHook(ContextHook):
    """Populate Plone version lists from PyPI for use in copier.yml choices."""

    def hook(self, context):
        all_versions = fetch_plone_versions()
        context["plone_versions_full"] = all_versions
        context["plone_versions_minor"] = get_major_minor_versions(all_versions)


class AddonContextHook(ContextHook):
    """Read addon settings from pyproject.toml or legacy files in the destination directory."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", ""))
        addon_context = self._read_context(dst_path)
        context["addon_context"] = addon_context
        context["plone_version_full_default"] = self._derive_full_version(
            addon_context, context.get("plone_versions_full") or []
        )

    @staticmethod
    def _derive_full_version(addon_context, all_versions):
        """Pick a full version matching the addon's minor series, else latest."""
        default_full = all_versions[0] if all_versions else ""
        minor = (addon_context or {}).get("plone_version")
        if minor:
            match = next(
                (v for v in all_versions if v == minor or v.startswith(minor + ".")),
                None,
            )
            if match:
                default_full = match
        return default_full

    @staticmethod
    def _read_context(dst_path):
        pyproject = dst_path / "pyproject.toml"
        if pyproject.exists():
            try:
                with open(pyproject, "rb") as f:
                    doc = tomllib.load(f)
                settings = (
                    doc.get("tool", {})
                    .get("plone", {})
                    .get("backend_addon", {})
                    .get("settings", {})
                )
                if settings:
                    project = doc.get("project", {})
                    result = dict(settings)
                    if "package_title" not in result and "name" in project:
                        result["package_title"] = (
                            project["name"].replace("-", " ").replace(".", " ").title()
                        )
                    if "package_description" not in result and "description" in project:
                        result["package_description"] = project["description"]
                    return result
            except Exception:
                pass

        # Fallback: try legacy detection (bobtemplate.cfg, setup.py, older pyproject.toml)
        legacy = find_legacy_addon_context(dst_path)
        if legacy:
            legacy.pop("_legacy_source", None)
            # Derive title/description from package_name
            package_name = legacy.get("package_name", "")
            if package_name and "package_title" not in legacy:
                legacy["package_title"] = (
                    package_name.replace("-", " ").replace(".", " ").title()
                )
            # Try to read description from setup.py or pyproject.toml
            if "package_description" not in legacy and pyproject.exists():
                try:
                    with open(pyproject, "rb") as f:
                        doc = tomllib.load(f)
                    desc = doc.get("project", {}).get("description")
                    if desc:
                        legacy["package_description"] = desc
                except Exception:
                    pass
            return legacy

        return {}
