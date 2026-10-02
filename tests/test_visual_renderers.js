const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.attributes = {};
    this.className = "";
    this._text = "";
  }
  set innerHTML(_value) { throw new Error("innerHTML must not be used by visual renderers"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((child) => child.textContent).join(""); }
  append(...children) { this.children.push(...children); }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "class") this.className = String(value);
  }
}

function descendants(root) { return [root, ...root.children.flatMap(descendants)]; }
function bySemantic(root, id) { return descendants(root).find((node) => node.attributes["data-semantic-id"] === id); }
function texts(root) { return descendants(root).filter((node) => node.tagName === "TEXT").map((node) => node.textContent); }
const localized = (text) => ({ en: text, ms: `MS ${text}`, zh: `ZH ${text}` });

const document = {
  createElement: (tag) => new FakeElement(tag),
  createElementNS: (_namespace, tag) => new FakeElement(tag),
};
const context = { console, document, globalThis: null };
context.globalThis = context;
const rendererSource = fs.readFileSync("app/visual-renderers.js", "utf8");
assert.equal(rendererSource.includes("innerHTML"), false, "renderer must not use innerHTML");
vm.runInNewContext(rendererSource, context, { filename: "app/visual-renderers.js" });
const visuals = context.PhysicsVisuals;
assert.ok(visuals);
assert.equal(visuals.rendererVersion, "1.0.0");
assert.deepEqual(Array.from(visuals.supportedTemplates), [
  "mechanics.cart_collision_1d",
  "mechanics.free_body_2d",
  "graph.cartesian_qualitative",
  "state.energy_bar",
]);

const common = (mode, template, description) => ({
  schemaVersion: "1.0", mode, template,
  accessibility: { description: localized(description), colorIndependent: true, reducedMotionStrategy: "not-applicable" },
  grounding: [{ factId: "fact-a", origin: "source_fact", appliesTo: ["subject"] }],
  fallback: { mode: "structured_interaction", reason: "Fallback" },
  validation: { answerRelevantIds: ["subject"], forbidAnswerLeakage: true },
});

const cartSpec = {
  ...common("scene_diagram", "mechanics.cart_collision_1d", "Two carts moving toward each other."),
  semanticParameters: { phase: "before", track_orientation: "horizontal" },
  entities: [
    { id: "cart-a", kind: "cart", label: localized("Cart A") },
    { id: "cart-b", kind: "cart", label: localized("Cart B") },
  ],
  vectors: [
    { id: "velocity-a", entityId: "cart-a", quantity: "velocity", direction: "right", relativeMagnitude: 0.8, label: localized("vA") },
    { id: "velocity-b", entityId: "cart-b", quantity: "velocity", direction: "left", relativeMagnitude: 0.6, label: localized("vB") },
  ],
};
const cart = visuals.renderVisualSpec(cartSpec, { locale: "en", document });
assert.equal(cart.tagName, "FIGURE");
assert.equal(cart.attributes["data-template"], "mechanics.cart_collision_1d");
assert.ok(bySemantic(cart, "cart-a"));
assert.ok(bySemantic(cart, "cart-b"));
assert.ok(bySemantic(cart, "velocity-a"));
assert.ok(texts(cart).includes("Cart A"));
assert.ok(texts(cart).includes("vA"));

const freeBodySpec = {
  ...common("vector_diagram", "mechanics.free_body_2d", "A body with force vectors."),
  semanticParameters: { reference_frame: "cartesian" },
  entities: [{ id: "body", kind: "body", label: localized("Block") }],
  vectors: [
    { id: "weight", entityId: "body", quantity: "weight", direction: "down", relativeMagnitude: 0.8, label: localized("W") },
    { id: "normal", entityId: "body", quantity: "normal-force", direction: "up", relativeMagnitude: 0.8, label: localized("N") },
  ],
};
const freeBody = visuals.renderVisualSpec(freeBodySpec, { locale: "en", document });
assert.ok(bySemantic(freeBody, "body"));
assert.ok(bySemantic(freeBody, "weight"));
assert.ok(texts(freeBody).includes("Block"));
assert.ok(texts(freeBody).includes("W"));

const graphSpec = {
  ...common("graph_plot", "graph.cartesian_qualitative", "A qualitative velocity-time graph."),
  axes: [
    { id: "time-axis", role: "x", quantity: "time", label: localized("Time"), unit: "s", scale: "qualitative" },
    { id: "velocity-axis", role: "y", quantity: "velocity", label: localized("Velocity"), unit: "m/s", scale: "qualitative" },
  ],
  graphSeries: [
    { id: "velocity-series", xAxisId: "time-axis", yAxisId: "velocity-axis", shape: "increasing-linear", features: ["positive-slope"], label: localized("Velocity") },
  ],
};
const graph = visuals.renderVisualSpec(graphSpec, { locale: "en", document });
const series = bySemantic(graph, "velocity-series");
assert.ok(series);
assert.equal(series.tagName, "PATH");
assert.ok(series.attributes.d.startsWith("M"));
assert.ok(texts(graph).some((text) => text.includes("Time")));
assert.ok(texts(graph).some((text) => text.includes("Velocity")));

const energySpec = {
  ...common("energy_bar", "state.energy_bar", "Kinetic and potential energy bars."),
  entities: [
    { id: "kinetic", kind: "energy-component", label: localized("Kinetic"), properties: { relativeAmount: 0.8 } },
    { id: "potential", kind: "energy-component", label: localized("Potential"), properties: { relativeAmount: 0.35 } },
  ],
};
const energy = visuals.renderVisualSpec(energySpec, { locale: "en", document });
const kinetic = bySemantic(energy, "kinetic");
const potential = bySemantic(energy, "potential");
assert.ok(Number(kinetic.attributes.height) > Number(potential.attributes.height));
assert.ok(texts(energy).includes("Kinetic"));

const contextArtwork = new FakeElement("img");
const hybrid = visuals.renderDeterministicOverlay(cartSpec, { locale: "en", document, baseLayer: contextArtwork });
const hybridNodes = descendants(hybrid);
const contextLayer = hybridNodes.find((node) => node.className === "physics-visual__context");
assert.ok(contextLayer);
assert.equal(contextLayer.attributes["aria-hidden"], "true");
assert.equal(contextLayer.children[0], contextArtwork);
assert.ok(bySemantic(hybrid, "cart-a"), "deterministic entities remain present over contextual art");

const unsafeLabelSpec = structuredClone(cartSpec);
unsafeLabelSpec.entities[0].label = localized("<script>not executable</script>");
const inert = visuals.renderVisualSpec(unsafeLabelSpec, { locale: "en", document });
assert.equal(descendants(inert).some((node) => node.tagName === "SCRIPT"), false);
assert.ok(texts(inert).includes("<script>not executable</script>"));

const unknown = visuals.renderVisualSpec({ ...cartSpec, template: "unknown.template" }, { locale: "en", document });
assert.ok(unknown.className.includes("physics-visual--fallback"));
assert.equal(unknown.attributes.role, "img");

console.log("Deterministic physics renderers produce safe, semantic SVG for all four trusted templates.");
