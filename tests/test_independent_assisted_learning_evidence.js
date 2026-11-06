"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

// Source-free browser fixture; HTML insertion, storage and network uploads disallowed.
class Element {
  constructor(tag) {
    this.tagName = tag.toUpperCase(); this.children = []; this.attributes = {};
    this.dataset = {}; this.style = {}; this.listeners = {}; this.className = "";
    this.disabled = false; this._text = "";
  }
  set innerHTML(_) { throw Error("untrusted HTML"); }
  set textContent(value) { this._text = String(value); this.children = []; }
  get textContent() { return this._text + this.children.map(c => c.textContent).join(""); }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this._text = ""; this.children = [...items]; }
  setAttribute(k,v) { this.attributes[k] = String(v); if (k === "id") this.id = String(v); }
  addEventListener(k,fn) { this.listeners[k] = fn; }
  focus() { this.focused = true; }
  click() { if (!this.disabled) this.listeners.click?.({ target: this }); }
}
const all = x => [x,...x.children.flatMap(all)];
const localized = s => ({ en:s, ms:s, zh:s });
const mcq = id => ({
  id, type:"mcq", difficulty:"easy", prompt:localized(id),
  feedback:localized("feedback"), hints:[localized("hint")],
  answerKey:{ correct:"right", options:[
    { id:"wrong", label:localized("Wrong") },
    { id:"right", label:localized("Right") },
  ] },
});
const pack = { subchapter:localized("Learning"), activities:
  ["direct","wrong-first","hint-first","skip-first"].map(mcq) };
const app = new Element("div"); app.dataset.packageUrl = "synthetic";
const locale = new Element("select");
const context = { console, document:{
  createElement:tag => new Element(tag),
  querySelector:q => q === "#app" ? app : locale,
  querySelectorAll:() => [],
}, fetch:async () => ({ ok:true, json:async () => pack }) };
vm.createContext(context);
vm.runInContext(fs.readFileSync("app/app.js","utf8"), context);
const id = x => all(app).find(e => e.id === x);
const choice = x => all(app).find(e => e.dataset?.value === x);
const metrics = () => JSON.parse(vm.runInContext("JSON.stringify(state.sessionMetrics)", context));
const report = () => JSON.parse(vm.runInContext("JSON.stringify(anonymousLearningFeedback())",context));
const mastery = () => JSON.parse(vm.runInContext("JSON.stringify(masteryEvidence())",context));
const levelLabel = () => all(app).find(e => e.className === "mastery-level")?.textContent;


setImmediate(() => {
  assert.equal(mastery().level,"not_started");
  assert.equal(levelLabel(),"Not yet demonstrated");
  // Independent success on the first submission.
  choice("right").click(); id("check").click(); id("check").click();
  assert.equal(mastery().level,"developing");
  assert.equal(mastery().independent,1);
  // Incorrect first response followed by correct answer is assisted.
  choice("wrong").click(); id("check").click();
  choice("right").click(); id("check").click(); id("check").click();
  // A correct first submitted answer after hint use is still assisted.
  id("hint").click(); choice("right").click(); id("check").click(); id("check").click();
  // Skip then revisit: never reclassify the first success as independent.
  id("skip").click();
  assert(id("review-pending"), "unfinished learner review action missing");
  id("review-pending").click();
  choice("right").click(); id("check").click(); id("check").click();

  assert.equal(mastery().level,"developing");
  assert.equal(mastery().independent,1);
  assert.equal(mastery().completed,4);
  assert.equal(mastery().independentPercent,25);
  assert.equal(mastery().notAGrade,true);
  const entries = report().activities;
  assert.deepEqual(entries.map(e => e.firstCheck),
    ["correct","wrong","correct","correct"]);
  assert.deepEqual(entries.map(e => e.completionEvidence),
    ["independent","assisted","assisted","assisted"]);
  assert.deepEqual(entries.map(e => e.firstCheckHadHint),
    [false,false,true,false]);
  assert.equal(entries[3].skips,1);
  assert.equal(metrics()["wrong-first"].wrong,1);
  assert.equal(report().schemaVersion,1,"additive fields preserve export compatibility");
  assert.equal(report().containsStudentIdentity,false);
  assert.equal(report().publicationAuthorized,false);
  assert(!JSON.stringify(report()).includes("feedback"));
  const summary = all(app).find(e => e.className === "evidence-summary");
  assert(summary && summary.textContent.includes("without help: 1"));
  assert(summary.textContent.includes("or a skip: 3"));
  locale.value = "ms"; locale.listeners.change({target:locale});
  assert.equal(levelLabel(),"Penaakulan kendiri sedang berkembang");
  assert(all(app).find(e => e.className === "evidence-summary")
    .textContent.includes("tanpa bantuan: 1"));
  locale.value = "zh"; locale.listeners.change({target:locale});
  assert.equal(levelLabel(),"独立推理能力逐步建立");
  assert(all(app).find(e => e.className === "evidence-summary").textContent.includes("3"));
  // Restart destroys all anonymous session evidence and skipped-history flags.
  id("restart").click();
  assert.deepEqual(metrics(),{});
  assert.equal(mastery().level,"not_started");
  assert.equal(levelLabel(),"尚未显示");
  assert.deepEqual(report().activities.map(e => e.completionEvidence),
    ["not_completed","not_completed","not_completed","not_completed"]);
  assert.deepEqual(report().activities.map(e => e.firstCheck),
    ["unattempted","unattempted","unattempted","unattempted"]);
  console.log("First-attempt and assisted learning evidence are correctly separated.");
});
