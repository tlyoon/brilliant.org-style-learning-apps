"use strict";
/* Read-only, DOM-semantic renderer smoke audit; no browser or pixel assertions. */
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

class AuditElement {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.attributes = {};
    this.className = "";
    this.value = "";
    this._text = "";
  }
  set innerHTML(_) { throw new Error("Unsafe renderer innerHTML assignment"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((c) => c.textContent).join(""); }
  append(...elements) { this.children.push(...elements); }
  setAttribute(key, value) {
    this.attributes[key] = String(value);
    if (key === "class") this.className = String(value);
  }
}
const descendants = (root) => [root, ...root.children.flatMap(descendants)];
const document = {
  createElement: (tag) => new AuditElement(tag),
  createElementNS: (_, tag) => new AuditElement(tag),
};

function auditRenderedPackage(pkg, root) {
  const context = { console, document, globalThis: null };
  context.globalThis = context;
  const script = fs.readFileSync(path.join(root, "domains/university-level physics/visuals/physics-renderers.js"), "utf8");
  vm.runInNewContext(script, context, { filename: "physics-renderers.js" });
  vm.runInNewContext(fs.readFileSync(path.join(root, "app/visual-renderers.js"), "utf8"), context);
  const messages = [];
  let examined = 0;
  for (const activity of pkg.activities ?? []) {
    if (!activity.visualSpec) continue;
    examined++;
    for (const locale of ["en", "ms", "zh"]) {
      try {
        const rendered = context.LearningVisuals.renderVisualSpec(activity.visualSpec, { document, locale });
        if (!rendered || rendered.tagName !== "FIGURE") throw new Error("renderer did not produce a figure");
        if (rendered.className.includes("fallback")) throw new Error("renderer fell back from trusted semantic visual");
        if (rendered.attributes["data-template"] !== activity.visualSpec.template) {
          throw new Error("renderer template ID mismatch");
        }
        if (!rendered.attributes["aria-label"]?.trim()) throw new Error("missing localized accessible description");
        const elements = descendants(rendered);
        if (!elements.some((item) => item.attributes["data-semantic-id"])) {
          throw new Error("no deterministic semantic elements");
        }
        for (const element of elements) {
          for (const name of ["height", "width", "x", "y"]) {
            const value = element.attributes[name];
            if (value !== undefined && !Number.isFinite(Number(value))) {
              throw new Error("nonfinite geometry attribute " + name);
            }
          }
        }
      } catch (error) {
        messages.push({ activityId: activity.id, locale, problem: String(error.message) });
      }
    }
  }
  return {
    status: messages.length ? "fail" : "semantic_render_pass",
    activitiesWithVisuals: examined,
    localeChecks: examined * 3,
    issues: messages,
    pixelQualityVerified: false,
    academicAccuracyVerified: false,
    browserAccessibilityVerified: false,
  };
}

if (require.main === module) {
  const i = process.argv.indexOf("--package");
  const r = process.argv.indexOf("--repo-root");
  if (i < 0 || !process.argv[i + 1]) {
    console.error("usage: node scripts/audit_visual_rendering.js --package PACKAGE [--repo-root REPO]");
    process.exitCode = 2;
  } else {
    try {
      const file = path.resolve(process.argv[i + 1]);
      const root = r >= 0 ? path.resolve(process.argv[r + 1]) : path.resolve(__dirname, "..");
      const result = auditRenderedPackage(JSON.parse(fs.readFileSync(file, "utf8")), root);
      console.log(JSON.stringify(result, null, 2));
      if (result.status !== "semantic_render_pass") process.exitCode = 1;
    } catch (error) {
      console.error(String(error));
      process.exitCode = 1;
    }
  }
}
module.exports = { auditRenderedPackage };
