(function (global) {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";
  const RENDERER_VERSION = "1.0.0";
  const VIEWBOX = "0 0 640 360";
  let renderSequence = 0;

  const TEMPLATE_RENDERERS = Object.freeze({
    "mechanics.cart_collision_1d": renderCartCollision,
    "mechanics.free_body_2d": renderFreeBody,
    "graph.cartesian_qualitative": renderQualitativeGraph,
    "state.energy_bar": renderEnergyBars,
    "mechanics.motion_1d_slider": renderMotion1DSimulation,
  });

  function localized(value, locale) {
    if (typeof value === "string") return value;
    if (!value || typeof value !== "object") return "";
    return value[locale] ?? value.en ?? Object.values(value).find((item) => typeof item === "string") ?? "";
  }

  function createElement(documentRef, tag, className) {
    const node = documentRef.createElement(tag);
    if (className) node.className = className;
    return node;
  }

  function createSvgElement(documentRef, tag, attributes = {}, text) {
    const node = documentRef.createElementNS
      ? documentRef.createElementNS(SVG_NS, tag)
      : documentRef.createElement(tag);
    for (const [name, value] of Object.entries(attributes)) {
      if (value !== undefined && value !== null) node.setAttribute(name, String(value));
    }
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function clamp(value, low, high) {
    return Math.min(high, Math.max(low, value));
  }

  function semanticLabel(item, locale, fallback = "") {
    return localized(item?.label, locale) || fallback || item?.id || "";
  }

  function addSvgText(svg, documentRef, x, y, text, className, anchor = "middle") {
    if (!text) return null;
    const node = createSvgElement(documentRef, "text", {
      x, y, class: className, "text-anchor": anchor, "dominant-baseline": "middle",
    }, text);
    svg.append(node);
    return node;
  }

  function addMarkerDefinitions(svg, documentRef, prefix) {
    const defs = createSvgElement(documentRef, "defs");
    const marker = createSvgElement(documentRef, "marker", {
      id: `${prefix}-arrow`, viewBox: "0 0 10 10", refX: "8.5", refY: "5",
      markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse",
    });
    marker.append(createSvgElement(documentRef, "path", { d: "M 0 0 L 10 5 L 0 10 z", class: "physics-visual__arrowhead" }));
    defs.append(marker);

    const pattern = createSvgElement(documentRef, "pattern", {
      id: `${prefix}-hatch`, width: "10", height: "10", patternUnits: "userSpaceOnUse",
      patternTransform: "rotate(45)",
    });
    pattern.append(createSvgElement(documentRef, "line", {
      x1: "0", y1: "0", x2: "0", y2: "10", class: "physics-visual__hatch-line",
    }));
    defs.append(pattern);
    svg.append(defs);
  }

  function vectorUnit(direction) {
    const root = Math.SQRT1_2;
    const map = {
      left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1],
      "up-left": [-root, -root], "up-right": [root, -root],
      "down-left": [-root, root], "down-right": [root, root],
      "positive-x": [1, 0], "negative-x": [-1, 0],
      "positive-y": [0, -1], "negative-y": [0, 1],
      "radial-in": [-1, 0], "radial-out": [1, 0],
      "tangent-cw": [0, 1], "tangent-ccw": [0, -1],
    };
    return map[direction] ?? [1, 0];
  }

  function drawVector(svg, documentRef, vector, origin, prefix, locale, index = 0) {
    const [dx, dy] = vectorUnit(vector.direction);
    const magnitude = clamp(Number(vector.relativeMagnitude ?? 0.65), 0.15, 1);
    const length = 58 + magnitude * 72;
    const end = [origin[0] + dx * length, origin[1] + dy * length];
    const line = createSvgElement(documentRef, "line", {
      x1: origin[0], y1: origin[1], x2: end[0], y2: end[1],
      class: `physics-visual__vector physics-visual__vector--${index % 4}`,
      "marker-end": `url(#${prefix}-arrow)`,
      "data-semantic-id": vector.id,
    });
    svg.append(line);
    const label = semanticLabel(vector, locale, vector.quantity);
    const labelX = end[0] + dx * 13 + (Math.abs(dy) > 0.3 ? 10 : 0);
    const labelY = end[1] + dy * 13 - (Math.abs(dx) > 0.3 ? 10 : 0);
    addSvgText(svg, documentRef, labelX, labelY, label, "physics-visual__vector-label");
  }

  function makeSurface(spec, options) {
    const documentRef = options.document ?? global.document;
    if (!documentRef) throw new Error("A document is required to render physics visuals");
    const figure = createElement(documentRef, "figure", `physics-visual physics-visual--${spec.mode}`);
    figure.setAttribute("data-template", spec.template ?? "");
    figure.setAttribute("data-renderer-version", RENDERER_VERSION);
    const description = localized(spec.accessibility?.description, options.locale ?? "en") || "Physics diagram";
    figure.setAttribute("role", "group");
    figure.setAttribute("aria-label", description);

    const stage = createElement(documentRef, "div", "physics-visual__stage");
    if (options.baseLayer) {
      const contextLayer = createElement(documentRef, "div", "physics-visual__context");
      contextLayer.setAttribute("aria-hidden", "true");
      contextLayer.append(options.baseLayer);
      stage.append(contextLayer);
    }
    const svg = createSvgElement(documentRef, "svg", {
      class: "physics-visual__svg", viewBox: VIEWBOX, preserveAspectRatio: "xMidYMid meet",
      "aria-hidden": "true", focusable: "false",
    });
    stage.append(svg);
    figure.append(stage);
    return { documentRef, figure, svg };
  }

  function renderCartCollision(spec, options) {
    const { documentRef, figure, svg } = makeSurface(spec, options);
    const prefix = `pv-${++renderSequence}`;
    addMarkerDefinitions(svg, documentRef, prefix);

    const phase = String(spec.semanticParameters?.phase ?? "").replace(/[-_]/g, " ");
    if (phase) addSvgText(svg, documentRef, 40, 35, phase, "physics-visual__phase", "start");

    svg.append(createSvgElement(documentRef, "line", { x1: "45", y1: "255", x2: "595", y2: "255", class: "physics-visual__track" }));
    for (let x = 65; x <= 575; x += 34) {
      svg.append(createSvgElement(documentRef, "line", { x1: x, y1: "263", x2: x + 14, y2: "275", class: "physics-visual__track-tie" }));
    }

    const carts = (spec.entities ?? []).filter((entity) => entity.kind === "cart" || entity.kind === "body");
    const visibleCarts = carts.length ? carts.slice(0, 4) : (spec.entities ?? []).slice(0, 4);
    const count = Math.max(visibleCarts.length, 1);
    const anchors = new Map();
    visibleCarts.forEach((cart, index) => {
      const x = count === 1 ? 320 : 150 + index * (340 / (count - 1));
      const y = 225;
      anchors.set(cart.id, [x, y - 30]);
      const group = createSvgElement(documentRef, "g", { "data-semantic-id": cart.id, class: "physics-visual__cart" });
      group.append(createSvgElement(documentRef, "rect", { x: x - 54, y: y - 52, width: "108", height: "54", rx: "15", class: "physics-visual__cart-body" }));
      group.append(createSvgElement(documentRef, "rect", { x: x - 43, y: y - 41, width: "86", height: "7", rx: "3.5", class: "physics-visual__cart-highlight" }));
      group.append(createSvgElement(documentRef, "circle", { cx: x - 31, cy: y + 5, r: "12", class: "physics-visual__wheel" }));
      group.append(createSvgElement(documentRef, "circle", { cx: x + 31, cy: y + 5, r: "12", class: "physics-visual__wheel" }));
      svg.append(group);
      addSvgText(svg, documentRef, x, y - 70, semanticLabel(cart, options.locale, cart.id), "physics-visual__entity-label");
    });

    (spec.vectors ?? []).forEach((vector, index) => {
      const origin = anchors.get(vector.entityId);
      if (origin) drawVector(svg, documentRef, vector, origin, prefix, options.locale, index);
    });
    return figure;
  }

  function renderFreeBody(spec, options) {
    const { documentRef, figure, svg } = makeSurface(spec, options);
    const prefix = `pv-${++renderSequence}`;
    addMarkerDefinitions(svg, documentRef, prefix);
    const entity = (spec.entities ?? [])[0];
    const center = [320, 185];

    svg.append(createSvgElement(documentRef, "line", { x1: "95", y1: center[1], x2: "545", y2: center[1], class: "physics-visual__reference-axis" }));
    svg.append(createSvgElement(documentRef, "line", { x1: center[0], y1: "45", x2: center[0], y2: "320", class: "physics-visual__reference-axis" }));
    const body = createSvgElement(documentRef, "g", { "data-semantic-id": entity?.id ?? "body", class: "physics-visual__body" });
    body.append(createSvgElement(documentRef, "rect", { x: "272", y: "148", width: "96", height: "74", rx: "20", class: "physics-visual__body-shape" }));
    svg.append(body);
    addSvgText(svg, documentRef, center[0], center[1], semanticLabel(entity, options.locale, "object"), "physics-visual__body-label");

    (spec.vectors ?? []).forEach((vector, index) => {
      drawVector(svg, documentRef, vector, center, prefix, options.locale, index);
    });
    return figure;
  }

  function graphPath(shape) {
    const points = [];
    if (shape === "sinusoidal") {
      for (let i = 0; i <= 48; i += 1) {
        const t = i / 48;
        points.push([110 + 430 * t, 180 - 82 * Math.sin(t * Math.PI * 2)]);
      }
      return points.map(([x, y], index) => `${index ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
    }
    const paths = {
      constant: "M110 170 L540 170",
      "increasing-linear": "M110 265 L540 85",
      "decreasing-linear": "M110 85 L540 265",
      proportional: "M92 290 L545 65",
      "parabolic-up": "M110 85 Q320 325 540 85",
      "parabolic-down": "M110 265 Q320 25 540 265",
      inverse: "M120 75 C170 85 205 125 245 250 M350 85 C390 150 455 220 540 250",
      "exponential-growth": "M110 265 C300 260 440 225 540 70",
      "exponential-decay": "M110 70 C215 190 345 245 540 265",
      piecewise: "M110 245 L235 185 L320 185 M350 140 L455 95 L540 95",
    };
    return paths[shape] ?? paths.constant;
  }

  function renderQualitativeGraph(spec, options) {
    const { documentRef, figure, svg } = makeSurface(spec, options);
    const prefix = `pv-${++renderSequence}`;
    addMarkerDefinitions(svg, documentRef, prefix);
    const xAxis = (spec.axes ?? []).find((axis) => axis.role === "x");
    const yAxis = (spec.axes ?? []).find((axis) => axis.role === "y");

    for (const y of [80, 130, 180, 230]) svg.append(createSvgElement(documentRef, "line", { x1: "90", y1: y, x2: "560", y2: y, class: "physics-visual__grid" }));
    for (const x of [170, 250, 330, 410, 490]) svg.append(createSvgElement(documentRef, "line", { x1: x, y1: "50", x2: x, y2: "290", class: "physics-visual__grid" }));
    svg.append(createSvgElement(documentRef, "line", { x1: "90", y1: "290", x2: "570", y2: "290", class: "physics-visual__axis", "marker-end": `url(#${prefix}-arrow)` }));
    svg.append(createSvgElement(documentRef, "line", { x1: "90", y1: "300", x2: "90", y2: "45", class: "physics-visual__axis", "marker-end": `url(#${prefix}-arrow)` }));
    addSvgText(svg, documentRef, 548, 323, `${semanticLabel(xAxis, options.locale, xAxis?.quantity ?? "x")}${xAxis?.unit ? ` (${xAxis.unit})` : ""}`, "physics-visual__axis-label", "end");
    addSvgText(svg, documentRef, 42, 60, `${semanticLabel(yAxis, options.locale, yAxis?.quantity ?? "y")}${yAxis?.unit ? ` (${yAxis.unit})` : ""}`, "physics-visual__axis-label", "start");

    (spec.graphSeries ?? []).forEach((series, index) => {
      svg.append(createSvgElement(documentRef, "path", {
        d: graphPath(series.shape),
        class: `physics-visual__series physics-visual__series--${index % 4}`,
        "data-semantic-id": series.id,
      }));
      const label = semanticLabel(series, options.locale);
      if (label) addSvgText(svg, documentRef, 535, 60 + index * 24, label, `physics-visual__legend physics-visual__legend--${index % 4}`, "end");
    });
    return figure;
  }

  function energyAmount(entity) {
    const value = Number(entity?.properties?.relativeAmount ?? entity?.properties?.amount ?? 0);
    return Number.isFinite(value) ? clamp(value, 0, 1) : 0;
  }

  function motionInitialState(spec) {
    const initial = (spec.states ?? []).find((state) => state.id === "initial-state");
    const values = initial?.values ?? {};
    return {
      position: Number(values.position ?? 0),
      velocity: Number(values.velocity ?? 0),
      time: Number(values.time ?? 0),
    };
  }

  function motionControl(spec, variableId) {
    return (spec.controls ?? []).find((control) => control.variableId === variableId);
  }

  function evaluateMotion1D(initialPosition, velocity, time) {
    const x0 = Number(initialPosition);
    const v = Number(velocity);
    const t = Number(time);
    if (![x0, v, t].every(Number.isFinite)) throw new Error("Motion state must be finite");
    return Object.freeze({ position: x0 + v * t, velocity: v, time: t });
  }

  function motionDomain(initialPosition, velocityControl, timeControl) {
    const vMin = Number(velocityControl?.min ?? 0);
    const vMax = Number(velocityControl?.max ?? 0);
    const tMin = Number(timeControl?.min ?? 0);
    const tMax = Number(timeControl?.max ?? 0);
    const candidates = [
      initialPosition,
      initialPosition + vMin * tMin,
      initialPosition + vMin * tMax,
      initialPosition + vMax * tMin,
      initialPosition + vMax * tMax,
    ].filter(Number.isFinite);
    let low = Math.min(...candidates);
    let high = Math.max(...candidates);
    if (low === high) { low -= 1; high += 1; }
    const padding = Math.max((high - low) * 0.08, 0.5);
    return [low - padding, high + padding];
  }

  function motionX(position, domain) {
    const fraction = (position - domain[0]) / (domain[1] - domain[0]);
    return 90 + clamp(fraction, 0, 1) * 460;
  }

  function appendMotionScene(svg, documentRef, spec, options, state, domain, prefix) {
    addMarkerDefinitions(svg, documentRef, prefix);
    svg.append(createSvgElement(documentRef, "line", { x1: "65", y1: "250", x2: "575", y2: "250", class: "physics-visual__track" }));
    for (let x = 80; x <= 555; x += 34) svg.append(createSvgElement(documentRef, "line", { x1: x, y1: "258", x2: x + 14, y2: "270", class: "physics-visual__track-tie" }));
    const cart = (spec.entities ?? [])[0];
    const x = motionX(state.position, domain);
    const group = createSvgElement(documentRef, "g", { "data-semantic-id": cart?.id ?? "cart", class: "physics-visual__cart" });
    group.append(createSvgElement(documentRef, "rect", { x: x - 50, y: "180", width: "100", height: "50", rx: "15", class: "physics-visual__cart-body" }));
    group.append(createSvgElement(documentRef, "circle", { cx: x - 29, cy: "237", r: "11", class: "physics-visual__wheel" }));
    group.append(createSvgElement(documentRef, "circle", { cx: x + 29, cy: "237", r: "11", class: "physics-visual__wheel" }));
    svg.append(group);
    addSvgText(svg, documentRef, x, 158, semanticLabel(cart, options.locale, "cart"), "physics-visual__entity-label");
    if (Math.abs(state.velocity) > 1e-12) {
      const direction = state.velocity > 0 ? "right" : "left";
      drawVector(svg, documentRef, {
        id: "motion-velocity-vector", entityId: cart?.id ?? "cart", quantity: "velocity",
        direction, relativeMagnitude: clamp(Math.abs(state.velocity) / 20, 0.2, 1),
        label: { en: "v", ms: "v", zh: "v" },
      }, [x, 165], prefix, options.locale, 0);
    }
    addSvgText(svg, documentRef, 78, 38, `x = ${state.position.toFixed(2)}`, "physics-visual__readout", "start");
    addSvgText(svg, documentRef, 78, 64, `v = ${state.velocity.toFixed(2)}`, "physics-visual__readout", "start");
    addSvgText(svg, documentRef, 78, 90, `t = ${state.time.toFixed(2)}`, "physics-visual__readout", "start");
  }

  function renderMotion1DStatic(spec, options = {}) {
    const { documentRef, figure, svg } = makeSurface(spec, options);
    figure.setAttribute("data-simulation-fallback", "static");
    const initial = motionInitialState(spec);
    const velocityControl = motionControl(spec, "velocity");
    const timeControl = motionControl(spec, "time");
    const domain = motionDomain(initial.position, velocityControl, timeControl);
    appendMotionScene(svg, documentRef, spec, options, evaluateMotion1D(initial.position, initial.velocity, initial.time), domain, `pv-${++renderSequence}`);
    return figure;
  }

  function makeRangeControl(documentRef, control, locale, onInput) {
    const wrapper = createElement(documentRef, "div", "physics-sim__control");
    const label = createElement(documentRef, "label", "physics-sim__label");
    const inputId = `physics-sim-${++renderSequence}-${control.id}`;
    label.setAttribute("for", inputId);
    label.textContent = semanticLabel(control, locale, control.variableId);
    const value = createElement(documentRef, "output", "physics-sim__value");
    const input = createElement(documentRef, "input", "physics-sim__range");
    input.setAttribute("id", inputId);
    input.setAttribute("type", "range");
    input.setAttribute("min", control.min);
    input.setAttribute("max", control.max);
    input.setAttribute("step", control.step);
    input.value = String(control.default);
    input.setAttribute("aria-label", semanticLabel(control, locale, control.variableId));
    const sync = () => {
      const numeric = Number(input.value);
      value.textContent = `${Number.isFinite(numeric) ? numeric : control.default}${control.unit ? ` ${control.unit}` : ""}`;
      onInput(Number.isFinite(numeric) ? numeric : Number(control.default));
    };
    input.addEventListener("input", sync);
    value.textContent = `${control.default}${control.unit ? ` ${control.unit}` : ""}`;
    wrapper.append(label, value, input);
    return { wrapper, input, value };
  }

  function renderMotion1DSimulation(spec, options) {
    if (options.forceStatic) return renderMotion1DStatic(spec, options);
    const { documentRef, figure, svg } = makeSurface(spec, options);
    figure.setAttribute("data-simulation-model", spec.simulation?.modelId ?? "");
    figure.setAttribute("data-simulation-version", "1.0.0");
    const initial = motionInitialState(spec);
    const velocityControl = motionControl(spec, "velocity");
    const timeControl = motionControl(spec, "time");
    const domain = motionDomain(initial.position, velocityControl, timeControl);
    const live = { velocity: Number(velocityControl?.default ?? initial.velocity), time: Number(timeControl?.default ?? initial.time) };
    const redraw = () => {
      if (typeof svg.replaceChildren === "function") svg.replaceChildren();
      else while (svg.children?.length) svg.children.pop();
      const state = evaluateMotion1D(initial.position, live.velocity, live.time);
      appendMotionScene(svg, documentRef, spec, options, state, domain, `pv-${++renderSequence}`);
      figure.setAttribute("data-position", state.position.toFixed(6));
      figure.setAttribute("data-velocity", state.velocity.toFixed(6));
      figure.setAttribute("data-time", state.time.toFixed(6));
    };
    const controls = createElement(documentRef, "div", "physics-sim__controls");
    controls.setAttribute("role", "group");
    controls.setAttribute("aria-label", localized(spec.accessibility?.description, options.locale ?? "en") || "Motion controls");
    const velocityUI = makeRangeControl(documentRef, velocityControl, options.locale, (value) => { live.velocity = value; redraw(); });
    const timeUI = makeRangeControl(documentRef, timeControl, options.locale, (value) => { live.time = value; redraw(); });
    controls.append(velocityUI.wrapper, timeUI.wrapper);
    figure.append(controls);
    redraw();
    return figure;
  }

  function renderEnergyBars(spec, options) {
    const { documentRef, figure, svg } = makeSurface(spec, options);
    const prefix = `pv-${++renderSequence}`;
    addMarkerDefinitions(svg, documentRef, prefix);
    const components = (spec.entities ?? []).filter((entity) => entity.kind === "energy-component");
    const bars = components.length ? components : (spec.entities ?? []);
    const count = Math.max(bars.length, 1);
    const width = Math.min(82, 400 / count);
    const gap = Math.min(44, 180 / count + 12);
    const totalWidth = count * width + Math.max(0, count - 1) * gap;
    const startX = 320 - totalWidth / 2;
    svg.append(createSvgElement(documentRef, "line", { x1: "80", y1: "292", x2: "560", y2: "292", class: "physics-visual__energy-baseline" }));

    bars.forEach((entity, index) => {
      const amount = energyAmount(entity);
      const x = startX + index * (width + gap);
      const maxHeight = 185;
      const barHeight = Math.max(6, amount * maxHeight);
      const y = 286 - barHeight;
      svg.append(createSvgElement(documentRef, "rect", { x, y: "101", width, height: "185", rx: "14", class: "physics-visual__energy-track" }));
      const fill = createSvgElement(documentRef, "rect", { x, y, width, height: barHeight, rx: "12", class: `physics-visual__energy-fill physics-visual__energy-fill--${index % 4}`, "data-semantic-id": entity.id });
      svg.append(fill);
      if (index % 2 === 1) svg.append(createSvgElement(documentRef, "rect", { x, y, width, height: barHeight, rx: "12", fill: `url(#${prefix}-hatch)`, class: "physics-visual__energy-pattern" }));
      addSvgText(svg, documentRef, x + width / 2, 320, semanticLabel(entity, options.locale, entity.id), "physics-visual__energy-label");
    });
    return figure;
  }

  function renderFallback(spec, options, message) {
    const documentRef = options.document ?? global.document;
    const fallback = createElement(documentRef, "div", "physics-visual physics-visual--fallback");
    fallback.setAttribute("role", "img");
    fallback.setAttribute("data-template", spec?.template ?? "");
    fallback.setAttribute("data-renderer-version", RENDERER_VERSION);
    const description = localized(spec?.accessibility?.description, options.locale ?? "en") || message || "Visual representation unavailable";
    fallback.setAttribute("aria-label", description);
    const text = createElement(documentRef, "p", "physics-visual__fallback-text");
    text.textContent = description;
    fallback.append(text);
    return fallback;
  }

  function renderVisualSpec(spec, options = {}) {
    if (!spec || typeof spec !== "object") return renderFallback(spec, options, "Visual representation unavailable");
    if (spec.schemaVersion !== "1.0") return renderFallback(spec, options, "Unsupported visual specification");
    const renderer = TEMPLATE_RENDERERS[spec.template];
    if (!renderer) return renderFallback(spec, options, "Unsupported visual template");
    try {
      return renderer(spec, options);
    } catch (_error) {
      if (spec.template === "mechanics.motion_1d_slider" && !options.forceStatic) {
        try { return renderMotion1DStatic(spec, options); } catch (_fallbackError) { /* use text fallback below */ }
      }
      return renderFallback(spec, options, "Visual representation unavailable");
    }
  }

  function renderDeterministicOverlay(spec, options = {}) {
    return renderVisualSpec(spec, { ...options, overlay: true });
  }

  global.PhysicsVisuals = Object.freeze({
    rendererVersion: RENDERER_VERSION,
    supportedTemplates: Object.freeze(Object.keys(TEMPLATE_RENDERERS)),
    renderVisualSpec,
    renderDeterministicOverlay,
    evaluateMotion1D,
  });
})(globalThis);
