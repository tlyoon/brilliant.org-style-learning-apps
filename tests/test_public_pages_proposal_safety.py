"""BSA228: synthetic public Pages PR-mode and Chapter9 immutable-scope gate.

No public GitHub requests, pushes, merges, or source PDF/model calls.
Tests inspect the real entrypoint with a fully fake Git and build transport.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from app_generator.errors import GitPublishError
from app_generator.publishing.public import PublicPagesPublisher


class FakePagesPublisher(PublicPagesPublisher):
    def __init__(self, config):
        super().__init__(config)
        self.commands=[]
        self.merged=False
    def _run(self,arguments,*,cwd=None,check=True):
        self.commands.append(arguments)
        if arguments[:2]==["git","clone"]:
            Path(arguments[-1]).mkdir(parents=True,exist_ok=True)
        if arguments[:3]==["gh","pr","merge"]:
            self.merged=True
        return ""
    def _pr_for_branch(self,branch):
        return {
            "url":"https://github.com/example/pages/pull/1",
            "state":"MERGED" if self.merged else "OPEN",
            "mergedAt":"2026-11-20" if self.merged else None,
        }


class SafePublicProposalTests(unittest.TestCase):
    def setUp(self):
        directory=TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)
        self.package=self.root/"package.json"
        self.package.write_text('{"fake":true}',encoding="utf8")
        self.config=SimpleNamespace(
            state_dir=self.root/"private",
            repo_root=self.root,
            public_deploy_repository="example/pages",
            public_deploy_base_branch="main",
            public_deploy_base_url="https://example.github.io/pages/",
            public_deploy_branch_prefix="automation/public-release",
            public_deploy_auto_merge=False,
        )

    @staticmethod
    def fake_build(output,package_path,**_):
        output.mkdir(parents=True)
        (output/"content").mkdir()
        (output/"content"/"package.json").write_bytes(
            package_path.read_bytes())
        (output/"index.html").write_text("fake release page")

    def run_fake(self,*,auto_merge=False):
        self.config.public_deploy_auto_merge=auto_merge
        publisher=FakePagesPublisher(self.config)
        calls=[]
        with patch("app_generator.publishing.public.enforce_academic_release_gate"
                   ) as gate, patch("app_generator.publishing.public.build",
                                    side_effect=self.fake_build):
            result=publisher.publish(
                package_path=self.package,subchapter_id="8.1",
                ensure_lease=lambda:calls.append("lease"))
        gate.assert_called_once()
        return publisher,result,calls

    def test_non_auto_mode_never_merges_public_pull_request(self):
        publisher,result,leases=self.run_fake(auto_merge=False)
        self.assertFalse(result.merged)
        self.assertEqual("https://github.com/example/pages/pull/1",
                         result.pr_url)
        self.assertNotIn(["gh","pr","merge",result.pr_url,"--merge",
                          "--repo","example/pages"],publisher.commands)
        self.assertGreater(len(leases),0)

    def test_explicit_nonprotected_auto_merge_keeps_intended_behavior(self):
        publisher,result,_=self.run_fake(auto_merge=True)
        self.assertTrue(result.merged)
        self.assertTrue(any(args[:3]==["gh","pr","merge"]
                            for args in publisher.commands))

    def test_existing_chapter9_automated_merge_blocked_before_public_io(self):
        self.config.public_deploy_repository="tlyoon/section-8-1-learning-app"
        self.config.public_deploy_auto_merge=True
        publisher=FakePagesPublisher(self.config)
        leases=[]
        with patch("app_generator.publishing.public.enforce_academic_release_gate") as gate:
            with self.assertRaisesRegex(GitPublishError,
                                        "pinned non-destructive release proposal"):
                publisher.publish(
                    package_path=self.package,subchapter_id="9.1",
                    ensure_lease=lambda:leases.append(1))
        self.assertEqual([],publisher.commands)
        self.assertEqual([],leases)
        gate.assert_not_called()

    def test_all_protected_chapter9_routes_reject_direct_merge(self):
        self.config.public_deploy_repository="tlyoon/section-8-1-learning-app"
        self.config.public_deploy_auto_merge=True
        publisher=FakePagesPublisher(self.config)
        for i in range(1,7):
            with self.subTest(section=i):
                with self.assertRaises(GitPublishError):
                    publisher.publish(
                        package_path=self.package,
                        subchapter_id=f"9.{i}",
                        ensure_lease=lambda:None)
        self.assertEqual([],publisher.commands)

    def test_valid_numeric_route_and_reject_injected_paths(self):
        publisher=FakePagesPublisher(self.config)
        self.assertEqual("section-9-1/",publisher.route_for("9.1"))
        for bad in ("9.1/../../../", "../9.1", "9/1", "9.1\\extra",
                    "", "9.1 \\n", "9.1/section-8-1"):
            with self.subTest(route=bad):
                with self.assertRaises(GitPublishError):
                    publisher.route_for(bad)

    def test_unset_auto_merge_mode_fails_safe(self):
        del self.config.public_deploy_auto_merge
        publisher=FakePagesPublisher(self.config)
        with patch("app_generator.publishing.public.enforce_academic_release_gate"
                   ),patch("app_generator.publishing.public.build",
                           side_effect=self.fake_build):
            result=publisher.publish(
                package_path=self.package,subchapter_id="8.1",
                ensure_lease=lambda:None)
        self.assertFalse(result.merged)


if __name__=="__main__":
    unittest.main()
