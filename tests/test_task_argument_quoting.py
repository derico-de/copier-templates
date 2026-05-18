"""Regression: free-text task arguments must survive shell-special characters.

Copier ``_tasks`` previously interpolated values into a single-quoted shell
string, so any apostrophe (or other shell metacharacter) in a user-supplied
free-text field terminated the quoted argument and aborted the entire copier
run with ``/bin/sh: Syntax error: Unterminated quoted string``.

Tasks are now list-form (executed without a shell), so arbitrary text must
pass through untouched. This is exercised for every template that interpolates
a free-text field (description / title) into a task command — the bug class
that the original happy-path tests, which only ever used default descriptions,
failed to catch.
"""
import pytest
from helpers import run_copier

# Deliberately hostile value: the apostrophe is the original trigger; the rest
# are shell metacharacters / an injection-style payload that list-form tasks
# must treat as inert text. Kept free of ``& < > "`` so it is also safe to
# embed verbatim in the generated XML/docstring we assert against (those would
# break XML/quoting for unrelated reasons and muddy this regression).
HOSTILE = "Plone CT's (e.g. $(whoami)) | rm -rf / ; echo done"


@pytest.fixture
def addon_dir(temp_dir, backend_addon_template):
    """A parent backend addon for the subtemplates under test."""
    pkg = temp_dir / "mypackage"
    result = run_copier(
        backend_addon_template,
        pkg,
        data={"package_name": "collective.mypackage"},
    )
    assert result.returncode == 0, result.stderr
    return pkg


@pytest.mark.parametrize(
    "template_fixture, data, rel_output",
    [
        (
            "behavior_template",
            {
                "behavior_name": "IThing",
                "package_name": "collective.mypackage",
                "behavior_description": HOSTILE,
            },
            "src/collective/mypackage/behaviors/ithing.py",
        ),
        (
            "content_type_template",
            {
                "content_type_name": "Thing",
                "package_name": "collective.mypackage",
                "content_type_description": HOSTILE,
            },
            "src/collective/mypackage/content/thing.py",
        ),
        (
            "upgrade_step_template",
            {
                "upgrade_step_title": HOSTILE,
                "package_name": "collective.mypackage",
                "source_version": "1000",
                "destination_version": "1001",
            },
            "src/collective/mypackage/upgrades/v1001.py",
        ),
    ],
)
def test_free_text_task_argument_survives_shell_metacharacters(
    request, addon_dir, template_fixture, data, rel_output
):
    template = request.getfixturevalue(template_fixture)

    result = run_copier(template, addon_dir, data=data)

    assert result.returncode == 0, (
        f"{template_fixture} aborted on hostile free-text input:\n{result.stderr}"
    )
    output = addon_dir / rel_output
    assert output.exists(), f"{output} was not generated"
    assert HOSTILE in output.read_text(), (
        f"free-text value was mangled in {rel_output}"
    )
