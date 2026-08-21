"""Staged generation protocol with resumable local state."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol

from app_generator.generation.assembler import assemble_package, validate_plan
from app_generator.generation.extraction import parse_json_response
from app_generator.errors import ResponseContractError, ValidationFailure
from app_generator.prompts import (
    activity_batch_prompt,
    activity_plan_prompt,
    repair_activity_prompt,
    semantic_audit_prompt,
    source_analysis_prompt,
    whole_package_audit_prompt,
)
from app_generator.runtime.run_context import RunContext


class ConversationPort(Protocol):
    def ask(self, prompt: str) -> str: ...


class GenerationProtocol:
    def __init__(self, conversation: ConversationPort, context: RunContext) -> None:
        self.conversation = conversation
        self.context = context

    def _stage(self, name: str, prompt_factory: Callable[[], str]) -> Any:
        existing = self.context.load_stage(name)
        if existing is not None:
            return existing
        response = self.conversation.ask(prompt_factory())
        self.context.save_raw_response(name, response)
        parsed = parse_json_response(response)
        self.context.save_stage(name, parsed)
        return parsed

    @staticmethod
    def _assert_stable_activity_contract(original: dict[str, Any], replacement: dict[str, Any]) -> None:
        for field in ("id", "type", "difficulty", "objective", "interactionMode"):
            if original.get(field) != replacement.get(field):
                raise ValueError(f"Repair attempted to change stable activity field {field} for {original.get('id')}")
        if set(original.get("misconceptions", [])) != set(replacement.get("misconceptions", [])):
            raise ValueError(f"Repair attempted to change stable misconceptions for {original.get('id')}")
        original_recovery = original.get("prerequisiteRecovery", {}).get("prerequisiteId")
        replacement_recovery = replacement.get("prerequisiteRecovery", {}).get("prerequisiteId")
        if original_recovery and original_recovery != replacement_recovery:
            raise ValueError(f"Repair attempted to change the prerequisite for {original.get('id')}")
        for path in (("answerKey", "options"), ("interaction", "items"), ("interaction", "targets")):
            old_items = original.get(path[0], {}).get(path[1], [])
            new_items = replacement.get(path[0], {}).get(path[1], [])
            old_ids = {item.get("id") for item in old_items if isinstance(item, dict) and item.get("id")}
            new_ids = {item.get("id") for item in new_items if isinstance(item, dict) and item.get("id")}
            if old_ids and old_ids != new_ids:
                raise ValueError(f"Repair attempted to rename stable {path[1]} IDs for {original.get('id')}")

    def _activity_batch(
        self,
        name: str,
        analysis: dict[str, Any],
        planned: list[dict[str, Any]],
        source_location: str,
    ) -> dict[str, Any]:
        try:
            return self._stage(
                name,
                lambda: activity_batch_prompt(analysis, planned, source_location=source_location),
            )
        except ResponseContractError:
            activities: list[dict[str, Any]] = []
            for item in planned:
                single = self._stage(
                    f"{name}-{item['id']}",
                    lambda item=item: activity_batch_prompt(analysis, [item], source_location=source_location),
                )
                if not isinstance(single, dict) or len(single.get("activities", [])) != 1:
                    raise ResponseContractError(f"Single-activity fallback for {item['id']} returned an invalid batch")
                activities.extend(single["activities"])
            combined = {"activities": activities}
            self.context.save_stage(name, combined)
            return combined

    def generate(
        self,
        *,
        config: Any,
        run_metadata: dict[str, Any],
        source_location: str,
    ) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        analysis = self._stage("source-analysis", lambda: source_analysis_prompt(run_metadata))
        plan = self._stage("activity-plan", lambda: activity_plan_prompt(analysis))
        planned = validate_plan(plan)
        batches: list[dict[str, Any]] = []
        for activity_type in ("mcq", "interactive"):
            for difficulty in ("easy", "moderate", "challenging"):
                slice_ = [item for item in planned if item["type"] == activity_type and item["difficulty"] == difficulty]
                name = f"{activity_type}-{difficulty}"
                batch = self._activity_batch(name, analysis, slice_, source_location)
                batches.append(batch)
        package = assemble_package(config, analysis, plan, batches)
        return package, analysis, batches

    def audit_and_repair(self, package: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        findings: list[dict[str, Any]] = []
        for index in range(0, len(package["activities"]), 3):
            group = package["activities"][index:index + 3]
            name = f"semantic-audit-{index // 3 + 1:02d}"
            audit = self._stage(name, lambda group=group: semantic_audit_prompt(group))
            findings.extend(audit.get("findings", []))
        whole_audit = self._stage("whole-package-audit", lambda: whole_package_audit_prompt(package))
        findings.extend(whole_audit.get("findings", []))
        blockers = [item for item in findings if item.get("severity") == "blocker"]
        by_id = {item["id"]: item for item in package["activities"]}
        unresolved = [item for item in blockers if item.get("activityId") not in by_id]
        if unresolved:
            raise ValidationFailure(
                "Semantic audit returned blocker findings without a valid activity ID",
                [str(item) for item in unresolved],
            )
        for activity_id in sorted({item.get("activityId") for item in blockers if item.get("activityId")}):
            activity_findings = [item.get("message", "unspecified blocker") for item in blockers if item.get("activityId") == activity_id]
            name = f"semantic-repair-{activity_id}"
            replacement = self._stage(
                name,
                lambda activity_id=activity_id, activity_findings=activity_findings: repair_activity_prompt(
                    by_id[activity_id], activity_findings,
                ),
            )
            self._assert_stable_activity_contract(by_id[activity_id], replacement)
            by_id[activity_id] = replacement
        package["activities"] = [by_id[item["id"]] for item in package["activities"]]
        return package, findings

    def repair_validation_errors(self, package: dict[str, Any], errors: list[str], attempt: int) -> dict[str, Any]:
        import re

        indices = sorted({int(match.group(1)) for error in errors if (match := re.search(r"activity\[(\d+)\]", error))})
        if not indices:
            return package
        for index in indices:
            activity = package["activities"][index]
            relevant = [error for error in errors if f"activity[{index}]" in error]
            name = f"repair-{attempt:02d}-activity-{index:02d}"
            replacement = self._stage(name, lambda: repair_activity_prompt(activity, relevant))
            self._assert_stable_activity_contract(activity, replacement)
            package["activities"][index] = replacement
        return package
