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
const mcq = (id, prompt) => ({
  id,
  type: "mcq",
  difficulty: "easy",
  prompt: localized(prompt),
  answerKey: {
    correct: "yes",
    options: [
      { id: "yes", label: localized("Yes") },
      { id: "no", label: localized("No") },
    ],
  },
  hints: [localized("Hint")],
  feedback: localized("Feedback"),
});

const packageData = {
  subchapter: "Controls test",
  activities: [mcq("first", "First question"), mcq("second", "Second question")],
};

function descendants(root) { return [root, ...root.children.flatMap(descendants)]; }
function find(root, predicate) { return descendants(root).find(predicate); }

const app = new FakeElement("section");
app.dataset.packageUrl = "controls-test.json";
const locale = new FakeElement("select");
const context = {
  console,
  document: {
    createElement: (tagName) => new FakeElement(tagName),
    querySelector: (selector) => selector === "#app" ? app : locale,
  },
  fetch: async () => ({ ok: true, json: async () => packageData }),
};
vm.runInNewContext(fs.readFileSync("app/app.js", "utf8"), context, { filename: "app/app.js" });

setImmediate(() => {
  const question = find(app, (node) => node.className === "question");
  assert.equal(question.textContent, "First question");

  const actionRow = find(app, (node) => node.className === "action-row");
  assert.ok(actionRow, "check and hint controls should share one horizontal action row");
  assert.deepEqual(actionRow.children.map((node) => node.id), ["check", "hint"]);
  assert.equal(actionRow.children[0].disabled, true, "check remains disabled until a response exists");

  const skip = find(app, (node) => node.id === "skip");
  assert.ok(skip, "skip control should be present");
  assert.equal(skip.disabled, false);
  skip.click();

  assert.equal(find(app, (node) => node.className === "question").textContent, "Second question");
  assert.equal(find(app, (node) => node.id === "check").disabled, true);

  find(app, (node) => node.id === "skip").click();
  assert.equal(find(app, (node) => node.tagName === "H1").textContent, "Journey complete");
  console.log("Player controls allow unanswered skips and keep check/hint in a shared action row.");
});
