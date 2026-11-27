import { api } from "./api.js";
import { $, node, pre, panel, empty, field, form, modal } from "./ui.js";

const facts = (rows) => node("dl", { className: "task-facts" },
  rows.map(([name, value]) => [node("dt", {}, name), node("dd", {}, String(value ?? "未返回"))]));
const record = (title, value) => value == null ? null :
  node("details", {}, node("summary", {}, title), pre(value));

function trainingEvidence({ locator, recipient, source_kind }, completion, conflict) {
  const lease = completion?.local_gpu_lease;
  const history = recipient?.history;
  const native = recipient?.native_receipt;
  const recovery = completion?.recovery_history;
  const screen = source_kind === "training_screen_result";
  const gpuRelease = source_kind === "training_gpu_release";
  return [
    panel(gpuRelease ? "原资源释放" : screen ? "原筛选决定" : "原训练结果", null,
      conflict,
      facts([
        ["原实验 ID", locator.experiment_id],
        ["原训练 Job ID", locator.job_id],
        ["原训练 Workflow ID", locator.workflow_id],
        ["原训练 Run ID", locator.run_id],
        ["原训练尝试 SHA256", locator.attempt_sha256],
        ["原训练请求 SHA256", locator.native_request_sha256],
        ...(gpuRelease ? [
          ["原池会话 ID", locator.session_id],
          ["原租约 ID", locator.lease_id],
          ["原释放序号", lease?.release_ref?.sequence],
          ["原 guard 停止证明 SHA256", lease?.release_ref?.proof_ref?.raw_sha256],
        ] : [
          ["原训练结果 SHA256", completion?.native_result_sha256],
        ]),
        ...(screen ? [
          ["原筛选状态", completion?.native_result_state],
          ["原筛选决定", completion?.decision],
          ["筛选结果 SHA256", completion?.screen_result_sha256],
        ] : []),
        ...(!gpuRelease ? [["训练执行回收记录 SHA256", completion?.reap_record_sha256]] : []),
        ["读取守卫清理 SHA256", completion?.reader_cleanup_sha256],
        ...(recovery ? [
          ["原读取 Activity 超时事件 ID", recovery.original_timeout_event_id],
          ["回执核对 Activity 完成事件 ID", recovery.completed_event_id],
        ] : [["训练读取 Activity 完成事件 ID", completion?.completed_event_id]]),
      ]),
      record("History 核对的原训练读取回执", completion)),
    panel("原训练资源租约", null,
      facts([["本地 GPU 租约观测", lease === null ? "源记录返回 null" : lease?.status]]),
      record("源返回的原租约观测", lease)),
    recipient ? panel("原接手唤醒", recipient.reason,
      facts([
        ["唤醒读取状态", recipient.status],
        ["原唤醒 ID", recipient.wake_id],
        ["History 唤醒 Activity 状态", history?.status],
        ["唤醒 Activity 调度事件 ID", history?.scheduled_event_id],
        ["唤醒 Activity 开始事件 ID", history?.started_event_id],
        ["唤醒 Activity 终止事件 ID", history?.completed_event_id],
      ])) : null,
    recipient ? panel("原接手原生回执", null,
      native ? facts([
        ["原接手会话 ID", native?.session_id],
        ["原接手父 Run ID", native?.parent_run_id],
        ["原接手意图 ID", native?.intent_id],
        ["原接手 Run ID", native?.run_id],
        ["原接手派发", native?.dispatch],
        ["原接手进程启动", native?.start_status],
        ["原接手结果", native?.status],
        ...(native.campaign_recipient_blocker ? [["原接手阻塞原因", native.campaign_recipient_blocker]] : []),
        ["原接手执行已停止", native?.execution_stopped],
        ["原接手退出码", native?.returncode],
        ["原接手结果 SHA256", native?.result_sha256],
      ]) : empty("未返回原接手原生回执。")) : null,
  ];
}

function timeline(result) {
  const evidence = result.task_evidence;
  const training = result.training_task;
  const selected = training ?? evidence;
  const job = evidence?.native_job;
  const current = result.task_state;
  const currentReadback = current?.readback_observation;
  const history = result.task_observation_history;
  const completion = result.readback_completion;
  const { stop, rollover } = result;
  const conflict = result.task_observation_history_status === "contradictory" ?
    node("p", { className: "form-note", role: "status" },
      `History 证据冲突（contradictory）。${result.task_observation_history_error}`) : null;
  const update = (title, attempt) => attempt == null ? null :
    node("section", {},
      node("h3", {}, title),
      facts([
        ["读取结果", attempt.status],
        ...(attempt.status === "failed" && attempt.reason ? [["原 Update 失败原因", attempt.reason]] : []),
        ["原 Update ID", attempt.update_id],
        ["原 Update 所属 Run ID", attempt.run_id],
        ["History 接受事件 ID", attempt.accepted_event_id],
        ["History 完成事件 ID", attempt.completed_event_id],
        ["原观测 SHA256", attempt.receipt?.observation_sha256],
      ]),
      record("History 核对的原 Update 回执", attempt.receipt));
  return [
    panel("原 Campaign 与任务", result.acceptance,
      facts([
        ["项目", result.project],
        ["原 Campaign ID", result.campaign],
        ["原任务 ID", selected.task_id],
        ["依赖任务 ID", selected.depends_on.join("、") || "无"],
        ["原计划 SHA256", result.plan_sha256],
        ["原项目修订", result.project_revision],
        ["原操作者 EUID", result.operator_euid],
        ["原截止时间（UTC）", new Date(result.expires_at * 1000).toISOString()],
      ])),
    panel("Workflow 读取状态", result.remote_error,
      facts([
        ["原 Workflow ID", result.workflow_id],
        ["原 Run ID", result.run_id],
        ...(result.current_run_id ? [["已核对的后继 Run ID", result.current_run_id]] : []),
        ["原启动尝试 SHA256", result.attempt_sha256],
        ["原启动回执已保存", result.result_saved],
        ["远端读取", result.remote_status],
        ["Temporal 状态", result.temporal_status],
        ["Workflow 状态读取", result.workflow_state_status],
        ["已核对的 Workflow 阶段", result.workflow_phase],
        ["已核对的任务状态", current?.status],
        ...(current?.state_source === "history" ? [["任务状态来源", "Temporal History"]] : []),
        ["任务观测准入（eligible）", current?.eligible],
        ["当前任务的原尝试状态", current?.attempt_status],
        ["当前任务的原 Update ID", current?.update_id],
      ]),
      (stop.status !== "not_recorded" || rollover) ? node("section", {},
        node("h3", {}, "原 STOP 与 rollover"),
        facts([
          ["STOP 记录状态", stop.status],
          ["STOP 远端读取", stop.remote_status],
          ["原 STOP Update ID", stop.update_id],
          ["原 STOP 决定", stop.decision],
          ["原 STOP 回执所属 Run ID", stop.receipt_run_id],
          ...(stop.local_fence_saved == null ? [] : [["原本地 STOP 已保存", stop.local_fence_saved]]),
          ...(rollover ? [["rollover 读取结果", rollover.status], ["原 rollover Update ID", rollover.update_id]] : []),
        ])) : null,
      currentReadback ? node("section", {},
        node("h3", {}, "Workflow 定时读取状态"),
        facts([
          ["当前定时读取结果", currentReadback.status],
          ...(currentReadback.reason ? [["当前定时读取原因", currentReadback.reason]] : []),
          ...(currentReadback.activity_id ? [["原定时读取 Activity ID", currentReadback.activity_id]] : []),
        ]),
        record("Workflow 返回的定时读取记录", currentReadback)) : null,
      record("Workflow 返回的原等待回执", current?.waiting_receipt),
      record("Workflow 返回的原终态回执", current?.receipt)),
    ...(training ? trainingEvidence(training, completion, conflict) : [
      panel("原 Update 与 History", null, conflict,
        history.waiting || history.terminal ? null : empty("该任务未返回已保存的 Update 尝试。"),
        update("等待 Update", history.waiting),
        record("History 核对的原定时读取 Activity 回执", completion),
        update("终态 Update", history.terminal)),
      panel("原固定检查 Job", evidence.native_read_error,
        facts([
          ["证据关联", evidence.correlation],
          ...(evidence.different_fields?.length ? [["冲突字段", evidence.different_fields.join("、")]] : []),
          ["冻结的 Job ID", evidence.source.job_id],
          ["冻结的 Job SHA256", evidence.source.job_sha256],
          ["原操作 ID", evidence.source.operation_id],
          ["原 Job 状态", job?.status],
          ["原 Job 清理已确认", job?.cleanup_confirmed],
          ["本次原 Job 读取 SHA256", evidence.native_observation_sha256],
        ]),
        record("冻结的原 Job 选择", evidence.source),
        record("原 Job 所有者返回的证据", job)),
    ]),
  ];
}

export function campaignTimeline({ base, projectId, controlDirectory, isCurrent }) {
  const key = `ergora-campaign-timeline:${JSON.stringify([controlDirectory, projectId])}`;
  const [previousCampaign = "", previousTask = ""] = JSON.parse(sessionStorage.getItem(key) || "[]");
  const output = node("div", { "aria-live": "polite" });
  const idInput = { required: true, pattern: "[A-Za-z0-9][A-Za-z0-9_\\-]{0,63}", maxlength: 64, autocomplete: "off" };
  let selection = 0;
  const active = () => isCurrent() && content.isConnected && $("#dialog").open;
  const content = node("div", {},
    node("p", {}, `项目 ${projectId} · 按冻结计划中的 ID 读取一个固定检查或训练结果任务的原证据。`),
    form([
      field("原 Campaign ID", "campaign", previousCampaign, "text", idInput),
      field("原任务 ID", "task", previousTask, "text", idInput),
    ], "读取原任务时间线", async (values) => {
      if (!active()) return;
      const reading = ++selection;
      const campaignId = values.get("campaign");
      const taskId = values.get("task");
      sessionStorage.setItem(key, JSON.stringify([campaignId, taskId]));
      output.replaceChildren(empty("正在读取原任务时间线…"));
      try {
        const data = await api(`${base}/campaigns/${encodeURIComponent(campaignId)}/tasks/${encodeURIComponent(taskId)}/timeline`);
        if (active() && reading === selection) output.replaceChildren(...timeline(data));
      } catch (error) {
        if (active() && reading === selection)
          output.replaceChildren(panel("原任务时间线读取失败", error.message));
      }
    }),
    output);
  content.addEventListener("input", () => {
    selection++;
    output.replaceChildren();
  });
  modal("Campaign 任务时间线", content);
}
