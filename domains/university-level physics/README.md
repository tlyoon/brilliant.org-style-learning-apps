# University-level Physics domain

This directory contains the subject-specific knowledge used by the generic Brilliant-style learning-app engine for university-level physics.

The root `domains/registry.json` maps the stable machine ID `university-level-physics` to this directory. The directory name intentionally remains human-readable: `university-level physics`.

Domain-specific prompts, scientific rules, renderer/simulation registries, runtime assets, validation extensions, and verification policy live here. Generic source discovery, LLM orchestration, schema handling, publication, coordination, and learner-shell code remain outside the domain.

A future textbook-domain discovery stage may select another installed domain. Until that work lands, this profile is the registry default so current physics behavior remains unchanged.
