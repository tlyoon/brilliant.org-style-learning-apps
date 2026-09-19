# Khan Academy / Khanmigo-Inspired Foundational Strategy for Post-Stage 0 and Stage 1A Development

## Purpose

This document records a foundational design strategy for expanding the learning-app platform after the present Stage 0 and Stage 1A pipeline has been completed, tested, and stabilized.

The strategy is inspired by useful principles in Khan Academy and its AI tutor, Khanmigo, but is not intended to reproduce Khan Academy. The goal is to combine a **Brilliant-style, game-first student experience** with a **Khan-like mastery and adaptive-learning engine hidden underneath it**, then extend that combination specifically for physics education and examination preparation.

The central product principle is:

> **The student experiences a game; the system experiences a diagnostic, mastery, and exam-readiness process.**

The student-facing experience should therefore remain deliberately simple, minimally guided, fast to enter, and easy to continue. The purpose is to reduce psychological resistance among exam-focused students who may be impatient with conventional course structures, long explanations, or forced progression.

## 1. Product identity: game first, learning system underneath

The future application should feel more like a game than a conventional online course.

A student should be able to:

**open the app → choose a topic → start playing immediately**

The default interaction should emphasize short challenges, immediate feedback, score, progress, streaks, and optional assistance rather than visible curriculum machinery.

The student should not need to understand the underlying mastery model, prerequisite graph, remediation logic, or adaptive controller in order to use the app successfully.

The player-facing language may use concepts such as:

- worlds or topics;
- levels;
- challenges;
- score;
- XP;
- streaks;
- ranks;
- achievements;
- personal bests;
- friend challenges.

Internally, however, the same interactions should be represented as:

**curriculum → learning outcome → skill → question → response evidence → mastery update → next-action decision**

This separation between **simple player experience** and **rigorous hidden learning model** is a core architectural principle.

## 2. Fundamental philosophy: mastery rather than content consumption

The fundamental unit of the future learning system should be a **skill or learning outcome**, not a video or question.

A student does not complete a topic simply because a video was watched or notes were read. Progress should ultimately depend on demonstrated ability to apply the associated skills.

A useful internal progression is:

**Not Started → Attempted → Familiar → Proficient → Mastered**

For this project, the stronger principle is:

> **Content completed ≠ concept understood ≠ skill mastered ≠ exam mastery.**

The student does not need to see these states unless useful. The visible interface can remain much simpler than the internal model.

## 3. Start with a complete curriculum map

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

This knowledge structure should underlie all generated teaching and assessment artifacts, even if the student-facing app presents it as a much simpler sequence of game levels or challenges.

## 4. Build complete instructional material around each micro-topic

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

These instructional materials should not necessarily be forced upon the player before questions begin. They should also function as **on-demand assistance and remediation resources** that can be surfaced when useful.

## 5. Questions derive from learning outcomes, not merely textbook text

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

The player may experience these as varied mini-games or challenges, while the system records exactly which learning outcome and skill each interaction assesses.

## 6. Minimal-guidance interaction loop

The main mode of operation should be a **minimally guided gaming experience**.

A typical player loop should be as simple as:

```text
ENTER TOPIC
    |
    v
QUESTION / MINI-GAME
    |
    v
ANSWER
    |
    v
INSTANT FEEDBACK
    |
    v
+ SCORE / XP / STREAK
    |
    v
NEXT CHALLENGE
    |
    +--> optional Hint / Explain / Skip
    |
    v
MORE CHALLENGES
    |
    v
TOPIC COMPLETE
    |
    v
SCORE + RANK + ACHIEVEMENTS
    |
    v
Continue / Replay / Challenge / Review
```

The interface should avoid unnecessary menus, long onboarding, forced tutorials, and excessive explanation before play begins.

The design assumption is that many exam candidates are impatient. The product should therefore reward immediate engagement rather than require the student to first behave like a highly motivated learner.

## 7. No hard mastery locks

The platform should avoid requiring a student to pass the current question, lesson, or topic before continuing.

A player should normally be free to:

- skip a question;
- jump ahead;
- move to another topic;
- retry later;
- continue despite a weak score.

The system should not present skipping as punishment or failure.

Internally, however, a skipped question remains useful evidence:

> **The learner has not yet demonstrated this skill in this context.**

Skipping should therefore affect confidence in mastery evidence without creating a punitive player experience.

The guiding principle is:

> **Progression is encouraged, not locked.**

## 8. Assistance is optional and progressively intrusive

Assistance should appear only when requested or when offered unobtrusively by the system. The player should remain in control.

A useful progression is:

### Level 0 — No help
The student answers independently.

### Level 1 — Hint
A small nudge that preserves most of the challenge.

### Level 2 — Guided hint
Directs attention to the relevant idea or representation.

### Level 3 — Explanation
Explains the relevant concept or method.

### Level 4 — Show solution
Provides the complete reasoning or worked solution.

The system should record the assistance pathway separately from correctness. For example:

- solved independently;
- solved after one hint;
- solved after guided help;
- solved after explanation;
- solution revealed;
- skipped.

This creates a rich learner model without burdening the student with visible complexity.

## 9. Hierarchy of assessment

The future examination system should distinguish levels of assessment.

### Level 1 — Practice / Game Play
Single skills or short combinations. Optional AI assistance and skipping are allowed. This is the lowest-resistance entry point.

### Level 2 — Skill Check
Small collection of related questions. Assistance is limited or clearly recorded.

### Level 3 — Subtopic Test
Multiple related skills. Independent performance is emphasized.

### Level 4 — Topic Test
Skills are mixed within a larger syllabus topic.

### Level 5 — Mastery Challenge
Previously learned material is deliberately reintroduced after time has passed.

### Level 6 — Mock Examination
Authentic examination structure, timing, mark allocation, question mixture, and expected response style.

The app can therefore remain game-like during normal use while still providing increasingly rigorous evidence of genuine exam readiness.

## 10. Mastery must be demonstrated repeatedly

One correct answer should not establish mastery.

The system should distinguish:

> **I answered this correctly once**

from

> **I can reliably solve this class of problem across time, representations, and unfamiliar contexts.**

Later mixed assessments should be able to increase or decrease mastery estimates as new evidence arrives.

## 11. Use spaced reassessment

Previously learned skills should reappear after other material has intervened.

A typical sequence is:

**Learn A → practice A → establish proficiency → learn B → learn C → unexpectedly reassess A → update mastery confidence**

This is especially important for examinations because real examinations require mixed retrieval rather than immediate repetition of one question type.

In the player experience, these reassessments can simply appear as normal challenges rather than being announced as formal remediation or testing.

## 12. Separate learning assistance from independent assessment

AI-supported performance must not be confused with independent performance.

### Game / Learning Mode
Hints, explanations, optional assistance, and skipping are available. The primary goal is engagement, practice, and evidence collection.

### Independent Assessment Mode
AI assistance is disabled or tightly controlled. The student's independent performance is measured.

### Examination Mode
Questions follow examination-standard constraints, expected terminology and methods, realistic timing, and mark allocation.

This separation is essential for an AI-native educational system.

## 13. Extend mastery specifically for examination training

Maintain distinct evidence for at least three forms of mastery.

### Learning mastery
Can the student solve the task with educational support?

### Independent mastery
Can the student solve an unseen problem without AI assistance?

### Exam mastery
Can the student solve examination-standard problems independently, using appropriate terminology and methods and within realistic time constraints?

Example:

- Learning mastery: 96%
- Independent mastery: 84%
- Exam mastery: 68%

These measures need not initially be percentages; the exact mastery model can be determined later.

## 14. Separate game score from mastery

The visible game score and the hidden mastery model should not be the same quantity.

A game score or XP system may reward:

- correct answers;
- streaks;
- speed;
- difficult questions;
- independent solutions;
- persistence;
- returning regularly;
- topic completion;
- optional social challenges.

Mastery should instead estimate what the student can reliably do.

A highly active player may therefore have a large XP total while still having weaknesses in exam mastery. This is acceptable and desirable: the **game layer motivates**, while the **mastery layer diagnoses**.

## 15. Topic completion should produce a simple player-facing result

At the end of a topic, the player should receive a concise and rewarding summary rather than a dense learning analytics report.

For example:

```text
LEVEL COMPLETE

Waves
Score: 82/100
Rank: Silver
Best streak: 11
XP earned: +650
Exam readiness: B

Strongest area: Graph interpretation
Needs work: Wave calculations
```

The exact metrics can evolve, but the first view should remain simple.

The player can then choose among actions such as:

- Continue;
- Beat my score;
- Challenge a friend;
- Review weaknesses;
- View detailed breakdown.

The default path should usually favor continued play rather than forcing remediation.

## 16. Diagnose why marks are lost

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
- primary error category;
- assistance level;
- skip status.

Example:

**Question 173**

- Concept: Newton's second law
- Physics understanding: correct
- Mathematical manipulation: correct
- Unit: incorrect
- Exam terminology: correct
- Reasoning: incomplete
- Assistance: none
- Marks: 2/3
- Primary error: unit omission

Accumulated evidence should produce an actionable learner profile rather than only a single course percentage.

## 17. The learner model controls question generation

The future question generator should not independently decide what to generate.

The adaptive controller should first determine what evidence is useful about the learner while respecting the low-friction game experience.

Example request to the assessment generator:

- Course: IGCSE Physics
- Skill: velocity-time graph → displacement
- Current mastery: Familiar
- Last tested: 18 days ago
- Previous weakness: area interpretation
- Required question type: unfamiliar application
- Difficulty: medium
- Assistance state: optional
- Player flow constraint: do not interrupt current game session

Only then should the system select or generate the next challenge.

> **AI generation serves the pedagogy; pedagogy is not determined by whatever the generative model happens to produce.**

## 18. Khanmigo-like AI is the tutoring layer, not the curriculum

The AI tutor should operate inside a validated curriculum rather than defining the curriculum itself.

Its role is to facilitate reasoning through progressively appropriate guidance rather than immediately providing answers.

Example:

Student: *I don't understand why the acceleration is negative.*

Tutor: *Look at the gradient between 4 s and 8 s. Is the velocity increasing or decreasing?*

Student: *Decreasing.*

Tutor: *What sign must the gradient therefore have?*

The validated curriculum, learning outcomes, and skill map remain authoritative.

In the game-first design, this tutor should normally appear as an **optional assistance layer**, not as a compulsory conversational interface that interrupts play.

## 19. Automatic remediation should be offered, not forced

Assessment and instruction should eventually form a closed loop:

**Assessment → diagnosis → remediation → reassessment**

For example, repeated errors in conservation of momentum may make the system offer:

> *Want a 4-minute boost on momentum for bonus XP?*

If accepted:

**retrieve micro-lesson → short video/notes → AI-guided example → targeted practice → independent skill check → return to game**

If declined, the player may continue and the system retains the weakness for later adaptive use.

This preserves the pedagogical value of remediation without recreating the psychological resistance of a locked course.

## 20. Social participation is opt-in

Players should be able to reveal their presence and status to other users, but visibility must be voluntary.

A practical visibility model is:

### Private
The player's profile and progress are not discoverable by other players.

### Friends
Only accepted connections can see the information the player chooses to share.

### Public / Discoverable
Other players may find the profile and see the categories of information the player has chosen to expose.

Visibility should be granular. A player may choose whether to reveal items such as:

- username or display name;
- avatar;
- XP;
- topic scores;
- rank;
- streak;
- achievements;
- current topic;
- challenge availability.

Detailed weaknesses, error diagnoses, or private learning analytics should remain private by default unless explicitly shared.

## 21. Social interaction should revolve around learning and play

The social layer should not become a generic social network detached from the educational purpose.

Useful interaction patterns include:

### Friend challenges
A player invites another player to beat a score on the same topic or challenge set.

### Head-to-head play
Two players receive equivalent or identical challenge sets and compare performance.

### Cooperative challenges
Players work together toward a shared target, streak, or team score.

### Leaderboards
Possible scopes include friends, class, school, weekly, topic-specific, or opt-in public boards.

### Achievements and reactions
Players can celebrate milestones and respond to visible achievements.

### Study groups or teams
Players can form persistent groups for social motivation and friendly competition.

### Question-specific discussion
This may be added later if moderation, safety, and quality-control mechanisms are ready.

Social features should strengthen participation and persistence without being required for ordinary app use.

## 22. Competition should include self-competition

Public competition motivates some learners but discourages others. The system should therefore support both competition with others and competition with oneself.

Examples include:

- personal best scores;
- score improvement;
- mastery improvement;
- streaks;
- skills improved this week;
- previous rank versus current rank;
- exam-readiness improvement.

A weaker student should always have a meaningful path to success even when not near the top of a leaderboard.

## 23. Long-term post-Stage-1A architecture

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
               Challenge generation
                         |
                         v
                GAME EXPERIENCE
          question / mini-game / score
          hint / explain / skip / next
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
             |              OPTIONAL REMEDIATION
             |              video / notes / AI
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
                         |
              +----------+----------+
              |                     |
              v                     v
        NEXT CHALLENGE         SOCIAL LAYER
                              friends / teams /
                              challenge / compare
```

The **adaptive controller** eventually becomes the component deciding what learning or assessment experience is most useful next, while the **game layer** protects the simplicity and autonomy of the player experience.

## 24. Relationship to the present Stage 0 and Stage 1A

**Stages 0 and 1A are not required to implement this complete adaptive, game-first, social-learning architecture. They establish the reliable content-generation foundation upon which the later architecture will be constructed.**

The immediate development strategy remains:

**Finish current Stage 0 → finish Stage 1A → test → stabilize → establish a known-good baseline**

Only afterward should the pipeline be expanded incrementally toward:

**source ingestion → curriculum compilation → micro-course generation → validation → assessment generation → game layer → learner model → adaptive controller → social layer → application**

Current work on source discovery, multi-source handling, provenance, validation, configuration, coordination, and generation infrastructure should therefore be preserved where possible and generalized rather than discarded.

## 25. Foundational principles

1. **Game first at the interface.** The student should experience immediate, low-friction play rather than a visibly complicated learning-management system.
2. **Curriculum before questions.** Build a validated knowledge and skill structure before large-scale assessment generation.
3. **Mastery before completion.** Watching content or answering a question once does not constitute learning.
4. **Freedom before locking.** Students may skip, jump ahead, retry, and explore; progression should be encouraged rather than forced.
5. **Assistance is optional.** Help should be available progressively without interrupting players who want to continue unaided.
6. **Evidence before adaptation.** The learner model should determine what the system needs to test or support next.
7. **Assistance and assessment remain distinguishable.** AI-supported performance must not be mistaken for independent mastery.
8. **Game score and mastery remain distinct.** Motivation metrics should not be confused with evidence of exam readiness.
9. **Generation serves pedagogy.** AI generates videos, notes, simulations, and questions because the curriculum and learner model require them—not simply because they can be generated.
10. **Remediation should be helpful, not coercive.** Weaknesses should trigger attractive opportunities for support rather than hard barriers.
11. **Social visibility is voluntary.** Players control whether and how they are seen by others.
12. **Social interaction serves learning and motivation.** Competition, cooperation, and socialization should reinforce participation rather than distract from it.
13. **The hidden system may be sophisticated; the visible app should remain simple.** Complexity belongs in the architecture, not in the player's way.

## Status

This document is a **future architectural foundation**, not a requirement to redesign the current Stage 0 or Stage 1A implementation before those stages are completed and stabilized.

The near-term development priority remains to complete and stabilize Stage 0 and Stage 1A. The game-first, adaptive, mastery-based, and social features documented here are intended to guide the architecture that follows.