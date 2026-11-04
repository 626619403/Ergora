import { api } from "./api.js";
import {
  $, node, button, pre, heading, panel, empty, row, field, select, badge, form, modal, table,
} from "./ui.js";
import { stages } from "./state.js";

const stageForPhase = {
  INVENTORY: "inventory", PLANNING: "plan", IMPLEMENTING: "work",
  INTEGRATING: "integrate", VERIFYING: "verify", REVIEWING: "review",
};
const disclosure = (title, value) =>
  node("details", {}, node("summary", {}, title), pre(value));
const facts = (items) =>
  node("dl", { className: "task-facts" }, items.map(([name, value]) => [
    node("dt", {}, name), node("dd", {}, value ?? "未返回"),
  ]));

export function tasksView(data, base) {
  const title = heading("正式任务", "查看冻结合同、原运行和候选结果。工作流设计中的草稿另行保存。");
  if (data.project.registration?.status !== "published")
    return [title, panel("先完成项目登记", "正式任务需要统一注册的执行目录、模板和可信检查。按仓库docs/PROJECTS.md准备项目定义，通过CLI发布或恢复登记后刷新页面。",
      pre(`ergora project register project.json --revision ${data.project.revision}\nergora project registration ${data.project.id}`))];

  const selectionKey = `ergora-task:${data.project.id}`;
  let selected = sessionStorage.getItem(selectionKey) || "";
  let listSequence = 0;
  let detailSequence = 0;
  let pageIndex = 0;
  const cursors = [null];
  let page;
  const entries = node("div", { "aria-live": "polite" });
  const pageNote = node("p", { className: "form-note" });
  const detail = node("div", { className: "task-detail", "aria-live": "polite" }, empty("选择一个任务查看合同。"));
  const previous = button("上一页", () => { pageIndex--; loadPage(); });
  const next = button("下一页", () => {
    cursors[++pageIndex] = page.next_after;
    loadPage();
  });
  const view = node("div", { className: "task-layout" },
    panel("任务合同", "每页最多扫描20条记录；运行状态需单独查询。", entries, pageNote,
      row(previous, next, button("重新读取列表", () => { pageIndex = 0; loadPage(); }))),
    detail,
  );
  title.append(row(
    button("预览与创建", () => creationDialog(), "primary"),
    button("按 ID 读取创建记录", () => creationLookup()),
  ));

  function selectPublished(record) {
    if (record.status !== "published") return;
    inspect(record.task_id);
    pageIndex = 0;
    loadPage();
  }

  function creationRecord(record, target, active) {
    const descriptions = {
      not_recorded: "没有统一创建记录；目录存在也不能证明创建成功，旧任务不由恢复入口接管。",
      pending: "原意图已保存，合同尚未完整发布。恢复将沿用原冻结内容和角色。",
      published: "冻结合同已完整发布；创建操作没有提交运行。",
      conflict: "现有合同与原意图冲突。请检查原文件；页面不会覆盖冲突内容。",
    };
    target.replaceChildren(panel(`创建记录：${record.status}`, descriptions[record.status],
      facts([
        ["任务 ID", record.task_id], ["项目当前修订", record.project_revision],
        ["原创建修订", record.created_revision], ["原意图 SHA256", record.intent_sha256],
        ["编译结果 SHA256", record.compiled_sha256],
      ]),
      disclosure("完整创建记录与冻结角色", record),
      record.status === "pending" ? form([], "确认恢复原创建", async () => {
        if (!active()) return;
        let resumed;
        try {
          resumed = await api(`${base}/tasks/${encodeURIComponent(record.task_id)}/resume-create`, {
            revision: record.project_revision, intent_sha256: record.intent_sha256,
          });
        } catch (error) {
          if (active()) creationUnknown(record.task_id, error, target, active);
          return;
        }
        if (!active()) return;
        creationRecord(resumed, target, active);
        selectPublished(resumed);
      }) : null,
      row(
        button("重新读取原创建记录", () => {
          if (active()) creationLookup(record.task_id);
        }),
        record.status === "published" ? button("查看正式任务", () => {
          if (!active()) return;
          $("#dialog").close();
          inspect(record.task_id);
        }) : null,
      ),
    ));
  }

  function creationUnknown(taskId, error, target, active) {
    target.replaceChildren(panel("操作结果尚未确认", error.message,
      node("p", {}, `请保留原任务 ID：${taskId}。先读取原创建记录，再决定是否恢复；不要据此更换 ID 或重发创建。`),
      button("按原 ID 读取创建记录", () => {
        if (active()) creationLookup(taskId);
      }),
    ));
  }

  function creationLookup(taskId = "") {
    let sequence = 0;
    const result = node("div", { "aria-live": "polite" });
    const idField = field("原任务 ID", "task_id", taskId, "text", {
      required: true, maxlength: 80, autocomplete: "off", readonly: taskId ? true : null,
    });
    const content = node("div", {},
      node("p", {}, "未完整发布的任务可能不在列表中。此入口只读创建记录，不查询或启动执行。"),
      form([idField], "读取创建记录", async (values) => {
        if (!active()) return;
        const reading = ++sequence;
        result.replaceChildren(empty("正在读取原创建记录…"));
        try {
          const record = await api(`${base}/tasks/${encodeURIComponent(values.get("task_id"))}/creation`);
          if (current(reading)) creationRecord(record, result, () => current(reading));
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("创建记录读取失败", error.message));
        }
      }), result,
    );
    const active = () => view.isConnected && content.isConnected && $("#dialog").open;
    const current = (reading) => active() && reading === sequence;
    idField.addEventListener("input", () => { sequence++; result.replaceChildren(); });
    modal("按原 ID 读取与恢复创建", content);
  }

  function creationDialog() {
    const kinds = data.project.registration.definition.templates.filter((kind) =>
      ["repository-governance", "large-change"].includes(kind));
    if (!kinds.length) {
      modal("没有已登记的开发模板", node("p", {}, "此项目使用独立训练合同；请使用工作流设计中的训练优化入口。"));
      return;
    }
    const kind = select(kinds, kinds[0], "task_type");
    const draft = select([
      ["", "选择已保存草稿…"],
      ...data.drafts.filter((item) => kinds.includes(item.kind)).map((item) =>
        [item.id, `${item.id} · ${item.kind} · r${item.revision}`]),
    ], "", "saved_draft");
    const inputField = field("完整任务输入 JSON", "input", "", "textarea", {
      required: true, className: "workflow-json", spellcheck: "false",
    });
    const input = inputField.querySelector("textarea");
    const result = node("div", { "aria-live": "polite" });
    let sequence = 0;
    let creationLocked = false;
    const fields = node("fieldset", { className: "task-creation-fields" },
      node("label", {}, "已登记开发模板", kind),
      row(button("载入所选模板", loadTemplate), node("label", {}, "从草稿载入输入", draft)),
      field("新任务 ID", "task_id", "", "text", { required: true, maxlength: 80, autocomplete: "off" }),
      field("工单编号或本地标识", "issue_id", "", "text", { required: true, maxlength: 160 }),
      field("起始提交 SHA（可选，留空使用登记基线）", "starting_sha", "", "text", { maxlength: 40 }),
      inputField,
    );
    const editor = form([fields], "预览冻结合同", async (values) => {
      if (!active() || creationLocked) return;
      const reading = ++sequence;
      result.replaceChildren(empty("正在编译预览…"));
      let snapshot;
      try {
        const definition = {
          schema_version: 1, task_id: values.get("task_id"), task_type: values.get("task_type"),
          issue_id: values.get("issue_id"), input: JSON.parse(values.get("input")),
        };
        if (values.get("starting_sha")) definition.starting_sha = values.get("starting_sha");
        snapshot = await api(`${base}/tasks/preview`, { definition, revision: data.project.revision });
      } catch (error) {
        if (current(reading)) result.replaceChildren(panel("预览失败", error.message));
        return;
      }
      if (!current(reading)) return;
      const bindings = snapshot.files["agent-bindings.json"];
      result.replaceChildren(panel("审阅冻结预览", "确认后只发布此合同，启动运行另行操作。",
        facts([
          ["项目修订", snapshot.project_revision], ["任务 ID", snapshot.definition.task_id],
          ["模板", snapshot.definition.task_type], ["工单", snapshot.definition.issue_id],
          ["基线提交", snapshot.files["task.spec.json"].request.repository.base_sha],
          ["预览 SHA256", snapshot.preview_sha256],
        ]),
        table(["冻结角色", "工具", "模型"], Object.entries(bindings.bindings).map(([role, binding]) =>
          [role, binding.tool, binding.model ?? "未指定"])),
        disclosure("完整服务端预览与冻结文件", snapshot),
        form([], "确认创建冻结合同", async () => {
          if (!current(reading) || creationLocked) return;
          creationLocked = true;
          // Keep the original ID across reloads even if the publication reply is lost.
          sessionStorage.setItem(selectionKey, snapshot.definition.task_id);
          fields.disabled = true;
          editor.querySelector('button[type="submit"]').disabled = true;
          result.replaceChildren(empty(`正在创建 ${snapshot.definition.task_id}；请保留此原任务 ID。关闭页面不会撤销已发出的操作。`));
          let record;
          try {
            record = await api(`${base}/tasks`, {
              definition: snapshot.definition, revision: snapshot.project_revision,
              preview_sha256: snapshot.preview_sha256,
            });
          } catch (error) {
            if (current(reading)) creationUnknown(snapshot.definition.task_id, error, result, () => current(reading));
            return;
          }
          if (!current(reading)) return;
          creationRecord(record, result, () => current(reading));
          selectPublished(record);
        }),
      ));
    });
    const content = node("div", {},
      node("p", {}, "载入模板或兼容的已保存草稿，再编辑输入。修改字段会废弃旧预览；训练优化使用独立入口。"),
      editor, result,
    );
    const active = () => view.isConnected && content.isConnected && $("#dialog").open;
    const current = (reading) => active() && reading === sequence;
    function invalidate() {
      sequence++;
      result.replaceChildren(empty("输入已更改，请重新预览后确认。"));
    }
    async function loadTemplate() {
      if (!active() || creationLocked) return;
      invalidate();
      const reading = sequence;
      input.value = "";
      draft.value = "";
      result.replaceChildren(empty("正在读取模板…"));
      try {
        const template = await api(`/api/templates/${encodeURIComponent(kind.value)}`);
        if (!current(reading)) return;
        input.value = JSON.stringify(template.input, null, 2);
        result.replaceChildren(empty("已载入模板输入，请填写任务标识并审阅。"));
      } catch (error) {
        if (current(reading)) result.replaceChildren(panel("模板读取失败", error.message));
      }
    }
    kind.addEventListener("change", () => { draft.value = ""; input.value = ""; });
    draft.addEventListener("change", () => {
      const saved = data.drafts.find((item) => item.id === draft.value);
      if (!saved) return;
      kind.value = saved.kind;
      input.value = JSON.stringify(saved.input, null, 2);
    });
    editor.addEventListener("input", invalidate);
    editor.addEventListener("change", invalidate);
    modal("预览与创建正式任务", content);
  }

  function renderPage() {
    previous.disabled = pageIndex === 0;
    next.disabled = !page?.next_after;
    if (!page) return;
    pageNote.textContent = `第${pageIndex + 1}页 · 本页匹配${page.items.length}项，扫描${page.inspected_entries}条记录`;
    entries.replaceChildren(...[
      ...(page.items.length ? page.items.map((item) =>
        node("article", { className: "list-item" },
          button(item.task_id, () => inspect(item.task_id), "text-button task-choice", {
            "aria-current": item.task_id === selected ? "true" : null,
          }),
          node("small", { className: "muted" }, item.task_type),
          node("p", {}, item.goal),
        ),
      ) : [empty(page.next_after ? "本页没有匹配任务，可继续下一页。" : "本页没有匹配任务。")]),
      page.unreadable_count || page.errors.length
        ? disclosure(`读取异常：${page.unreadable_count}条无法读取，${page.errors.length}条合同无效`, page.errors)
        : null,
    ].filter(Boolean));
  }

  async function loadPage() {
    const sequence = ++listSequence;
    const query = new URLSearchParams({ limit: "20" });
    if (cursors[pageIndex]) query.set("after", cursors[pageIndex]);
    page = null;
    previous.disabled = true;
    next.disabled = true;
    pageNote.textContent = "";
    entries.replaceChildren(empty("正在读取任务合同…"));
    let result;
    try {
      result = await api(`${base}/tasks?${query}`);
    } catch (error) {
      if (view.isConnected && sequence === listSequence) {
        entries.replaceChildren(panel("任务列表读取失败", error.message));
        previous.disabled = pageIndex === 0;
      }
      return;
    }
    if (!view.isConnected || sequence !== listSequence) return;
    page = result;
    renderPage();
    if (!selected && page.items.length) inspect(page.items[0].task_id);
  }

  async function inspect(taskId) {
    const sequence = ++detailSequence;
    selected = taskId;
    sessionStorage.setItem(selectionKey, taskId);
    renderPage();
    detail.replaceChildren(empty(`正在读取 ${taskId}…`));
    const path = `${base}/tasks/${encodeURIComponent(taskId)}`;
    const [contract, submission] = await Promise.allSettled([api(path), api(`${path}/submission`)]);
    if (!view.isConnected || sequence !== detailSequence) return;
    if (contract.status === "rejected") {
      detail.replaceChildren(panel("任务合同读取失败", `${taskId} · ${contract.reason.message}`,
        button("按原 ID 读取创建记录", () => creationLookup(taskId)),
        button("重试任务详情", () => inspect(taskId))));
      return;
    }
    const task = contract.value;
    const request = task.spec.request;
    const input = request.input;
    const bindings = task.agent_bindings;
    const saved = submission.status === "fulfilled" ? submission.value : null;
    const runtime = node("div", {}, empty("尚未查询运行状态。查询会读取所登记的Temporal，合同存在不代表已经提交或完成。"));
    const runKey = `ergora-run:${data.project.id}:${taskId}`;
    const runField = field("原 run ID", "run_id", sessionStorage.getItem(runKey) || saved?.run_id || "", "text", {
      required: true, maxlength: 128, autocomplete: "off",
    });
    const runInput = runField.querySelector("input");
    let runSequence = 0;
    runInput.addEventListener("input", () => {
      runSequence++;
      runtime.replaceChildren(empty("run ID已更改，请重新查询。"));
    });

    function submissionDialog() {
      let readingSequence = 0;
      const result = node("div", { "aria-live": "polite" });
      const content = node("div", {},
        node("p", {}, "先读取本地创建与提交记录，再明确提交或恢复。关闭页面不会撤销已经发出的操作，未知结果不能直接重发。"),
        result,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        content.isConnected && $("#dialog").open;
      const current = (reading) => active() && reading === readingSequence;

      function showSubmission(creation, record, reading) {
        const descriptions = {
          not_recorded: "没有统一提交记录。确认后沿原生准入提交此冻结合同一次。",
          prepared: "原提交意图已保存，尚无派发检查点。明确恢复后，由原生流程决定是否继续首次派发。",
          unknown: "派发结果尚未确认。恢复只核对原工作流，不重新发起start；not_found仍不证明从未提交。",
          submitted: "本地回执已保存原run；这不代表六阶段完成。请按原run单独查询运行状态。",
          rejected: "原提交归属已被拒绝。请核对冲突记录，页面不会覆盖、重提或更换任务ID。",
        };
        const canStart = creation.status === "published" && record.status === "not_recorded";
        const canResume = creation.status === "published" && ["prepared", "unknown"].includes(record.status);
        if (record.status === "submitted") sessionStorage.setItem(runKey, record.run_id);
        result.replaceChildren(panel(`提交记录：${record.status}`, descriptions[record.status],
          facts([
            ["任务 ID", taskId], ["项目当前修订", creation.project_revision],
            ["创建状态", creation.status], ["原创建修订", creation.created_revision],
            ["原创建意图 SHA256", creation.intent_sha256],
            ["请求 SHA256", task.request_sha256], ["合同文件 SHA256", task.spec_file_sha256],
            ["原提交意图 SHA256", record.intent_sha256], ["原提交修订", record.submitted_revision],
            ["工作流 ID", record.workflow_id], ["原 run ID", record.run_id],
            ["原工作流恢复查询", record.reconciliation],
            ["归属拒绝原因", record.reason], ["冲突 run ID", record.conflicting_run_id],
          ]),
          disclosure("完整创建记录与冻结角色", creation),
          disclosure("冻结合同、输入与验收", task.spec),
          disclosure("完整本地提交记录", record),
          creation.status !== "published" ? empty("创建尚未完整发布；请先按原ID检查创建记录，不能提交运行。") : null,
          canStart || canResume ? form([], canStart ? "确认提交此冻结任务" : "确认恢复原提交意图", async () => {
            if (!current(reading)) return;
            result.replaceChildren(empty(`正在处理 ${taskId} 的原提交；关闭页面不取消操作。回复未知时先重新读取原记录。`));
            let observed;
            try {
              observed = await api(`${path}/${canStart ? "start" : "resume-start"}`, {
                revision: creation.project_revision, timeout: 20,
                ...(canStart ? { creation_sha256: creation.intent_sha256 }
                  : { intent_sha256: record.intent_sha256 }),
              });
            } catch (error) {
              if (current(reading)) result.replaceChildren(panel("提交结果尚未确认", error.message,
                node("p", {}, `请保留原任务 ID：${taskId}。先重新读取原提交记录；不要更换ID或重发start。`),
                button("重新读取原提交记录", read),
              ));
              return;
            }
            if (current(reading)) showSubmission(creation, observed, reading);
          }) : null,
          row(
            button("重新读取原提交记录", read),
            record.status === "submitted" ? button("查看原任务与运行", () => {
              if (!current(reading)) return;
              $("#dialog").close();
              inspect(taskId);
            }) : null,
          ),
        ));
      }

      async function read() {
        if (!active()) return;
        const reading = ++readingSequence;
        result.replaceChildren(empty(`正在读取 ${taskId} 的原创建与提交记录…`));
        let creation, record;
        try {
          [creation, record] = await Promise.all([api(`${path}/creation`), api(`${path}/submission`)]);
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("提交检查读取失败", error.message,
            node("p", {}, `原任务 ID：${taskId}。两份记录未完整读取，不提供写入确认。`),
            button("重新读取原提交记录", read),
          ));
          return;
        }
        if (current(reading)) showSubmission(creation, record, reading);
      }
      modal("检查提交与恢复", content);
      read();
    }

    detail.replaceChildren(
      panel(taskId, input.goal,
        row(badge(request.task_type), badge("冻结合同 · 本地读取")),
        facts([
          ["项目当前修订", task.project_revision],
          ["冻结角色修订", bindings?.project_revision],
          ["工单", `${request.tracker.kind} · ${request.tracker.project} #${request.tracker.issue_id}`],
          ["基线提交", request.repository.base_sha],
          ["请求 SHA256", task.request_sha256],
          ["合同 SHA256", task.spec_file_sha256],
        ]),
        disclosure("输入、验收与约束", input),
        disclosure("完整冻结合同", task.spec),
      ),
      panel("冻结角色与工作单元", "后续项目绑定调整不会更换此任务已冻结的选择。",
        bindings
          ? table(["角色", "工具", "模型"], Object.entries(bindings.bindings).map(([role, binding]) => [role, binding.tool, binding.model ?? "未指定"]))
          : empty("旧任务没有角色快照；这里不使用当前绑定补写历史。"),
        table(["工作单元", "前置依赖", "允许路径"], input.work_units.map((unit) => [
          unit.id, unit.depends_on.join("、") || "无", unit.paths.join("、"),
        ])),
        bindings ? disclosure("完整角色快照", bindings) : null,
      ),
      panel("本地提交回执", "回执记录操作事实；submitted不代表六阶段通过。",
        saved ? disclosure(`提交状态：${saved.status}`, saved)
          : node("p", { className: "task-error" }, `提交回执读取失败：${submission.reason.message}`),
        button("检查提交与恢复", submissionDialog),
      ),
      panel("原生运行", "按固定run读取。关闭页面不会取消任务；取消后的外部清理需另行对账。",
        form([runField], "读取原运行", async (values) => {
          const runId = values.get("run_id");
          sessionStorage.setItem(runKey, runId);
          const reading = ++runSequence;
          runtime.replaceChildren(empty("正在查询原运行…"));
          let observed;
          try {
            observed = await api(`${path}/status?${new URLSearchParams({ run_id: runId, timeout: "20" })}`);
          } catch (error) {
            if (view.isConnected && sequence === detailSequence && reading === runSequence)
              runtime.replaceChildren(panel("运行查询失败", error.message));
            return;
          }
          if (!view.isConnected || sequence !== detailSequence || reading !== runSequence) return;
          const state = observed.status || observed.outcome;
          const currentStage = observed.terminal ? null : stageForPhase[observed.phase];
          runtime.replaceChildren(...[
            row(badge(observed.runtime_status), observed.phase ? badge(observed.phase) : null),
            observed.runtime_status === "not_found"
              ? empty("未找到所选原运行；这不证明任务从未提交。请核对原run和提交回执。")
              : facts([
                ["工作流 ID", observed.workflow_id], ["原 run ID", observed.run_id],
                ["原运行已闭合", observed.terminal ? "是" : "否"],
                ["候选提交", state?.candidate_sha], ["计划 SHA256", state?.plan_sha256],
              ]),
            node("div", { className: "stage-strip", "aria-label": "六阶段位置" }, stages.map((stage) =>
              node("span", { className: currentStage === stage ? "current" : null }, stage))),
            observed.status ? facts([
              ["活动阶段/单元", observed.status.active_stages.join("、") || "无"],
              ["已完成阶段/单元", observed.status.completed_stages.join("、") || "无"],
            ]) : null,
            disclosure("原始运行与结果", observed),
          ].filter(Boolean));
        }),
        runtime,
      ),
    );
  }

  loadPage();
  if (selected) inspect(selected);
  return [title, view];
}
