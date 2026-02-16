#!/usr/bin/env python3
"""Tasks for restapi_service subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context
from hooks.git_check import warn_git_unclean
from utils.pyproject_updater import PyprojectUpdater


def validate(dest_path: str) -> None:
    """Validate that parent addon exists."""
    dest = Path(dest_path)

    # Warn about git state (non-blocking)
    warn_git_unclean(dest)

    # Check addon context (blocking - raises exception)
    context = find_addon_context(dest)
    if not context:
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(dest_path: str, service_name: str) -> None:
    """
    Post-copy tasks:
    1. Register service in addon settings
    2. Add include for services subpackage in parent configure.zcml
    """
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

    # Normalize service name to endpoint format
    endpoint = f"@{service_name.lower().replace('_', '-').replace(' ', '-')}"

    updater = PyprojectUpdater(pyproject_path)
    updater.register_subtemplate("services", endpoint)
    updater.save()

    print(f"Registered service '{endpoint}' in addon settings.")

    # Get package info for ZCML update
    addon_settings = updater.get_addon_settings()
    package_folder = addon_settings.get("package_folder", "")
    if not package_folder:
        package_name = addon_settings.get("package_name", "")
        if package_name:
            package_folder = package_name.replace(".", "/")

    if package_folder:
        parent_zcml = dest / f"src/{package_folder}/configure.zcml"
        if parent_zcml.exists():
            from utils.xml_updater import ParentZCMLUpdater
            zcml_updater = ParentZCMLUpdater(parent_zcml)
            if not zcml_updater.has_include(".services"):
                zcml_updater.add_include(".services")
                zcml_updater.save()
                print(f"Added <include package=\".services\" /> to parent configure.zcml.")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args...]")
        print("Commands: validate, post_copy")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "validate":
            if len(sys.argv) < 3:
                print("Usage: tasks.py validate <dest_path>")
                sys.exit(1)
            validate(sys.argv[2])

        elif command == "post_copy":
            if len(sys.argv) < 4:
                print("Usage: tasks.py post_copy <dest_path> <service_name>")
                sys.exit(1)
            post_copy(sys.argv[2], sys.argv[3])

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except CopierTemplateError as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print("\nFirst create an addon with:")
        print("  copier copy gh:plone/copier-templates/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-addon")
        print("  copier copy gh:plone/copier-templates/restapi_service .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
