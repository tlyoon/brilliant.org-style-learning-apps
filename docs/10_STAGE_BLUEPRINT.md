# 10-Stage Blueprint for the Brilliant-Style Learning App

## Purpose

This document is the long-term guiding blueprint for evolving this repository from its current PDF-driven learning-package generator into a full Brilliant-style interactive learning system.

The intended end product is a **course-level learning-app generator and learning environment**, not merely a one-PDF-to-one-app or question-generation tool. A course or selected subject area may contain many topics, and each topic may be supported by an arbitrary number of PDF source files stored together in that topic's source folder. The package must systematically discover those topic folders, synthesize each topic's source corpus, generate a coherent gamified learning experience for every topic, connect the topics into a course-level knowledge and prerequisite structure, and present the result to the learner as one coherent learning environment.

It defines ten logically sequential capability stages, numbered Stage 0 through Stage 9. Each stage should leave the system working, testable, and usable. Later stages extend earlier stages rather than replacing them.

This is a strategic roadmap, not a statement that future-stage capabilities already exist on `main`. Current behavior remains governed by the repository's authority order in `docs/CONTEXT_INDEX.md`, especially current code/schema/configuration, approved decisions, product requirements, learning-design rules, architecture, and the development roadmap.

The guiding principle is:

> Transform the package from a question generator into a course-level learning-experience generator.

The intended high-level evolution is:

```text
Stage 0  Validated single-source-root PDF-to-learning-package baseline
   ↓
Stage 1  Multi-source topic and course knowledge/pedagogy model
   ↓
Stage 2  Rich interactive activity framework
   ↓
Stage 3  Topic learning-journey generation
   ↓
Stage 4  Diagnostic feedback and scaffolding
   ↓
Stage 5  Cross-topic mastery model and adaptive routing
   ↓
Stage 6  Context-aware AI tutor
   ↓
Stage 7  Course-wide motivation, progression, and gamification
   ↓
Stage 8  Full student/teacher course learning system
   ↓
Stage 9  Production and institutional platform
```

---

## Single Source Root Principle

The complete generation system shall have **exactly one project-level configurable source-root placeholder**. Stage 0 and every subsequent blueprint stage must obtain source documents, topic structure, provenance, discovery scope, and downstream source-derived artifacts from this root or from artifacts derived from it. Individual stages must not introduce independent source-root configuration values.

For the present project, the configured Google Drive source root is:

```text
source_root_folder_id = 1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA
```

This root currently contains the source hierarchy for Chapters 8 through 14 and is the top directory whose source PDFs are in scope for the package.

Conceptually, the authoritative project configuration should contain one value equivalent to:

```toml
[source]
root_folder_id = "1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA"
```

The exact configuration key must be reconciled with the repository's current authoritative configuration before implementation. If an equivalent source-root field already exists, it should be reused or generalized rather than creating a second competing setting.

Topic, chapter, subchapter, or individual-file choices are **selectors beneath the Source Root**, not alternative roots. For example:

```toml
[source]
root_folder_id = "1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA"

[generation]
target = "8.2"
```

means "generate target 8.2 from within the configured source universe." A future `target = "8"` may select a whole chapter and `target = "all"` may select the complete source tree, but all modes must resolve from the same Source Root.

This principle is an architectural invariant from **Stage 0 onward**.

---

## End-state source and generation model

The source library is expected to be organized below the single Source Root by course structure and topic. The present project uses a hierarchy such as:

```text
SOURCE ROOT
├── 8/
│   ├── 8.1/
│   │   └── source.pdf
│   ├── 8.2/
│   │   └── source.pdf
│   ├── ...
│   └── auxiliary folders where applicable
├── 9/
├── 10/
├── 11/
├── 12/
├── 13/
└── 14/
```

A topic folder may contain one, two, three, or any number of PDF files. All eligible PDFs within a topic folder collectively form that topic's authoritative source corpus for generation. `source.pdf` remains valid for backward compatibility but must not permanently define the only eligible source filename.

The exact filenames and directory naming convention may be configurable, but the architectural rules are stable:

> **There is one Source Root for the project.**
>
> **The primary pedagogical generation unit is the topic; PDFs are source documents belonging to that topic.**

The target end-state pipeline is therefore:

```text
ONE CONFIGURED SOURCE ROOT
            ↓
Discover course/chapter/topic structure
            ↓
For each topic, discover all eligible source PDFs
            ↓
Synthesize the topic source corpus
            ↓
Generate a Topic Learning Model
            ↓
Generate a Topic Learning Journey
            ↓
Generate validated interactive/gamified learning material
            ↓
Connect all Topic Learning Models
            ↓
Generate / update the Course Learning Model
            ↓
Present one coherent course-level learning environment
```

The system must not treat overlapping explanations in different PDFs as unrelated duplicate concepts. Multiple source documents should be synthesized into one topic model while retaining provenance back to the supporting source documents.

The system should also support incremental generation. Unchanged topic corpora should be skippable, while a topic whose source set changes can be regenerated without unnecessarily rebuilding every other topic. Source manifests, content hashes, versioning, or equivalent mechanisms should make this behavior reliable and auditable.

---

## Development principles

The stages are capability boundaries rather than single pull requests. A stage may require several independently reviewable PRs.

1. **Preserve a working system.** Do not require a large rewrite merely to advance a stage.
2. **One configurable Source Root.** Every stage derives its source universe from the same project-level Source Root.
3. **Selectors are not roots.** Chapter/topic/file targets choose material beneath the Source Root and must not redefine it.
4. **Topic is the generation unit.** One or more PDFs provide evidence for a topic; they are not inherently separate learning apps.
5. **Course coherence is a first-class requirement.** Independently generated topic material must ultimately connect into one subject/course learning environment.
6. **Pedagogy before cosmetics.** Improve the learning mechanism before investing heavily in visual polish or gamification.
7. **Generated educational content and runtime code remain separate.** Prefer validated, reusable interaction primitives over AI-generated arbitrary executable code.
8. **Deterministic core first.** Core learning, validation, feedback, and mastery mechanisms should remain testable without depending on a runtime LLM wherever practical.
9. **AI augments the learning system.** Runtime AI should be introduced where it adds capabilities that deterministic mechanisms cannot provide well, especially contextual tutoring.
10. **Source grounding remains explicit.** PDF/source provenance and human review requirements remain part of the content lifecycle, including when several PDFs support the same synthesized concept.
11. **Multilingual capability remains first-class.** English, Malay, and Simplified Chinese should remain supported by the learning contract as capabilities expand.
12. **Assisted and independent performance remain distinct.** A learner succeeding after scaffolding has provided different evidence from a learner succeeding independently.
13. **Incremental generation is required.** A changed topic should be rebuildable without forcing unnecessary regeneration of the whole course.
14. **Every stage requires validation.** Schemas, tests, documentation, and acceptance criteria should evolve with the implementation.
15. **Do not claim future-stage capability early.** The blueprint describes direction; shipped behavior is determined by current `main`.

---

# Stage 0 — Validated Single-Source-Root PDF-to-Learning-Package Baseline

## Goal

Preserve and clearly identify the current working system as the baseline from which the Brilliant-style transformation proceeds, while establishing the **Single Source Root Principle** as a Stage-0 invariant.

## Source-root requirement

Stage 0 must use the same project-level Source Root that every later stage will use:

```text
1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA
```

For the current project, all Stage-0 source selection must resolve beneath this root. Stage 0 may continue to select a specific subchapter or existing `source.pdf` using the current generation mechanism, but such a target is a selector beneath the Source Root rather than a separately configured source location.

Conceptually:

```text
ONE SOURCE ROOT
      ↓
Chapters 8 ... 14
      ↓
selected Stage-0 target
      ↓
existing PDF/source generator
      ↓
content package
      ↓
validation/review
      ↓
learner application
```

Stage 0 therefore establishes the source universe that Stage 1 will later discover and model more comprehensively. Stage 1 must generalize the behavior below this root rather than create a parallel source system.

## Starting capability

The repository already provides a PDF/source-driven generation workflow, structured content packages, schemas and validation, a learner scaffold, multilingual learner-facing content, formative hints and retries, prerequisite routing, difficulty levels, assisted/independent evidence, review controls, and deployment/generation infrastructure.

The current learning-package contract includes both multiple-choice and interactive activities. Stage 0 should therefore not be described merely as an MCQ system; rather, it is the validated baseline whose learning experience is still substantially question/activity oriented.

## Configuration rule

Before Stage 0 is considered fully aligned with this blueprint, the current configuration and generator code should be audited so that:

- exactly one authoritative project-level source-root setting exists;
- its default/current project value resolves to the Drive root above;
- existing target-selection modes resolve beneath that root;
- no second source-root placeholder is introduced for Stage 1 or later stages;
- backward compatibility is preserved where practical;
- canonical configuration documentation and tests reflect the single-root behavior.

## Exit condition

Stage 0 is considered established when the current baseline is reproducible, documented, tested, and can be referenced as the pre-blueprint implementation state **with all source selection resolving from the one configured project Source Root**.

---

# Stage 1 — Multi-Source Topic and Course Knowledge/Pedagogy Model

## Goal

Change the generator's primary question from:

> What questions can be generated from this PDF?

into:

> What should the learner understand and be able to do in this topic, based on the complete set of source documents for that topic, and how does this topic connect to the rest of the course?

## Stage 1A source-discovery boundary

Stage 1A starts from the **same Source Root established in Stage 0**. It must not define another Drive folder or source-path placeholder.

Its initial transformation is:

```text
SAME SOURCE ROOT AS STAGE 0
            ↓
recursive deterministic discovery
            ↓
chapter / topic / auxiliary classification
            ↓
all eligible PDFs for each topic
            ↓
normalized source-corpus manifest
```

Stage 1A is responsible for understanding the structure beneath the root, not for redefining the root itself. It should support the current Chapter 8–14 hierarchy while keeping the scanner reusable for future projects.

## Core transformation

Insert machine-readable topic- and course-level knowledge/pedagogy layers between source ingestion and activity generation:

```text
Topic folder
   ↓
PDF_1 + PDF_2 + ... + PDF_n
   ↓
source-corpus synthesis
   ↓
Topic Learning Model
   ↓
activities / learning journey

All Topic Learning Models
   ↓
Course Learning Model
```

The system must discover an arbitrary number of PDFs in each topic folder. The PDFs are evidence sources; the **topic** is the pedagogical unit.

For each topic, represent at least:

- topic identity and scope;
- concepts and relationships among them;
- learning objectives;
- prerequisite relationships;
- expected reasoning;
- common misconceptions;
- useful representations;
- mastery evidence;
- source provenance at concept/claim level where practical;
- relationships to concepts in other topics.

For the course/subject level, represent at least:

- topic ordering or recommended progression;
- cross-topic prerequisite relationships;
- shared concepts;
- dependencies between topic learning objectives;
- course-level concept graph;
- mappings from concepts to their supporting topic/source corpora.

## Multi-source synthesis rule

If several PDFs discuss the same concept, the system should synthesize them rather than create artificial duplicates. The synthesized concept may combine complementary definitions, representations, examples, and explanations while preserving provenance to the individual sources.

Source-grounded statements should remain distinguishable from pedagogically inferred information such as likely misconceptions, recommended scaffolds, or prerequisite relationships when those are not explicitly present in the source corpus.

## Expected artifacts

A future implementation may use a structure such as:

```text
source-manifest.json
course-model.json

topics/
  8.1/
    topic-model.json
  8.2/
    topic-model.json
  ...
```

The exact filenames are implementation decisions, but the separation between root-derived source discovery, topic-level synthesis, and course-level relationships is intentional.

## Exit condition

Given the single configured Source Root containing multiple chapter/topic folders and arbitrary numbers of PDFs per topic, the package can systematically discover the source structure, synthesize each topic corpus into a validated provenance-aware Topic Learning Model, and connect those topic models into a validated Course Learning Model before activity generation begins. Downstream generated activities can explicitly reference these models without defining another source root.

---

# Stage 2 — Rich Interactive Activity Framework

## Goal

Move beyond MCQ-dominant interaction by giving the learner multiple ways to manipulate, construct, compare, classify, predict, and explore concepts.

## Core architecture

Create a reusable library of tested interaction primitives. The generator selects and parameterizes primitives rather than generating arbitrary JavaScript for individual activities.

Candidate activity types include multiple choice, multiple select, prediction, drag and drop, matching, ordering, classification, slider experiments, vector manipulation, graph manipulation, diagram annotation, simulation, construction, comparison, error spotting, guided derivation, short response, and concept mapping.

Generated activities must derive their source/topic identity through Stage-1 artifacts that ultimately trace back to the same project Source Root; Stage 2 introduces no source-root setting.

## Design rule

Interaction primitives are trusted runtime components. Generated packages provide declarative content and parameters. Activity quantity and type should ultimately be determined by pedagogical need rather than a permanently fixed quota; existing Stage-0 quotas may remain for backward compatibility during transition.

## Exit condition

A generated topic can use several genuinely different interaction modes, and the runtime can validate and render each supported mode reliably.

---

# Stage 3 — Topic Learning-Journey Generation

## Goal

Transform each topic's concepts and activities into an intentionally ordered learning journey while retaining coherence with prerequisite and follow-on topics.

Possible sequences include Hook → Predict → Explore → Notice → Explain → Guided practice → Independent challenge → Transfer → Reflect. The pedagogy model determines the appropriate pattern rather than imposing one fixed sequence.

Topic journeys should consume the Course Learning Model so that prerequisite assumptions, terminology, shared concepts, and progression remain coherent across the subject. Source provenance continues to resolve transitively to the single Source Root.

## Exit condition

The generator can produce validated topic learning journeys whose ordering has explicit pedagogical roles and whose activities collectively build understanding. Multiple topic journeys can coexist coherently within the same course model.

---

# Stage 4 — Diagnostic Feedback and Scaffolding

## Goal

Make incorrect responses diagnostically useful and provide targeted help based on the learner's reasoning.

The target pattern is response → reasoning/misconception diagnosis → targeted feedback → progressive scaffold → retry, alternate representation, or prerequisite remediation.

Scaffolding may progress through reflective prompts, conceptual hints, visual/representational hints, partial demonstrations, prerequisite remediation, and guided reconstruction. The system should record which scaffolds were required.

Because Stage 1 provides course-level prerequisite relationships, remediation may route a learner to a prerequisite concept in an earlier topic. No new source root is introduced; remediation content remains traceable through course/topic artifacts to the same root.

## Exit condition

Common wrong answers or interaction patterns can be mapped to known misconceptions or reasoning failures, and the learner receives targeted rather than generic remediation, including cross-topic prerequisite remediation where appropriate.

---

# Stage 5 — Cross-Topic Mastery Model and Adaptive Routing

## Goal

Create a persistent learner model across the whole course and use learning evidence to decide what the individual learner should do next.

Track mastery at a finer level than topic completion, including evidence dimensions such as recognition, prediction, representation, explanation, and transfer. Distinguish independent evidence from assisted evidence.

Possible routes include harder/transfer activity after independent success, consolidation after assisted success, targeted remediation for a known misconception, cross-topic prerequisite routing for prerequisite weakness, and spaced review after stable mastery.

The learner model spans topic boundaries while the underlying instructional content remains rooted in the same source universe established at Stage 0.

## Exit condition

Two learners with different evidence histories can legitimately receive different next activities or topic-level routes while working toward the same course objectives.

---

# Stage 6 — Context-Aware AI Tutor

## Goal

Introduce a constrained AI tutor that understands the learner's current activity, topic, course relationships, and learning state and provides Socratic, pedagogically appropriate assistance.

Tutor context should include source-grounded concept information, current topic/concept/objective, relevant cross-topic prerequisites, current activity state, expected reasoning, attempts, diagnosed misconceptions, hints used, mastery state, and language preference.

The tutor should ask guiding questions, direct attention to relevant evidence, diagnose reasoning divergence, progressively scaffold, route attention to prerequisites where appropriate, avoid immediate answer revelation, and remain within approved/source-grounded scope.

The tutor does not configure or discover an independent content root. Its source-grounded context is supplied through artifacts derived from the single Source Root.

## Exit condition

The tutor can provide context-sensitive assistance while respecting pedagogical constraints, source boundaries, cross-topic relationships, multilingual requirements, and cost/safety controls.

---

# Stage 7 — Course-Wide Motivation, Progression, and Gamification

## Goal

Improve engagement and persistence across the entire course without allowing game mechanics to distort learning objectives.

Candidate capabilities include XP, named mastery levels, topic/course progress visualization, streaks, achievements, challenge activities, concept mastery maps, review milestones, and optional cohort-relative indicators where pedagogically appropriate.

Rewards should favor meaningful learning evidence. Independent mastery should generally carry stronger evidence/value than assisted completion, and repeated guessing should not be rewarded equivalently to demonstrated understanding.

Gamification should operate coherently across topics. A learner should experience progression through a subject, not a collection of unrelated mini-apps. Stage 7 introduces no source-root configuration.

## Exit condition

Learners receive clear course-wide motivational and progression signals tied to genuine learning behavior and mastery evidence.

---

# Stage 8 — Full Student/Teacher Course Learning System

## Goal

Present all generated topic experiences as a coherent course-level learning environment for students and instructors.

A generic hierarchy may be Course/Subject → Chapter/Module where applicable → Topic → Concept → Learning journey → Activity.

Student capabilities may include course/topic/concept mastery maps, recommended next activities/topics, learning history, independent versus assisted performance, review queues, weak-concept identification, multilingual preferences, and XP history.

Instructor capabilities may include concept mastery by student/cohort, misconception patterns, attempts/time-on-task, participation/completion, problematic activity identification, intervention candidates, topic/source management, and content review/publishing controls.

Although generation may create separate artifacts internally for each topic, the learner-facing product should present one coherent subject/course experience. All generated course content remains traceable to the one configured Source Root.

## Exit condition

The platform can support sustained learning across a complete selected subject/course, generated from multiple topic-specific source corpora, and provide actionable learning information to students and instructors.

---

# Stage 9 — Production and Institutional Platform

## Goal

Make the system reliable, secure, maintainable, and economically operable for real institutional deployment.

Capability areas include authentication/authorization, accounts, enrolment, persistent databases, privacy/retention, accessibility, responsive/mobile operation, weak-network/offline strategies, analytics governance, AI cost controls, content versioning/publishing, institutional administration, observability, backup/recovery, security review, deployment, and scaling.

Existing repository infrastructure for source discovery, generation, validation, provenance, review, workstation coordination, and release/deployment should be generalized and reused rather than unnecessarily replaced. Production configuration management must preserve the Single Source Root Principle rather than proliferating stage-specific source roots.

## Exit condition

The system can support real learners and instructors with appropriate operational, security, privacy, reliability, accessibility, and cost controls while systematically maintaining course content derived from the single configured source universe and its many topic-specific corpora.

---

# Stage dependency summary

```text
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
```

- Stage 0 establishes the working baseline **and the single authoritative Source Root**.
- Stage 1 discovers/models the hierarchy beneath that same root and establishes what is learned at topic/course levels.
- Stage 2 establishes how learners interact with those concepts.
- Stage 3 sequences experiences into topic learning journeys.
- Stage 4 turns errors into learning opportunities, including prerequisite remediation.
- Stage 5 establishes personalization/mastery across topic boundaries.
- Stage 6 adds generative tutoring on top of structured context.
- Stage 7 adds course-wide motivational systems.
- Stage 8 integrates generated topics into a coherent student/instructor course environment.
- Stage 9 operationalizes the platform at production/institutional scale.

No stage is permitted to create a second independently configured source universe.

---

# Recommended implementation discipline

For each stage:

1. inspect current `main` and identify what already satisfies part of the stage;
2. verify that source access ultimately resolves from the single authoritative project Source Root;
3. treat chapter/topic/file values as selectors beneath that root, not alternative roots;
4. preserve the topic-folder/multi-source/course-level end-state architecture when making local decisions;
5. write or update relevant product/learning/architecture decision records;
6. define schema/API/runtime changes before large implementation work;
7. split implementation into independently reviewable PRs;
8. add automated tests and validators alongside each capability;
9. update canonical documentation in the same PR as operator-visible behavior changes;
10. independently review generated learning quality, not merely software correctness;
11. preserve backward compatibility where practical;
12. verify incremental generation and provenance when source corpora change;
13. do not mark the stage complete until explicit exit criteria are satisfied;
14. record completion and blueprint amendments in version-controlled documentation.

---

# Blueprint status

This file is the project's **10-Stage Blueprint**: the strategic guide for the intended long-term development direction.

It is deliberately more stable and higher-level than individual implementation plans. Detailed delivery sequencing belongs in `docs/DEVELOPMENT_ROADMAP.md`, issues, decision records, and pull requests. If implementation experience shows that a stage boundary or dependency is wrong, amend this document explicitly rather than silently drifting away from it.

The following end-state constraints are fundamental:

- the project has exactly one configurable Source Root;
- for the present project that root is Google Drive folder ID `1xiYsp3pe3bcWV9W_ikarnjo_i_EsAPaA`;
- Stage 0 and all later stages derive their source universe from that same root;
- chapter/topic/file choices are selectors beneath the root, not replacement roots;
- a course/subject may contain an arbitrary number of topics;
- each topic may contain an arbitrary number of PDF source documents;
- topic PDFs are synthesized as one source corpus rather than automatically treated as separate apps;
- generation should systematically sweep/discover the hierarchy beneath the Source Root;
- topic generation should support incremental rebuilds;
- topic models should connect through a course-level concept/prerequisite model;
- generated topic experiences should ultimately appear to the learner as one coherent, adaptive, gamified course environment.

When a future developer or AI coding agent is asked to implement a new capability, it should first identify which blueprint stage the capability belongs to, verify that the necessary earlier-stage foundations exist on the current branch, and ensure that the implementation remains compatible with the single-root, multi-source, multi-topic, course-level end state.
