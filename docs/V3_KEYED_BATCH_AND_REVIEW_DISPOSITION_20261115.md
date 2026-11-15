# Bosla Yoga 6 — keyed Batch identity and unresolved V3 disposition (2026-11-15)

**Repository:** tlyoon/brilliant.org-style-learning-apps, draft PR #223.
**Scope:** source-free code and tests on designated Yoga 6 only; no public deployment or automatic merge.
**Starting verified code:** 7344d078028cddf8e786e4fd6e8dca9e820c5756.

## Provider-specific Batch response identity

Google's Batch documentation (https://aistudio.google.com/docs/batch-api) says each file-backed JSONL request contains a user-defined key that is echoed with its output. Inline SDK responses can be returned out of order. The old source-free Batch mock discarded the local row hash when building an inline request. This was not safe for actual per-activity review.

Normal function app_generator/gemini/v3_batch_recovery.py::submit_once_with_sdk now calls app_generator/gemini/v3_keyed_batch.py. The keyed-file transport:
- Constructs file-backed JSONL in memory from exact frozen package, activity, reviewer role and prompt digest, with one hex SHA-256 request key per review row.
- Requires explicit independent operation and generated-text transfer flags before file upload or batch creation, and verifies the local SDK supports file upload and Batch create.
- Latches immutable SUBMITTING in the pre-existing private event journal before the first possible provider operation; ambiguous upload/create becomes AMBIGUOUS and must not be repeated.
- Checks exact provider job name and display name before read-only GET; retrieves only the documented output file, binds output by echoed user key independent of response order, rejects mismatches, duplications, malformed/unknown/partial response lines and individual response errors as non-PASS.
- Supports repeated read-only GET/download after a crash but never repeats POST. No provider job state or key match alone establishes model consensus or release eligibility.

The installed Yoga 6 Google SDK method signatures for files.upload, batches.create, batches.get and files.download were inspected source-free; they are compatible with this interface. **This is not proof of a successful live Batch request.**

**Local source-free tests:** 19 new keyed-file adversarial cases + 23 existing Batch regression cases PASS. No live Batch API call or generated text transfer was performed during this development change. Authentic provider key-echo results and subsequent immutable private V3 role-checkpoint integration remain open.

## Section 9.1 — terminal ambiguous synchronous call

Original Section 9.1 activity 1 in the private immutable Yoga 6 course record has AI_UNCERTAIN from the earlier Gemini ServerError, without an attributable synchronous provider job ID. Neither a new Google account nor a new key can establish whether that old request completed. Therefore it remains quarantined with no replay and no fabricated PASS. The existing section-level independent-continuation dispatcher treats it as nonblocking for other sections. It is STILL a missing final V3 acceptance result.

## Section 9.2 — genuine content repair backlog

The independent V3 review of activity 14 in Section 9.2 yielded AI_REPAIR_REQUIRED specifically for trilingualMeaning. The same two reviewers' consensus gives PASS for physicsAnswer, visualValue and accessibleLearnerExperience. A corrected version must be independently versioned and reviewed, preserving the existing frozen candidate/hash and history; this source-free Batch milestone does not silently edit the content or mark it resolved.

## Actual Yoga 6 continuation

Read-only V3 progress on 15 November 2026 after the local scheduled 19:13 recurrence: 19/108 assessment rows, 18 with complete two-model reviews, 17 consensus passes, one AI_UNCERTAIN and one AI_REPAIR_REQUIRED. Section 9.3 is next eligible. Registered Windows Scheduled Task BoslaYoga6V3Recovery had last result 0 and remains configured for a 30-minute interval when Windows user is logged in.

## Acceptance limitations

Current active Decision 0036/0039 requires actual two-Gemini adversarial checks for all revised activities and deterministic exact-artifact browser/privacy/CI evidence. Neither synthetic Batch tests, source-free metadata nor partial model counts satisfy full technical V3 acceptance. No protected source PDFs, student records, private prompts, credentials, batch requests, public merge or release were performed. Continue allowed independent sections normally, not duplicate ambiguous requests. Closing legacy uncertain/content-fail sections requires distinct evidence-bound versioning and genuine fresh review, not a status rewrite.
