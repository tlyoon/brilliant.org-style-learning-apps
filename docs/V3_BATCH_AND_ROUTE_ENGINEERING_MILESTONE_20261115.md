# Bosla Yoga6: Batch and learner-route engineering checkpoint (2026-11-15)

Source-free candidate on isolated Yoga6 draft checkout, starting SHA 2b89d3e, draft PR #223, no merge or publication.

## Step 3: Batch API candidate

- New app_generator/gemini/v3_batch_recovery.py binds deterministic two-role manifest and exact package/prompt SHA-256; prohibits mixed packages, duplicated or historically ambiguous role requests.
- Durable hash-chained, exclusive-create lifecycle records persist PREPARED, SUBMITTING, AMBIGUOUS and provider batch IDs. Crash after submission never triggers an automatic resubmission.
- Mock SDK submission is single-attempt and requires explicit operation and generated-text transfer permission. It stores no prompts, source PDFs, credentials or student records.
- Response acceptance requires independently echoed row hash. Gemini inline Batch SDK may not echo the client-side row metadata. Untagged or reordered responses MUST remain unaccepted; no academic PASS can be inferred.
- 23 targeted source-free Python unit tests passed. No authenticated Google Batch request was made. Do not claim production readiness.

## Step 4: learner routing normal-path repair

BSA-20261115-170 repairs premature downstream unlocking when a learner checks a still-locked section before completing its prerequisites. The shared app/rc1-course-routing.js computes prerequisite-valid independent completion by fixed-point closure. Adversarial tests passed in both tests/test_rc1_course_routing.js and tests/test_rc1_draft_diagnostic.js. This remains session-only advisory evidence and not proof of scientific mastery.

## Independent continuous V3 review

Yoga6 Windows Scheduled Task BoslaYoga6V3Recovery last reported LastTaskResult 0 and 15:13:23 local run on 15 Nov. Source-free private checkpoint recorded 10 of 108 activities attempted, nine with completed two-Gemini-reviewer model consensus, and one Section 9.1 uncertain/quarantined. No existing ambiguous request was replayed.

## Unresolved gates

A proven provider-specific row identity mechanism and live Batch API pilot, remaining 99/108 real model reviews, scientific/language/visual and learner acceptance appropriate to V3, exact-head CI and actual release decision. Keep git_auto_merge=false and git_publish=false. No source PDF, private claims, model text, credentials or student data enter Git.
