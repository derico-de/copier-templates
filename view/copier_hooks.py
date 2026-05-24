#!/usr/bin/env python3
"""Tasks for the view subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from hooks.git_check import warn_git_unclean  # noqa: E402
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml  # noqa: E402


def validate(dest_path: str) -> None:
    dest = Path(dest_path)
    warn_git_unclean(dest)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(
    dest_path: str,
    view_name: str,
    view_for_interface: str = "*",
    view_module: str = "",
    view_class_name: str = "",
    view_template: str = "True",
    view_marker: str = "False",
) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("views", view_name):
        print(f"Registered view '{view_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    # Extend views/configure.zcml (create if missing) with a new browser:page
    views_zcml = dest / f"src/{package_folder}/views/configure.zcml"
    if view_template.lower() == "true":
        snippet = (
            "  <browser:page\n"
            f'      name="{view_name}"\n'
            f'      for="{view_for_interface}"\n'
            f'      class=".{view_module}.{view_class_name}"\n'
            f'      template="{view_module}.pt"\n'
            '      permission="zope2.View"\n'
            "      />\n"
        )
    else:
        snippet = (
            "  <browser:page\n"
            f'      name="{view_name}"\n'
            f'      for="{view_for_interface}"\n'
            f'      class=".{view_module}.{view_class_name}"\n'
            '      permission="zope2.View"\n'
            "      />\n"
        )
    _, msg = extend_configure_zcml(
        views_zcml,
        package_name or "package",
        namespaces={"browser": "http://namespaces.zope.org/browser"},
        element_tag="browser:page",
        identifying_attr="name",
        identifying_value=view_name,
        snippet=snippet,
        # A view is identified by name + the interface it is registered for,
        # so the same @@name may exist for different content types.
        extra_identifying_attrs={"for": view_for_interface},
    )
    print(msg)

    # Add include for views subpackage in parent configure.zcml
    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".views"):
            zcml_updater.add_include(".views")
            zcml_updater.save()
            print(
                'Added <include package=".views" /> to parent '
                "configure.zcml."
            )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: copier_hooks.py <command> [args...]")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command == "validate":
            validate(sys.argv[2])
        elif command == "post_copy":
            post_copy(*sys.argv[2:])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except CopierTemplateError as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
