// All values, including source documents and model output, enter the DOM as text.
const $ = (selector, root = document) => root.querySelector(selector);
const app = {
  tab: "overview",
  project: sessionStorage.getItem("ergora-project"),
  bootstrap: null,
  data: null,
};
const layers = {
  inspector: ["仓库盘点 Agent", "理解代码、建立知识导航与基线清单", "⌕"],
  planner: ["开发规划 Agent", "规划范围、工作单元、依赖与回退", "▧"],
  implementer: ["实现 Agent", "编写与修改项目代码", "⌘"],
  reviewer: ["审查 Agent", "在独立调用中核对实现与证据", "◇"],
  "experiment-planner": [
    "实验规划 Agent",
    "提出有固定 workload 和基线的实验",
    "◈",
  ],
  "performance-analyst": [
    "性能分析 Agent",
    "分析瓶颈并提出可复验的测量计划",
    "↝",
  ],
  "kernel-tuner": ["Kernel 提案 Agent", "生成候选说明与独立验证计划", "⊞"],
  kernel: [
    "Kernel 生成工具",
    "原生候选生成；独立正确性与性能门禁仍由项目负责",
    "⚙",
  ],
  memory: ["项目记忆", "保存来源、修订和可检索的项目约定", "▤"],
  optimizer: ["Skill 优化", "产生候选，通过固定评价后显式采用", "↗"],
  research: ["资料来源", "有预算地观察指定资料的新版本", "◎"],
  scheduler: ["任务调度", "手动触发或使用 Temporal 持久调度", "◷"],
};
const agentRoles = [
  "inspector",
  "planner",
  "implementer",
  "reviewer",
  "experiment-planner",
  "performance-analyst",
  "kernel-tuner",
];
const bindingFor = (project, layer) =>
  project.bindings[layer] ||
  (layer === "kernel" ? { tool: "manual" } : project.bindings.implementer);
const stages = ["inventory", "plan", "work", "integrate", "verify", "review"];
let refreshSequence = 0,
  workflowEpoch = 0,
  noticeTimer,
  graph,
  workflow;

function node(tag, properties = {}, ...children) {
  const element = document.createElement(tag);
  // Avoid the single-select default choosing the first dependency on insertion.
  if (properties.multiple) element.multiple = true;
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined && child !== false)
      element.append(
        child instanceof Node ? child : document.createTextNode(String(child)),
      );
  }
  for (const [name, value] of Object.entries(properties)) {
    if (name.startsWith("on"))
      element.addEventListener(name.slice(2).toLowerCase(), (event) => {
        try {
          Promise.resolve(value(event)).catch((error) =>
            notify(error.message, true),
          );
        } catch (error) {
          notify(error.message, true);
        }
      });
    else if (
      ["value", "checked", "disabled", "selected", "hidden"].includes(name)
    )
      element[name] = value;
    else if (value !== null && value !== undefined)
      element.setAttribute(
        name === "className" ? "class" : name,
        String(value),
      );
  }
  return element;
}
const button = (text, action, className = "secondary", extra = {}) =>
  node(
    "button",
    { type: "button", className, onclick: action, ...extra },
    text,
  );
const pre = (value) =>
  node(
    "pre",
    {},
    typeof value === "string" ? value : JSON.stringify(value, null, 2),
  );
function outputPanels(result) {
  return Object.entries(result.streams).map(([name, stream]) =>
    panel(
      name === "stdout" ? "标准输出" : "诊断输出",
      !stream.available
        ? "输出文件尚未产生"
        : stream.truncated
          ? "显示前 64 KiB；完整输出保存在运行归档"
          : "",
      pre(stream.text),
    ),
  );
}
const lines = (value) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
const short = (value) => (value ? value.slice(0, 12) : "—");
const heading = (title, description, action) =>
  node(
    "div",
    { className: "page-heading" },
    node(
      "div",
      {},
      node("div", { className: "eyebrow" }, "Ergora workspace"),
      node("h1", {}, title),
      node("p", {}, description),
    ),
    action,
  );
const panel = (title, description, ...children) =>
  node(
    "section",
    { className: "panel" },
    title ? node("h2", {}, title) : null,
    description ? node("p", {}, description) : null,
    ...children,
  );
const empty = (text) => node("div", { className: "inline-empty" }, text);
const row = (...children) =>
  node("div", { className: "button-row" }, ...children);
const select = (options, value, name) =>
  node(
    "select",
    { name, value },
    options.map((item) =>
      node(
        "option",
        { value: Array.isArray(item) ? item[0] : item },
        Array.isArray(item) ? item[1] : item,
      ),
    ),
  );
const field = (label, name, value = "", type = "text", extra = {}) =>
  node(
    "label",
    {},
    label,
    type === "textarea"
      ? node("textarea", { name, value, ...extra })
      : node("input", { name, type, value, ...extra }),
  );
const selectField = (label, options, value, name) =>
  node("label", {}, label, select(options, value, name));
const checkbox = (label, name, checked = false) =>
  node(
    "label",
    { className: "field-check" },
    node("input", { type: "checkbox", name, checked }),
    label,
  );
const badge = (label, color = "gray") =>
  node("span", { className: `badge ${color}` }, label);
function status(value) {
  const color = ["succeeded", "reviewed"].includes(value)
    ? "green"
    : ["failed", "native_failed", "timed_out", "budget_exhausted"].includes(
          value,
        )
      ? "red"
      : ["running", "pending", "outcome_unknown"].includes(value)
        ? "amber"
        : "gray";
  return badge(value, color);
}
function notify(message, error = false) {
  const notice = $("#notice");
  clearTimeout(noticeTimer);
  notice.textContent = message;
  notice.className = error ? "error" : "";
  notice.hidden = false;
  noticeTimer = setTimeout(
    () => {
      notice.hidden = true;
    },
    error ? 16000 : 7000,
  );
}
async function api(path, body, method = "POST") {
  const options =
    body === undefined
      ? {}
      : {
          method,
          headers: {
            "Content-Type": "application/json",
            "X-Ergora-Request": "1",
          },
          body: JSON.stringify(body),
        };
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok)
    throw new Error(
      result.error ||
        (typeof result.detail === "string"
          ? result.detail
          : JSON.stringify(result.detail)) ||
        `HTTP ${response.status}`,
    );
  return result;
}
function form(children, text, submit) {
  const action = node("button", { className: "primary", type: "submit" }, text);
  const element = node(
    "form",
    {
      onsubmit: async (event) => {
        event.preventDefault();
        if (action.disabled) return;
        action.disabled = true;
        action.textContent = "正在处理…";
        try {
          await submit(new FormData(element), element);
        } finally {
          action.disabled = false;
          action.textContent = text;
        }
      },
    },
    children,
    row(action),
  );
  return element;
}
function modal(title, content) {
  const dialog = $("#dialog");
  if (dialog.open) dialog.close();
  $("#dialog-content").replaceChildren(
    node(
      "div",
      { className: "dialog-header" },
      node("h2", {}, title),
      button("×", () => dialog.close(), "close", { "aria-label": "关闭" }),
    ),
    node("div", { className: "dialog-body" }, content),
  );
  dialog.showModal();
}
function download(name, content) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/plain;charset=utf-8" }),
  );
  const link = node("a", { href: url, download: name });
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function table(headers, rows) {
  return rows.length
    ? node(
        "div",
        { className: "table-wrap" },
        node(
          "table",
          {},
          node(
            "thead",
            {},
            node(
              "tr",
              {},
              headers.map((text) => node("th", {}, text)),
            ),
          ),
          node(
            "tbody",
            {},
            rows.map((cells) =>
              node(
                "tr",
                {},
                cells.map((cell) => node("td", {}, cell)),
              ),
            ),
          ),
        ),
      )
    : empty("还没有记录。完成一次操作后，结果会显示在这里。");
}
async function refresh(expectedProject) {
  if (expectedProject && app.project !== expectedProject) return;
  const sequence = ++refreshSequence;
  const bootstrap = await api("/api/bootstrap");
  if (sequence !== refreshSequence) return;
  app.bootstrap = bootstrap;
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
  render();
}
function projectDialog() {
  modal(
    "注册项目",
    form(
      [
        node(
          "p",
          {},
          "选择本机已有的 Git 仓库。每个项目保存自己的工具绑定、记忆与证据。",
        ),
        field("项目 ID", "id", "", "text", {
          required: true,
          pattern: "[A-Za-z0-9][A-Za-z0-9_\\-]{0,63}",
          placeholder: "my-project",
        }),
        field("Git 仓库绝对路径", "repo", "", "text", {
          required: true,
          placeholder: "/path/to/my-project",
        }),
      ],
      "注册项目",
      async (values) => {
        const result = await api("/api/projects", Object.fromEntries(values));
        app.project = result.id;
        workflowEpoch++;
        workflow = null;
        $("#dialog").close();
        await refresh();
        notify("项目已注册");
      },
    ),
  );
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
      "3. 工作流设计保存任务输入草稿。下载 input.json 后，使用参考编译器和六阶段运行时执行；草稿校验成功只证明输入满足合同。",
    ),
    pre(
      "ergora --help\nergora tools list\nergora reference info\nergora templates copy training-optimization ./training-task",
    ),
    node(
      "p",
      {},
      "持久状态默认在 ~/.local/share/ergora。先停止写入，再备份完整目录。换机后重新核对项目路径与工具认证。",
    ),
    node(
      "p",
      {},
      "本地控制台沿用当前用户权限；请仅注册可信项目。使用指南与集成协议见仓库 docs/USAGE.md 和 docs/INTEGRATIONS.md。",
    ),
  ]);
}
function render() {
  if (graph) {
    graph.destroy();
    graph = null;
  }
  document
    .querySelectorAll("[data-tab]")
    .forEach((item) =>
      item.classList.toggle("active", item.dataset.tab === app.tab),
    );
  if (!app.data) {
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
        button("＋ 注册项目", projectDialog, "primary"),
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
    workflow: workflowView,
  };
  $("#main").replaceChildren(...views[app.tab](data, base));
  if (app.tab === "workflow" && workflow?.project === id && workflow.input)
    drawGraph();
}
function overview(data, base) {
  const counts = [
    ["项目记忆", data.memories.length, "有来源的持久记录", "▤"],
    ["活动 Skill", data.skills.active.length, "明确采用的版本", "◇"],
    [
      "待审资料",
      data.research.proposals.filter((item) => item.status === "pending")
        .length,
      "观察结果需要人工核对",
      "◎",
    ],
    ["工具调用", data.agent_runs.length, "最近最多 100 次调用", "⌘"],
  ];
  return [
    node(
      "section",
      { className: "hero" },
      node(
        "div",
        {},
        node("div", { className: "eyebrow" }, "Project workspace"),
        node("h1", {}, "把协作变成可积累的能力"),
        node(
          "p",
          {},
          "为项目组合适合的工具，让记忆带有来源，让改进经过评价，让每次执行留下证据。",
        ),
        button(
          "配置工具 →",
          () => {
            app.tab = "tools";
            render();
          },
          "primary",
        ),
      ),
      node(
        "div",
        { className: "hero-art", "aria-hidden": "true" },
        node("div", { className: "orbit-node" }, "◇"),
        node("div", { className: "orbit-line" }),
        node("div", { className: "orbit-node center" }, "e"),
        node("div", { className: "orbit-line" }),
        node("div", { className: "orbit-node" }, "◎"),
      ),
    ),
    node(
      "div",
      { className: "stats" },
      counts.map(([label, value, note, icon]) =>
        node(
          "div",
          { className: "stat" },
          node(
            "div",
            { className: "stat-label" },
            label,
            node("span", {}, icon),
          ),
          node("div", { className: "stat-value" }, value),
          node("small", {}, note),
        ),
      ),
    ),
    node(
      "div",
      { className: "grid-two" },
      panel(
        "六阶段协作合同",
        "沿用固定阶段，工作单元可以按依赖关系并行。",
        node(
          "div",
          { className: "stages" },
          stages.map((stage, index) =>
            node(
              "div",
              { className: "stage" },
              node("div", { className: "stage-number" }, `0${index + 1}`),
              node("strong", {}, stage),
            ),
          ),
        ),
        node(
          "div",
          { className: "stage-note" },
          "○ 这是协议阶段说明。正式执行和验收状态由参考运行时产生。",
        ),
        row(
          button("设计工作单元", () => {
            app.tab = "workflow";
            render();
          }),
        ),
      ),
      panel(
        "项目约定",
        null,
        node(
          "div",
          { className: "check-row" },
          node("span", { className: "check-icon" }, "▤"),
          node(
            "div",
            {},
            node("strong", {}, "记忆有来源与修订"),
            node("p", {}, "更正保留历史；删除与远端同步分别确认。"),
          ),
        ),
        node(
          "div",
          { className: "check-row" },
          node("span", { className: "check-icon" }, "◇"),
          node(
            "div",
            {},
            node("strong", {}, "候选先评价再采用"),
            node("p", {}, "固定评分和保留集，采用及回退都记录理由。"),
          ),
        ),
        node(
          "div",
          { className: "check-row" },
          node("span", { className: "check-icon" }, "⌘"),
          node(
            "div",
            {},
            node("strong", {}, data.project.repo),
            node("p", {}, `项目配置修订 ${data.project.revision}`),
          ),
        ),
      ),
    ),
    panel(
      "最近工具调用",
      "进程成功退出仅代表调用完成，正式验收继续使用已有证据门禁。",
      row(button("运行一次 Agent", () => agentDialog(data, base), "primary")),
      table(
        ["角色 / 工具", "状态", "开始时间", "记录"],
        data.agent_runs.slice(0, 8).map((item) => [
          node("span", {}, item.role, node("small", {}, item.binding.tool)),
          status(item.status),
          item.started,
          button(
            "查看记录",
            async () => {
              const output = await api(`${base}/agent-runs/${item.id}/output`);
              modal("工具调用记录", [pre(item), ...outputPanels(output)]);
            },
            "text-button",
          ),
        ]),
      ),
    ),
  ];
}
function agentDialog(data, base) {
  const result = node("div");
  modal(
    "运行 Agent",
    form(
      [
        selectField(
          "角色",
          [...agentRoles.map((role) => [role, layers[role][0]])],
          "reviewer",
          "role",
        ),
        selectField(
          "模板产物要求（可选）",
          [
            ["", "普通独立调用"],
            ...app.bootstrap.templates.map((kind) => [kind, kind]),
          ],
          "",
          "template",
        ),
        field("任务说明", "prompt", "", "textarea", { required: true }),
        field("活动 Skill 名称（逗号分隔，可选）", "skills"),
        field("项目记忆检索（可选）", "recall"),
        field("超时（秒）", "timeout", 300, "number", { min: 1, max: 3600 }),
        result,
      ],
      "执行调用",
      async (values) => {
        result.replaceChildren(
          node("p", {}, "工具正在执行。可在其他页面刷新查看运行记录。"),
        );
        const response = await api(`${base}/agent-runs`, {
          role: values.get("role"),
          prompt: values.get("prompt"),
          timeout: Number(values.get("timeout")),
          skills: values
            .get("skills")
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
          recall: values.get("recall") || null,
          template: values.get("template") || null,
        });
        const output = await api(`${base}/agent-runs/${response.id}/output`);
        result.replaceChildren(
          status(response.status),
          pre(response),
          ...outputPanels(output),
        );
        await refresh(data.project.id);
      },
    ),
  );
}
function toolsView(data) {
  return [
    heading(
      "为每一层选择工具",
      "工具按项目绑定。检查结果区分本地可用性；认证、服务连接和实际效果需要进一步确认。",
    ),
    node(
      "div",
      { className: "tools-grid" },
      Object.entries(layers).map(([layer, [title, description, icon]]) => {
        const binding = bindingFor(data.project, layer);
        const check = data.tools.checks.find((item) => item.layer === layer);
        return node(
          "section",
          { className: "panel tool-card" },
          node("div", { className: "tool-icon" }, icon),
          node("h2", {}, title),
          node("p", {}, description),
          node(
            "div",
            { className: "tool-footer" },
            node(
              "div",
              {},
              node("div", { className: "tool-name" }, binding.tool),
              badge(
                check?.installed === true
                  ? agentRoles.includes(layer)
                    ? "本地可用 · 认证待确认"
                    : check.connectivity === "not_checked"
                      ? "组件可用 · 服务待确认"
                      : "本地可用"
                  : check?.installed === false
                    ? "尚未安装"
                    : "外部配置待确认",
                check?.installed === false ? "amber" : "gray",
              ),
            ),
            button("配置", () => bindingDialog(data, layer), "text-button", {
              "aria-label": `配置${title}`,
            }),
          ),
        );
      }),
    ),
    node(
      "div",
      { className: "info-bar" },
      "独立调用使用当前项目绑定。正式六阶段需显式启用 ergora reference executor；它在新任务首次接入时冻结角色绑定，恢复不换 Agent。集成和可信验证仍由执行器负责。",
    ),
    panel("检查详情", null, pre(data.tools)),
  ];
}
function bindingDialog(data, layer) {
  const current = bindingFor(data.project, layer);
  const choice = select(
    app.bootstrap.tools[layer].map((item) => item.tool),
    current.tool,
    "tool",
  );
  const options = node("div");
  function fields() {
    const tool = choice.value;
    const same = tool === current.tool ? current : {};
    const content = [];
    if (["codex", "claude-code"].includes(tool))
      content.push(
        field("模型 ID（留空采用工具配置）", "model", same.model || ""),
      );
    if (tool === "codex")
      content.push(
        selectField(
          "执行边界",
          [
            ["", "使用角色默认 sandbox"],
            ["read-only", "只读 sandbox"],
            ["workspace-write", "工作区写入 sandbox"],
            ["current-container", "已信任的当前容器 / 用户"],
          ],
          same.sandbox || "",
          "sandbox",
        ),
      );
    if (tool === "command")
      content.push(
        field(
          "命令参数 JSON 数组",
          "argv",
          JSON.stringify(same.argv || ["python3", "/path/to/tool.py"]),
          "textarea",
          { required: true },
        ),
        selectField(
          "命令协议",
          [
            ["", "stdin 文本（普通调用）"],
            ["stage-json-v1", "结构化阶段 JSON"],
          ],
          same.protocol || "",
          "protocol",
        ),
        field(
          "声明能力 JSON 数组（结构化命令必填）",
          "capabilities",
          JSON.stringify(
            same.capabilities || app.bootstrap.tools[layer][0].requires || [],
          ),
          "textarea",
        ),
      );
    if (tool === "mini-swe-agent")
      content.push(
        field("provider/model ID", "model", same.model || "", "text", {
          required: true,
        }),
        field("独立环境 Python 路径（可选）", "python", same.python || ""),
        field("最大步数", "step_limit", same.step_limit || 30, "number", {
          min: 1,
          max: 1000,
        }),
        field(
          "报告成本预算（USD；单次调用可超过剩余值）",
          "cost_limit",
          same.cost_limit || 3,
          "number",
          { min: 0.01, max: 100, step: 0.01 },
        ),
      );
    if (tool === "forgekernel")
      content.push(
        field("固定版本源码目录", "checkout", same.checkout || "", "text", {
          required: true,
        }),
        field(
          "Forge 环境 Python 绝对路径",
          "python",
          same.python || "",
          "text",
          { required: true },
        ),
        field("原生任务目录绝对路径", "task", same.task || "", "text", {
          required: true,
        }),
        node(
          "p",
          {},
          "使用独立安装器准备固定版本。当前适配仅支持 local delivery，执行需要 Claude 与 GPU；计划检查不运行它们。",
        ),
      );
    if (tool === "gepa")
      content.push(
        field(
          "提案器参数 JSON 数组",
          "proposer_argv",
          JSON.stringify(
            same.proposer_argv || ["python3", "/path/to/propose-skill.py"],
          ),
          "textarea",
          { required: true },
        ),
        node(
          "p",
          {},
          "提案器遵守 JSON 输入/输出协议。GEPA 需要安装可选依赖，仍须固定评价和显式采用。",
        ),
      );
    if (tool === "reme")
      content.push(
        field(
          "服务地址",
          "endpoint",
          same.endpoint || "http://127.0.0.1:2333",
          "url",
          { required: true },
        ),
        field("凭据环境变量名（可选）", "token_env", same.token_env || ""),
        node(
          "p",
          {},
          "只填写变量名称。密钥由服务进程环境读取。切换前核对远端项目和删除传播。",
        ),
      );
    if (tool === "temporal")
      content.push(
        field(
          "Temporal 地址",
          "address",
          same.address || "127.0.0.1:7233",
          "text",
          { required: true },
        ),
        field("命名空间", "namespace", same.namespace || "default", "text", {
          required: true,
        }),
        field(
          "项目 Task Queue",
          "task_queue",
          same.task_queue || `ergora-${data.project.id}-research`,
          "text",
          { required: true },
        ),
        node(
          "p",
          {},
          "Schedule 和 worker 使用 CLI 创建和启动。各项目使用独立 task queue；新 Schedule 默认暂停。",
        ),
      );
    options.replaceChildren(...content);
  }
  choice.addEventListener("change", fields);
  fields();
  modal(
    layers[layer][0],
    form(
      [node("label", {}, "选择工具", choice), options],
      "保存绑定",
      async (values, element) => {
        const binding = Object.fromEntries(values);
        for (const key of ["argv", "proposer_argv", "capabilities"])
          if (key in binding) binding[key] = JSON.parse(binding[key]);
        for (const key of [
          "model",
          "token_env",
          "python",
          "sandbox",
          "protocol",
        ])
          if (binding[key] === "") delete binding[key];
        for (const key of ["step_limit", "cost_limit"])
          if (key in binding) binding[key] = Number(binding[key]);
        await api(
          `/api/projects/${encodeURIComponent(data.project.id)}/bindings/${layer}`,
          { binding, revision: data.project.revision },
          "PUT",
        );
        await refresh(data.project.id);
        if ($("#dialog").contains(element)) $("#dialog").close();
        notify("工具绑定已保存");
      },
    ),
  );
}
function memoryView(data, base) {
  const cards = node("div", { className: "memory-grid" });
  const show = (items) =>
    cards.replaceChildren(
      ...(items.length
        ? items.map((item) =>
            node(
              "article",
              { className: "panel memory-card" },
              node(
                "div",
                { className: "row-between" },
                badge(`修订 ${item.revision}`),
                node("small", { className: "muted" }, short(item.id)),
              ),
              node("div", { className: "memory-body" }, item.text),
              node(
                "div",
                { className: "source-line" },
                node("strong", {}, item.source.uri),
                ` · ${item.source.revision}`,
              ),
              node(
                "div",
                { className: "memory-actions" },
                button(
                  "更正",
                  () => memoryDialog(data, base, item),
                  "text-button",
                ),
                button(
                  "修订历史",
                  async () => {
                    const history = await api(
                      `${base}/memories/${item.id}/history`,
                    );
                    modal(
                      "记忆修订历史",
                      history.map((version) =>
                        panel(
                          `修订 ${version.revision}`,
                          version.observed,
                          pre(version.text),
                          version.revision !== item.revision &&
                            version.status === "active"
                            ? button("恢复此修订", async () => {
                                await api(
                                  `${base}/memories/${item.id}/restore`,
                                  {
                                    from_revision: version.revision,
                                    revision: item.revision,
                                  },
                                );
                                $("#dialog").close();
                                await refresh(data.project.id);
                                notify("已创建恢复修订");
                              })
                            : null,
                        ),
                      ),
                    );
                  },
                  "text-button",
                ),
                button(
                  "删除",
                  () =>
                    modal("删除项目记忆", [
                      node(
                        "p",
                        {},
                        "将清空此记忆的全部历史正文和来源。配置过 ReMe 时，随后执行同步确认远端删除。",
                      ),
                      button(
                        "确认删除",
                        async () => {
                          await api(
                            `${base}/memories/${item.id}`,
                            { revision: item.revision },
                            "DELETE",
                          );
                          $("#dialog").close();
                          await refresh(data.project.id);
                          notify("本地记录已删除；按需同步远端");
                        },
                        "secondary danger",
                      ),
                    ]),
                  "text-button danger",
                ),
              ),
            ),
          )
        : [empty("保存第一条带来源的项目记忆。")]),
    );
  show(data.memories);
  const query = node("input", {
    name: "query",
    placeholder: "搜索项目约定、经验与来源…",
    "aria-label": "搜索项目记忆",
  });
  const searchForm = node(
    "form",
    {
      className: "search-row",
      onsubmit: async (event) => {
        event.preventDefault();
        show(
          query.value.trim()
            ? (
                await api(
                  `${base}/memory-search?query=${encodeURIComponent(query.value)}`,
                )
              ).results
            : data.memories,
        );
      },
    },
    query,
    node("button", { className: "secondary", type: "submit" }, "检索"),
  );
  return [
    heading(
      "让项目经验持续积累",
      "记录可更正、可检索的观察，并保留它来自哪里。检索沿用当前绑定的记忆后端。",
      button("＋ 新增记忆", () => memoryDialog(data, base), "primary"),
    ),
    searchForm,
    cards,
    row(
      button("同步记忆投影", async () => {
        const result = await api(`${base}/memory-sync`, {});
        modal("记忆同步结果", pre(result));
      }),
      button("重建远端投影", async () => {
        const result = await api(`${base}/memory-sync?rebuild=true`, {});
        modal("投影重建结果", pre(result));
      }),
    ),
    node(
      "p",
      { className: "form-note" },
      "重建适用于远端 workspace 被清空或迁移后。删除不改写已归档的工具输入和独立备份。",
    ),
  ];
}
function memoryDialog(data, base, item) {
  modal(
    item ? "更正项目记忆" : "新增项目记忆",
    form(
      [
        field("记忆正文", "text", item?.text || "", "textarea", {
          required: true,
          maxlength: 100000,
        }),
        field("来源 URI", "uri", item?.source.uri || "", "text", {
          required: true,
          placeholder: "git:docs/design.md 或资料 URL",
        }),
        field(
          "来源版本 / SHA",
          "source_revision",
          item?.source.revision || "",
          "text",
          { required: true, placeholder: "提交 SHA、快照 SHA 或明确版本" },
        ),
      ],
      "保存记忆",
      async (values) => {
        await api(`${base}/memories`, {
          text: values.get("text"),
          source: {
            uri: values.get("uri"),
            revision: values.get("source_revision"),
          },
          id: item?.id || null,
          revision: item?.revision || 0,
        });
        $("#dialog").close();
        await refresh(data.project.id);
        notify("记忆已保存");
      },
    ),
  );
}
function skillsView(data, base) {
  const versions = data.skills.versions;
  const versionOptions = versions.map((item) => [
    item.digest,
    `${item.name} · ${short(item.digest)}`,
  ]);
  const activeDigest = data.skills.active[0]?.digest || versionOptions[0]?.[0];
  const candidateDigest =
    versions.find((item) => item.digest !== activeDigest)?.digest ||
    activeDigest;
  const baseline = select(versionOptions, activeDigest, "baseline");
  const candidate = select(versionOptions, candidateDigest, "candidate");
  const diffResult = node("div");
  const suites = data.evaluations.suites;
  const suite = select(
    suites.map((item) => [
      item.digest,
      `${short(item.digest)} · ${item.manifest.cases.length} cases`,
    ]),
    suites[0]?.digest,
    "suite",
  );
  async function evaluate(digest) {
    if (!suite.value || !digest) throw new Error("先导入 Skill 并注册评价集");
    notify("正在执行可信 evaluator；请保留页面或稍后刷新查看证据");
    const result = await api(`${base}/evaluations/run`, {
      digest,
      suite: suite.value,
    });
    await refresh(data.project.id);
    modal("评价记录", pre(result));
  }
  const runOptions = data.evaluations.runs.map((item) => [
    item.id,
    `${short(item.skill)} · ${item.status} · ${short(item.id)}`,
  ]);
  const baseRun = select(
    runOptions,
    data.evaluations.runs.find((item) => item.skill === activeDigest)?.id,
    "baseline_run",
  );
  const candidateRun = select(
    runOptions,
    data.evaluations.runs.find((item) => item.skill === candidateDigest)?.id,
    "candidate_run",
  );
  const comparison = node("div");
  async function compare() {
    if (!baseRun.value || !candidateRun.value)
      throw new Error("先完成双方评价");
    const baselineId = baseRun.value,
      candidateId = candidateRun.value;
    const result = await api(
      `${base}/evaluations/compare?baseline=${encodeURIComponent(baselineId)}&candidate=${encodeURIComponent(candidateId)}`,
    );
    const candidateVersion = versions.find(
      (item) => item.digest === result.candidate,
    );
    const head = data.skills.active.find(
      (item) => item.name === candidateVersion?.name,
    );
    comparison.replaceChildren(
      node(
        "div",
        { className: `result-box ${result.eligible ? "" : "rejected"}` },
        node(
          "strong",
          {},
          result.eligible
            ? "评价门禁通过 · 等待审阅采用"
            : "候选尚不满足采用条件",
        ),
        pre(result),
        result.eligible
          ? form(
              [field("采用理由", "reason", "", "textarea", { required: true })],
              "采用候选",
              async (values) => {
                await api(`${base}/skills/adopt`, {
                  baseline_run: baselineId,
                  candidate_run: candidateId,
                  revision: head?.revision || 0,
                  reason: values.get("reason"),
                });
                await refresh(data.project.id);
                notify("候选已采用；下一次工具调用可选择该活动 Skill");
              },
            )
          : null,
      ),
    );
  }
  const items = versions.map((item) => {
    const head = data.skills.active.find((active) => active.name === item.name);
    const active = head?.digest === item.digest;
    return node(
      "div",
      { className: "list-item" },
      node(
        "div",
        { className: "row-between" },
        node(
          "div",
          { className: "version-heading" },
          node("strong", {}, item.name),
          badge(
            active ? `活动修订 ${head.revision}` : "候选 / 历史",
            active ? "green" : "gray",
          ),
        ),
        button("版本详情", () => modal("Skill 版本", pre(item)), "text-button"),
      ),
      node("div", { className: "version-meta mono" }, item.digest),
      node("p", { className: "form-note" }, item.hypothesis),
      !active && data.skills.history.some((event) => event.to === item.digest)
        ? button(
            "回退到此版本",
            () =>
              modal(
                "回退活动 Skill",
                form(
                  [
                    field("回退理由", "reason", "", "textarea", {
                      required: true,
                    }),
                  ],
                  "确认回退",
                  async (values) => {
                    await api(`${base}/skills/rollback`, {
                      name: item.name,
                      digest: item.digest,
                      revision: head.revision,
                      reason: values.get("reason"),
                    });
                    $("#dialog").close();
                    await refresh(data.project.id);
                    notify("活动版本已回退");
                  },
                ),
              ),
            "text-button",
          )
        : null,
    );
  });
  const controls = panel(
    "比较与评价",
    "固定评价集，检查完整目录变更；双方证据使用相同 suite。",
    node(
      "div",
      { className: "form-grid" },
      node("label", {}, "基线版本", baseline),
      node("label", {}, "候选版本", candidate),
    ),
    row(
      button("比较版本", async () => {
        if (!baseline.value || !candidate.value)
          throw new Error("先导入两个版本");
        const result = await api(
          `${base}/skills/diff?baseline=${baseline.value}&candidate=${candidate.value}`,
        );
        const diff = pre(
          result.diff || "SKILL.md 无文本变化；请核对其他文件。",
        );
        diff.className = "diff";
        diffResult.replaceChildren(
          node(
            "p",
            { className: "form-note" },
            `变更文件：${result.changed_files.join(", ") || "无"}`,
          ),
          diff,
        );
      }),
    ),
    diffResult,
    node("hr"),
    node("label", {}, "固定评价集", suite),
    row(
      button("评价基线", () => evaluate(baseline.value), "secondary", {
        disabled: !suites.length,
      }),
      button("评价候选", () => evaluate(candidate.value), "secondary", {
        disabled: !suites.length,
      }),
    ),
    node("hr"),
    node(
      "div",
      { className: "form-grid" },
      node("label", {}, "基线评价记录", baseRun),
      node("label", {}, "候选评价记录", candidateRun),
    ),
    row(
      button("比较评价证据", compare, "primary", {
        disabled: !runOptions.length,
      }),
    ),
    comparison,
    node(
      "details",
      {},
      node("summary", {}, "注册评价集 JSON"),
      form(
        [
          field("评价集 JSON", "manifest", "", "textarea", {
            required: true,
            placeholder:
              "按 docs/INTEGRATIONS.md 的 schema 填写；使用可信评分命令与独立保留集",
          }),
        ],
        "固定并注册评价集",
        async (values) => {
          await api(
            `${base}/evaluations/suites`,
            JSON.parse(values.get("manifest")),
          );
          await refresh(data.project.id);
          notify("评价集已固定并登记");
        },
      ),
    ),
  );
  return [
    heading(
      "用证据改进 Skill",
      "导入完整 Agent Skills 目录。新版本先成为候选，通过正确性、验证集和保留集门禁后再采用。",
      button(
        "＋ 导入目录",
        () =>
          modal(
            "导入 Skill",
            form(
              [
                field("本机 Skill 目录", "directory", "", "text", {
                  required: true,
                  placeholder: "/path/to/my-skill",
                }),
                field(
                  "改进假设",
                  "hypothesis",
                  "Imported candidate",
                  "textarea",
                  { required: true },
                ),
                node(
                  "p",
                  {},
                  "目录名称须与 SKILL.md 中的 name 一致。首次同名导入建立初始基线，后续版本只创建候选。",
                ),
              ],
              "导入 Skill",
              async (values) => {
                await api(`${base}/skills/import`, Object.fromEntries(values));
                $("#dialog").close();
                await refresh(data.project.id);
                notify("Skill 版本已导入");
              },
            ),
          ),
        "primary",
      ),
    ),
    node(
      "div",
      { className: "grid-two" },
      controls,
      panel(
        "版本与活动状态",
        null,
        items.length ? items : empty("还没有 Skill。先导入一个标准目录。"),
      ),
    ),
    panel(
      "有限优化",
      `当前优化工具：${data.project.bindings.optimizer.tool}。优化只产生候选，采用继续使用上方证据门禁。`,
      data.project.bindings.optimizer.tool === "gepa"
        ? form(
            [
              field("优化目标", "objective", "", "textarea", {
                required: true,
              }),
              node(
                "div",
                { className: "form-grid" },
                field("最多 metric calls", "max_evaluations", 20, "number", {
                  min: 1,
                  max: 1000,
                }),
                field("最多提案", "max_proposals", 5, "number", {
                  min: 1,
                  max: 100,
                }),
                field("总时限（秒）", "timeout", 300, "number", {
                  min: 1,
                  max: 3600,
                }),
              ),
            ],
            "运行 GEPA 优化",
            async (values) => {
              if (!baseline.value || !suite.value)
                throw new Error("先选择基线和评价集");
              const result = await api(`${base}/optimizations`, {
                baseline: baseline.value,
                suite: suite.value,
                objective: values.get("objective"),
                max_evaluations: Number(values.get("max_evaluations")),
                max_proposals: Number(values.get("max_proposals")),
                timeout: Number(values.get("timeout")),
              });
              await refresh(data.project.id);
              modal("优化记录", pre(result));
            },
          )
        : node(
            "p",
            {},
            "可手动导入改进候选，或在工具绑定中选择 GEPA 并配置 JSON 提案器。",
          ),
      ...data.optimizations.slice(0, 5).map((item) =>
        row(
          status(item.status),
          node("code", {}, short(item.id)),
          button("查看证据", () => modal("优化证据", pre(item)), "text-button"),
        ),
      ),
    ),
    panel(
      "评价历史",
      null,
      table(
        ["候选", "状态", "报告成本", "证据"],
        data.evaluations.runs.map((item) => [
          short(item.skill),
          status(item.status),
          item.reported_cost,
          button("查看记录", () => modal("评价证据", pre(item)), "text-button"),
        ]),
      ),
    ),
  ];
}
function researchView(data, base) {
  const observing = form(
    [
      field("来源 URL（每行一个，最多 10 个）", "urls", "", "textarea", {
        required: true,
        placeholder: "https://example.com/official-doc",
      }),
      node(
        "div",
        { className: "form-grid" },
        field("正文总预算（字节）", "max_bytes", 1000000, "number", {
          min: 1,
          max: 10000000,
        }),
        field("总时限（秒）", "timeout", 30, "number", { min: 1, max: 300 }),
      ),
      field("观察 ID（可选；相同 ID 的输入被冻结）", "id"),
      checkbox("允许可信内网来源", "allow_private"),
      node(
        "p",
        { className: "form-note" },
        "页面内容只作为资料；不会执行其中指令或自动写入有效记忆。",
      ),
    ],
    "观察指定来源",
    async (values) => {
      const result = await api(`${base}/research-runs`, {
        urls: lines(values.get("urls")),
        max_bytes: Number(values.get("max_bytes")),
        timeout: Number(values.get("timeout")),
        id: values.get("id") || null,
        allow_private: values.has("allow_private"),
      });
      await refresh(data.project.id);
      modal("资料观察结果", pre(result));
    },
  );
  const proposals = data.research.proposals.map((item) =>
    node(
      "div",
      { className: "list-item" },
      node(
        "div",
        { className: "row-between" },
        node("span", { className: "url" }, item.url),
        status(item.status),
      ),
      node(
        "div",
        { className: "version-meta mono" },
        `SHA ${short(item.sha)} · ${item.observed}`,
      ),
      row(
        button(
          "核对资料",
          async () => {
            const source = await api(`${base}/research-proposals/${item.id}`);
            modal("核对来源快照", [
              node("p", { className: "url" }, source.final_url),
              node("small", { className: "mono" }, source.sha),
              pre(source.text),
              form(
                [
                  field("审阅理由", "reason", "", "textarea", {
                    required: true,
                  }),
                  selectField(
                    "处理方式",
                    [
                      ["reviewed", "已核对"],
                      ["dismissed", "不采用此资料"],
                    ],
                    "reviewed",
                    "status",
                  ),
                ],
                "保存资料审阅",
                async (values) => {
                  await api(`${base}/research-proposals/${item.id}/review`, {
                    status: values.get("status"),
                    reason: values.get("reason"),
                    revision: source.revision,
                  });
                  $("#dialog").close();
                  await refresh(data.project.id);
                  notify("资料审阅已记录；活动记忆与 Skill 由你单独决定");
                },
              ),
            ]);
          },
          "text-button",
        ),
      ),
    ),
  );
  return [
    heading(
      "观察资料变化",
      "明确来源与预算，保存可核对的快照。只有内容变化才产生新提案，重复观察保留记录。",
    ),
    node(
      "div",
      { className: "grid-two equal-columns" },
      panel("发起观察", null, observing),
      panel(
        "资料提案",
        null,
        proposals.length
          ? proposals
          : empty("尚无来源快照。先发起一次资料观察。"),
      ),
    ),
    panel(
      "观察记录",
      "操作中可以刷新列表并请求取消；终态由实际执行确认。",
      table(
        ["观察 ID", "状态", "正文计费", "操作"],
        data.research.runs.map((item) => [
          node("code", {}, item.id),
          status(item.status),
          `${item.bytes} bytes${item.reserved_bytes ? ` + ${item.reserved_bytes} reserved` : ""}`,
          row(
            button("记录", () => modal("观察证据", pre(item)), "text-button"),
            item.status === "running"
              ? button(
                  "请求取消",
                  async () => {
                    await api(`${base}/research-runs/${item.id}/cancel`, {});
                    await refresh(data.project.id);
                    notify("取消请求已登记；刷新确认实际终态");
                  },
                  "text-button danger",
                )
              : null,
          ),
        ]),
      ),
    ),
    panel(
      "持久调度",
      `当前调度工具：${data.project.bindings.scheduler.tool}`,
      pre(
        `ergora research worker ${data.project.id}\nergora research schedule ${data.project.id} create docs-check --url https://example.com/official-doc --interval 86400\nergora research schedule ${data.project.id} trigger docs-check\nergora research schedule ${data.project.id} resume docs-check`,
      ),
      node(
        "p",
        {},
        "Temporal Schedule 默认暂停；先配置 scheduler、启动 worker 并核对一次触发结果，再启用。每次有独立预算，长期总量由频率和预算共同决定。",
      ),
    ),
  ];
}
function workflowView(data, base) {
  const current = workflow?.project === data.project.id ? workflow : null;
  const templateChoice = select(
    [
      ["repository-governance", "存量仓库治理"],
      ["large-change", "大型开发任务"],
      ["training-optimization", "训练优化实验"],
    ],
    current?.kind || "large-change",
    "template",
  );
  templateChoice.setAttribute("aria-label", "工作流模板");
  async function loadTemplate() {
    const epoch = ++workflowEpoch;
    const kind = templateChoice.value;
    const result = await api(`/api/templates/${kind}`);
    if (epoch !== workflowEpoch || app.project !== data.project.id) return;
    workflow = {
      project: data.project.id,
      kind,
      id: "my-task",
      revision: 0,
      selected: 0,
      ...result,
    };
    render();
  }
  const draftChoice = select(
    [
      ["", "打开已保存草稿…"],
      ...data.drafts.map((item) => [item.id, `${item.id} · r${item.revision}`]),
    ],
    "",
    "saved_draft",
  );
  draftChoice.setAttribute("aria-label", "已保存草稿");
  draftChoice.addEventListener("change", () => {
    const saved = data.drafts.find((item) => item.id === draftChoice.value);
    if (saved) {
      workflowEpoch++;
      workflow = { ...structuredClone(saved), selected: 0 };
      render();
    }
  });
  const contents = [
    heading(
      "设计可执行的协作关系",
      "保持六阶段合同，编辑 work units 的依赖、路径和说明；服务端复用正式编译器校验。",
    ),
    node(
      "div",
      { className: "workflow-toolbar" },
      templateChoice,
      button("载入模板", loadTemplate, "primary"),
      draftChoice,
    ),
    node(
      "div",
      { className: "stage-strip" },
      stages.map((stage) => node("span", {}, stage)),
    ),
  ];
  if (!current)
    return [
      ...contents,
      panel(
        "从模板或草稿开始",
        "先载入模板，再选择工作单元编辑依赖关系。训练优化使用独立 workload / experiment 模板。",
      ),
    ];
  const requirements =
    current.agents || app.bootstrap.agent_contracts[current.kind];
  contents.push(
    panel(
      "模板角色与 Agent 选择",
      "模板声明能力和产物；在工具绑定中选择实现，模板正文保持一致。",
      table(
        ["角色", "所需能力", "当前 Agent", "产物"],
        Object.entries(requirements.agents).map(([role, requirement]) => [
          role,
          requirement.capabilities.join(", "),
          bindingFor(data.project, role).tool,
          requirement.artifacts.join(", "),
        ]),
      ),
      node(
        "p",
        {},
        current.kind === "training-optimization"
          ? "提案与原生候选需要可信 runner 和独立测量后才能放行。"
          : "integrate / verify 由可信执行器运行；工作单元的 test-results 也来自可信检查。",
      ),
    ),
  );
  if (current.kind === "training-optimization")
    return [
      ...contents,
      panel(
        "训练优化模板",
        "先固定 workload 合同与 baseline，再运行精确实验和证据门禁。可下载文件，或用 CLI 复制完整模板目录。",
        pre("ergora templates copy training-optimization ./training-task"),
        Object.entries(current.files).map(([name, text]) =>
          node(
            "details",
            {},
            node("summary", {}, name),
            pre(text),
            button("下载文件", () => download(name, text)),
          ),
        ),
      ),
      kernelPanel(data, base),
    ];
  const input = current.input;
  const units = input.work_units;
  current.selected = Math.min(current.selected, units.length - 1);
  const selected = units[current.selected];
  const unitSelect = select(
    units.map((item, index) => [String(index), item.id]),
    String(current.selected),
    "unit",
  );
  unitSelect.addEventListener("change", () => {
    current.selected = Number(unitSelect.value);
    render();
  });
  const dependencies = node(
    "select",
    { name: "depends_on", multiple: true, "aria-label": "依赖工作单元" },
    units
      .filter((unit) => unit !== selected)
      .map((unit) =>
        node(
          "option",
          { value: unit.id, selected: selected.depends_on.includes(unit.id) },
          unit.id,
        ),
      ),
  );
  const editor = form(
    [
      node("label", {}, "当前工作单元", unitSelect),
      field("单元 ID", "unit_id", selected.id, "text", { required: true }),
      node("label", {}, "依赖工作单元（可多选）", dependencies),
      field(
        "可写路径（每行一个）",
        "paths",
        selected.paths.join("\n"),
        "textarea",
        { required: true },
      ),
      field("任务说明", "instructions", selected.instructions, "textarea", {
        required: true,
      }),
    ],
    "更新单元草稿",
    (values) => {
      workflowEpoch++;
      const oldId = selected.id,
        newId = values.get("unit_id").trim();
      if (units.some((unit) => unit !== selected && unit.id === newId))
        throw new Error("单元 ID 已存在");
      selected.id = newId;
      selected.paths = lines(values.get("paths"));
      selected.instructions = values.get("instructions");
      selected.depends_on = values.getAll("depends_on");
      units
        .filter((unit) => unit !== selected)
        .forEach((unit) => {
          unit.depends_on = unit.depends_on.map((dependency) =>
            dependency === oldId ? newId : dependency,
          );
        });
      current.validation = null;
      render();
      notify("已更新本次页面草稿；保存时将校验全部输入");
    },
  );
  editor.addEventListener("input", () => workflowEpoch++);
  const draftId = node("input", {
    value: current.id,
    name: "draft_id",
    "aria-label": "草稿 ID",
  });
  draftId.addEventListener("input", () => workflowEpoch++);
  async function validate(save) {
    const epoch = ++workflowEpoch;
    const payload = {
      id: draftId.value,
      kind: current.kind,
      input,
      revision:
        draftId.value === current.id
          ? current.revision
          : app.data.drafts.find((draft) => draft.id === draftId.value)
              ?.revision || 0,
    };
    const result = await api(
      `${base}/drafts${save ? "" : "/validate"}`,
      payload,
    );
    if (app.project !== data.project.id) return;
    if (save) {
      // The server saved this snapshot even if the user has since edited it.
      app.data.drafts = app.data.drafts.filter(
        (draft) => draft.id !== result.id,
      );
      app.data.drafts.push(result);
      if (workflow !== current || epoch !== workflowEpoch) {
        if (workflow === current && current.id === result.id) {
          current.revision = result.revision;
          current.validation = null;
        }
        notify("提交时的快照已保存；页面中的较新编辑仍未保存");
        return;
      }
      workflow = { ...result, selected: current.selected };
      render();
    }
    if (!save && (workflow !== current || epoch !== workflowEpoch)) return;
    notify(
      save ? "草稿已校验并持久保存" : "输入合同校验通过；这不代表正式任务验收",
    );
  }
  const json = node("textarea", {
    className: "workflow-json",
    value: JSON.stringify(input, null, 2),
    "aria-label": "完整任务输入 JSON",
  });
  json.addEventListener("input", () => workflowEpoch++);
  return [
    ...contents,
    node(
      "div",
      { className: "workflow-toolbar" },
      draftId,
      button("校验输入", () => validate(false)),
      button("保存草稿", () => validate(true), "primary"),
      button("下载 input.json", () =>
        download("input.json", JSON.stringify(input, null, 2) + "\n"),
      ),
      badge(`草稿修订 ${current.revision}`),
    ),
    node(
      "div",
      { className: "workflow-layout" },
      node(
        "section",
        { className: "panel graph-panel" },
        node(
          "div",
          { className: "graph-header" },
          node("h2", {}, "工作单元依赖图"),
          button(
            "＋ 单元",
            () => {
              workflowEpoch++;
              let index = units.length + 1;
              while (units.some((unit) => unit.id === `unit-${index}`)) index++;
              units.push({
                id: `unit-${index}`,
                depends_on: [],
                paths: [],
                instructions: "",
              });
              current.selected = units.length - 1;
              render();
            },
            "text-button",
          ),
        ),
        node("div", {
          id: "workflow-graph",
          className: "graph",
          role: "img",
          "aria-label": "工作单元有向依赖图",
        }),
        node(
          "div",
          { className: "graph-footer" },
          "点击节点选择单元；拖动只调整显示。依赖和写入范围由右侧表单编辑。",
        ),
      ),
      panel(
        "编辑工作单元",
        null,
        editor,
        button(
          "删除当前单元",
          () => {
            workflowEpoch++;
            if (units.length <= 1) throw new Error("至少保留一个工作单元");
            input.work_units = units.filter((unit) => unit !== selected);
            input.work_units.forEach((unit) => {
              unit.depends_on = unit.depends_on.filter(
                (id) => id !== selected.id,
              );
            });
            current.selected = 0;
            render();
          },
          "text-button danger",
        ),
      ),
    ),
    panel(
      "完整任务输入",
      "目标、允许路径、验收条件和约束一并保存在 input.json；JSON 载入也通过服务端合同校验。",
      json,
      row(
        button("校验并载入 JSON", async () => {
          const epoch = ++workflowEpoch;
          const taskInput = JSON.parse(json.value);
          await api(`${base}/drafts/validate`, {
            id: current.id,
            kind: current.kind,
            input: taskInput,
            revision: current.revision,
          });
          if (
            app.project !== data.project.id ||
            workflow !== current ||
            epoch !== workflowEpoch
          )
            return;
          current.input = taskInput;
          current.selected = 0;
          render();
          notify("已载入有效任务输入");
        }),
      ),
    ),
    node(
      "div",
      { className: "info-bar" },
      "草稿不启动工具或正式任务。下载 input.json 后，按使用手册使用参考编译、冻结和六阶段执行入口。",
    ),
  ];
}
let kernelInvocation = 0;
function kernelPanel(data, base) {
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
    `生成工具：${bindingFor(data.project, "kernel").tool}。先配置任务与预算，计划检查不运行模型或 GPU。`,
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
function drawGraph() {
  if (!window.cytoscape) {
    $("#workflow-graph").append(
      empty("图组件未加载。仍可使用工作单元表单与 JSON 编辑。"),
    );
    return;
  }
  const units = workflow.input.work_units;
  graph = window.cytoscape({
    container: $("#workflow-graph"),
    elements: [
      ...units.map((unit, index) => ({
        data: { id: `unit:${unit.id}`, label: unit.id, index },
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
    layout: {
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
  graph.on("tap", "node", (event) => {
    workflow.selected = event.target.data("index");
    render();
  });
}
$("#project-select").addEventListener("change", (event) => {
  app.project = event.target.value;
  workflowEpoch++;
  workflow = null;
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
$("#add-project").addEventListener("click", projectDialog);
$("#help").addEventListener("click", helpDialog);
refresh().catch((error) => {
  $("#main").replaceChildren(
    heading(
      "无法读取工作空间",
      error.message,
      button("重试", () => refresh()),
    ),
  );
  notify(error.message, true);
});
