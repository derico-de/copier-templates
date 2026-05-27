"""Pytest configuration and shared fixtures for copier-templates tests."""
import os
import shutil
import tempfile
from pathlib import Path

import pytest


# Ensure copier tasks can find tomlkit from the venv
# Copier runs tasks with system python3, not the venv python
@pytest.fixture(scope="session", autouse=True)
def setup_pythonpath():
    """Set PYTHONPATH so copier tasks can find venv packages like tomlkit."""
    venv_site_packages = Path(__file__).parent.parent / ".venv" / "lib"
    # Find the python version directory (e.g., python3.11)
    for python_dir in venv_site_packages.glob("python*/site-packages"):
        if python_dir.exists():
            existing = os.environ.get("PYTHONPATH", "")
            new_path = str(python_dir)
            if existing:
                os.environ["PYTHONPATH"] = f"{new_path}:{existing}"
            else:
                os.environ["PYTHONPATH"] = new_path
            break


@pytest.fixture
def temp_dir():
    """Create temporary directory for test output."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def copier_defaults():
    """Default answers for copier prompts."""
    return {
        "author_name": "Test Author",
        "author_email": "test@example.com",
    }


@pytest.fixture
def templates_dir():
    """Return the path to the templates directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def zope_setup_template(templates_dir):
    """Return path to zope-setup template."""
    return templates_dir / "zope-setup"


@pytest.fixture
def backend_addon_template(templates_dir):
    """Return path to backend_addon template."""
    return templates_dir / "backend_addon"


@pytest.fixture
def content_type_template(templates_dir):
    """Return path to content_type template."""
    return templates_dir / "content_type"


@pytest.fixture
def behavior_template(templates_dir):
    """Return path to behavior template."""
    return templates_dir / "behavior"


@pytest.fixture
def restapi_service_template(templates_dir):
    """Return path to restapi_service template."""
    return templates_dir / "restapi_service"


@pytest.fixture
def zope_instance_template(templates_dir):
    """Return path to zope_instance template."""
    return templates_dir / "zope_instance"


@pytest.fixture
def upgrade_step_template(templates_dir):
    """Return path to upgrade_step template."""
    return templates_dir / "upgrade_step"


@pytest.fixture
def vocabulary_template(templates_dir):
    """Return path to vocabulary template."""
    return templates_dir / "vocabulary"


@pytest.fixture
def indexer_template(templates_dir):
    """Return path to indexer template."""
    return templates_dir / "indexer"


@pytest.fixture
def subscriber_template(templates_dir):
    """Return path to subscriber template."""
    return templates_dir / "subscriber"


@pytest.fixture
def view_template(templates_dir):
    """Return path to view template."""
    return templates_dir / "view"


@pytest.fixture
def viewlet_template(templates_dir):
    """Return path to viewlet template."""
    return templates_dir / "viewlet"


@pytest.fixture
def form_template(templates_dir):
    """Return path to form template."""
    return templates_dir / "form"


@pytest.fixture
def portlet_template(templates_dir):
    """Return path to portlet template."""
    return templates_dir / "portlet"


@pytest.fixture
def controlpanel_template(templates_dir):
    """Return path to controlpanel template."""
    return templates_dir / "controlpanel"


@pytest.fixture
def site_initialization_template(templates_dir):
    """Return path to site_initialization template."""
    return templates_dir / "site_initialization"


@pytest.fixture
def theme_basic_template(templates_dir):
    """Return path to theme_basic template."""
    return templates_dir / "theme_basic"


@pytest.fixture
def theme_barceloneta_template(templates_dir):
    """Return path to theme_barceloneta template."""
    return templates_dir / "theme_barceloneta"


@pytest.fixture
def theme_template(templates_dir):
    """Return path to theme template."""
    return templates_dir / "theme"


@pytest.fixture
def mockup_pattern_template(templates_dir):
    """Return path to mockup_pattern template."""
    return templates_dir / "mockup_pattern"


@pytest.fixture
def svelte_app_template(templates_dir):
    """Return path to svelte_app template."""
    return templates_dir / "svelte_app"


@pytest.fixture
def language_template(templates_dir):
    """Return path to language template."""
    return templates_dir / "language"


@pytest.fixture(scope="session")
def prebuilt_addon_source(tmp_path_factory, backend_addon_session_template):
    """
    Generate a backend_addon once per test session.

    Returns the path to a read-only reference directory. Individual tests
    must copy it via :func:`tests.helpers.copy_tree` rather than mutating
    it directly.
    """
    from helpers import run_copier

    src = tmp_path_factory.mktemp("prebuilt_addon") / "mypackage"
    result = run_copier(
        backend_addon_session_template,
        src,
        data={"package_name": "collective.mypackage"},
    )
    assert result.returncode == 0, (
        f"Session backend_addon generation failed: {result.stderr}"
    )
    return src


@pytest.fixture(scope="session")
def backend_addon_session_template():
    """Session-scoped path to backend_addon template."""
    return Path(__file__).parent.parent / "backend_addon"


@pytest.fixture
def fresh_addon(temp_dir, prebuilt_addon_source):
    """
    A fresh copy of the prebuilt addon in this test's temp_dir.

    Cheap (a tree copy) compared to re-running copier for backend_addon.
    """
    from helpers import copy_tree

    dst = temp_dir / "mypackage"
    return copy_tree(prebuilt_addon_source, dst)
