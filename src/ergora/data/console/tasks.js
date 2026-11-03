import { api } from "./api.js";
import {
  node, button, pre, heading, panel, empty, row, field, badge, form, table,
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
      detail.replaceChildren(panel("任务合同读取失败", contract.reason.message,
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
