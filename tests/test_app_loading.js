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

  set innerHTML(_value) {
    throw new Error("innerHTML must not be used by the learner application");
  }

  set textContent(value) {
    this._text = String(value);
    this.children = [];
  }

  get textContent() {
    return this._text + this.children.map((child) => child.textContent).join("");
  }

  append(...children) {
    this.children.push(...children);
  }

  replaceChildren(...children) {
    this._text = "";
    this.children = [...children];
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
  }

  addEventListener(name, listener) {
    this.listeners[name] = listener;
  }
}

function descendants(root) {
  return [root, ...root.children.flatMap(descendants)];
}

function packageNamed(name) {
  const localized = (suffix) => ({ en: `${name} en ${suffix}`, ms: `${name} ms ${suffix}`, zh: `${name} zh ${suffix}` });
  return {
    subchapter: name,
    activities: [{
      difficulty: "easy",
      prompt: localized("prompt"),
      answerKey: { correct: "a", options: [{ id: "a", label: localized("option") }] },
      hints: [localized("hint")],
      feedback: localized("feedback"),
    }],
  };
}

function flush() {
  return new Promise((resolve) => setImmediate(resolve));
}

(async () => {
  const app = new FakeElement("section");
  const locale = new FakeElement("select");
  const requests = new Map();
  const context = {
    console,
    document: {
      createElement: (tagName) => new FakeElement(tagName),
      querySelector: (selector) => selector === "#app" ? app : locale,
    },
    fetch: (url) => new Promise((resolve) => requests.set(url, resolve)),
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync("app/app.js", "utf8"), context, { filename: "app/app.js" });

  assert.equal(locale.disabled, true);
  assert.doesNotThrow(() => locale.listeners.change({ target: { value: "ms" } }));
  assert.doesNotThrow(() => locale.listeners.change({ target: { value: "zh" } }));
  assert.equal(app.children.length, 0);

  vm.runInContext('loadPackage("older.json")', context);
  vm.runInContext('loadPackage("newer.json")', context);
  requests.get("newer.json")({ ok: true, json: async () => packageNamed("newer") });
  await flush();
  await flush();

  assert.equal(locale.disabled, false);
  const heading = descendants(app).find((node) => node.tagName === "H1");
  assert.equal(heading.textContent, "newer zh prompt");

  requests.get("older.json")({ ok: true, json: async () => packageNamed("older") });
  requests.get("../content/chapter-1/section-1-1/package.json")({ ok: true, json: async () => packageNamed("initial") });
  await flush();
  await flush();

  const finalHeading = descendants(app).find((node) => node.tagName === "H1");
  assert.equal(finalHeading.textContent, "newer zh prompt");
  assert.equal(locale.disabled, false);
  console.log("Locale changes and out-of-order package loads are race-safe.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
