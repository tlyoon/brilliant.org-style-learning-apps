/* Stage-0 six real draft packages + RC1 course graph + actual answer events.
   A provisional local instructor demonstration, NOT verified diagnosis.
   All events are in-memory, with no persistent profiles or real student data. */
"use strict";
(function initDraftCourseBridge() {
  const panel = document.querySelector("#rc1-draft-course");
  const player = document.querySelector("#app");
  const chooser = document.querySelector("#course-select");
  if (!panel || !player || !chooser
    || !globalThis.BOSLACourseRoute || !globalThis.BOSLADraftDiagnostic) return;
  const diagnostic = globalThis.BOSLADraftDiagnostic.createSession();
  const routeStatus = document.querySelector("#rc1-draft-status");
  const summary = document.querySelector("#rc1-draft-summary");
  const routeList = document.querySelector("#rc1-draft-list");
  const reset = document.querySelector("#rc1-draft-reset");
  const sections = Object.freeze([
    {id:"section-9-1", title:"9.1 Linear Momentum", prerequisites:[]},
    {id:"section-9-2", title:"9.2 Isolated System: Momentum", prerequisites:["section-9-1"]},
    {id:"section-9-3", title:"9.3 Nonisolated System: Momentum", prerequisites:["section-9-2"]},
    {id:"section-9-4", title:"9.4 Collisions in One Dimension", prerequisites:["section-9-2"]},
    {id:"section-9-5", title:"9.5 Collisions in Two Dimensions", prerequisites:["section-9-4"]},
    {id:"section-9-6", title:"9.6 Center of Mass", prerequisites:["section-9-1"]},
  ]);
  globalThis.BOSLACourseRoute.validateSections(sections);
  let active = 0;

  function render() {
    const evidence = diagnostic.snapshot();
    const route = globalThis.BOSLACourseRoute.planDraftCourse(
      sections, evidence.observations
    );
    summary.textContent = "Observed first checks correct: "
      + evidence.firstCorrect + " / " + evidence.firstChecks
      + "; independent first-activity completions: "
      + evidence.independentlyCompleted + " / 6; assisted completions: "
      + evidence.assistedCompletions + ". Session-only, not a grade.";
    if (chooser.disabled) {
      routeStatus.textContent = "Awaiting a verified local draft roster. "
        + "No real package has been loaded.";
    } else {
      const chosen = route.stages.find((item) => item.id === route.suggestedSection);
      routeStatus.textContent = chosen
        ? "Provisional suggested next topic: " + chosen.title
          + ". Route is advisory only; answer-key accuracy remains unverified."
        : "No further topic is recommended by this provisional route. "
          + "This does not establish course mastery.";
    }
    routeList.replaceChildren();
    for (const stage of route.stages) {
      const row = document.createElement("li");
      const title = document.createElement("strong");
      title.textContent = stage.title + ": ";
      const detail = document.createElement("span");
      detail.textContent = stage.status.replaceAll("_", " ")
        + (stage.unmetPrerequisites.length
          ? " (sample prerequisites: " + stage.unmetPrerequisites.join(", ") + ")" : "");
      row.append(title, detail);
      routeList.append(row);
    }
    reset.disabled = evidence.observations.length === 0;
  }

  panel.addEventListener("bosla:course-roster-state", render);
  chooser.addEventListener("change", () => {
    if (active) diagnostic.leave(active);
    active = /^[1-6]$/.test(chooser.value) ? Number(chooser.value) : 0;
    render();
  });
  player.addEventListener("bosla:player-evidence", (event) => {
    if (active && !chooser.disabled && diagnostic.accept(active, event.detail)) {
      render();
    }
  });
  reset.addEventListener("click", () => {
    diagnostic.reset();
    active = 0;
    chooser.value = "";
    chooser.dispatchEvent(new Event("change"));
    render();
  });
  // The course-preview selector itself will fetch and hash-verify the
  // exact six registered local packages; this bridge never fetches them.
  render();
})();
