# controlpanel

Adds a registry-backed Plone control panel to an existing `backend_addon`
package. Must be run inside an addon directory.

## What it generates

- `src/<package_folder>/controlpanels/__init__.py`
- `src/<package_folder>/controlpanels/<module>/` -- subpackage
  (bobtemplates layout) with `controlpanel.py` (settings schema
  `I<Name>Settings`, `<Name>ControlPanelForm` (`RegistryEditForm`) and
  `<Name>ControlPanelView` (`ControlPanelFormWrapper`)) and its own
  `configure.zcml` (`browser:page` registration bound to `IPloneSiteRoot`)
- `src/<package_folder>/controlpanels/configure.zcml` -- includes the
  subpackage
- `src/<package_folder>/profiles/default/controlpanel.xml` -- configlet
  entry under `portal_controlpanel`
- `src/<package_folder>/profiles/default/registry/<module>.xml` --
  registry records scaffold for the settings schema
- Adds `<include package=".controlpanels" />` to the parent `configure.zcml`
- Records the control panel in
  `[tool.plone.backend_addon.settings.subtemplates]`

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `controlpanel_name` | Base name (PascalCase) | `MyFeatured` |
| `controlpanel_title` | Human-readable title | `<controlpanel_name>` |
| `controlpanel_description` | Short description | `A custom control panel` |
| `package_name` | Parent addon package name | (required) |

The ZCML `browser:page` name is derived as
`<kebab-name>-controlpanel`, e.g. `MyFeatured` -> `my-featured-controlpanel`.

## Usage

```bash
cd my-addon
copier copy <templates>/controlpanel . \
  --data controlpanel_name=MyFeatured \
  --data package_name=collective.mypackage
```
