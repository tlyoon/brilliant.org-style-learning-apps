# University-level physics visual registries

This domain directory contains the repository-owned university-physics registries used by the visual-first activity contract. Generated packages may reference these IDs but may not define arbitrary renderer or simulation code.

- `template-registry.json` - supported representation templates, visual modes, allowed render strategies, and trusted simulation-model bindings.
- `style-profiles.json` - versioned aesthetic intent shared by deterministic renderers and generated-image prompts.
- `simulation-model-registry.json` - trusted simulation model identifiers, variable vocabularies, controllable variables, and independent verification categories.

The registries are validated by `app_generator.visuals.validation.visual_registry_errors`. A broken or internally inconsistent trusted registry blocks repository/generator validation.

Adding a new template or model is a code-review event, not a content-generation event. A simulation prototype produced in Replit or another external tool must be promoted into repository-owned, tested runtime code before its registry entry is considered production-capable.

Provider names and model versions do not belong in generated activity content. Runtime configuration will map provider-neutral strategy/profile names to approved Gemini image models, independent verifiers such as Wolfram, and local deterministic renderer implementations.

## Runtime availability

`implementationStatus` distinguishes a contract that merely exists from a template that the learner runtime can actually render. `available` entries bind to an exact repository renderer ID and version. `planned` entries are not selectable for publishable generated content.

The current deterministic runtime (`physics-renderers.js`, renderer version `1.0.0`) implements cart/collision, free-body/vector, qualitative Cartesian graph, and energy-bar templates. The motion-slider simulation is available as `mechanics.motion_1d_slider` with the trusted `kinematics.motion_1d` model.
