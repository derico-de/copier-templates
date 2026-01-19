# Multi-Template Copier Repository Plan

## Overview

Create a multi-template Copier repository that modernizes bobtemplates.plone with composable templates.

**Key Architectural Principles:**

1. **backend_addon is INDEPENDENT** - Not a subtemplate of zope-setup
2. **Subtemplates belong to backend_addon** - content_type, behavior, restapi_service modify an existing addon
3. **TDD approach** - Write tests first, then implement
4. **Custom pyproject.toml namespaces** for settings persistence

---

## Development Approach: TDD

All templates developed test-first:

```
1. Write test defining expected behavior
2. Run test (should fail)
3. Implement template to pass test
4. Refactor
5. Repeat
```

### Test Categories

| Test Type       | Description                                            |
| --------------- | ------------------------------------------------------ |
| **Isolated**    | Test single template in isolation                      |
| **Combination** | Test backend_addon + subtemplate(s) together           |
| **Integration** | Test full workflow (zope-setup + addon + subtemplates) |

---

## Template Architecture

### Hierarchy & Relationships

```
INDEPENDENT TEMPLATES:
├── zope-setup              → Creates Plone/Zope project structure
└── backend_addon           → Creates standalone addon package
                             (can be used WITHOUT zope-setup)

SUBTEMPLATES OF backend_addon:
├── content_type            → Adds Dexterity content type to addon
├── behavior                → Adds Dexterity behavior to addon
└── restapi_service         → Adds REST API endpoint to addon
```

### Subtemplate Detection

Subtemplates detect their parent addon via:

1. `.copier-answers.backend-addon.*.yml` file in current directory
2. `[tool.plone.backend_addon.settings]` section in pyproject.toml

---

## Custom Namespaces in pyproject.toml

### Project Settings (zope-setup)

```toml
[tool.plone.project.settings]
plone_version = "6.1.1"
distribution = "plone.volto"
db_storage = "direct"
created_at = "2024-01-18"
```

### Addon Settings (backend_addon)

```toml
[tool.plone.backend_addon.settings]
package_name = "collective.myaddon"
package_folder = "collective/myaddon"
plone_version = "6.1"
is_headless = false
author_name = "John Doe"
author_email = "john@example.com"

# Subtemplates register themselves here:
[tool.plone.backend_addon.settings.subtemplates]
content_types = ["Document", "News Item"]
behaviors = ["IMyBehavior"]
services = ["@my-endpoint"]
```

**Why Custom Namespaces:**

- Subtemplates can read parent addon context without re-asking questions
- Settings persist across template updates
- Clear separation between project vs addon configuration

---

## Repository Structure

```
copier-templates/
├── pyproject.toml                   # Dev dependencies (pytest, copier, tomlkit)
├── README.md
│
├── tests/                           # TDD: All tests
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── helpers.py                   # Test utilities (run_copier, assert_file_exists)
│   ├── test_zope_setup.py           # Isolated zope-setup tests
│   ├── test_backend_addon.py        # Isolated backend_addon tests
│   ├── test_content_type.py         # content_type requires parent addon
│   ├── test_behavior.py             # behavior requires parent addon
│   ├── test_restapi_service.py      # restapi_service requires parent addon
│   └── test_combinations.py         # Multi-subtemplate scenarios
│       # - addon + content_type + behavior
│       # - addon + all subtemplates
│       # - zope-setup + addon + subtemplates (full stack)
│
├── shared/                          # Shared utilities
│   ├── __init__.py
│   ├── hooks/
│   │   ├── __init__.py
│   │   └── addon_context.py         # Detect parent addon for subtemplates
│   └── utils/
│       ├── __init__.py
│       └── pyproject_updater.py     # Modify pyproject.toml safely
│
├── zope-setup/                      # INDEPENDENT TEMPLATE
│   ├── copier.yml
│   └── template/
│       ├── {{_copier_conf.answers_file}}.jinja
│       ├── README.md.jinja
│       ├── pyproject.toml.jinja     # Includes [tool.plone.project.settings]
│       ├── tasks.py.jinja           # Generated invoke tasks
│       └── instance/
│           └── etc/
│               ├── zope.conf.tpl.jinja
│               └── zope.ini.jinja
│
├── backend_addon/                   # INDEPENDENT TEMPLATE
│   ├── copier.yml
│   └── template/
│       ├── {{_copier_conf.answers_file}}.jinja
│       ├── pyproject.toml.jinja     # Includes [tool.plone.backend_addon.settings]
│       ├── README.md.jinja
│       ├── CHANGELOG.md.jinja
│       ├── tests/
│       │   ├── __init__.py
│       │   ├── conftest.py.jinja
│       │   └── test_setup.py.jinja
│       └── src/{{_package_folder}}/
│           ├── __init__.py.jinja
│           ├── configure.zcml.jinja
│           ├── testing.py.jinja
│           ├── setuphandlers.py.jinja
│           └── profiles/
│               ├── default/metadata.xml.jinja
│               └── uninstall/metadata.xml.jinja
│
├── content_type/                    # SUBTEMPLATE OF backend_addon
│   ├── copier.yml                   # Reads addon context, validates parent exists
│   ├── tasks.py                     # Registers in parent's configure.zcml
│   └── template/
│       └── src/{{package_folder}}/
│           ├── content/
│           │   ├── __init__.py.jinja
│           │   ├── configure.zcml.jinja
│           │   └── {{_content_type_module}}.py.jinja
│           └── profiles/default/
│               ├── types.xml.jinja
│               └── types/{{_content_type_class}}.xml.jinja
│
├── behavior/                        # SUBTEMPLATE OF backend_addon
│   ├── copier.yml
│   ├── tasks.py
│   └── template/
│       └── src/{{package_folder}}/
│           └── behaviors/
│               ├── __init__.py.jinja
│               ├── configure.zcml.jinja
│               └── {{_behavior_module}}.py.jinja
│
└── restapi_service/                 # SUBTEMPLATE OF backend_addon
    ├── copier.yml
    ├── tasks.py
    └── template/
        └── src/{{package_folder}}/
            └── services/
                ├── __init__.py.jinja
                ├── configure.zcml.jinja
                └── {{_service_module}}.py.jinja
```

---

## Test Strategy

### Test File: tests/conftest.py

```python
import pytest
import tempfile
import shutil
from pathlib import Path
import subprocess


@pytest.fixture
def temp_dir():
    """Create temporary directory for test output."""
    d = tempfile.mkdtemp()
    yield Path(d)
    shutil.rmtree(d)


@pytest.fixture
def copier_defaults():
    """Default answers for copier prompts."""
    return {
        "author_name": "Test Author",
        "author_email": "test@example.com",
    }


def run_copier(template_path, dest_path, data=None, defaults=True):
    """Run copier with given parameters."""
    cmd = ["copier", "copy", "--trust", str(template_path), str(dest_path)]
    if defaults:
        cmd.append("--defaults")
    if data:
        for key, value in data.items():
            cmd.extend(["--data", f"{key}={value}"])
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def assert_file_exists(path, content_contains=None):
    """Assert file exists and optionally contains text."""
    assert path.exists(), f"File {path} does not exist"
    if content_contains:
        content = path.read_text()
        assert content_contains in content, f"'{content_contains}' not found in {path}"
```

### Test File: tests/test_backend_addon.py

```python
import pytest
from conftest import run_copier, assert_file_exists


class TestBackendAddonIsolated:
    """Test backend_addon template in isolation."""

    def test_creates_package_structure(self, temp_dir):
        """Backend addon creates correct package structure."""
        result = run_copier(
            "backend_addon",
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"}
        )
        assert result.returncode == 0

        # Verify structure
        pkg_dir = temp_dir / "mypackage"
        assert_file_exists(pkg_dir / "pyproject.toml")
        assert_file_exists(pkg_dir / "src/collective/mypackage/__init__.py")
        assert_file_exists(pkg_dir / "src/collective/mypackage/configure.zcml")

    def test_pyproject_has_addon_settings(self, temp_dir):
        """Backend addon includes custom settings namespace."""
        run_copier(
            "backend_addon",
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"}
        )

        pyproject = temp_dir / "mypackage/pyproject.toml"
        assert_file_exists(
            pyproject,
            content_contains="[tool.plone.backend_addon.settings]"
        )

    def test_flat_package_name_allowed(self, temp_dir):
        """Flat package names (without namespace) are allowed."""
        result = run_copier(
            "backend_addon",
            temp_dir / "mypackage",
            data={"package_name": "mypackage"}  # No dot
        )
        assert result.returncode == 0
        assert_file_exists(temp_dir / "mypackage/src/mypackage/__init__.py")
```

### Test File: tests/test_content_type.py

```python
import pytest
from conftest import run_copier, assert_file_exists


class TestContentTypeRequiresAddon:
    """Content type subtemplate requires parent addon."""

    def test_fails_without_parent_addon(self, temp_dir):
        """Content type fails if no parent addon detected."""
        result = run_copier(
            "content_type",
            temp_dir,  # No addon here
            data={"content_type_name": "Document"}
        )
        assert result.returncode != 0
        assert "parent addon" in result.stderr.lower()

    def test_succeeds_with_parent_addon(self, temp_dir):
        """Content type succeeds when parent addon exists."""
        # First create parent addon
        run_copier(
            "backend_addon",
            temp_dir / "mypackage",
            data={"package_name": "collective.mypackage"}
        )

        # Then add content type
        result = run_copier(
            "content_type",
            temp_dir / "mypackage",
            data={"content_type_name": "News Item"}
        )
        assert result.returncode == 0

        # Verify content type created
        ct_file = temp_dir / "mypackage/src/collective/mypackage/content/news_item.py"
        assert_file_exists(ct_file)


class TestContentTypeIntegration:
    """Test content type registers in parent addon."""

    def test_updates_configure_zcml(self, temp_dir):
        """Content type is registered in configure.zcml."""
        # Create addon
        run_copier("backend_addon", temp_dir / "pkg", data={"package_name": "my.pkg"})

        # Add content type
        run_copier("content_type", temp_dir / "pkg", data={"content_type_name": "Article"})

        # Verify ZCML updated
        zcml = temp_dir / "pkg/src/my/pkg/configure.zcml"
        assert_file_exists(zcml, content_contains="content")

    def test_updates_addon_settings(self, temp_dir):
        """Content type registered in addon settings."""
        run_copier("backend_addon", temp_dir / "pkg", data={"package_name": "my.pkg"})
        run_copier("content_type", temp_dir / "pkg", data={"content_type_name": "Article"})

        pyproject = temp_dir / "pkg/pyproject.toml"
        assert_file_exists(pyproject, content_contains="content_types")
```

### Test File: tests/test_combinations.py

```python
import pytest
from conftest import run_copier, assert_file_exists


class TestMultipleSubtemplates:
    """Test applying multiple subtemplates to same addon."""

    def test_addon_with_content_type_and_behavior(self, temp_dir):
        """Addon with content type and behavior works together."""
        pkg_dir = temp_dir / "mypackage"

        # Create addon
        run_copier("backend_addon", pkg_dir, data={"package_name": "collective.news"})

        # Add content type
        run_copier("content_type", pkg_dir, data={"content_type_name": "News Item"})

        # Add behavior
        run_copier("behavior", pkg_dir, data={"behavior_name": "IFeatured"})

        # Verify both exist
        assert_file_exists(pkg_dir / "src/collective/news/content/news_item.py")
        assert_file_exists(pkg_dir / "src/collective/news/behaviors/ifeatured.py")

        # Verify both registered
        zcml = pkg_dir / "src/collective/news/configure.zcml"
        content = zcml.read_text()
        assert "content" in content
        assert "behaviors" in content

    def test_full_stack_integration(self, temp_dir):
        """Full workflow: zope-setup + addon + subtemplates."""
        project_dir = temp_dir / "my-project"

        # Create zope-setup project
        run_copier("zope-setup", project_dir, data={"project_name": "my-project"})

        # Create addon in sources/
        addon_dir = project_dir / "sources/collective/mysite"
        run_copier("backend_addon", addon_dir, data={"package_name": "collective.mysite"})

        # Add multiple features
        run_copier("content_type", addon_dir, data={"content_type_name": "Page"})
        run_copier("behavior", addon_dir, data={"behavior_name": "ISocial"})
        run_copier("restapi_service", addon_dir, data={"service_name": "stats"})

        # Verify everything exists
        assert_file_exists(project_dir / "pyproject.toml")
        assert_file_exists(addon_dir / "pyproject.toml")
        assert_file_exists(addon_dir / "src/collective/mysite/content/page.py")
        assert_file_exists(addon_dir / "src/collective/mysite/behaviors/isocial.py")
        assert_file_exists(addon_dir / "src/collective/mysite/services/stats.py")
```

---

## Subtemplate Context Detection

### shared/hooks/addon_context.py

```python
#!/usr/bin/env python3
"""Detect parent addon context for subtemplates."""
import sys
from pathlib import Path

try:
    import tomlkit
except ImportError:
    print("ERROR: tomlkit required. Install with: pip install tomlkit")
    sys.exit(1)


def find_addon_context(start_path: Path = None) -> dict | None:
    """
    Find parent addon context by looking for:
    1. .copier-answers.backend-addon.*.yml
    2. [tool.plone.backend_addon.settings] in pyproject.toml
    """
    start_path = start_path or Path.cwd()

    # Check for copier answers file
    for f in start_path.glob(".copier-answers.backend-addon.*.yml"):
        # Found answers file, read pyproject.toml for settings
        pyproject_path = start_path / "pyproject.toml"
        if pyproject_path.exists():
            return _read_addon_settings(pyproject_path)

    # Check pyproject.toml directly
    pyproject_path = start_path / "pyproject.toml"
    if pyproject_path.exists():
        settings = _read_addon_settings(pyproject_path)
        if settings:
            return settings

    return None


def _read_addon_settings(pyproject_path: Path) -> dict | None:
    """Read addon settings from pyproject.toml."""
    with open(pyproject_path) as f:
        doc = tomlkit.parse(f.read())

    try:
        return dict(doc["tool"]["plone"]["backend_addon"]["settings"])
    except KeyError:
        return None


def require_addon_context():
    """Exit with error if no parent addon found."""
    context = find_addon_context()
    if not context:
        print("\n" + "=" * 60)
        print("ERROR: No parent addon detected!")
        print("=" * 60)
        print("\nThis template must be run inside an existing backend_addon.")
        print("First create an addon with:")
        print("  copier copy gh:plone/copier-templates/backend_addon my-addon")
        print("\nThen run this subtemplate inside that directory.")
        print("=" * 60 + "\n")
        sys.exit(1)
    return context


if __name__ == "__main__":
    # Used as pre-copy hook by subtemplates
    require_addon_context()
```

---

## Implementation Phases

### Phase 1: Repository & Test Infrastructure

1. Create repository with pyproject.toml (dev dependencies)
2. Set up pytest with conftest.py and helpers
3. Create shared/ utilities structure
4. Implement git_check.py hook
5. Implement addon_context.py hook
6. **Write failing tests** for all planned templates

### Phase 2: zope-setup Template (TDD)

1. Write tests in test_zope_setup.py
2. Implement copier.yml
3. Implement pyproject.toml.jinja with `[tool.plone.project.settings]`
4. Implement tasks.py.jinja
5. Implement instance/ configuration
6. Implement GitHub Actions workflow
7. Pass all zope-setup tests

### Phase 3: backend_addon Template (TDD)

1. Write tests in test_backend_addon.py
2. Implement copier.yml
3. Implement pyproject.toml.jinja with `[tool.plone.backend_addon.settings]`
4. Implement package structure (src/, configure.zcml)
5. Pass all backend_addon tests

### Phase 4: Subtemplates (TDD)

1. Write tests for each subtemplate (including combination tests)
2. Implement content_type/ (requires parent addon)
3. Implement behavior/ (requires parent addon)
4. Implement restapi_service/ (requires parent addon)
5. Each subtemplate:
   - Validates parent addon exists
   - Reads context from `[tool.plone.backend_addon.settings]`
   - Adds files to correct location
   - Updates parent's configure.zcml
   - Registers itself in parent settings
6. Pass all subtemplate tests

### Phase 5: Integration Testing

1. Run full test suite
2. Test combinations in test_combinations.py
3. Manual testing of workflows
4. Documentation

---

## Files to Create (in order)

### Phase 1 ✓

1. `pyproject.toml` - Repository dependencies ✓
2. `tests/conftest.py` - Test fixtures ✓
3. `tests/helpers.py` - Test utilities ✓
4. `shared/__init__.py` ✓
5. `shared/hooks/__init__.py` ✓
6. `shared/hooks/addon_context.py` ✓
7. `shared/utils/__init__.py` ✓
8. `shared/utils/pyproject_updater.py` ✓

### Phase 2 ✓

9. `tests/test_zope_setup.py` ✓
10. `zope-setup/copier.yml` ✓
11. `zope-setup/template/` files ✓

### Phase 3 ✓

12. `tests/test_backend_addon.py` ✓
13. `backend_addon/copier.yml` ✓
14. `backend_addon/template/` files ✓

### Phase 4 ✓

15. `tests/test_content_type.py` ✓
16. `tests/test_behavior.py` ✓
17. `tests/test_restapi_service.py` ✓
18. `tests/test_combinations.py` ✓
19. `content_type/` implementation ✓
20. `behavior/` implementation ✓
21. `restapi_service/` implementation ✓

---

## Verification

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_zope_setup.py -v           # Isolated
pytest tests/test_backend_addon.py -v        # Isolated
pytest tests/test_combinations.py -v         # Integration

# Test coverage
pytest tests/ --cov=shared --cov-report=html
```

---

## Design Decisions

1. **Addon path**: `sources/` (matches existing pattern)
2. **Package namespace**: Allow flat packages (no enforcement)
3. **Testing**: pytest with TDD approach
4. **CI/CD**: GitHub Actions included
5. **Settings persistence**: Custom pyproject.toml namespaces
6. **Subtemplate detection**: Via copier answers file + pyproject.toml settings
