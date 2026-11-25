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
      id: "activity-" + name,
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
  app.dataset.packageUrl = "initial.json";
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
  assert.match(app.textContent, /Loading selected learning package/,
    "initial standalone load must show an inert pending state");
  assert.equal(descendants(app).some((node) => node.tagName === "H1"), false);

  vm.runInContext('loadPackage("older.json")', context);
  vm.runInContext('loadPackage("newer.json")', context);
  requests.get("newer.json")({ ok: true, json: async () => packageNamed("newer") });
  await flush();
  await flush();

  assert.equal(locale.disabled, false);
  const heading = descendants(app).find((node) => node.tagName === "H1");
  assert.equal(heading.textContent, "newer zh prompt");

  requests.get("older.json")({ ok: true, json: async () => packageNamed("older") });
  requests.get("initial.json")({ ok: true, json: async () => packageNamed("initial") });
  await flush();
  await flush();

  const finalHeading = descendants(app).find((node) => node.tagName === "H1");
  assert.equal(finalHeading.textContent, "newer zh prompt");
  assert.equal(locale.disabled, false);

  // A loaded package is a trust boundary: duplicate IDs alias the same
  // anonymous completion/misconception counters across two activities.
  const duplicate = packageNamed("duplicate");
  duplicate.activities.push({ ...duplicate.activities[0] });
  vm.runInContext('loadPackage("duplicate.json")', context);
  requests.get("duplicate.json")({ ok: true, json: async () => duplicate });
  await flush();
  await flush();
  assert.match(app.textContent, /Invalid learning package activity identifiers/, "duplicate activity IDs must fail closed before any learner activity renders");
  assert.equal(vm.runInContext("state.package === null", context), true);
  assert.equal(vm.runInContext("Object.keys(state.sessionMetrics).length", context), 0);

  const missing = packageNamed("missing");
  delete missing.activities[0].id;
  vm.runInContext('loadPackage("missing.json")', context);
  requests.get("missing.json")({ ok: true, json: async () => missing });
  await flush();
  await flush();
  assert.match(app.textContent, /Invalid learning package activity identifiers/, "missing activity IDs must fail closed, not share the undefined evidence key");

  const recovered = packageNamed("recovered");
  vm.runInContext('loadPackage("recovered.json")', context);
  requests.get("recovered.json")({ ok: true, json: async () => recovered });
  await flush();
  await flush();
  assert.equal(descendants(app).find((node) => node.tagName === "H1").textContent,
    "recovered zh prompt", "a valid fresh package should recover after invalid input");

  // Direct loadPackage() is a supported host API as well as the instructor
  // preview path. A pending replacement must not expose stale answer controls
  // or old session mastery while the new package fetch is unresolved.
  vm.runInContext("state.sessionMetrics['activity-recovered'] = {checks:1,wrong:1}", context);
  vm.runInContext('loadPackage("pending.json")', context);
  assert.equal(vm.runInContext("state.package === null", context), true, "pending direct package replacement must invalidate the previous package immediately");
  assert.equal(vm.runInContext("Object.keys(state.sessionMetrics).length", context), 0,
    "pending direct package replacement must clear prior anonymous evidence");
  assert.equal(descendants(app).some((node) => node.tagName === "H1"), false, "pending direct package replacement must hide stale learner questions");
  assert.match(app.textContent, /Loading selected learning package/,
    "direct package replacement should render an inert pending placeholder");
  requests.get("pending.json")({ ok: true, json: async () => packageNamed("pending") });
  await flush();
  await flush();
  assert.equal(descendants(app).find((node) => node.tagName === "H1").textContent,
    "pending zh prompt", "fresh package must become usable after load completes");
  console.log("Locale, race ordering and fail-closed package session boundaries passed.");
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
