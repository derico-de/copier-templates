#!/usr/bin/env python3
"""Tasks for behavior subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from hooks.addon_context import find_addon_context
from utils.pyproject_updater import PyprojectUpdater


def validate(dest_path: str) -> None:
    """Validate that parent addon exists."""
    dest = Path(dest_path)
    context = find_addon_context(dest)
    if not context:
        print("\n" + "=" * 60)
        print("ERROR: No parent addon detected!")
        print("=" * 60)
        print(f"\nThis template must be run inside an existing backend_addon.")
        print(f"Destination: {dest}")
        print("\nFirst create an addon with:")
        print("  copier copy gh:plone/copier-templates/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-addon")
        print("  copier copy gh:plone/copier-templates/behavior .")
        print("=" * 60 + "\n")
        sys.exit(1)


def post_copy(dest_path: str, behavior_name: str) -> None:
    """
    Post-copy tasks:
    1. Register behavior in addon settings
    """
    dest = Path(dest_path)
    pyproject_path = dest / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    updater = PyprojectUpdater(pyproject_path)
    updater.register_subtemplate("behaviors", behavior_name)
    updater.save()

    print(f"Registered behavior '{behavior_name}' in addon settings.")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args...]")
        print("Commands: validate, post_copy")
        sys.exit(1)

    command = sys.argv[1]

    if command == "validate":
        if len(sys.argv) < 3:
            print("Usage: tasks.py validate <dest_path>")
            sys.exit(1)
        validate(sys.argv[2])

    elif command == "post_copy":
        if len(sys.argv) < 4:
            print("Usage: tasks.py post_copy <dest_path> <behavior_name>")
            sys.exit(1)
        post_copy(sys.argv[2], sys.argv[3])

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
