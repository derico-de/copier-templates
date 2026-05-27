#!/usr/bin/env python3
"""Post-copy tasks for zope-setup template."""
import subprocess
import sys
from pathlib import Path

# Add shared module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from hooks.addon_context import find_addon_context
from utils.pyproject_updater import PyprojectUpdater


def update_pyproject(dest_path, plone_version, distribution, db_storage, base_path="var"):
    # CWD resolution (MUST come first — copier may set CWD to dest)
    cwd = Path.cwd()
    dest = Path(dest_path)

    if (cwd / "pyproject.toml").exists():
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    pyproject_path = dest / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"Warning: pyproject.toml not found at {pyproject_path}")
        return

    updater = PyprojectUpdater(pyproject_path)

    # Auto-detect addon context
    addon_context = find_addon_context(dest)

    # 1. Add runtime dependencies
    runtime_deps = [distribution, "Paste", "plone.app.caching", "plone.app.upgrade"]
    if db_storage == "zeo":
        runtime_deps.append("ZEO")
    elif db_storage == "relstorage":
        runtime_deps.extend(["relstorage", "psycopg2-binary"])
    # "instance" needs no extra deps

    for dep in runtime_deps:
        updater.add_to_list("project", "dependencies", value=dep)

    # 2. Add dev tooling to a PEP 735 dependency group. uv installs the
    #    default ``dev`` group automatically on ``uv run``, so the invoke
    #    task runner is available without passing ``--extra``/``--group``.
    for dep in ["invoke", "watchdog"]:
        updater.add_to_list("dependency-groups", "dev", value=dep)

    # 3. Ensure [tool.uv] and add constraint-dependencies / override-dependencies
    updater.ensure_section("tool", "uv")
    constraint = f"Products.CMFPlone=={plone_version}"
    updater.add_to_list("tool", "uv", "constraint-dependencies", value=constraint)

    # 4. Record project settings
    updater.set_project_setting("plone_version", plone_version)
    updater.set_project_setting("distribution", distribution)
    updater.set_project_setting("db_storage", db_storage)
    updater.set_project_setting("base_path", base_path)

    # 5. If inside an addon, register zope_setup in addon settings
    if addon_context:
        updater.set_addon_setting("zope_setup", True)
        package_name = addon_context.get("package_name", "")
        print(f"Detected addon context: {package_name}")
        print("Registered zope_setup in addon settings.")

    updater.save()
    print("Updated pyproject.toml with zope-setup dependencies.")


def create_initial_instance(dest_path, db_storage, base_path="var",
                            initial_zope_username="admin",
                            initial_user_password="admin", zeo_address="localhost:8100",
                            pg_host="localhost", pg_port="5432",
                            pg_dbname="", pg_user="plone", pg_password=""):
    """Invoke zope_instance copier template to create the first instance."""
    cwd = Path.cwd()
    dest = Path(dest_path)

    if (cwd / "pyproject.toml").exists():
        dest = cwd
    elif not dest.is_absolute():
        dest = dest.resolve()

    template_path = Path(__file__).resolve().parent.parent / "zope_instance"

    cmd = [
        sys.executable, "-m", "copier", "copy", "--trust", "--defaults", "--overwrite",
        "--data", f"db_storage={db_storage}",
        "--data", f"base_path={base_path}",
        "--data", f"initial_zope_username={initial_zope_username}",
        "--data", f"initial_user_password={initial_user_password}",
    ]

    if db_storage == "zeo":
        cmd.extend(["--data", f"zeo_address={zeo_address}"])
    elif db_storage == "relstorage":
        cmd.extend([
            "--data", f"pg_host={pg_host}",
            "--data", f"pg_port={pg_port}",
            "--data", f"pg_dbname={pg_dbname}",
            "--data", f"pg_user={pg_user}",
        ])
        if pg_password:
            cmd.extend(["--data", f"pg_password={pg_password}"])

    cmd.extend([str(template_path), str(dest)])

    print("Creating initial instance via zope_instance template...")
    result = subprocess.run(cmd, cwd=str(dest))
    if result.returncode != 0:
        print("Warning: Failed to create initial instance.")


def main():
    """Main entry point — sys.argv dispatch."""
    if len(sys.argv) < 2:
        print("Usage: tasks.py <command> [args...]")
        print("Commands: update_pyproject")
        sys.exit(1)

    command = sys.argv[1]

    if command == "update_pyproject":
        if len(sys.argv) < 3:
            print("Usage: tasks.py update_pyproject <dest_path> [--plone-version=X] [--distribution=Y] [--db-storage=Z]")
            sys.exit(1)

        dest_path = sys.argv[2]
        # Parse --key=value args
        kwargs = {}
        for arg in sys.argv[3:]:
            if arg.startswith("--"):
                key, _, value = arg[2:].partition("=")
                kwargs[key.replace("-", "_")] = value

        update_pyproject(
            dest_path,
            plone_version=kwargs.get("plone_version", "6.1.1"),
            distribution=kwargs.get("distribution", "plone.volto"),
            db_storage=kwargs.get("db_storage", "instance"),
            base_path=kwargs.get("base_path", "var"),
        )
    elif command == "create_initial_instance":
        if len(sys.argv) < 3:
            print("Usage: copier_hooks.py create_initial_instance <dest_path> [--db-storage=X] ...")
            sys.exit(1)

        dest_path = sys.argv[2]
        kwargs = {}
        for arg in sys.argv[3:]:
            if arg.startswith("--"):
                key, _, value = arg[2:].partition("=")
                kwargs[key.replace("-", "_")] = value

        create_initial_instance(
            dest_path,
            db_storage=kwargs.get("db_storage", "instance"),
            base_path=kwargs.get("base_path", "var"),
            initial_zope_username=kwargs.get("initial_zope_username", "admin"),
            initial_user_password=kwargs.get("initial_user_password", "admin"),
            zeo_address=kwargs.get("zeo_address", "localhost:8100"),
            pg_host=kwargs.get("pg_host", "localhost"),
            pg_port=kwargs.get("pg_port", "5432"),
            pg_dbname=kwargs.get("pg_dbname", ""),
            pg_user=kwargs.get("pg_user", "plone"),
            pg_password=kwargs.get("pg_password", ""),
        )

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
