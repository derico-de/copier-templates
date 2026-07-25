#!/usr/bin/env python3
"""Tasks for restapi_service subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError
from hooks.addon_context import find_addon_context, resolve_post_copy_context
from hooks.git_check import warn_git_unclean
from utils.xml_updater import (
    ParentZCMLUpdater,
    ZCMLConfigureExtender,
)


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
    service_for: str = "plone.dexterity.interfaces.IDexterityContainer",
    service_module: str = "",
    service_class: str = "",
    service_endpoint: str = "",
    http_get: str = "True",
    http_post: str = "False",
    http_patch: str = "False",
    http_delete: str = "False",
    expandable: str = "False",
) -> None:
    """
    Post-copy tasks:
    1. Register service in addon settings
    2. Extend services/configure.zcml with <plone:service> entries
    3. Add include for services subpackage in parent configure.zcml
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    endpoint = service_endpoint or (
        f"@{service_name.lower().replace('_', '-').replace(' ', '-')}"
    )

    if ctx.register_subtemplate("services", endpoint):
        print(f"Registered service '{endpoint}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    import re as _re

    factory = f".{service_module}.{service_class}"
    methods = [
        ("GET", http_get, "zope2.View"),
        ("POST", http_post, "cmf.ModifyPortalContent"),
        ("PATCH", http_patch, "cmf.ModifyPortalContent"),
        ("DELETE", http_delete, "cmf.ModifyPortalContent"),
    ]
    services_zcml = dest / f"src/{package_folder}/services/configure.zcml"
    ext = ZCMLConfigureExtender(services_zcml)
    ext.create_if_missing(
        package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
    )
    ext.ensure_namespaces({"plone": "http://namespaces.plone.org/plone"})

    def _has_method_name(content: str, method: str, name: str) -> bool:
        pat = _re.compile(
            r"<plone:service\b[^>]*?\bmethod\s*=\s*[\"']"
            + _re.escape(method)
            + r"[\"'][^>]*?\bname\s*=\s*[\"']"
            + _re.escape(name)
            + r"[\"']",
            _re.DOTALL,
        )
        return bool(pat.search(content))

    for method, enabled, permission in methods:
        if enabled.lower() != "true":
            continue
        if _has_method_name(ext.load(), method, endpoint):
            print(
                f"plone:service {method} '{endpoint}' already exists in "
                f"{services_zcml.relative_to(dest)}."
            )
            continue
        snippet = (
            "  <plone:service\n"
            f'      method="{method}"\n'
            f'      for="{service_for}"\n'
            f'      factory="{factory}"\n'
            f'      name="{endpoint}"\n'
            f'      permission="{permission}"\n'
            "      />\n"
        )
        ext.append_element(snippet)
        print(
            f"Extended {services_zcml.relative_to(dest)} with plone:service "
            f"{method} '{endpoint}'."
        )
    # Register IExpandableElement adapter if requested
    if expandable.lower() == "true":
        element_factory = f".{service_module}.{service_class}Element"
        element_name = service_name.lower().replace("_", "-").replace(" ", "-")
        adapter_snippet = (
            "  <adapter\n"
            f'      factory="{element_factory}"\n'
            f'      name="{element_name}"\n'
            "      />\n"
        )
        content = ext.load()
        if element_factory not in content:
            ext.append_element(adapter_snippet)
            print(
                f"Extended {services_zcml.relative_to(dest)} with "
                f"IExpandableElement adapter '{element_name}'."
            )

    ext.save()

    # Declare the plone.restapi profile dependency in metadata.xml
    ctx.add_profile_dependency("profile-plone.restapi:default")

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".services"):
            zcml_updater.add_include(".services")
            zcml_updater.save()
            print("Added <include package=\".services\" /> to parent configure.zcml.")


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
