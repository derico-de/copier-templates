#!/usr/bin/env python3
"""Tasks for the portlet subtemplate."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from utils.xml_updater import (  # noqa: E402
    ParentZCMLUpdater,
    PortletsXMLUpdater,
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
    portlet_name: str,
    portlet_module: str = "",
    portlet_description: str = "A custom portlet",
) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("portlets", portlet_name):
        print(f"Registered portlet '{portlet_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    registration_name = f"{package_name}.{portlet_name}"
    snippet = (
        "  <plone:portlet\n"
        f'      name="{registration_name}"\n'
        f'      interface=".{portlet_module}.I{portlet_name}Portlet"\n'
        f'      assignment=".{portlet_module}.Assignment"\n'
        '      view_permission="zope2.View"\n'
        '      edit_permission="cmf.ManagePortal"\n'
        f'      renderer=".{portlet_module}.Renderer"\n'
        f'      addview=".{portlet_module}.AddForm"\n'
        f'      editview=".{portlet_module}.EditForm"\n'
        "      />\n"
    )
    portlets_zcml = dest / f"src/{package_folder}/portlets/configure.zcml"
    _, msg = extend_configure_zcml(
        portlets_zcml,
        package_name or "package",
        namespaces={"plone": "http://namespaces.plone.org/plone"},
        element_tag="plone:portlet",
        identifying_attr="name",
        identifying_value=registration_name,
        snippet=snippet,
    )
    print(msg)

    # Idempotently merge the GS portlet entry into profiles/default/portlets.xml
    portlets_xml = dest / f"src/{package_folder}/profiles/default/portlets.xml"
    portlets_updater = PortletsXMLUpdater(portlets_xml)
    if portlets_updater.add_portlet(
        package_name or "package",
        addview=registration_name,
        title=portlet_name,
        description=portlet_description,
        portlet_module=portlet_module,
    ):
        print(f"Added portlet '{registration_name}' to portlets.xml.")
    else:
        print(f"Portlet '{registration_name}' already in portlets.xml.")

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".portlets"):
            zcml_updater.add_include(".portlets")
            zcml_updater.save()
            print(
                'Added <include package=".portlets" /> to parent '
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
