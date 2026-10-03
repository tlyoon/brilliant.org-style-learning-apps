const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.attributes = {};
    this.listeners = {};
    this.className = "";
    this.value = "";
    this._text = "";
  }
  set innerHTML(_value) { throw new Error("innerHTML must not be used"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((child) => child.textContent).join(""); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ""; this.children = [...children]; }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === "class") this.className = String(value); }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  dispatch(name) { this.listeners[name]?.({ target: this }); }
}
function descendants(root) { return [root, ...root.children.flatMap(descendants)]; }
function find(root, predicate) { return descendants(root).find(predicate); }
const localized = (text) => ({ en: text, ms: text, zh: text });
const document = {
  createElement: (tag) => new FakeElement(tag),
  createElementNS: (_namespace, tag) => new FakeElement(tag),
};
const context = { console, document, globalThis: null };
context.globalThis = context;
vm.runInNewContext(fs.readFileSync("app/visual-renderers.js", "utf8"), context, { filename: "app/visual-renderers.js" });
const visuals = context.PhysicsVisuals;

const spec = {
  schemaVersion: "1.0",
  mode: "parameter_simulation",
  template: "mechanics.motion_1d_slider",
  semanticParameters: { motion_model: "constant-velocity" },
  entities: [{ id: "cart-a", kind: "cart", label: localized("Cart A") }],
  controls: [
    { id: "velocity-control", kind: "slider", variableId: "velocity", label: localized("Velocity"), min: -4, max: 4, default: 2, step: 1, unit: "m/s" },
    { id: "time-control", kind: "slider", variableId: "time", label: localized("Time"), min: 0, max: 5, default: 0, step: 1, unit: "s" },
  ],
  states: [{ id: "initial-state", values: { position: 0, velocity: 2, time: 0 } }],
  invariants: [{ id: "constant-velocity", kind: "constant", references: ["motion"], description: localized("Velocity remains constant.") }],
  simulation: { id: "motion", modelId: "kinematics.motion_1d", variableIds: ["position", "velocity", "time"], invariantIds: ["constant-velocity"] },
  accessibility: { description: localized("One-dimensional constant-velocity cart motion."), colorIndependent: true, reducedMotionStrategy: "instant-state" },
  grounding: [{ factId: "fact-motion", origin: "source_fact", appliesTo: ["cart-a"] }],
  fallback: { mode: "scene_diagram", template: "mechanics.cart_collision_1d", reason: "Use the initial state as a static diagram." },
  validation: { answerRelevantIds: ["cart-a"], forbidAnswerLeakage: true },
};

assert.deepEqual(Object.fromEntries(Object.entries(visuals.evaluateMotion1D(1, 3, 2))), { position: 7, velocity: 3, time: 2 });
assert.throws(() => visuals.evaluateMotion1D(0, Infinity, 1));

const figure = visuals.renderVisualSpec(spec, { locale: "en", document });
assert.equal(figure.attributes["data-simulation-model"], "kinematics.motion_1d");
assert.equal(figure.attributes["data-position"], "0.000000");
const velocity = find(figure, (node) => node.tagName === "INPUT" && node.attributes["aria-label"] === "Velocity");
const time = find(figure, (node) => node.tagName === "INPUT" && node.attributes["aria-label"] === "Time");
assert.ok(velocity && time, "both bounded sliders should render");
velocity.value = "-3";
velocity.dispatch("input");
time.value = "2";
time.dispatch("input");
assert.equal(figure.attributes["data-position"], "-6.000000");
assert.equal(figure.attributes["data-velocity"], "-3.000000");
assert.equal(figure.attributes["data-time"], "2.000000");
assert.ok(find(figure, (node) => node.attributes["data-semantic-id"] === "cart-a"));

const staticFallback = visuals.renderVisualSpec(spec, { locale: "en", document, forceStatic: true });
assert.equal(staticFallback.attributes["data-simulation-fallback"], "static");
assert.equal(descendants(staticFallback).some((node) => node.tagName === "INPUT"), false);
assert.ok(find(staticFallback, (node) => node.attributes["data-semantic-id"] === "cart-a"));

console.log("Bounded one-dimensional motion simulation updates deterministically and provides a static fallback.");
