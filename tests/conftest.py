"""Pytest configuration and shared fixtures for copier-templates tests."""
import shutil
import tempfile
from pathlib import Path

import pytest


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
