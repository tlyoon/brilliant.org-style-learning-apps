"""Publish validated artifacts on a unique branch and open a draft pull request."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from app_generator.config import GeneratorConfig
from app_generator.errors import GitPublishError


@dataclass(frozen=True)
class PublishResult:
    branch: str
    commit: str
    pr_url: str


class GitPublisher:
    def __init__(self, config: GeneratorConfig) -> None:
        self.config = config
        self.repo = config.repo_root

    def _run(self, arguments: list[str], *, check: bool = True) -> str:
        try:
            result = subprocess.run(
                arguments,
                cwd=self.repo,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except OSError as exc:
            raise GitPublishError(f"Could not execute {arguments[0]}: {exc}") from exc
        output = (result.stdout + "\n" + result.stderr).strip()
        if check and result.returncode:
            raise GitPublishError(f"Command failed ({' '.join(arguments)}): {output}")
        return output

    def sync_base(self) -> None:
        if self._run(["git", "status", "--porcelain"]):
            raise GitPublishError(
                "The repository worktree is not clean. Commit or stash unrelated work before starting an automated job."
            )
        remote = self.config.git_remote
        base = self.config.git_base_branch
        self._run(["git", "fetch", remote, "--prune"])
        self._run(["git", "switch", base])
        self._run(["git", "pull", "--ff-only", remote, base])

    def prepare_branch(self, *, subchapter_id: str, job_key: str) -> str:
        remote = self.config.git_remote
        slug = subchapter_id.replace(".", "-")
        branch = f"{self.config.git_branch_prefix}/section-{slug}-{job_key[:10]}"
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch:
            raise GitPublishError(f"Generated unsafe branch name: {branch}")
        local_exists = bool(self._run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], check=False))
        remote_exists = bool(
            self._run(["git", "ls-remote", "--heads", remote, f"refs/heads/{branch}"], check=False)
        )
        if local_exists or remote_exists:
            raise GitPublishError(
                f"The job branch already exists: {branch}. Inspect the previous attempt before retrying this job."
            )
        self._run(["git", "switch", "-c", branch])
        return branch

    def _run_full_tests(self) -> None:
        commands = (
            [sys.executable, "scripts/lint.py"],
            [sys.executable, "scripts/validate_content.py"],
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        )
        for command in commands:
            self._run(command)

    def _existing_pr(self, branch: str) -> str:
        return self._run(
            ["gh", "pr", "view", branch, "--json", "url", "--jq", ".url"],
            check=False,
        ).strip()

    def _create_pr(self, branch: str, title: str, body: str) -> str:
        existing = self._existing_pr(branch)
        if existing.startswith("https://"):
            return existing
        arguments = [
            "gh", "pr", "create", "--base", self.config.git_base_branch, "--head", branch,
            "--title", title, "--body", body,
        ]
        if self.config.git_create_draft_pr:
            arguments.append("--draft")
        last_error = ""
        for delay in (0, 2, 5):
            if delay:
                time.sleep(delay)
            output = self._run(arguments, check=False)
            url = next((line.strip() for line in output.splitlines() if line.strip().startswith("https://")), "")
            if url:
                return url
            existing = self._existing_pr(branch)
            if existing.startswith("https://"):
                return existing
            last_error = output
        raise GitPublishError(f"Branch was pushed, but the draft pull request could not be created: {last_error}")

    def publish(
        self,
        *,
        branch: str,
        installed_paths: Iterable[Path],
        subchapter: str,
        package_id: str,
        ensure_lease: Callable[[], None],
    ) -> PublishResult:
        if self.config.git_run_full_tests:
            self._run_full_tests()
        ensure_lease()
        relative = [str(path.resolve().relative_to(self.repo.resolve())) for path in installed_paths]
        self._run(["git", "add", "--", *relative])
        self._run(["git", "diff", "--cached", "--check"])
        title = f"Generate {subchapter} learning-content draft"
        self._run(["git", "commit", "-m", title])
        commit = self._run(["git", "rev-parse", "HEAD"]).splitlines()[0].strip()
        ensure_lease()
        self._run(["git", "push", "--set-upstream", self.config.git_remote, branch])
        body = (
            f"Automated generation for `{package_id}`. The source PDF was attached to a fresh Gem conversation "
            "and was not committed. Deterministic repository checks passed. The package remains a draft pending "
            "qualified physics, instructional, language, accessibility, and provenance review."
        )
        pr_url = self._create_pr(branch, title, body)
        return PublishResult(branch=branch, commit=commit, pr_url=pr_url)
