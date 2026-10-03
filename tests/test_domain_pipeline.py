import json
import shutil
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from app_generator.domains import package_domain_errors, resolve_domain
from app_generator.domains.prompting import compose_domain_prompt, instruction_key_for_stage
from app_generator.generation.protocol import GenerationProtocol
from app_generator.runtime.orchestrator import _bind_domain_context
from app_generator.runtime.run_context import RunContext
from app_generator.validation.repository_checks import validate_candidate
from app_generator.visuals.validation import visual_contract_errors
from scripts.build_public_release import build


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "content" / "chapter-1" / "section-1-1" / "package.json"


class DomainPipelineTests(unittest.TestCase):
    def test_stage_mapping_covers_current_and_future_domain_aware_stages(self):
        self.assertEqual("sourceAnalysis", instruction_key_for_stage("source-analysis"))
        self.assertEqual("activityGeneration", instruction_key_for_stage("activity-plan"))
        self.assertEqual("activityGeneration", instruction_key_for_stage("mcq-easy-activity-one"))
        self.assertEqual("activityGeneration", instruction_key_for_stage("interactive-challenging"))
        self.assertEqual("semanticAudit", instruction_key_for_stage("semantic-audit-01"))
        self.assertEqual("semanticAudit", instruction_key_for_stage("whole-package-audit"))
        self.assertEqual("repair", instruction_key_for_stage("semantic-repair-activity-one"))
        self.assertEqual("repair", instruction_key_for_stage("repair-01-activity-00"))
        self.assertEqual("visualGeneration", instruction_key_for_stage("visual-plan-activity-one"))
        self.assertIsNone(instruction_key_for_stage("domain-discovery"))

    def test_domain_prompt_extension_precedes_and_cannot_replace_generic_contract(self):
        profile = resolve_domain(ROOT)
        generic = "GENERIC CONTRACT\n\nReturn exactly one valid JSON value."
        prompt = compose_domain_prompt(profile, "source-analysis", generic)
        extension_heading = profile.path("instructions", "sourceAnalysis").read_text(encoding="utf-8").splitlines()[0]
        self.assertIn(extension_heading, prompt)
        self.assertIn("generic stage contract", prompt.casefold())
        self.assertIn("remains authoritative", prompt)
        self.assertTrue(prompt.endswith(generic))
        self.assertEqual(generic, compose_domain_prompt(profile, "domain-discovery", generic))

    def test_generation_protocol_sends_composed_prompt_to_conversation(self):
        class Conversation:
            def __init__(self):
                self.calls = []

            def ask(self, prompt, *, stage=None):
                self.calls.append((stage, prompt))
                return 'BEGIN_JSON\n{"ok": true}\nEND_JSON'

        with tempfile.TemporaryDirectory() as directory:
            conversation = Conversation()
            protocol = GenerationProtocol(
                conversation,
                RunContext.create(Path(directory)),
                domain_profile=resolve_domain(ROOT),
            )
            self.assertEqual({"ok": True}, protocol._stage("activity-plan", lambda: "GENERIC ACTIVITY CONTRACT"))
            stage, prompt = conversation.calls[0]
            self.assertEqual("activity-plan", stage)
            self.assertIn("University-level physics activity-generation extension", prompt)
            self.assertTrue(prompt.endswith("GENERIC ACTIVITY CONTRACT"))

    def test_package_domain_identity_matches_active_profile_and_rejects_stale_version(self):
        profile = resolve_domain(ROOT)
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        package["domain"] = profile.identity()
        self.assertEqual([], package_domain_errors(ROOT, package, "package"))
        package["domain"]["profileVersion"] = "0.0.0-stale"
        errors = package_domain_errors(ROOT, package, "package")
        self.assertTrue(any("profileVersion" in error for error in errors), errors)

    def test_legacy_package_without_domain_identity_remains_compatible(self):
        package = json.loads(PACKAGE.read_text(encoding="utf-8"))
        package.pop("domain", None)
        self.assertEqual([], package_domain_errors(ROOT, package, "package"))

    def test_domain_context_invalidates_stale_cached_generation_stages(self):
        old = {"id": "old-domain", "profileVersion": "1", "subject": "old", "academicLevel": "university"}
        new = {"id": "new-domain", "profileVersion": "2", "subject": "new", "academicLevel": "university"}
        profile = SimpleNamespace(identity=lambda: new)
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("domain-context", old)
            context.save_stage("source-analysis", {"sectionTitle": "stale"})
            _bind_domain_context(context, profile)
            self.assertEqual(new, context.load_stage("domain-context"))
            self.assertIsNone(context.load_stage("source-analysis"))

    def test_preserved_domain_context_is_republished_after_checkpoint_clear(self):
        class Checkpoint:
            def __init__(self):
                self.saved = []
                self.deleted = []
                self.cleared = 0

            def save(self, name, document):
                self.saved.append((name, document))

            def delete(self, name):
                self.deleted.append(name)

            def clear(self):
                self.cleared += 1

        identity = {"id": "same-domain", "profileVersion": "1", "subject": "same", "academicLevel": "university"}
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Checkpoint()
            context = RunContext.create(Path(directory)).with_checkpoint(checkpoint)
            context.save_stage("domain-context", identity)
            context.save_stage("source-analysis", {"sectionTitle": "stale"})
            checkpoint.saved.clear()
            context.discard_parsed_stages(preserve={"domain-context"})
            self.assertEqual(1, checkpoint.cleared)
            self.assertEqual([("domain-context", identity)], checkpoint.saved)
            self.assertEqual(identity, context.load_stage("domain-context"))
            self.assertIsNone(context.load_stage("source-analysis"))

    def test_matching_domain_context_preserves_cached_generation_stages(self):
        identity = {"id": "same-domain", "profileVersion": "1", "subject": "same", "academicLevel": "university"}
        profile = SimpleNamespace(identity=lambda: identity)
        with tempfile.TemporaryDirectory() as directory:
            context = RunContext.create(Path(directory))
            context.save_stage("domain-context", identity)
            context.save_stage("source-analysis", {"sectionTitle": "kept"})
            _bind_domain_context(context, profile)
            self.assertEqual({"sectionTitle": "kept"}, context.load_stage("source-analysis"))

    def test_visual_validation_uses_package_declared_domain_validator(self):
        from tests.test_visual_contracts import package_with_visual

        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory) / "repo"
            shutil.copytree(ROOT / "domains", temp_root / "domains")
            shutil.copytree(ROOT / "content" / "schema", temp_root / "content" / "schema")
            alt_path = temp_root / "domains" / "alternate-domain"
            shutil.copytree(ROOT / "domains" / "university-level physics", alt_path)
            manifest_path = alt_path / "domain.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update({
                "id": "alternate-domain",
                "displayName": "Alternate Domain",
                "subject": "alternate-subject",
                "academicLevel": "university",
                "profileVersion": "9.9.9",
            })
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            validator_path = alt_path / manifest["validation"]["visualValidatorModule"]
            validator_path.write_text(
                'def visual_plan_errors(plan, label):\n    return [f"{label}: ALTERNATE-PLAN-VALIDATOR"]\n\n'
                'def visual_spec_errors(spec, label):\n    return [f"{label}: ALTERNATE-SPEC-VALIDATOR"]\n',
                encoding="utf-8",
            )
            registry_path = temp_root / "domains" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["domains"].append({"id": "alternate-domain", "path": "alternate-domain"})
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

            package = package_with_visual()
            package["domain"] = {
                "id": "alternate-domain",
                "profileVersion": "9.9.9",
                "subject": "alternate-subject",
                "academicLevel": "university",
            }
            errors = visual_contract_errors(temp_root, package, "package")
            self.assertTrue(any("ALTERNATE-PLAN-VALIDATOR" in error for error in errors), errors)
            self.assertTrue(any("ALTERNATE-SPEC-VALIDATOR" in error for error in errors), errors)

    def test_candidate_validation_resolves_domain_assets_from_repository_not_candidate_tree(self):
        profile = resolve_domain(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "candidate"
            relative = Path("content/chapter-1/section-1-1/package.json")
            package_dir = candidate / relative.parent
            package_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(PACKAGE.parent, package_dir)
            manifest_target = candidate / "content" / "source-manifests" / "chapter-1-section-1-1.json"
            manifest_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "content" / "source-manifests" / manifest_target.name, manifest_target)
            package = json.loads((candidate / relative).read_text(encoding="utf-8"))
            package["domain"] = profile.identity()
            (candidate / relative).write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self.assertEqual([], validate_candidate(ROOT, candidate, relative))

    def test_public_release_uses_domain_declared_by_package_not_registry_default(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory) / "repo"
            shutil.copytree(ROOT / "app", temp_root / "app")
            shutil.copytree(ROOT / "domains", temp_root / "domains")
            alt_path = temp_root / "domains" / "alternate-domain"
            shutil.copytree(ROOT / "domains" / "university-level physics", alt_path)

            manifest_path = alt_path / "domain.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest.update({
                "id": "alternate-domain",
                "displayName": "Alternate Domain",
                "subject": "alternate-subject",
                "academicLevel": "university",
                "profileVersion": "9.9.9",
            })
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            renderer = alt_path / manifest["visuals"]["rendererScript"]
            renderer.write_text("// ALTERNATE-DOMAIN-RENDERER\n" + renderer.read_text(encoding="utf-8"), encoding="utf-8")
            stylesheet = alt_path / manifest["visuals"]["stylesheet"]
            stylesheet.write_text("/* ALTERNATE-DOMAIN-STYLE */\n" + stylesheet.read_text(encoding="utf-8"), encoding="utf-8")

            registry_path = temp_root / "domains" / "registry.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["domains"].append({"id": "alternate-domain", "path": "alternate-domain"})
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

            package_path = temp_root / "content" / "chapter-1" / "section-1-1" / "package.json"
            package_path.parent.mkdir(parents=True)
            package = json.loads(PACKAGE.read_text(encoding="utf-8"))
            package["domain"] = {
                "id": "alternate-domain",
                "profileVersion": "9.9.9",
                "subject": "alternate-subject",
                "academicLevel": "university",
            }
            package_path.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

            output = Path(directory) / "release"
            build(output, package_path, source_root=temp_root)
            self.assertIn("ALTERNATE-DOMAIN-RENDERER", (output / "app" / "domain-renderers.js").read_text(encoding="utf-8"))
            self.assertIn("ALTERNATE-DOMAIN-STYLE", (output / "app" / "domain-styles.css").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
