#!/usr/bin/env python3
"""Tasks for upgrade_step subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from hooks.git_check import warn_git_unclean  # noqa: E402
from utils.xml_updater import (  # noqa: E402
    MetadataXMLUpdater,
    ParentZCMLUpdater,
    UpgradeZCMLUpdater,
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
    upgrade_step_title: str,
    upgrade_step_description: str,
    source_version: str,
    destination_version: str,
) -> None:
    """Wire the new upgrade step files into the addon configuration.

    Works for both modern (pyproject.toml) and legacy (bobtemplate.cfg /
    setup.py) packages.
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if not ctx.package_folder:
        print("Warning: could not determine package_folder. Skipping updates.")
        return

    # Add include for per-step ZCML in upgrades/configure.zcml
    zcml_path = ctx.dest / f"src/{ctx.package_folder}/upgrades/configure.zcml"
    zcml_updater = UpgradeZCMLUpdater(zcml_path)
    zcml_updater.create_if_missing(ctx.package_name or "package")
    step_zcml = f"{destination_version}.zcml"
    if not zcml_updater.has_file_include(step_zcml):
        zcml_updater.add_file_include(step_zcml)
        zcml_updater.save()
        print(
            f"Updated {zcml_path.relative_to(ctx.dest)} with "
            f'<include file="{step_zcml}" />.'
        )
    else:
        print(
            f'Include for "{step_zcml}" already exists in '
            f"{zcml_path.relative_to(ctx.dest)}."
        )

    # Add include for upgrades subpackage in parent configure.zcml
    parent_zcml = ctx.dest / f"src/{ctx.package_folder}/configure.zcml"
    if parent_zcml.exists():
        parent_updater = ParentZCMLUpdater(parent_zcml)
        if not parent_updater.has_include(".upgrades"):
            parent_updater.add_include(".upgrades")
            parent_updater.save()
            print(
                'Added <include package=".upgrades" /> to parent '
                "configure.zcml."
            )

    # Bump profile version in metadata.xml
    metadata_path = (
        ctx.dest / f"src/{ctx.package_folder}/profiles/default/metadata.xml"
    )
    metadata_updater = MetadataXMLUpdater(metadata_path)
    current = metadata_updater.get_version()
    if current and current != destination_version:
        metadata_updater.set_version(destination_version)
        print(
            f"Updated profile version in metadata.xml: "
            f"{current} -> {destination_version}."
        )
    elif not current:
        print("Warning: Could not read current profile version from metadata.xml.")


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
            if len(sys.argv) < 7:
                print(
                    "Usage: tasks.py post_copy <dest_path> <title> <description> "
                    "<source_version> <destination_version>"
                )
                sys.exit(1)
            post_copy(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except CopierTemplateError as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print("\nFirst create an addon with:")
        print(
            "  copier copy ~/.copier-templates/plone-copier-templates/backend_addon my-addon"
        )
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-addon")
        print(
            "  copier copy ~/.copier-templates/plone-copier-templates/upgrade_step ."
        )
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
