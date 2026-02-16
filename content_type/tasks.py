#!/usr/bin/env python3
"""Tasks for content_type subtemplate."""
import re
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context
from hooks.git_check import warn_git_unclean
from utils.pyproject_updater import PyprojectUpdater
from utils.xml_updater import ConfigureZCMLUpdater, TypesXMLUpdater


def compute_content_type_values(content_type_name: str) -> dict:
    """
    Compute derived values from content_type_name.

    These match the computations in copier.yml.
    """
    # content_type_class: remove spaces, dashes, underscores
    content_type_class = re.sub(r"[ \-_]", "", content_type_name)

    # content_type_module: lowercase, replace spaces/dashes with underscores
    content_type_module = content_type_name.lower().replace(" ", "_").replace("-", "_")

    # content_type_interface: I + class name
    content_type_interface = f"I{content_type_class}"

    return {
        "content_type_class": content_type_class,
        "content_type_module": content_type_module,
        "content_type_interface": content_type_interface,
    }


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


def post_copy(dest_path: str, content_type_name: str, content_type_description: str = "A custom content type") -> None:
    """
    Post-copy tasks:
    1. Register content type in addon settings
    2. Update content/configure.zcml with behavior entry
    3. Update profiles/default/types.xml with FTI reference
    """
    # Copier runs tasks from the destination directory, so check CWD first
    cwd = Path.cwd()
    dest = Path(dest_path)

    # If pyproject.toml exists in CWD, use that (copier runs from destination)
    if (cwd / "pyproject.toml").exists():
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    pyproject_path = dest / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    # Get computed values
    values = compute_content_type_values(content_type_name)
    content_type_class = values["content_type_class"]
    content_type_module = values["content_type_module"]
    content_type_interface = values["content_type_interface"]

    # Get package info from pyproject.toml
    pyproject_updater = PyprojectUpdater(pyproject_path)
    addon_settings = pyproject_updater.get_addon_settings()
    package_name = addon_settings.get("package_name", "")

    # Fallback: read package_name directly from pyproject.toml if not found
    if not package_name:
        pyproject_content = pyproject_path.read_text()
        # Try to find package_name in [tool.plone.backend_addon.settings]
        match = re.search(r'^\s*package_name\s*=\s*["\']([^"\']+)["\']', pyproject_content, re.MULTILINE)
        if match:
            package_name = match.group(1)
        else:
            # Fallback to project name
            match = re.search(r'^\s*name\s*=\s*["\']([^"\']+)["\']', pyproject_content, re.MULTILINE)
            if match:
                package_name = match.group(1)

    if not package_name:
        print("Warning: Could not determine package_name from pyproject.toml")
        return

    package_folder = package_name.replace(".", "/")

    # 1. Register content type in addon settings
    pyproject_updater.register_subtemplate("content_types", content_type_name)
    pyproject_updater.save()
    print(f"Registered content type '{content_type_name}' in addon settings.")

    # 2. Update content/configure.zcml with behavior entry
    zcml_path = dest / f"src/{package_folder}/content/configure.zcml"
    zcml_updater = ConfigureZCMLUpdater(zcml_path)
    zcml_updater.create_if_missing(package_name)
    provides = f".{content_type_module}.{content_type_interface}"
    if not zcml_updater.has_behavior(provides):
        zcml_updater.add_behavior(
            title=content_type_interface,
            description=content_type_description,
            provides=provides,
        )
        zcml_updater.save()
        print(f"Updated {zcml_path.relative_to(dest)} with behavior entry.")
    else:
        print(f"Behavior already exists in {zcml_path.relative_to(dest)}.")

    # 3. Update profiles/default/types.xml with FTI reference
    types_path = dest / f"src/{package_folder}/profiles/default/types.xml"
    types_updater = TypesXMLUpdater(types_path)
    types_updater.create_if_missing()
    if not types_updater.has_fti_reference(content_type_class):
        types_updater.add_fti_reference(content_type_class)
        types_updater.save()
        print(f"Updated {types_path.relative_to(dest)} with FTI reference.")
    else:
        print(f"FTI reference already exists in {types_path.relative_to(dest)}.")

    # 4. Add include for content subpackage in parent configure.zcml
    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        from utils.xml_updater import ParentZCMLUpdater
        parent_updater = ParentZCMLUpdater(parent_zcml)
        if not parent_updater.has_include(".content"):
            parent_updater.add_include(".content")
            parent_updater.save()
            print(f"Added <include package=\".content\" /> to parent configure.zcml.")


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
                print("Usage: tasks.py post_copy <dest_path> <content_type_name> [content_type_description]")
                sys.exit(1)
            content_type_description = sys.argv[4] if len(sys.argv) > 4 else "A custom content type"
            post_copy(sys.argv[2], sys.argv[3], content_type_description)

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
        print("  copier copy gh:plone/copier-templates/content_type .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
