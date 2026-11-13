import { api } from "./api.js";
import { node, button, pre, heading, panel, empty, row, table, short } from "./ui.js";
import { app } from "./state.js";

export function trainingView(data, base) {
  const project = data.project.id;
  const home = app.bootstrap.state_directory;
  const entries = node("div", { "aria-live": "polite" });
  const baseline = node("div");
  const note = node("p", { className: "form-note" });
  const detail = node("div", { className: "task-detail", "aria-live": "polite" }, empty("选择一个实验，查看完整合同与已保存证据。"));
  let pageSequence = 0, detailSequence = 0, pageIndex = 0, page;
  const cursors = [null];
  const previous = button("上一页", () => { pageIndex--; load(); });
  const next = button("下一页", () => { cursors[++pageIndex] = page.next_after; load(); });
  const view = node("div", { className: "task-layout" },
    node("div", {}, panel("当前基线", null, baseline),
      panel("原实验记录", "列表读取已保存文件；不会查询或启动训练。", entries, note,
        row(previous, next, button("重新读取列表", () => { pageIndex = 0; load(); })))), detail);
  const active = () => view.isConnected && app.project === project && app.tab === "training" && app.bootstrap.state_directory === home;

  async function inspect(id) {
    const sequence = ++detailSequence;
    detail.replaceChildren(empty(`正在读取实验 ${id}…`));
    try {
      const observed = await api(`${base}/training/${encodeURIComponent(id)}`);
      if (!active() || sequence !== detailSequence) return;
      const item = observed.experiment;
      const gate = item.recorded_gate;
      const live = node("div", { "aria-live": "polite" }, empty("尚未实时查询。"));
      let runtimeSequence = 0;
      async function queryRuntime() {
        const attempt = ++runtimeSequence;
        live.replaceChildren(empty("正在查询原运行状态…"));
        try {
          const result = await api(`${base}/training/${encodeURIComponent(id)}/status`);
          if (!active() || sequence !== detailSequence || attempt !== runtimeSequence) return;
          live.replaceChildren(result.runtime_status === "not_found"
            ? empty("原运行时明确未找到该工作流；本次查询没有提交实验。")
            : node("div", {}, table(["实时查询", "结果"], [
              ["原工作流", result.workflow_id], ["原运行 ID", result.run_id],
              ["控制工作流状态", result.temporal_status], ["原实验阶段", result.phase],
              ["控制工作流已结束", result.terminal ? "是；外部作业停止仍须核对" : "否"],
            ]), node("details", {}, node("summary", {}, "完整运行状态"), pre(result))));
        } catch (error) {
          if (active() && sequence === detailSequence && attempt === runtimeSequence)
            live.replaceChildren(panel("未取得实时状态", error.message));
        }
      }
      detail.replaceChildren(panel(`实验 ${item.experiment_id}`, "这些是原记录；运行状态未实时查询，统计和正确性未重新复验，也未授予采用。",
        table(["记录", "值"], [
          ["原作业 ID", item.job_id || "尚未读到作业请求"],
          ["已保存的执行结果", item.recorded_result_state || "尚未读到结果，当前状态未知"],
          ["执行开始记录", item.started_recorded ? "存在；不能证明仍在运行" : "未读到"],
          ["取消围栏记录", item.fence_recorded ? "存在；停止结果需沿原作业核对" : "未读到"],
          ["与当前基线匹配", item.baseline_matches ? "匹配" : item.baseline_error],
          ["原门禁记录", gate ? (gate.passed === true ? "记录通过；仍须原证据批准" : "记录未通过") : "尚无绑定的门禁报告"],
          ["原 evidence SHA256", gate?.evidence_sha256 || "未读到"],
          ["已有 MLflow run ID", gate?.mlflow_run_id || "未读到"],
          ["排队加执行窗口（秒）", item.max_run_seconds],
        ]),
        node("details", {}, node("summary", {}, "完整原件与文件摘要"), pre(observed)),
      ), panel("原运行状态", "点击后查询一次原工作流。查询不会启动、取消或批准训练，负结果与未确认取消会原样保留。",
        live, button("查询原运行状态", queryRuntime)));
    } catch (error) {
      if (active() && sequence === detailSequence)
        detail.replaceChildren(panel("未取得一致的实验记录", error.message,
          button("重新读取该实验", () => inspect(id))));
    }
  }

  async function load() {
    const sequence = ++pageSequence;
    previous.disabled = next.disabled = true;
    entries.replaceChildren(empty("正在读取实验列表…"));
    baseline.replaceChildren(empty("正在读取…"));
    const parameters = new URLSearchParams({ limit: "20" });
    if (cursors[pageIndex]) parameters.set("after", cursors[pageIndex]);
    try {
      const observed = await api(`${base}/training?${parameters}`);
      if (!active() || sequence !== pageSequence) return;
      page = observed;
      baseline.replaceChildren(observed.baseline ? node("div", {},
        table(["基线", "记录"], [
          ["ID", observed.baseline.baseline_id], ["代码提交", short(observed.baseline.commit)],
          ["Workload", short(observed.baseline.workload_fingerprint)],
        ]), node("details", {}, node("summary", {}, "完整基线与摘要"),
          pre({ baseline: observed.baseline, files: observed.baseline_files })))
        : empty("尚未初始化基线。按训练手册用原生 training init 登记真实 baseline。"));
      entries.replaceChildren(observed.items.length ? table(["实验"], observed.items.map((item) => [
        node("div", { className: "task-choice" }, node("strong", {}, item.experiment_id),
          node("p", { className: "form-note" }, `已保存结果：${item.recorded_result_state || "未知／未读到"}`),
          node("p", { className: "form-note" }, `当前基线：${item.baseline_matches ? "匹配" : "不匹配／缺失"}`),
          button("查看原件", () => inspect(item.experiment_id))),
      ])) : empty("本页未读到有效实验。"),
      ...observed.errors.map((item) => panel(`实验 ${item.experiment_id} 无法读取`, item.error)));
      note.textContent = `第 ${pageIndex + 1} 页 · 检查 ${observed.inspected_entries} 个条目 · ${observed.items.length} 个可读实验`;
      previous.disabled = pageIndex === 0;
      next.disabled = !observed.next_after;
    } catch (error) {
      if (!active() || sequence !== pageSequence) return;
      baseline.replaceChildren(empty("本次读取未取得基线。"));
      entries.replaceChildren(panel("未取得实验列表", error.message));
      note.textContent = "请核对项目已登记训练模板及所选执行目录，再重新读取。";
      previous.disabled = pageIndex === 0;
    }
  }

  load();
  return [heading("训练实验", "固定 workload → baseline → 精确 experiment → 可信 runner → 复验与人工批准。"),
    view,
    panel("开始与执行实验", "先准备真实合同、数据、环境和预算，再按训练手册使用原生执行流程。",
      pre(`ergora templates copy training-optimization ./training-task\nergora training list ${project}\nergora training show ${project} EXPERIMENT_ID`),
      node("p", {}, "原生 agentflow training 的 prepare／start／run-local／status／cancel／approve 沿用原实验 ID。执行、取消、恢复和 evidence SHA 批准的步骤见仓库 docs/TRAINING.md；当前页面只读。")),
    panel("Forge 候选来源", "原生 campaign 是候选材料；完成不代表实验通过或已经采用。在工作流设计中选择训练模板可操作原生工具。",
      pre(`ergora kernel list ${project}`),
      data.kernel_runs.length ? table(["原记录 ID", "记录状态"], data.kernel_runs.map((item) => [item.id, item.status])) : empty("尚无 Forge 候选记录。")),
  ];
}
