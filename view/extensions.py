"""Jinja2 extensions for the view subtemplate."""

import sys
from pathlib import Path

from copier_template_extensions import ContextHook

# Ensure shared package is importable
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.utils.content_types_scanner import (  # noqa: E402
    SITE_ROOT_INTERFACE,
    all_content_type_interfaces,
    portal_type_for_interface,
)


class ContentTypeInterfacesHook(ContextHook):
    """Populate ``view_for_choices`` and the test-context for the view's ``for``."""

    update = False

    def hook(self, context):
        dst_path = Path(context.get("_copier_conf", {}).get("dst_path", "") or ".")
        choices = all_content_type_interfaces(dst_path)
        choices.append("<enter manually>")
        context["view_for_choices"] = choices

        # Once the view's target interface is known (file-render phase),
        # derive the content the generated test should adapt so it reflects
        # the real registration instead of always using a Document.
        view_for = context.get("view_for_interface")
        if view_for is not None:
            context.update(_view_test_context(view_for, dst_path))


def _view_test_context(view_for_interface, dst_path):
    """Compute test-fixture variables for the view's ``for`` interface."""
    if view_for_interface == SITE_ROOT_INTERFACE:
        return {"view_test_use_site_root": True}
    portal_type = portal_type_for_interface(view_for_interface, dst_path) or "Document"
    test_id = "test-" + portal_type.lower().replace(" ", "-")
    return {
        "view_test_use_site_root": False,
        "view_test_type": portal_type,
        "view_test_id": test_id,
        "view_test_title": f"Test {portal_type}",
    }
