#!/usr/bin/env python3
"""Git status check hook for copier templates."""
import subprocess
import sys
from pathlib import Path


def check_git_status(path: Path | None = None) -> dict:
    """
    Check git repository status.

    Args:
        path: Directory to check (defaults to current directory)

    Returns:
        Dictionary with:
        - is_git_repo: bool
        - is_clean: bool
        - has_uncommitted: bool
        - untracked_files: list[str]
        - modified_files: list[str]
    """
    path = path or Path.cwd()

    result = {
        "is_git_repo": False,
        "is_clean": False,
        "has_uncommitted": False,
        "untracked_files": [],
        "modified_files": [],
    }

    # Check if it's a git repository
    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=path,
            capture_output=True,
            check=True,
        )
        result["is_git_repo"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return result

    # Get status
    try:
        status_output = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        lines = status_output.stdout.strip().split("\n") if status_output.stdout.strip() else []

        for line in lines:
            if not line:
                continue
            status = line[:2]
            filename = line[3:]

            if status.startswith("?"):
                result["untracked_files"].append(filename)
            else:
                result["modified_files"].append(filename)
                result["has_uncommitted"] = True

        result["is_clean"] = not lines

    except subprocess.CalledProcessError:
        pass

    return result


def require_clean_git(path: Path | None = None, allow_untracked: bool = True) -> None:
    """
    Exit with error if git repository is not clean.

    Args:
        path: Directory to check (defaults to current directory)
        allow_untracked: Whether to allow untracked files

    Raises:
        SystemExit: If repository has uncommitted changes
    """
    status = check_git_status(path)

    if not status["is_git_repo"]:
        # Not a git repo, allow proceeding
        return

    if status["has_uncommitted"]:
        print("\n" + "=" * 60)
        print("ERROR: Git repository has uncommitted changes!")
        print("=" * 60)
        print("\nPlease commit or stash your changes before running this template.")
        print("\nModified files:")
        for f in status["modified_files"]:
            print(f"  - {f}")
        print("\n" + "=" * 60 + "\n")
        sys.exit(1)

    if not allow_untracked and status["untracked_files"]:
        print("\n" + "=" * 60)
        print("ERROR: Git repository has untracked files!")
        print("=" * 60)
        print("\nPlease commit or remove untracked files before running this template.")
        print("\nUntracked files:")
        for f in status["untracked_files"]:
            print(f"  - {f}")
        print("\n" + "=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    # Used as pre-copy hook
    require_clean_git()
