#!/usr/bin/env python3
"""Post-copy tasks for zope_instance template."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import CopierTemplateError, ProjectContextError
from hooks.project_context import find_project_context
from utils.pyproject_updater import PyprojectUpdater


def validate(dest_path: str) -> None:
    """Validate that we are inside a zope-setup project."""
    dest = Path(dest_path)

    # Check project context (blocking)
    context = find_project_context(dest)
    if not context:
        raise ProjectContextError(
            f"No project context detected at {dest}. "
            "This template must be run inside an existing zope-setup project."
        )


def post_copy(dest_path: str, instance_name: str, port: int = 8080) -> None:
    """
    Post-copy tasks:
    1. Register instance in project settings
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

    updater = PyprojectUpdater(pyproject_path)
    updater.add_to_list("tool", "plone", "project", "settings", "instances", value=instance_name)
    updater.save()
    print(f"Registered instance '{instance_name}' (port {port}) in project settings.")


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
                print("Usage: tasks.py post_copy <dest_path> <instance_name> [--port=N]")
                sys.exit(1)
            instance_name = sys.argv[3]
            # Parse --key=value args
            kwargs = {}
            for arg in sys.argv[4:]:
                if arg.startswith("--"):
                    key, _, value = arg[2:].partition("=")
                    kwargs[key.replace("-", "_")] = value

            post_copy(
                sys.argv[2],
                instance_name,
                port=int(kwargs.get("port", 8080)),
            )

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except CopierTemplateError as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print("\nFirst create a project with:")
        print("  copier copy ~/.copier-templates/plone-copier-templates/zope-setup my-project")
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-project")
        print("  copier copy ~/.copier-templates/plone-copier-templates/zope_instance .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
