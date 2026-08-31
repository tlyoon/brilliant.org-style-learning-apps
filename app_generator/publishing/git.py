"""Publish validated artifacts with crash-safe deterministic Git handoff."""

from __future__ import annotations

import json
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
    merged: bool


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

    def refresh_remote(self) -> None:
        """Refresh remote refs without changing the current branch."""

        self._run(["git", "fetch", self.config.git_remote, "--prune"])

    def job_branch(self, *, subchapter_id: str, job_key: str) -> str:
        slug = subchapter_id.replace(".", "-")
        branch = f"{self.config.git_branch_prefix}/section-{slug}-{job_key[:10]}"
        if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch) or ".." in branch:
            raise GitPublishError(f"Generated unsafe branch name: {branch}")
        return branch

    def _local_branch_exists(self, branch: str) -> bool:
        return bool(
            self._run(
                ["git", "show-ref", "--verify", f"refs/heads/{branch}"],
                check=False,
            ).strip()
        )

    def _remote_branch_exists(self, branch: str) -> bool:
        return bool(
            self._run(
                ["git", "ls-remote", "--heads", self.config.git_remote, f"refs/heads/{branch}"],
                check=False,
            ).strip()
        )

    def _local_commits_ahead(self, branch: str) -> int:
        output = self._run(
            ["git", "rev-list", "--count", f"{self.config.git_base_branch}..{branch}"]
        ).strip()
        try:
            return int(output)
        except ValueError as exc:
            raise GitPublishError(f"Git returned an invalid ahead count for {branch}: {output!r}") from exc

    def _pr_for_branch(self, branch: str) -> dict[str, object]:
        output = self._run(
            [
                "gh", "pr", "list", "--state", "all", "--head", branch,
                "--base", self.config.git_base_branch, "--limit", "1",
                "--json", "url,state,mergedAt,headRefOid",
            ],
            check=False,
        ).strip()
        if not output.startswith("["):
            return {}
        try:
            payload = json.loads(output)
        except json.JSONDecodeError:
            return {}
        if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
            return {}
        return payload[0]

    @staticmethod
    def _pr_is_merged(info: dict[str, object]) -> bool:
        return bool(info.get("mergedAt")) or str(info.get("state", "")).upper() == "MERGED"

    def _existing_pr(self, branch: str) -> str:
        return str(self._pr_for_branch(branch).get("url", "")).strip()

    @staticmethod
    def _title(subchapter: str) -> str:
        return f"Generate {subchapter} learning-content draft"

    @staticmethod
    def _body(package_id: str) -> str:
        return (
            f"Automated generation for `{package_id}`. The source PDF was attached to a fresh Gem conversation "
            "and was not committed. Deterministic repository checks passed. The package remains a draft pending "
            "qualified physics, instructional, language, accessibility, and provenance review."
        )

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

    def _ensure_pr(self, branch: str, *, subchapter: str, package_id: str) -> dict[str, object]:
        info = self._pr_for_branch(branch)
        if info and self._pr_is_merged(info):
            return info
        if info and str(info.get("state", "")).upper() == "OPEN":
            return info
        if info and str(info.get("state", "")).upper() == "CLOSED":
            url = str(info.get("url", ""))
            output = self._run(["gh", "pr", "reopen", url], check=False)
            reopened = self._pr_for_branch(branch)
            if str(reopened.get("state", "")).upper() == "OPEN":
                return reopened
            raise GitPublishError(f"Could not reopen the existing generated-content pull request {url}: {output}")
        url = self._create_pr(branch, self._title(subchapter), self._body(package_id))
        info = self._pr_for_branch(branch)
        if info:
            return info
        return {"url": url, "state": "OPEN", "mergedAt": None}

    def _merge_pr(self, pr_url: str) -> None:
        self._run(["gh", "pr", "merge", pr_url, "--merge"])
        payload = self._run(["gh", "pr", "view", pr_url, "--json", "state,mergedAt"])
        try:
            status = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise GitPublishError("GitHub returned an invalid merge-verification response") from exc
        if status.get("state") != "MERGED" or not status.get("mergedAt"):
            raise GitPublishError("GitHub did not confirm that the generated-content pull request merged")

    def _finalize_pr(self, branch: str, *, subchapter: str, package_id: str) -> tuple[str, bool]:
        info = self._ensure_pr(branch, subchapter=subchapter, package_id=package_id)
        pr_url = str(info.get("url", "")).strip()
        if not pr_url:
            raise GitPublishError(f"GitHub did not return a pull request URL for {branch}")
        merged = self._pr_is_merged(info)
        if self.config.git_auto_merge and not merged:
            self._merge_pr(pr_url)
            merged = True
        return pr_url, merged

    def _expected_relative_paths(self, paths: Iterable[Path]) -> tuple[str, ...]:
        relative: list[str] = []
        for path in paths:
            candidate = path.resolve() if path.is_absolute() else (self.repo / path).resolve()
            try:
                relative.append(candidate.relative_to(self.repo.resolve()).as_posix())
            except ValueError as exc:
                raise GitPublishError(f"Generated path is outside the repository: {path}") from exc
        return tuple(relative)

    def _verify_expected_changes(self, ref: str, expected_paths: Iterable[Path]) -> None:
        relative = self._expected_relative_paths(expected_paths)
        changed = set(
            line.strip().replace("\\", "/")
            for line in self._run(
                ["git", "diff", "--name-only", f"{self.config.git_base_branch}..{ref}", "--", *relative]
            ).splitlines()
            if line.strip()
        )
        missing = sorted(set(relative) - changed)
        if missing:
            raise GitPublishError(
                f"Existing job branch {ref} does not contain the complete expected generated handoff: "
                + ", ".join(missing)
            )

    def has_recoverable_handoff(self, *, subchapter_id: str, job_key: str) -> bool:
        """Return whether this exact deterministic job has a recoverable Git handoff.

        Empty local branches left before a job commit are safe to delete because the
        synchronized base branch remains authoritative and the generator checkpoints
        contain the only recoverable in-progress content.
        """

        branch = self.job_branch(subchapter_id=subchapter_id, job_key=job_key)
        info = self._pr_for_branch(branch)
        if info and self._pr_is_merged(info):
            return True
        if self._remote_branch_exists(branch):
            return True
        if not self._local_branch_exists(branch):
            return False
        if self._local_commits_ahead(branch) == 0:
            self._run(["git", "branch", "-D", branch])
            return False
        return True

    def recover_handoff(
        self,
        *,
        subchapter_id: str,
        job_key: str,
        expected_paths: Iterable[Path],
        subchapter: str,
        package_id: str,
        ensure_lease: Callable[[], None],
    ) -> PublishResult | None:
        """Finish a previously committed/pushed job without re-running Gemini."""

        branch = self.job_branch(subchapter_id=subchapter_id, job_key=job_key)
        info = self._pr_for_branch(branch)
        if info and self._pr_is_merged(info):
            ensure_lease()
            return PublishResult(
                branch=branch,
                commit=str(info.get("headRefOid", "")),
                pr_url=str(info.get("url", "")),
                merged=True,
            )

        remote = self.config.git_remote
        if self._remote_branch_exists(branch):
            ensure_lease()
            self._run([
                "git", "fetch", remote,
                f"refs/heads/{branch}:refs/remotes/{remote}/{branch}",
            ])
            remote_ref = f"{remote}/{branch}"
            self._verify_expected_changes(remote_ref, expected_paths)
            commit = self._run(["git", "rev-parse", remote_ref]).splitlines()[0].strip()
            pr_url, merged = self._finalize_pr(branch, subchapter=subchapter, package_id=package_id)
            return PublishResult(branch=branch, commit=commit, pr_url=pr_url, merged=merged)

        if self._local_branch_exists(branch):
            if self._local_commits_ahead(branch) == 0:
                self._run(["git", "branch", "-D", branch])
                return None
            self._verify_expected_changes(branch, expected_paths)
            ensure_lease()
            self._run(["git", "switch", branch])
            if self.config.git_run_full_tests:
                self._run_full_tests()
            ensure_lease()
            self._run(["git", "push", "--set-upstream", remote, branch])
            commit = self._run(["git", "rev-parse", "HEAD"]).splitlines()[0].strip()
            pr_url, merged = self._finalize_pr(branch, subchapter=subchapter, package_id=package_id)
            return PublishResult(branch=branch, commit=commit, pr_url=pr_url, merged=merged)

        return None

    def prepare_branch(self, *, subchapter_id: str, job_key: str) -> str:
        branch = self.job_branch(subchapter_id=subchapter_id, job_key=job_key)
        if self._remote_branch_exists(branch):
            raise GitPublishError(
                f"A durable job branch already exists for {branch}; auto reconciliation must recover it before regeneration."
            )
        if self._local_branch_exists(branch):
            if self._local_commits_ahead(branch) == 0:
                self._run(["git", "branch", "-D", branch])
            else:
                raise GitPublishError(
                    f"The local job branch {branch} contains unpublished commits; auto reconciliation must recover it."
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

    def _cleanup_generated_paths(self, relative: Iterable[str]) -> None:
        paths = list(relative)
        if not paths:
            return
        self._run(["git", "restore", "--staged", "--worktree", "--source=HEAD", "--", *paths], check=False)
        self._run(["git", "clean", "-f", "--", *paths], check=False)

    def publish(
        self,
        *,
        branch: str,
        installed_paths: Iterable[Path],
        subchapter: str,
        package_id: str,
        ensure_lease: Callable[[], None],
    ) -> PublishResult:
        relative = [str(path.resolve().relative_to(self.repo.resolve())) for path in installed_paths]
        try:
            if self.config.git_run_full_tests:
                self._run_full_tests()
            ensure_lease()
            self._run(["git", "add", "--", *relative])
            self._run(["git", "diff", "--cached", "--check"])
            title = self._title(subchapter)
            self._run(["git", "commit", "-m", title])
            commit = self._run(["git", "rev-parse", "HEAD"]).splitlines()[0].strip()
            ensure_lease()
            self._run(["git", "push", "--set-upstream", self.config.git_remote, branch])
            pr_url, merged = self._finalize_pr(branch, subchapter=subchapter, package_id=package_id)
            return PublishResult(branch=branch, commit=commit, pr_url=pr_url, merged=merged)
        except BaseException:
            self._cleanup_generated_paths(relative)
            raise
