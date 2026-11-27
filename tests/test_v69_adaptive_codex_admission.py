"""BSA288 provider evidence / budget / restart / no replay regression tests."""
from __future__ import annotations
from tempfile import TemporaryDirectory
from pathlib import Path
from datetime import datetime
import json
import os
from unittest import TestCase
from unittest.mock import patch

from app_generator.runtime.v3_adaptive_codex_admission import (
    admission_decision,classify_provider_result,observed_cli_tokens,
    record_invocation_start,record_invocation_outcome,
)
from scripts import bosla_persistent_development as owner


class AdaptiveModelAdmissionTests(TestCase):
    NOW=1795798800.0

    def test_legacy_fixed_twelve_and_large_count_do_not_block(self):
        for used in (12,13,2000):
            with self.subTest(used=used):
                s={"codexDay":"2026-11-27","codexCount":used}
                decision=admission_decision(s,now_epoch=self.NOW)
                self.assertTrue(decision["allowed"])
                self.assertEqual(decision["status"],"BSA288_REAL_PROVIDER_ELIGIBLE")

    def test_actual_provider_rate_limit_backs_off_across_restart(self):
        s={}
        record_invocation_start(s,now_epoch=self.NOW)
        x=record_invocation_outcome(
            s,now_epoch=self.NOW+20,exit_code=1,
            log_excerpt="ERROR: HTTP 429 Too Many Requests\nRetry-After: 3600")
        self.assertEqual(x["providerClass"],"PROVIDER_RATE_LIMIT")
        self.assertGreaterEqual(x["nextRetryEpoch"],self.NOW+3620)
        reread=json.loads(json.dumps(s))
        self.assertFalse(admission_decision(reread,now_epoch=self.NOW+100)["allowed"])
        self.assertTrue(admission_decision(reread,now_epoch=self.NOW+3700)["allowed"])

    def test_repeated_true_rate_limit_backoff_grows(self):
        s={}
        record_invocation_start(s,now_epoch=self.NOW)
        record_invocation_outcome(s,now_epoch=self.NOW+10,exit_code=3,
            log_excerpt="Error: rate_limit_exceeded")
        first=s["codexProviderGate"]["blockedUntilEpoch"]-(self.NOW+10)
        record_invocation_start(s,now_epoch=self.NOW+first+11)
        record_invocation_outcome(s,now_epoch=self.NOW+first+22,
            exit_code=3,log_excerpt="Error: rate_limit_exceeded")
        second=s["codexProviderGate"]["blockedUntilEpoch"]-(self.NOW+first+22)
        self.assertGreater(second,first)

    def test_subscription_unavailable_and_auth_use_safe_rechecks(self):
        for excerpt,family,min_seconds in (
            ("insufficient_quota","BILLING_REQUIRED",86400),
            ("401 Unauthorized","AUTHORIZATION_DENIED",43200),
            ("HTTP 503 Service Unavailable","PROVIDER_TEMPORARY_UNAVAILABLE",300),
        ):
            with self.subTest(family=family):
                s={}
                event=record_invocation_outcome(s,now_epoch=self.NOW,
                          exit_code=1,log_excerpt=excerpt)
                self.assertEqual(event["providerClass"],family)
                self.assertGreaterEqual(event["nextRetryEpoch"],self.NOW+min_seconds)

    def test_success_never_confuses_quoted_error_with_real_provider_error(self):
        s={}
        record_invocation_start(s,now_epoch=self.NOW)
        out=record_invocation_outcome(
            s,now_epoch=self.NOW+100,exit_code=0,
            log_excerpt="Here is code handling HTTP 429 Too Many Requests\n"
                        "tokens used\n85,970\n")
        self.assertEqual(out["providerClass"],"AVAILABLE_LAST_OBSERVED")
        self.assertEqual(out["tokensReported"],85970)
        self.assertIsNone(out["usdCost"])
        self.assertEqual(s["codexProviderGate"]["totalReportedTokens"],85970)
        self.assertEqual(s["codexProviderGate"]["usdCost"],"UNAVAILABLE_FROM_CLI")
        self.assertTrue(admission_decision(s,now_epoch=self.NOW+221)["allowed"])

    def test_unknown_cost_cap_fails_closed_instead_of_fabricating_price(self):
        for raw in ("0","1.25","12"):
            with self.subTest(raw=raw):
                x=admission_decision({},now_epoch=self.NOW,
                                     explicit_max_usd_per_day=raw)
                self.assertEqual(x["status"],"BSA288_EXPLICIT_COST_CAP_UNMETERED_STOP")
                self.assertFalse(x["allowed"])
        for raw in ("nan","-3","not money"):
            with self.assertRaises(ValueError):
                admission_decision({},now_epoch=self.NOW,
                                   explicit_max_usd_per_day=raw)

    def test_inflight_unknown_request_does_not_replay(self):
        s={}
        record_invocation_start(s,now_epoch=self.NOW)
        snapshot=json.loads(json.dumps(s))
        x=admission_decision(snapshot,now_epoch=self.NOW+9000)
        self.assertEqual(x["status"],"BSA288_UNCERTAIN_CODEX_REQUEST_QUARANTINED")
        self.assertFalse(x["allowed"])

    def test_model_spacing_only_blocks_immediate_duplicate_call(self):
        s={}
        record_invocation_start(s,now_epoch=self.NOW)
        record_invocation_outcome(s,now_epoch=self.NOW+10,exit_code=0,
                                  log_excerpt="tokens used\n3,000")
        self.assertEqual(admission_decision(s,now_epoch=self.NOW+11)["status"],
                         "BSA288_MODEL_INVOCATION_SPACING")
        self.assertTrue(admission_decision(s,now_epoch=self.NOW+121)["allowed"])

    def test_no_provider_preflight_and_untrusted_clock_fail_closed(self):
        s={"codexProviderGate":{"lastInvocationEpoch":float("nan")}}
        self.assertEqual(admission_decision(s,now_epoch=self.NOW)["status"],
                         "BSA288_PERSISTED_PROVIDER_GATE_UNTRUSTED")
        self.assertEqual(classify_provider_result(0,"rate_limit_exceeded"),
                         "AVAILABLE_LAST_OBSERVED")
        self.assertIsNone(observed_cli_tokens("MODEL_TEXT=85970 tokens used"))

    def test_legacy_budget_state_migrates_without_deleting_science_receipt(self):
        s={"codexDay":datetime.fromtimestamp(self.NOW).strftime("%Y-%m-%d"),
           "codexCount":12,
           "scienceAcceptance":{"acceptedCount":15,
                                "independentReceiptSha256":"a"*64}}
        self.assertTrue(admission_decision(s,now_epoch=self.NOW)["allowed"])
        record_invocation_start(s,now_epoch=self.NOW)
        self.assertEqual(s["scienceAcceptance"]["acceptedCount"],15)
        self.assertEqual(s["scienceAcceptance"]["independentReceiptSha256"],"a"*64)
        self.assertEqual(s["codexCount"],13)

    def test_no_paid_gemini_or_academic_bypass_from_new_admission(self):
        prompt=owner._codex_prompt()
        self.assertIn("Do not initiate paid Gemini",prompt)
        self.assertIn("No public PR merge",prompt)
        self.assertNotIn("MAX_CODEX_PER_DAY",Path(owner.__file__).read_text("utf8"))

    def test_host_legacy_count_12_starts_model_and_records_real_provider_result(self):
        with TemporaryDirectory() as td:
            p=Path(td);dev=p/"dev";dev.mkdir()
            s={"codexDay":"2026-11-27","codexCount":12,"cycle":24,
               "academicFailure":{"head":"a"*40,
                                  "mode":"DISPATCH_INDEPENDENT_SOURCE_SAFE_CODE_REPAIR",
                                  "classification":"MISSING_SCIENCE_PRODUCER"}}
            def branch(path=owner.ROOT):
                return owner.MAIN_BRANCH
            with (patch.object(owner,"PRIVATE",p),
                  patch.object(owner,"STATE",p/"state.json"),
                  patch.object(owner,"JOURNAL",p/"events.jsonl"),
                  patch.object(owner,"_clean",return_value=True),
                  patch.object(owner,"_branch",side_effect=branch),
                  patch.object(owner,"_head",return_value="a"*40),
                  patch.object(owner.shutil,"which",return_value="codex.cmd"),
                  patch.object(owner,"_dev_worktree",return_value=("feature/test",dev)),
                  patch.object(owner,"build_isolated_coding_snapshot",return_value={}),
                  patch.object(owner,"_log_process",return_value=0) as real_call,
                  patch.object(owner,"_safe_last_log",return_value="tokens used\n250\n"),
                  patch.object(owner,"apply_isolated_patch",return_value=[]),
                  patch.dict(os.environ,{"BOSLA_CODEX_MAX_USD_PER_DAY":""})):
                self.assertFalse(owner._codex_stage(s))
            self.assertEqual(real_call.call_count,1)
            self.assertEqual(s["codexProviderGate"]["lastReportedTokens"],250)
            self.assertEqual(s["codexCount"],13)
            self.assertEqual(s["scienceAcceptance"] if "scienceAcceptance" in s else None,None)
