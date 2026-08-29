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
const item = (id, label = id.toUpperCase()) => ({ id, label: localized(label) });
const target = (id, label = id.toUpperCase()) => ({ id, label: localized(label) });
const base = (id, mode, interaction) => ({
  id,
  type: "interactive",
  difficulty: "easy",
  interactionMode: mode,
  prompt: localized(id),
  interaction,
  hints: [localized("hint")],
  feedback: localized("feedback"),
});

const packageData = {
  subchapter: "Interaction test",
  activities: [
    base("classification", "classification", {
      items: [item("one"), item("two"), item("three")],
      targets: [target("left"), target("right")],
      placements: [
        { itemId: "one", targetId: "left" },
        { itemId: "two", targetId: "right" },
        { itemId: "three", targetId: "left" },
      ],
    }),
    base("matching", "matching", {
      items: [item("red"), item("green"), item("blue")],
      targets: [target("r"), target("g"), target("b")],
      placements: [
        { itemId: "red", targetId: "r" },
        { itemId: "green", targetId: "g" },
        { itemId: "blue", targetId: "b" },
      ],
    }),
    base("ordering", "ordering", {
      items: [item("a"), item("b"), item("c")],
      correctOrder: ["a", "b", "c"],
    }),
    base("selection", "selection", {
      items: [item("keep-one"), item("leave"), item("keep-two")],
      correctSelections: ["keep-one", "keep-two"],
    }),
  ],
};

function descendants(root) { return [root, ...root.children.flatMap(descendants)]; }
function find(root, predicate) { return descendants(root).find(predicate); }
function findAll(root, predicate) { return descendants(root).filter(predicate); }
function checkAndAdvance(app) {
  const check = find(app, (node) => node.id === "check");
  assert.equal(check.disabled, false);
  check.click();
  assert.match(findAll(app, (node) => node.className === "feedback").at(-1).textContent, /That reasoning fits/);
  find(app, (node) => node.id === "check").click();
}
function choosePlacements(app, targetLabels) {
  const groups = findAll(app, (node) => node.className === "interaction-group");
  assert.equal(groups.length, targetLabels.length);
  groups.forEach((group, index) => {
    find(group, (node) => node.tagName === "BUTTON" && node.textContent === targetLabels[index]).click();
  });
}
function moveDown(app, itemLabel) {
  const row = find(app, (node) => node.className === "order-row" && node.textContent.includes(itemLabel));
  const controls = find(row, (node) => node.className === "order-controls");
  controls.children[1].click();
}

const app = new FakeElement("section");
app.dataset.packageUrl = "interaction-test.json";
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
  choosePlacements(app, ["LEFT", "RIGHT", "LEFT"]);
  checkAndAdvance(app);

  choosePlacements(app, ["R", "G", "B"]);
  checkAndAdvance(app);

  moveDown(app, "C");
  moveDown(app, "C");
  moveDown(app, "B");
  checkAndAdvance(app);

  find(app, (node) => node.tagName === "BUTTON" && node.textContent === "KEEP-ONE").click();
  find(app, (node) => node.tagName === "BUTTON" && node.textContent === "KEEP-TWO").click();
  checkAndAdvance(app);

  assert.equal(find(app, (node) => node.tagName === "H1").textContent, "Journey complete");
  console.log("All interaction modes render, accept keyboard-native button input, and score correctly.");
});
