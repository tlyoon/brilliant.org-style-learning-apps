const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
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
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === "id") this.id = String(value); }
  addEventListener(name, listener) { this.listeners[name] = listener; }
  click() { if (!this.disabled) this.listeners.click?.({ target: this }); }
}

const localized = (text) => ({ en: text, ms: text, zh: text });
const mcq = (id) => ({
  id,
  type: "mcq",
  difficulty: "easy",
  prompt: localized(`${id} prompt`),
  answerKey: { correct: "yes", options: [{ id: "yes", label: localized(`${id} yes`) }] },
  hints: [localized("hint")],
  feedback: localized("feedback"),
});
const interactive = {
  id: "interactive-two",
  type: "interactive",
  difficulty: "moderate",
  interactionMode: "selection",
  prompt: localized("interactive-two prompt"),
  interaction: {
    items: [{ id: "keep", label: localized("KEEP") }, { id: "leave", label: localized("LEAVE") }],
    correctSelections: ["keep"],
  },
  hints: [localized("hint")],
  feedback: localized("feedback"),
};
const packageData = { subchapter: "Deep links", activities: [mcq("first"), interactive, mcq("third")] };
const descendants = (root) => [root, ...root.children.flatMap(descendants)];
const find = (root, predicate) => descendants(root).find(predicate);

const app = new FakeElement("section");
app.dataset.packageUrl = "package.json";
const locale = new FakeElement("select");
const popstateListeners = [];
const replacements = [];
const fakeWindow = {
  location: { href: "https://example.test/section-9-5/?foo=keep&activity=interactive-two#frag" },
  history: {
    replaceState(_state, _title, next) {
      replacements.push(next);
      fakeWindow.location.href = new URL(next, fakeWindow.location.href).href;
    },
  },
  addEventListener(name, listener) { if (name === "popstate") popstateListeners.push(listener); },
};
const context = {
  console,
  URL,
  window: fakeWindow,
  document: {
    createElement: (tagName) => new FakeElement(tagName),
    querySelector: (selector) => selector === "#app" ? app : locale,
  },
  fetch: async () => ({ ok: true, json: async () => packageData }),
};
vm.runInNewContext(fs.readFileSync("app/app.js", "utf8"), context, { filename: "app/app.js" });

setImmediate(() => {
  assert.equal(find(app, (node) => node.tagName === "H1").textContent, "interactive-two prompt");
  let current = new URL(fakeWindow.location.href);
  assert.equal(current.searchParams.get("activity"), "interactive-two");
  assert.equal(current.searchParams.get("foo"), "keep");
  assert.equal(current.hash, "#frag");

  find(app, (node) => node.tagName === "BUTTON" && node.textContent === "KEEP").click();
  find(app, (node) => node.id === "check").click();
  find(app, (node) => node.id === "check").click();
  assert.equal(find(app, (node) => node.tagName === "H1").textContent, "third prompt");
  current = new URL(fakeWindow.location.href);
  assert.equal(current.searchParams.get("activity"), "third");

  fakeWindow.location.href = "https://example.test/section-9-5/?activity=first";
  popstateListeners[0]();
  assert.equal(find(app, (node) => node.tagName === "H1").textContent, "first prompt");

  fakeWindow.location.href = "https://example.test/section-9-5/?activity=does-not-exist";
  popstateListeners[0]();
  assert.equal(find(app, (node) => node.tagName === "H1").textContent, "first prompt");
  assert.equal(new URL(fakeWindow.location.href).searchParams.get("activity"), "first");
  assert.ok(replacements.length >= 4);
  console.log("Activity deep links select, update, preserve URL state, and recover safely.");
});
