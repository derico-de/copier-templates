"""Jinja2 extensions for the restapi_service subtemplate."""

import sys
from pathlib import Path

from copier_template_extensions import ContextHook

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.utils.content_types_scanner import (  # noqa: E402
    all_content_type_interfaces,
)


class ServiceForInterfacesHook(ContextHook):
    """Populate ``service_for_choices`` with default + package interfaces."""

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", "") or ".")
        choices = all_content_type_interfaces(dst_path)
        choices.append("<enter manually>")
        context["service_for_choices"] = choices
