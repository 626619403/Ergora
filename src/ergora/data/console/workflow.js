import { api } from "./api.js";
import {
  $, node, button, pre, lines, short, heading, panel, empty, row,
  select, field, badge, status, notify, form, modal, download, table,
} from "./ui.js";
import { app, bindingFor, stages } from "./state.js";

// One lifecycle owner: raw buffers and layout never become task inputs implicitly.
let workflowEpoch = 0, graph, graphSession, workflow;
const sessions = new Map();
const HISTORY_STEPS = 50, HISTORY_BYTES = 4 * 1024 * 1024;
const dictionary = (value = {}) => Object.assign(Object.create(null), value);
const textOf = (input) => JSON.stringify(input, null, 2);
const sessionKey = (project, home = app.bootstrap.state_directory) => JSON.stringify(["ergora-editor-v1", home, project]);
const pendingText = (current) => current.jsonText !== textOf(current.input) || Object.keys(current.unitBuffers).length > 0;
const changed = (current) => current.input && (pendingText(current) || textOf(current.input) !== current.cleanText || current.draftId !== current.cleanId);

function remember(current) {
  const key = sessionKey(current.project, current.controlDirectory);
  if (sessions.get(key) !== current) return;
  if (!current.input) return;
  const { history, historyIndex, request, storageError, ...buffer } = current;
  try {
    sessionStorage.setItem(key, JSON.stringify({ version: 1, ...buffer }));
    current.storageError = "";
  } catch (error) {
    current.storageError = `浏览器未能保存编辑缓冲：${error.message}。请保留此页并复制未完成的文本。`;
  }
}

function startSession(document, project) {
  const { agents, validation, ...details } = structuredClone(document);
  const current = { ...details, project, controlDirectory: app.bootstrap.state_directory, selected: 0, draftId: document.id,
    revisions: dictionary({ [document.id]: document.revision }), unitBuffers: dictionary(), layout: { positions: dictionary() }, request: null,
    cleanText: document.input ? textOf(document.input) : "", cleanId: document.id,
    jsonText: document.input ? textOf(document.input) : "", history: [], historyIndex: 0 };
  if (current.input) current.history.push({ text: current.jsonText, selected: 0, ids: current.input.work_units.map((unit) => unit.id), bytes: new TextEncoder().encode(current.jsonText).length });
  sessions.set(sessionKey(project, current.controlDirectory), current);
  return current;
}

function restoreSession(project) {
  const key = sessionKey(project);
  if (sessions.has(key)) return sessions.get(key);
  const raw = sessionStorage.getItem(key);
  if (!raw) return null;
  try {
    const { agents, validation, ...saved } = JSON.parse(raw);
    // This checks our browser checkpoint's renderable shape, not the task contract.
    if (saved.version !== 1 || saved.project !== project || saved.controlDirectory !== app.bootstrap.state_directory ||
        typeof saved.kind !== "string" || !Object.hasOwn(app.bootstrap.agent_contracts, saved.kind) || saved.kind === "training-optimization" ||
        !Number.isInteger(saved.selected) || saved.selected < 0 || !Array.isArray(saved.input?.work_units) || !saved.input.work_units.length ||
        !saved.input.work_units.every((unit) => typeof unit.id === "string" && typeof unit.instructions === "string" &&
          Array.isArray(unit.paths) && Array.isArray(unit.depends_on)) || typeof saved.jsonText !== "string" ||
        !saved.layout || !saved.layout.positions || !Object.values(saved.layout.positions).every((point) =>
          point && Number.isFinite(point.x) && Number.isFinite(point.y)) ||
        !saved.unitBuffers || typeof saved.unitBuffers !== "object" || !Object.values(saved.unitBuffers).every((item) =>
          item && typeof item.unit_id === "string" && typeof item.paths === "string" && typeof item.instructions === "string" && Array.isArray(item.depends_on))) throw new Error("编辑缓冲格式无法读取");
    const unitIds = new Set(saved.input.work_units.map((unit) => unit.id));
    if (Object.keys(saved.unitBuffers).some((id) => !unitIds.has(id))) throw new Error("编辑缓冲含有无法归属的单元文本");
    const current = { ...startSession(saved, project), ...saved, request: null, revisions: dictionary(saved.revisions), unitBuffers: dictionary(saved.unitBuffers),
      layout: { ...saved.layout, positions: dictionary(saved.layout?.positions) } };
    current.history = [{ text: textOf(current.input), selected: current.selected, ids: current.input.work_units.map((unit) => unit.id),
      bytes: new TextEncoder().encode(textOf(current.input)).length }];
    current.historyIndex = 0;
    sessions.set(key, current);
    return current;
  } catch (error) {
    return { project, restoreError: error.message, raw };
  }
}

function touched(current) {
  workflowEpoch++;
  remember(current);
}

function commitInput(current, input, selected, render) {
  current.history[current.historyIndex].selected = current.selected;
  const text = textOf(input);
  if (text !== current.history[current.historyIndex].text) {
    current.history.splice(current.historyIndex + 1);
    current.history.push({ text, selected, ids: input.work_units.map((unit) => unit.id), bytes: new TextEncoder().encode(text).length });
    let bytes = current.history.reduce((total, item) => total + item.bytes, 0);
    while (current.history.length > 1 && (current.history.length > HISTORY_STEPS || bytes > HISTORY_BYTES))
      bytes -= current.history.shift().bytes;
    current.historyIndex = current.history.length - 1;
  }
  const retained = new Set(current.history.flatMap((snapshot) => snapshot.ids));
  current.layout.positions = dictionary(Object.fromEntries(Object.entries(current.layout.positions).filter(([id]) => retained.has(id))));
  current.input = input;
  current.selected = selected;
  current.jsonText = text;
  touched(current);
  render();
}

export function resetWorkflow() {
  workflowEpoch++;
  if (workflow && !workflow.restoreError) remember(workflow);
  workflow = null;
}

function keepGraphLayout() {
  if (!graph) return;
  for (const item of graph.nodes()) graphSession.layout.positions[item.data("unitId")] = { ...item.position() };
  graphSession.layout.zoom = graph.zoom();
  graphSession.layout.pan = { ...graph.pan() };
  remember(graphSession);
}

export function disposeGraph() {
  if (graph) {
    keepGraphLayout();
    graph.destroy();
    graph = null;
    graphSession = null;
  }
}

export function workflowView(data, base, { refresh, render }) {
  const controlDirectory = app.bootstrap.state_directory;
  if (workflow?.project !== data.project.id || workflow?.controlDirectory !== controlDirectory) workflow = restoreSession(data.project.id);
  const current = workflow;
  if (current?.restoreError) return [panel("编辑缓冲无法打开", current.restoreError,
    button("下载原始缓冲", () => download("ergora-editor-buffer.txt", current.raw)),
    button("明确清除浏览器缓冲", () => {
      sessionStorage.removeItem(sessionKey(data.project.id)); sessions.delete(sessionKey(data.project.id));
      workflow = null; workflowEpoch++; render();
    }))];
  const templateChoice = select([
    ["repository-governance", "存量仓库治理"], ["large-change", "大型开发任务"], ["training-optimization", "训练优化实验"],
  ], current?.kind || "large-change", "template");
  templateChoice.setAttribute("aria-label", "工作流模板");
  const canReplace = () => !current || !changed(current) || window.confirm("载入会替换当前未保存的编辑。确定放弃并载入吗？");
  async function loadTemplate() {
    if (!canReplace()) return;
    const epoch = ++workflowEpoch, kind = templateChoice.value;
    const result = await api(`/api/templates/${kind}`);
    if (epoch !== workflowEpoch || app.project !== data.project.id || app.bootstrap.state_directory !== controlDirectory) return;
    workflow = startSession({ project: data.project.id, kind, id: "my-task", revision: 0, ...result }, data.project.id);
    remember(workflow); render();
  }
  const draftChoice = select([["", "打开已保存草稿…"], ...data.drafts.map((item) => [item.id, `${item.id} · r${item.revision}`])], "", "saved_draft");
  draftChoice.setAttribute("aria-label", "已保存草稿");
  draftChoice.addEventListener("change", () => {
    const saved = data.drafts.find((item) => item.id === draftChoice.value);
    if (saved && canReplace()) {
      workflowEpoch++; workflow = startSession(saved, data.project.id); remember(workflow); render();
    } else draftChoice.value = "";
  });
  const contents = [
    heading("设计可执行的协作关系", "保持六阶段合同。先应用单元或 JSON 文本，再校验、保存或下载同一份输入。"),
    node("div", { className: "workflow-toolbar" }, templateChoice, button("载入模板", loadTemplate, "primary"), draftChoice),
    node("div", { className: "stage-strip" }, stages.map((stage) => node("span", {}, stage))),
  ];
  if (!current) return [...contents, panel("从模板或草稿开始", "先载入模板，再编辑工作单元。训练优化使用独立 workload / experiment 模板。")];
  const requirements = app.bootstrap.agent_contracts[current.kind];
  contents.push(panel("模板角色与 Agent 选择", "模板声明能力和产物；在工具绑定中选择实现，模板正文保持一致。",
    table(["角色", "所需能力", "当前 Agent", "产物"], Object.entries(requirements.agents).map(([role, requirement]) => [
      role, requirement.capabilities.join(", "), bindingFor(data, role).tool, requirement.artifacts.join(", "),
    ])), node("p", {}, current.kind === "training-optimization"
      ? "提案与原生候选需要可信 runner 和独立测量后才能放行。" : "integrate / verify 由可信执行器运行；test-results 来自可信检查。")));
  if (current.kind === "training-optimization") return [...contents,
    panel("训练优化模板", "先固定 workload 合同与 baseline，再运行精确实验和证据门禁。",
      pre("ergora templates copy training-optimization ./training-task"),
      Object.entries(current.files).map(([name, text]) => node("details", {}, node("summary", {}, name), pre(text), button("下载文件", () => download(name, text))))),
    kernelPanel(data, base, refresh)];

  const input = current.input, units = input.work_units;
  current.selected = Math.min(current.selected, units.length - 1);
  const selected = units[current.selected];
  const buffer = current.unitBuffers[selected.id] || { unit_id: selected.id, paths: selected.paths.join("\n"),
    instructions: selected.instructions, depends_on: [...selected.depends_on] };
  const controls = [];
  const notice = node("p", { role: "status" });
  const updateControls = () => {
    const pending = pendingText(current), busy = Boolean(current.request);
    notice.textContent = current.storageError || (pending ? "有未应用文本。先应用或明确放弃，再保存、下载、增删或撤销。"
      : current.request ? "正在提交当前快照；后续编辑会保留。" : changed(current) ? "当前输入有未保存修改。" : "当前编辑与载入或最近保存的快照一致。");
    for (const [control, blocked] of controls) control.disabled = blocked(pending, busy);
  };
  const action = (text, callback, blocked, className = "secondary") => {
    const control = button(text, callback, className); controls.push([control, blocked]); return control;
  };
  const unitSelect = select(units.map((item, index) => [String(index), item.id]), String(current.selected), "unit");
  unitSelect.addEventListener("change", () => {
    workflowEpoch++;
    current.selected = Number(unitSelect.value);
    remember(current);
    render();
    $("select[name='unit']").focus();
  });
  const dependencies = node("select", { name: "depends_on", multiple: true, "aria-label": "依赖工作单元" },
    units.filter((unit) => unit !== selected).map((unit) => node("option", { value: unit.id, selected: buffer.depends_on.includes(unit.id) }, unit.id)));
  const editor = form([
    node("label", {}, "当前工作单元", unitSelect), field("单元 ID", "unit_id", buffer.unit_id, "text", { required: true }),
    node("label", {}, "依赖工作单元（可多选）", dependencies),
    field("可写路径（每行一个）", "paths", buffer.paths, "textarea", { required: true }),
    field("任务说明", "instructions", buffer.instructions, "textarea", { required: true }),
  ], "更新单元草稿", (values) => {
    if (current.jsonText !== textOf(current.input) || current.request) throw new Error("请先处理完整 JSON 文本或等待当前提交完成");
    const next = structuredClone(input), oldId = selected.id, newId = values.get("unit_id").trim();
    if (units.some((unit) => unit !== selected && unit.id === newId)) throw new Error("单元 ID 已存在");
    next.work_units[current.selected] = { id: newId, paths: lines(values.get("paths")), instructions: values.get("instructions"), depends_on: values.getAll("depends_on") };
    for (const unit of next.work_units) unit.depends_on = unit.depends_on.map((id) => id === oldId ? newId : id);
    delete current.unitBuffers[oldId];
    for (const pending of Object.values(current.unitBuffers)) pending.depends_on = pending.depends_on.map((id) => id === oldId ? newId : id);
    if (current.layout.positions[oldId]) current.layout.positions[newId] = current.layout.positions[oldId];
    commitInput(current, next, current.selected, render);
  });
  editor.addEventListener("input", (event) => {
    if (event.target === unitSelect) return;
    const values = new FormData(editor);
    const raw = { unit_id: values.get("unit_id"), paths: values.get("paths"), instructions: values.get("instructions"), depends_on: values.getAll("depends_on") };
    if (raw.unit_id === selected.id && raw.paths === selected.paths.join("\n") && raw.instructions === selected.instructions &&
        JSON.stringify(raw.depends_on) === JSON.stringify(selected.depends_on)) delete current.unitBuffers[selected.id];
    else current.unitBuffers[selected.id] = raw;
    touched(current); updateControls();
  });
  const draftId = node("input", { value: current.draftId, name: "draft_id", "aria-label": "草稿 ID" });
  draftId.addEventListener("input", () => { current.draftId = draftId.value; touched(current); updateControls(); });
  async function validate(save) {
    if (pendingText(current) || current.request) return;
    const epoch = ++workflowEpoch;
    const payload = { id: current.draftId, kind: current.kind, input: structuredClone(current.input), revision: current.revisions[current.draftId] || 0 };
    current.request = save ? "save" : "validate"; updateControls();
    try {
      const result = await api(`${base}/drafts${save ? "" : "/validate"}`, payload);
      if (save) {
        current.revisions[result.id] = result.revision;
        current.cleanText = textOf(payload.input); current.cleanId = result.id;
        if (current.draftId === result.id) { current.id = result.id; current.revision = result.revision; }
        if (app.data?.project.id === data.project.id && app.bootstrap.state_directory === controlDirectory) {
          const observed = app.data.drafts.find((draft) => draft.id === result.id);
          if (!observed || observed.revision <= result.revision) {
            app.data.drafts = app.data.drafts.filter((draft) => draft.id !== result.id);
            app.data.drafts.push(result);
          }
        }
        remember(current);
      }
      if (workflow !== current || app.project !== data.project.id || app.bootstrap.state_directory !== controlDirectory) return;
      if (epoch !== workflowEpoch) { if (save) notify("提交时的快照已保存；较新编辑仍未保存"); return; }
      notify(save ? "草稿已校验并持久保存" : "输入合同校验通过；这不代表正式任务验收");
    } finally {
      current.request = null;
      if (workflow === current && app.project === data.project.id && app.bootstrap.state_directory === controlDirectory) { remember(current); render(); }
    }
  }
  const json = node("textarea", { className: "workflow-json", value: current.jsonText, "aria-label": "完整任务输入 JSON" });
  json.addEventListener("input", () => { current.jsonText = json.value; touched(current); updateControls(); });
  const historyMove = (direction) => {
    current.historyIndex += direction;
    const snapshot = current.history[current.historyIndex];
    current.input = JSON.parse(snapshot.text); current.jsonText = snapshot.text;
    current.selected = Math.min(snapshot.selected, current.input.work_units.length - 1);
    touched(current); render();
  };
  const result = [ ...contents,
    node("div", { className: "workflow-toolbar" }, draftId,
      action("校验输入", () => validate(false), (pending, busy) => pending || busy),
      action("保存草稿", () => validate(true), (pending, busy) => pending || busy, "primary"),
      action("下载 input.json", () => download("input.json", textOf(current.input) + "\n"), (pending, busy) => pending || busy),
      badge(`目标草稿修订 ${current.revisions[current.draftId] || 0}`)),
    node("p", {}, "改 ID 按新草稿保存；要修改已有草稿，请先从列表打开。已载入或本会话保存的目标使用已知修订，冲突须重新载入。"),
    notice,
    row(action("撤销", () => historyMove(-1), (pending, busy) => pending || busy || current.historyIndex === 0),
      action("重做", () => historyMove(1), (pending, busy) => pending || busy || current.historyIndex === current.history.length - 1),
      node("span", {}, "本页最多50个快照、共4MiB；单份输入超限时仅保留当前输入。重新打开保留缓冲并重建历史。")),
    node("div", { className: "workflow-layout" },
      node("section", { className: "panel graph-panel" },
        node("div", { className: "graph-header" }, node("h2", {}, "工作单元依赖图"),
          action("＋ 单元", () => {
            const next = structuredClone(input); let index = units.length + 1;
            while (units.some((unit) => unit.id === `unit-${index}`)) index++;
            next.work_units.push({ id: `unit-${index}`, depends_on: [], paths: [], instructions: "" });
            commitInput(current, next, next.work_units.length - 1, render);
          }, (pending, busy) => pending || busy, "text-button"),
          button("重新排布", () => { disposeGraph(); current.layout = { positions: dictionary() }; remember(current); render(); }, "text-button")),
        node("div", { id: "workflow-graph", className: "graph", role: "img", "aria-label": "工作单元有向依赖图" }),
        node("div", { className: "graph-footer" }, "点击选择；拖动与视口只调整显示。表单与JSON编辑同一份任务输入。")),
      panel("编辑工作单元", null, editor,
        button("放弃当前单元文本", () => { delete current.unitBuffers[selected.id]; touched(current); render(); }, "text-button"),
        action("删除当前单元", () => {
          const next = structuredClone(input); next.work_units.splice(current.selected, 1);
          for (const unit of next.work_units) unit.depends_on = unit.depends_on.filter((id) => id !== selected.id);
          commitInput(current, next, 0, render);
        }, (pending, busy) => pending || busy || units.length <= 1, "text-button danger"))),
    panel("完整任务输入", "原始文本在应用前独立保留。单元和JSON不能静默覆盖另一处尚未应用的修改。", json,
      row(action("校验并载入 JSON", async () => {
        if (Object.keys(current.unitBuffers).length || current.request) throw new Error("请先应用或放弃单元文本");
        const epoch = ++workflowEpoch, taskInput = JSON.parse(current.jsonText);
        current.request = "json"; updateControls();
        try {
          await api(`${base}/drafts/validate`, { id: current.draftId, kind: current.kind, input: taskInput, revision: current.revisions[current.draftId] || 0 });
          if (workflow !== current || app.project !== data.project.id || app.bootstrap.state_directory !== controlDirectory || epoch !== workflowEpoch) return;
          commitInput(current, taskInput, 0, render);
        } finally { current.request = null; if (workflow === current && app.project === data.project.id && app.bootstrap.state_directory === controlDirectory) render(); }
      }, (_, busy) => busy || Object.keys(current.unitBuffers).length > 0),
      button("放弃 JSON 文本", () => { current.jsonText = textOf(current.input); touched(current); render(); }))),
    node("div", { className: "info-bar" }, "浏览器缓冲按控制目录与项目分开；持久化须明确保存草稿。编辑不会启动工具或正式任务。"),
  ];
  updateControls();
  return result;
}
let kernelInvocation = 0;
function kernelPanel(data, base, refresh) {
  const invoke = async (action, id, timeout = 30, reconcile_reason = null) => {
    const request = ++kernelInvocation;
    const epoch = workflowEpoch;
    const content = $("#dialog-content").firstElementChild;
    const wasOpen = $("#dialog").open;
    const ownsView = () =>
      app.project === data.project.id &&
      app.tab === "workflow" &&
      workflowEpoch === epoch &&
      request === kernelInvocation &&
      $("#dialog-content").firstElementChild === content &&
      (!wasOpen || $("#dialog").open);
    const result = await api(`${base}/kernel-runs${id ? `/${id}` : ""}`, {
      action,
      timeout,
      reconcile_reason,
    });
    if (!ownsView()) return;
    await refresh(data.project.id);
    if (!ownsView()) return;
    modal("原生 Kernel 工具记录", pre(result));
  };
  return panel(
    "原生 Kernel 候选",
    `生成工具：${bindingFor(data, "kernel").tool}。先配置任务与预算，计划检查不运行模型或 GPU。`,
    row(
      button("检查原生计划", () => invoke("plan")),
      button("创建原生 campaign", () => invoke("prepare")),
    ),
    table(
      ["ID", "状态", "操作"],
      data.kernel_runs.map((item) => [
        short(item.id),
        status(item.status),
        row(
          button(
            "记录",
            () => modal("Kernel campaign", pre(item)),
            "text-button",
          ),
          button(
            "原生状态 / 对账",
            () => invoke("status", item.id),
            "text-button",
          ),
          item.campaign
            ? button(
                "运行 / 继续",
                () =>
                  modal("执行同一个原生 campaign", [
                    node(
                      "p",
                      {},
                      "这会调用所选工具的模型与本机 GPU。预算来自冻结的原生任务，超时后须先对账，再明确继续；结果仍是待独立复验的候选。",
                    ),
                    form(
                      [
                        field("本次进程时限（秒）", "timeout", 3600, "number", {
                          min: 1,
                          max: 86400,
                        }),
                        field(
                          "旧作业停止的核对依据（结果不明后继续时必填）",
                          "reconcile_reason",
                          "",
                          "textarea",
                        ),
                      ],
                      "执行原生任务",
                      (values) =>
                        invoke(
                          "run",
                          item.id,
                          Number(values.get("timeout")),
                          values.get("reconcile_reason") || null,
                        ),
                    ),
                  ]),
                "text-button",
              )
            : null,
        ),
      ]),
    ),
  );
}
export function drawGraph(projectId, render) {
  if (workflow?.project !== projectId || !workflow.input) return;
  if (!window.cytoscape) {
    $("#workflow-graph").append(
      empty("图组件未加载。仍可使用工作单元表单与 JSON 编辑。"),
    );
    return;
  }
  const units = workflow.input.work_units;
  const current = workflow;
  const positions = current.layout.positions;
  const restored = Object.keys(positions).length > 0;
  const complete = units.every((unit) => positions[unit.id]);
  const right = Math.max(0, ...Object.values(positions).map((position) => position.x));
  graphSession = current;
  graph = window.cytoscape({
    container: $("#workflow-graph"),
    elements: [
      ...units.map((unit, index) => ({
        data: { id: `unit:${unit.id}`, label: unit.id, unitId: unit.id, index },
        ...(restored ? { position: positions[unit.id] || { x: right + 180, y: index * 90 } } : {}),
        classes: index === workflow.selected ? "selected" : "",
      })),
      ...units.flatMap((unit) =>
        unit.depends_on
          .filter((id) => units.some((other) => other.id === id))
          .map((dependency, index) => ({
            data: {
              id: `edge:${unit.id}:${index}`,
              source: `unit:${dependency}`,
              target: `unit:${unit.id}`,
            },
          })),
      ),
    ],
    layout: restored ? { name: "preset", fit: !complete, padding: 35 } : {
      name: "breadthfirst",
      directed: true,
      padding: 35,
      spacingFactor: 1.2,
    },
    style: [
      {
        selector: "node",
        style: {
          "background-color": "#edf3e6",
          "border-color": "#98b38d",
          "border-width": 1,
          shape: "round-rectangle",
          width: 125,
          height: 52,
          label: "data(label)",
          "font-size": 11,
          color: "#294d36",
          "text-valign": "center",
          "text-wrap": "wrap",
          "text-max-width": 115,
        },
      },
      {
        selector: "node.selected",
        style: {
          "background-color": "#d0dfbd",
          "border-color": "#3e7050",
          "border-width": 2,
        },
      },
      {
        selector: "edge",
        style: {
          width: 1.5,
          "line-color": "#93ad85",
          "target-arrow-color": "#93ad85",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
        },
      },
    ],
  });
  if (restored && complete && current.layout.zoom !== undefined) {
    graph.zoom(current.layout.zoom);
    graph.pan(current.layout.pan);
  }
  keepGraphLayout();
  graph.on("dragfree", keepGraphLayout);
  graph.on("pan zoom", () => {
    // Keep viewport edits in memory; serialize at teardown or page hide.
    current.layout.zoom = graph.zoom();
    current.layout.pan = { ...graph.pan() };
  });
  graph.on("tap", "node", (event) => {
    workflowEpoch++;
    current.selected = event.target.data("index");
    remember(current);
    render();
  });
}

window.addEventListener("pagehide", () => {
  if (graph) keepGraphLayout();
  if (workflow && !workflow.restoreError) remember(workflow);
});
