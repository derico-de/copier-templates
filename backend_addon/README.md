# backend_addon

Creates a standalone Plone addon package with complete Python package structure, namespace support, testing infrastructure, and editor configurations.

## What it generates

```
<package_name>/
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── .editorconfig
├── .pre-commit-config.yaml
└── src/<package_folder>/
    ├── __init__.py
    ├── configure.zcml
    ├── testing.py
    ├── setuphandlers.py
    ├── locales/
    ├── profiles/
    │   ├── default/metadata.xml
    │   └── uninstall/metadata.xml
    └── tests/            # inside the package (bobtemplates layout)
        ├── __init__.py
        ├── conftest.py
        └── test_setup.py
```

Addon settings are stored in `[tool.plone.backend_addon.settings]` in `pyproject.toml`, enabling subtemplates (`content_type`, `behavior`, `restapi_service`) to auto-detect the addon context.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `package_name` | Python package name (e.g., `collective.mypackage`) | Directory name |
| `package_title` | Human-readable title | Auto-generated from package name |
| `package_description` | Short description | `A Plone addon package` |
| `plone_version` | Minimum Plone version (`6.1`, `6.0`) | `6.0` |
| `is_headless` | Headless/API-only addon | `false` |
| `author_name` | Author name | `Plone Developer` |
| `author_email` | Author email | `dev@plone.org` |

## Usage

```bash
copier copy ~/.copier-templates/plone-copier-templates/backend_addon collective.news \
  --data package_name=collective.news

# Then add components:
cd collective.news
copier copy ~/.copier-templates/plone-copier-templates/content_type .
copier copy ~/.copier-templates/plone-copier-templates/behavior .
copier copy ~/.copier-templates/plone-copier-templates/restapi_service .
```

## Self-contained addon with zope-setup

You can add a Zope project setup inside the addon for a self-contained development environment:

```bash
cd collective.news
copier copy ~/.copier-templates/plone-copier-templates/zope-setup .
```

Project name, title, and description are automatically inherited from the addon.
