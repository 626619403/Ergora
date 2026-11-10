import { node, button, pre, empty, row, badge, table } from "./ui.js";

// Private presentation of an already compiled preview. Paths identify instances;
// port nodes are display anchors, never additional workflow instances.
export function compositionGraphView(preview, session, agents, openDefinition) {
  const instances = new Map(preview.instances.map((item) => [item.path, item]));
  const agentMetadata = new Map(preview.instances.filter((item) => item.kind === "agent").map((item) => [item.path,
    agents.find((agent) => agent.id === item.ref.id && agent.version === item.ref.version && agent.digest === item.ref.digest)]));
  const folded = new Set(session.folded || []);
  const portId = (path, direction, name) => `port:${JSON.stringify([path, direction, name])}`;
  const elements = [], relations = [], sizes = new Map();
  let graph, disposed = false, positions = {}, matches = [];
  const container = node("div", { className: "graph composition-graph", role: "img", "aria-label": "已发布嵌套组合关系图" });
  const inspector = node("section", { className: "definition-details", "aria-label": "组合实例详情" });
  const selectedLabel = node("p", { role: "status" });
  const choices = new Map(), foldChoices = new Map();
  const relationInspector = node("section", { className: "definition-details", "aria-label": "原始组合关系", hidden: true });
  const searchStatus = node("p", { role: "status", "aria-label": "组合查找状态" });
  const searchResults = node("section", { "aria-label": "组合查找结果" });

  function edge(kind, source, target, label, facts) {
    const id = `edge:${elements.length}`;
    elements.push({ data: { id, source, target, label, kind }, classes: kind });
    relations.push({ id, kind, source, target, label, facts });
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

  const nodes = new Map(elements.filter((item) => item.data.path).map((item) => [item.data.id, item]));
  const searchTexts = new Map(preview.instances.map((item) => {
    const metadata = agentMetadata.get(item.path);
    return [item.path, [item.path, item.kind, item.role, item.review_requirement, item.ref?.id, item.ref?.version,
      JSON.stringify(item.backend_request || {}), ...(metadata?.specialties || []), ...(metadata?.roles || [])]
      .filter(Boolean).join(" ").toLocaleLowerCase()];
  }));

  // The outermost folded structural ancestor represents a hidden node or port.
  function representative(id) {
    let path = nodes.get(id).data.path, visible = id;
    while (path) {
      if (folded.has(path)) visible = path;
      path = instances.get(path).parent;
    }
    return visible;
  }

  function visibleElements(savedPositions) {
    return elements.flatMap((item) => {
      const data = { ...item.data };
      if (data.path) {
        if (representative(data.id) !== data.id) return [];
        if (folded.has(data.id)) data.label += "\n已折叠";
        return [{ data, classes: item.classes + (folded.has(data.id) ? " collapsed" : ""),
          position: (savedPositions && session.positions?.[data.id]) || positions[data.id] }];
      }
      const source = representative(data.source), target = representative(data.target);
      if (source === target) return [];
      const summary = source !== data.source || target !== data.target;
      return [{ data: { ...data, source, target, label: (summary ? "摘要 · " : "") + data.label },
        classes: item.classes + (summary ? " summary" : "") }];
    });
  }

  // Use the compiler's levels, without deriving another dependency ordering.
  function measure(path) {
    const item = instances.get(path);
    let size = { width: 220, height: 100 };
    if (item.kind === "workflow" && !folded.has(path)) {
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
    if (item.kind !== "workflow" || folded.has(path)) { positions[path] = { x: x + size.width / 2, y: y + size.height / 2 }; return; }
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
  function arrange() {
    sizes.clear();
    positions = {};
    measure("root");
    place("root", 0, 0);
  }
  arrange();

  function updateSelection() {
    const path = session.selected, visible = representative(path), item = instances.get(path);
    selectedLabel.textContent = `所选实例：${path}` + (visible === path ? "" : `；画布代表：${visible}（已折叠）`);
    for (const [key, choice] of choices) choice.setAttribute("aria-pressed", String(key === path));
    selectedFold.disabled = item.kind !== "workflow" || path === "root";
    selectedFold.textContent = folded.has(path) ? "展开所选子工作流" : "折叠所选子工作流";
    if (graph) {
      graph.nodes().removeClass("selected");
      graph.getElementById(visible).addClass("selected");
    }
  }

  function selectInstance(path) {
    session.selected = path;
    const item = instances.get(path);
    const metadata = agentMetadata.get(path);
    updateSelection();
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

  function inspectRelation(id) {
    const { facts, ...relation } = relations.find((item) => item.id === id);
    relationInspector.hidden = false;
    relationInspector.replaceChildren(node("h3", {}, `原始关系 ${id}`),
      pre({ ...relation, source_label: facts[0], target_label: facts[1], binding: facts[2] }));
  }

  function refreshSearch() {
    const terms = (session.query || "").trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    matches = terms.length ? preview.instances.filter((item) => terms.every((term) => searchTexts.get(item.path).includes(term))).map((item) => item.path) : [];
    const missing = [...agentMetadata.values()].filter((item) => !item).length;
    const hidden = matches.filter((path) => representative(path) !== path).length;
    searchStatus.textContent = (terms.length ? `${matches.length} 个匹配，${hidden} 个在折叠组内。` : "输入字面词项查找；多个词项需同时匹配，不区分大小写。") +
      (missing ? ` ${missing} 个 Agent 缺少精确索引元数据，仍可查原preview字段；未推断其专长。` : "");
    previousMatch.disabled = nextMatch.disabled = matches.length === 0;
    searchResults.replaceChildren(terms.length ? table(["展开祖先并定位", "职责 / 类型", "后端请求", "精确专长"], matches.map((path) => {
      const item = instances.get(path);
      return [button(`展开祖先并定位 ${path}`, () => locate(path), "text-button"), item.role || item.kind,
        item.backend_request?.tool || "—", agentMetadata.get(path)?.specialties?.join(", ") || "—"];
    })) : empty("查找保留所有未匹配实例和关系；图中高亮匹配实例及包含匹配的折叠组。"));
    if (graph) {
      graph.nodes().removeClass("match contains-match");
      for (const path of matches) {
        const visible = representative(path);
        graph.getElementById(visible).addClass(visible === path ? "match" : "contains-match");
      }
    }
  }

  function rebuild() {
    session.folded = [...folded];
    arrange();
    if (graph) {
      graph.batch(() => { graph.elements().remove(); graph.add(visibleElements(false)); });
      graph.resize().fit(undefined, 35);
      remember();
    } else {
      session.positions = session.zoom = session.pan = undefined;
    }
    for (const [path, choice] of foldChoices) {
      choice.textContent = `${folded.has(path) ? "展开" : "折叠"} ${path}`;
      choice.setAttribute("aria-expanded", String(!folded.has(path)));
    }
    expandAll.disabled = folded.size === 0;
    refreshSearch();
    updateSelection();
  }

  function toggleFold(path) {
    if (folded.has(path)) folded.delete(path);
    else folded.add(path);
    rebuild();
  }

  function locate(path) {
    let parent = instances.get(path).parent, changed = false;
    while (parent) {
      changed = folded.delete(parent) || changed;
      parent = instances.get(parent).parent;
    }
    if (changed) rebuild();
    selectInstance(path);
    if (graph) graph.resize().fit(graph.getElementById(path), 65);
  }

  function navigateMatch(direction) {
    const current = matches.indexOf(session.selected);
    const index = current < 0 ? (direction > 0 ? 0 : matches.length - 1) : (current + direction + matches.length) % matches.length;
    locate(matches[index]);
  }

  const selectedFold = button("折叠所选子工作流", () => toggleFold(session.selected));
  const expandAll = button("展开所有子工作流", () => { folded.clear(); rebuild(); }, "secondary", { disabled: folded.size === 0 });
  const previousMatch = button("上一个匹配", () => navigateMatch(-1));
  const nextMatch = button("下一个匹配", () => navigateMatch(1));
  const searchInput = node("input", { type: "search", value: session.query || "", oninput: (event) => {
    session.query = event.target.value;
    refreshSearch();
  } });
  const instanceTable = table(["实例路径 / 选择", "职能 / 类型", "后端请求", "结构父级", "先行依赖", "子工作流显示"], preview.instances.map((item) => {
    const choice = button(item.path, () => selectInstance(item.path), "text-button", { "aria-pressed": "false" });
    choices.set(item.path, choice);
    let foldChoice = "—";
    if (item.kind === "workflow" && item.parent) {
      foldChoice = button(`${folded.has(item.path) ? "展开" : "折叠"} ${item.path}`, () => toggleFold(item.path), "text-button", { "aria-expanded": String(!folded.has(item.path)) });
      foldChoices.set(item.path, foldChoice);
    }
    return [choice, item.role || item.kind, item.backend_request?.tool || "—", item.parent || "根", item.depends_on.join("\n") || "—", foldChoice];
  }));
  selectInstance(instances.has(session.selected) ? session.selected : "root");
  refreshSearch();
  const element = node("div", {},
    row(badge("嵌套框：结构继承"), badge("虚线箭头：先行依赖"), badge("蓝色实线：具名数据"), badge("入 / 出：工作流端口")),
    row(button("适配组合图", () => graph?.resize().fit(undefined, 35)),
      button("定位所选实例", () => locate(session.selected)), button("重排组合图", rebuild), selectedFold, expandAll), container,
    node("p", { className: "muted" }, "折叠 / 展开按原层级重排当前视图。摘要线只代表原跨组关系，点击连线或下方关系ID可查原始端点；组内关系仍在完整表中。拖动、缩放、折叠和查找只属于本页会话，刷新重置。图不修改草稿、依赖或权限。端口不是额外实例，连线不是运行值。"),
    node("label", {}, "查找实例（路径、职责、专长、后端）", searchInput),
    row(previousMatch, nextMatch, button("清除组合查找", () => { searchInput.value = session.query = ""; refreshSearch(); })),
    searchStatus, searchResults, instanceTable, selectedLabel, inspector, relationInspector,
    node("details", {}, node("summary", {}, "依赖与具名数据关系表"),
      table(["原关系ID / 查看", "关系", "来源", "目标", "原绑定"], relations.map((item) => [button(item.id, () => inspectRelation(item.id), "text-button"),
        item.kind === "dependency" ? "先行依赖" : "具名数据", ...item.facts]))));

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
        elements: visibleElements(true),
        layout: { name: "preset", padding: 35 },
        style: [
          { selector: "node", style: { shape: "round-rectangle", width: 190, height: 65,
            "background-color": "#e7f1e9", "border-color": "#98b38d", "border-width": 1,
            label: "data(label)", "font-size": 12, color: "#20342f", "text-valign": "center", "text-wrap": "wrap", "text-max-width": 180 } },
          { selector: "node.workflow", style: { "background-opacity": 0.12, padding: 30, "text-valign": "top", "text-halign": "left", "text-margin-x": 12, "text-margin-y": 25 } },
          { selector: "node.join", style: { shape: "diamond", width: 90, "background-color": "#f1e6cf" } },
          { selector: "node.port", style: { width: 90, height: 30, "background-color": "#e2edf8", "font-size": 11 } },
          { selector: "node.collapsed", style: { width: 210, height: 85, "background-opacity": 1, "text-valign": "center", "text-halign": "center", "text-margin-x": 0, "text-margin-y": 0 } },
          { selector: "node.match", style: { "border-width": 4, "border-color": "#b56721" } },
          { selector: "node.contains-match", style: { "border-width": 4, "border-color": "#b56721", "border-style": "dashed" } },
          { selector: "node.selected", style: { "border-width": 3, "border-color": "#23664e" } },
          { selector: "edge", style: { width: 1.5, "curve-style": "bezier", "target-arrow-shape": "triangle", label: "data(label)", "font-size": 10, "text-background-color": "#f5f7f2", "text-background-opacity": 0.85, "text-background-padding": 2 } },
          { selector: "edge.dependency", style: { "line-style": "dashed", "line-color": "#9b7046", "target-arrow-color": "#9b7046", color: "#79522e" } },
          { selector: "edge.data", style: { "line-color": "#527fa3", "target-arrow-color": "#527fa3", color: "#345f81" } },
          { selector: "edge.summary", style: { width: 2.5 } },
        ],
      });
      if (session.zoom !== undefined) { graph.zoom(session.zoom); graph.pan(session.pan); }
      updateSelection();
      refreshSearch();
      graph.on("tap", "node", (event) => selectInstance(event.target.data("path")));
      graph.on("tap", "edge", (event) => inspectRelation(event.target.id()));
      graph.on("dragfree", remember);
      graph.on("pan zoom", () => { session.zoom = graph.zoom(); session.pan = { ...graph.pan() }; });
    },
    dispose() { remember(); graph?.destroy(); graph = null; disposed = true; },
  };
}
