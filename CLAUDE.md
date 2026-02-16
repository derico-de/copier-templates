# Copier Templates for Plone

## Project Overview

Multi-template Copier repository providing code generators for Plone 6 backend development.
Uses [Copier](https://copier.readthedocs.io/) >= 9.0 with Python task hooks for post-generation automation.

## Architecture

```
copier-templates/
  backend_addon/     # Independent: Plone backend addon package
  zope-setup/        # Independent: Zope/Plone project environment
  content_type/      # Subtemplate: Dexterity content types (requires backend_addon)
  behavior/          # Subtemplate: Dexterity behaviors (requires backend_addon)
  restapi_service/   # Subtemplate: plone.restapi endpoints (requires backend_addon)
  shared/            # Shared Python utilities for all templates
  tests/             # pytest test suite
```

### Template Types

**Independent templates** can be used standalone:
- `backend_addon`: Creates a full Plone addon package with pyproject.toml, ZCML, testing, GenericSetup profiles
- `zope-setup`: Creates a Zope/Plone project environment with configuration

**Subtemplates** must run inside an existing `backend_addon` directory:
- `content_type`: Adds Dexterity content type (module, FTI XML, ZCML behavior registration, types.xml)
- `behavior`: Adds Dexterity behavior (interface, marker, factory, ZCML registration)
- `restapi_service`: Adds plone.restapi service endpoint (GET/POST/PATCH/DELETE)

### Template Structure Pattern

Each template follows this layout:
```
template_name/
  copier.yml          # Copier config: questions, computed values, tasks
  tasks.py            # Python hooks: validate (pre-copy), post_copy
  template/           # Jinja2 template files (_subdirectory: template)
```

### Shared Utilities (`shared/`)

- `utils/pyproject_updater.py` - PyprojectUpdater: safely modify pyproject.toml via tomlkit
- `utils/xml_updater.py` - ConfigureZCMLUpdater, TypesXMLUpdater, ParentZCMLUpdater: XML config file management
- `hooks/addon_context.py` - Detect parent addon via pyproject.toml `[tool.plone.backend_addon.settings]`
- `hooks/git_check.py` - Warn about uncommitted changes
- `exceptions.py` - CopierTemplateError, AddonContextError, ValidationError

### Post-Copy Task Flow (Subtemplates)

1. `validate`: Check parent addon exists (via `find_addon_context`), warn about git state
2. `post_copy`: Register in pyproject.toml subtemplates section, update XML configs, add parent ZCML includes

### Addon Settings in pyproject.toml

Generated addons store metadata at `[tool.plone.backend_addon.settings]`:
```toml
[tool.plone.backend_addon.settings]
package_name = "collective.mypackage"
package_folder = "collective/mypackage"

[tool.plone.backend_addon.settings.subtemplates]
content_types = ["Article"]
behaviors = ["IFeatured"]
services = ["@stats"]
```

## Conventions

- **Line length**: 100 (project code and generated output)
- **Python**: >= 3.10, type hints with `X | Y` syntax
- **Linting**: ruff with E, F, I, W, C90, B, S, UP, SIM, PGH rules
- **Template files**: `.jinja` extension, Jinja2 syntax
- **Copier version**: >= 9.0.0
- **Package names**: dotted notation (e.g., `collective.mypackage`)
- **ZCML namespaces**: Always include `xmlns:plone` in addon configure.zcml
- **XML indentation**: 2 spaces in ZCML/XML files
- **Tests**: pytest with subprocess-based copier invocation, temp directories

## Testing

```bash
uv run pytest tests/ -v
```

Test patterns:
- `run_copier()` helper executes copier as subprocess (tests/helpers.py)
- Fixtures provide temp dirs, template paths, and default answers (tests/conftest.py)
- Each template has its own test file; `test_combinations.py` tests multi-subtemplate scenarios
- `test_plone_standards.py` verifies generated output follows Plone/plone.meta standards
- PYTHONPATH fixture ensures copier tasks find venv packages (tomlkit)

## Key Technical Details

- Copier tasks use `uv run --with tomlkit python3` to ensure tomlkit is available
- Subtemplates use `sys.path.insert(0, shared_dir)` to import shared utilities
- CWD resolution: copier may run tasks from destination dir, so tasks check `Path.cwd()` first
- XML updaters are idempotent - safe to run multiple times without duplicates
- ParentZCMLUpdater adds `<include package=".subpackage" />` to parent configure.zcml

## Generated Output Standards

Generated Plone addons follow plone.meta/cookieplone conventions:
- `.editorconfig` for consistent formatting across editors
- `.pre-commit-config.yaml` with ruff and pre-commit-hooks
- Extended ruff config with security (bandit), bugbear, pyupgrade rules
- GenericSetup profiles for install/uninstall
- ZCML registration with proper namespace declarations
