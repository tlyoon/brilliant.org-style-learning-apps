# BOSLA production source contract — one textbook, no external three-PDF requirement

**Status:** binding production architecture amendment, 22 November 2026
**Project:** BOSLA (tlyoon/brilliant.org-style-learning-apps), execution on Yoga 6
**Not applicable to:** MicroGen_AI_Web or MicroGen_AI, which are separate projects

## Historical origin and supersession

The earlier BOSLA **C3 held-out generalization campaign** and its bounded cross-topic acceptance/acquisition runbooks required three distinct unseen physics PDFs as an **experiment**. That choice was not an intrinsic requirement of BOSLA's generator. Its immutable two-round receipts and historical FAILED_LIMITED_CAMPAIGN finding remain valid as historical evidence. **The requirement to find, download, supply, or pass three external PDFs is withdrawn as a normal production or release-admission dependency.** A future generalized assessment may be arranged separately only when technically justified and specifically authorized; historical three-source manifests are not to be replayed.

The older docs/10_STAGE_BLUEPRINT.md described automatically synthesizing **every PDF found in a topic folder**. This is superseded for production. There is **one authoritative, instructor-selected textbook per generated course**. One source.pdf (or a different explicitly selected PDF filename) supplies each topic/subchapter. Other subchapter PDFs from the same textbook may be used for those other subchapters but must not automatically be combined into the current topic. Files such as old slides, a question bank, extra unrelated PDFs, or outside OpenStax/MIT materials are not additional source inputs.

## Executable invariants

1. Stage 0 and every downstream production stage use **only the one selected textbook PDF** for a given topic. Local configuration already disallows a tuple of two source PDFs. The configured Google Drive target_filename is the sole PDF returned to the production downloader, Selenium/LLM attachment and source manifest. Sibling PDF files may exist but are ignored, never downloaded or attached.
2. Automatic worker/coordinator job identities depend on the selected PDF's verified Drive file ID/version, **not** siblings. Adding or modifying an unrelated PDF does not trigger regeneration or change the authoritative evidence.
3. No stage may search for or download an external supplementary textbook to fill an absent topic. Missing, ambiguous or unavailable selected sources produce an explicit fail-closed source error, not a fallback.
4. Newly built production manifests must contain exactly one sources entry with role primary. Old multi-source manifests can still be inspected as historical evidence but cannot be newly admitted into the current production source pipeline.
5. An LLM may explain, structure, translate, assess or visualize **what is grounded in the selected textbook**. It cannot invent unsupported textbook claims, inject facts from other books, automatically look up replacement PDFs or assert external source permission. Scientific, visual, learner and translation QA remain separate acceptance concerns.
6. Any course/textbook migration is an explicit change of source identity and checkpoints, never an invisible second textbook. Preserve no-overwrite/restart invariants, no-replay of uncertain provider requests, source SHA integrity, and existing release/privacy controls.
7. The v7.1 autonomous progress/recovery workflow remains binding: history → targeted repair → real test → injected failure/regression → executable registry → normal Yoga 6 pipeline restart. The three-PDF test is **not** a blocker to beginning or completing the next eligible single-textbook BOSLA production step.

## Historical test separation

heldout_generalization_gate.py, bounded_cross_topic_acceptance.py and bounded_acquisition.py retain their **frozen historical schemas** so earlier trial receipts can be reconciled without changing claimed evidence. Their three-PDF condition applies **only to those bounded historical trial formats**, not to the authoritative production source selection, generated learning material, or release prerequisites. There is no automatic new external PDF acquisition for BOSLA.

The private BSA242 OpenStax three-PDF preflight from 22 November was exploratory only, never admitted for generation or commercial publication; it is **quarantined as non-required** for BOSLA production. It does not form part of the selected textbook, the upcoming source manifest, or a launch dependency. Do not mistake those private staging files or their licensing notes for production permission.

## Next active source-science stage (BSA244, 22 November 2026)

The ordinary Yoga 6 BOSLA V17-to-V18 recovery handoff must **actually** reopen the one already selected Serway 9.1 source.pdf locally, verify the installed source manifest and all 18 activity source-location anchors, run bounded exact momentum mathematical and answer-pattern witnesses, and then dispatch the real existing academic proof-gap audit within the same invocation. The source, page excerpts and generated materials must never be uploaded to another textbook provider. The initial BSA244 owner Yoga 6 standalone real proof located all 18 original source passages and passed six rational mathematical checks/five bounded answer patterns. The independent gate still has 90 unmet source/answer/physics/visual/multilingual proof slots; V18 must **not** claim full academic or commercial publication PASS. See [V18 genuine source-evidence execution](BOSLA_V18_REAL_SELECTED_TEXTBOOK_SCIENCE_PROVENANCE.md).

## Acceptance tests

Source-free executable tests prove that selected source.pdf alone is chosen even when an extra question bank, duplicate sibling filename, disabled extra PDF, or outside source is present. Replacing an extra PDF never changes the production coordinator job SHA. Missing/ambiguous target fails closed; one source produces a single-source manifest; a multi-source manifest request is rejected. Hosted exact-HEAD CI and actual Yoga 6 normal worker must verify integration before declaring this correction fully closed.
