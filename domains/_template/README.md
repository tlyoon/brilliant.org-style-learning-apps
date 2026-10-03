# Domain-template workspace

Copy this directory to `domains/<human-readable domain name>/` when manually creating a new subject domain. Rename `.example` files to their runtime names, fill the manifest and instructions/rules, and keep the new domain out of `domains/registry.json` until it has been validated and intentionally activated.

A safe minimal domain may start text-first with empty template and simulation registries plus the no-op renderer. Add deterministic renderers/simulations only after their semantics and tests are defined.
