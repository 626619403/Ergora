import { api } from "./api.js";
import {
  $, node, button, pre, lines, short, heading, panel, empty, row,
  select, field, badge, status, notify, form, modal, download, table,
} from "./ui.js";
import { app, bindingFor, stages } from "./state.js";

// Drafts, request epochs and the graph share one lifecycle owner.
let workflowEpoch = 0, graph, workflow;

export function resetWorkflow() {
  workflowEpoch++;
  workflow = null;
}

export function disposeGraph() {
  if (graph) {
    graph.destroy();
    graph = null;
  }
}

export function workflowView(data, base, { refresh, render }) {
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
          bindingFor(data, role).tool,
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
      kernelPanel(data, base, refresh),
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
    if (app.project !== data.project.id || app.data?.project.id !== data.project.id) return;
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
