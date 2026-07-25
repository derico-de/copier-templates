# restapi_service

Adds a plone.restapi service endpoint to an existing `backend_addon` package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/api/services/<module>/` -- service subpackage with one
  module per HTTP verb (`get.py`, `post.py`, ...) and a self-contained
  `configure.zcml` (bobtemplates layout)
- `src/<package_folder>/api/configure.zcml` and
  `src/<package_folder>/api/services/configure.zcml` -- include chain
- Adds `<include package=".api" />` to the parent addon's `configure.zcml`
- Records the service in `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `service_name` | Endpoint name (e.g., `stats`, `my-endpoint`) | (required) |
| `service_description` | Short description | `A custom REST API endpoint` |
| `package_name` | Parent addon package name | (required) |
| `http_get` | Support GET requests | `true` |
| `http_post` | Support POST requests | `false` |
| `http_patch` | Support PATCH requests | `false` |
| `http_delete` | Support DELETE requests | `false` |
| `service_for` | Context interface | `IDexterityContainer` |

Context choices: `IDexterityContainer`, `IDexterityContent`, `IPloneSiteRoot`, `Interface`

## Usage

```bash
cd my-addon
copier copy ~/.copier-templates/plone-copier-templates/restapi_service . \
  --data service_name=analytics \
  --data http_get=true \
  --data http_post=true \
  --data package_name=collective.news
```
