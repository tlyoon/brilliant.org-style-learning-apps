# Security and privacy

## Data minimisation

Use synthetic identities in development. Never commit names, matric numbers, learning records, raw audio, tutor transcripts, parent/supporter links, API keys, `.env` files, production logs, or database exports.

Raw voice audio is deleted immediately after transcription. Tutor transcripts are retained only temporarily for safety and quality review; the default planning assumption is 30 days, subject to institutional approval. Retain a compact diagnostic summary for the course plus 12 months, then remove identifiers. Aggregated anonymised statistics may remain for product evaluation.

## Access

- Course learning packages are private by default and controlled by the uploading instructor.
- Teacher views follow least privilege.
- Students can inspect and export their own learning history.
- Any read-only supporter link is revocable, consent-based, auditable, and scoped to one learner.
- Detailed supporter access for adult university students requires explicit student choice and institutional review.

## AI and supply chain

- Ground tutor output in approved content and standard prerequisites.
- Do not send personal identifiers to a model unless separately approved and required.
- Maintain a soft AI budget with a lower-cost fallback; preserve validated non-AI help when unavailable.
- Pin dependencies, review additions, enable secret scanning, and keep automated deployment and merging disabled during the prototype.

Suspected privacy or security incidents must be handled outside ordinary public issue text.

