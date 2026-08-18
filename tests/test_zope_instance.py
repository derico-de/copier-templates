"""Tests for zope_instance template."""

from helpers import assert_dir_exists, assert_file_exists, read_toml, run_copier


def _create_project(temp_dir, zope_setup_template, **extra_data):
    """Helper to create a zope-setup project for testing."""
    data = {"project_name": "my-project", **extra_data}
    result = run_copier(zope_setup_template, temp_dir / "my-project", data=data)
    assert result.returncode == 0, f"zope-setup failed: {result.stderr}"
    return temp_dir / "my-project"


class TestZopeInstanceRequiresProject:
    """Test that zope_instance requires a zope-setup project."""

    def test_fails_without_project(self, temp_dir, zope_instance_template):
        """zope_instance fails if no zope-setup project detected."""
        dest = temp_dir / "empty"
        dest.mkdir()
        result = run_copier(
            zope_instance_template,
            dest,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert result.returncode != 0

    def test_succeeds_inside_project(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance succeeds when run inside a zope-setup project."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        result = run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert result.returncode == 0, f"zope_instance failed: {result.stderr}"


class TestZopeInstanceCreatesFiles:
    """Test that zope_instance creates expected files."""

    def test_creates_instance_directory(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance creates named instance directory inside base_path."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert_dir_exists(project_dir / "var/instance1")
        assert_dir_exists(project_dir / "var/instance1/etc")
        assert_dir_exists(project_dir / "var/instance1/var")

    def test_creates_zope_conf(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance creates zope.conf."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.conf",
            content_contains="instancehome",
        )

    def test_creates_zope_ini(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance creates zope.ini with correct port."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.ini",
            content_contains="port = 8081",
        )

    def test_creates_inituser(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance creates inituser file."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert_file_exists(
            project_dir / "var/instance1/inituser",
            content_contains="admin:admin",
        )

    def test_creates_answers_file(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance creates per-instance answers file."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert_file_exists(project_dir / ".copier-answers.zope-instance-instance1.yml")


class TestZopeInstancePaths:
    """Test path handling with base_path."""

    def test_default_base_path(self, temp_dir, zope_setup_template, zope_instance_template):
        """With default base_path (var), instance_home includes var/ prefix."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        zope_conf = project_dir / "var/instance1/etc/zope.conf"
        content = zope_conf.read_text()
        assert "%define INSTANCEHOME var/instance1" in content
        assert "%define CLIENTHOME var/instance1" in content

    def test_custom_base_path(self, temp_dir, zope_setup_template, zope_instance_template):
        """With custom base_path, instance_home and file placement match."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={
                "instance_name": "instance1",
                "port": 8081,
                "base_path": "deploy/instances",
            },
        )
        zope_conf = project_dir / "deploy/instances/instance1/etc/zope.conf"
        content = zope_conf.read_text()
        assert "%define INSTANCEHOME deploy/instances/instance1" in content
        assert "%define CLIENTHOME deploy/instances/instance1" in content


class TestZopeInstancePort:
    """Test port configuration."""

    def test_default_port(self, temp_dir, zope_setup_template, zope_instance_template):
        """Default port is 8080."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1"},
        )
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.ini",
            content_contains="port = 8080",
        )

    def test_custom_port(self, temp_dir, zope_setup_template, zope_instance_template):
        """Custom port is rendered in zope.ini."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 9090},
        )
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.ini",
            content_contains="port = 9090",
        )


class TestZopeInstanceHost:
    """Test host binding configuration."""

    def test_standalone_project_binds_loopback(
        self, temp_dir, zope_setup_template, zope_instance_template
    ):
        """A standalone project is a deployment target: bind to 127.0.0.1."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.ini",
            content_contains="host = 127.0.0.1",
        )

    def test_initial_instance_binds_loopback(self, temp_dir, zope_setup_template):
        """The instance created by zope-setup itself also binds to 127.0.0.1."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        assert_file_exists(
            project_dir / "var/instance/etc/zope.ini",
            content_contains="host = 127.0.0.1",
        )

    def test_addon_project_binds_all_interfaces(
        self, temp_dir, backend_addon_template, zope_setup_template, zope_instance_template
    ):
        """Inside an addon the instance is a dev server: bind to 0.0.0.0."""
        pkg_dir = temp_dir / "myaddon"
        result = run_copier(
            backend_addon_template, pkg_dir, data={"package_name": "collective.myaddon"}
        )
        assert result.returncode == 0, f"backend_addon failed: {result.stderr}"

        result = run_copier(zope_setup_template, pkg_dir, data={})
        assert result.returncode == 0, f"zope-setup failed: {result.stderr}"
        assert_file_exists(
            pkg_dir / "var/instance/etc/zope.ini",
            content_contains="host = 0.0.0.0",
        )

        result = run_copier(
            zope_instance_template,
            pkg_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert result.returncode == 0, f"zope_instance failed: {result.stderr}"
        assert_file_exists(
            pkg_dir / "var/instance1/etc/zope.ini",
            content_contains="host = 0.0.0.0",
        )

    def test_custom_host(self, temp_dir, zope_setup_template, zope_instance_template):
        """Custom host is rendered in zope.ini."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081, "host": "10.0.0.5"},
        )
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.ini",
            content_contains="host = 10.0.0.5",
        )


class TestZopeInstanceDbStorage:
    """Test database storage configuration."""

    def test_relstorage_config(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance renders relstorage config when specified."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081, "db_storage": "relstorage"},
        )
        zope_conf = project_dir / "var/instance1/etc/zope.conf"
        assert_file_exists(zope_conf, content_contains="<relstorage>")

    def test_instance_storage(self, temp_dir, zope_setup_template, zope_instance_template):
        """zope_instance renders filestorage config with instance db_storage."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081, "db_storage": "instance"},
        )
        zope_conf = project_dir / "var/instance1/etc/zope.conf"
        assert_file_exists(zope_conf, content_contains="<filestorage>")


class TestMultipleInstances:
    """Test creating multiple instances."""

    def test_two_instances(self, temp_dir, zope_setup_template, zope_instance_template):
        """Can create multiple instances in the same project."""
        project_dir = _create_project(temp_dir, zope_setup_template)

        result1 = run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        assert result1.returncode == 0, f"instance1 failed: {result1.stderr}"

        result2 = run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance2", "port": 8082},
        )
        assert result2.returncode == 0, f"instance2 failed: {result2.stderr}"

        # Both directories exist inside var/
        assert_dir_exists(project_dir / "var/instance1")
        assert_dir_exists(project_dir / "var/instance2")

        # Each has its own port
        assert_file_exists(
            project_dir / "var/instance1/etc/zope.ini",
            content_contains="port = 8081",
        )
        assert_file_exists(
            project_dir / "var/instance2/etc/zope.ini",
            content_contains="port = 8082",
        )

        # Each has its own answers file
        assert_file_exists(project_dir / ".copier-answers.zope-instance-instance1.yml")
        assert_file_exists(project_dir / ".copier-answers.zope-instance-instance2.yml")

    def test_instances_registered_in_pyproject(self, temp_dir, zope_setup_template, zope_instance_template):
        """Instances are registered in project settings."""
        project_dir = _create_project(temp_dir, zope_setup_template)

        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance1", "port": 8081},
        )
        run_copier(
            zope_instance_template,
            project_dir,
            data={"instance_name": "instance2", "port": 8082},
        )

        pyproject = read_toml(project_dir / "pyproject.toml")
        instances = pyproject["tool"]["plone"]["project"]["settings"]["instances"]
        assert "instance1" in instances
        assert "instance2" in instances


class TestZopeSetupTasksIntegration:
    """Test that zope-setup tasks.py includes create_instance task."""

    def test_tasks_has_create_instance(self, temp_dir, zope_setup_template):
        """Generated tasks.py includes create_instance task."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        assert_file_exists(
            project_dir / "tasks.py",
            content_contains="def create_instance",
        )

    def test_tasks_has_instance_parameter(self, temp_dir, zope_setup_template):
        """Generated tasks.py start/debug/shell accept instance parameter."""
        project_dir = _create_project(temp_dir, zope_setup_template)
        tasks_content = (project_dir / "tasks.py").read_text()
        assert 'def start(c, instance="instance")' in tasks_content
        assert 'def debug(c, instance="instance")' in tasks_content
        assert 'def shell(c, instance="instance")' in tasks_content
