# Decision 0083 — Version-bound public destination scope and permissions (BSA227)

**20 November 2026.** Owner continuation v7.1 for BOSLA, Yoga 6.

## Historical failure and authoritative observations

BSA225/BSA226 established genuine private V7 output with six source-bound
packages, independent real Chrome and signed native V3 release receipts.
The next checkpoint requested public deployment scope and permission checks.
The [automation] configuration targets `tlyoon/section-8-1-learning-app`
at `https://tlyoon.github.io/section-8-1-learning-app/`, despite the
legacy section-8.1 repository name.

Read-only authenticated owner GitHub verified that this **existing** public
Pages repository is not Section-8.1-only: `main` at SHA
`eb86fe8eb94ec33f8c0c055d2423b245e5898241` contains routes
`section-9-1` through `section-9-9`; the connected account reports
admin and push rights. The exact genuine source comparison with the private
V7 candidate finds only five changed activities across sections 9.1 (one),
9.2 (one), and 9.6 (three); 9.3, 9.4, 9.5 are byte-identical. Each of the
six routes contains 18 activities with stable IDs and package identities.
All public and candidate package status fields remain `draft`.

## Automatic V8 read-only release-scope boundary

The normal `--source-free-advance` path must automatically dispatch
`v3_public_deployment_scope.verify_public_deployment_scope` once authentic
V7 succeeds. This step checks source Git clean exact-head hosted CI, signed
V7 private receipt, configured destination and Pages URL, authenticated
GitHub admin/push rights, and a read-only clone of the actual public main
branch. It compares the six real existing public SHA256 package bytes to
the previously frozen exact revision, verifies all six genuine private
source digests and activity identifiers, requires exactly the expected
1+1+0+0+0+3 changes, protects routes 9.7–9.9, and checks that remote main
has not moved during the audit. It writes an immutable local V8
integrity receipt. Any drift, changed source, missing permission, HMAC
tampering or unexpected public change fails closed instead of silently
overwriting live course content.

The step only uses authenticated read-only `gh api`, `git clone`,
`git rev-parse`, and `git ls-remote`. It **does not** invoke
`PublicPagesPublisher`, push a branch, create/merge a PR, run Gemini,
read source PDFs, or deploy publicly. The fact that repository
configuration currently enables auto merge is NOT itself permission to
bypass the final exact-version release route. No human academic signoff,
rights gate, visual approval or learner pilot is reintroduced as a
technical-completion criterion.

## Validation and forward progression

Synthetic fault controls test wrong destination, modified public package,
stale public base SHA, changed activity identities/roster, missing
other Chapter 9 routes, compromised V7 evidence, prohibited write commands,
and immutable V8 restart. Genuine Yoga 6 audit and normal worker must
produce V8, exact-head CI must pass, and the recovery registry must record
the working remedy. The next operational milestone is a pinned,
non-destructive public release proposal that cannot merge blindly or
overwrite unrelated material. Independently, the historical finite C3
three-topic generalization remains `FAILED_LIMITED_CAMPAIGN` and is
not changed by this release evidence.
