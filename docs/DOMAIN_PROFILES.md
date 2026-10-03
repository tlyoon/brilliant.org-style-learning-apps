# Domain profiles and new-subject onboarding

## Purpose

The repository is one Brilliant-style learning-app engine, not a physics-only fork. Generic source discovery, Drive/coordinator logic, LLM transport, package schemas, publication, the learner shell, and generic visual contracts stay in the shared core. Subject-specific pedagogy, scientific/disciplinary rules, visual templates, simulations, validation extensions, verification policy, and runtime assets live under `domains/`.

The current installed domain is `university-level-physics`, stored in the human-readable directory `domains/university-level physics/`. `domains/registry.json` maps the stable machine ID to that directory. The space in the directory name is intentional; code loads it through the manifest rather than importing the directory as a Python package.

## Three-layer model

```text
generic learning-app engine
        +
active domain profile
        +
project/course policy
        =
generated learning experience
```

Examples of generic concerns are source-tree traversal, multilingual field handling, activity packaging, deployment, accessibility primitives, visual-plan/spec schemas, and safe fallback. Examples of domain concerns are free-body diagrams in physics, molecular structures in chemistry, geometric constructions in mathematics, pathway diagrams in biology, or timelines/maps in history. Project/course policy contains choices such as activity quotas, supported learner languages, calculator policy, mastery presentation, and deployment configuration.

## Current domain layout

```text
domains/
  registry.json
  _template/
  university-level physics/
    domain.json
    instructions/
    rules/
    visuals/
    simulations/
    validators/
    verification/
    tests/
```

`domain.json` is the domain contract. It declares the domain identity and the paths to its instructions, rules, renderer/style assets, simulation registry/model module, validation hook, verification policy, and trusted renderer identities. The generic core resolves those paths; it does not hard-code physics template IDs.

## Current behavior and next Stage-0 behavior

On the revision that introduced this architecture, `university-level-physics` remains the default active domain so the existing physics generator is behavior-compatible. Automatic textbook-domain classification is the next bounded Stage-0 implementation slice; it must not be falsely described as already active.

The target Stage-0 flow is:

```text
single source root
  -> discover all subchapter source corpora
  -> infer one textbook-level subject/academic level from representative samples
  -> cross-sample consistency/confidence check
  -> resolve an installed active domain profile
  -> bind source-corpus fingerprint to domain ID/version
  -> continue generation
```

All subchapter sources beneath one configured source root are assumed to belong to the same textbook. Classification is therefore textbook-level, not per-subchapter. A mathematics-heavy chapter in a physics textbook must not silently switch the project to a mathematics domain.

If the classifier is ambiguous, or if a confident domain has no installed active profile, automatic/distributed generation must stop safely rather than falling back to the current physics rules. Interactive operation should explain the detected domain and request manual domain onboarding. Auto workers must record a domain-profile-required state and exit/wait cleanly rather than blocking for keyboard input or creating competing profiles on several PCs.

## Creating a new domain today

Until the planned `domain bootstrap` workflow is implemented, domain onboarding is deliberately manual. Use one of the alternatives below and keep the new profile unregistered until it is complete enough to validate.

### Alternative A - LLM-assisted domain authoring (recommended)

1. Create `domains/<human-readable domain name>/` by copying `domains/_template/` as a structural guide; rename the `.example` files to their runtime names.
2. Give the LLM representative samples from the new textbook/source tree plus this document, the generic architecture/content/visual documents, and the `_template` contract. Do **not** ask it to copy physics pedagogy semantically.
3. Ask it to identify the domain's dominant reasoning modes, misconceptions, native representations, useful interaction families, answer-critical information, hallucination hazards, appropriate independent verification, and safe fallbacks.
4. Have it draft the domain instructions/rules and propose trusted renderer/simulation specifications. LLM output remains a draft: it must not mark unsupported runtime code as available.
5. Implement or promote any required deterministic renderer/simulation code into the new domain directory and add domain-specific tests.
6. Set the domain manifest to `active` and add it to `domains/registry.json` only after the profile is coherent and repository validation passes.

This is the intended precursor to a future interactive bootstrap command. That command will automate drafting and file placement, but activation will remain an explicit intervention.

### Alternative B - minimal text-first domain

For a new discipline where no trusted visual/simulation library exists yet, start safely with empty `templates` and `models` registries, the no-op domain renderer from `_template`, and a concept-first style profile. Generic MCQ/matching/ordering/classification interactions can still be used. Add domain renderers later. This is preferable to reusing incorrect physics visuals merely to achieve visual coverage.

### Alternative C - clone the closest installed domain structurally

An expert may copy an existing domain directory to accelerate setup, but every subject-specific instruction, validator, template/model registry, verifier policy, and runtime asset must be reviewed and replaced as needed. Never retain a physics invariant, molecular rule, chronology rule, or other subject semantic merely because the directory structure is convenient.

### Alternative D - expert-authored profile

A domain expert can author the profile directly without an LLM. This is especially appropriate when the discipline has formal notation or safety/correctness constraints that are easier to codify deterministically than to infer from prompts.

## What a domain-authoring LLM should produce

The manual/automated authoring brief should ask for:

- stable domain ID, display name, subject and academic level;
- source-analysis and activity-generation extensions;
- domain-specific content and visual rules;
- native representations and when each is pedagogically valuable;
- trusted renderer/template proposals and their semantic parameters;
- simulation models, controllable/derived variables, bounds and invariants;
- domain-specific semantic validation hooks;
- independent verification policy and providers where useful;
- accessibility/mobile/multilingual considerations particular to the representations;
- safe fallback behavior for unsupported or ambiguous representations;
- seeded tests for likely hallucinations and cross-modal contradictions.

Generated raster imagery may improve appearance, but no domain may let image pixels become the only source of answer-critical truth when a deterministic representation can carry it.

## Activation checklist

Before registering a new domain as active:

- its `domain.json` ID and paths are valid and stay beneath its own directory;
- required instruction/rule/registry/runtime/validator/policy files exist;
- every template marked `available` has a matching trusted renderer identity/version;
- every simulation references a declared model and bounded controls/invariants;
- domain-specific validation rejects seeded incorrect examples;
- generic package/schema/deployment tests still pass;
- a representative source sample produces pedagogically appropriate activities for that discipline;
- the profile does not inherit unrelated rules from another subject;
- documentation states any deliberately unsupported visual/simulation families.

## Source-tree changes

Changing the configured source root to another textbook will eventually trigger the textbook-domain discovery step. The planned corpus/domain lock will bind a source-corpus fingerprint to the selected domain ID/version so a stale physics profile cannot silently be applied to a chemistry, mathematics, biology, history, or other textbook.

Until automatic discovery lands, changing to a different-subject source root requires manual domain selection/onboarding rather than assuming the default physics profile is appropriate.
