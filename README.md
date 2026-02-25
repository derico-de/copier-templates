# Plone Copier Templates

A multi-template [Copier](https://copier.readthedocs.io/) repository for modern Plone development. This project provides composable templates for creating Plone projects, addons, and addon components.

## Overview

This repository contains templates that follow a hierarchical architecture:

```
INDEPENDENT TEMPLATES:
├── zope-setup              → Creates Plone/Zope project structure
└── backend_addon           → Creates standalone addon package

SUBTEMPLATES (require backend_addon):
├── content_type            → Adds Dexterity content type to addon
├── behavior                → Adds Dexterity behavior to addon
└── restapi_service         → Adds REST API endpoint to addon
```

## Requirements

- Python 3.10+
- [Copier](https://copier.readthedocs.io/) 9.0.0+

## Installation

```bash
uv tool install copier
```

## Quick Start

### Create a Plone Project

```bash
copier copy gh:plone/copier-templates/zope-setup my-project
cd my-project
```

### Create a Standalone Addon

```bash
copier copy gh:plone/copier-templates/backend_addon my-addon
cd my-addon
```

### Add Components to an Addon

Subtemplates must be run from inside an existing addon directory:

```bash
cd my-addon

# Add a content type
copier copy gh:plone/copier-templates/content_type .

# Add a behavior
copier copy gh:plone/copier-templates/behavior .

# Add a REST API service
copier copy gh:plone/copier-templates/restapi_service .
```

## Templates

### zope-setup

Creates a complete Plone/Zope project structure with:

- `pyproject.toml` with Plone dependencies
- Zope configuration files (`zope.conf`, `zope.ini`)
- Invoke tasks for common operations
- GitHub Actions CI workflow
- Project settings in `[tool.plone.project.settings]`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `project_name` | Project name | (required) |
| `project_title` | Human-readable title | Auto-generated |
| `plone_version` | Plone version | `6.1.1` |
| `distribution` | Plone distribution | `plone.volto` |
| `db_storage` | Database backend | `direct` |
| `author_name` | Author name | `Plone Developer` |
| `author_email` | Author email | `dev@plone.org` |

**Example:**

```bash
copier copy gh:plone/copier-templates/zope-setup my-project \
  --data project_name=my-project \
  --data plone_version=6.1.1 \
  --data distribution=plone.volto
```

### backend_addon

Creates a standalone Plone addon package with:

- Complete Python package structure
- `configure.zcml` with GenericSetup profiles
- Testing infrastructure (`testing.py`, sample tests)
- Addon settings in `[tool.plone.backend_addon.settings]`

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `package_name` | Python package name (e.g., `collective.mypackage`) | (required) |
| `package_title` | Human-readable title | Auto-generated |
| `plone_version` | Minimum Plone version | `6.1` |
| `is_headless` | Headless/API-only addon | `false` |
| `author_name` | Author name | `Plone Developer` |
| `author_email` | Author email | `dev@plone.org` |

**Example:**

```bash
copier copy gh:plone/copier-templates/backend_addon collective.news \
  --data package_name=collective.news \
  --data is_headless=false
```

### content_type (Subtemplate)

Adds a Dexterity content type to an existing addon:

- Content type class with schema interface
- FTI (Factory Type Information) XML
- ZCML registration
- Registers in parent addon settings

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `content_type_name` | Content type name (e.g., `News Item`) | (required) |
| `content_type_description` | Description | `A custom content type` |
| `content_type_base` | Base class (`Container` or `Item`) | `Container` |
| `enable_dublin_core` | Enable Dublin Core behavior | `true` |
| `enable_navigation` | Enable navigation behavior | `true` |
| `package_name` | Parent addon package name | (required) |

**Example:**

```bash
cd my-addon
copier copy gh:plone/copier-templates/content_type . \
  --data content_type_name="News Item" \
  --data package_name=collective.news
```

### behavior (Subtemplate)

Adds a Dexterity behavior to an existing addon:

- Behavior interface with schema
- Optional marker interface
- Optional behavior adapter/factory
- ZCML registration

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `behavior_name` | Behavior interface name (e.g., `IFeatured`) | (required) |
| `behavior_description` | Description | `A custom Dexterity behavior` |
| `behavior_marker` | Create marker interface | `true` |
| `behavior_factory` | Create behavior factory | `true` |
| `package_name` | Parent addon package name | (required) |

**Example:**

```bash
cd my-addon
copier copy gh:plone/copier-templates/behavior . \
  --data behavior_name=IFeatured \
  --data package_name=collective.news
```

### restapi_service (Subtemplate)

Adds a plone.restapi service endpoint to an existing addon:

- Service class with configurable HTTP methods
- ZCML registration with permissions
- Configurable context (container, content, site root)

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `service_name` | Endpoint name (e.g., `stats`) | (required) |
| `service_description` | Description | `A custom REST API endpoint` |
| `http_get` | Support GET requests | `true` |
| `http_post` | Support POST requests | `false` |
| `http_patch` | Support PATCH requests | `false` |
| `http_delete` | Support DELETE requests | `false` |
| `service_for` | Context interface | `IDexterityContainer` |
| `package_name` | Parent addon package name | (required) |

**Example:**

```bash
cd my-addon
copier copy gh:plone/copier-templates/restapi_service . \
  --data service_name=analytics \
  --data http_get=true \
  --data http_post=true \
  --data package_name=collective.news
```

## Architecture

### Custom Namespaces in pyproject.toml

Templates persist settings in custom pyproject.toml namespaces, enabling subtemplates to read parent context without re-asking questions.

**Project Settings (zope-setup):**

```toml
[tool.plone.project.settings]
plone_version = "6.1.1"
distribution = "plone.volto"
db_storage = "direct"
created_at = "2024-01-18"
```

**Addon Settings (backend_addon):**

```toml
[tool.plone.backend_addon.settings]
package_name = "collective.mypackage"
package_folder = "collective/mypackage"
plone_version = "6.1"
is_headless = false

[tool.plone.backend_addon.settings.subtemplates]
content_types = ["News Item", "Article"]
behaviors = ["IFeatured", "ITaggable"]
services = ["@stats", "@analytics"]
```

### Subtemplate Detection

Subtemplates detect their parent addon by:

1. Looking for `.copier-answers.backend-addon.*.yml` in the target directory
2. Reading `[tool.plone.backend_addon.settings]` from `pyproject.toml`

### Repository Structure

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
│   ├── test_content_type.py         # content_type with parent addon
│   ├── test_behavior.py             # behavior with parent addon
│   ├── test_restapi_service.py      # restapi_service with parent addon
│   └── test_combinations.py         # Multi-subtemplate scenarios
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
│       ├── pyproject.toml.jinja
│       ├── tasks.py.jinja
│       └── instance/
│           └── etc/
│               ├── zope.conf.jinja
│               └── zope.ini.jinja
│
├── backend_addon/                   # INDEPENDENT TEMPLATE
│   ├── copier.yml
│   └── template/
│       ├── {{_copier_conf.answers_file}}.jinja
│       ├── pyproject.toml.jinja
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
│   ├── copier.yml
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

### Generated Project Structure

After running all templates, your project might look like:

```
my-project/
├── pyproject.toml                    # Project config with [tool.plone.project.settings]
├── instance/
│   └── etc/
│       ├── zope.conf
│       └── zope.ini
├── sources/
│   └── collective.mysite/            # Addon created with backend_addon
│       ├── pyproject.toml            # Addon config with [tool.plone.backend_addon.settings]
│       ├── src/
│       │   └── collective/
│       │       └── mysite/
│       │           ├── __init__.py
│       │           ├── configure.zcml
│       │           ├── testing.py
│       │           ├── setuphandlers.py
│       │           ├── profiles/
│       │           │   ├── default/metadata.xml
│       │           │   └── uninstall/metadata.xml
│       │           ├── content/      # Added by content_type
│       │           │   ├── __init__.py
│       │           │   └── configure.zcml
│       │           ├── behaviors/    # Added by behavior
│       │           │   ├── __init__.py
│       │           │   └── configure.zcml
│       │           └── services/     # Added by restapi_service
│       │               ├── __init__.py
│       │               └── configure.zcml
│       └── tests/
│           ├── conftest.py
│           └── test_setup.py
└── .github/
    └── workflows/
        └── ci.yml
```

## Development

### Setup

```bash
git clone https://github.com/plone/copier-templates.git
cd copier-templates
uv sync --extra dev
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_backend_addon.py -v

# Run with coverage
pytest tests/ --cov=shared --cov-report=html
```

### Test Categories

| Test File | Description |
|-----------|-------------|
| `test_zope_setup.py` | Isolated zope-setup tests |
| `test_backend_addon.py` | Isolated backend_addon tests |
| `test_content_type.py` | content_type with parent addon |
| `test_behavior.py` | behavior with parent addon |
| `test_restapi_service.py` | restapi_service with parent addon |
| `test_combinations.py` | Multi-subtemplate scenarios |

### Adding a New Template

1. Create test file in `tests/test_<template_name>.py`
2. Create template directory with `copier.yml`
3. Add template files in `template/` subdirectory
4. If it's a subtemplate, create `tasks.py` for post-copy registration

## Full Workflow Example

```bash
# 1. Create a new Plone project
copier copy gh:plone/copier-templates/zope-setup my-intranet \
  --data project_name=my-intranet \
  --data plone_version=6.1.1

cd my-intranet

# 2. Create a custom addon
copier copy gh:plone/copier-templates/backend_addon sources/intranet.policy \
  --data package_name=intranet.policy

cd sources/intranet.policy

# 3. Add a custom content type
copier copy gh:plone/copier-templates/content_type . \
  --data content_type_name="Department" \
  --data content_type_base=Container \
  --data package_name=intranet.policy

# 4. Add a behavior for social features
copier copy gh:plone/copier-templates/behavior . \
  --data behavior_name=ISocialMedia \
  --data package_name=intranet.policy

# 5. Add a REST API endpoint
copier copy gh:plone/copier-templates/restapi_service . \
  --data service_name=org-chart \
  --data http_get=true \
  --data package_name=intranet.policy

# 6. Install and run
cd ../..
uv sync --extra dev
uv pip install -e sources/intranet.policy
invoke start
```

## Updating Templates

To update an existing project with template changes:

```bash
copier update --trust
```

This will re-apply the template while preserving your customizations.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests first (TDD)
4. Implement the feature
5. Submit a pull request

## License

MIT

## Credits

- Plone Foundation
- Inspired by [bobtemplates.plone](https://github.com/plone/bobtemplates.plone)
