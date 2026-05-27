"""End-to-end: a scaffolded addon must be ruff-clean out of the box.

Generates a backend addon plus a representative set of subtemplates and runs
``ruff check`` (the same lint the generated CI runs) on the result. This locks
in the contract that scaffolded code passes linting with zero hand-edits.
"""
import shutil
import subprocess
import sys

import pytest
from helpers import run_copier


def _ruff_available():
    return shutil.which("ruff") is not None


@pytest.mark.skipif(not _ruff_available(), reason="ruff not installed")
def test_generated_addon_is_ruff_clean(
    temp_dir,
    backend_addon_template,
    content_type_template,
    behavior_template,
    restapi_service_template,
    vocabulary_template,
    view_template,
    language_template,
):
    pkg = temp_dir / "mypackage"
    pkg_name = "collective.demo"

    def _run(template, **data):
        data.setdefault("package_name", pkg_name)
        result = run_copier(template, pkg, data=data)
        assert result.returncode == 0, f"copier failed: {result.stderr}"

    _run(backend_addon_template)
    # Globally addable + contained content types exercise both test paths.
    _run(content_type_template, content_type_name="Todos", global_allow=True)
    _run(
        content_type_template,
        content_type_name="Todo",
        global_allow=False,
        parent_content_type="Todos",
    )
    _run(behavior_template, behavior_name="IFeatured")
    _run(restapi_service_template, service_name="stats")
    _run(vocabulary_template, vocabulary_name="Priorities", vocabulary_type="simple")
    _run(view_template, view_name="my-view")
    _run(language_template, language_code="de", language_name="German")

    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=pkg,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        "Generated addon is not ruff-clean:\n"
        f"{result.stdout}\n{result.stderr}"
    )
