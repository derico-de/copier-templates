# theme_basic

This is an alternative to `theme` and `theme_barceloneta`. Remove an existing
generated theme before applying a different theme template.

Adds a minimal Diazo-based Plone theme (`manifest.cfg`, `rules.xml`,
`index.html`, `scss/theme.scss`, `css/theme.css`, `js/theme.js`,
`package.json`, GenericSetup `theme.xml`) to an existing `backend_addon`
package. Must be run inside an addon directory.

Structurally mirrors the bobtemplates.plone `theme_basic` layout, with
placeholder content. Binary files from upstream (e.g. `preview.png`)
are intentionally not generated.

## What it generates

- `src/<package_folder>/theme/manifest.cfg`
- `src/<package_folder>/theme/rules.xml`
- `src/<package_folder>/theme/index.html`
- `src/<package_folder>/theme/scss/theme.scss`
- `src/<package_folder>/theme/css/theme.css`
- `src/<package_folder>/theme/js/theme.js`
- `src/<package_folder>/theme/package.json`
- `src/<package_folder>/profiles/default/theme.xml`
- Records the theme in `[tool.plone.backend_addon.settings.subtemplates.themes]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `theme_name` | Theme display name | `My Theme` |
| `theme_description` | Short description | `A basic Plone theme` |
| `package_name` | Parent addon package name | (required) |

`theme_id` is derived from `theme_name` (lowercased, spaces and
underscores replaced with `-`).

## Usage

```bash
cd my-addon
copier copy <templates>/theme_basic . \
  --data theme_name="My Theme" \
  --data package_name=collective.mypackage
```
