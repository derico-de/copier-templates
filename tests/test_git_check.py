"""Tests for template git-status scoping."""

import subprocess

from shared.hooks.git_check import check_git_status


def test_parent_repository_is_not_used_for_generated_project(temp_dir):
    """A nested project does not inherit dirtiness from an outer repository."""
    subprocess.run(["git", "init", "-q"], cwd=temp_dir, check=True)
    outer_file = temp_dir / "outer.txt"
    outer_file.write_text("dirty\n")
    project = temp_dir / "generated"
    project.mkdir()

    status = check_git_status(project)

    assert status["is_git_repo"] is False
    assert status["modified_files"] == []
    assert status["untracked_files"] == []
