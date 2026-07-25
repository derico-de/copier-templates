#!/usr/bin/env python3
"""Tasks for restapi_service subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context, resolve_post_copy_context
from hooks.git_check import warn_git_unclean
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml


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


def post_copy(
    dest_path: str,
    service_name: str,
    service_module: str,
    service_endpoint: str,
) -> None:
    """
    Post-copy tasks:
    1. Register service in addon settings
    2. Chain the zcml includes: parent -> api -> services -> <service>
       (the service subpackage ships its own configure.zcml)
    3. Declare the plone.restapi profile dependency
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("services", service_endpoint):
        print(f"Registered service '{service_endpoint}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    api_zcml = dest / f"src/{package_folder}/api/configure.zcml"
    _, msg = extend_configure_zcml(
        api_zcml,
        package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="include",
        identifying_attr="package",
        identifying_value=".services",
        snippet='  <include package=".services" />\n',
    )
    print(msg)

    services_zcml = dest / f"src/{package_folder}/api/services/configure.zcml"
    _, msg = extend_configure_zcml(
        services_zcml,
        package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="include",
        identifying_attr="package",
        identifying_value=f".{service_module}",
        snippet=f'  <include package=".{service_module}" />\n',
    )
    print(msg)

    # Declare the plone.restapi profile dependency in metadata.xml
    ctx.add_profile_dependency("profile-plone.restapi:default")

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".api"):
            zcml_updater.add_include(".api")
            zcml_updater.save()
            print('Added <include package=".api" /> to parent configure.zcml.')


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
                print("Usage: tasks.py post_copy <dest_path> <service_name> ...")
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
        print("  copier copy ~/.copier-templates/plone-copier-templates/restapi_service .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
