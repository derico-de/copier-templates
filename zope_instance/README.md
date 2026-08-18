# zope_instance

Adds a Zope instance to an existing `zope-setup` project. Must be run inside a directory that was created with the `zope-setup` template.

The initial instance is created automatically by `zope-setup`. Use this template to add additional instances for multi-client setups (relstorage or ZEO).

## What it generates

```
var/<instance_name>/
├── etc/
│   ├── zope.conf        # ZODB config (filestorage, relstorage, or zeoclient)
│   └── zope.ini         # Waitress WSGI server on configured port
├── inituser             # Admin credentials
└── var/                 # Data directory for ZODB storage and blobs
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `instance_name` | Instance directory name (e.g., `instance`, `instance2`, `zeo-client1`) | `instance` |
| `port` | HTTP port for this instance | `8080` |
| `host` | Host/IP the instance binds to | `0.0.0.0` inside an addon, else `127.0.0.1` |
| `base_path` | Base path for instance directory | `var/` |
| `db_storage` | Database backend (`instance`, `relstorage`, `zeo`) | From project context |
| `zeo_address` | ZEO server address (only when `db_storage=zeo`) | `localhost:8100` |
| `pg_host` | PostgreSQL host (only when `db_storage=relstorage`) | `localhost` |
| `pg_port` | PostgreSQL port (only when `db_storage=relstorage`) | `5432` |
| `pg_dbname` | PostgreSQL database name (only when `db_storage=relstorage`) | `plone_<project_name>` |
| `pg_user` | PostgreSQL user (only when `db_storage=relstorage`) | `plone` |
| `pg_password` | PostgreSQL password (only when `db_storage=relstorage`) | (empty) |
| `initial_zope_username` | Initial Zope admin username | `admin` |
| `initial_user_password` | Initial Zope admin password (secret) | `admin` |

## Context detection

Reads `[tool.plone.project.settings]` from the parent project's `pyproject.toml` to auto-detect `db_storage` and `project_name`. If no project context is found, the template exits with an error.

`[tool.plone.backend_addon.settings]` (or legacy addon files) marks the project as an addon development environment: `host` then defaults to `0.0.0.0` so the instance is reachable from outside a container. A standalone project is a deployment target and defaults to `127.0.0.1`, expecting a reverse proxy in front.

After creation, the instance is registered in `[tool.plone.project.settings].instances` in `pyproject.toml`.

## Usage

```bash
cd my-project

# Add a second instance
copier copy ~/.copier-templates/plone-copier-templates/zope_instance . \
  --data instance_name=instance2 \
  --data port=8081

# Or use the invoke task
uv run invoke create-instance --name=instance2 --port=8081
```
