"""Jinja2 extension to read addon context from pyproject.toml."""

import tomllib
from pathlib import Path

from copier_template_extensions import ContextHook


class AddonContextHook(ContextHook):
    """Read addon settings from pyproject.toml in the destination directory."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", ""))
        addon_context = self._read_context(dst_path)
        context["addon_context"] = addon_context

    @staticmethod
    def _read_context(dst_path):
        pyproject = dst_path / "pyproject.toml"
        if not pyproject.exists():
            return {}
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
        return {}
