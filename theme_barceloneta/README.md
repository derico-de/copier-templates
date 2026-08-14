# theme_barceloneta

This is an alternative to `theme` and `theme_basic`. Remove an existing
generated theme before applying a different theme template.

Adds a Barceloneta-based Plone theme variant to an existing
`backend_addon` package. Must be run inside an addon directory.

File layout mirrors `theme_basic`; the difference is that
`scss/theme.scss` is prepared to import Plone's Barceloneta variables,
mixins and main styles, letting you layer customizations on top.

## What it generates

- `src/<package_folder>/theme/manifest.cfg`
- `src/<package_folder>/theme/rules.xml`
- `src/<package_folder>/theme/index.html`
- `src/<package_folder>/theme/scss/theme.scss` -- imports
  `barceloneta/variables`, `barceloneta/mixins`, `barceloneta/main`
- `src/<package_folder>/theme/css/theme.css`
- `src/<package_folder>/theme/js/theme.js`
- `src/<package_folder>/theme/package.json`
- `src/<package_folder>/profiles/default/theme.xml`
- Records the theme in `[tool.plone.backend_addon.settings.subtemplates.themes]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `theme_name` | Theme display name | `My Theme` |
| `theme_description` | Short description | `A Barceloneta-based Plone theme` |
| `package_name` | Parent addon package name | (required) |

## Usage

```bash
cd my-addon
copier copy <templates>/theme_barceloneta . \
  --data theme_name="My Barceloneta Theme" \
  --data package_name=collective.mypackage
```
