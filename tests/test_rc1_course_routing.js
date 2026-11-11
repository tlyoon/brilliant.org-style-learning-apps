"use strict";
// New, independent source-free RC1 scope: deterministic in-memory routing tests.
// These outcomes are synthetic, not learner results or academic acceptance.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const crypto = require("node:crypto");
const route = require("../app/rc1-course-routing.js");
const scope = JSON.parse(fs.readFileSync("docs/rc1_engineering_scope.json", "utf8"));

assert.equal(
  crypto.createHash("sha256").update(JSON.stringify(scope)).digest("hex"),
  "13c5234f5f22d7904c7a78f7d7927605a3e2ff4fbc9609ec66dfe34560619d76",
  "RC1 scope identity must not drift or reuse a frozen source campaign"
);
assert.equal(scope.baselineGitSha, "a6bc4dac35b6fb0a157ac0261bfe3474b2b1a78b");
assert.equal(scope.originalChapter9CampaignsReopened, false);
assert.equal(scope.textbookEditionOrRightsGateRequired, false);
assert.equal(scope.publicPublicationAllowed, false);
assert.equal(scope.externalModelCallsAllowed, false);
assert.equal(scope.realLearnerRecordsAllowed, false);
assert.equal(scope.reviewBudget.maxSourceCampaigns, 0);
assert.equal(scope.reviewBudget.maxAcademicExternalReviews, 0);
route.validateScope(scope);

const stage = (plan, id) => plan.stages.find((item) => item.id === id);
const observation = (id, outcome, reviewDue = false) => ({id, outcome, reviewDue});
const initial = route.plan(scope);
assert.equal(initial.suggestedSection, "concept-vectors");
assert.equal(initial.evidenceKind, "SIMULATED_SESSION_ONLY");
assert.equal(initial.persistentMasteryClaim, false);
assert.equal(initial.publicationAuthorized, false);
assert.equal(stage(initial, "concept-motion").status, "locked");
assert.equal(stage(initial, "concept-connections").status, "locked");

// Assisted work never unlocks an independent prerequisite.
const helped = route.plan(scope, [observation("concept-vectors", "assisted")]);
assert.equal(helped.suggestedSection, "concept-vectors");
assert.equal(stage(helped, "concept-vectors").status, "assisted_practice");
assert.equal(stage(helped, "concept-motion").status, "locked");
assert.equal(stage(helped, "concept-forces").status, "locked");

// Exact successful prerequisites unlock both independent branches.
const vector = observation("concept-vectors", "independent");
const branches = route.plan(scope, [vector]);
assert.equal(branches.suggestedSection, "concept-motion");
assert.equal(stage(branches, "concept-motion").status, "ready");
assert.equal(stage(branches, "concept-forces").status, "ready");
assert.equal(stage(branches, "concept-energy").status, "locked");
const motionHelped = route.plan(scope, [vector, observation("concept-motion", "assisted")]);
assert.equal(motionHelped.suggestedSection, "concept-motion");
assert.equal(stage(motionHelped, "concept-energy").status, "locked");

// A due review is prioritized without a real timer, timestamp or learner record.
const due = route.plan(scope, [observation("concept-vectors", "independent", true)]);
assert.equal(due.suggestedSection, "concept-vectors");
assert.equal(due.suggestionReason, "review_due");
const all = scope.sections.map(({id}) => observation(id, "independent"));
assert.equal(route.plan(scope, all).suggestedSection, null);
assert.equal(route.plan(scope, all.slice(0, 5)).suggestedSection, "concept-connections");

// Invalid evidence cannot be used to manufacture a route or independent mastery.
for (const evidence of [
  [{}], [observation("unknown-concept", "independent")],
  [observation("concept-vectors", "passed")],
  [observation("concept-vectors", "assisted", true)],
  [observation("concept-vectors", "independent"), observation("concept-vectors", "independent")],
  [observation("concept-vectors", "independent", "true")],
  new Array(7).fill(observation("concept-vectors", "independent")),
]) assert.throws(() => route.plan(scope, evidence), /RC1_INVALID_SESSION_OBSERVATIONS/);

const clone = () => JSON.parse(JSON.stringify(scope));
const bad = [
  (x) => { x.publicPublicationAllowed = true; },
  (x) => { x.externalModelCallsAllowed = true; },
  (x) => { x.textbookEditionOrRightsGateRequired = true; },
  (x) => { x.originalChapter9CampaignsReopened = true; },
  (x) => { x.sections.pop(); },
  (x) => { x.sections[1].prerequisites = ["missing"]; },
  (x) => { x.sections[0].prerequisites = ["concept-motion"]; },
  (x) => { x.sections[0].id = x.sections[1].id; },
  (x) => { x.sections[0].title = "<script>alert(1)</script>".repeat(5); },
  (x) => { x.reviewBudget.maxSourceCampaigns = 1; },
  (x) => { x.sections[3].prerequisites = ["concept-energy"]; },
];
for (const mutation of bad) {
  const changed = clone();
  mutation(changed);
  assert.throws(() => route.plan(changed), /RC1_/);
}
console.log("RC1 independent source-free route and anti-replay contracts passed.");
