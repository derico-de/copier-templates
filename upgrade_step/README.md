# Upgrade Step Subtemplate

Adds a GenericSetup upgrade step to an existing `backend_addon`.

## Usage

```bash
cd my-addon
copier copy path/to/upgrade_step .
```

## What it creates

- `src/<package>/upgrades/__init__.py` — package init
- `src/<package>/upgrades/<handler>.py` — upgrade step handler function
- `src/<package>/upgrades/configure.zcml` — ZCML registration (created or appended to)

## What it updates

- `profiles/default/metadata.xml` — bumps profile version to the destination version
- `configure.zcml` — adds `<include package=".upgrades" />` if not present

## Questions

| Question | Default | Description |
|----------|---------|-------------|
| `upgrade_step_title` | (required) | Human-readable title for the upgrade step |
| `upgrade_step_description` | "A custom upgrade step" | Description of what this step does |
| `source_version` | current metadata.xml version | Source profile version |
| `destination_version` | source + 1 | Target profile version |
