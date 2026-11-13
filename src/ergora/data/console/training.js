import { api } from "./api.js";
import { node, button, pre, heading, panel, empty, row, table, short } from "./ui.js";
import { app } from "./state.js";
import { trainingCancellationPanel } from "./training-cancellation.js";

export function trainingView(data, base) {
  const project = data.project.id;
  const home = app.bootstrap.state_directory;
  const entries = node("div", { "aria-live": "polite" });
  const baseline = node("div");
  const setup = node("div");
  const runnerSetup = node("div");
  const note = node("p", { className: "form-note" });
  const detail = node("div", { className: "task-detail", "aria-live": "polite" }, empty("选择一个实验，查看完整合同与已保存证据。"));
  let pageSequence = 0, detailSequence = 0, pageIndex = 0, page;
  const cursors = [null];
  const previous = button("上一页", () => { pageIndex--; load(); });
  const next = button("下一页", () => { cursors[++pageIndex] = page.next_after; load(); });
  const view = node("div", { className: "task-layout training-workbench" },
    node("div", {}, panel("当前基线", null, baseline, setup),
      panel("可信 runner", "明确登记项目命令；登记不会执行 argv。", runnerSetup),
      panel("原实验记录", "列表读取已保存文件；不会查询或启动训练。", entries, note,
        row(previous, next, button("重新读取列表", () => { pageIndex = 0; load(); })))), detail);
  const active = () => view.isConnected && app.project === project && app.tab === "training" && app.bootstrap.state_directory === home;

  function setupDocument(kind) {
    const isBaseline = kind === "baseline", label = isBaseline ? "基线" : "runner";
    const publishLabel = isBaseline ? "初始化基线" : "登记 runner";
    const previewOperation = isBaseline ? "baseline-preview" : "runner-preview";
    const publishOperation = isBaseline ? "init-baseline" : "register-runner";
    const shaKey = `${kind}_sha256`;
    let sequence = 0, sending = false;
    const result = node("div", { "aria-live": "polite" });
    const source = node("textarea", { rows: 12, "aria-label": `完整 ${kind} JSON`, spellcheck: "false",
      placeholder: `粘贴已审阅的完整 ${kind} JSON`, oninput: () => { sequence++; result.replaceChildren(); } });
    const preview = button(`预览${label}`, async () => {
      if (sending) return;
      const text = source.value, request = ++sequence;
      const document = JSON.parse(text);
      result.replaceChildren(empty(`正在验证${label}…`));
      try {
        const observed = await api(`${base}/training/${previewOperation}`, { [kind]: document });
        if (!active() || request !== sequence || source.value !== text) return;
        result.replaceChildren(pre(observed));
        if (observed.status === "conflict") {
          result.append(empty(isBaseline ? "当前基线与输入不同；需要经过审阅的基线迁移，此处不覆盖。"
            : "同 ID 的 runner 与输入不同；请为新版本选用新的 runner_template_id。"));
          return;
        }
        if (app.bootstrap.platform !== "linux") {
          result.append(empty("原生初始化与 runner 登记请在登记的 Linux／WSL2 环境执行。"));
          return;
        }
        const confirm = node("input", { type: "text", "aria-label": `确认 ${kind} 内容 SHA256`,
          autocomplete: "off", spellcheck: "false", placeholder: `粘贴预览返回的完整 ${shaKey}` });
        const initialize = button(`确认${publishLabel}`, async () => {
          if (!active() || sending || request !== sequence || source.value !== text) return;
          if (confirm.value !== observed[shaKey]) throw new Error(`请确认预览中的完整 ${kind} 内容 SHA256。`);
          sending = true;
          source.disabled = preview.disabled = confirm.disabled = initialize.disabled = true;
          try {
            const reply = await api(`${base}/training/${publishOperation}`, {
              [kind]: document, revision: observed.project_revision, [shaKey]: observed[shaKey],
            });
            if (active() && request === sequence) {
              result.replaceChildren(pre(reply), empty(`已读取原${label}文件。此登记不证明测量、质量或训练收益。`));
              load();
            }
          } catch (error) {
            if (active() && request === sequence)
              result.replaceChildren(panel(`未取得${publishLabel}确认`, error.message,
                node("p", {}, `重新预览相同内容以读取原${label}文件，再明确确认重试。已有不同内容不会被覆盖。`),
                ...(isBaseline ? [button("重新读取原基线", () => load())] : [])));
          } finally {
            sending = false;
            source.disabled = preview.disabled = false;
          }
        }, "primary");
        result.append(node("p", {}, `核对完整${label}和项目修订，粘贴内容SHA后${publishLabel}。相同内容可重试；原文件字节SHA在回执中另列。`), confirm, initialize);
      } catch (error) {
        if (active() && request === sequence) result.replaceChildren(panel(`未取得${label}预览`, error.message));
      }
    });
    return node("details", {}, node("summary", {}, `预览与${publishLabel}`),
      node("p", {}, isBaseline ? "使用训练模板中的 baseline.json 填写真实代码、配置和 workload。预览与初始化无需启动服务。"
        : "使用 runner-template.example.json 填写当前项目、Git 根、argv 和超时。需要 Linux／WSL2 与 ergora[temporal]，无需启动服务；只登记，不运行命令。"),
      source, preview, result);
  }

  setup.append(setupDocument("baseline"));
  runnerSetup.append(setupDocument("runner"));

  function submissionPanel(id, selected, cancellation) {
    const submission = node("div", { "aria-live": "polite" });
    let submissionSequence = 0, sending = false, source, lastResult;

    function showSubmission(result) {
      lastResult = result;
      cancellation.setSubmission(result);
      const controls = node("div");
      const refresh = button("读取本地提交记录", readSubmission);
      submission.replaceChildren(table(["提交记录", "值"], [
        ["状态", result.status], ["项目修订", result.project_revision], ["原工作流", result.workflow_id],
        ["原运行 ID", result.run_id || "尚无确认回执"],
        ["意图 SHA256", result.intent_sha256 || "尚未创建意图"],
        ["发送记录", result.attempt_saved ? "已有；仅按原 ID 对账" : "尚未记录发送"],
        ["归属拒绝", result.reason || "无"],
      ]), node("details", {}, node("summary", {}, "完整提交记录"), pre(result)), controls, refresh);
      if (!["not_recorded", "prepared", "unknown"].includes(result.status)) return;
      const starting = result.status === "not_recorded";
      if (starting && !source) {
        controls.append(node("p", {}, "先读取一致的实验原件才能首次提交。已有意图的继续／对账不依赖当前原件。"));
        return;
      }
      const item = source?.experiment;
      const material = starting ? { binding: item.binding, max_run_seconds: item.max_run_seconds, runner: item.current_runner }
        : result.confirmation;
      const digest = starting ? item.binding.manifest_sha : result.intent_sha256;
      const confirmation = node("input", { type: "text", "aria-label": starting ? "确认 manifest SHA256" : "确认原意图 SHA256",
        autocomplete: "off", spellcheck: "false", placeholder: "粘贴上方完整 SHA256" });
      const action = button(starting ? "提交已准备实验" : result.status === "unknown" ? "按原 ID 对账" : "继续原提交", async () => {
        if (!selected() || sending) return;
        if (confirmation.value !== digest) throw new Error("请粘贴本次操作的完整 SHA256；项目变化后需重新读取。");
        sending = true;
        const request = ++submissionSequence;
        for (const control of submission.querySelectorAll("button, input")) control.disabled = true;
        try {
          const reply = await api(`${base}/training/${encodeURIComponent(id)}/${starting ? "start" : "resume-start"}`,
            { revision: starting ? source.project_revision : result.project_revision, [starting ? "manifest_sha256" : "intent_sha256"]: digest });
          if (selected() && request === submissionSequence) showSubmission(reply);
        } catch (error) {
          if (selected() && request === submissionSequence)
            submission.replaceChildren(panel("本次操作未取得确认", error.message,
              node("p", {}, "先读取原意图。若已有发送记录，只能对账，不要换实验 ID 或重新提交。"),
              button("读取本地提交记录", readSubmission)));
        } finally {
          sending = false;
        }
      }, "primary");
      controls.append(node("p", {}, starting
        ? "确认下列原合同与可信 runner 后，粘贴 manifest SHA256。此操作提交原控制工作流；逐实验执行仍使用原 run-local。"
        : result.status === "unknown" ? "已有发送记录：粘贴原意图 SHA256后，仅查询原运行与归属，不会重发 start。"
          : "意图已保存但尚无发送记录：粘贴原意图 SHA256后，可以继续一次原提交。"),
        pre({ confirmation_sha256: digest, ...material }),
        confirmation, action);
    }

    async function readSubmission() {
      if (sending) return;
      const request = ++submissionSequence;
      submission.replaceChildren(empty("正在读取本地提交记录…"));
      try {
        const result = await api(`${base}/training/${encodeURIComponent(id)}/submission`);
        if (selected() && request === submissionSequence) showSubmission(result);
      } catch (error) {
        if (selected() && request === submissionSequence)
          submission.replaceChildren(panel("未取得本地提交记录", error.message, button("重新读取提交记录", readSubmission)));
      }
    }

    readSubmission();
    return { element: panel("原实验提交", "默认只读本地记录。原意图与当前原件分别读取，恢复须确认原 SHA256；回执不代表训练成功或外部作业停止。", submission),
      setSource(observed) {
        source = observed;
        if (selected() && lastResult?.status === "not_recorded") showSubmission(lastResult);
      } };
  }

  async function inspect(id) {
    const sequence = ++detailSequence;
    const selected = () => active() && sequence === detailSequence;
    const records = node("div", {}, empty(`正在读取实验 ${id}…`));
    const cancellation = trainingCancellationPanel(base, id, selected);
    const submission = submissionPanel(id, selected, cancellation);
    detail.replaceChildren(records, submission.element, cancellation.element);
    try {
      const observed = await api(`${base}/training/${encodeURIComponent(id)}`);
      if (!active() || sequence !== detailSequence) return;
      submission.setSource(observed);
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
      records.replaceChildren(panel(`实验 ${item.experiment_id}`, "这些是原记录；运行状态未实时查询，统计和正确性未重新复验，也未授予采用。",
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
        records.replaceChildren(panel("未取得一致的实验记录", error.message,
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
        : empty("尚未初始化基线。展开下方入口预览并确认真实 baseline。"));
      entries.replaceChildren(observed.items.length ? table(["实验"], observed.items.map((item) => [
        node("div", { className: "task-choice" }, node("strong", {}, item.experiment_id),
          node("p", { className: "form-note" }, `已保存结果：${item.recorded_result_state || "未知／未读到"}`),
          node("p", { className: "form-note" }, `当前基线：${item.baseline_matches ? "匹配" : "不匹配／缺失"}`),
          button("查看原件", () => inspect(item.experiment_id))),
      ])) : empty("本页未读到有效实验。"),
      ...observed.errors.map((item) => panel(`实验 ${item.experiment_id} 无法读取`, item.error,
          button("查看原件与原意图", () => inspect(item.experiment_id)))));
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
      node("p", {}, "先按原生 agentflow training prepare 准备实验，再在此确认提交。已确认原运行可用稳定请求 ID 取消、按原意图恢复并读取停止事实。run-local／approve沿用原实验 ID；执行和 evidence SHA 批准见仓库 docs/TRAINING.md。")),
    panel("Forge 候选来源", "原生 campaign 是候选材料；完成不代表实验通过或已经采用。在工作流设计中选择训练模板可操作原生工具。",
      pre(`ergora kernel list ${project}`),
      data.kernel_runs.length ? table(["原记录 ID", "记录状态"], data.kernel_runs.map((item) => [item.id, item.status])) : empty("尚无 Forge 候选记录。")),
  ];
}
