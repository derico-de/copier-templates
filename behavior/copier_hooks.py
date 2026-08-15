#!/usr/bin/env python3
"""Tasks for behavior subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context, resolve_post_copy_context
from utils.xml_escape import escape_xml_attr
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml


def validate(dest_path: str) -> None:
    """Validate that parent addon exists."""
    dest = Path(dest_path)

    # Check addon context (blocking - raises exception)
    context = find_addon_context(dest)
    if not context:
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(
    dest_path: str,
    behavior_name: str,
    behavior_interface: str = "",
    behavior_module: str = "",
    behavior_class: str = "",
    behavior_description: str = "A custom Dexterity behavior",
    behavior_marker: str = "True",
    behavior_factory: str = "True",
) -> None:
    """
    Post-copy tasks:
    1. Register behavior in addon settings
    2. Extend behaviors/configure.zcml with a <plone:behavior> entry
    3. Add include for behaviors subpackage in parent configure.zcml
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("behaviors", behavior_name):
        print(f"Registered behavior '{behavior_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    # Extend behaviors/configure.zcml with the <plone:behavior> entry.
    # Pin an explicit short name so the behavior is addressable by a stable
    # identifier instead of the full interface dotted path (which would change
    # if the module/interface is ever moved or renamed).
    provides = f".{behavior_module}.{behavior_interface}"
    behavior_lookup_name = f"{package_name}.{behavior_module}"
    lines = [
        "  <plone:behavior",
        f'      name="{behavior_lookup_name}"',
        f'      title="{behavior_interface}"',
        f'      description="{escape_xml_attr(behavior_description)}"',
        f'      provides="{provides}"',
    ]
    if behavior_marker.lower() == "true":
        lines.append(f'      marker=".{behavior_module}.{behavior_interface}Marker"')
    if behavior_factory.lower() == "true":
        lines.append(f'      factory=".{behavior_module}.{behavior_class}"')
    lines.append("      />")
    snippet = "\n".join(lines) + "\n"

    behaviors_zcml = dest / f"src/{package_folder}/behaviors/configure.zcml"
    _, msg = extend_configure_zcml(
        behaviors_zcml,
        package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="plone:behavior",
        identifying_attr="provides",
        identifying_value=provides,
        snippet=snippet,
    )
    print(msg)

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".behaviors"):
            zcml_updater.add_include(".behaviors")
            zcml_updater.save()
            print("Added <include package=\".behaviors\" /> to parent configure.zcml.")


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
                print("Usage: tasks.py post_copy <dest_path> <behavior_name> ...")
                sys.exit(1)
            post_copy(*sys.argv[2:])

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except CopierTemplateError as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print("\nFirst create an addon with:")
        print("  copier copy ~/.copier-templates/plone-copier-templates/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-addon")
        print("  copier copy ~/.copier-templates/plone-copier-templates/behavior .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
