# 10-Stage Blueprint for the Brilliant-Style Learning App

## Purpose

This document is the long-term guiding blueprint for evolving this repository from its current PDF-driven learning-package generator into a full Brilliant-style interactive learning system.

It defines ten logically sequential capability stages, numbered Stage 0 through Stage 9. Each stage should leave the system working, testable, and usable. Later stages extend earlier stages rather than replacing them.

This is a strategic roadmap, not a statement that future-stage capabilities already exist on `main`. Current behavior remains governed by the repository's authority order in `docs/CONTEXT_INDEX.md`, especially current code/schema/configuration, approved decisions, product requirements, learning-design rules, architecture, and the development roadmap.

The guiding principle is:

> Transform the package from a question generator into a learning-experience generator.

The intended high-level evolution is:

```text
Stage 0  Validated PDF-to-learning-package baseline
   ↓
Stage 1  Knowledge and pedagogy model
   ↓
Stage 2  Rich interactive activity framework
   ↓
Stage 3  Pedagogical learning-sequence engine
   ↓
Stage 4  Diagnostic feedback and scaffolding
   ↓
Stage 5  Mastery model and adaptive routing
   ↓
Stage 6  Context-aware AI tutor
   ↓
Stage 7  Motivation, progression, and gamification
   ↓
Stage 8  Full student/teacher course learning system
   ↓
Stage 9  Production and institutional platform
```

---

## Development principles

The stages are capability boundaries rather than single pull requests. A stage may require several independently reviewable PRs.

1. **Preserve a working system.** Do not require a large rewrite merely to advance a stage.
2. **Pedagogy before cosmetics.** Improve the learning mechanism before investing heavily in visual polish or gamification.
3. **Generated educational content and runtime code remain separate.** Prefer validated, reusable interaction primitives over AI-generated arbitrary executable code.
4. **Deterministic core first.** Core learning, validation, feedback, and mastery mechanisms should remain testable without depending on a runtime LLM wherever practical.
5. **AI augments the learning system.** Runtime AI should be introduced where it adds capabilities that deterministic mechanisms cannot provide well, especially contextual tutoring.
6. **Source grounding remains explicit.** PDF/source provenance and human review requirements remain part of the content lifecycle.
7. **Multilingual capability remains first-class.** English, Malay, and Simplified Chinese should remain supported by the learning contract as capabilities expand.
8. **Assisted and independent performance remain distinct.** A learner succeeding after scaffolding has provided different evidence from a learner succeeding independently.
9. **Every stage requires validation.** Schemas, tests, documentation, and acceptance criteria should evolve with the implementation.
10. **Do not claim future-stage capability early.** The blueprint describes direction; shipped behavior is determined by current `main`.

---

# Stage 0 — Validated PDF-to-Learning-Package Baseline

## Goal

Preserve and clearly identify the current working system as the baseline from which the Brilliant-style transformation proceeds.

## Starting capability

The repository already provides a PDF/source-driven generation workflow, structured content packages, schemas and validation, a learner scaffold, multilingual learner-facing content, formative hints and retries, prerequisite routing, difficulty levels, assisted/independent evidence, review controls, and deployment/generation infrastructure.

The current learning-package contract includes both multiple-choice and interactive activities. Stage 0 should therefore not be described merely as an MCQ system; rather, it is the validated baseline whose learning experience is still substantially question/activity oriented.

## Conceptual pipeline

```text
PDF/source material
      ↓
generator
      ↓
content package
      ↓
validation/review
      ↓
learner application
```

## Exit condition

Stage 0 is considered established when the current baseline is reproducible, documented, tested, and can be referenced as the pre-blueprint implementation state.

---

# Stage 1 — Knowledge and Pedagogy Model

## Goal

Change the generator's primary question from:

> What questions can be generated from this source?

into:

> What exactly should the learner understand and be able to do?

## Core transformation

Insert a machine-readable concept/pedagogy layer between source ingestion and activity generation:

```text
PDF/source
    ↓
concept and pedagogy model
    ↓
activities
```

For each subchapter, represent at least:

- concepts;
- learning objectives;
- prerequisite relationships;
- expected reasoning;
- common misconceptions;
- useful representations;
- mastery evidence;
- source provenance.

Example conceptual structure:

```text
Concept: Newton's Third Law

Objectives:
- identify interacting objects
- identify action-reaction pairs
- distinguish force from acceleration
- reason about equal-magnitude/opposite-direction forces

Prerequisites:
- force
- vectors
- Newton's Second Law

Misconceptions:
- the heavier object exerts the larger interaction force
- action and reaction act on the same object
- the faster-moving object must exert the larger force

Representations:
- verbal scenario
- vector diagram
- free-body diagram
- manipulable physical scenario

Mastery evidence:
- recognize
- predict
- explain
- transfer
```

## Exit condition

A subchapter can be converted from source material into a validated concept/pedagogy model before activity generation begins, and generated activities can explicitly reference that model.

---

# Stage 2 — Rich Interactive Activity Framework

## Goal

Move beyond MCQ-dominant interaction by giving the learner multiple ways to manipulate, construct, compare, classify, predict, and explore concepts.

## Core architecture

Create a reusable library of tested interaction primitives. The generator selects and parameterizes primitives rather than generating arbitrary JavaScript for individual activities.

Candidate activity types include:

- multiple choice;
- multiple select;
- prediction;
- drag and drop;
- matching;
- ordering;
- classification;
- slider experiment;
- vector manipulation;
- graph manipulation;
- diagram annotation;
- simulation;
- construction;
- comparison;
- error spotting;
- guided derivation;
- short response;
- concept mapping.

Example activity contract:

```text
activity_type: vector_manipulation
concept: newtons_third_law
student_action: construct_force_pair
constraints:
  vector_origins_locked: true
success_condition:
  equal_magnitude: true
  opposite_direction: true
```

## Design rule

Interaction primitives are trusted runtime components. Generated packages provide declarative content and parameters. This separation keeps generated learning experiences testable, secure, and reusable.

## Exit condition

A generated subchapter can use several genuinely different interaction modes, and the runtime can validate and render each supported mode reliably.

---

# Stage 3 — Pedagogical Learning-Sequence Engine

## Goal

Transform a collection of activities into an intentionally ordered learning journey.

## Core transformation

Replace the dominant pattern:

```text
question → question → question → question
```

with sequences such as:

```text
Hook
  ↓
Predict
  ↓
Explore
  ↓
Notice
  ↓
Explain
  ↓
Guided practice
  ↓
Independent challenge
  ↓
Transfer
  ↓
Reflect
```

Not every concept must use exactly this sequence. The pedagogy model should determine the appropriate learning pattern.

## Example

For Newton's Third Law, a sequence might first ask the learner to predict which of two interacting objects experiences the larger force, then manipulate masses, observe force vectors, confront the misconception, formalize the law, and finally transfer the reasoning to a different physical situation.

## Exit condition

The generator can produce validated learning sequences whose ordering has explicit pedagogical roles and whose activities collectively build understanding rather than merely sample questions from a topic.

---

# Stage 4 — Diagnostic Feedback and Scaffolding

## Goal

Make incorrect responses diagnostically useful and provide targeted help based on the learner's reasoning.

## Core transformation

Move from:

```text
wrong → generic hint → retry
```

toward:

```text
response
   ↓
reasoning/misconception diagnosis
   ↓
targeted feedback
   ↓
progressive scaffold
   ↓
retry / alternate representation / prerequisite remediation
```

## Scaffolding levels

A useful progression may include:

1. reflective prompt;
2. conceptual hint;
3. visual or representational hint;
4. partial demonstration;
5. prerequisite remediation;
6. guided reconstruction of the solution.

The system should record which scaffolds were required.

## Design rule

Initial misconception mapping and feedback policy should be deterministic and validated where possible. Runtime generative AI is not required for this stage.

## Exit condition

Common wrong answers or interaction patterns can be mapped to known misconceptions or reasoning failures, and the learner receives targeted rather than generic remediation.

---

# Stage 5 — Mastery Model and Adaptive Routing

## Goal

Create a persistent learner model and use learning evidence to decide what the individual learner should do next.

## Core capability

Track mastery at a finer level than subchapter completion. A concept may carry evidence dimensions such as:

```text
recognition
prediction
representation
explanation
transfer
```

The system should distinguish evidence obtained independently from evidence obtained after hints or tutoring.

Example conceptual state:

```text
Newton's Third Law
  recognition:    high
  prediction:     high
  representation: moderate
  explanation:    developing
  transfer:       developing
```

## Adaptive routing

Possible routes include:

```text
successful independent response → harder/transfer activity
assisted success              → consolidation activity
known misconception           → targeted remediation
prerequisite weakness         → prerequisite activity
stable mastery                → spaced review later
```

## Exit condition

Two learners with different evidence histories can legitimately receive different next activities while working toward the same learning objectives.

---

# Stage 6 — Context-Aware AI Tutor

## Goal

Introduce a constrained AI tutor that understands the learner's current activity and learning state and provides Socratic, pedagogically appropriate assistance.

## Tutor context

The tutor should receive structured context including:

- source-grounded concept information;
- current concept and objective;
- current activity and interaction state;
- expected reasoning;
- learner attempts;
- diagnosed misconception(s);
- hints/scaffolds already used;
- relevant prerequisite/mastery state;
- language preference.

## Tutor behavior

The tutor should preferentially:

- ask guiding questions;
- direct attention to relevant visual/interactive evidence;
- diagnose where reasoning diverged;
- provide progressively stronger scaffolding;
- avoid immediately revealing the final answer;
- remain within approved/source-grounded instructional scope.

The tutor augments rather than replaces deterministic validation, activity logic, and mastery tracking.

## Exit condition

The tutor can provide context-sensitive assistance during supported activities while respecting pedagogical constraints, source boundaries, multilingual requirements, and cost/safety controls.

---

# Stage 7 — Motivation, Progression, and Gamification

## Goal

Improve engagement and persistence without allowing game mechanics to distort the learning objectives.

## Candidate capabilities

- XP;
- named mastery levels;
- progress visualization;
- streaks;
- achievements;
- challenge activities;
- concept mastery maps;
- optional cohort-relative indicators or leaderboards where pedagogically appropriate.

## Design rule

Rewards should favor meaningful learning evidence. Independent mastery should generally carry stronger evidence/value than assisted completion, and repeated guessing should not be rewarded equivalently to demonstrated understanding.

Gamification follows the learning engine rather than defining it.

## Exit condition

Learners receive clear motivational and progression signals tied to genuine learning behavior and mastery evidence.

---

# Stage 8 — Full Student/Teacher Course Learning System

## Goal

Expand from standalone subchapter experiences into a coherent course-level learning environment for students and instructors.

## Course hierarchy

```text
Course
  ↓
Chapter
  ↓
Subchapter
  ↓
Concept
  ↓
Learning journey
  ↓
Activity
```

## Student capabilities

Potential capabilities include:

- course and concept mastery map;
- recommended next learning activity;
- full learning history;
- independent versus assisted performance;
- review queue;
- weak-concept identification;
- multilingual learning preferences;
- progress and XP history.

## Instructor capabilities

Potential capabilities include:

- concept mastery by student;
- class/cohort mastery summaries;
- common misconception patterns;
- attempts and time-on-task;
- participation/completion;
- problematic activity identification;
- students requiring intervention;
- content review/publishing controls.

## Exit condition

The platform can support sustained learning across a course and provide actionable learning information to both students and instructors.

---

# Stage 9 — Production and Institutional Platform

## Goal

Make the system reliable, secure, maintainable, and economically operable for real institutional deployment.

## Capability areas

- authentication and authorization;
- student and instructor accounts;
- course enrolment;
- persistent databases;
- privacy and retention controls;
- accessibility;
- responsive/mobile operation;
- weak-network/offline strategy where feasible;
- analytics governance;
- AI cost controls, quotas, caching, and fallback models;
- content versioning and publishing workflow;
- institutional administration;
- observability and production monitoring;
- backup/recovery;
- security review;
- deployment and scaling strategy.

Existing repository infrastructure for generation, validation, provenance, review, workstation coordination, and release/deployment should be reused rather than unnecessarily replaced.

## Exit condition

The system is capable of supporting real learners and instructors with appropriate operational, security, privacy, reliability, accessibility, and cost controls.

---

# Stage dependency summary

The intended dependency order is:

```text
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
```

This does not prohibit preparatory work for later stages, but a later-stage feature should not force premature architectural coupling. In particular:

- Stage 1 establishes what is learned.
- Stage 2 establishes how learners can interact with it.
- Stage 3 establishes how those experiences are sequenced.
- Stage 4 establishes how difficulty and errors become learning opportunities.
- Stage 5 establishes personalization from evidence.
- Stage 6 adds generative tutoring on top of that structured context.
- Stage 7 adds motivational systems around meaningful learning.
- Stage 8 organizes the experience across students, instructors, and courses.
- Stage 9 operationalizes the platform at production/institutional scale.

---

# Recommended implementation discipline

For each stage:

1. inspect current `main` and identify what already satisfies part of the stage;
2. write or update the relevant product/learning/architecture decision records;
3. define schema/API/runtime changes before large implementation work;
4. split implementation into independently reviewable PRs;
5. add automated tests and validators alongside each capability;
6. update canonical documentation in the same PR as operator-visible behavior changes;
7. independently review generated learning quality, not merely software correctness;
8. preserve backward compatibility where practical;
9. do not mark the stage complete until explicit exit criteria are satisfied;
10. record completion and any blueprint amendments in version-controlled documentation.

---

# Blueprint status

This file is the project's **10-Stage Blueprint**: the strategic guide for the intended long-term development direction.

It is deliberately more stable and higher-level than individual implementation plans. Detailed delivery sequencing belongs in `docs/DEVELOPMENT_ROADMAP.md`, issues, decision records, and pull requests. If implementation experience shows that a stage boundary or dependency is wrong, amend this document explicitly rather than silently drifting away from it.

When a future developer or AI coding agent is asked to implement a new capability, it should first identify which blueprint stage the capability belongs to and verify that the necessary earlier-stage foundations exist on the current branch.
