# Product requirements

## Purpose

Create a mobile-first, concept-driven learning application inspired by short interactive learning journeys without copying any protected product design, wording, assets, or branding.

The physics product should increasingly behave as a **visual-interactive reasoning environment**: learners predict, manipulate, compare, classify, and observe meaningful representations rather than merely answer a sequence of text questions.

## Pilot scope

- Six subchapters from an instructor-selected undergraduate physics chapter.
- Formative practice only; pilot performance does not directly determine course grades.
- Initial access uses a student's formal name and matric number, implemented outside this repository with appropriate institutional controls.
- Class-only pilot built on a reusable architecture suitable for later subjects and institutions.
- Automatic unlocking with adaptive routing to prerequisites and delayed review.

## Required learner experience

- Short diagnostic and recommended starting point.
- One clear idea per screen with prediction before explanation where suitable.
- Activities use diagrams, graphs, state representations, animations, or simulations whenever those representations materially improve the physics reasoning.
- Manipulation is preferred when changing a meaningful parameter helps expose cause and effect, an invariant, or a physical relationship.
- Visuals are instructional, not decorative: every important entity, vector, label, graph feature, or state must be relevant to the activity and scientifically consistent with its answer logic.
- Text-first activities remain valid when a visual adds little learning value; there is no requirement to attach irrelevant imagery merely to reach a visual percentage.
- Hints, retries, explanations, prerequisite activities, and the ability to skip an activity without being forced to answer it.
- Named mastery level shown prominently; percentage shown secondarily.
- Cohort standing calculated separately for each subchapter and shown only with adequate comparable evidence.
- Student view distinguishes independent from assisted performance.
- Mobile, keyboard/touch, reduced-motion, multilingual, and non-color-only accessibility are preserved as interaction types expand.

## Required activity package

The current Stage-0 package contract remains 18 activities per publishable subchapter: nine multiple-choice and nine interactive, with exactly three easy, three moderate, and three challenging activities of each type. All activities must be original, conceptual, multilingual, and calculator-free.

This quota is a compatibility requirement for the current baseline, not the long-term pedagogical target. Under the Stage-2 visual-interactive framework, activity type and quantity may become pedagogically selected once the richer schema, renderer library, validation, and pilot evidence are proven. Any such migration requires an explicit versioned schema/product decision rather than silently changing the current contract.

Every generated activity must receive a visual-value assessment. When a visual is required, the learning package supplies a versioned declarative visual specification for a trusted renderer or interaction primitive; generated arbitrary executable visual code is not part of the content contract. The plan also declares an aesthetic/render strategy: generated imagery may provide polished context when useful, but answer-critical physics remains deterministic and generated-image composites must pass final multimodal audit.

## Out of scope for the foundation

- Production authentication, hosting, billing, and databases.
- Copyrighted textbook storage.
- Real student records or tutor transcripts.
- Final branding or a public marketplace.
- Unconstrained AI-generated executable simulation code.
- Decorative photorealistic imagery that does not contribute to the learning objective.
