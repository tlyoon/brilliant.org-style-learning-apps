# Decision 0052 — Prevent post-return Gemini SDK text-accessor ValueError from losing captured evidence

**Date:** 17 November 2026
**Resolved future-provider software defect:** BSA-20261117-191.
**Older historical ambiguity remains active:** BSA-20261117-183.

The actual old Section9.6 role was recorded as `AMBIGUOUS ValueError` before immutable returned-response capture was introduced. A real read-only Yoga6 audit on 17 Nov found no recoverable raw sidecar for it. It is **unknown** whether the exception arose from Google's remote transport, its SDK's `.text` convenience property, or strict JSON/rubric parsing; do not retroactively assert the cause.

A separate, reproducible forward defect exists in `app_generator/gemini/v3_native_api_reviewers.py`: the native conversation calls `send_v3_native_text_once`, then reads `response.text` BEFORE returning raw text to the owning V3 assessment engine. Even if the SDK **has already returned a response object containing text parts**, its convenience `.text` getter can raise `ValueError`, causing the assessor to record an uncaptured `AMBIGUOUS` role instead of saving the actual returned text.

The production adapter now:
1. Continues returning untouched `response.text` whenever valid. It never opens a new provider client, retries, changes a prompt, rotates a key or guesses missing output.
2. Only when `response.text` is absent/empty or raises a local `ValueError` **after a response object exists**, inspect the *same already-returned* `response.candidates` object for **exactly one** candidate and literal text parts. Reject multiple candidates, mixed function/image/tool parts, empty results and oversized content. Return the verbatim concatenation of actual text parts (excluding explicit thoughts), never a generated verdict.
3. The existing V3 assessor then fsyncs that exact returned text and its response SHA **before** JSON/rubric checking, so malformed JSON yields a hash-proven `PARSE_FAILED` with no provider resubmission. An SDK call throwing *before* any response object remains historical `AMBIGUOUS` and is never retried automatically.

Verified with the genuine installed `google-genai` SDK v2.25.0 `GenerateContentResponse`, `Candidate`, `Content`, and `Part` types and the actual repository Section9.6 activity content, but using a local broken `.text` accessor wrapper and synthetic text, **not an actual new Gemini network call**. Both direct conversation and the real V3 capture/checkpoint/rubric path pass: a returned malformed JSON string causes durable `.response.txt` + exact `responseSha256` and `PARSE_FAILED`, not another `AMBIGUOUS` remote error; the reviewer transport is invoked only once. A subsequent attempt on the same conversation is refused. Negative controls show a real SDK-shaped multi-candidate or mixed function-call response cannot be silently converted into an accepted answer.

The code fix is integrated at the shared native API conversation transport, used by both original reviews and any future separately authorized new-version reviews. It is a **preventative and recoverable post-return error solution**, not proof that the older missing-response Section9.6 request ever returned content. That old role remains unclassified under BSA-183; no new paid calls or publication permission were created.

The owner instruction to recover on the flight is fulfilled for the subclass of post-return SDK text-accessor faults **with an actual attributable returned textual object**. Unknown remote delivery or denial, missing/corrupted return data, and absent paid authorization remain mandatory STOPs; claiming universal automatic recovery would be factually unsupported.
