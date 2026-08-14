"""Jinja2 extensions for the backend_addon template."""

import sys
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


class LegacyContextHook(ContextHook):
    """Pre-fill defaults from legacy package files (bobtemplate.cfg, setup.py, etc.)."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", ""))
        legacy = find_legacy_addon_context(dst_path)
        if legacy:
            legacy.pop("_legacy_source", None)
            context["legacy_context"] = legacy
        else:
            context["legacy_context"] = {}
