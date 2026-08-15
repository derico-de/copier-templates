#!/usr/bin/env python3
"""Tasks for the controlpanel subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from utils.xml_updater import (  # noqa: E402
    ControlPanelXMLUpdater,
    ParentZCMLUpdater,
    extend_configure_zcml,
)


def validate(dest_path: str) -> None:
    dest = Path(dest_path)
    if not find_addon_context(dest):
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(
    dest_path: str,
    controlpanel_name: str,
    controlpanel_url_id: str = "",
    controlpanel_module: str = "",
    controlpanel_title: str = "",
) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("controlpanels", controlpanel_name):
        print(
            f"Registered controlpanel '{controlpanel_name}' in addon settings."
        )

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    cp_zcml = dest / f"src/{package_folder}/controlpanels/configure.zcml"

    # The subpackage ships its own configure.zcml (bobtemplates parity);
    # controlpanels/configure.zcml only includes it.
    include_snippet = f'  <include package=".{controlpanel_module}" />\n'
    _, msg = extend_configure_zcml(
        cp_zcml,
        package_name or "package",
        namespaces={"browser": "http://namespaces.zope.org/browser"},
        element_tag="include",
        identifying_attr="package",
        identifying_value=f".{controlpanel_module}",
        snippet=include_snippet,
    )
    print(msg)

    # Idempotently merge the configlet into profiles/default/controlpanel.xml
    controlpanel_xml = (
        dest / f"src/{package_folder}/profiles/default/controlpanel.xml"
    )
    cp_updater = ControlPanelXMLUpdater(controlpanel_xml)
    if cp_updater.add_configlet(
        package_name or "package",
        action_id=controlpanel_url_id,
        title=controlpanel_title or controlpanel_name,
    ):
        print(f"Added configlet '{controlpanel_url_id}' to controlpanel.xml.")
    else:
        print(f"Configlet '{controlpanel_url_id}' already in controlpanel.xml.")

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".controlpanels"):
            zcml_updater.add_include(".controlpanels")
            zcml_updater.save()
            print(
                'Added <include package=".controlpanels" /> to parent '
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
