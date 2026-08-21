# Decision 0006: Distributed one-PDF generation workers

**Status:** Accepted 21 August 2026

## Context

The controlled source tree contains one `source.pdf` below each subchapter directory. Several independently configured Windows PCs may generate learning-content drafts concurrently. A local scan followed by a later status update can assign the same PDF to two PCs. Mutating a shared Gem Knowledge collection creates an additional cross-worker collision boundary.

## Decision

- Process exactly one controlled PDF per generation job.
- Keep the reusable Gem Description and Instructions fixed after one-time initialization.
- Attach the claimed PDF to a fresh Gem conversation; do not place source PDFs in Gem Knowledge.
- Identify each source version by Drive file ID plus Drive version/checksum metadata.
- Use a central atomic lease registry with worker ID, expiry, heartbeat, attempt count, branch, PR URL, and status.
- Stop a worker before commit or push when lease ownership cannot be proved.
- Generate on a unique feature branch and open a draft PR; do not push directly to `main`, merge, publish, or deploy automatically.
- Keep generated packages as drafts pending the existing qualified human reviews.

For the pilot, the coordinator is a private Google Sheet updated through Apps Script `LockService`. A transactional database-backed coordinator may replace it later without changing the source, generation, validation, or Gem-conversation boundaries.

## Consequences

- Multiple PCs can generate different subchapters concurrently without sharing mutable Gem source state.
- A crashed worker's job can be reclaimed after lease expiry.
- The coordinator and GitHub review state become operational dependencies in distributed mode.
- Selenium remains vulnerable to Gemini UI changes and therefore requires a controlled live validation before batch operation.
- Submitted PDF files may remain in Gemini Activity according to the account's retention settings; local deletion does not imply service-side deletion.
