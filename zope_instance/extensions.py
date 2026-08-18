"""Jinja2 extension to read project context from pyproject.toml."""

import sys
import tomllib
from pathlib import Path

from copier_template_extensions import ContextHook

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.hooks.legacy_context import find_legacy_addon_context  # noqa: E402


class ProjectContextHook(ContextHook):
    """Read project settings from pyproject.toml in the destination directory."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", ""))
        project_context = self._read_context(dst_path)
        context["project_context"] = project_context
        context["addon_context"] = self._read_addon_context(dst_path)

    @staticmethod
    def _read_addon_context(dst_path):
        """Detect whether the project lives inside an addon package.

        An addon project is a development environment, so the instance may
        bind to all interfaces. A standalone project is treated as a
        deployment target and binds to loopback only.
        """
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
                    return dict(settings)
            except Exception:
                pass

        legacy = find_legacy_addon_context(dst_path)
        if legacy:
            legacy.pop("_legacy_source", None)
            return legacy

        return {}

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
                .get("project", {})
                .get("settings", {})
            )
            if settings:
                result = dict(settings)
                project = doc.get("project", {})
                if "project_name" not in result and "name" in project:
                    result["project_name"] = project["name"]
                return result
        except Exception:
            pass
        return {}
