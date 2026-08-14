"""Jinja2 extensions for the content_type subtemplate."""

import sys
from pathlib import Path

from copier_template_extensions import ContextHook

_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.utils.content_types_scanner import all_portal_types  # noqa: E402


class ParentPortalTypesHook(ContextHook):
    """Populate ``parent_content_type_choices`` with default + package portal types."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", "") or ".")
        choices = all_portal_types(dst_path)
        choices.append("<enter manually>")
        context["parent_content_type_choices"] = choices
