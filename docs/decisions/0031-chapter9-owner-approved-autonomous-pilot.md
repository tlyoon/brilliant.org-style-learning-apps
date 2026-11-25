# Decision 0031 - Owner-approved Chapter 9 pilot and autonomous acceptance

Status: OWNER_APPROVED_SCOPE, 7 November 2026. New independent course-pilot scope after terminal Decisions 0029 and 0030; previously exhausted campaigns remain terminal.

## Owner authorization and autonomous review contract

The owner explicitly approves Chapter 9 sections 9.1-9.6 as the exact pilot roster. The owner reiterates that development, physics/diagram/visual, multilingual and technical verification are autonomous: no mandatory manual academic reviewer, manual grading or further routine owner approval is to be introduced. Authorized AI-assisted independent source-grounded QA must actually corroborate each scientific, diagram, answer and EN/MS/ZH claim; it must fail closed where evidence is missing. This does not waive source or third-party figure rights, external service restrictions, institutional student privacy, paid operation limits or explicit public release and merge permission.

## Frozen selection identities

Existing six tracked packages are fixed as of candidate PR #223 commit 689fcdf8e5c9999331bc21ae597dbe99362e729d. Package blob SHA-1 values below are exact committed package identities. PDF SHA-256 values are preexisting source-manifest declarations only, not newly rehashed original PDF bytes. Drive listed each original source.pdf ID matching the corresponding manifest. Existing packages are all drafts, EN/MS/ZH, 18 activities per section (9 MCQ and 9 interactive), with 0/108 declared visualSpec activities.

| Section | Selected topic | Git package blob SHA-1 | Manifest-reported original PDF SHA-256 |
|---|---|---|---|
| 9.1 | Linear Momentum | 6dc84d7bbc8f6944d150bb79bb26906a71e2f3f5 | cdbea066436ace273b94aedc2eb1b22f94d0fd5b0b3f810d6bfc27469a5e7b50 |
| 9.2 | Analysis Model: Isolated System (Momentum) | 779deb4e207078f9081a9de78a14226d473f9b25 | 07f5aad2a580e5684d882e3b7370f381f86b410474e8837cbbb65ebfc17c4547 |
| 9.3 | Analysis Model: Nonisolated System (Momentum) | 7b019d9502d8da7eab9f311e9c3d0830e8b30396 | a813202fdd9155b310027c73e1bc4b3d5eff3b8a0c29f428061352b1b6634a25 |
| 9.4 | Collisions in One Dimension | f9604d795a6d8c02d2de02a5672f8cba0e4bf949 | 08c450e780e95aab57cfd7425df1401893c52378a2a5e890df4bbcd58c3d0578 |
| 9.5 | Collisions in Two Dimensions | aa6d34978b79a13cf26f9558c21dd8aafa08c80b | 3c3d2c145d7fa3ff86e8632144c7be695225372591d95df0a594b75c5b381049 |
| 9.6 | The Center of Mass | 90b8a5e7d627de3bfcc2320428981e73022a968e | 1e73735b2b44f6b287f3e3fcd1a2d8febd85fcd5aeba273a4b83bcf038929717 |

## Finite fully autonomous closure procedure

1. Scope: PASS_OWNER_APPROVED for only these six sections. No further manual instructor selection is needed.
2. Source-free structural/integrity: run one isolated frozen clean worktree check using existing prepare_course_preview.py and audit_course_pilot_readiness.py. Record Git SHA and per-worktree package SHA-256 privately. No original PDF/model/student data/publication.
3. Real-package browser: run existing full learner browser audit on the six approved packages, no more than one bounded run each per unchanged source package and exact code head; keep receipts private. Local browser technical proof does not establish meaning, visuals or institutionally approved course operation.
4. Independent academic/visual: automatically establish real original source checksum and necessary use rights, independent physics/answer and EN/MS/ZH meaning, diagram and meaningful visual representations with sources. No manual human academic sign-off, but no self-certified PASS or unauthorized protected-data distribution.
5. Actual pilot: independently verify real course-wide diagnostic, adaptive prerequisite routing, accessibility including mobile touch and reduced motion, privacy/consent/retention and operational rollback. Existing local six-option preview is not a full adaptive course.
6. Integration/release: keep PR #223 draft/unmerged; do not merge or deploy without separate evidenced mandatory acceptance and explicit authorization.

## Existing CRLF portability issue

An isolated Yoga 6 Windows Git-clean worktree at 689fcdf8e5c9999331bc21ae597dbe99362e729d had core.autocrlf=true and i/lf w/crlf on packages. The old roster implementation rejected it against the LF Git blob. Git normalized hash-object --path equaled HEAD blob. Generalized fix and adversarial regression BSA-20261107-127 address the shared Git checkout representation problem; keep the actual-file SHA-256 guard. Do not restart the historical Section 9.4 PDF repair loop.

Only instructor scope is closed. Independent source, scientific, translation, visual, accessible real learner, institutional and release gates remain NOT_VERIFIED or NOT_AUTHORIZED.
