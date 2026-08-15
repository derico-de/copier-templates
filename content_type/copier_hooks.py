#!/usr/bin/env python3
"""Tasks for content_type subtemplate."""
import re
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context, resolve_post_copy_context
from utils.xml_updater import (
    ConfigureZCMLUpdater,
    DiffToolXMLUpdater,
    ParentFTIUpdater,
    RepositoryToolXMLUpdater,
    TypesXMLUpdater,
)


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


MARKER = "<!-- -*- extra stuff goes here -*- -->"


def _register_add_permission(
    permissions_path: Path,
    rolemap_path: Path,
    package_name: str,
    content_type_class: str,
) -> None:
    """Add ``Add <Type>`` permission declarations to permissions.zcml and rolemap.xml."""
    permission_id = f"{package_name}.Add{content_type_class}"
    permission_title = f"{package_name}: Add {content_type_class}"

    if permissions_path.exists():
        text = permissions_path.read_text()
        if permission_id not in text:
            snippet = (
                f'{MARKER}\n\n'
                f'    <permission\n'
                f'        id="{permission_id}"\n'
                f'        title="{permission_title}"\n'
                f'    />\n'
            )
            text = text.replace(MARKER, snippet, 1)
            permissions_path.write_text(text)
            print(f"Registered '{permission_title}' in permissions.zcml.")

    if rolemap_path.exists():
        text = rolemap_path.read_text()
        if permission_title not in text:
            snippet = (
                f'{MARKER}\n\n'
                f'    <permission name="{permission_title}" acquire="True">\n'
                f'      <role name="Manager"/>\n'
                f'      <role name="Site Administrator"/>\n'
                f'      <role name="Owner"/>\n'
                f'      <role name="Contributor"/>\n'
                f'    </permission>\n'
            )
            text = text.replace(MARKER, snippet, 1)
            rolemap_path.write_text(text)
            print(f"Registered '{permission_title}' in rolemap.xml.")


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
    content_type_name: str,
    content_type_description: str = "A custom content type",
    parent_content_type: str = "",
) -> None:
    """
    Post-copy tasks:
    1. Register content type in addon settings
    2. Update content/configure.zcml with behavior entry
    3. Update profiles/default/types.xml with FTI reference
    4. Declare plone.app.dexterity profile dependency in metadata.xml
    5. Register the type for versioning in repositorytool.xml
    6. Register the type with the diff tool in diff_tool.xml
    7. If global_allow=false and parent_content_type is set, update the
       parent FTI's allowed_content_types (when that FTI lives in this package).
    8. Include the content subpackage in the parent configure.zcml
    9. Register the Add permission in permissions.zcml and rolemap.xml
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_name:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    # Get computed values
    values = compute_content_type_values(content_type_name)
    content_type_class = values["content_type_class"]
    content_type_module = values["content_type_module"]
    content_type_interface = values["content_type_interface"]

    # 1. Register content type in addon settings
    if ctx.register_subtemplate("content_types", content_type_name):
        print(
            f"Registered content type '{content_type_name}' in addon settings."
        )

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

    profiles_dir = dest / f"src/{package_folder}/profiles/default"

    # 4. Declare the Dexterity profile dependency in metadata.xml
    ctx.add_profile_dependency("profile-plone.app.dexterity:default")

    # 5. Register the type for versioning in repositorytool.xml
    if RepositoryToolXMLUpdater(profiles_dir / "repositorytool.xml").add_type(
        content_type_class
    ):
        print(
            f"Registered '{content_type_class}' for versioning in "
            "repositorytool.xml."
        )
    else:
        print(f"'{content_type_class}' already in repositorytool.xml.")

    # 6. Register the type with the diff tool in diff_tool.xml
    if DiffToolXMLUpdater(profiles_dir / "diff_tool.xml").add_type(
        content_type_class
    ):
        print(
            f"Registered '{content_type_class}' with the diff tool in "
            "diff_tool.xml."
        )
    else:
        print(f"'{content_type_class}' already in diff_tool.xml.")

    # 7. If not globally addable, update parent FTI's allowed_content_types
    if parent_content_type:
        types_dir = dest / f"src/{package_folder}/profiles/default/types"
        # Try package-local naming (no spaces) first, then GenericSetup
        # convention (spaces → underscores) for default Plone types.
        parent_fti_name = parent_content_type.replace(" ", "")
        parent_fti_path = types_dir / f"{parent_fti_name}.xml"
        if not parent_fti_path.exists():
            parent_fti_name = parent_content_type.replace(" ", "_")
            parent_fti_path = types_dir / f"{parent_fti_name}.xml"

        parent_updater = ParentFTIUpdater(parent_fti_path)
        if parent_updater.exists():
            if parent_updater.add_allowed_child(content_type_class):
                parent_updater.save()
                print(
                    f"Added '{content_type_class}' to allowed_content_types of "
                    f"parent '{parent_content_type}' in "
                    f"{parent_fti_path.relative_to(dest)}."
                )
        else:
            # Parent FTI doesn't exist locally — create a minimal override
            # with purge="False" so it only appends to the allowed list.
            parent_updater.create_minimal(parent_content_type, content_type_class)
            parent_updater.save()
            print(
                f"Created minimal FTI override for '{parent_content_type}' "
                f"at {parent_fti_path.relative_to(dest)} "
                f"to allow '{content_type_class}'."
            )

    # 8. Add include for content subpackage in parent configure.zcml
    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        from utils.xml_updater import ParentZCMLUpdater
        parent_updater = ParentZCMLUpdater(parent_zcml)
        if not parent_updater.has_include(".content"):
            parent_updater.add_include(".content")
            parent_updater.save()
            print("Added <include package=\".content\" /> to parent configure.zcml.")

    # 9. Register the Add permission in permissions.zcml and rolemap.xml.
    _register_add_permission(
        dest / f"src/{package_folder}/permissions.zcml",
        dest / f"src/{package_folder}/profiles/default/rolemap.xml",
        package_name,
        content_type_class,
    )


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
                print(
                    "Usage: tasks.py post_copy <dest_path> <content_type_name> "
                    "[description] [content_type_class] [parent_content_type]"
                )
                sys.exit(1)
            content_type_description = sys.argv[4] if len(sys.argv) > 4 else "A custom content type"
            parent_content_type = sys.argv[5] if len(sys.argv) > 5 else ""
            post_copy(
                sys.argv[2],
                sys.argv[3],
                content_type_description,
                parent_content_type,
            )

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
        print("  copier copy ~/.copier-templates/plone-copier-templates/content_type .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
