# theme

This is an alternative to `theme_basic` and `theme_barceloneta`. Remove an
existing generated theme before applying a different theme template.

Adds a full Diazo-based Plone theme (webpack + SCSS partials + Diazo
rules + GenericSetup profile) to an existing `backend_addon` package.
Must be run inside an addon directory.

The difference from `theme_basic` is a richer front-end scaffold:
- `webpack.config.js` with mini-css-extract-plugin + sass-loader
- `scss/_variables.scss` partial with design-token placeholders
- `scss/theme.scss` imports `_variables` and applies a few example rules

## What it generates

- `src/<package_folder>/theme/manifest.cfg`
- `src/<package_folder>/theme/rules.xml`
- `src/<package_folder>/theme/index.html`
- `src/<package_folder>/theme/webpack.config.js`
- `src/<package_folder>/theme/package.json` (webpack deps)
- `src/<package_folder>/theme/scss/_variables.scss`
- `src/<package_folder>/theme/scss/theme.scss`
- `src/<package_folder>/theme/css/theme.css`
- `src/<package_folder>/theme/js/theme.js`
- `src/<package_folder>/profiles/default/theme.xml`
- Records the theme in `[tool.plone.backend_addon.settings.subtemplates.themes]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `theme_name` | Theme display name | `My Theme` |
| `theme_description` | Short description | `A custom Plone theme` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/theme . \
  --data theme_name="My Theme" \
  --data package_name=collective.mypackage
```
