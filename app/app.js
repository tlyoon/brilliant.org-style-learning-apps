const DEFAULT_PACKAGE = "../content/examples/conceptual-forces.json";
const state = { package: null, activityIndex: 0, locale: "en", selected: null, checked: false, hint: false };

const copy = {
  en: { activity: "Activity", of: "of", check: "Check answer", next: "Next activity", tryAgain: "Try again", restart: "Start again", hint: "Show a hint", complete: "Journey complete", correct: "That reasoning fits.", retry: "Reconsider the relationship and try again." },
  ms: { activity: "Aktiviti", of: "daripada", check: "Semak jawapan", next: "Aktiviti seterusnya", tryAgain: "Cuba lagi", restart: "Mula semula", hint: "Tunjukkan petunjuk", complete: "Perjalanan selesai", correct: "Penaakulan itu sesuai.", retry: "Pertimbangkan semula hubungan itu dan cuba lagi." },
  zh: { activity: "活动", of: "/", check: "检查答案", next: "下一个活动", tryAgain: "再试一次", restart: "重新开始", hint: "显示提示", complete: "学习旅程完成", correct: "这个推理是恰当的。", retry: "重新思考其中的关系，然后再试一次。" },
};

const localized = (value) => typeof value === "string" ? value : value?.[state.locale] ?? value?.en ?? "";

function resetActivity() {
  state.selected = null;
  state.checked = false;
  state.hint = false;
}

function render() {
  const root = document.querySelector("#app");
  const activities = state.package.activities;
  if (state.activityIndex >= activities.length) {
    root.innerHTML = `<section class="card"><p class="eyebrow">${localized(state.package.subchapter)}</p><h1>${copy[state.locale].complete}</h1><button class="action" id="restart">${copy[state.locale].restart}</button></section>`;
    document.querySelector("#restart").addEventListener("click", () => { state.activityIndex = 0; resetActivity(); render(); });
    return;
  }

  const activity = activities[state.activityIndex];
  const labels = copy[state.locale];
  const options = activity.answerKey.options;
  const feedback = state.checked
    ? `<div class="feedback" role="status">${state.selected === activity.answerKey.correct ? labels.correct : labels.retry} ${localized(activity.feedback)}</div>`
    : "";
  root.innerHTML = `
    <section class="card">
      <p class="eyebrow">${labels.activity} ${state.activityIndex + 1} ${labels.of} ${activities.length} · ${activity.difficulty}</p>
      <div class="progress" aria-label="Progress"><span style="width:${((state.activityIndex + 1) / activities.length) * 100}%"></span></div>
      <h1>${localized(activity.prompt)}</h1>
      <div class="choices">${options.map((option) => `<button class="choice" data-value="${option.id}" aria-pressed="${state.selected === option.id}">${localized(option.label)}</button>`).join("")}</div>
      ${state.hint ? `<div class="feedback">${localized(activity.hints[0])}</div>` : ""}
      ${feedback}
      <div class="choices">
        <button class="action" id="check" ${state.selected === null ? "disabled" : ""}>${state.checked ? (state.selected === activity.answerKey.correct ? labels.next : labels.tryAgain) : labels.check}</button>
        <button class="action secondary" id="hint">${labels.hint}</button>
      </div>
    </section>`;

  document.querySelectorAll(".choice").forEach((button) => button.addEventListener("click", () => { state.selected = button.dataset.value; state.checked = false; render(); }));
  document.querySelector("#hint").addEventListener("click", () => { state.hint = true; render(); });
  document.querySelector("#check").addEventListener("click", () => {
    if (!state.checked) state.checked = true;
    else if (state.selected === activity.answerKey.correct) { state.activityIndex += 1; resetActivity(); }
    else resetActivity();
    render();
  });
}

async function start() {
  try {
    const response = await fetch(DEFAULT_PACKAGE);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.package = await response.json();
    render();
  } catch (error) {
    document.querySelector("#app").innerHTML = `<p class="error">Could not load the example package. Start the app through the documented local server. (${error.message})</p>`;
  }
}

document.querySelector("#locale").addEventListener("change", (event) => { state.locale = event.target.value; render(); });
start();
