"""Jinja2 extensions for the Barceloneta theme template."""

import sys
from pathlib import Path

from copier_template_extensions import ContextHook

_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from shared.hooks.theme_conflict import reject_other_theme  # noqa: E402


class ThemeConflictHook(ContextHook):
    """Reject another theme variant before files are rendered."""

    def hook(self, context):
        dest = Path(context.get("_copier_conf", {}).get("dst_path", "."))
        reject_other_theme(dest, "theme_barceloneta")
