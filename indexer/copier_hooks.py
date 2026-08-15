#!/usr/bin/env python3
"""Tasks for the indexer subtemplate."""
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


def post_copy(dest_path: str, indexer_name: str) -> None:
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("indexers", indexer_name):
        print(f"Registered indexer '{indexer_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    # The adapters live in a per-indexer <name>.zcml (bobtemplates parity);
    # indexers/configure.zcml only includes it.
    indexers_zcml = dest / f"src/{package_folder}/indexers/configure.zcml"
    _, msg = extend_configure_zcml(
        indexers_zcml,
        package_name or "package",
        namespaces={},
        element_tag="include",
        identifying_attr="file",
        identifying_value=f"{indexer_name}.zcml",
        snippet=f'  <include file="{indexer_name}.zcml" />\n',
    )
    print(msg)

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".indexers"):
            zcml_updater.add_include(".indexers")
            zcml_updater.save()
            print(
                'Added <include package=".indexers" /> to parent '
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
            post_copy(sys.argv[2], sys.argv[3])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except CopierTemplateError as e:
        print(f"\nERROR: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
