# Khan Academy / Khanmigo-Inspired Foundational Strategy for Post-Stage 0 and Stage 1A Development

## Purpose

This document records a foundational design strategy for expanding the learning-app platform after the present Stage 0 and Stage 1A pipeline has been completed, tested, and stabilized.

The strategy is inspired by useful principles in Khan Academy and its AI tutor, Khanmigo, but is not intended to reproduce Khan Academy. The goal is to adapt mastery learning, structured curriculum, assessment, adaptive remediation, and AI tutoring specifically for physics education and examination preparation.

## 1. Fundamental philosophy: mastery rather than content consumption

The fundamental unit of the future system should be a **skill or learning outcome**, not a video or question.

A student does not complete a topic simply because a video was watched or notes were read. Progress should ultimately depend on demonstrated ability to apply the associated skills.

A useful progression is:

**Not Started → Attempted → Familiar → Proficient → Mastered**

For this project, the stronger principle is:

> **Content completed ≠ concept understood ≠ skill mastered ≠ exam mastery.**

## 2. Start with a complete curriculum map

The future pipeline should transform authoritative source material into a structured hierarchy:

**Textbook + syllabus → Course → Chapter → Subchapter → Micro-topic → Learning outcomes → Examinable skills**

Example:

- Physics
  - Mechanics
    - Motion
      - Distance and displacement
        - distinguish distance and displacement
        - determine displacement
      - Speed and velocity
        - distinguish speed and velocity
        - calculate average speed
        - calculate velocity
      - Velocity-time graphs
        - interpret graphs
        - determine acceleration
        - determine displacement
        - explain physical motion

This knowledge structure should underlie all generated teaching and assessment artifacts.

## 3. Build complete instructional material around each micro-topic

Instead of immediately generating questions from a textbook, first compile the source into a coherent micro-course.

A future pipeline may be:

**Source material → curriculum decomposition → micro-lessons → complete lecture notes → diagrams/animations → worked examples → 5–10 minute video → transcript → summary → learning outcomes**

Each micro-topic becomes a self-contained learning object.

Example:

### M1.17 — Velocity-Time Graphs

- Video: approximately 5–10 minutes
- Full lecture notes
- Concise revision summary
- Worked examples
- Explicit learning outcomes
- Examinable skills
- Prerequisites
- Syllabus mapping
- Common misconceptions
- Figures/animations/simulation assets where appropriate

The micro-course should be validated before it becomes the basis for large-scale assessment generation.

## 4. Questions derive from learning outcomes, not merely textbook text

Avoid the weak architecture:

**PDF → LLM → many questions**

Prefer:

**Validated micro-lesson → learning outcomes → examinable skills → question specifications → questions**

For one learning outcome such as *interpret velocity-time graphs*, assessment families could include:

- recognition;
- interpretation;
- calculation;
- integration of concepts;
- explanation;
- unfamiliar application.

This makes assessment coverage deliberate rather than equating quantity of generated questions with quality.

## 5. Hierarchy of assessment

The future examination system should distinguish levels of assessment.

### Level 1 — Practice
Single skill. AI assistance allowed.

### Level 2 — Skill Check
Small collection of related questions. Assistance limited or disabled.

### Level 3 — Subtopic Test
Multiple related skills. Independent performance.

### Level 4 — Topic Test
Skills mixed within a larger syllabus topic.

### Level 5 — Mastery Challenge
Previously learned material is deliberately reintroduced after time has passed.

### Level 6 — Mock Examination
Authentic examination structure, timing, mark allocation, question mixture, and expected response style.

This extends mastery learning specifically toward standardized examination preparation.

## 6. Mastery must be demonstrated repeatedly

One correct answer should not establish mastery.

The system should distinguish:

> **I answered this correctly once**

from

> **I can reliably solve this class of problem across time, representations, and unfamiliar contexts.**

Later mixed assessments should be able to increase or decrease mastery estimates as new evidence arrives.

## 7. Use spaced reassessment

Previously learned skills should reappear after other material has intervened.

A typical sequence is:

**Learn A → practice A → establish proficiency → learn B → learn C → unexpectedly reassess A → update mastery confidence**

This is especially important for examinations because real examinations require mixed retrieval rather than immediate repetition of one question type.

## 8. Separate learning assistance from assessment

AI-supported performance must not be confused with independent performance.

### Learning Mode
AI tutor available. Hints, guided questions, explanations, and scaffolding may be provided.

### Assessment Mode
AI assistance disabled or strictly controlled. The student's independent performance is measured.

This separation is essential for an AI-native educational system.

## 9. Extend mastery specifically for examination training

Maintain distinct evidence for at least three forms of mastery.

### Learning mastery
Can the student solve the task with educational support?

### Independent mastery
Can the student solve an unseen problem without AI assistance?

### Exam mastery
Can the student solve examination-standard problems independently, using appropriate terminology/methods and within realistic time constraints?

Example:

- Learning mastery: 96%
- Independent mastery: 84%
- Exam mastery: 68%

These measures need not initially be percentages; the exact mastery model can be determined later.

## 10. Diagnose why marks are lost

Do not store only correct/incorrect outcomes.

Future assessment records should capture dimensions such as:

- physics concept;
- examinable skill;
- conceptual understanding;
- mathematical manipulation;
- graph/data interpretation;
- unit handling;
- terminology;
- reasoning completeness;
- experimental reasoning;
- time management;
- mark allocation;
- primary error category.

Example:

**Question 173**

- Concept: Newton's second law
- Physics understanding: correct
- Mathematical manipulation: correct
- Unit: incorrect
- Exam terminology: correct
- Reasoning: incomplete
- Marks: 2/3
- Primary error: unit omission

Accumulated evidence should produce an actionable learner profile rather than only a single course percentage.

## 11. The learner model controls question generation

The future question generator should not independently decide what to generate.

The adaptive controller should first determine what evidence is needed about the learner.

Example request to the assessment generator:

- Course: IGCSE Physics
- Skill: velocity-time graph → displacement
- Current mastery: Familiar
- Last tested: 18 days ago
- Previous weakness: area interpretation
- Required question type: unfamiliar application
- Difficulty: medium
- AI assistance: off

Only then should the system select or generate the next question.

> **AI generation serves the pedagogy; pedagogy is not determined by whatever the generative model happens to produce.**

## 12. Khanmigo-like AI is the tutoring layer, not the curriculum

The AI tutor should operate inside a validated curriculum rather than defining the curriculum itself.

Its role is to facilitate reasoning through progressively appropriate guidance rather than immediately providing answers.

Example:

Student: *I don't understand why the acceleration is negative.*

Tutor: *Look at the gradient between 4 s and 8 s. Is the velocity increasing or decreasing?*

Student: *Decreasing.*

Tutor: *What sign must the gradient therefore have?*

The validated curriculum, learning outcomes, and skill map remain authoritative.

## 13. Automatic remediation

Assessment and instruction should eventually form a closed loop:

**Assessment → diagnosis → remediation → reassessment**

For example, repeated errors in conservation of momentum may trigger:

**pause exam practice → retrieve appropriate micro-lesson → short video/notes → AI-guided example → targeted practice → independent skill check → return to examination practice**

This is preferable to endlessly presenting additional questions without addressing the underlying weakness.

## 14. Long-term post-Stage-1A architecture

```text
                 AUTHORITATIVE SOURCES
            Textbook + Syllabus + Other Sources
                         |
                         v
                CURRICULUM COMPILER
                         |
                         v
               Curriculum Knowledge Map
                         |
             +-----------+-----------+
             |                       |
             v                       v
       MICRO-COURSES             SKILL MAP
             |                       |
     +-------+--------+              |
     v       v        v              |
   Notes    Video   Examples          |
     |       |        |              |
     +-------+--------+              |
             |                       |
             +-----------+-----------+
                         |
                         v
                ASSESSMENT ENGINE
                         |
               Question generation
                         |
                         v
                    STUDENT
                         |
                         v
                 MARKING ENGINE
                         |
                         v
                ERROR DIAGNOSIS
                         |
                         v
                   LEARNER MODEL
                         |
             +-----------+-----------+
             |                       |
             v                       v
       MASTERED SKILL           WEAK SKILL
             |                       |
             |                       v
             |                  REMEDIATION
             |                video / notes /
             |                  AI tutor
             |                       |
             |                       v
             |                    RETEST
             |                       |
             +-----------+-----------+
                         |
                         v
                ADAPTIVE CONTROLLER
                         |
                         v
                   "WHAT NEXT?"
```

The **adaptive controller** eventually becomes the component deciding what learning or assessment experience the student should encounter next.

## 15. Relationship to the present Stage 0 and Stage 1A

**Stages 0 and 1A are not required to implement this complete adaptive-learning architecture. They establish the reliable content-generation foundation upon which the later architecture will be constructed.**

The immediate development strategy remains:

**Finish current Stage 0 → finish Stage 1A → test → stabilize → establish a known-good baseline**

Only afterward should the pipeline be expanded incrementally toward:

**source ingestion → curriculum compilation → micro-course generation → validation → assessment generation → learner model → adaptive controller → application**

Current work on source discovery, multi-source handling, provenance, validation, configuration, coordination, and generation infrastructure should therefore be preserved where possible and generalized rather than discarded.

## 16. Five foundational principles

1. **Curriculum before questions.** Build a validated knowledge and skill structure before large-scale assessment generation.
2. **Mastery before completion.** Watching content or answering a question once does not constitute learning.
3. **Evidence before adaptation.** The learner model should determine what the student needs next.
4. **Assistance and assessment must remain distinguishable.** AI-supported performance must not be mistaken for independent mastery.
5. **Generation serves pedagogy.** AI generates videos, notes, simulations, and questions because the curriculum and learner model require them—not simply because they can be generated.

## Status

This document is a **future architectural foundation**, not a requirement to redesign the current Stage 0 or Stage 1A implementation before those stages are completed and stabilized.
