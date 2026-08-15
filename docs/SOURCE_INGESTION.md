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

