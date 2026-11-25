const assert = require("node:assert/strict");
const path = require("node:path");
const { auditRenderedPackage } = require("../scripts/audit_visual_rendering.js");

const root = path.resolve(__dirname, "..");
const label = (en) => ({ en, ms: "MS " + en, zh: "ZH " + en });
const base = {
  activities: [{
    id: "energy-a",
    visualSpec: {
      schemaVersion: "1.0",
      mode: "energy_bar",
      template: "state.energy_bar",
      entities: [
        { id: "kinetic", kind: "energy-component", label: label("Kinetic"), properties: { relativeAmount: 0.6 } },
        { id: "elastic", kind: "energy-component", label: label("Elastic"), properties: { relativeAmount: 0.4 } },
      ],
      accessibility: {
        description: label("Kinetic and elastic energy comparison"),
        colorIndependent: true,
        reducedMotionStrategy: "not-applicable",
      },
    },
  }],
};
const original = JSON.stringify(base);
const result = auditRenderedPackage(base, root);
assert.equal(result.status, "semantic_render_pass", JSON.stringify(result));
assert.equal(result.localeChecks, 3);
assert.equal(result.activitiesWithVisuals, 1);
assert.equal(result.pixelQualityVerified, false);
assert.equal(result.academicAccuracyVerified, false);
assert.equal(result.browserAccessibilityVerified, false);
assert.equal(JSON.stringify(base), original, "audit may not mutate source content");

const unsupported = structuredClone(base);
unsupported.activities[0].visualSpec.template = "untrusted.image";
const failure = auditRenderedPackage(unsupported, root);
assert.equal(failure.status, "fail");
assert.equal(failure.issues.length, 3);
assert.ok(failure.issues.every((x) => Boolean(x.problem)));
console.log("Read-only semantic visual rendering audit passes across three locales and fails on unknown templates.");
