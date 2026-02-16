#!/usr/bin/env python3
"""Detect parent addon context for subtemplates."""
import sys
import tomllib
from pathlib import Path
from typing import Any

from exceptions import AddonContextError


def find_addon_context(start_path: Path | None = None) -> dict[str, Any] | None:
    """
    Find parent addon context by looking for:
    1. .copier-answers.backend-addon.*.yml file in current directory
    2. [tool.plone.backend_addon.settings] section in pyproject.toml

    Args:
        start_path: Directory to search in (defaults to current directory)

    Returns:
        Dictionary with addon settings or None if not found
    """
    start_path = start_path or Path.cwd()

    # Check for copier answers file pattern
    for f in start_path.glob(".copier-answers.backend-addon.*.yml"):
        # Found answers file, read pyproject.toml for settings
        pyproject_path = start_path / "pyproject.toml"
        if pyproject_path.exists():
            settings = _read_addon_settings(pyproject_path)
            if settings:
                return settings

    # Also check for the default copier answers file
    default_answers = start_path / ".copier-answers.yml"
    if default_answers.exists():
        pyproject_path = start_path / "pyproject.toml"
        if pyproject_path.exists():
            settings = _read_addon_settings(pyproject_path)
            if settings:
                return settings

    # Check pyproject.toml directly
    pyproject_path = start_path / "pyproject.toml"
    if pyproject_path.exists():
        settings = _read_addon_settings(pyproject_path)
        if settings:
            return settings

    return None


def _read_addon_settings(pyproject_path: Path) -> dict[str, Any] | None:
    """
    Read addon settings from pyproject.toml.

    Args:
        pyproject_path: Path to pyproject.toml

    Returns:
        Dictionary with addon settings or None if not found
    """
    try:
        with open(pyproject_path, "rb") as f:
            doc = tomllib.load(f)

        settings = doc.get("tool", {}).get("plone", {}).get("backend_addon", {}).get("settings", {})
        if settings:
            return dict(settings)
    except (tomllib.TOMLDecodeError, OSError):
        pass

    return None


def require_addon_context(start_path: Path | None = None) -> dict[str, Any]:
    """
    Raise AddonContextError if no parent addon found.

    Args:
        start_path: Directory to search in (defaults to current directory)

    Returns:
        Dictionary with addon settings

    Raises:
        AddonContextError: If no parent addon is detected
    """
    context = find_addon_context(start_path)
    if not context:
        raise AddonContextError(
            "No parent addon detected. This template must be run inside an existing backend_addon."
        )
    return context


def get_package_folder(package_name: str) -> str:
    """
    Convert package name to folder path.

    Args:
        package_name: Python package name (e.g., 'collective.mypackage')

    Returns:
        Folder path (e.g., 'collective/mypackage')
    """
    return package_name.replace(".", "/")


if __name__ == "__main__":
    # Used as pre-copy hook by subtemplates
    try:
        require_addon_context()
    except AddonContextError as e:
        print("\n" + "=" * 60)
        print("ERROR: No parent addon detected!")
        print("=" * 60)
        print(f"\n{e}")
        print("\nFirst create an addon with:")
        print("  copier copy gh:plone/copier-templates/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory.")
        print("=" * 60 + "\n")
        sys.exit(1)
