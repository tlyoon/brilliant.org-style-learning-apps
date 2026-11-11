"use strict";
const assert = require("node:assert/strict");
const diagnostic = require("../app/rc1-course-diagnostic.js");
const route = require("../app/rc1-course-routing.js");

const sections = [
  {id:"section-9-1", title:"Linear momentum", prerequisites:[]},
  {id:"section-9-2", title:"Isolated system", prerequisites:["section-9-1"]},
  {id:"section-9-3", title:"Nonisolated system", prerequisites:["section-9-2"]},
  {id:"section-9-4", title:"Collisions in one dimension", prerequisites:["section-9-2"]},
  {id:"section-9-5", title:"Collisions in two dimensions", prerequisites:["section-9-4"]},
  {id:"section-9-6", title:"Center of mass", prerequisites:["section-9-1"]},
];
const packet = (section, kind, updates = {}) => ({
  packageId:"chapter-9-section-9-" + section, activityOrdinal:1,
  kind, checks:0, firstCheck:null, firstCheckHadHint:false,
  hints:0, skips:0, completed:false, completionEvidence:null,
  ...updates,
});
const s = diagnostic.createSession();
assert.deepEqual(s.snapshot().observations, []);
const base = route.planDraftCourse(sections, []);
assert.equal(base.evidenceKind, "OBSERVED_DRAFT_PACKAGE_ANSWER_KEY_CHECKS");
assert.equal(base.scientificAnswerKeyVerified, false);
assert.equal(base.courseMasteryVerified, false);
assert.equal(base.publicationAuthorized, false);
assert.equal(base.advisoryOnly, true);
assert.equal(base.suggestedSection, "section-9-1");
assert.equal(base.stages[1].status, "locked");

// A valid player event must identify the selected real package, first activity,
// and minimal counters. It is never an independently validated physics grade.
assert.equal(s.accept(1, packet(2, "correct", {checks:1, firstCheck:"correct"})), false);
assert.equal(s.accept(1, packet(1, "correct", {
  activityOrdinal:2, checks:1, firstCheck:"correct",
})), false);
assert.equal(s.accept(7, packet(7, "wrong", {checks:1, firstCheck:"wrong"})), false);
assert.equal(s.accept(1, packet(1, "completed", {
  checks:0, completed:true, completionEvidence:"independent",
})), false);
assert.equal(s.snapshot().observations.length, 0, "invalid events must not create evidence");

// Check != completion: only actual second player action may mark independent.
assert.equal(s.accept(1, packet(1, "correct", {
  checks:1, firstCheck:"correct",
})), true);
let report = s.snapshot();
assert.equal(report.firstChecks, 1);
assert.equal(report.firstCorrect, 1);
assert.equal(report.independentlyCompleted, 0);
assert.equal(route.planDraftCourse(sections, report.observations).stages[1].status, "locked");
assert.equal(s.accept(1, packet(1, "completed", {
  checks:1, firstCheck:"correct", completed:true,
  completionEvidence:"independent",
})), true);
report = s.snapshot();
assert.equal(report.independentlyCompleted, 1);
assert.equal(report.firstCorrect, 1);
assert.equal(route.planDraftCourse(sections, report.observations).stages[1].status, "ready");
assert.equal(s.accept(1, packet(1, "completed", {
  checks:1, firstCheck:"correct", completed:true,
  completionEvidence:"independent",
})), false, "same completion cannot be counted twice");

// Wrong first check followed by a correct retry stays assisted even if caller
// reports "independent" on another package replay.
assert.equal(s.accept(2, packet(2, "wrong", {
  checks:1, firstCheck:"wrong",
})), true);
assert.equal(s.accept(2, packet(2, "correct", {
  checks:2, firstCheck:"wrong",
})), true);
assert.equal(s.accept(2, packet(2, "completed", {
  checks:2, firstCheck:"wrong", completed:true,
  completionEvidence:"assisted",
})), true);
report = s.snapshot();
assert.equal(report.firstChecks, 2);
assert.equal(report.firstCorrect, 1);
assert.equal(report.assistedCompletions, 1);
assert.equal(route.planDraftCourse(sections, report.observations).stages[2].status, "locked");
assert.equal(s.accept(2, packet(2, "completed", {
  checks:1, firstCheck:"correct", completed:true,
  completionEvidence:"independent",
})), false, "retaking cannot replace first encounter");

// A hint before checking disqualifies independent completion.
assert.equal(s.accept(6, packet(6, "hints", {hints:1})), true);
assert.equal(s.accept(6, packet(6, "correct", {
  checks:1, firstCheck:"correct", firstCheckHadHint:true, hints:1,
})), true);
assert.equal(s.accept(6, packet(6, "completed", {
  checks:1, firstCheck:"correct", firstCheckHadHint:true, hints:1,
  completed:true, completionEvidence:"assisted",
})), true);
assert.equal(s.snapshot().assistedCompletions, 2);

// Skipping and returning cannot turn the second encounter into first try.
assert.equal(s.accept(3, packet(3, "skips", {skips:1})), true);
assert.equal(s.accept(3, packet(3, "correct", {
  checks:1, firstCheck:"correct",
})), true);
assert.equal(s.accept(3, packet(3, "completed", {
  checks:1, firstCheck:"correct", completed:true,
  completionEvidence:"independent",
})), true);
assert.equal(s.snapshot().independentlyCompleted, 1);

// Navigation interruption also prevents inflation.
assert.equal(s.accept(4, packet(4, "correct", {
  checks:1, firstCheck:"correct",
})), true);
s.leave(4);
assert.equal(s.accept(4, packet(4, "completed", {
  checks:1, firstCheck:"correct", completed:true,
  completionEvidence:"independent",
})), true);
assert.equal(s.snapshot().independentlyCompleted, 1);
assert.equal(s.snapshot().assistedCompletions, 4);

// Normal session data remains anonymous, ephemeral and refuses malformed
// events, including answer-bearing extra fields.
const before = JSON.stringify(s.snapshot());
assert.equal(s.accept(5, {...packet(5, "correct", {
  checks:1, firstCheck:"correct",
}), selectedAnswer:"a"}), false);
assert.equal(s.accept(5, packet(5, "wrong", {
  checks:1, firstCheck:"correct",
})), false);
assert.equal(JSON.stringify(s.snapshot()), before);
assert.equal(s.snapshot().containsStudentIdentity, false);
assert.equal(s.snapshot().cohortStandingAvailable, false);
assert.equal(s.snapshot().persistent, false);
assert.equal(s.snapshot().grade, false);
s.reset();
assert.deepEqual(s.snapshot().observations, []);
assert.equal(route.planDraftCourse(sections, []).suggestedSection, "section-9-1");

const circular = structuredClone(sections);
circular[0].prerequisites = ["section-9-5"];
assert.throws(() => route.planDraftCourse(circular), /RC1_CYCLIC_PREREQUISITES/);
console.log("Actual-player diagnostic event scoring, no-inflation routing, and advisory draft-course rules passed.");
