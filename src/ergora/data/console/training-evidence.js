import { api } from "./api.js";
import { node, button, pre, panel, empty, table, row } from "./ui.js";

export function trainingEvidencePanel(base, id, selected, platform, openTasks) {
  const path = `${base}/training/${encodeURIComponent(id)}`;
  const evidenceBody = node("div", { "aria-live": "polite" });
  const approvalBody = node("div", { "aria-live": "polite" });
  let evidence, approval, evidenceSequence = 0, approvalSequence = 0, textSequence = 0, sending = false;
  const view = panel("证据审阅与 owner 批准", "读取原归档与本地意图；投递、原授权、集成票据与真实复验分别确认。",
    row(button("读取原归档证据", readEvidence), button("读取本地批准记录", readApproval)),
    panel("原归档与文本", "artifact 索引只声明摘要；正文须明确选择并按原 SHA 核对。", evidenceBody),
    panel("原 owner 决策", "凭据创建 unknown 与信号投递 unknown 分别保留；此处不自动续期、重发或采用。", approvalBody));

  function showApproval() {
    if (!approval || sending) return;
    const observed = approval;
    approvalBody.replaceChildren(table(["批准记录", "事实"], [
      ["状态", observed.status], ["原运行 ID", observed.run_id],
      ["原意图 SHA256", observed.intent_sha256 || "尚无本入口意图"],
      ["原 evidence SHA256", observed.evidence_sha256 || "尚未确认"],
      ["原凭据创建", observed.owner_receipt_status || "尚未记录"],
      ["信号投递", observed.signal_delivery || (observed.attempt_saved ? "unknown；仅查原历史" : "尚无发送记录")],
      ["授权是否采纳", "尚未评价；请查询原运行与原票据"],
    ]), node("details", {}, node("summary", {}, "完整原批准记录"), pre(observed)));
    if (observed.status === "requested") {
      approvalBody.append(empty("已确认投递；不表示原授权采纳、票据创建、集成复验通过或候选采用。读取原运行及归档中的原票据。"));
      return;
    }
    if (platform !== "linux") {
      approvalBody.append(empty("批准与恢复请使用登记的 Linux／WSL2 环境；本地记录仍可读取。"));
      return;
    }
    const first = observed.status === "not_recorded", source = evidence;
    if (!first && !["prepared", "unknown"].includes(observed.status)) return;
    if (first && source?.archive_status !== "recorded") {
      approvalBody.append(empty("首次批准前，请先读取并审阅本次原 accepted archive。原意图恢复不要求当前归档可读。"));
      return;
    }
    const confirm = node("input", { type: "text", "aria-label": first ? "批准确认 evidence SHA256" : "批准恢复确认 intent SHA256",
      autocomplete: "off", spellcheck: "false", placeholder: "粘贴上方完整 SHA256" });
    const run = first ? node("input", { type: "text", "aria-label": "批准确认原运行 ID", autocomplete: "off",
      spellcheck: "false", placeholder: "粘贴原完整 run ID" }) : null;
    const digest = first ? source.archive.evidence_sha256 : observed.intent_sha256;
    approvalBody.append(node("p", {}, first
      ? "审阅完整原 gate／binding／evidence后，输入下列原 run 与完整 evidence SHA，明确作出当前用户的 owner 决策。"
      : observed.status === "unknown" ? "已有信号发送记录：确认原意图后只查原 run 的完整历史，不会重发。"
        : "原意图已保存：确认后仅继续原决策；原凭据不续期，创建结果不明且原件缺失时会拒绝重建。"),
    pre(first ? { run_id: observed.run_id, evidence_sha256: digest, binding: source.binding }
      : { intent_sha256: digest, owner_receipt: observed.owner_receipt }), ...(run ? [run] : []), confirm,
    button(first ? "确认 owner 批准" : "恢复原批准意图", async () => {
      if (!selected() || sending || approval !== observed || (first && evidence !== source)) return;
      if (confirm.value !== digest || (first && run.value !== observed.run_id))
        throw new Error("请确认本次完整原运行 ID 与 evidence SHA，或原批准意图 SHA。");
      sending = true;
      const request = ++approvalSequence;
      for (const control of view.querySelectorAll("button, input, select")) control.disabled = true;
      try {
        const result = await api(`${path}/${first ? "approve" : "resume-approve"}`, {
          revision: observed.project_revision, confirm: true,
          ...(first ? { run_id: observed.run_id, evidence_sha256: digest } : { intent_sha256: digest }),
        });
        if (selected() && request === approvalSequence) approval = result;
      } catch (error) {
        if (selected() && request === approvalSequence) {
          approval = undefined;
          approvalBody.replaceChildren(panel("本次批准未取得确认", error.message,
            node("p", {}, "原凭据或信号可能已记录。先读取原批准意图，再确认同一 SHA 恢复；不要换 ID 或自动重试。"),
            button("读取原批准记录恢复", readApproval)));
        }
      } finally {
        sending = false;
        for (const control of view.querySelectorAll("button, input, select")) control.disabled = false;
        if (selected() && request === approvalSequence) showApproval();
      }
    }, "primary"));
  }

  async function readApproval() {
    if (!selected() || sending) return;
    const request = ++approvalSequence;
    approval = undefined;
    approvalBody.replaceChildren(empty("正在读取原本地批准意图…"));
    try {
      const observed = await api(`${path}/approval`);
      if (selected() && request === approvalSequence) { approval = observed; showApproval(); }
    } catch (error) {
      if (selected() && request === approvalSequence)
        approvalBody.replaceChildren(panel("未取得本地批准记录", error.message,
          node("p", {}, "先恢复原 start 回执；已有批准意图不依赖当前 manifest／archive 读取成功。")));
    }
  }

  async function readEvidence() {
    if (!selected() || sending) return;
    const request = ++evidenceSequence;
    ++textSequence; evidence = undefined;
    showApproval();
    evidenceBody.replaceChildren(empty("正在读取原归档证据…"));
    try {
      const observed = await api(`${path}/evidence`);
      if (!selected() || request !== evidenceSequence) return;
      evidence = observed;
      evidenceBody.replaceChildren(table(["归档观察", "事实"], [
        ["归档", observed.archive_status], ["当前基线", observed.baseline_matches ? "匹配" : observed.baseline_error],
        ["原 gate", observed.recorded_gate_report?.passed === true ? "记录通过，未重新评价" : "未记录通过"],
        ["完整 evidence SHA256", observed.archive?.evidence_sha256 || "尚无 accepted archive"],
        ["artifact 正文", observed.archive?.artifact_content_status || "未读取"],
      ]), node("details", {}, node("summary", {}, "完整原证据、归档元数据与摘要"), pre(observed)));
      if (observed.archive) showArtifacts(observed, request);
      if (observed.integration_ticket) {
        evidenceBody.append(panel("原集成复验票据", "原 owner 创建的本地票据；尚不表示真实集成复验或采用。",
          pre(observed.integration_ticket),
          node("p", {}, "到正式任务页手动绑定原候选与 evidence，完成独立集成复验。不会自动创建任务、合并或采用。"),
          button("前往正式任务页", () => { if (selected() && !sending) openTasks(); })));
      }
      showApproval();
      if (sending) for (const control of view.querySelectorAll("button, input, select")) control.disabled = true;
    } catch (error) {
      if (selected() && request === evidenceSequence)
        evidenceBody.replaceChildren(panel("未取得原归档证据", error.message,
          node("p", {}, "原资料缺失或冲突时可独立读取本地批准意图；已有发送 attempt 的恢复只查原历史。")));
    }
  }

  function showArtifacts(source, evidenceRequest) {
    const content = node("div", { "aria-live": "polite" });
    const changed = () => { ++textSequence; content.replaceChildren(); };
    const artifact = node("select", { "aria-label": "原证据 artifact", onchange: () => { offset.value = "0"; changed(); } },
      node("option", { value: "" }, "明确选择原 artifact"),
      source.archive.evidence.artifacts.map((item) => node("option", { value: item.path }, item.path)));
    const confirm = node("input", { type: "text", "aria-label": "文本窗口确认 evidence SHA256", autocomplete: "off", spellcheck: "false", oninput: changed });
    const offset = node("input", { type: "number", "aria-label": "证据文本字符 offset", min: 0, step: 1, value: "0", oninput: changed });
    const limit = node("input", { type: "number", "aria-label": "证据文本字符 limit", min: 1, max: 65536, step: 1, value: "12000", oninput: changed });
    const current = (request) => selected() && evidence === source && evidenceSequence === evidenceRequest && request === textSequence;
    async function read() {
      if (!selected() || sending || evidence !== source || evidenceSequence !== evidenceRequest) return;
      if (!artifact.value || confirm.value !== source.archive.evidence_sha256)
        throw new Error("请选择原索引中的 artifact 并确认本次完整 evidence SHA256。");
      if (![offset, limit].every((input) => input.value !== "" && input.checkValidity() && Number.isSafeInteger(Number(input.value))))
        throw new Error("请填写有效的非负整数 offset 和 1–65536 的整数 limit。");
      const request = ++textSequence;
      const parameters = new URLSearchParams({ artifact: artifact.value, evidence_sha256: confirm.value, offset: String(Number(offset.value)), limit: String(Number(limit.value)) });
      content.replaceChildren(empty("正在按原摘要核对完整文件并读取窗口…"));
      try {
        const observed = await api(`${path}/evidence?${parameters}`);
        if (!current(request)) return;
        const item = observed.artifact;
        content.replaceChildren(pre({ path: item.path, sha256: item.sha256, bytes: item.bytes,
          characters: item.characters, offset: item.offset, next_offset: item.next_offset }), pre(item.text));
        if (item.next_offset !== null)
          content.append(button("读取下一证据窗口", () => { offset.value = String(item.next_offset); return read(); }, "secondary", { disabled: sending }));
      } catch (error) {
        if (current(request)) content.replaceChildren(panel("未取得证据文本窗口", error.message,
          node("p", {}, "二进制／NUL／超限／摘要漂移请沿原索引使用对应工具，不显示为已核正文。")));
      }
    }
    evidenceBody.append(node("details", {}, node("summary", {}, "选择与读取证据文本窗口"),
      node("p", {}, "先核上方完整 evidence SHA。窗口按原文件的 Unicode 字符计数；每个所选文件先完整核 SHA，最多16MiB。"),
      artifact, confirm, node("label", {}, "字符 offset", offset), node("label", {}, "字符 limit", limit),
      button("读取证据文本窗口", read), content));
  }

  return view;
}
