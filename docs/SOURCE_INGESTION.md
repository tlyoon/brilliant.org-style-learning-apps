# Source-ingestion boundary

Source PDFs and extracted passages must not enter this repository.

The permitted Git artifact is a manifest containing:

- source identifier and controlled filename
- SHA-256 checksum
- edition or version when known
- chapter, subchapter, heading, and page range
- instructor-defined learning boundary
- extraction date and responsible reviewer
- rights/access note

Generated packages should cite manifest locations for provenance while remaining understandable without reproducing the source. If the source changes, create a new manifest version and re-review affected content rather than silently replacing provenance.


## Stage-1A source metadata continuity and multi-PDF discovery (6 November 2026)

A topic can contain the primary controlled source.pdf and arbitrary
supplementary PDFs in the same topic folder. The normal discover_topic_corpus
function now resolves the anchor and sibling PDFs in one bounded root traversal,
rather than rewalking the full root simply to list siblings. Callers may still
deliberately perform separate domain-binding or coordinator inventory scans.

- The configured Source Root remains singular; topic selectors are not roots.
- Case-insensitive filename collisions or ambiguous topic anchors stop before
  any download. Non-downloadable sibling PDFs cannot be silently skipped.
- The corpus order and coordinator topic_corpus_job_key algorithm remain
  unchanged, with the original exact hash locked by a regression.
- select_primary_source uses the configured target filename for old manifest
  validation and new manifests. A multi-PDF corpus without the configured
  primary fails closed; the single-source legacy fallback stays supported.
- All new tests use artificial metadata and do not contact Drive or AI models.

This improves source discovery and metadata provenance; it does not constitute
complete Stage 1A synthesis, a Topic Learning Model, a Course Learning Model,
independent scientific/EN-MS-ZH approval or public release.
Incident: BSA-20261106-123.
