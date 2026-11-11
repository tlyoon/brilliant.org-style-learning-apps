/* RC1 source-free, in-memory prerequisite and review routing.
   This module never opens a PDF, grades a learner or persists any evidence. */
"use strict";
(function installCourseRouting(host) {
  const VERSION = "RC1_SOURCEFREE_ROUTE_V1";
  const ID = /^[a-z][a-z0-9-]{2,47}$/;
  const OWN = (object, key) => Object.prototype.hasOwnProperty.call(object, key);

  function objectWithKeys(value, keys) {
    return value !== null && typeof value === "object" && !Array.isArray(value)
      && Object.keys(value).length === keys.length && keys.every((key) => OWN(value, key));
  }

  function validateScope(scope) {
    const keys = ["schemaVersion", "scopeId", "kind", "baselineGitSha",
      "mode", "gatesSource", "originalChapter9CampaignsReopened",
      "textbookEditionOrRightsGateRequired", "externalModelCallsAllowed",
      "sourcePdfReadsAllowed", "realLearnerRecordsAllowed",
      "publicPublicationAllowed", "gitAutoMergeAllowed", "reviewBudget", "sections"];
    const flags = ["originalChapter9CampaignsReopened", "textbookEditionOrRightsGateRequired",
      "externalModelCallsAllowed", "sourcePdfReadsAllowed",
      "realLearnerRecordsAllowed", "publicPublicationAllowed", "gitAutoMergeAllowed"];
    if (!objectWithKeys(scope, keys) || scope.schemaVersion !== 1
      || scope.scopeId !== "bosla-rc1-sourcefree-course-routing-20261111"
      || scope.kind !== "INDEPENDENT_SOURCEFREE_ENGINEERING_SCOPE"
      || !/^[a-f0-9]{40}$/.test(scope.baselineGitSha)
      || scope.mode !== "ORIGINAL_SYNTHETIC_CONCEPTS_ONLY"
      || scope.gatesSource !== "docs/acceptance_closure_chapter9.json"
      || flags.some((key) => scope[key] !== false)
      || !objectWithKeys(scope.reviewBudget, [
        "maxSyntheticBrowserSmokes", "maxSourceCampaigns", "maxAcademicExternalReviews"
      ]) || scope.reviewBudget.maxSyntheticBrowserSmokes !== 1
      || scope.reviewBudget.maxSourceCampaigns !== 0
      || scope.reviewBudget.maxAcademicExternalReviews !== 0
      || !Array.isArray(scope.sections) || scope.sections.length !== 6) {
      throw new Error("RC1_SCOPE_UNAUTHORIZED_OR_INVALID");
    }
    const ids = new Set();
    for (const section of scope.sections) {
      if (!objectWithKeys(section, ["id", "title", "prerequisites"])
        || typeof section.id !== "string" || !ID.test(section.id)
        || typeof section.title !== "string" || !section.title.trim()
        || section.title.length > 80 || !Array.isArray(section.prerequisites)
        || section.prerequisites.length > 5
        || section.prerequisites.some((id) => typeof id !== "string" || !ID.test(id))
        || new Set(section.prerequisites).size !== section.prerequisites.length
        || ids.has(section.id)) throw new Error("RC1_INVALID_SECTION_GRAPH");
      ids.add(section.id);
    }
    for (const section of scope.sections) {
      if (section.prerequisites.some((id) => !ids.has(id) || id === section.id)) {
        throw new Error("RC1_MISSING_OR_SELF_PREREQUISITE");
      }
    }
    const visited = new Set(), visiting = new Set();
    const lookup = new Map(scope.sections.map((section) => [section.id, section]));
    function walk(id) {
      if (visiting.has(id)) throw new Error("RC1_CYCLIC_PREREQUISITES");
      if (visited.has(id)) return;
      visiting.add(id);
      lookup.get(id).prerequisites.forEach(walk);
      visiting.delete(id);
      visited.add(id);
    }
    ids.forEach(walk);
  }

  function plan(scope, observations = []) {
    validateScope(scope);
    if (!Array.isArray(observations) || observations.length > 6) {
      throw new Error("RC1_INVALID_SESSION_OBSERVATIONS");
    }
    const known = new Set(scope.sections.map((row) => row.id));
    const results = new Map();
    for (const item of observations) {
      if (!objectWithKeys(item, ["id", "outcome", "reviewDue"])
        || !known.has(item.id) || results.has(item.id)
        || !["independent", "assisted", "not_yet"].includes(item.outcome)
        || typeof item.reviewDue !== "boolean"
        || (item.reviewDue && item.outcome !== "independent")) {
        throw new Error("RC1_INVALID_SESSION_OBSERVATIONS");
      }
      results.set(item.id, {outcome: item.outcome, reviewDue: item.reviewDue});
    }
    const completed = new Set([...results].filter(([, item]) =>
      item.outcome === "independent").map(([id]) => id));
    const stages = scope.sections.map((section) => {
      const result = results.get(section.id);
      const unmet = section.prerequisites.filter((id) => !completed.has(id));
      const status = unmet.length ? "locked" : result?.outcome === "independent"
        ? (result.reviewDue ? "review_due" : "independent_completed")
        : result?.outcome === "assisted" ? "assisted_practice" : "ready";
      return {id: section.id, title: section.title, status, unmetPrerequisites: unmet};
    });
    const chosen = ["review_due", "assisted_practice", "ready"]
      .map((kind) => stages.find((stage) => stage.status === kind))
      .find(Boolean) || null;
    return {
      version: VERSION, scopeId: scope.scopeId,
      evidenceKind: "SIMULATED_SESSION_ONLY",
      persistentMasteryClaim: false, publicationAuthorized: false,
      suggestedSection: chosen?.id || null,
      suggestionReason: chosen?.status || "no_available_section",
      stages,
    };
  }

  const api = Object.freeze({version: VERSION, validateScope, plan});
  host.BOSLACourseRoute = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis === "object" ? globalThis : this);
