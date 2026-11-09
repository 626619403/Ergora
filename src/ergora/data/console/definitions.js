import { api } from "./api.js";
import { app } from "./state.js";
import { node, button, pre, heading, panel, empty, row, select, badge, download, table } from "./ui.js";

// Library assets belong to the control directory, independently of project selection.
const library = {
  started: false, loading: false, installing: null, error: "", message: "",
  agents: [], workflows: [], presets: [], request: 0,
  selection: null, detail: null, detailLoading: false, detailError: "", detailRequest: 0,
  grant: "", preview: null, previewLoading: false, previewError: "", previewRequest: 0,
};

function redraw(render) {
  if (app.tab === "definitions") render();
}

async function loadLibrary(render) {
  const request = ++library.request;
  library.loading = true;
  library.error = "";
  redraw(render);
  try {
    const [agents, workflows, presets] = await Promise.all([
      api("/api/agent-definitions"), api("/api/workflow-definitions"), api("/api/composition/presets"),
    ]);
    if (request !== library.request) return false;
    Object.assign(library, { agents, workflows, presets });
    const selected = library.selection;
    if (selected && !library[selected.kind === "agent" ? "agents" : "workflows"].some(
      (item) => item.id === selected.id && item.version === selected.version,
    )) {
      library.detailRequest++;
      library.previewRequest++;
      Object.assign(library, { selection: null, detail: null, preview: null, detailLoading: false, previewLoading: false });
    }
    return true;
  } catch (error) {
    if (request === library.request) library.error = error.message;
    return false;
  } finally {
    if (request === library.request) {
      library.loading = false;
      redraw(render);
    }
  }
}

async function openDefinition(kind, reference, render) {
  const request = ++library.detailRequest;
  library.previewRequest++;
  Object.assign(library, {
    selection: { kind, id: reference.id, version: reference.version }, detail: null, detailLoading: true,
    detailError: "", grant: "", preview: null, previewLoading: false, previewError: "",
  });
  redraw(render);
  try {
    const result = await api(`/api/${kind}-definitions/${encodeURIComponent(reference.id)}/${encodeURIComponent(reference.version)}`);
    if (request !== library.detailRequest) return;
    library.detail = result;
    if (kind === "workflow") library.grant = JSON.stringify({ schema_version: 1,
      permissions: result.definition.permissions, limits: result.definition.limits }, null, 2);
  } catch (error) {
    if (request === library.detailRequest) library.detailError = error.message;
  } finally {
    if (request === library.detailRequest) {
      library.detailLoading = false;
      redraw(render);
    }
  }
}

async function installPreset(identity, render) {
  if (library.installing) return;
  library.installing = identity;
  library.message = "";
  library.error = "";
  const selectionRequest = library.detailRequest;
  const previewRequest = library.previewRequest;
  redraw(render);
  try {
    const result = await api(`/api/composition/presets/${encodeURIComponent(identity)}/install`, {});
    library.message = `${identity} 的精确版本已导入；后续可在任务中显式选择。`;
    const loaded = await loadLibrary(render);
    if (loaded && selectionRequest === library.detailRequest && previewRequest === library.previewRequest)
      await openDefinition("workflow", result.root, render);
  } catch (error) {
    library.error = error.message;
  } finally {
    library.installing = null;
    redraw(render);
  }
}

async function previewDefinition(render) {
  const request = ++library.previewRequest;
  const selected = library.selection;
  library.previewLoading = true;
  library.previewError = "";
  library.preview = null;
  redraw(render);
  try {
    const grant = JSON.parse(library.grant);
    const result = await api("/api/composition/preview", { id: selected.id, version: selected.version, grant });
    if (request === library.previewRequest) library.preview = result;
  } catch (error) {
    if (request === library.previewRequest) library.previewError = error.message;
  } finally {
    if (request === library.previewRequest) {
      library.previewLoading = false;
      redraw(render);
    }
  }
}

function instancesView(preview) {
  return panel(
    "静态组合与完整祖先指令",
    "结构父链决定资源继承和权限上限；依赖决定先后，端口决定数据来源。此处尚未调用 Agent。",
    row(badge(`${preview.usage.instances} 个实例`), badge(`${preview.usage.material_bytes} 指令字节`)),
    pre({ root: preview.root, preview_sha256: preview.preview_sha256, pending: preview.pending }),
    table(["实例路径", "职能 / 类型", "后端请求", "结构父级", "先行依赖"], preview.instances.map((item) => [
      item.path, item.role || item.kind, item.backend_request?.tool || "—", item.parent || "根", item.depends_on.join("\n") || "—",
    ])),
    preview.instances.map((item) => node("details", { className: "definition-details" },
      node("summary", {}, `${item.path} · 权限、端口${item.kind === "agent" ? "与完整指令" : ""}`),
      pre({ ref: item.ref, role: item.role, backend_request: item.backend_request, permissions: item.permissions,
        limits: item.limits, usage: item.usage, concurrency_scopes: item.concurrency_scopes,
        inputs: item.inputs, outputs: item.outputs, review_requirement: item.review_requirement }),
      item.kind === "agent" ? [
        pre({ material_bytes: item.material_bytes, prompt_sha256: item.prompt_sha256 }),
        ...item.resources.map((resource) => node("details", {},
          node("summary", {}, `${resource.kind} · ${resource.ids.join(", ")}`),
          pre({ content_digest: resource.content_digest, sources: resource.sources }), pre(resource.text),
        )),
        node("details", {}, node("summary", {}, "完整装配后的提示正文"), pre(item.prompt)),
      ] : null,
    )),
    button("下载 composition-preview.json", () => download("composition-preview.json", JSON.stringify(preview, null, 2) + "\n")),
  );
}

function detailView(render) {
  if (library.detailLoading) return [panel("精确版本", "正在读取定义…")];
  if (library.detailError) return [panel("定义读取失败", library.detailError,
    button("重试读取定义", () => openDefinition(library.selection.kind, library.selection, render)))];
  if (!library.detail) return [panel("选择一个精确版本", "先导入内置组合，或从列表选择 Agent / 子工作流。版本详情和静态预览均不执行任务。")];
  const { definition, resources, digest } = library.detail;
  const selected = library.selection;
  const contents = [panel(
    `${definition.id} @ ${definition.version}`, definition.description,
    pre({ kind: selected.kind, digest, roles: definition.roles, specialties: definition.specialties,
      backend_request: definition.backend }),
    node("details", {}, node("summary", {}, "标准定义 JSON"), pre(definition),
      button("下载定义 JSON", () => download(`${selected.kind}.json`, JSON.stringify(definition, null, 2) + "\n"))),
    resources.map((resource) => node("details", {}, node("summary", {}, `自身资源 · ${resource.id}`),
      pre({ kind: resource.kind, path: resource.path, digest: resource.digest, sha256: resource.sha256 }), pre(resource.text))),
    node("details", {}, node("summary", {}, "完整包文件身份（含 Skill 附件）"), pre(library.detail.files)),
  )];
  if (selected.kind !== "workflow") return contents;
  const result = node("div", {},
    library.previewError ? panel("预览未通过", library.previewError) : null,
    library.preview ? instancesView(library.preview) : empty("预览后查看所有叶实例继承的指令、来源、权限和预算。"),
  );
  const grant = node("textarea", { className: "workflow-json", value: library.grant,
    "aria-label": "静态预览上限 JSON", spellcheck: "false" });
  const previewAction = button(library.previewLoading ? "正在预览…" : "预览完整组合", () => previewDefinition(render),
    "primary", { disabled: library.previewLoading });
  grant.addEventListener("input", () => {
    library.grant = grant.value;
    library.previewRequest++;
    Object.assign(library, { preview: null, previewLoading: false, previewError: "" });
    previewAction.disabled = false;
    previewAction.textContent = "预览完整组合";
    result.replaceChildren(empty("上限已修改；重新预览后查看当前结果。"));
  });
  contents.push(panel(
    "预览整个嵌套组合",
    "初始上限来自该根定义，可修改后显式预览。这是静态校验上限；正式任务仍需项目授权、冻结输入与后端能力准入。",
    node("label", {}, "静态预览上限 JSON", grant),
    previewAction,
  ), result);
  return contents;
}

export function definitionsView(render) {
  if (!library.started) {
    library.started = true;
    queueMicrotask(() => loadLibrary(render));
  }
  const selected = library.selection;
  const agentIndex = selected?.kind === "agent" ? library.agents.findIndex(
    (item) => item.id === selected.id && item.version === selected.version) : -1;
  const workflowIndex = selected?.kind === "workflow" ? library.workflows.findIndex(
    (item) => item.id === selected.id && item.version === selected.version) : -1;
  const agentChoice = select([
    ["", "选择 Agent 精确版本…"], ...library.agents.map((item, index) => [String(index), `${item.id} @ ${item.version} · ${item.roles.join(", ")}`]),
  ], agentIndex < 0 ? "" : String(agentIndex), "agent_definition");
  agentChoice.setAttribute("aria-label", "Agent 精确版本");
  agentChoice.addEventListener("change", () => {
    if (agentChoice.value !== "") openDefinition("agent", library.agents[Number(agentChoice.value)], render);
  });
  const workflowChoice = select([
    ["", "选择子工作流精确版本…"], ...library.workflows.map((item, index) => [String(index), `${item.id} @ ${item.version}`]),
  ], workflowIndex < 0 ? "" : String(workflowIndex), "workflow_definition");
  workflowChoice.setAttribute("aria-label", "子工作流精确版本");
  workflowChoice.addEventListener("change", () => {
    if (workflowChoice.value !== "") openDefinition("workflow", library.workflows[Number(workflowChoice.value)], render);
  });
  return [
    heading("Agent 与组合库", "复用专长 Agent 与嵌套子工作流。此库在同一控制目录内共享，可在注册项目之前使用。",
      button(library.loading ? "正在读取…" : "刷新定义库", () => loadLibrary(render), "secondary", { disabled: library.loading })),
    library.error ? panel("库操作未完成", library.error) : null,
    library.message ? node("p", { role: "status" }, library.message) : null,
    panel("内置领域组合", "导入版本化定义以供后续选择；执行时另行确认项目授权与后端能力。后端工具的安装和认证在工具绑定中处理。",
      table(["组合", "支持范围", "操作"], library.presets.map((item) => [
        node("div", {}, node("strong", {}, item.id), node("p", {}, item.description)),
        item.runtime === "development-v5" ? "原六阶段开发运行；writer 信任须显式选择" : "静态组合与只读提案叶；实验由可信 runner 执行",
        button(library.installing === item.id ? "正在导入…" : `导入 ${item.id}`, () => installPreset(item.id, render),
          "secondary", { disabled: Boolean(library.installing) }),
      ])),
      library.loading && !library.presets.length ? empty("正在读取内置组合…") : null,
    ),
    panel("选择定义", `${library.agents.length} 个 Agent 版本 · ${library.workflows.length} 个工作流版本。后端字段表示默认请求，可用性由实际调用核验。`,
      node("label", {}, "Agent 精确版本", agentChoice), node("label", {}, "子工作流精确版本", workflowChoice)),
    ...detailView(render),
  ].filter(Boolean);
}
