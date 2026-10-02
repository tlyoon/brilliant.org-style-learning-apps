const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeElement {
  constructor(tagName) {
    this.tagName = String(tagName).toUpperCase();
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = {};
    this.listeners = {};
    this.className = "";
    this.disabled = false;
    this._text = "";
  }
  set innerHTML(_value) { throw new Error("innerHTML must not be used"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((child) => child.textContent).join(""); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ""; this.children = [...children]; }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "class") this.className = String(value);
    if (name === "id") this.id = String(value);
  }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  click() { if (!this.disabled) this.listeners.click?.({ target: this }); }
}
function descendants(root) { return [root, ...root.children.flatMap(descendants)]; }
function find(root, predicate) { return descendants(root).find(predicate); }
const localized = (text) => ({ en: text, ms: text, zh: text });

const app = new FakeElement("section");
app.dataset.packageUrl = "visual-package.json";
const locale = new FakeElement("select");
const packageData = {
  subchapter: "Visual integration",
  activities: [{
    id: "visual-question",
    type: "mcq",
    difficulty: "easy",
    prompt: localized("Which cart is moving to the right?"),
    answerKey: {
      correct: "a",
      options: [
        { id: "a", label: localized("Cart A") },
        { id: "b", label: localized("Cart B") },
      ],
    },
    hints: [localized("Inspect the arrow directions.")],
    feedback: localized("The right-pointing velocity vector identifies the motion."),
    visualSpec: {
      schemaVersion: "1.0",
      mode: "scene_diagram",
      template: "mechanics.cart_collision_1d",
      semanticParameters: { phase: "before", track_orientation: "horizontal" },
      entities: [
        { id: "cart-a", kind: "cart", label: localized("Cart A") },
        { id: "cart-b", kind: "cart", label: localized("Cart B") },
      ],
      vectors: [
        { id: "va", entityId: "cart-a", quantity: "velocity", direction: "right", relativeMagnitude: 0.8, label: localized("vA") },
        { id: "vb", entityId: "cart-b", quantity: "velocity", direction: "left", relativeMagnitude: 0.8, label: localized("vB") },
      ],
      accessibility: { description: localized("Two carts with opposing velocity arrows."), colorIndependent: true, reducedMotionStrategy: "not-applicable" },
      grounding: [],
      fallback: { mode: "structured_interaction", reason: "Text fallback" },
      validation: { answerRelevantIds: ["cart-a", "cart-b"], forbidAnswerLeakage: true },
    },
  }],
};
const document = {
  createElement: (tag) => new FakeElement(tag),
  createElementNS: (_namespace, tag) => new FakeElement(tag),
  querySelector: (selector) => selector === "#app" ? app : locale,
};
const context = {
  console,
  document,
  fetch: async () => ({ ok: true, json: async () => packageData }),
  globalThis: null,
};
context.globalThis = context;
vm.runInNewContext(fs.readFileSync("app/visual-renderers.js", "utf8"), context, { filename: "app/visual-renderers.js" });
vm.runInNewContext(fs.readFileSync("app/app.js", "utf8"), context, { filename: "app/app.js" });

setImmediate(() => {
  const card = find(app, (node) => node.tagName === "SECTION" && node.className === "card");
  const visual = find(card, (node) => node.tagName === "FIGURE" && node.className.includes("physics-visual"));
  const choices = find(card, (node) => node.className === "choices");
  assert.ok(visual, "visualSpec should be rendered by the trusted visual runtime");
  assert.equal(visual.attributes["aria-label"], "Two carts with opposing velocity arrows.");
  assert.ok(choices, "answer controls should still render");
  assert.ok(card.children.indexOf(visual) < card.children.indexOf(choices), "visual should appear before answer controls");
  assert.ok(find(visual, (node) => node.attributes["data-semantic-id"] === "va"));
  assert.equal(find(app, (node) => node.className === "question").textContent, "Which cart is moving to the right?");
  console.log("Player renders deterministic visual content before the response controls without changing question flow.");
});
