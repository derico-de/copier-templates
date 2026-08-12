#!/usr/bin/env python3
"""Tasks for the theme_barceloneta subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    AddonContext,
    find_addon_context,
    resolve_post_copy_context,
)
from hooks.git_check import warn_git_unclean  # noqa: E402
from utils.xml_updater import extend_configure_zcml  # noqa: E402


def validate(dest_path: str) -> None:
    dest = Path(dest_path)
    warn_git_unclean(dest)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(dest_path: str, theme_name: str) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("themes", theme_name):
        print(f"Registered theme '{theme_name}' in addon settings.")

    _register_theme_static_resource(ctx, theme_name)

    ctx.add_profile_dependency("profile-plone.app.theming:default")


def _register_theme_static_resource(ctx: AddonContext, theme_name: str) -> None:
    if not ctx.package_folder:
        return

    theme_id = theme_name.lower().replace(" ", "-").replace("_", "-")
    parent_zcml = ctx.dest / f"src/{ctx.package_folder}/configure.zcml"
    snippet = (
        "  <plone:static\n"
        '      directory="theme"\n'
        f'      name="{theme_id}"\n'
        '      type="theme"\n'
        "      />\n"
    )
    _, msg = extend_configure_zcml(
        parent_zcml,
        ctx.package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="plone:static",
        identifying_attr="name",
        identifying_value=theme_id,
        snippet=snippet,
    )
    print(msg)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: copier_hooks.py <command> [args...]")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command == "validate":
            validate(sys.argv[2])
        elif command == "post_copy":
            post_copy(sys.argv[2], sys.argv[3])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except CopierTemplateError as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
