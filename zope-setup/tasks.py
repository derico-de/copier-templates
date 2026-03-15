#!/usr/bin/env python3
"""Post-copy tasks for zope-setup template."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from hooks.addon_context import find_addon_context
from utils.pyproject_updater import PyprojectUpdater


def update_pyproject(dest_path, plone_version, distribution, db_storage):
    # CWD resolution (MUST come first — copier may set CWD to dest)
    cwd = Path.cwd()
    dest = Path(dest_path)

    if (cwd / "pyproject.toml").exists():
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    pyproject_path = dest / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    updater = PyprojectUpdater(pyproject_path)

    # Auto-detect addon context
    addon_context = find_addon_context(dest)

    # 1. Add runtime dependencies
    runtime_deps = [distribution, "Paste", "plone.app.caching", "plone.app.upgrade"]
    if db_storage == "zeo":
        runtime_deps.append("ZEO")
    elif db_storage == "relstorage":
        runtime_deps.extend(["relstorage", "psycopg2"])
    # "blobs" and "direct" need no extra deps

    for dep in runtime_deps:
        updater.add_to_list("project", "dependencies", value=dep)

    # 2. Add dev dependencies
    for dep in ["invoke", "watchdog"]:
        updater.add_to_list("project", "optional-dependencies", "dev", value=dep)

    # 3. Ensure [tool.uv] and add constraint-dependencies
    updater.ensure_section("tool", "uv")
    constraint = f"Products.CMFPlone=={plone_version}"
    updater.add_to_list("tool", "uv", "constraint-dependencies", value=constraint)

    # 4. Record project settings
    updater.set_project_setting("plone_version", plone_version)
    updater.set_project_setting("distribution", distribution)
    updater.set_project_setting("db_storage", db_storage)

    # 5. If inside an addon, register zope_setup in addon settings
    if addon_context:
        updater.set_addon_setting("zope_setup", True)
        package_name = addon_context.get("package_name", "")
        print(f"Detected addon context: {package_name}")
        print(f"Registered zope_setup in addon settings.")

    updater.save()
    print(f"Updated pyproject.toml with zope-setup dependencies.")


def main():
    """Main entry point — sys.argv dispatch."""
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args...]")
        print("Commands: update_pyproject")
        sys.exit(1)

    command = sys.argv[1]

    if command == "update_pyproject":
        if len(sys.argv) < 3:
            print("Usage: tasks.py update_pyproject <dest_path> [--plone-version=X] [--distribution=Y] [--db-storage=Z]")
            sys.exit(1)

        dest_path = sys.argv[2]
        # Parse --key=value args
        kwargs = {}
        for arg in sys.argv[3:]:
            if arg.startswith("--"):
                key, _, value = arg[2:].partition("=")
                kwargs[key.replace("-", "_")] = value

        update_pyproject(
            dest_path,
            plone_version=kwargs.get("plone_version", "6.1.1"),
            distribution=kwargs.get("distribution", "plone.volto"),
            db_storage=kwargs.get("db_storage", "direct"),
        )
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
