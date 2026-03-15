"""Tests for zope-setup template."""
import pytest

from helpers import assert_dir_exists, assert_file_exists, read_toml, run_copier


class TestZopeSetupIsolated:
    """Test zope-setup template in isolation."""

    def test_creates_project_structure(self, temp_dir, zope_setup_template):
        """Zope-setup creates correct project structure."""
        result = run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )
        assert result.returncode == 0, f"Copier failed: {result.stderr}"

        # Verify structure
        project_dir = temp_dir / "my-project"
        assert_file_exists(project_dir / "pyproject.toml")
        assert_dir_exists(project_dir / "instance")
        assert_dir_exists(project_dir / "sources")

    def test_pyproject_has_project_settings(self, temp_dir, zope_setup_template):
        """Zope-setup includes custom project settings namespace."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        pyproject = temp_dir / "my-project/pyproject.toml"
        assert_file_exists(
            pyproject,
            content_contains="[tool.plone.project.settings]",
        )

    def test_project_settings_contain_plone_version(self, temp_dir, zope_setup_template):
        """Project settings include plone_version."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={
                "project_name": "my-project",
                "plone_version": "6.1.1",
            },
        )

        pyproject = temp_dir / "my-project/pyproject.toml"
        data = read_toml(pyproject)
        settings = data["tool"]["plone"]["project"]["settings"]
        assert settings["plone_version"] == "6.1.1"

    def test_creates_zope_conf(self, temp_dir, zope_setup_template):
        """Zope-setup creates rendered zope.conf."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        zope_conf = temp_dir / "my-project/instance/etc/zope.conf"
        assert_file_exists(zope_conf, content_contains="<filestorage>")

    def test_creates_gitignore(self, temp_dir, zope_setup_template):
        """Zope-setup creates .gitignore file."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        gitignore = temp_dir / "my-project/.gitignore"
        assert_file_exists(gitignore)

    def test_creates_tasks_file(self, temp_dir, zope_setup_template):
        """Zope-setup creates tasks.py for invoke."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        tasks = temp_dir / "my-project/tasks.py"
        assert_file_exists(tasks, content_contains="from invoke import")

    def test_tasks_use_uv_run(self, temp_dir, zope_setup_template):
        """Zope-setup tasks.py uses uv run for all commands."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        tasks = temp_dir / "my-project/tasks.py"
        assert_file_exists(tasks, content_contains="uv run runwsgi")
        assert_file_exists(tasks, content_contains="uv run pytest")
        assert_file_exists(tasks, content_contains="uv run ruff")

    def test_distribution_options(self, temp_dir, zope_setup_template):
        """Zope-setup handles different distribution options."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={
                "project_name": "my-project",
                "distribution": "plone.volto",
            },
        )

        pyproject = temp_dir / "my-project/pyproject.toml"
        data = read_toml(pyproject)
        settings = data["tool"]["plone"]["project"]["settings"]
        assert settings["distribution"] == "plone.volto"

    def test_db_storage_options(self, temp_dir, zope_setup_template):
        """Zope-setup handles different database storage options."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={
                "project_name": "my-project",
                "db_storage": "relstorage",
            },
        )

        pyproject = temp_dir / "my-project/pyproject.toml"
        data = read_toml(pyproject)
        settings = data["tool"]["plone"]["project"]["settings"]
        assert settings["db_storage"] == "relstorage"

    def test_zope_conf_no_temporarystorage(self, temp_dir, zope_setup_template):
        """Zope-setup does not include deprecated temporarystorage section."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        zope_conf = temp_dir / "my-project/instance/etc/zope.conf"
        content = zope_conf.read_text()
        assert "temporarystorage" not in content
        assert "temp_folder" not in content
        assert "TemporaryContainer" not in content

    def test_zope_conf_relstorage(self, temp_dir, zope_setup_template):
        """Zope-setup renders relstorage config in zope.conf."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={
                "project_name": "my-project",
                "db_storage": "relstorage",
            },
        )

        zope_conf = temp_dir / "my-project/instance/etc/zope.conf"
        assert_file_exists(zope_conf, content_contains="<relstorage>")
        assert_file_exists(zope_conf, content_contains="dbname=plone_my_project")

    def test_creates_inituser_with_defaults(self, temp_dir, zope_setup_template):
        """Zope-setup creates inituser file with default credentials."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        inituser = temp_dir / "my-project/instance/inituser"
        assert_file_exists(inituser, content_contains="admin:admin")

    def test_creates_inituser_with_custom_credentials(self, temp_dir, zope_setup_template):
        """Zope-setup creates inituser file with custom username and password."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={
                "project_name": "my-project",
                "initial_zope_username": "manager",
                "initial_user_password": "secret123",
            },
        )

        inituser = temp_dir / "my-project/instance/inituser"
        assert_file_exists(inituser, content_contains="manager:secret123")

    def test_gitignore_excludes_inituser(self, temp_dir, zope_setup_template):
        """Zope-setup .gitignore excludes inituser file."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        gitignore = temp_dir / "my-project/.gitignore"
        assert_file_exists(gitignore, content_contains="instance/inituser")

    def test_creates_copier_answers_file(self, temp_dir, zope_setup_template):
        """Zope-setup creates copier answers file."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        answers = temp_dir / "my-project/.copier-answers.zope-setup.yml"
        assert_file_exists(answers)


class TestZopeSetupGitHubActions:
    """Test GitHub Actions workflow generation."""

    def test_creates_ci_workflow(self, temp_dir, zope_setup_template):
        """Zope-setup creates CI workflow file."""
        run_copier(
            zope_setup_template,
            temp_dir / "my-project",
            data={"project_name": "my-project"},
        )

        ci = temp_dir / "my-project/.github/workflows/ci.yml"
        assert_file_exists(ci)
