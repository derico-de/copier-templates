#!/usr/bin/env python3
"""Detect legacy Plone package context from old-style files.

Supports detection from:
- bobtemplate.cfg (bobtemplates.plone)
- setup.py (setuptools)
- pyproject.toml with [project] but without [tool.plone.backend_addon.settings]
"""
import configparser
import re
from pathlib import Path
from typing import Any


def find_legacy_addon_context(start_path: Path | None = None) -> dict[str, Any] | None:
    """
    Try to detect addon context from legacy files.

    Checks in order:
    1. bobtemplate.cfg
    2. setup.py
    3. pyproject.toml [project] section (without plone settings)

    Returns:
        Dictionary with at least package_name and package_folder, or None
    """
    start_path = start_path or Path.cwd()

    # Try bobtemplate.cfg first
    context = _read_bobtemplate_cfg(start_path)
    if context:
        return context

    # Try setup.py
    context = _read_setup_py(start_path)
    if context:
        return context

    # Try pyproject.toml [project] section
    context = _read_pyproject_project_section(start_path)
    if context:
        return context

    return None


def _read_bobtemplate_cfg(start_path: Path) -> dict[str, Any] | None:
    """
    Read package info from bobtemplate.cfg.

    Typical format:
        [mr.bob]
        template = bobtemplates.plone:addon

        [variables]
        package.name = collective.mypackage
        package.type = Addon
    """
    cfg_path = start_path / "bobtemplate.cfg"
    if not cfg_path.exists():
        return None

    try:
        config = configparser.ConfigParser()
        config.read(cfg_path)

        if not config.has_section("variables"):
            return None

        package_name = config.get("variables", "package.name", fallback=None)
        if not package_name:
            return None

        package_folder = package_name.replace(".", "/")

        result = {
            "package_name": package_name,
            "package_folder": package_folder,
            "_legacy_source": "bobtemplate.cfg",
        }

        # Read optional fields
        package_type = config.get("variables", "package.type", fallback=None)
        if package_type:
            result["package_type"] = package_type

        return result
    except (configparser.Error, OSError):
        return None


def _read_setup_py(start_path: Path) -> dict[str, Any] | None:
    """
    Extract package name from setup.py.

    Looks for patterns like:
        name='collective.mypackage'
        name="collective.mypackage"
    """
    setup_path = start_path / "setup.py"
    if not setup_path.exists():
        return None

    try:
        content = setup_path.read_text()

        # Match name= in setup() call
        match = re.search(
            r"""name\s*=\s*['"]([^'"]+)['"]""",
            content,
        )
        if not match:
            return None

        package_name = match.group(1)
        package_folder = package_name.replace(".", "/")

        return {
            "package_name": package_name,
            "package_folder": package_folder,
            "_legacy_source": "setup.py",
        }
    except OSError:
        return None


def _read_pyproject_project_section(start_path: Path) -> dict[str, Any] | None:
    """
    Read package name from pyproject.toml [project] section.

    This is the fallback for packages that have a pyproject.toml with a
    [project] section but no [tool.plone.backend_addon.settings].
    """
    import tomllib

    pyproject_path = start_path / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    try:
        with open(pyproject_path, "rb") as f:
            doc = tomllib.load(f)

        # Only use this fallback if there are no modern Plone settings.
        # A standalone zope-setup project is not a legacy backend add-on.
        plone = doc.get("tool", {}).get("plone", {})
        addon_settings = plone.get("backend_addon", {}).get("settings", {})
        project_settings = plone.get("project", {}).get("settings", {})
        if addon_settings or project_settings:
            return None

        project = doc.get("project", {})
        package_name = project.get("name")
        if not package_name:
            return None

        # Verify this looks like a Plone package by checking for plone-related
        # dependencies, keywords, or classifiers
        if not _looks_like_plone_package(doc):
            return None

        package_folder = package_name.replace(".", "/")

        return {
            "package_name": package_name,
            "package_folder": package_folder,
            "_legacy_source": "pyproject.toml",
        }
    except (tomllib.TOMLDecodeError, OSError):
        return None


def _looks_like_plone_package(doc: dict) -> bool:
    """
    Heuristic check: does this pyproject.toml look like a Plone/Zope package?

    Checks dependencies, classifiers, and keywords for Plone/Zope references.
    Also checks for src directory layout typical of Plone addons.
    """
    project = doc.get("project", {})

    # Check dependencies
    deps = project.get("dependencies", [])
    dep_str = " ".join(str(d).lower() for d in deps)
    if any(keyword in dep_str for keyword in ["plone", "zope", "products."]):
        return True

    # Check classifiers
    classifiers = project.get("classifiers", [])
    classifier_str = " ".join(str(c).lower() for c in classifiers)
    if "plone" in classifier_str or "zope" in classifier_str:
        return True

    # Check keywords
    keywords = project.get("keywords", [])
    keyword_str = " ".join(str(k).lower() for k in keywords)
    if "plone" in keyword_str or "zope" in keyword_str:
        return True

    # Check build-system for zest.releaser or other Plone tools
    build_system = doc.get("build-system", {})
    requires = build_system.get("requires", [])
    requires_str = " ".join(str(r).lower() for r in requires)
    if "plone" in requires_str:
        return True

    # Check for [tool.zest-releaser] or other Plone-specific tool sections
    tools = doc.get("tool", {})
    if "zest-releaser" in tools:
        return True

    # Check for z3c.autoinclude.plugin entry point
    entry_points = project.get("entry-points", {})
    if "z3c.autoinclude.plugin" in entry_points:
        return True

    return False
