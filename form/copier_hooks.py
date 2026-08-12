#!/usr/bin/env python3
"""Tasks for the form subtemplate."""
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
    form_name: str,
    form_for: str = "*",
    form_module: str = "",
    form_class_name: str = "",
) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("forms", form_name):
        print(f"Registered form '{form_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    # bobtemplates parity: forms are management-permission protected and
    # bound to the package's browser layer.
    layer = ctx.browser_layer()
    lines = [
        "  <browser:page",
        f'      name="{form_name}"',
        f'      for="{form_for}"',
        f'      class=".{form_module}.{form_class_name}"',
        '      permission="cmf.ManagePortal"',
    ]
    if layer:
        lines.append(f'      layer="{layer}"')
    lines.append("      />")
    snippet = "\n".join(lines) + "\n"
    forms_zcml = dest / f"src/{package_folder}/forms/configure.zcml"
    _, msg = extend_configure_zcml(
        forms_zcml,
        package_name or "package",
        namespaces={"browser": "http://namespaces.zope.org/browser"},
        element_tag="browser:page",
        identifying_attr="name",
        identifying_value=form_name,
        snippet=snippet,
    )
    print(msg)

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".forms"):
            zcml_updater.add_include(".forms")
            zcml_updater.save()
            print(
                'Added <include package=".forms" /> to parent '
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
