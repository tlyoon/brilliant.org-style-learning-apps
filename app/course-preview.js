/* Local instructor preview only: no course progression, student identity, or release. */
"use strict";
(function initCoursePreview() {
  const root = document.querySelector("#course-preview");
  if (!root) return;
  const selector = document.querySelector("#course-select");
  const notice = document.querySelector("#course-status");
  const language = document.querySelector("#locale");
  if (!selector || !notice || !language) return;
  const labels = {
    en: { choose: "Choose a subchapter", ready: "Select a section to inspect its draft activities.", absent: "No local pilot roster has been configured.", invalid: "Pilot roster unavailable or invalid. No package was loaded.", selected: "Instructor preview of section", note: "Not verified for classroom use or publication." },
    ms: { choose: "Pilih subbab", ready: "Pilih bahagian untuk melihat aktiviti draf.", absent: "Tiada senarai rintis tempatan dikonfigurasikan.", invalid: "Senarai rintis tiada atau tidak sah. Tiada pakej dimuatkan.", selected: "Pratonton pensyarah untuk bahagian", note: "Belum disahkan untuk kelas atau penerbitan." },
    zh: { choose: "选择小节", ready: "选择一个小节以查看草稿活动。", absent: "尚未配置本地试点清单。", invalid: "试点清单不可用或无效，未加载任何学习包。", selected: "教师预览小节", note: "尚未获准用于课堂或发布。" },
  };
  const message = () => labels[language.value] || labels.en;
  let available = new Map();
  let currentSelection = "";
  let currentChapter = 0;
  let state = "absent";
  const permittedManifest = /^\.\.\/local-pilot\/[a-z0-9][a-z0-9-]{0,79}\.json$/;
  const packagePath = /^content\/chapter-([1-9][0-9]*)\/section-([1-9][0-9]*)-([1-9][0-9]*)\/package\.json$/;
  const digest = /^[a-f0-9]{64}$/;
  const gitSha = /^[a-f0-9]{40}$/;
  const identity = /^sourcefree-pilot-[a-z0-9-]{3,60}$/;

  function exactKeys(obj, keys) {
    return obj !== null && typeof obj === "object" && !Array.isArray(obj)
      && Object.keys(obj).length === keys.length
      && keys.every((key) => Object.prototype.hasOwnProperty.call(obj, key));
  }

  function validRoster(data) {
    const fields = ["scopeId", "baselineGitSha", "chapterNumber", "mode", "cases",
      "modelCallsAllowed", "pdfReadsAllowed", "publicationAllowed"];
    const caseFields = ["sectionNumber", "packagePath", "packageSha256"];
    if (!exactKeys(data, fields) || typeof data.scopeId !== "string"
      || !identity.test(data.scopeId) || typeof data.baselineGitSha !== "string"
      || !gitSha.test(data.baselineGitSha) || !Number.isSafeInteger(data.chapterNumber)
      || data.chapterNumber < 1 || data.mode !== "OFFLINE_EXISTING_PACKAGES_ONLY"
      || data.modelCallsAllowed !== false || data.pdfReadsAllowed !== false
      || data.publicationAllowed !== false || !Array.isArray(data.cases)
      || data.cases.length !== 6) return false;
    const sections = new Set(), paths = new Set(), hashes = new Set();
    for (const entry of data.cases) {
      if (!exactKeys(entry, caseFields) || !Number.isSafeInteger(entry.sectionNumber)
        || entry.sectionNumber < 1 || typeof entry.packagePath !== "string"
        || typeof entry.packageSha256 !== "string" || !digest.test(entry.packageSha256)) return false;
      const match = entry.packagePath.match(packagePath);
      if (!match || Number(match[1]) !== data.chapterNumber
        || Number(match[2]) !== data.chapterNumber
        || Number(match[3]) !== entry.sectionNumber) return false;
      const folded = entry.packagePath.toLowerCase();
      if (sections.has(entry.sectionNumber) || paths.has(folded)
        || hashes.has(entry.packageSha256)) return false;
      sections.add(entry.sectionNumber);
      paths.add(folded);
      hashes.add(entry.packageSha256);
    }
    return true;
  }

  function rerenderMenu() {
    selector.replaceChildren();
    const initial = document.createElement("option");
    initial.value = "";
    initial.textContent = message().choose;
    selector.append(initial);
    for (const [section] of available) {
      const option = document.createElement("option");
      option.value = String(section);
      option.textContent = String(currentChapter) + "." + String(section);
      selector.append(option);
    }
    selector.value = currentSelection;
    selector.disabled = available.size !== 6;
    if (state === "selected") {
      notice.textContent = message().selected + " " + currentChapter + "." + currentSelection + ". " + message().note;
    } else {
      notice.textContent = message()[state] || message().invalid;
    }
  }

  selector.addEventListener("change", () => {
    const section = Number(selector.value);
    const entry = available.get(section);
    if (!selector.value || !entry || typeof loadPackage !== "function") {
      currentSelection = "";
      state = "ready";
      rerenderMenu();
      // Invalidate any in-flight fetch and remove the previous section's
      // practice state; an unselected course menu must not show old mastery.
      if (typeof loadPackage === "function") void loadPackage();
      return;
    }
    currentSelection = selector.value;
    state = "selected";
    rerenderMenu();
    // The existing learner remains single-package, in-memory and no-login.
    // Exact bytes are verified by loadPackage before activity rendering.
    void loadPackage("../" + entry.packagePath, entry.packageSha256);
  });
  language.addEventListener("change", rerenderMenu);

  const url = root.dataset.manifestUrl || "";
  if (!permittedManifest.test(url)) {
    state = "absent";
    rerenderMenu();
    return;
  }
  state = "invalid";
  rerenderMenu();
  Promise.resolve().then(async () => {
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) throw new Error("roster fetch failed");
      const data = await response.json();
      if (!validRoster(data)) throw new Error("roster scope is invalid");
      available = new Map(data.cases
        .map((entry) => [entry.sectionNumber, entry])
        .sort((a, b) => a[0] - b[0]));
      currentChapter = data.chapterNumber;
      state = "ready";
    } catch (_error) {
      available = new Map();
      state = "invalid";
    }
    rerenderMenu();
  });
})();
