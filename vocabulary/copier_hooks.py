#!/usr/bin/env python3
"""Tasks for the vocabulary subtemplate."""
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from exceptions import AddonContextError, CopierTemplateError  # noqa: E402
from hooks.addon_context import (  # noqa: E402
    find_addon_context,
    resolve_post_copy_context,
)
from utils.xml_updater import ParentZCMLUpdater, extend_configure_zcml  # noqa: E402


def validate(dest_path: str) -> None:
    """Validate that a parent backend_addon exists at ``dest_path``."""
    dest = Path(dest_path)
    context = find_addon_context(dest)
    if not context:
        raise AddonContextError(
            f"No parent addon detected at {dest}. "
            "This template must be run inside an existing backend_addon."
        )


def post_copy(
    dest_path: str,
    vocabulary_name: str,
    vocabulary_module: str = "",
    vocabulary_class: str = "",
) -> None:
    """Register the vocabulary in the parent addon.

    1. Record it under ``[tool.plone.backend_addon.settings.subtemplates]``
       (or ``bobtemplate.cfg [subtemplates]`` for legacy packages).
    2. Extend ``vocabularies/configure.zcml`` with the ``<utility>`` entry.
    3. Ensure ``<include package=".vocabularies" />`` in parent
       ``configure.zcml`` (idempotent).
    """
    ctx = resolve_post_copy_context(dest_path)
    if ctx is None or not ctx.package_folder:
        print(
            "Warning: could not detect parent addon (no pyproject.toml, "
            "bobtemplate.cfg, or setup.py). Skipping configuration updates."
        )
        return

    if ctx.register_subtemplate("vocabularies", vocabulary_name):
        print(f"Registered vocabulary '{vocabulary_name}' in addon settings.")

    dest = ctx.dest
    package_name = ctx.package_name
    package_folder = ctx.package_folder

    utility_name = f"{package_name}.{vocabulary_class or vocabulary_name}"
    component = f".{vocabulary_module}.{vocabulary_class or vocabulary_name}Factory"
    snippet = (
        "  <utility\n"
        f'      component="{component}"\n'
        f'      name="{utility_name}"\n'
        '      provides="zope.schema.interfaces.IVocabularyFactory"\n'
        "      />\n"
    )
    vocabs_zcml = dest / f"src/{package_folder}/vocabularies/configure.zcml"
    _, msg = extend_configure_zcml(
        vocabs_zcml,
        package_name or "package",
        namespaces={},
        element_tag="utility",
        identifying_attr="name",
        identifying_value=utility_name,
        snippet=snippet,
    )
    print(msg)

    parent_zcml = dest / f"src/{package_folder}/configure.zcml"
    if parent_zcml.exists():
        zcml_updater = ParentZCMLUpdater(parent_zcml)
        if not zcml_updater.has_include(".vocabularies"):
            zcml_updater.add_include(".vocabularies")
            zcml_updater.save()
            print(
                'Added <include package=".vocabularies" /> to parent '
                "configure.zcml."
            )


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: copier_hooks.py <command> [args...]")
        print("Commands: validate, post_copy")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command == "validate":
            if len(sys.argv) < 3:
                print("Usage: copier_hooks.py validate <dest_path>")
                sys.exit(1)
            validate(sys.argv[2])
        elif command == "post_copy":
            if len(sys.argv) < 4:
                print(
                    "Usage: copier_hooks.py post_copy <dest_path> <vocabulary_name> ..."
                )
                sys.exit(1)
            post_copy(*sys.argv[2:])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except CopierTemplateError as e:
        print("\n" + "=" * 60)
        print(f"ERROR: {e}")
        print("=" * 60)
        print("\nFirst create an addon with:")
        print("  copier copy <templates>/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory:")
        print("  cd my-addon")
        print("  copier copy <templates>/vocabulary .")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
