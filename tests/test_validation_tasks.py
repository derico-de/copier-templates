"""Tests for subtemplate validation task configuration."""

import yaml

COPY_CONDITION = "{{ _copier_operation == 'copy' }}"


def test_validation_tasks_run_on_initial_copy(templates_dir):
    """Every validation task uses Copier's task operation variable."""
    validated_templates = set()

    for config_path in templates_dir.glob("*/copier.yml"):
        config = yaml.safe_load(config_path.read_text())
        for task in config.get("_tasks", []):
            if "validate" not in task.get("command", []):
                continue
            validated_templates.add(config_path.parent.name)
            assert task.get("when") == COPY_CONDITION, config_path

    assert validated_templates == {
        "behavior",
        "content_type",
        "controlpanel",
        "form",
        "indexer",
        "language",
        "mockup_pattern",
        "portlet",
        "restapi_service",
        "site_initialization",
        "subscriber",
        "svelte_app",
        "theme",
        "theme_barceloneta",
        "theme_basic",
        "upgrade_step",
        "view",
        "viewlet",
        "vocabulary",
        "zope_instance",
    }


def test_validation_tasks_do_not_report_post_copy_git_changes(templates_dir):
    """Post-copy validation must not mistake generated files for prior dirtiness."""
    for hook_path in templates_dir.glob("*/copier_hooks.py"):
        source = hook_path.read_text()
        if "def validate(" in source:
            assert "warn_git_unclean" not in source, hook_path
