"""Shared hooks for copier-templates."""
from .addon_context import find_addon_context, require_addon_context
from .git_check import check_git_status, require_clean_git

__all__ = [
    "find_addon_context",
    "require_addon_context",
    "check_git_status",
    "require_clean_git",
]
