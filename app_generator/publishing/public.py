"""Deterministic, PR-based publication of minimal GitHub Pages review bundles."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app_generator.errors import GitPublishError
from scripts.build_public_release import build


@dataclass(frozen=True)
class PublicDeployResult:
    branch: str
    pr_url: str
    package_sha256: str
    public_url: str
    merged: bool


class PublicPagesPublisher:
    """Publish one package into a route through a deterministic public-repo PR.

    The package digest is part of the branch name.  Therefore a retry, including
    one from another workstation, discovers the same PR instead of creating a
    second write.  Different sections touch different route directories and can
    proceed concurrently.
    """

    def __init__(self, config: object) -> None:
        self.config = config

    @staticmethod
    def package_digest(package_path: Path) -> str:
        return hashlib.sha256(package_path.read_bytes()).hexdigest()

    def route_for(self, subchapter_id: str) -> str:
        route = f"section-{subchapter_id.replace('.', '-')}/"
        if not route.startswith("section-") or ".." in Path(route).parts:
            raise GitPublishError(f"Unsafe public review route: {route}")
        return route

    def branch_for(self, subchapter_id: str, digest: str) -> str:
        return f"{self.config.public_deploy_branch_prefix}/section-{subchapter_id.replace('.', '-')}-{digest[:12]}"

    def public_url_for(self, subchapter_id: str) -> str:
        return f"{self.config.public_deploy_base_url}section-{subchapter_id.replace('.', '-')}/"

    def _run(self, arguments: list[str], *, cwd: Path | None = None, check: bool = True) -> str:
        result = subprocess.run(
            arguments, cwd=cwd, check=False, capture_output=True, text=True, encoding="utf-8"
        )
        if check and result.returncode:
            raise GitPublishError(result.stderr.strip() or result.stdout.strip() or "Public deployment command failed")
        return result.stdout.strip()

    def _pr_for_branch(self, branch: str) -> dict[str, object] | None:
        output = self._run([
            "gh", "pr", "list", "--repo", self.config.public_deploy_repository,
            "--head", branch, "--state", "all", "--json", "url,state,mergedAt",
        ])
        try:
            entries = json.loads(output or "[]")
        except json.JSONDecodeError as exc:
            raise GitPublishError("GitHub returned invalid pull-request data for public review deployment") from exc
        return entries[0] if entries else None

    @staticmethod
    def _merged(info: dict[str, object]) -> bool:
        return str(info.get("state", "")).upper() == "MERGED" or bool(info.get("mergedAt"))

    def publish(
        self,
        *,
        package_path: Path,
        subchapter_id: str,
        ensure_lease: Callable[[], None],
    ) -> PublicDeployResult:
        digest = self.package_digest(package_path)
        branch = self.branch_for(subchapter_id, digest)
        public_url = self.public_url_for(subchapter_id)
        existing = self._pr_for_branch(branch)
        if existing and self._merged(existing):
            return PublicDeployResult(branch, str(existing.get("url", "")), digest, public_url, True)

        ensure_lease()
        # Always re-materialize the deterministic branch. An earlier PC can have
        # pushed it and crashed before creating its PR; treating that branch as a
        # recoverable handoff is what prevents duplicate review deployments.
        with tempfile.TemporaryDirectory(prefix="public-review-") as directory:
            checkout = Path(directory) / "pages"
            clone_url = f"https://github.com/{self.config.public_deploy_repository}.git"
            self._run(["git", "clone", "--origin", "origin", clone_url, str(checkout)])
            remote_branch = self._run(["git", "ls-remote", "--heads", "origin", f"refs/heads/{branch}"], cwd=checkout)
            if remote_branch:
                self._run(["git", "fetch", "origin", f"refs/heads/{branch}:refs/heads/{branch}"], cwd=checkout)
                self._run(["git", "switch", branch], cwd=checkout)
            else:
                self._run(["git", "fetch", "origin", self.config.public_deploy_base_branch], cwd=checkout)
                self._run([
                    "git", "switch", "-c", branch,
                    f"origin/{self.config.public_deploy_base_branch}",
                ], cwd=checkout)
            route = checkout / self.route_for(subchapter_id)
            # route_for is deliberately constrained before this replacement.
            if route.exists():
                shutil.rmtree(route)
            bundle = Path(directory) / "bundle"
            build(bundle, package_path, source_root=self.config.repo_root)
            shutil.copytree(bundle, route)
            self._run(["git", "add", "--", self.route_for(subchapter_id)], cwd=checkout)
            self._run(["git", "diff", "--cached", "--check"], cwd=checkout)
            changed = bool(self._run(["git", "diff", "--cached", "--name-only"], cwd=checkout))
            if changed:
                self._run([
                    "git", "commit", "-m", f"Publish draft review Section {subchapter_id}",
                ], cwd=checkout)
                ensure_lease()
                self._run(["git", "push", "--set-upstream", "origin", branch], cwd=checkout)
        existing = self._pr_for_branch(branch)
        if not existing:
            url = self._run([
                "gh", "pr", "create", "--repo", self.config.public_deploy_repository,
                "--head", branch, "--base", self.config.public_deploy_base_branch,
                "--title", f"Publish draft review Section {subchapter_id}",
                "--body", "Automated draft/review deployment. This is not human scientific approval.",
            ], check=False)
            existing = self._pr_for_branch(branch)
            if not existing:
                if not url.startswith("https://"):
                    raise GitPublishError("Public review branch was pushed but its pull request could not be created")
                existing = {"url": url, "state": "OPEN"}

        ensure_lease()
        pr_url = str(existing.get("url", ""))
        if str(existing.get("state", "")).upper() == "CLOSED" and not self._merged(existing):
            # A prior worker/operator may have closed the deterministic PR after
            # the branch was pushed. Reopen the same handoff rather than creating
            # a duplicate branch/PR or forcing regeneration.
            self._run(["gh", "pr", "reopen", pr_url, "--repo", self.config.public_deploy_repository])
            existing = self._pr_for_branch(branch) or existing
            pr_url = str(existing.get("url", pr_url))
        self._run(["gh", "pr", "merge", pr_url, "--merge", "--repo", self.config.public_deploy_repository])
        info = self._pr_for_branch(branch)
        if not info or not self._merged(info):
            raise GitPublishError(f"Public review PR did not merge: {pr_url}")
        return PublicDeployResult(branch, str(info.get("url", pr_url)), digest, public_url, True)
