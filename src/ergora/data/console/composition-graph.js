import { node, button, pre, empty, row, badge, table } from "./ui.js";

// Private presentation of an already compiled preview. Paths identify instances;
// port nodes are display anchors, never additional workflow instances.
export function compositionGraphView(preview, session, agents, openDefinition) {
  const instances = new Map(preview.instances.map((item) => [item.path, item]));
  const portId = (path, direction, name) => `port:${JSON.stringify([path, direction, name])}`;
  const elements = [], relations = [], sizes = new Map(), positions = {};
  let graph, disposed = false;
  const container = node("div", { className: "graph composition-graph", role: "img", "aria-label": "已发布嵌套组合关系图" });
  const inspector = node("section", { className: "definition-details", "aria-label": "组合实例详情" });
  const selectedLabel = node("p", { role: "status" });
  const choices = new Map();

  function edge(kind, source, target, label, facts) {
    elements.push({ data: { id: `edge:${elements.length}`, source, target, label, kind }, classes: kind });
    relations.push([kind === "dependency" ? "先行依赖" : "具名数据", ...facts]);
  }

  function sourceOf(scope, binding) {
    if (binding.input !== undefined) return portId(scope, "input", binding.input);
    const source = instances.get(`${scope}/${binding.node}`);
    return source.kind === "workflow" ? portId(source.path, "output", binding.output) : source.path;
  }

  for (const item of preview.instances) {
    const name = item.path.split("/").pop();
    elements.push({ data: { id: item.path, parent: item.parent || undefined, path: item.path,
      label: `${name}\n${item.kind === "agent" ? `${item.role} · ${item.backend_request.tool}` : item.kind === "join" ? "all 汇合" : "子工作流"}` },
      classes: item.kind });
    if (item.kind === "workflow") {
      for (const [direction, ports] of [["input", item.inputs], ["output", item.outputs]])
        for (const name of Object.keys(ports)) elements.push({ data: {
          id: portId(item.path, direction, name), parent: item.path, path: item.path,
          label: `${direction === "input" ? "入" : "出"} · ${name}` }, classes: "port" });
    }
    for (const dependency of item.depends_on)
      edge("dependency", dependency, item.path, "先行", [dependency, item.path, "depends_on"]);
    if (item.parent) for (const [name, binding] of Object.entries(item.inputs || {})) {
      const target = item.kind === "workflow" ? portId(item.path, "input", name) : item.path;
      const from = binding.input !== undefined ? `${item.parent} · input.${binding.input}` : `${item.parent}/${binding.node} · output.${binding.output}`;
      edge("data", sourceOf(item.parent, binding), target,
        `${binding.input ?? binding.output} → ${name}`, [from, `${item.path} · input.${name}`, JSON.stringify(binding)]);
    }
    if (item.kind === "workflow") for (const [name, binding] of Object.entries(item.outputs)) {
      const from = binding.input !== undefined ? `${item.path} · input.${binding.input}` : `${item.path}/${binding.node} · output.${binding.output}`;
      edge("data", sourceOf(item.path, binding), portId(item.path, "output", name),
        `${binding.input ?? binding.output} → ${name}`, [from, `${item.path} · output.${name}`, JSON.stringify(binding)]);
    }
  }

  // Use the compiler's levels, without deriving another dependency ordering.
  function measure(path) {
    const item = instances.get(path);
    let size = { width: 220, height: 100 };
    if (item.kind === "workflow") {
      const columns = item.levels.map((level) => level.map(measure));
      size = { width: 360 + columns.reduce((sum, column) => sum + Math.max(...column.map((s) => s.width)) + 70, 0),
        height: 100 + Math.max(60 * Math.max(Object.keys(item.inputs).length, Object.keys(item.outputs).length),
          ...columns.map((column) => column.reduce((sum, s) => sum + s.height + 50, 0))) };
    }
    sizes.set(path, size);
    return size;
  }

  function place(path, x, y) {
    const item = instances.get(path), size = sizes.get(path);
    if (item.kind !== "workflow") { positions[path] = { x: x + size.width / 2, y: y + size.height / 2 }; return; }
    for (const [direction, ports] of [["input", item.inputs], ["output", item.outputs]])
      Object.keys(ports).forEach((name, index) => {
        positions[portId(path, direction, name)] = { x: direction === "input" ? x + 60 : x + size.width - 60, y: y + 100 + index * 60 };
      });
    let left = x + 180;
    for (const level of item.levels) {
      let top = y + 70;
      for (const child of level) { place(child, left, top); top += sizes.get(child).height + 50; }
      left += Math.max(...level.map((child) => sizes.get(child).width)) + 70;
    }
  }
  measure("root");
  place("root", 0, 0);

  function selectInstance(path) {
    session.selected = path;
    const item = instances.get(path);
    const metadata = item.kind === "agent" ? agents.find((agent) => agent.id === item.ref.id &&
      agent.version === item.ref.version && agent.digest === item.ref.digest) : null;
    selectedLabel.textContent = `所选实例：${path}`;
    for (const [key, choice] of choices) choice.setAttribute("aria-pressed", String(key === path));
    if (graph) {
      graph.nodes().removeClass("selected");
      graph.getElementById(path).addClass("selected");
    }
    const { resources, prompt, ...facts } = item;
    inspector.replaceChildren(...[node("h3", {}, path),
      row(item.ref ? button("打开所选精确定义", () => openDefinition(item.ref)) : null,
        item.parent ? button("打开结构父定义", () => openDefinition(instances.get(item.parent).ref)) : null),
      pre(facts), metadata ? pre({ specialties: metadata.specialties, declared_roles: metadata.roles }) : null,
      item.kind === "agent" && !metadata ? empty("该精确 Agent 的索引元数据不可用；原preview事实和完整材料仍在下方。") : null,
      ...(resources || []).map((resource) => node("details", {},
        node("summary", {}, `${resource.kind} · ${resource.ids.join(", ")}`),
        pre({ content_digest: resource.content_digest, sources: resource.sources }), pre(resource.text))),
      prompt === undefined ? empty("完整祖先材料在每个 Agent 叶实例中查看；此处展示原编译器的结构事实。") :
        node("details", {}, node("summary", {}, "完整装配后的提示正文"), pre(prompt))].filter(Boolean));
  }

  const instanceTable = table(["实例路径 / 选择", "职能 / 类型", "后端请求", "结构父级", "先行依赖"], preview.instances.map((item) => {
    const choice = button(item.path, () => selectInstance(item.path), "text-button", { "aria-pressed": "false" });
    choices.set(item.path, choice);
    return [choice, item.role || item.kind, item.backend_request?.tool || "—", item.parent || "根", item.depends_on.join("\n") || "—"];
  }));
  selectInstance(instances.has(session.selected) ? session.selected : "root");
  const element = node("div", {},
    row(badge("嵌套框：结构继承"), badge("虚线箭头：先行依赖"), badge("蓝色实线：具名数据"), badge("入 / 出：工作流端口")),
    row(button("适配组合图", () => graph?.resize().fit(undefined, 35)),
      button("定位所选实例", () => graph?.resize().fit(graph.getElementById(session.selected), 65)),
      button("重排组合图", () => {
        if (!graph) return;
        graph.nodes().filter((item) => !item.isParent()).positions((item) => positions[item.id()]);
        graph.resize().fit(undefined, 35);
      })), container,
    node("p", { className: "muted" }, "拖动、缩放和选择只改变本页布局；刷新后重新排布。图不修改草稿、依赖或权限。端口不是额外实例，连线不是运行值。"),
    instanceTable, selectedLabel, inspector,
    node("details", {}, node("summary", {}, "依赖与具名数据关系表"),
      table(["关系", "来源", "目标", "原绑定"], relations)));

  function remember() {
    if (!graph) return;
    session.positions = Object.fromEntries(graph.nodes().filter((item) => !item.isParent()).map((item) => [item.id(), { ...item.position() }]));
    session.zoom = graph.zoom();
    session.pan = { ...graph.pan() };
  }

  return { element,
    mount() {
      if (disposed || graph) return;
      if (!window.cytoscape) { container.append(empty("图组件未加载；请使用下方键盘实例表和完整详情。")); return; }
      graph = window.cytoscape({ container,
        elements: elements.map((item) => ({ ...item, position: session.positions?.[item.data.id] || positions[item.data.id] })),
        layout: { name: "preset", padding: 35 },
        style: [
          { selector: "node", style: { shape: "round-rectangle", width: 190, height: 65,
            "background-color": "#e7f1e9", "border-color": "#98b38d", "border-width": 1,
            label: "data(label)", "font-size": 12, color: "#20342f", "text-valign": "center", "text-wrap": "wrap", "text-max-width": 180 } },
          { selector: "node.workflow", style: { "background-opacity": 0.12, padding: 30, "text-valign": "top", "text-halign": "left", "text-margin-x": 12, "text-margin-y": 25 } },
          { selector: "node.join", style: { shape: "diamond", width: 90, "background-color": "#f1e6cf" } },
          { selector: "node.port", style: { width: 90, height: 30, "background-color": "#e2edf8", "font-size": 11 } },
          { selector: "node.selected", style: { "border-width": 3, "border-color": "#23664e" } },
          { selector: "edge", style: { width: 1.5, "curve-style": "bezier", "target-arrow-shape": "triangle", label: "data(label)", "font-size": 10, "text-background-color": "#f5f7f2", "text-background-opacity": 0.85, "text-background-padding": 2 } },
          { selector: "edge.dependency", style: { "line-style": "dashed", "line-color": "#9b7046", "target-arrow-color": "#9b7046", color: "#79522e" } },
          { selector: "edge.data", style: { "line-color": "#527fa3", "target-arrow-color": "#527fa3", color: "#345f81" } },
        ],
      });
      if (session.zoom !== undefined) { graph.zoom(session.zoom); graph.pan(session.pan); }
      graph.getElementById(session.selected).addClass("selected");
      graph.on("tap", "node", (event) => selectInstance(event.target.data("path")));
      graph.on("dragfree", remember);
      graph.on("pan zoom", () => { session.zoom = graph.zoom(); session.pan = { ...graph.pan() }; });
    },
    dispose() { remember(); graph?.destroy(); graph = null; disposed = true; },
  };
}
