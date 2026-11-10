# Learning design

## Learning loop

The general learning loop is:

**diagnostic ? recommendation ? observe/orient ? predict ? manipulate/explore where useful ? commit response ? reasoning diagnosis ? hint/explanation/retry/prerequisite ? transfer/variation ? mastery update ? next activity ? delayed review**.

Not every activity must contain every step. The generator chooses the shortest sequence that serves the learning objective, but prediction should precede explanation where that order creates useful cognitive engagement.

## Visual-interactive pedagogy

Physics representations are part of the reasoning, not merely presentation polish. When a concept has meaningful spatial, graphical, vectorial, causal, or dynamical structure, the learner should interact with an appropriate diagram, graph, state representation, or simulation rather than receive a decorative image beside a text question.

Prefer experiences in which the learner can do one or more of the following:

- predict a physical outcome before seeing it;
- manipulate a meaningful variable and observe a consequence;
- construct or adjust a vector, graph, ordering, label, or state;
- compare before/after states or competing representations;
- identify a misconception through the representation itself;
- transfer the same concept to a changed but bounded situation.

A static visual is preferable to a weak simulation when manipulation adds no meaningful insight. A text-first interaction is preferable to an irrelevant visual. Engagement comes from clear cause-and-effect reasoning and responsive feedback, not from animation for its own sake.

## Mastery presentation

Named levels are primary: **Starting**, **Developing**, **Proficient**, and **Mastered**. A percentage may appear as secondary evidence, for example: ?Proficient ? 78% mastery.? Do not imply more precision than the evidence supports.

Cohort standing is calculated separately for each subchapter. Display it only after a minimum comparison group and comparable evidence threshold are met, using broad bands such as ?Top 25% of students with comparable evidence.?

## Evidence model

Record first attempt separately from later assisted success. Evidence includes correctness, attempts, time on task, hints, revisits, skips, representation type, meaningful simulation/control changes, and delayed review. Fast guessing or indiscriminate slider movement must not outrank slower, well-supported reasoning.

Visual interaction telemetry is evidence about the learning process, not mastery by itself. Mastery should depend on demonstrated conceptual success, including transfer where appropriate.

## Motivation

Use XP, named mastery levels, learning streaks, restrained achievements, satisfying interaction feedback, and visible progress to support continuity. Avoid limited lives and high-pressure global leaderboards. Progress should remain recoverable after mistakes and skips.

## Dynamic tutor

The tutor may explain, question, diagnose misconceptions, create bounded variants, and refer to the same validated representation vocabulary used by the learning package. It must ground responses in the approved package plus standard prerequisites, disclose uncertainty, and avoid treating generated visual detail as scientific evidence unless that detail is supported by the package or a trusted template invariant.

Potential package defects or low-confidence visual/question inconsistencies should be flagged for quality review. Optional instructor review does not gate normal automated publication.

## Pilot learner evidence separation

The browser prototype records anonymous, in-memory first-check evidence separately from later correctly completed activities. A completion is independent only when the first submitted answer is correct with no prior hints or skips. An error, hint, or skip makes later success assisted. The completion screen shows both counts without implying mastery, grades, or cohort rank. Opt-in local feedback export adds firstCheck, firstCheckHadHint, and completionEvidence to its existing schemaVersion 1 JSON records. Earlier fields are unchanged. No identity or learning history is persisted or uploaded. This is not production mastery storage, adaptive routing, or academic release approval.

## Keyboard and screen-reader continuity in the existing player

The Stage-0 player replaces its activity card when a learner changes a response,
requests a hint, checks, retries, skips, advances, revisits or restarts.
For the normal learner click path, focus must follow the replacement: keep the
updated check or hint control focused while the same activity remains, and move
focus to the next question or journey-complete heading after navigation.
Question and completion headings are programmatically focusable; authored
hints carry polite status semantics. This preserves existing mastery,
progression and anonymous in-memory evidence rules; it does not constitute
an independently verified accessibility or learner-pilot PASS.

## No unearned completion from prefilled ordering

Ordering activities must never start with the correct order already selected.
The normal learner player chooses an initially incorrect, deterministic
permutation while preserving the authored item IDs and answer model.
A deliberate learner reordering is still required for first-try correctness.
This preserves existing independent/assisted session evidence rules; no
course-level mastery or learner privacy policy changes are implied.

## Runtime activity identity is an evidence trust boundary

Activity identifiers are unique keys for anonymous first-check, wrong,
hint, skip, completed and independent/assisted session evidence, and for
activity deep links. Before a package becomes available in the normal player,
the loader must reject absent, malformed or duplicate activity IDs, even if
the package bytes match the instructor roster's SHA-256. A matching digest
proves byte identity, not content validity. Failure clears transient learning
state, does not attribute progress to any activity, and permits subsequent
valid loading. This complements authoring-time validation and does not
change actual mastery definitions or add persistence/student identity.

## Session-boundary isolation on every package replacement

The shared Stage-0 player exposes loadPackage() to an authorized standalone
host and the local instructor selector. Both entrypoints must invalidate
the previous package, response, and anonymous session evidence *before*
awaiting a replacement fetch; the old activity and buttons must not remain
interactable while the new source is in flight. A neutral loading message
replaces the card. Preserve the original standalone activity deep link on
its initial load; clear a former package activity link when replacing it.
Course preview retains its existing section-selection idle behavior. Neither
the transition nor an incoming SHA-256 proof confers academic approval,
course-level progress, persistence, or publication rights.

The standalone index uses the existing normal classic app.js script so its
documented host loadPackage(packageUrl) function is actually reachable,
consistent with the already-working course-preview entrypoint. The
source-free Node and real browser checks cover both entrypoints.
