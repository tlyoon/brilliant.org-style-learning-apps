/* A provisional diagnostic from ACTUAL Stage-0 answer checks, never synthetic
   button presses, graded mastery, or independently validated academic evidence.
   Entirely session-memory; no student identity, timestamps or persistence. */
"use strict";
(function installDraftDiagnostic(host) {
  const ALLOWED = new Set(["wrong", "correct", "completed", "hints", "skips"]);
  const OWN = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const FIELDS = ["packageId", "activityOrdinal", "kind", "checks",
    "firstCheck", "firstCheckHadHint", "hints", "skips", "completed",
    "completionEvidence"];
  function isPacket(packet) {
    return packet !== null && typeof packet === "object" && !Array.isArray(packet)
      && Object.keys(packet).length === FIELDS.length
      && FIELDS.every((key) => OWN(packet, key))
      && typeof packet.packageId === "string"
      && packet.activityOrdinal === 1 && ALLOWED.has(packet.kind)
      && Number.isSafeInteger(packet.checks) && packet.checks >= 0
      && Number.isSafeInteger(packet.hints) && packet.hints >= 0
      && Number.isSafeInteger(packet.skips) && packet.skips >= 0
      && [null, "wrong", "correct"].includes(packet.firstCheck)
      && typeof packet.firstCheckHadHint === "boolean"
      && typeof packet.completed === "boolean"
      && [null, "independent", "assisted"].includes(packet.completionEvidence)
      && (packet.firstCheck === null || packet.checks > 0)
      && (!packet.completed || packet.completionEvidence !== null)
      && (packet.completed || packet.completionEvidence === null);
  }

  function createSession() {
    const rows = new Map();
    function accept(sectionNumber, packet) {
      if (!Number.isInteger(sectionNumber) || sectionNumber < 1
        || sectionNumber > 6 || !isPacket(packet)
        || packet.packageId !== "chapter-9-section-9-" + sectionNumber) return false;
      if ((packet.kind === "correct" || packet.kind === "wrong")
        && (packet.checks < 1
          || packet.checks === 1 && packet.firstCheck !== packet.kind)
        || packet.kind === "completed" && !packet.completed) return false;
      const id = "section-9-" + sectionNumber;
      // A completion without an earlier observed check is not admissible
      // evidence; never create a row before deciding to refuse it.
      if (packet.kind === "completed" && !rows.has(id)) return false;
      let row = rows.get(id);
      if (row?.completed) return false;
      if (!row) {
        row = {id, firstCheck:null, firstCheckHadHint:false, priorHelp:false,
          answered:false, completed:false, outcome:"not_yet", interrupted:false};
        rows.set(id, row);
      }
      if (packet.kind === "skips" || packet.kind === "hints") {
        row.priorHelp = true;
      }
      // Once the first checked response is observed it is frozen, even
      // across navigation/retries. Never select the best of multiple checks.
      if (row.firstCheck === null && packet.firstCheck !== null) {
        row.firstCheck = packet.firstCheck;
        row.firstCheckHadHint = packet.firstCheckHadHint;
        row.answered = true;
        row.priorHelp = row.priorHelp || packet.firstCheckHadHint
          || packet.hints > 0 || packet.skips > 0
          || packet.checks > 1;
      }
      if (packet.kind === "completed") {
        if (!row.answered) return false;
        row.completed = true;
        row.outcome = row.firstCheck === "correct" && !row.priorHelp
          && !row.interrupted && packet.completionEvidence === "independent"
          ? "independent" : "assisted";
      }
      return true;
    }

    function leave(sectionNumber) {
      if (!Number.isInteger(sectionNumber) || sectionNumber < 1
        || sectionNumber > 6) return;
      const row = rows.get("section-9-" + sectionNumber);
      if (row && !row.completed) row.interrupted = true;
    }

    function snapshot() {
      const observations = [];
      let firstChecks = 0, firstCorrect = 0, independent = 0, assisted = 0;
      for (const row of rows.values()) {
        if (row.answered) {
          firstChecks += 1;
          if (row.firstCheck === "correct") firstCorrect += 1;
        }
        if (row.outcome === "independent") independent += 1;
        if (row.outcome === "assisted") assisted += 1;
        observations.push({id:row.id, outcome:row.outcome, reviewDue:false});
      }
      return {
        evidenceKind:"ACTUAL_DRAFT_PLAYER_KEY_CHECKS",
        keyAndTranslationsIndependentlyVerified:false,
        containsStudentIdentity:false, persistent:false,
        cohortStandingAvailable:false, grade:false,
        firstChecks, firstCorrect, independentlyCompleted:independent,
        assistedCompletions:assisted, observations,
      };
    }

    function reset() { rows.clear(); }
    return Object.freeze({accept, leave, snapshot, reset});
  }
  const api = Object.freeze({createSession});
  host.BOSLADraftDiagnostic = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis === "object" ? globalThis : this);
