const DEFAULT_PACKAGE = document.querySelector("#app").dataset.packageUrl || "";
const state = { package: null, activityIndex: 0, locale: "en", response: null, checked: false, hint: false, loading: false, sessionMetrics: {}, reviewPending: false };
let loadGeneration = 0;

const copy = {
  en: { activity: "Activity", of: "of", check: "Check answer", next: "Next activity", tryAgain: "Try again", restart: "Start again", hint: "Show a hint", complete: "Journey complete", correct: "That reasoning fits.", retry: "Reconsider the relationship and try again.", moveUp: "Move up", moveDown: "Move down", position: "Position", skip: "Skip", completedCount: "Correctly completed:", reviewPending: "Review unfinished activities" },
  ms: { activity: "Aktiviti", of: "daripada", check: "Semak jawapan", next: "Aktiviti seterusnya", tryAgain: "Cuba lagi", restart: "Mula semula", hint: "Tunjukkan petunjuk", complete: "Perjalanan selesai", correct: "Penaakulan itu sesuai.", retry: "Pertimbangkan semula hubungan itu dan cuba lagi.", moveUp: "Alih ke atas", moveDown: "Alih ke bawah", position: "Kedudukan", skip: "Langkau", completedCount: "Diselesaikan dengan betul:", reviewPending: "Ulang aktiviti belum selesai" },
  zh: { activity: "活动", of: "/", check: "检查答案", next: "下一个活动", tryAgain: "再试一次", restart: "重新开始", hint: "显示提示", complete: "学习旅程完成", correct: "这个推理是恰当的。", retry: "重新思考其中的关系，然后再试一次。", moveUp: "上移", moveDown: "下移", position: "位置", skip: "跳过", completedCount: "\u5df2\u6b63\u786e\u5b8c\u6210\uff1a", reviewPending: "\u590d\u4e60\u672a\u5b8c\u6210\u7684\u6d3b\u52a8" },
};

const localized = (value) => typeof value === "string" ? value : value?.[state.locale] ?? value?.en ?? "";

const ACTIVITY_QUERY_KEY = "activity";

function activityIdFromLocation() {
  if (typeof window === "undefined" || !window.location) return "";
  try {
    return new URL(window.location.href).searchParams.get(ACTIVITY_QUERY_KEY) || "";
  } catch (_error) {
    return "";
  }
}

function applyActivityDeepLink(activities) {
  const requestedId = activityIdFromLocation();
  const requestedIndex = requestedId ? activities.findIndex((activity) => activity.id === requestedId) : -1;
  state.activityIndex = requestedIndex >= 0 ? requestedIndex : 0;
  resetActivity();
}

function syncActivityUrl(activity) {
  if (typeof window === "undefined" || !window.location || !window.history?.replaceState) return;
  try {
    const url = new URL(window.location.href);
    if (activity?.id) url.searchParams.set(ACTIVITY_QUERY_KEY, activity.id);
    else url.searchParams.delete(ACTIVITY_QUERY_KEY);
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
  } catch (_error) {
    // Rendering must remain usable even when a host blocks History API access.
  }
}

function element(tag, { className, text, attributes } = {}) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  for (const [name, value] of Object.entries(attributes ?? {})) node.setAttribute(name, value);
  return node;
}

function focusUpdatedChoice(selector, matches) {
  // Interaction updates rebuild the card. Return keyboard focus to the
  // same semantic control on the new card rather than the document body.
  const controls = document.querySelectorAll?.(selector) ?? [];
  for (const control of controls) {
    if (matches(control)) { control.focus?.(); return true; }
  }
  return false;
}

// Anonymous, in-memory session counters only: no content, identity, network or persistence.
function recordLearningEvent(activity, event) {
  const id = activity.id;
  if (!Object.hasOwn(state.sessionMetrics, id)) {
    state.sessionMetrics[id] = { checks: 0, wrong: 0, correct: 0, hints: 0, skips: 0, autoHintShown: false, completed: false };
  }
  const entry = state.sessionMetrics[id];
  if (event === "wrong" || event === "correct") {
    entry.checks += 1;
    entry[event] += 1;
  } else if (event === "completed") {
    entry.completed = true;
  } else if (event === "hints" || event === "skips") {
    entry[event] += 1;
  } else {
    throw new Error("unknown private learning event");
  }
}

function resetActivity() {
  state.response = null;
  state.checked = false;
  state.hint = false;
}

function ensureResponse(activity) {
  if (state.response !== null) return;
  if (activity.type !== "interactive") state.response = null;
  else if (activity.interactionMode === "ordering") state.response = activity.interaction.items.map((item) => item.id).reverse();
  else if (activity.interactionMode === "selection") state.response = [];
  else state.response = {};
}

function sameMembers(actual, expected) {
  return actual.length === expected.length && actual.every((value) => expected.includes(value));
}

function responseComplete(activity) {
  if (activity.type !== "interactive") return state.response !== null;
  if (activity.interactionMode === "selection") return state.response.length > 0;
  if (activity.interactionMode === "ordering") return state.response.length === activity.interaction.items.length;
  return activity.interaction.items.every((item) => state.response[item.id]);
}

function responseCorrect(activity) {
  if (activity.type !== "interactive") return state.response === activity.answerKey.correct;
  const interaction = activity.interaction;
  if (activity.interactionMode === "ordering") {
    return interaction.correctOrder.every((itemId, index) => state.response[index] === itemId);
  }
  if (activity.interactionMode === "selection") return sameMembers(state.response, interaction.correctSelections);
  return interaction.placements.every((placement) => state.response[placement.itemId] === placement.targetId);
}

function renderMcq(card, activity) {
  const choices = element("div", { className: "choices" });
  for (const option of activity.answerKey.options) {
    const button = element("button", {
      className: "choice",
      text: localized(option.label),
      attributes: { "aria-pressed": String(state.response === option.id) },
    });
    button.dataset.value = option.id;
    button.addEventListener("click", () => {
      state.response = option.id;
      state.checked = false;
      render();
      // Rerendering replaces the activated button. Restore focus to its
      // selected replacement so keyboard users keep their place.
      document.querySelector("#app .choices button[aria-pressed='true']")?.focus?.();
    });
    choices.append(button);
  }
  card.append(choices);
}

function renderPlacements(card, activity) {
  const interaction = activity.interaction;
  const groups = element("div", { className: "interaction-groups" });
  for (const item of interaction.items) {
    const group = element("div", { className: "interaction-group", attributes: { role: "group", "aria-label": localized(item.label) } });
    group.append(element("p", { className: "interaction-item", text: localized(item.label) }));
    const targets = element("div", { className: "target-choices" });
    for (const target of interaction.targets) {
      const button = element("button", {
        className: "choice target-choice",
        text: localized(target.label),
        attributes: { "aria-pressed": String(state.response[item.id] === target.id) },
      });
      button.dataset.itemId = item.id;
      button.dataset.targetId = target.id;
      button.addEventListener("click", () => {
        state.response = { ...state.response, [item.id]: target.id };
        state.checked = false;
        render();
        focusUpdatedChoice("#app .target-choice", (candidate) =>
          candidate.dataset?.itemId === item.id && candidate.dataset?.targetId === target.id
        );
      });
      targets.append(button);
    }
    group.append(targets);
    groups.append(group);
  }
  card.append(groups);
}

function renderSelection(card, activity) {
  const choices = element("div", { className: "choices" });
  for (const item of activity.interaction.items) {
    const selected = state.response.includes(item.id);
    const button = element("button", {
      className: "choice",
      text: localized(item.label),
      attributes: { "aria-pressed": String(selected) },
    });
    button.dataset.value = item.id;
    button.addEventListener("click", () => {
      state.response = selected ? state.response.filter((id) => id !== item.id) : [...state.response, item.id];
      state.checked = false;
      render();
      focusUpdatedChoice("#app .choices button", (candidate) => candidate.dataset?.value === item.id);
    });
    choices.append(button);
  }
  card.append(choices);
}

function renderOrdering(card, activity) {
  const labels = copy[state.locale];
  const byId = Object.fromEntries(activity.interaction.items.map((item) => [item.id, item]));
  const list = element("div", { className: "ordering", attributes: { role: "list", "aria-label": localized(activity.prompt) } });
  state.response.forEach((itemId, index) => {
    const row = element("div", { className: "order-row", attributes: { role: "listitem" } });
    row.dataset.itemId = itemId;
    row.append(element("p", { className: "interaction-item", text: `${labels.position} ${index + 1}: ${localized(byId[itemId].label)}` }));
    const controls = element("div", { className: "order-controls" });
    for (const [text, delta] of [[labels.moveUp, -1], [labels.moveDown, 1]]) {
      const button = element("button", { className: "secondary order-control", text, attributes: { "aria-label": `${text}: ${localized(byId[itemId].label)}` } });
      button.dataset.itemId = itemId;
      button.dataset.delta = String(delta);
      button.disabled = index + delta < 0 || index + delta >= state.response.length;
      button.addEventListener("click", () => {
        const reordered = [...state.response];
        [reordered[index], reordered[index + delta]] = [reordered[index + delta], reordered[index]];
        state.response = reordered;
        state.checked = false;
        render();
        const selector = "#app .order-control";
        const sameDirection = focusUpdatedChoice(selector, (control) =>
          control.dataset?.itemId === itemId && control.dataset?.delta === String(delta) && !control.disabled
        );
        if (!sameDirection) focusUpdatedChoice(selector, (control) =>
          control.dataset?.itemId === itemId && control.dataset?.delta === String(-delta) && !control.disabled
        );
      });
      controls.append(button);
    }
    row.append(controls);
    list.append(row);
  });
  card.append(list);
}

function renderResponse(card, activity) {
  ensureResponse(activity);
  if (activity.type !== "interactive") renderMcq(card, activity);
  else if (["classification", "matching"].includes(activity.interactionMode)) renderPlacements(card, activity);
  else if (activity.interactionMode === "ordering") renderOrdering(card, activity);
  else renderSelection(card, activity);
}

function renderVisual(card, activity) {
  if (!activity.visualSpec) return;
  const renderer = globalThis.LearningVisuals ?? globalThis.PhysicsVisuals;
  if (renderer?.renderVisualSpec) {
    card.append(renderer.renderVisualSpec(activity.visualSpec, {
      locale: state.locale,
      plan: activity.visualPlan,
    }));
    return;
  }
  const fallback = element("div", { className: "learning-visual learning-visual--fallback" });
  fallback.setAttribute("role", "img");
  fallback.setAttribute("aria-label", localized(activity.visualSpec.accessibility?.description) || "Learning visual");
  fallback.append(element("p", {
    className: "learning-visual__fallback-text",
    text: localized(activity.visualSpec.accessibility?.description) || "Learning visual",
  }));
  card.append(fallback);
}

function nextUnfinishedIndex(start) {
  const i = state.package.activities.findIndex((activity,index) =>
    index >= start && !state.sessionMetrics[activity.id]?.completed
  );
  return i < 0 ? state.package.activities.length : i;
}

function renderComplete(root) {
  syncActivityUrl(null);
  const card = element("section", { className: "card" });
  card.append(
    element("p", { className: "eyebrow", text: localized(state.package.subchapter) }),
    element("h1", { text: copy[state.locale].complete }),
  );
  const total = state.package.activities.length;
  const completed = state.package.activities.filter((a) => state.sessionMetrics[a.id]?.completed).length;
  card.append(element("p", { className: "progress-summary",
    text: copy[state.locale].completedCount + " " + completed + " / " + total }));
  if (completed < total) {
    const review = element("button", { className: "action secondary",
      text: copy[state.locale].reviewPending, attributes: { id: "review-pending" } });
    review.addEventListener("click", () => {
      state.reviewPending = true;
      state.activityIndex = nextUnfinishedIndex(0);
      resetActivity();
      render();
    });
    card.append(review);
  }
  const restart = element("button", { className: "action", text: copy[state.locale].restart, attributes: { id: "restart" } });
  restart.addEventListener("click", () => {
    state.sessionMetrics = {};
    state.reviewPending = false;
    state.activityIndex = 0;
    resetActivity();
    render();
  });
  card.append(restart);
  root.replaceChildren(card);
}

function render() {
  const root = document.querySelector("#app");
  const activities = state.package.activities;
  if (state.activityIndex >= activities.length) {
    renderComplete(root);
    return;
  }

  const activity = activities[state.activityIndex];
  syncActivityUrl(activity);
  ensureResponse(activity);
  const labels = copy[state.locale];
  const card = element("section", { className: "card" });
  card.append(element("p", {
    className: "eyebrow",
    text: `${labels.activity} ${state.activityIndex + 1} ${labels.of} ${activities.length} · ${activity.difficulty}`,
  }));

  const progress = element("div", { className: "progress", attributes: { "aria-label": "Progress" } });
  const progressBar = element("span");
  progressBar.style.width = `${((state.activityIndex + 1) / activities.length) * 100}%`;
  progress.append(progressBar);
  card.append(progress, element("h1", { className: "question", text: localized(activity.prompt) }));

  renderVisual(card, activity);
  renderResponse(card, activity);

  if (state.hint) card.append(element("div", { className: "feedback", text: localized(activity.hints[0]) }));
  if (state.checked) {
    const result = responseCorrect(activity) ? labels.correct : labels.retry;
    card.append(element("div", {
      className: "feedback",
      text: `${result} ${localized(activity.feedback)}`,
      attributes: { role: "status" },
    }));
  }

  const actions = element("div", { className: "action-row" });
  const checkLabel = state.checked
    ? (responseCorrect(activity) ? labels.next : labels.tryAgain)
    : labels.check;
  const check = element("button", { className: "action", text: checkLabel, attributes: { id: "check" } });
  check.disabled = !responseComplete(activity);
  check.addEventListener("click", () => {
    if (!state.checked) {
      const correct = responseCorrect(activity);
      recordLearningEvent(activity, correct ? "correct" : "wrong");
      // Feedback loop: after two wrong checks, reveal the EXISTING authored
      // hint in the selected locale; never generate ungrounded scientific text.
      const progress = state.sessionMetrics[activity.id];
      if (!correct && progress.wrong >= 2 && !state.hint && !progress.autoHintShown &&
          activity.hints?.[0]) {
        progress.autoHintShown = true;
        recordLearningEvent(activity, "hints");
        state.hint = true;
      }
      state.checked = true;
    } else if (responseCorrect(activity)) {
      recordLearningEvent(activity, "completed");
      state.activityIndex = state.reviewPending
        ? nextUnfinishedIndex(state.activityIndex + 1) : state.activityIndex + 1;
      resetActivity();
    } else resetActivity();
    render();
  });
  const hint = element("button", { className: "action secondary", text: labels.hint, attributes: { id: "hint" } });
  hint.addEventListener("click", () => {
    if (!state.hint) recordLearningEvent(activity, "hints");
    state.hint = true; render();
  });
  actions.append(check, hint);
  const skip = element("button", { className: "action secondary skip-action", text: labels.skip, attributes: { id: "skip" } });
  skip.addEventListener("click", () => {
    recordLearningEvent(activity, "skips");
    state.activityIndex = state.reviewPending
      ? nextUnfinishedIndex(state.activityIndex + 1) : state.activityIndex + 1;
    resetActivity();
    render();
  });
  card.append(actions, skip);
  root.replaceChildren(card);
}

const localeSelector = document.querySelector("#locale");

async function loadPackage(packageUrl = DEFAULT_PACKAGE) {
  const generation = ++loadGeneration;
  state.loading = true;
  localeSelector.disabled = true;
  if (!packageUrl) {
    state.package = null;
    state.loading = false;
    localeSelector.disabled = false;
    const message = "No learning package was selected. Supply data-package-url in the host page or call loadPackage(packageUrl).";
    document.querySelector("#app").replaceChildren(element("p", { className: "error", text: message }));
    return;
  }
  try {
    const response = await fetch(packageUrl);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const loadedPackage = await response.json();
    if (generation !== loadGeneration) return;
    state.package = loadedPackage;
    state.sessionMetrics = {};
    state.reviewPending = false;
    applyActivityDeepLink(loadedPackage.activities ?? []);
    state.loading = false;
    localeSelector.disabled = false;
    render();
  } catch (error) {
    if (generation !== loadGeneration) return;
    state.package = null;
    state.loading = false;
    localeSelector.disabled = false;
    const message = `Could not load the selected learning package. Start the app through the documented local server. (${error.message})`;
    document.querySelector("#app").replaceChildren(element("p", { className: "error", text: message }));
  }
}

if (typeof window !== "undefined" && window.addEventListener) {
  window.addEventListener("popstate", () => {
    if (!state.package) return;
    applyActivityDeepLink(state.package.activities);
    render();
  });
}

localeSelector.addEventListener("change", (event) => {
  state.locale = event.target.value;
  if (!state.loading && state.package) render();
});
loadPackage();
