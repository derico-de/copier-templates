#!/usr/bin/env python3
"""Tasks for the svelte_app subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    AddonContext,
    find_addon_context,
    resolve_post_copy_context,
)
from utils.xml_updater import extend_configure_zcml  # noqa: E402


def validate(dest_path: str) -> None:
    dest = Path(dest_path)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(dest_path: str, svelte_app_name: str) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("svelte_apps", svelte_app_name):
        print(f"Registered Svelte app '{svelte_app_name}' in addon settings.")

    _register_svelte_static_resource(ctx)


def _register_svelte_static_resource(ctx: AddonContext) -> None:
    """Register the built-bundle directory as a plone static resource.

    The bundle registry entries point at ``++plone++<package>.svelte/...``;
    without this registration those resources are never served (bobtemplates
    parity). The directory is ``svelte_apps/static`` (the vite build output)
    rather than bobtemplates' ``svelte_apps``, which here contains the
    Python mount-point modules.
    """
    if not ctx.package_folder:
        return

    resource_name = f"{ctx.package_name}.svelte"
    parent_zcml = ctx.dest / f"src/{ctx.package_folder}/configure.zcml"
    snippet = (
        "  <plone:static\n"
        '      directory="svelte_apps/static"\n'
        '      type="plone"\n'
        f'      name="{resource_name}"\n'
        "      />\n"
    )
    _, msg = extend_configure_zcml(
        parent_zcml,
        ctx.package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="plone:static",
        identifying_attr="name",
        identifying_value=resource_name,
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
