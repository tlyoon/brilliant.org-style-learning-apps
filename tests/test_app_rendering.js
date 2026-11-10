const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName.toUpperCase();
    this.children = [];
    this.attributes = {};
    this.dataset = {};
    this.style = {};
    this.listeners = {};
    this.className = "";
    this.disabled = false;
    this._text = "";
  }

  set innerHTML(_value) {
    throw new Error("innerHTML must not be used by the learner application");
  }

  set textContent(value) {
    this._text = String(value);
    this.children = [];
  }

  get textContent() {
    return this._text + this.children.map((child) => child.textContent).join("");
  }

  append(...children) {
    this.children.push(...children);
  }

  replaceChildren(...children) {
    this._text = "";
    this.children = [...children];
  }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
  }

  addEventListener(name, listener) {
    this.listeners[name] = listener;
  }

  click() {
    this.listeners.click?.({ target: this });
  }
}

function descendants(root) {
  return [root, ...root.children.flatMap(descendants)];
}

function find(root, predicate) {
  return descendants(root).find(predicate);
}

const app = new FakeElement("section");
app.dataset.packageUrl = "test-package.json";
const locale = new FakeElement("select");
const malicious = {
  prompt: '<script>globalThis.__packageCodeExecuted = true</script>',
  option: '<img src=x onerror="globalThis.__packageCodeExecuted = true">',
  hint: "&lt;strong&gt;hint&lt;/strong&gt;",
  feedback: "2 < 3 &amp; 4 > 1",
  explanation: '<svg onload="globalThis.__packageCodeExecuted = true">The inelastic explanation is text only.</svg>',
  subchapter: "Vectors < scalars & entities",
};
const localized = (text) => ({ en: text, ms: text, zh: text });
const packageData = {
  subchapter: malicious.subchapter,
  activities: [{
    id: "safe-rendering-fixture",
    difficulty: "easy",
    prompt: localized(malicious.prompt),
    answerKey: {
      correct: "safe",
      options: [
        { id: "safe", label: localized(malicious.option) },
        { id: "other", label: localized("Ordinary <angle brackets>") },
      ],
    },
    hints: [localized(malicious.hint)],
    feedback: localized(malicious.feedback),
    explanation: {
      en: malicious.explanation,
      ms: "Penjelasan selepas jawapan betul.",
      zh: "\u6b63\u786e\u4f5c\u7b54\u540e\u7684\u89e3\u91ca\u3002",
    },
  }],
};

const context = {
  console,
  globalThis: null,
  document: {
    createElement: (tagName) => new FakeElement(tagName),
    querySelector: (selector) => selector === "#app" ? app : locale,
  },
  fetch: async () => ({ ok: true, json: async () => packageData }),
};
context.globalThis = context;
context.__packageCodeExecuted = false;
vm.runInNewContext(fs.readFileSync("app/app.js", "utf8"), context, { filename: "app/app.js" });

setImmediate(() => {
  assert.equal(context.__packageCodeExecuted, false);
  assert.equal(find(app, (node) => node.tagName === "H1").textContent, malicious.prompt);
  assert.equal(find(app, (node) => node.className === "choice").textContent, malicious.option);
  assert.equal(descendants(app).some((node) => ["SCRIPT", "IMG"].includes(node.tagName)), false);

  assert.equal(find(app, (node) => node.className === "scientific-reasoning"), undefined);
  find(app, (node) => node.id === "hint").click();
  assert.equal(find(app, (node) => node.className === "feedback").textContent, malicious.hint);

  assert.equal(find(app, (node) => node.className === "scientific-reasoning"), undefined);
  find(app, (node) => node.className === "choice" && node.dataset.value === "other").click();
  find(app, (node) => node.id === "check").click();
  assert.equal(find(app, (node) => node.className === "scientific-reasoning"), undefined);
  find(app, (node) => node.id === "check").click();

  find(app, (node) => node.className === "choice").click();
  find(app, (node) => node.id === "check").click();
  const feedback = descendants(app).filter((node) => node.className === "feedback").at(-1);
  assert.equal(feedback.textContent, `That reasoning fits. ${malicious.feedback}`);

  const reasoning = find(app, (node) => node.className === "scientific-reasoning");
  assert.ok(reasoning);
  assert.equal(find(reasoning, (node) => node.className === "reasoning-text").textContent,
               malicious.explanation);
  assert.equal(descendants(app).some((node) => node.tagName === "SVG"), false);
  assert.equal(context.__packageCodeExecuted, false);
  locale.listeners.change({ target: { value: "ms" } });
  assert.equal(find(app, (node) => node.className === "reasoning-title").textContent,
               "Mengapa jawapan ini betul");
  assert.equal(find(app, (node) => node.className === "reasoning-text").textContent,
               "Penjelasan selepas jawapan betul.");
  locale.listeners.change({ target: { value: "zh" } });
  assert.equal(find(app, (node) => node.className === "reasoning-text").textContent,
               "\u6b63\u786e\u4f5c\u7b54\u540e\u7684\u89e3\u91ca\u3002");
  locale.listeners.change({ target: { value: "en" } });

  find(app, (node) => node.id === "check").click();
  assert.equal(find(app, (node) => node.className === "eyebrow").textContent, malicious.subchapter);
  assert.equal(find(app, (node) => node.className === "scientific-reasoning"), undefined);
  assert.equal(context.__packageCodeExecuted, false);
  console.log("Package-controlled strings render as inert text.");
});
