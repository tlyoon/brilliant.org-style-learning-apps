(function (global) {
  "use strict";

  const domainRuntime = global.DomainVisuals;
  if (!domainRuntime || typeof domainRuntime.renderVisualSpec !== "function") {
    global.LearningVisuals = Object.freeze({
      rendererVersion: "unavailable",
      supportedTemplates: Object.freeze([]),
    });
    return;
  }

  global.LearningVisuals = domainRuntime;
  // Compatibility alias for packages/tests created before domain profiles existed.
  if (!global.PhysicsVisuals) global.PhysicsVisuals = domainRuntime;
})(globalThis);
