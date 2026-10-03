# Decision 0025: Domain-profile architecture

## Status

Accepted.

## Context

The first mature visual/interaction implementation was built for university-level physics. Keeping physics template IDs, simulation laws, semantic validators, and renderer assets in the generic core would make the package superficially reusable but pedagogically unsafe for mathematics, chemistry, biology, history, and other disciplines.

## Decision

The repository shall separate a domain-independent learning-app engine from versioned subject-domain profiles. The current physics implementation becomes the first active profile at `domains/university-level physics/`, with stable machine ID `university-level-physics`.

Generic code owns source discovery, orchestration, schemas, publication, learner-shell behavior, and generic visual contracts. Domain profiles own subject-specific instructions, disciplinary rules, trusted renderer/template registries, simulation models, semantic validation extensions, verifier policy, and domain runtime assets.

Domain directories are resolved through `domains/registry.json` and `domain.json`; they are not imported by directory name. A domain must not be used merely because it is the default when textbook evidence indicates another subject.

Future Stage-0 work shall classify the textbook at the source-root/corpus level, not per subchapter. A confident unknown domain or ambiguous classification shall stop generation and require explicit domain onboarding rather than silently applying physics rules.

New domain profiles may be created with LLM assistance, from the repository template, by adapting an existing profile structurally, or by direct expert authorship. Generated domain instructions/code remain draft until deterministic validation and explicit activation. Automatic/distributed workers shall not independently invent and activate new domains.

## Consequences

Physics quality can continue to improve without weakening its scientific constraints, while new disciplines can add their own native representations and validators. Public bundles are assembled from the generic learner shell plus the active domain's runtime assets. Existing physics behavior remains covered by compatibility shims and regression tests during migration.
