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
Stage 0  Validated PDF-to-learning-package baseline
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

## End-state source and generation model

The source library is expected to be organized by course/subject and topic. A topic folder may contain one, two, three, or any number of PDF files. All PDFs within a topic folder collectively form that topic's authoritative source corpus for generation.

Example:

```text
Classical_Physics/
├── 01_Kinematics/
│   ├── source_01.pdf
│   └── source_02.pdf
├── 02_Newtons_Laws/
│   ├── source_01.pdf
│   ├── source_02.pdf
│   └── source_03.pdf
├── 03_Work_and_Energy/
│   ├── source_01.pdf
│   └── source_02.pdf
└── m_Topic/
    ├── source_01.pdf
    ├── ...
    └── source_n.pdf
```

The exact filenames and directory naming convention may be configurable, but the architectural rule is stable:

> **The primary generation unit is the topic; PDFs are source documents belonging to that topic.**

The target end-state pipeline is therefore:

```text
COURSE / SUBJECT SOURCE ROOT
            ↓
Discover topic folders
            ↓
For each topic, discover all source PDFs
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
2. **Topic is the generation unit.** One or more PDFs provide evidence for a topic; they are not inherently separate learning apps.
3. **Course coherence is a first-class requirement.** Independently generated topic material must ultimately connect into one subject/course learning environment.
4. **Pedagogy before cosmetics.** Improve the learning mechanism before investing heavily in visual polish or gamification.
5. **Generated educational content and runtime code remain separate.** Prefer validated, reusable interaction primitives over AI-generated arbitrary executable code.
6. **Deterministic core first.** Core learning, validation, feedback, and mastery mechanisms should remain testable without depending on a runtime LLM wherever practical.
7. **AI augments the learning system.** Runtime AI should be introduced where it adds capabilities that deterministic mechanisms cannot provide well, especially contextual tutoring.
8. **Source grounding remains explicit.** PDF/source provenance and human review requirements remain part of the content lifecycle, including when several PDFs support the same synthesized concept.
9. **Multilingual capability remains first-class.** English, Malay, and Simplified Chinese should remain supported by the learning contract as capabilities expand.
10. **Assisted and independent performance remain distinct.** A learner succeeding after scaffolding has provided different evidence from a learner succeeding independently.
11. **Incremental generation is required.** A changed topic should be rebuildable without forcing unnecessary regeneration of the whole course.
12. **Every stage requires validation.** Schemas, tests, documentation, and acceptance criteria should evolve with the implementation.
13. **Do not claim future-stage capability early.** The blueprint describes direction; shipped behavior is determined by current `main`.

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

# Stage 1 — Multi-Source Topic and Course Knowledge/Pedagogy Model

## Goal

Change the generator's primary question from:

> What questions can be generated from this PDF?

into:

> What should the learner understand and be able to do in this topic, based on the complete set of source documents for that topic, and how does this topic connect to the rest of the course?

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

Example topic conceptual structure:

```text
Topic: Newton's Laws

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

Supported by:
- source_01.pdf
- source_02.pdf
- source_03.pdf
```

## Multi-source synthesis rule

If several PDFs discuss the same concept, the system should synthesize them rather than create artificial duplicates. For example:

```text
PDF 1 ─┐
PDF 2 ─┼─→ Newton's Second Law concept model
PDF 3 ─┘
```

The synthesized concept may combine complementary definitions, representations, examples, and explanations while preserving provenance to the individual sources.

Source-grounded statements should remain distinguishable from pedagogically inferred information such as likely misconceptions, recommended scaffolds, or prerequisite relationships when those are not explicitly present in the source corpus.

## Expected artifacts

A future implementation may use a structure such as:

```text
course-model.json

topics/
  01_Kinematics/
    source-manifest.json
    topic-model.json
  02_Newtons_Laws/
    source-manifest.json
    topic-model.json
  ...
```

The exact filenames are implementation decisions, but the separation between topic-level synthesis and course-level relationships is intentional.

## Exit condition

Given a course/subject source root containing multiple topic folders and arbitrary numbers of PDFs per topic, the package can systematically discover the source structure, synthesize each topic corpus into a validated provenance-aware Topic Learning Model, and connect those topic models into a validated Course Learning Model before activity generation begins. Downstream generated activities can explicitly reference these models.

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

Activity quantity and type should ultimately be determined by the pedagogical needs of the topic and its concepts rather than by a permanently fixed MCQ/interactive quota. Existing Stage 0 quotas may remain for backward compatibility during transition.

## Exit condition

A generated topic can use several genuinely different interaction modes, and the runtime can validate and render each supported mode reliably.

---

# Stage 3 — Topic Learning-Journey Generation

## Goal

Transform each topic's collection of concepts and activities into an intentionally ordered learning journey, while retaining coherence with prerequisite and follow-on topics in the course.

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

## Course relationship

Topic journeys should be independently generatable and reviewable, but they should consume the Course Learning Model so that prerequisite assumptions, terminology, shared concepts, and progression remain coherent across the subject.

## Exit condition

The generator can produce validated topic learning journeys whose ordering has explicit pedagogical roles and whose activities collectively build understanding rather than merely sample questions from a topic. Multiple generated topic journeys can coexist coherently within the same course model.

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

## Cross-topic remediation

Because Stage 1 provides course-level prerequisite relationships, remediation may route a learner to a prerequisite concept in an earlier topic rather than only to another activity in the current topic.

## Design rule

Initial misconception mapping and feedback policy should be deterministic and validated where possible. Runtime generative AI is not required for this stage.

## Exit condition

Common wrong answers or interaction patterns can be mapped to known misconceptions or reasoning failures, and the learner receives targeted rather than generic remediation, including cross-topic prerequisite remediation where appropriate.

---

# Stage 5 — Cross-Topic Mastery Model and Adaptive Routing

## Goal

Create a persistent learner model across the whole course and use learning evidence to decide what the individual learner should do next.

## Core capability

Track mastery at a finer level than topic completion. A concept may carry evidence dimensions such as:

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
prerequisite weakness         → prerequisite concept, possibly in another topic
stable mastery                → spaced review later
```

The learner model should span topic boundaries so that weaknesses in earlier concepts can explain and remediate difficulties in later topics.

## Exit condition

Two learners with different evidence histories can legitimately receive different next activities or topic-level routes while working toward the same course objectives.

---

# Stage 6 — Context-Aware AI Tutor

## Goal

Introduce a constrained AI tutor that understands the learner's current activity, topic, course relationships, and learning state and provides Socratic, pedagogically appropriate assistance.

## Tutor context

The tutor should receive structured context including:

- source-grounded concept information from the relevant topic corpus;
- current topic, concept, and objective;
- relevant cross-topic prerequisites;
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
- route attention to prerequisite concepts when appropriate;
- avoid immediately revealing the final answer;
- remain within approved/source-grounded instructional scope.

The tutor augments rather than replaces deterministic validation, activity logic, and mastery tracking.

## Exit condition

The tutor can provide context-sensitive assistance during supported activities while respecting pedagogical constraints, source boundaries, cross-topic relationships, multilingual requirements, and cost/safety controls.

---

# Stage 7 — Course-Wide Motivation, Progression, and Gamification

## Goal

Improve engagement and persistence across the entire course without allowing game mechanics to distort the learning objectives.

## Candidate capabilities

- XP;
- named mastery levels;
- topic and course progress visualization;
- streaks;
- achievements;
- challenge activities;
- concept mastery maps;
- review milestones;
- optional cohort-relative indicators or leaderboards where pedagogically appropriate.

## Design rule

Rewards should favor meaningful learning evidence. Independent mastery should generally carry stronger evidence/value than assisted completion, and repeated guessing should not be rewarded equivalently to demonstrated understanding.

Gamification should operate coherently across topics. A learner should experience progression through a subject, not a collection of unrelated mini-apps.

## Exit condition

Learners receive clear course-wide motivational and progression signals tied to genuine learning behavior and mastery evidence.

---

# Stage 8 — Full Student/Teacher Course Learning System

## Goal

Present all generated topic experiences as a coherent course-level learning environment for students and instructors.

## Course hierarchy

A generic hierarchy may be:

```text
Course / Subject
  ↓
Topic
  ↓
Concept
  ↓
Learning journey
  ↓
Activity
```

Projects that need chapters/subchapters may introduce those structural levels without changing the core rule that a topic owns a source corpus and a learning model.

## Student capabilities

Potential capabilities include:

- course, topic, and concept mastery map;
- recommended next learning activity/topic;
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
- topic/source management;
- content review/publishing controls.

## End-user experience

Although generation may create separate artifacts internally for each topic, the learner-facing product should present one coherent subject/course experience, for example:

```text
Classical Physics
├── Kinematics              Mastery 92%
├── Newton's Laws           Mastery 71%
├── Work and Energy         Mastery 48%
├── Momentum                Not started
└── Rotation                Not started
```

## Exit condition

The platform can support sustained learning across a complete selected subject/course, generated from multiple topic-specific source corpora, and provide actionable learning information to both students and instructors.

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

Existing repository infrastructure for source discovery, generation, validation, provenance, review, workstation coordination, and release/deployment should be generalized and reused rather than unnecessarily replaced.

## Exit condition

The system is capable of supporting real learners and instructors with appropriate operational, security, privacy, reliability, accessibility, and cost controls, while systematically maintaining and updating course content derived from many topic-specific source corpora.

---

# Stage dependency summary

The intended dependency order is:

```text
0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9
```

This does not prohibit preparatory work for later stages, but a later-stage feature should not force premature architectural coupling. In particular:

- Stage 1 establishes what is learned at both topic and course levels from multi-PDF source corpora.
- Stage 2 establishes how learners can interact with those concepts.
- Stage 3 establishes how experiences are sequenced into topic learning journeys.
- Stage 4 establishes how difficulty and errors become learning opportunities, including prerequisite remediation.
- Stage 5 establishes personalization and mastery across topic boundaries.
- Stage 6 adds generative tutoring on top of that structured context.
- Stage 7 adds course-wide motivational systems around meaningful learning.
- Stage 8 integrates generated topics into a coherent student/instructor course environment.
- Stage 9 operationalizes the platform at production/institutional scale.

---

# Recommended implementation discipline

For each stage:

1. inspect current `main` and identify what already satisfies part of the stage;
2. preserve the topic-folder/multi-source/course-level end-state architecture when making local decisions;
3. write or update the relevant product/learning/architecture decision records;
4. define schema/API/runtime changes before large implementation work;
5. split implementation into independently reviewable PRs;
6. add automated tests and validators alongside each capability;
7. update canonical documentation in the same PR as operator-visible behavior changes;
8. independently review generated learning quality, not merely software correctness;
9. preserve backward compatibility where practical;
10. verify incremental generation and provenance when source corpora change;
11. do not mark the stage complete until explicit exit criteria are satisfied;
12. record completion and any blueprint amendments in version-controlled documentation.

---

# Blueprint status

This file is the project's **10-Stage Blueprint**: the strategic guide for the intended long-term development direction.

It is deliberately more stable and higher-level than individual implementation plans. Detailed delivery sequencing belongs in `docs/DEVELOPMENT_ROADMAP.md`, issues, decision records, and pull requests. If implementation experience shows that a stage boundary or dependency is wrong, amend this document explicitly rather than silently drifting away from it.

The following end-state constraints are fundamental and should not be weakened by later implementation shortcuts:

- a course/subject may contain an arbitrary number of topics;
- each topic may contain an arbitrary number of PDF source documents;
- topic PDFs are synthesized as one source corpus rather than automatically treated as separate apps;
- generation should systematically sweep/discover topic folders;
- topic generation should support incremental rebuilds;
- topic models should connect through a course-level concept/prerequisite model;
- generated topic experiences should ultimately appear to the learner as one coherent, adaptive, gamified course environment.

When a future developer or AI coding agent is asked to implement a new capability, it should first identify which blueprint stage the capability belongs to, verify that the necessary earlier-stage foundations exist on the current branch, and ensure that the implementation remains compatible with this multi-source, multi-topic, course-level end state.
