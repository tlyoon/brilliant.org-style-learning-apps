# Section 1.1 review record

## Current status

Ready for qualified human review. The package remains `review`, not `publishable`, until every sign-off below is recorded by an appropriate reviewer.

## Completed authoring checks

- Source boundary checked against the instructor-provided Drive PDF, textbook pages 3–6.
- Source PDF SHA-256 recorded without committing the PDF.
- All learner activities are newly written and use only source-location provenance.
- Current SI definitions checked on 17 August 2026 against the BIPM SI Brochure, 9th edition version 4.01, and NIST's current SI base-unit definitions.
- The obsolete artifact definition of the kilogram in the 2019 source is not taught as current science.
- Automated schema, distribution, multilingual-completeness, calculator-free, and repository checks are required before review.
- All nine interactive activities use multi-item, mode-specific response data rather than single-choice answer keys; complete placements, orders, or selections are machine-validated.

## Independent-review corrective-action traceability

These entries record authoring work and automated evidence only. They are not reviewer sign-offs.

| Finding | Corrective action | Automated evidence | State |
|---|---|---|---|
| Interactive records behaved as single-choice questions | Replaced all nine with multi-item classification, matching, ordering, or multiple-selection data | Schema and `test_review_rejects_single_choice_disguised_as_interactive` | Addressed; pending human review |
| Interaction modes lacked complete response semantics | Added mode-specific schema rules and complete placements, order, or selections | `test_schema_enforces_mode_specific_interaction_shapes` | Addressed; pending human review |
| Difficulty was nominal rather than demonstrated | Reworked challenging interactions around chained density reasoning, compound unit–constant matching, and multi-fault diagnosis | Distribution and package validation tests | Addressed; pending instructional review |
| Learning support and provenance did not follow expanded tasks | Aligned prompts, hints, feedback, recovery, accessibility text, and page ranges with every rewritten activity | Multilingual schema and package validation | Addressed; pending language and provenance review |
| Incorrect responses could not support misconception diagnosis | Added response-pattern diagnostic rules and corrected density distractor mappings | Diagnostic-rule validation and tests | Addressed; pending instructional review |
| Calculator-free validation omitted interaction text | Extended scanning across learner-facing prompts, labels, hints, feedback, explanations, and recovery text | `test_numerical_requests_are_rejected_in_interaction_labels` | Addressed |
| Package consumers and regression tests did not exercise genuine interactions | Versioned the contract as schema 1.1 and added accessible rendering/tests for every interaction mode | Node interaction-rendering regression test | Addressed; pending accessibility review |

## Required sign-offs

| Domain | Status | Reviewer requirement |
|---|---|---|
| Physics and metrology | Pending | Qualified physics instructor or metrology subject-matter expert |
| Instructional design and difficulty | Pending | Instructor or learning designer |
| English | Pending | Instructor/editor |
| Malay | Pending | Competent Malay-language reviewer |
| Simplified Chinese | Pending | Competent Simplified-Chinese reviewer |
| Accessibility and interaction semantics | Pending | Accessibility reviewer, including keyboard and screen-reader walkthrough |
| Provenance and originality | Pending | Instructor or repository maintainer with access to the controlled source |

Reviewers must record their name, date, outcome, and any corrective action here before the package status changes to `publishable`.

## Current standards references

- BIPM, “The International System of Units (SI),” 9th edition, version 4.01: https://www.bipm.org/en/publications/si-brochure
- BIPM, “SI defining constants”: https://www.bipm.org/en/measurement-units/si-defining-constants
- NIST, “Definitions of SI Base Units”: https://www.nist.gov/si-redefinition/definitions-si-base-units

