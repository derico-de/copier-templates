"""Per-field value matrix: every free-text question across every template.

This module is the data-driven counterpart to the per-template happy-path
tests. For each template that exposes a free-text field (description, title,
display name, etc.) it runs the template with that field set to a deliberately
hostile string (apostrophes, ``$``, backticks, pipes, semicolons, parentheses,
spaces, unicode) and asserts:

1. Copier exits with status 0 (no shell-quoting / Jinja / hook crash).
2. The hostile value lands verbatim somewhere under the generated tree.

The matrix is the protection against the original ``_tasks`` shell-quoting
bug — an apostrophe in ``behavior_description`` aborted the whole copier run
because every prior test relied on copier defaults for description fields.

The hostile value stays clear of ``<``, ``>``, ``"``, ``&`` so it can also be
embedded in XML attribute / element content that some templates emit (FTI,
portlet XML, controlpanel XML, registry XML). Those would break unrelated
XML quoting and muddy the signal we care about here.

In addition, ``TestInProcessCopierApi`` runs the same templates through the
in-process ``copier.run_copy`` Python API — the same entry point plonecli
uses — to make sure both the CLI and the library path stay regression-free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest
from helpers import run_copier

# Apostrophe is the original trigger of the _tasks shell-quoting bug. The
# rest is shell-significant noise an injection-style payload that list-form
# tasks must treat as inert text. ``< > " &`` are excluded because some
# templates embed the value into XML attribute / element content where those
# characters legitimately need escaping and would muddy this regression.
HOSTILE = "Plone CT's (e.g. $(whoami)) | rm -rf / ; echo done — ünïcödé"


@dataclass(frozen=True)
class TemplateSpec:
    """A row in the per-field matrix.

    Attributes:
        name: short label for parametrize ids.
        fixture: name of the pytest fixture that returns the template path.
        base_data: minimum --data answers required to run the template.
        free_text_fields: questions that must accept hostile free text.
        parent_template: fixture name of a parent template to scaffold first
            (sub-templates), or ``None`` for main templates.
        parent_data: --data answers for the parent scaffold.
        parent_dir_name: directory name for the parent scaffold inside the
            test temp dir.
    """

    name: str
    fixture: str
    base_data: dict[str, str]
    free_text_fields: tuple[str, ...]
    parent_template: str | None = None
    parent_data: dict[str, str] = field(default_factory=dict)
    parent_dir_name: str = "mypackage"


# Shared parent-addon scaffold for every backend_addon sub-template.
_ADDON_PARENT = {
    "parent_template": "backend_addon_template",
    "parent_data": {"package_name": "collective.mypackage"},
    "parent_dir_name": "mypackage",
}

# Shared parent-project scaffold for zope_instance.
_PROJECT_PARENT = {
    "parent_template": "zope_setup_template",
    "parent_data": {"project_name": "my-project"},
    "parent_dir_name": "my-project",
}

SPECS: tuple[TemplateSpec, ...] = (
    # ------------------------- Main templates -------------------------
    TemplateSpec(
        name="backend_addon",
        fixture="backend_addon_template",
        base_data={"package_name": "collective.mypackage"},
        free_text_fields=("package_title", "package_description", "author_name"),
    ),
    TemplateSpec(
        name="zope-setup",
        fixture="zope_setup_template",
        base_data={"project_name": "my-project"},
        free_text_fields=("project_title", "project_description", "author_name"),
    ),
    # ------------------------ backend_addon subs ----------------------
    TemplateSpec(
        name="behavior",
        fixture="behavior_template",
        base_data={
            "behavior_name": "IThing",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("behavior_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="content_type",
        fixture="content_type_template",
        base_data={
            "content_type_name": "Thing",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("content_type_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="controlpanel",
        fixture="controlpanel_template",
        base_data={
            "controlpanel_name": "MyFeatured",
            "package_name": "collective.mypackage",
        },
        # controlpanel_title lands in an XML attribute; ``"`` would break it.
        # The HOSTILE constant deliberately excludes ``"`` for that reason.
        free_text_fields=("controlpanel_title", "controlpanel_description"),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="form",
        fixture="form_template",
        base_data={
            "form_name": "my-form",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("form_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="indexer",
        fixture="indexer_template",
        base_data={
            "indexer_name": "my_index",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("indexer_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="mockup_pattern",
        fixture="mockup_pattern_template",
        base_data={
            "pattern_name": "my-pattern",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("pattern_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="portlet",
        fixture="portlet_template",
        base_data={
            "portlet_name": "Weather",
            "package_name": "collective.mypackage",
        },
        # portlet_description lands in XML attribute (portlets.xml); HOSTILE
        # is XML-attribute-safe by construction.
        free_text_fields=("portlet_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="restapi_service",
        fixture="restapi_service_template",
        base_data={
            "service_name": "stats",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("service_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="site_initialization",
        fixture="site_initialization_template",
        base_data={"package_name": "collective.mypackage"},
        free_text_fields=("site_name",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="subscriber",
        fixture="subscriber_template",
        base_data={
            "subscriber_handler_name": "obj_modified_do_something",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("subscriber_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="svelte_app",
        fixture="svelte_app_template",
        base_data={
            "svelte_app_name": "my-app",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("svelte_app_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="theme",
        fixture="theme_template",
        base_data={
            "theme_name": "My Theme",
            "package_name": "collective.mypackage",
        },
        # theme_name is NOT in free_text_fields because it derives ``theme_id``
        # which becomes a file path / URL slug; hostile chars would mangle
        # generated file names rather than test the _tasks/Jinja path.
        free_text_fields=("theme_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="theme_basic",
        fixture="theme_basic_template",
        base_data={
            "theme_name": "My Theme",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("theme_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="theme_barceloneta",
        fixture="theme_barceloneta_template",
        base_data={
            "theme_name": "My Theme",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("theme_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="upgrade_step",
        fixture="upgrade_step_template",
        base_data={
            "upgrade_step_title": "Add catalog index",
            "package_name": "collective.mypackage",
            "source_version": "1000",
            "destination_version": "1001",
        },
        # upgrade_step_title is itself free text (and also feeds _tasks); test
        # it explicitly alongside the description.
        free_text_fields=("upgrade_step_title", "upgrade_step_description"),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="view",
        fixture="view_template",
        base_data={
            "view_name": "my-view",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("view_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="viewlet",
        fixture="viewlet_template",
        base_data={
            "viewlet_name": "myviewlet",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("viewlet_description",),
        **_ADDON_PARENT,
    ),
    TemplateSpec(
        name="vocabulary",
        fixture="vocabulary_template",
        base_data={
            "vocabulary_name": "AvailableThings",
            "package_name": "collective.mypackage",
        },
        free_text_fields=("vocabulary_description",),
        **_ADDON_PARENT,
    ),
    # ------------------------- zope-setup subs ------------------------
    TemplateSpec(
        name="zope_instance",
        fixture="zope_instance_template",
        base_data={"instance_name": "instance1", "port": "8081"},
        free_text_fields=(),  # no free-text-only fields; covered via base_data
        **_PROJECT_PARENT,
    ),
)


# Flattened list of (spec, field_name) for parametrize, only including specs
# that have at least one free-text field.
_FREE_TEXT_CASES: list[tuple[TemplateSpec, str]] = [
    (spec, field_name)
    for spec in SPECS
    if spec.free_text_fields
    for field_name in spec.free_text_fields
]


def _scaffold_parent(request, spec: TemplateSpec, temp_dir: Path) -> Path:
    """Scaffold the parent template if the spec needs one; return target dir."""
    if spec.parent_template is None:
        return temp_dir / spec.parent_dir_name
    parent_path = request.getfixturevalue(spec.parent_template)
    parent_dir = temp_dir / spec.parent_dir_name
    result = run_copier(parent_path, parent_dir, data=spec.parent_data)
    assert result.returncode == 0, (
        f"Parent scaffold ({spec.parent_template}) failed for {spec.name}:\n"
        f"{result.stderr}"
    )
    return parent_dir


def _find_in_tree(root: Path, needle: str) -> list[Path]:
    """Return text files under ``root`` whose contents contain ``needle``."""
    hits: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if needle in text:
            hits.append(p)
    return hits


@pytest.mark.parametrize(
    "spec,field_name",
    _FREE_TEXT_CASES,
    ids=[f"{spec.name}::{field_name}" for spec, field_name in _FREE_TEXT_CASES],
)
def test_free_text_field_accepts_hostile_input(
    request, temp_dir, spec: TemplateSpec, field_name: str
):
    """Every free-text field must survive shell- and unicode-hostile input.

    Sets a single free-text field to ``HOSTILE`` (keeping the rest of the
    template's base_data intact), runs copier, and verifies:

    * The run exits 0 — no shell-quoting failure in ``_tasks``, no Jinja
      crash, no hook traceback.
    * The literal ``HOSTILE`` value lands somewhere in the generated tree —
      no silent mangling by intermediate quoting.
    """
    target_dir = _scaffold_parent(request, spec, temp_dir)
    template_path = request.getfixturevalue(spec.fixture)

    data = dict(spec.base_data)
    data[field_name] = HOSTILE

    result = run_copier(template_path, target_dir, data=data)
    assert result.returncode == 0, (
        f"{spec.name}::{field_name} aborted on hostile input:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    # Fields that land in XML are escaped there (e.g. ' -> &#39;), which is
    # a faithful landing, not mangling.
    from markupsafe import escape as xml_escaped

    hits = _find_in_tree(target_dir, HOSTILE) or _find_in_tree(
        target_dir, str(xml_escaped(HOSTILE))
    )
    assert hits, (
        f"{spec.name}::{field_name} did not land in any generated file. "
        "Either the field is unused or it was mangled by intermediate "
        f"quoting/escaping. Searched: {target_dir}"
    )


@pytest.mark.parametrize(
    "spec",
    SPECS,
    ids=[spec.name for spec in SPECS],
)
def test_template_runs_with_defaults(request, temp_dir, spec: TemplateSpec):
    """Every template must run cleanly with the minimum required answers.

    Complements the hostile-input matrix: this guards the "no custom input"
    code path (which was the only path tested before the _tasks bug shipped).
    """
    target_dir = _scaffold_parent(request, spec, temp_dir)
    template_path = request.getfixturevalue(spec.fixture)

    result = run_copier(template_path, target_dir, data=spec.base_data)
    assert result.returncode == 0, (
        f"{spec.name} failed with default answers:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )


class TestInProcessCopierApi:
    """Mirror the plonecli entry point: ``copier.run_copy()`` not the CLI.

    The CLI path goes through ``argparse`` -> ``copier copy`` -> shell. The
    Python API path used by plonecli (and other library users) is
    ``copier.run_copy(src_path, dst_path, data=..., defaults=True, ...)``.
    Both paths share most of the copier core, but ``_tasks`` execution and
    answer rendering differ enough that bugs can hide in one and not the
    other. These tests provide the in-process baseline.
    """

    def test_backend_addon_via_python_api(self, temp_dir, backend_addon_template):
        """Main template runs cleanly via ``copier.run_copy``."""
        import copier

        dst = temp_dir / "mypackage"
        copier.run_copy(
            str(backend_addon_template),
            str(dst),
            data={
                "package_name": "collective.mypackage",
                "package_description": HOSTILE,
            },
            defaults=True,
            overwrite=True,
            unsafe=True,
        )

        assert (dst / "pyproject.toml").exists()
        hits = _find_in_tree(dst, HOSTILE)
        assert hits, "package_description with hostile chars not found in API run"

    def test_behavior_subtemplate_via_python_api(
        self, temp_dir, backend_addon_template, behavior_template
    ):
        """Sub-template runs cleanly via ``copier.run_copy`` on top of parent."""
        import copier

        dst = temp_dir / "mypackage"
        # Parent: backend_addon via the same API path.
        copier.run_copy(
            str(backend_addon_template),
            str(dst),
            data={"package_name": "collective.mypackage"},
            defaults=True,
            overwrite=True,
            unsafe=True,
        )
        # Sub: behavior with hostile description.
        copier.run_copy(
            str(behavior_template),
            str(dst),
            data={
                "behavior_name": "IThing",
                "package_name": "collective.mypackage",
                "behavior_description": HOSTILE,
            },
            defaults=True,
            overwrite=True,
            unsafe=True,
        )

        behavior_file = dst / "src/collective/mypackage/behaviors/thing.py"
        assert behavior_file.exists()
        assert HOSTILE in behavior_file.read_text()


# XML-structural characters that must be escaped wherever free text lands in
# generated XML/ZCML (profile files, FTI, registrations). Complements HOSTILE,
# which deliberately excludes them.
XML_HOSTILE = "Desc & <tag> \"quoted\" 'apo' &amp; more"

# (template name, field) pairs whose free-text answer can land in XML/ZCML.
# Name fields (content_type_name, portlet_name, theme_name, ...) are excluded
# for the same reason as in SPECS: they derive Python/file identifiers, so
# XML-structural characters would break the generated code before any XML
# escaping is exercised.
_XML_FIELD_CASES: list[tuple[str, str]] = [
    ("backend_addon", "package_title"),
    ("backend_addon", "package_description"),
    ("behavior", "behavior_description"),
    ("content_type", "content_type_description"),
    ("controlpanel", "controlpanel_title"),
    ("controlpanel", "controlpanel_description"),
    ("portlet", "portlet_description"),
    ("site_initialization", "site_name"),
    ("upgrade_step", "upgrade_step_title"),
    ("upgrade_step", "upgrade_step_description"),
]

_SPEC_BY_NAME = {spec.name: spec for spec in SPECS}


@pytest.mark.parametrize(
    "spec_name,field_name",
    _XML_FIELD_CASES,
    ids=[f"{name}::{field}" for name, field in _XML_FIELD_CASES],
)
def test_xml_structural_chars_stay_wellformed(
    request, temp_dir, spec_name: str, field_name: str
):
    """XML-structural characters in free text must not break generated XML.

    Runs the template with ``&``, ``<``, ``>``, ``"``, ``'`` in the given
    field and asserts the run exits 0 and every generated ``.xml``/``.zcml``
    file still parses.
    """
    import xml.etree.ElementTree as ET

    spec = _SPEC_BY_NAME[spec_name]
    target_dir = _scaffold_parent(request, spec, temp_dir)
    template_path = request.getfixturevalue(spec.fixture)

    data = dict(spec.base_data)
    data[field_name] = XML_HOSTILE

    result = run_copier(template_path, target_dir, data=data)
    assert result.returncode == 0, (
        f"{spec.name}::{field_name} aborted on XML-hostile input:\n"
        f"stdout:\n{result.stdout}\n"
        f"stderr:\n{result.stderr}"
    )

    unparsable = []
    for path in target_dir.rglob("*"):
        if not path.is_file() or path.suffix not in (".xml", ".zcml"):
            continue
        try:
            ET.parse(path)
        except ET.ParseError as exc:
            unparsable.append(f"{path}: {exc}")
    assert not unparsable, (
        f"{spec.name}::{field_name} produced malformed XML:\n"
        + "\n".join(unparsable)
    )
