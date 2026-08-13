# svelte_app

Adds a Svelte application scaffold (vite + main/App + Python mount view)
to an existing `backend_addon` package. Must be run inside an addon
directory.

Mirrors the bobtemplates.plone `svelte_app` layout: a `svelte_src/<app>/`
directory with the frontend source and a small `src/<package>/svelte_apps/`
Python mount view that serves an HTML shell for the built bundle.

## What it generates

### Frontend (`svelte_src/<app>/`)
- `src/App.svelte` -- Svelte 5 root component using runes
- `src/main.js` -- entry point that mounts `App` or registers its custom element
- `index.html` -- local Vite development page
- `package.json` -- current Svelte, Vite, and Vite plugin dependencies
- `README.md` -- local development and build commands
- `svelte.config.js` -- Svelte compiler configuration
- `vite.config.js` -- SvelteKit-less library build that outputs into
  `src/<package>/svelte_apps/static/<app>/`

The generated setup requires Node.js 20.19+ or 22.12+.

### Backend (`src/<package>/svelte_apps/`)
- `__init__.py`
- `<module>.py` -- `BrowserView` subclass serving the mount page
- `<module>.pt` -- HTML shell with a mount `<div>` or custom element

Records the app in
`[tool.plone.backend_addon.settings.subtemplates.svelte_apps]`.

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `svelte_app_name` | App name (kebab-case) | `my-svelte-app` |
| `svelte_app_description` | Short description | `A custom Svelte application` |
| `svelte_app_custom_element` | Compile as Web Component | `false` |
| `package_name` | Parent addon package name | (required) |

`svelte_app_module` (snake_case) and `svelte_app_class` (PascalCase) are
computed at render time.

## Usage

```bash
cd my-addon
copier copy <templates>/svelte_app . \
  --data svelte_app_name=dashboard-ui \
  --data package_name=collective.mypackage
```

Then, to build the frontend:

```bash
cd svelte_src/dashboard-ui
npm install
npm run build
```

The build output lands inside the Python package under
`src/<package>/svelte_apps/static/<app>/`. Use `npm run dev` for Vite's
local development server.
