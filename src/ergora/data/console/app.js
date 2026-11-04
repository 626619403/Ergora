import { api } from "./api.js";
import { $, node, button, pre, heading, notify, modal } from "./ui.js";
import { app } from "./state.js";
import { projectDialog } from "./projects.js";
import { overview } from "./overview.js";
import { toolsView } from "./tools.js";
import { memoryView } from "./memory.js";
import { skillsView } from "./skills.js";
import { researchView } from "./research.js";
import { tasksView } from "./tasks.js";
import { workflowView, resetWorkflow, disposeGraph, drawGraph } from "./workflow.js";

let refreshSequence = 0;
let refreshing = false;
let refreshError = "";
const savedTab = sessionStorage.getItem("ergora-tab");
if ([...document.querySelectorAll("[data-tab]")].some((item) => item.dataset.tab === savedTab))
  app.tab = savedTab;

async function refresh(expectedProject) {
  if (expectedProject && app.project !== expectedProject) return;
  const sequence = ++refreshSequence;
  refreshing = true;
  refreshError = "";
  if (app.data?.project.id !== app.project) {
    app.data = null;
    render();
  }
  try {
    const bootstrap = await api("/api/bootstrap");
    if (sequence !== refreshSequence) return;
    app.bootstrap = bootstrap;
    app.layers = Object.fromEntries(
      Object.entries(bootstrap.layers)
        .sort(([, left], [, right]) => left.display_order - right.display_order)
        .map(([layer, definition]) => [layer, [definition.title, definition.description, definition.icon]]),
    );
    app.agentRoles = Object.entries(bootstrap.layers)
      .filter(([, definition]) => definition.kind === "agent")
      .map(([layer]) => layer);
    if (!bootstrap.projects.some((project) => project.id === app.project))
      app.project = bootstrap.projects[0]?.id || null;
    const projectId = app.project;
    const data = projectId
      ? await api(`/api/projects/${encodeURIComponent(projectId)}/dashboard`)
      : null;
    if (sequence !== refreshSequence || app.project !== projectId) return;
    app.data = data;
    sessionStorage.setItem("ergora-project", projectId || "");
    $("#version").textContent = `Ergora ${bootstrap.version}`;
    $("#project-title").textContent = projectId || "选择项目";
    $("#project-select").replaceChildren(
      ...(bootstrap.projects.length
        ? bootstrap.projects.map((project) =>
            node(
              "option",
              { value: project.id, selected: project.id === projectId },
              project.id,
            ),
          )
        : [node("option", {}, "先注册一个项目")]),
    );
    refreshing = false;
    render();
  } catch (error) {
    if (sequence !== refreshSequence) return;
    refreshing = false;
    refreshError = error.message;
    render();
    throw error;
  }
}
function helpDialog() {
  modal("从项目开始", [
    node(
      "p",
      {},
      "1. 注册已有 Git 仓库；在工具绑定中选择实现、审查、记忆、优化、资料和调度工具。可安装与认证状态需要实际调用确认。",
    ),
    node(
      "p",
      {},
      "2. 保存带来源的项目记忆，导入 Agent Skills 目录；候选先比较与评价，再说明理由采用或回退。",
    ),
    node(
      "p",
      {},
      "3. 工作流设计保存任务输入草稿；正式任务页可预览、明确创建、检查提交并按原意图恢复，随后读取指定run的原状态。待批时审阅完整计划并显式批准；运行中明确请求取消，按原决策或请求ID查询/恢复。闭合后可只读核外部证据，再明确对账或恢复原意图；仅reconciled表示原租约已释放且回执保存。投递、清理和开发成功分别核对。候选导出使用ergora task统一CLI，详见docs/USAGE.md。",
    ),
    pre(
      "ergora --help\nergora tools list\nergora reference info\nergora templates copy training-optimization ./training-task",
    ),
    node(
      "p",
      {},
      `持久状态目录：${app.bootstrap.state_directory}。先停止写入，再备份完整目录。换机后重新核对项目路径与工具认证。`,
    ),
    node(
      "p",
      {},
      "本地控制台沿用当前用户权限；请仅注册可信项目。使用指南与集成协议见仓库 docs/USAGE.md 和 docs/INTEGRATIONS.md。",
    ),
  ]);
}
function render() {
  disposeGraph();
  sessionStorage.setItem("ergora-tab", app.tab);
  document
    .querySelectorAll("[data-tab]")
    .forEach((item) =>
      item.classList.toggle("active", item.dataset.tab === app.tab),
    );
  if (!app.data) {
    if (refreshing || refreshError) {
      $("#main").replaceChildren(heading(
        refreshError ? "无法读取工作空间" : "正在读取工作空间",
        refreshError || `正在读取 ${app.project || "项目列表"}…`,
        refreshError ? button("重试", () => refresh()) : null,
      ));
      return;
    }
    $("#main").replaceChildren(
      node(
        "div",
        { className: "empty" },
        node("div", { className: "empty-symbol" }, "◈"),
        node("h2", {}, "为第一个项目建立工作空间"),
        node(
          "p",
          {},
          "连接一个已有的 Git 仓库，开始配置工具、保存记忆和积累可复查的改进证据。",
        ),
        button("＋ 注册项目", () => projectDialog(refresh), "primary"),
      ),
    );
    return;
  }
  const data = app.data;
  const id = data.project.id;
  const base = `/api/projects/${encodeURIComponent(id)}`;
  const views = {
    overview,
    tools: toolsView,
    memory: memoryView,
    skills: skillsView,
    research: researchView,
    tasks: tasksView,
    workflow: workflowView,
  };
  $("#main").replaceChildren(...views[app.tab](data, base, { refresh, render }));
  if (app.tab === "workflow") drawGraph(id, render);
}
$("#project-select").addEventListener("change", (event) => {
  app.project = event.target.value;
  resetWorkflow();
  refresh().catch((error) => notify(error.message, true));
});
document.querySelectorAll("[data-tab]").forEach((item) =>
  item.addEventListener("click", () => {
    app.tab = item.dataset.tab;
    render();
  }),
);
$("#refresh").addEventListener("click", () =>
  refresh()
    .then(() => notify("已读取最新状态"))
    .catch((error) => notify(error.message, true)),
);
$("#add-project").addEventListener("click", () => projectDialog(refresh));
$("#help").addEventListener("click", helpDialog);
refresh().catch((error) => notify(error.message, true));
