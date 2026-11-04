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
const rendererSource = fs.readFileSync("domains/university-level physics/visuals/physics-renderers.js", "utf8");
assert.equal(rendererSource.includes("innerHTML"), false, "renderer must not use innerHTML");
vm.runInNewContext(rendererSource, context, { filename: "physics-renderers.js" });
vm.runInNewContext(fs.readFileSync("app/visual-renderers.js", "utf8"), context, { filename: "app/visual-renderers.js" });
const visuals = context.LearningVisuals;
assert.ok(visuals);
assert.equal(visuals.rendererVersion, "1.0.0");
assert.deepEqual(Array.from(visuals.supportedTemplates), [
  "mechanics.cart_collision_1d",
  "mechanics.free_body_2d",
  "graph.cartesian_qualitative",
  "state.energy_bar",
  "mechanics.motion_1d_slider",
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

// A section's phase is learner-facing text: never leave it English-only
// when the student explicitly selected Malay or Chinese.
for (const [locale, expected] of [
  ["en", "Before"], ["ms", "Sebelum pelanggaran"],
  ["zh", "\u78b0\u649e\u524d"],
]) {
  const figure = visuals.renderVisualSpec(cartSpec, { locale, document });
  const phase = descendants(figure).find((n) =>
    n.tagName === "TEXT" && n.attributes.class === "physics-visual__phase");
  assert.equal(phase.textContent, expected, "phase must be localized");
}
for (const [phaseName, expected] of [
  ["after", "Selepas pelanggaran"], ["during", "Semasa pelanggaran"],
]) {
  const figure = visuals.renderVisualSpec({
    ...cartSpec, semanticParameters: {...cartSpec.semanticParameters, phase:phaseName},
  }, { locale:"ms", document });
  const caption = descendants(figure).find((n) =>
    n.tagName === "TEXT" && n.attributes.class === "physics-visual__phase");
  assert.equal(caption.textContent, expected);
}
assert.ok(texts(cart).includes("vA"));

// Regression: opposing arrows must not place long labels at converging tips.
const longLabels = {
  en: ["Initial velocity v1i", "Initial velocity v2i"],
  ms: ["Halaju permulaan v1i", "Halaju permulaan v2i"],
  zh: ["\u521d\u59cb\u901f\u5ea6\u65b9\u5411v1i", "\u521d\u59cb\u901f\u5ea6\u65b9\u5411v2i"],
};
const weightedUnits = (txt) => Array.from(txt).reduce(
  (sum, c) => sum + (c.codePointAt(0) >= 0x2e80 ? 2 : 1), 0);
for (const locale of ["en", "ms", "zh"]) {
  const labelSpec = {
    ...cartSpec,
    vectors: cartSpec.vectors.map((v, i) => ({
      ...v, label: { en: longLabels.en[i], ms: longLabels.ms[i], zh: longLabels.zh[i] },
    })),
  };
  const figure = visuals.renderVisualSpec(labelSpec, { locale, document });
  const labels = descendants(figure).filter((n) => n.tagName === "TEXT"
    && n.attributes["data-vector-label-for"]);
  assert.equal(labels.length, 2);
  assert.deepEqual(labels.map((n) => Number(n.attributes.x)), [150, 490]);
  assert.ok(labels.every((n) => Number(n.attributes.y) === 108));
  assert.ok(labels.every((n) => n.children.every(
    (line) => weightedUnits(line.textContent) <= 27)));
  assert.deepEqual(labels.map((n) => n.textContent), longLabels[locale]);
  assert.ok(Number(labels[1].attributes.x) - Number(labels[0].attributes.x) >= 27 * 8);
}
const fourCartSpec = {
  ...cartSpec,
  entities: [0, 1, 2, 3].map((i) => ({
    id: "cart-" + i, kind: "cart", label: localized("Cart " + i),
  })),
  vectors: [0, 1, 2, 3].map((i) => ({
    id: "speed-" + i, entityId: "cart-" + i, quantity: "velocity",
    direction: i % 2 === 0 ? "right" : "left",
    relativeMagnitude: 0.7,
    label: localized("A deliberately long approach velocity label"),
  })),
};
const fourFigure = visuals.renderVisualSpec(fourCartSpec, { locale: "en", document });
const fourLabels = descendants(fourFigure).filter((n) => n.tagName === "TEXT"
  && n.attributes["data-vector-label-for"]);
assert.equal(fourLabels.length, 4);
assert.deepEqual(fourLabels.map((n) => Number(n.attributes.y)), [65, 110, 65, 110]);
assert.ok(fourLabels.every((n) => n.children.every(
  (line) => weightedUnits(line.textContent) <= 20)));
assert.ok(fourLabels.every((n) => n.textContent ===
  "A deliberately long approach velocity label"));

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

// The original spring-energy screenshot lacked complete English/Malay labels
// because the capture was viewport-cropped; full capture exposed the actual
// overlap. Assert source label identity and bounded wrapped lines in all 3.
const energyWords = {
  en: ["Kinetic energy", "Elastic potential energy"],
  ms: ["Tenaga kinetik", "Tenaga keupayaan kenyal"],
  zh: ["\u52a8\u80fd", "\u5f39\u6027\u52bf\u80fd"],
};
for (const locale of ["en", "ms", "zh"]) {
  const spec = {...energySpec,
    entities: energySpec.entities.map((e, i) => ({
      ...e, label:{en:energyWords.en[i],ms:energyWords.ms[i],zh:energyWords.zh[i]},
    })),
  };
  const rendered = visuals.renderVisualSpec(spec, {locale,document});
  const labels = descendants(rendered).filter(n =>
    n.tagName === "TEXT" && n.className === "physics-visual__energy-label");
  assert.equal(labels.length,2);
  assert.deepEqual(labels.map(n => n.attributes["data-full-label"]),energyWords[locale]);
  assert.ok(labels.every(n => n.children.length <= 3));
  assert.ok(labels.every(n => n.children.every(
    line => weightedUnits(line.textContent) <= 10)));
  assert.ok(labels.every(n => Number(n.attributes.y) === 318));
  assert.ok(labels.every(n => n.children.reduce(
    (height, item) => height + Number(item.attributes.dy), 318) <= 350));
}

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
