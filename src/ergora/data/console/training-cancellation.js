import { api } from "./api.js";
import { node, button, pre, panel, empty, row, table } from "./ui.js";

// Own the fixed-run cancellation form and its asynchronous lifecycle. The
// experiment detail can fail while its original operation remains recoverable.
export function trainingCancellationPanel(base, id, selected) {
  const endpoint = `${base}/training/${encodeURIComponent(id)}`;
  const content = node("div", { "aria-live": "polite" });
  const observation = node("div", { "aria-live": "polite" }, empty("尚未观察停止事实。"));
  let submission, sequence = 0, stopSequence = 0, sending = false, observing = false;
  const requestId = node("input", { type: "text", "aria-label": "取消请求 ID", autocomplete: "off",
    placeholder: "为本次请求取一个稳定 ID；恢复时复用", oninput: () => {
      sequence++;
      content.replaceChildren(empty("请求 ID 已改变，先读取该 ID 的本地记录。"));
    } });
  const read = button("读取本地取消记录", readCancellation);
  const stop = button("读取停止事实", observeStop);
  const controls = row(requestId, read);
  const element = panel("原运行取消与停止事实",
    "默认不查询或取消。先确认原提交回执，再用固定请求 ID 操作；请求投递、控制结果与执行器观察分别展示。",
    controls, content, row(stop), observation);

  function show(result) {
    const actions = node("div");
    content.replaceChildren(table(["取消记录", "值"], [
      ["状态", result.status], ["原运行 ID", result.run_id], ["请求 ID", result.request_id],
      ["原因", result.reason || "尚未创建请求"], ["原意图 SHA256", result.intent_sha256 || "尚未创建意图"],
      ["信号投递证据", result.signal_delivery || "尚无确认"],
    ]), node("details", {}, node("summary", {}, "完整取消记录"), pre(result)), actions);
    if (!["not_recorded", "prepared", "unknown"].includes(result.status)) return;
    const initial = result.status === "not_recorded";
    const confirm = node("input", { type: "text", autocomplete: "off", spellcheck: "false",
      "aria-label": initial ? "确认取消原运行 ID" : "确认取消意图 SHA256" });
    const reason = node("textarea", { "aria-label": "取消原因", maxlength: "1000", rows: "3" });
    const digest = initial ? result.run_id : result.intent_sha256;
    const action = button(initial ? "请求取消原运行" : result.status === "unknown" ? "仅对账原取消信号" : "继续原取消请求", async () => {
      if (!selected() || sending) return;
      if (confirm.value !== digest) throw new Error(initial ? "请粘贴上方完整原运行 ID。" : "请粘贴原取消意图的完整 SHA256。");
      if (initial && !reason.value.trim()) throw new Error("请填写本次取消原因。");
      sending = true;
      const attempt = ++sequence;
      const ident = requestId.value;
      for (const control of element.querySelectorAll("input, textarea, button")) control.disabled = true;
      try {
        const reply = await api(`${endpoint}/${initial ? "cancel" : "resume-cancel"}`, {
          revision: result.project_revision, request_id: ident,
          ...(initial ? { run_id: result.run_id, reason: reason.value } : { intent_sha256: digest }),
        });
        if (selected() && attempt === sequence) show(reply);
      } catch (error) {
        if (selected() && attempt === sequence)
          content.replaceChildren(panel("本次取消未取得确认", error.message,
            pre({ request_id: ident }), node("p", {}, "保留此请求 ID，先读取本地记录；已有发送记录时只能对账，不要换 ID 重发。")));
      } finally {
        sending = false;
        if (selected()) {
          for (const control of element.querySelectorAll("input, textarea, button")) control.disabled = false;
          stop.disabled = observing;
        }
      }
    }, "primary");
    actions.append(node("p", {}, initial ? "粘贴完整原运行 ID，并填写取消原因。"
      : result.status === "unknown" ? "已有发送记录：确认原意图 SHA256后，仅查询固定运行的完整信号历史。"
        : "意图已保存但尚未发送。确认原意图 SHA256后可继续一次原请求。"),
      pre({ confirmation: digest }), confirm, ...(initial ? [reason] : []), action);
  }

  async function readCancellation() {
    if (!selected() || sending || !submission) return;
    if (!requestId.value) throw new Error("先填写稳定的取消请求 ID；已有请求请复用原 ID。");
    const attempt = ++sequence;
    const ident = requestId.value;
    content.replaceChildren(empty("正在读取本地取消记录…"));
    try {
      const result = await api(`${endpoint}/cancellations/${encodeURIComponent(ident)}`);
      if (selected() && attempt === sequence) show(result);
    } catch (error) {
      if (selected() && attempt === sequence)
        content.replaceChildren(panel("未取得取消记录", error.message));
    }
  }

  async function observeStop() {
    if (!selected() || !submission || observing || sending) return;
    observing = true;
    stop.disabled = true;
    const attempt = ++stopSequence;
    observation.replaceChildren(empty("正在分别读取原控制结果、执行器观察与围栏…"));
    try {
      const result = await api(`${endpoint}/stop-status`);
      if (selected() && attempt === stopSequence)
        observation.replaceChildren(table(["停止事实", "观察结果"], [
          ["原运行 ID", result.run_id], ["原控制结果／阶段", result.control.phase],
          ["原控制工作流状态", result.control.temporal_status],
          ["原执行器观察", result.executor_observation?.state || "未读到作业；不能据此确认停止"],
          ["原取消围栏", result.fence_recorded ? "存在；仍须核对执行结果" : "未读到"],
        ]), node("p", {}, "以上是分别读取的事实，不构成整体停止或采用结论。"),
        node("details", {}, node("summary", {}, "完整停止观察"), pre(result)));
    } catch (error) {
      if (selected() && attempt === stopSequence)
        observation.replaceChildren(panel("未取得停止事实", error.message));
    } finally {
      observing = false;
      if (selected()) stop.disabled = sending;
    }
  }

  function setSubmission(result) {
    const next = result.status === "submitted" ? result : null;
    if (submission?.run_id === next?.run_id && submission) return;
    submission = next;
    sequence++;
    stopSequence++;
    requestId.disabled = read.disabled = stop.disabled = !submission;
    content.replaceChildren(empty(submission ? "填写稳定请求 ID，读取本地记录后再确认操作。"
      : "先恢复原提交回执；尚未确认的 start 不能用来取消或观察原执行器。"));
  }

  setSubmission({});
  return { element, setSubmission };
}
