#!/usr/bin/env python3
"""Tasks for the svelte_app subtemplate."""
import re
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
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml  # noqa: E402

SVELTE_APP_NAME = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")
RESERVED_CUSTOM_ELEMENT_NAMES = {
    "annotation-xml",
    "color-profile",
    "font-face",
    "font-face-format",
    "font-face-name",
    "font-face-src",
    "font-face-uri",
    "missing-glyph",
}


def validate(
    dest_path: str,
    svelte_app_name: str,
    svelte_app_custom_element: str,
) -> None:
    dest = Path(dest_path)
    warn_git_unclean(dest)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )
    if not SVELTE_APP_NAME.fullmatch(svelte_app_name):
        raise CopierTemplateError(
            "Svelte app name must use lowercase kebab-case."
        )
    custom_element = svelte_app_custom_element.lower() == "true"
    if custom_element and "-" not in svelte_app_name:
        raise CopierTemplateError(
            "A custom element name must contain a hyphen."
        )
    if custom_element and svelte_app_name in RESERVED_CUSTOM_ELEMENT_NAMES:
        raise CopierTemplateError(
            "This custom element name is reserved by HTML."
        )


def post_copy(
    dest_path: str,
    svelte_app_name: str,
    svelte_app_module: str,
    svelte_app_class: str,
) -> None:
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
    _register_svelte_view(
        ctx,
        svelte_app_name,
        svelte_app_module,
        svelte_app_class,
    )


def _register_svelte_view(
    ctx: AddonContext,
    app_name: str,
    app_module: str,
    app_class: str,
) -> None:
    """Register the browser view that renders the Svelte mount point."""
    if not ctx.package_folder:
        return

    package_folder = ctx.package_folder
    views_zcml = ctx.dest / f"src/{package_folder}/svelte_apps/configure.zcml"
    lines = [
        "  <browser:page",
        f'      name="{app_name}"',
        '      for="*"',
        f'      class=".{app_module}.{app_class}View"',
        '      permission="zope2.View"',
    ]
    layer = ctx.browser_layer()
    if layer:
        lines.append(f'      layer="{layer}"')
    lines.append("      />")
    snippet = "\n".join(lines) + "\n"
    _, msg = extend_configure_zcml(
        views_zcml,
        ctx.package_name or "package",
        namespaces={"browser": "http://namespaces.zope.org/browser"},
        element_tag="browser:page",
        identifying_attr="name",
        identifying_value=app_name,
        snippet=snippet,
    )
    print(msg)

    parent_zcml = ctx.dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        updater = ParentZCMLUpdater(parent_zcml)
        if not updater.has_include(".svelte_apps"):
            updater.add_include(".svelte_apps")
            updater.save()
            print(
                'Added <include package=".svelte_apps" /> to parent '
                "configure.zcml."
            )


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
            validate(*sys.argv[2:])
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
