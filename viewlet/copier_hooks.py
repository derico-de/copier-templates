#!/usr/bin/env python3
"""Tasks for the viewlet subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml  # noqa: E402


def validate(dest_path: str) -> None:
    dest = Path(dest_path)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(
    dest_path: str,
    viewlet_name: str,
    viewlet_for: str = "*",
    viewlet_manager: str = "plone.portalheader",
    viewlet_module: str = "",
    viewlet_class_name: str = "",
) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("viewlets", viewlet_name):
        print(f"Registered viewlet '{viewlet_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    snippet = (
        "  <browser:viewlet\n"
        f'      name="{viewlet_name}"\n'
        f'      for="{viewlet_for}"\n'
        f'      manager="{viewlet_manager}"\n'
        f'      class=".{viewlet_module}.{viewlet_class_name}"\n'
        '      permission="zope2.View"\n'
        "      />\n"
    )
    viewlets_zcml = dest / f"src/{package_folder}/viewlets/configure.zcml"
    _, msg = extend_configure_zcml(
        viewlets_zcml,
        package_name or "package",
        namespaces={"browser": "http://namespaces.zope.org/browser"},
        element_tag="browser:viewlet",
        identifying_attr="name",
        identifying_value=viewlet_name,
        snippet=snippet,
    )
    print(msg)

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".viewlets"):
            zcml_updater.add_include(".viewlets")
            zcml_updater.save()
            print(
                'Added <include package=".viewlets" /> to parent '
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
