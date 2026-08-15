# Architecture

## Logical components

- Responsive learner application with offline-tolerant activity delivery.
- Instructor content workspace and validation pipeline.
- Versioned learning-package store.
- Progress, mastery, and recommendation service.
- Guarded AI tutor with retrieval from approved content.
- Teacher, student, and consented read-only supporter reporting views.
- Audit and quality-review pipeline.

## Boundaries

Repository content is provider-neutral. Application, database, model, and hosting choices remain open until the vertical-slice issue defines them. Production dependencies require approval.

## Data flow

Instructor source → controlled extraction outside Git → source manifest → original draft package → schema and rule validation → scientific/instructional review → versioned publication → learner evidence → mastery/recommendation → minimal reporting summaries.

Raw source documents, personal data, audio, credentials, and production exports stay outside GitHub.

## Reliability principles

- Version content and algorithms independently.
- Make submissions idempotent and queue them during intermittent connectivity.
- Preserve first-attempt evidence before retries.
- Log safety decisions without storing unnecessary conversation content.
- Degrade gracefully to validated static hints if the AI tutor is unavailable.

