# University-level physics visual rules

The trusted v1 physics visual library contains cart/collision scenes, free-body/vector diagrams, qualitative Cartesian graphs, energy bars, and a bounded one-dimensional constant-velocity simulation.

Physics visual specifications are semantic, never raw drawing code. Renderer geometry is derived from physical state, vector direction, graph relation, energy amount, or bounded simulation state.

For `mechanics.motion_1d_slider`, the trusted model is `kinematics.motion_1d` with `x = x0 + v t`. Velocity and elapsed time are bounded controls; position is derived. The simulation requires a constant-velocity invariant, instant-state reduced-motion behavior, and a static cart-scene fallback.

Unsupported or ambiguous physics visuals must simplify or fall back rather than invent missing scientific detail.
