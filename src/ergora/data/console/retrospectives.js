import { api } from "./api.js";
import { node, button, field, checkbox, heading, panel, empty, row, pre, table, download } from "./ui.js";

export function retrospectivesView(data, base) {
  const disclosure = (title, value) => node("details", {}, node("summary", {}, title), pre(value));
  const packetField = field("本机交接包路径", "handoff_packet", "", "text", { required: true, autocomplete: "off" });
  const digestField = field("预期整包 SHA256", "handoff_sha256", "", "text", { required: true, autocomplete: "off", spellcheck: "false" });
  const packet = packetField.querySelector("input");
  const digest = digestField.querySelector("input");
  const directoryStatus = node("div", { "aria-live": "polite" });
  const directoryButton = node("button", { type: "submit", className: "primary" }, "读取交接包目录");
  const readButton = button("读取选中完整材料", readSelected);
  const count = node("p", { "aria-live": "polite" }, "已选 0 份原件。");
  const choices = node("fieldset", { disabled: true, hidden: true },
    node("legend", {}, "选择原 job 的材料"));
  const result = node("div", { "aria-live": "polite" });
  const source = node("form", { onsubmit: (event) => {
    event.preventDefault();
    return readDirectory();
  } }, packetField, digestField, row(directoryButton));
  const view = node("div", { className: "retrospective-evidence" },
    heading("复盘改进", "从原交接包明确选择完整材料，保留任务、运行、回执与成本来源。"),
    panel("核对原交接包", "先在正式任务页下载交接包，并保存到控制台所在机器。填写保存路径和该次下载的整包 SHA256；读取不提取文件或改写原包。",
      source, directoryStatus),
    panel("完整复盘材料", "目录不会自动选择原件。明确选择后读取完整 UTF-8 正文；二进制、NUL 或超出原容量时整次拒绝，不截断。",
      choices, result),
    panel("后续候选", "本页先提供完整证据与可下载选择清单。Skill、记忆和流程候选仍使用原 retrospective CLI；本页不调用 Agent、不评价或采用候选。",
      pre("ergora handoff read HANDOFF.zip --sha256 PACKET_SHA --selection selected-artifacts.json")),
  );
  const active = () => view.isConnected;
  let directorySequence = 0;
  let selectionSequence = 0;
  let directory = null;
  let entries = [];

  function invalidateSelection() {
    selectionSequence++;
    readButton.disabled = false;
    result.replaceChildren(empty("明确选择后，读取本次完整材料。"));
  }

  function invalidateDirectory() {
    directorySequence++;
    directory = null;
    directoryButton.disabled = false;
    choices.disabled = true;
    invalidateSelection();
    directoryStatus.replaceChildren(empty("来源已更改；已有目录仅保留显示，须重新读取。"));
  }

  async function readDirectory() {
    if (!active() || directoryButton.disabled) return;
    invalidateDirectory();
    const reading = directorySequence;
    const selected = { packet: packet.value, packet_sha256: digest.value, selection: [] };
    directoryButton.disabled = true;
    directoryStatus.replaceChildren(empty("正在核对原交接包与目录…"));
    try {
      const observed = await api(`${base}/handoff/evidence`, selected);
      if (!active() || reading !== directorySequence) return;
      directory = selected;
      entries = observed.index.jobs.flatMap((job) => job.receipt.artifacts.map((artifact, index) => {
        const label = checkbox(`${job.job_id} · ${artifact.name}`, `handoff:${job.job_id}:${index}`);
        return { selection: { job_id: job.job_id, name: artifact.name }, choice: label.querySelector("input"),
          element: node("div", {}, label, disclosure("原 job 与回执引用", {
            stage: job.stage, job_id: job.job_id, job_sha256: job.job_sha256,
            receipt_state: job.receipt_state, receipt_sha256: job.receipt_sha256, artifact,
          })) };
      }));
      count.textContent = "已选 0 份原件。";
      choices.replaceChildren(node("legend", {}, "选择原 job 的材料"), count,
        ...(entries.length ? entries.map((item) => item.element) : [empty("原目录没有可选材料。")]), row(readButton));
      choices.disabled = choices.hidden = false;
      directoryStatus.replaceChildren(table(["来源", "原记录"], [
        ["原项目", observed.index.project], ["原任务", observed.index.task_id], ["原运行", observed.index.run_id],
        ["整包 SHA256", observed.packet_sha256], ["索引 SHA256", observed.index_sha256],
      ]), disclosure("完整原索引、状态与成本", observed.index),
      node("p", {}, "已核本次包字节及内部声明；不认证来源或推断执行成功。重新读取目录会清空勾选。"));
    } catch (error) {
      if (active() && reading === directorySequence)
        directoryStatus.replaceChildren(panel("交接包读取失败", error.message, "原输入保留；旧目录不可用，请核对后明确重读。"));
    } finally {
      if (active() && reading === directorySequence) directoryButton.disabled = false;
    }
  }

  async function readSelected() {
    if (!active() || !directory || readButton.disabled) return;
    const selection = entries.filter((item) => item.choice.checked).map((item) => item.selection);
    invalidateSelection();
    if (!selection.length) {
      result.replaceChildren(empty("请先选择要读取的原材料。"));
      return;
    }
    const reading = selectionSequence;
    const selected = { ...directory, selection };
    readButton.disabled = true;
    result.replaceChildren(empty("正在按整包身份读取完整原件…"));
    try {
      const observed = await api(`${base}/handoff/evidence`, selected);
      if (!active() || reading !== selectionSequence) return;
      result.replaceChildren(panel("完整原材料已读取", "下方正文与原来源全部来自本次已核交接包；材料选择 SHA256 是原 canonical 身份，不是下载 JSON 文件的字节摘要。",
        table(["来源", "原记录"], [["整包 SHA256", observed.packet_sha256], ["材料选择 SHA256", observed.sha256],
          ["完整原件数量", observed.artifacts.length], ["执行成功", observed.execution_success ?? "未据此判断"]]),
        ...observed.artifacts.map((item) => node("section", {}, node("h3", {}, `${item.job_id} · ${item.artifact.name}`),
          disclosure("完整来源与原身份", { ...item, text: undefined }), pre(item.text))),
        disclosure("完整原证据结果", observed),
        row(button("下载精确选择清单", () => {
          if (active() && reading === selectionSequence)
            download("selected-artifacts.json", JSON.stringify(selection, null, 2) + "\n", "application/json");
        }), button("下载完整复盘材料", () => {
          if (active() && reading === selectionSequence)
            download("retrospective-evidence.json", JSON.stringify(observed, null, 2) + "\n", "application/json");
        })),
      ));
    } catch (error) {
      if (active() && reading === selectionSequence)
        result.replaceChildren(panel("完整材料读取失败", error.message, "原勾选保持；核对或减少选择后明确重读，失败不交付部分材料。"));
    } finally {
      if (active() && reading === selectionSequence) readButton.disabled = false;
    }
  }

  for (const input of [packet, digest]) input.addEventListener("input", invalidateDirectory);
  choices.addEventListener("change", () => {
    invalidateSelection();
    count.textContent = `已选 ${entries.filter((item) => item.choice.checked).length} 份原件。`;
  });
  return [view];
}
