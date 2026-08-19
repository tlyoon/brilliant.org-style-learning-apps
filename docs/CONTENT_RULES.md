# Content rules

## Non-negotiable rules

1. Activities are newly written; do not copy or closely paraphrase textbook questions or passages.
2. Store source filename, checksum, page range, and heading—not source text.
3. Every question must be solvable without arithmetic, a calculator, or a numerical response.
4. Use qualitative comparisons, ordering, classification, diagram interaction, misconception diagnosis, and conceptual prediction.
5. Every publishable subchapter has exactly 18 activities with the required type/difficulty distribution.
   Interactive activities must require learners to manipulate and resolve multiple items through classification, matching, ordering, or multiple selection; a single-choice answer key is an MCQ, not an interactive activity.
6. English (`en`), Malay (`ms`), and Simplified Chinese (`zh`) learner-facing fields must be complete and semantically aligned.
7. Each activity declares learning objective, misconception targets, hints, feedback, answer logic, provenance, and accessibility text where media is used.
   Each interactive activity also declares machine-readable diagnostic rules for recognizable incorrect response patterns.
8. Generated variants must preserve the same concept, difficulty, answer logic, and calculator-free status.

## Prohibited patterns

- Prompts requesting a calculated value, decimal, percentage, unit conversion, or equation evaluation.
- False precision in mastery or cohort comparisons.
- Punitive lives or engagement mechanics that block learning.
- Leaderboards based on raw speed or total activity volume.
- Unsupported AI answers outside the approved package and standard prerequisites.

Use `python scripts/validate_content.py` before review. Automated checks are necessary but do not replace scientific and instructional review.

