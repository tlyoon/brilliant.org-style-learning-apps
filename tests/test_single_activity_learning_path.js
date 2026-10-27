// Real app.js learner-path smoke using an isolated, non-browser DOM harness.
// Optional original-source candidate is read ONLY from a private absolute path.
// No original PDF, localized learner text or package bytes enter Git history.
"use strict";
const assert = require("node:assert/strict");
const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const ACTIVITY = "int-select-isolated-conditions";
const privateFile = process.env.BRILLIANT_PRIVATE_PACKAGE;
const privateSha = process.env.BRILLIANT_EXPECTED_SHA256;
const languages = ["en", "ms", "zh"];
const localized = (v) => Object.fromEntries(languages.map((lang) => [lang, v + "-" + lang]));
const fixture = {
  subchapter: "Private-free fixture",
  activities: [{
    id: ACTIVITY,
    type: "interactive", interactionMode: "selection",
    difficulty: "medium",
    prompt: localized("Select valid conditions"),
    feedback: localized("Net external impulse determines total momentum change"),
    hints: [localized("Check the impulse of external forces")],
    interaction: {
      items: [
        { id: "correct-one", label: localized("Internal forces cancel") },
        { id: "incorrect", label: localized("All forces must be small") },
        { id: "correct-two", label: localized("Net external impulse negligible") },
      ],
      correctSelections: ["correct-one", "correct-two"],
    },
  }],
};

function readPrivatePackage() {
  if (!privateFile && !privateSha) return fixture;
  assert(privateFile && privateSha, "private package path and SHA must be supplied together");
  assert(path.isAbsolute(privateFile), "private package must use absolute path");
  const absolute = path.resolve(privateFile);
  const repo = path.resolve(".");
  assert(!(absolute === repo || absolute.startsWith(repo + path.sep)),
    "private package must not live in public source checkout");
  const raw = fs.readFileSync(absolute);
  assert.equal(crypto.createHash("sha256").update(raw).digest("hex"), privateSha.toLowerCase(),
    "private package changed from expected exact version");
  const content = JSON.parse(raw.toString("utf8"));
  const selected = content.activities.filter((activity) => activity.id === ACTIVITY);
  assert.equal(selected.length, 1, "selected original-source activity missing or duplicated");
  return { subchapter: content.subchapter, activities: selected };
}

class FakeElement {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = {};
    this.listeners = {};
    this.className = "";
    this.disabled = false;
    this._text = "";
  }
  set innerHTML(_) { throw new Error("unsafe raw HTML"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((child) => child.textContent).join(""); }
  append(...children) { this.children.push(...children); }
  replaceChildren(...children) { this._text = ""; this.children = [...children]; }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
  }
  addEventListener(type, cb) { this.listeners[type] = cb; }
  focus() { this.focused = true; }
  click() { if (!this.disabled) this.listeners.click?.({ target: this }); }
}
function flatten(node) { return [node, ...node.children.flatMap(flatten)]; }
function find(root, fn) { return flatten(root).find(fn); }
function all(root, fn) { return flatten(root).filter(fn); }
function byId(root, id) { return find(root, (node) => node.id === id); }
function choice(app, id) {
  return find(app, (node) => node.tagName === "BUTTON" && node.dataset?.value === id);
}
function feedback(app) { return all(app, (node) => node.className === "feedback"); }

async function runLocale(data, lang) {
  const activity = data.activities[0];
  assert.equal(activity.type, "interactive");
  assert.equal(activity.interactionMode, "selection");
  assert(activity.interaction.items.length >= 2);
  const answerIds = activity.interaction.correctSelections;
  const candidates = activity.interaction.items.map((item) => item.id);
  const wrong = candidates.find((id) => !answerIds.includes(id));
  assert(wrong, "activity requires at least one explicit incorrect option");
  assert(answerIds.length > 0 && answerIds.every((id) => candidates.includes(id)));
  for (const obj of [activity.prompt, activity.feedback, activity.hints?.[0],
    ...activity.interaction.items.map((item) => item.label)]) {
    assert.equal(typeof obj?.[lang], "string");
    assert(obj[lang].trim(), "localized learner text missing");
  }
  const app = new FakeElement("section");
  app.dataset.packageUrl = "private-path-not-fetched";
  const locale = new FakeElement("select");
  const context = {
    console,
    document: {
      createElement: (tag) => new FakeElement(tag),
      querySelector: (selector) => selector === "#app" ? app : locale,
      querySelectorAll: (selector) =>
        selector === "#app .choices button" ?
          all(app, (node) => node.className === "choice") : [],
    },
    fetch: async () => ({ ok: true, json: async () => data }),
  };
  vm.runInNewContext(fs.readFileSync("app/app.js", "utf8"), context,
    { filename: "app/app.js" });
  await new Promise((resolve) => setImmediate(resolve));
  locale.value = lang;
  locale.listeners.change({ target: locale });
  assert.equal(find(app, (node) => node.className === "question").textContent,
    activity.prompt[lang], "locale-specific question did not render");
  assert.equal(byId(app, "check").disabled, true);

  byId(app, "hint").click();
  assert(feedback(app).some((node) => node.textContent === activity.hints[0][lang]),
    "locale hint absent");

  choice(app, wrong).click();
  assert.equal(choice(app, wrong).attributes["aria-pressed"], "true");
  assert(choice(app, wrong).focused, "keyboard focus not restored");
  assert.equal(byId(app, "check").disabled, false);
  byId(app, "check").click();
  const wrongMessage = feedback(app).at(-1).textContent;
  assert(wrongMessage.includes(activity.feedback[lang]), "wrong answer feedback missing");
  assert.equal(byId(app, "check").disabled, false);
  byId(app, "check").click();
  assert.equal(byId(app, "check").disabled, true, "try again did not reset response");

  for (const id of answerIds) {
    choice(app, id).click();
    assert.equal(choice(app, id).attributes["aria-pressed"], "true");
  }
  byId(app, "check").click();
  const correctMessage = feedback(app).at(-1).textContent;
  assert(correctMessage.includes(activity.feedback[lang]), "correct feedback missing");
  assert.notEqual(wrongMessage, correctMessage,
    "wrong and correct answer must have different encouragement");
  byId(app, "check").click();
  assert(byId(app, "restart"), "completion screen not reached");
  assert(find(app, (node) => node.tagName === "H1").textContent.trim(),
    "completion text missing");
}

(async () => {
  const data = readPrivatePackage();
  for (const lang of languages) await runLocale(data, lang);
  console.log(JSON.stringify({
    selectedActivity: ACTIVITY,
    privateOriginalPackage: Boolean(privateFile),
    validatedLocales: languages,
    simulatedStages: ["wrong", "hint", "retry", "correct", "complete"],
    academicQA: "REVIEW_REQUIRED",
    publicationAuthorized: false,
  }));
})().catch((error) => {
  // Error names and generic messages are safe; never print private learner text.
  console.error("Learner path blocked:", error.name);
  process.exitCode = 1;
});