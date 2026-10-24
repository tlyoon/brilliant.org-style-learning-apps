# Section 9.4 impulse approximation: review-only candidate

## Evidence and scientific reason

The generated activity int-select-isolated-conditions correctly uses Newton's
third-law cancellation of internal forces, but repeatedly describes total
momentum as *strictly* conserved under the impulse approximation. That
approximation says the net external impulse during impact is negligible, not
necessarily identically zero. The exact theorem is:

    total momentum change = net external impulse over the collision interval

A tiny nonzero external impulse (1/100000 in the independent rational-number
witness) produces a correspondingly tiny nonzero momentum change. This is
approximate, not exact, momentum conservation. In a truly isolated system,
or when the total net external impulse over the interval is exactly zero,
the total system momentum is conserved exactly regardless of collision type.

## Controlled repair

The authoritative original generated package on Yoga6 is not overwritten.
The review-only generator
app_generator/validation/impulse_qualifier_repair.py is bound to:
- controlled source PDF SHA256:
  08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578
- installed package canonical SHA256:
  2ffe799784c5492b5b8cf2062f7ffaa40264e3933820349b506c39fb651a01f7
- frozen original question/locale semantic SHA from the independent
  nine-interaction physics reference model.

It rewrites only one prompt, feedback, answer logic, explanation, hint,
prerequisite prompt, and the corresponding answer statement in English,
Malay and Chinese. It retains the original learning objective, visual plan,
all correctSelections, all item IDs and the other 17 activities.

The source-free tests require each rewritten language to distinguish
*approximate* conservation for negligible external impulse from *exact*
conservation for strictly zero net external impulse. Preserve delta,
integral and CJK glyphs without an encoding-loss fallback.

Private review output (outside Git) is saved on Yoga6 at:
%LOCALAPPDATA%/BrilliantContentGenerator/academic-source-evidence/
review-candidate-impulse-20261024-v2/

The review-only candidate package SHA256:
31a52ab461c62d0d9c7e244290b8ec94f3dd105f8056f2a8bb7db2b61cd5967a.

The first v1 candidate is **superseded**: its unchanged objective was not
preserved, breaking the visual contract, and its recorded file digest did
not match Windows-translated newline bytes. Never promote v1. v2 uses
exact UTF8 write_bytes with LF and verifies the disk SHA. The protected
original package is intact.

Reproduce on the authorized Yoga6 checkout (use a NEW private output path):

    python -I scripts/make_impulse_review_candidate.py --installed-package ORIGINAL_PACKAGE --source-pdf PRIVATE_PDF --out NEW_PRIVATE_FOLDER

The generation does NOT automatically install, merge, publish, mark a human
as having reviewed, or claim full academic PASS. The old physics proof
fingerprint is intentionally invalidated by changed narrative text. Before
any new academic PASS, independently verify exact source grounding,
complete answer/distractor semantics, EN/MS/ZH equivalence and matching
visual/interaction behavior of the new content.
