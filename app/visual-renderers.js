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
  });
})(globalThis);
