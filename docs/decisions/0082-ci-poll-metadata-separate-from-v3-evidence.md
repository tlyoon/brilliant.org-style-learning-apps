# Decision 0082 — Keep CI polling metadata out of native V3 release evidence

19 November 2026. BSA-20261119-226. Applies to BOSLA on owner Yoga6.

## Actual failure

At committed Git 926edf49, the first genuine 108/698 source-bound Chrome
checks completed before GitHub CI #44536308759. BSA224's normal sourcefree
poller safely waited and recovered green CI, and the same ordinary worker
generated the entire six-package V1-V6 private native V3 technical dossier.
The next new BSA225 V7 public builder gate returned a ValueError with
normal-worker exit 3, with no public deploy.

The error was reproduced precisely without any provider call: the CI-resume
helper returns a verified readiness copy with two transient diagnostic fields,
`ciRecoveryPolls` and `ciRecoveredInSameInvocation`. The strict V7 release
checker requires that exact readiness equals the original persisted source
evidence, and correctly refused the modified copy:
`V3_PUBLIC_BUILD_READINESS_NOT_SAVED`.

On the same exact genuine SHA and saved canonical readiness, the actual
original six private public-release builders passed 6/6 through native
exact-package HMAC gates. No scientific defect or failed publisher bundle
was observed.

## Architectural repair

The ordinary sourcefree controller now separates operation-level CI-poll
diagnostics from the canonical signed scientific/browser/CI readiness. It
passes only the original identical saved proof to all V1-V7 native package
gates, retains a separate nonauthoritative
`exactHostedCiRecovery` record with a bounded count, and refuses a malformed
purported successful recovery. Failed/unknown/timeout CI never proceeds to
V7; no paid provider request or historical source operation is replayed.

The targeted pre-fix negative control reproduced the exact genuine refusal.
A delayed-CI synthetic regression now explicitly injects poll annotations,
checks the original V7 admission contract, asserts that the metadata is
not present in the evidence sent to the private release gate, and also
protects the original CI-failure negative control.

## Closure

BSA226 and dependent BSA225 remain ACTIVE until new committed exact-head
CI succeeds and owner Yoga6 executes real ordinary
`--source-free-advance` with source-bound 108/698 and V1-V7 genuine
private outputs including a six-build V7 receipt. This is not public
publication or independent C3 generalization. The frozen two-round C3
`FAILED_LIMITED_CAMPAIGN` status is unchanged.
