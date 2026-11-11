/* Strictly local, original source-free RC1 route demonstration.
   No storage, real learner records, academic source, model, or publication. */
"use strict";
(function initRC1Demo() {
  const root = document.getElementById("rc1-lab");
  if (!root || !globalThis.BOSLACourseRoute) return;
  const status = document.getElementById("rc1-status");
  const route = document.getElementById("rc1-route");
  const reset = document.getElementById("rc1-reset");
  const FROZEN_SCOPE_SHA256 =
    "13c5234f5f22d7904c7a78f7d7927605a3e2ff4fbc9609ec66dfe34560619d76";
  let scope = null;
  const observations = new Map();

  async function verifyFrozenScope(value) {
    if (!globalThis.crypto?.subtle || typeof TextEncoder !== "function") {
      throw new Error("RC1_FROZEN_SCOPE_DIGEST_UNAVAILABLE");
    }
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
    const hex = Array.from(new Uint8Array(digest),
      (byte) => byte.toString(16).padStart(2, "0")).join("");
    if (hex !== FROZEN_SCOPE_SHA256) throw new Error("RC1_FROZEN_SCOPE_DRIFT");
  }

  function button(label, action, disabled = false) {
    const control = document.createElement("button");
    control.type = "button";
    control.textContent = label;
    control.disabled = disabled;
    control.addEventListener("click", action);
    return control;
  }

  function render() {
    const result = globalThis.BOSLACourseRoute.plan(
      scope, [...observations].map(([id, entry]) => ({id, ...entry}))
    );
    route.replaceChildren();
    const selected = result.stages.find((row) => row.id === result.suggestedSection);
    status.textContent = selected
      ? "Suggested next simulation: " + selected.title
        + " (" + result.suggestionReason.replaceAll("_", " ") + ")."
      : "All six concepts have simulated independent completion.";
    for (const section of result.stages) {
      const card = document.createElement("section");
      card.className = "rc1-card";
      const heading = document.createElement("h2");
      heading.textContent = section.title;
      const explanation = document.createElement("p");
      explanation.textContent = section.status === "locked"
        ? "Locked by sample prerequisite(s): " + section.unmetPrerequisites.join(", ")
        : "Simulated status: " + section.status.replaceAll("_", " ");
      card.append(heading, explanation);
      const controls = document.createElement("div");
      controls.className = "controls";
      const locked = section.status === "locked";
      const current = observations.get(section.id);
      controls.append(
        button("Simulate independent", () => {
          observations.set(section.id, {outcome:"independent", reviewDue:false});
          render();
        }, locked),
        button("Simulate assisted", () => {
          observations.set(section.id, {outcome:"assisted", reviewDue:false});
          render();
        }, locked),
        button("Flag review due", () => {
          observations.set(section.id, {outcome:"independent", reviewDue:true});
          render();
        }, locked || current?.outcome !== "independent"),
        button("Clear simulation", () => {
          observations.delete(section.id);
          render();
        }, !current)
      );
      card.append(controls);
      route.append(card);
    }
    reset.disabled = observations.size === 0;
  }

  reset.addEventListener("click", () => {
    observations.clear();
    render();
  });

  fetch("../docs/rc1_engineering_scope.json", {cache:"no-store"})
    .then((response) => {
      if (!response.ok) throw new Error("RC1_SCOPE_MISSING");
      return response.json();
    })
    .then(async (value) => {
      globalThis.BOSLACourseRoute.validateScope(value);
      await verifyFrozenScope(value);
      scope = value;
      render();
    })
    .catch(() => {
      status.textContent = "RC1 source-free scope unavailable or invalid. Routing disabled.";
      route.replaceChildren();
      reset.disabled = true;
    });
})();
