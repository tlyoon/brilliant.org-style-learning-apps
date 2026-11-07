"use strict";
// Exercises the real player and local preview selector with an inert DOM.
// No browser, student data, PDF, provider or public deployment is used.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const crypto = require("node:crypto");

class FakeElement {
  constructor(tag) {
    this.tagName = tag.toUpperCase();
    this.children = [];
    this.dataset = {};
    this.style = {};
    this.attributes = {};
    this.listeners = {};
    this.value = "";
    this.disabled = false;
    this._text = "";
  }
  set innerHTML(_value) { throw new Error("untrusted HTML injection"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map((x) => x.textContent).join(""); }
  append(...elements) { this.children.push(...elements); }
  replaceChildren(...elements) { this._text = ""; this.children = [...elements]; }
  addEventListener(type, callback) {
    const previous = this.listeners[type];
    this.listeners[type] = previous
      ? (...args) => { previous(...args); callback(...args); }
      : callback;
  }
  setAttribute(name, value) { this.attributes[name] = String(value); if (name === "id") this.id = String(value); }
}
const descendants = (element) => [element, ...element.children.flatMap(descendants)];
const localized = (prefix) => Object.fromEntries(["en", "ms", "zh"].map((lang) => [lang, prefix + " " + lang]));
const fixturePackage = (id) => ({
  subchapter: "9." + id,
  activities: [{
    id: "fixture-" + id,
    type: "mcq",
    difficulty: "easy",
    prompt: localized("Prompt " + id),
    answerKey: { correct: "a", options: [{ id: "a", label: localized("Correct") }] },
    feedback: localized("Feedback"),
    hints: [localized("Hint")],
  }],
});
const sha = (value) => crypto.createHash("sha256").update(value).digest("hex");
const flush = () => new Promise((resolve) => setImmediate(resolve));
async function waitFor(predicate) {
  for (let attempt = 0; attempt < 50; attempt++) {
    if (predicate()) return;
    await new Promise((resolve) => setTimeout(resolve, 20));
  }
  assert.fail("asynchronous package load did not settle");
}

function harness({ corruptManifest = false, wrongBytes = false, absentManifest = false } = {}) {
  const app = new FakeElement("section");
  app.dataset.packageUrl = "";
  app.dataset.externalPackageSelection = "true";
  const locale = new FakeElement("select");
  locale.value = "en";
  const preview = new FakeElement("section");
  preview.dataset.manifestUrl = absentManifest ? "" : "../local-pilot/roster.json";
  const select = new FakeElement("select");
  const status = new FakeElement("p");
  const nodes = { "#app": app, "#locale": locale, "#course-preview": preview, "#course-select": select, "#course-status": status };
  const files = new Map(), cases = [];
  for (let number = 1; number <= 6; number++) {
    const path = "content/chapter-9/section-9-" + number + "/package.json";
    const raw = Buffer.from(JSON.stringify(fixturePackage(number)), "utf8");
    files.set("../" + path, raw);
    cases.push({ sectionNumber: number, packagePath: path, packageSha256: sha(raw) });
  }
  if (corruptManifest) cases[1].sectionNumber = 1;
  const manifest = {
    scopeId: "sourcefree-pilot-synthetic-course",
    baselineGitSha: "a".repeat(40),
    chapterNumber: 9,
    mode: "OFFLINE_EXISTING_PACKAGES_ONLY",
    cases,
    modelCallsAllowed: false,
    pdfReadsAllowed: false,
    publicationAllowed: false,
  };
  if (wrongBytes) {
    const path = "../content/chapter-9/section-9-1/package.json";
    files.set(path, Buffer.from(JSON.stringify(fixturePackage(5)), "utf8"));
  }
  const calls = [];
  const fetch = async (url, options) => {
    calls.push({ url, options });
    if (url === "../local-pilot/roster.json") return { ok: true, json: async () => manifest };
    if (!files.has(url)) throw new Error("unexpected URL " + url);
    const raw = files.get(url);
    return {
      ok: true,
      arrayBuffer: async () => raw.buffer.slice(raw.byteOffset, raw.byteOffset + raw.byteLength),
      json: async () => JSON.parse(raw.toString("utf8")),
    };
  };
  const context = {
    document: { querySelector: (selector) => nodes[selector] || null, createElement: (tag) => new FakeElement(tag) },
    fetch, console, crypto: crypto.webcrypto, TextDecoder, Uint8Array,
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync("app/app.js", "utf8"), context, { filename: "app/app.js" });
  vm.runInContext(fs.readFileSync("app/course-preview.js", "utf8"), context, { filename: "app/course-preview.js" });
  return { app, locale, select, status, calls, context };
}

(async () => {
  const valid = harness();
  await flush();
  await flush();
  assert.equal(valid.select.disabled, false);
  assert.equal(valid.select.children.length, 7, "six authored candidates and one placeholder");
  assert.equal(valid.calls.length, 1, "do not fetch a package until the instructor selects one");
  assert.match(valid.status.textContent, /Select a section/);
  assert.match(valid.app.textContent, /Select a subchapter above/);
  assert.equal(vm.runInContext("state.package === null", valid.context), true);
  assert.doesNotMatch(valid.app.textContent, /No learning package was selected|Could not load/);
  valid.select.value = "3";
  valid.select.listeners.change();
  await waitFor(() => valid.app.textContent.includes("Prompt 3") || valid.app.textContent.includes("Could not load"));
  assert.deepEqual(valid.calls.map((x) => x.url), [
    "../local-pilot/roster.json", "../content/chapter-9/section-9-3/package.json",
  ]);
  assert.equal(descendants(valid.app).find((x) => x.tagName === "H1")?.textContent, "Prompt 3 en", valid.app.textContent);
  valid.locale.value = "ms";
  valid.locale.listeners.change({ target: { value: "ms" } });
  await flush();
  assert.equal(descendants(valid.app).find((x) => x.tagName === "H1").textContent, "Prompt 3 ms");
  assert.match(valid.status.textContent, /Pratonton pensyarah/);
  assert.equal(valid.calls.length, 2, "locale change must never reload or send learning evidence");

  // Exercise the player, then deselect. Old section activity and session-only
  // evidence must disappear; a fresh selection must restart at no mastery.
  const choice = descendants(valid.app).find((x) => x.className === "choice");
  assert.ok(choice?.listeners.click, "the actual player choice must be rendered");
  choice.listeners.click();
  const check = descendants(valid.app).find((x) => x.id === "check");
  assert.ok(check?.listeners.click);
  check.listeners.click();
  assert.equal(JSON.parse(vm.runInContext("JSON.stringify(state.sessionMetrics)", valid.context))["fixture-3"].checks, 1);

  valid.select.value = "";
  valid.select.listeners.change();
  assert.match(valid.app.textContent, /Select a subchapter above/);
  assert.equal(descendants(valid.app).filter((x) => x.tagName === "H1").length, 0);
  assert.deepEqual(JSON.parse(vm.runInContext("JSON.stringify(state.sessionMetrics)", valid.context)), {});
  assert.equal(vm.runInContext("state.package === null", valid.context), true);
  assert.equal(valid.calls.length, 2, "deselection must not fetch or persist learning data");
  valid.select.value = "4";
  valid.select.listeners.change();
  assert.match(valid.app.textContent, /Loading selected subchapter/);
  assert.doesNotMatch(valid.app.textContent, /Prompt 3|Session mastery evidence|Bukti penguasaan sesi/);
  await waitFor(() => valid.app.textContent.includes("Prompt 4 ms"));
  assert.equal(JSON.parse(vm.runInContext("JSON.stringify(masteryEvidence())", valid.context)).level, "not_started");
  assert.equal(valid.calls.length, 3);

  const invalid = harness({ corruptManifest: true });
  await flush();
  await flush();
  assert.equal(invalid.select.disabled, true);
  assert.equal(invalid.calls.length, 1, "invalid roster must not fetch a package");

  const noRoster = harness({ absentManifest: true });
  await flush();
  assert.equal(noRoster.calls.length, 0);
  assert.equal(noRoster.select.disabled, true);

  const mismatch = harness({ wrongBytes: true });
  await flush();
  await flush();
  mismatch.select.value = "1";
  mismatch.select.listeners.change();
  await waitFor(() => mismatch.app.textContent.includes("Could not load"));
  assert.match(mismatch.app.textContent, /Package bytes differ from the selected roster/);
  assert.equal(descendants(mismatch.app).filter((x) => x.tagName === "H1").length, 0,
    "tampered package must not render its activities");
  assert.equal(mismatch.calls.length, 2);
  console.log("Six-section instructor preview, multilingual selection and package SHA-256 fail-closed checks passed.");
})().catch((error) => { console.error(error); process.exitCode = 1; });
