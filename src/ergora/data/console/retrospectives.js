import { api } from "./api.js";
import { node, button, field, selectField, checkbox, heading, panel, empty, row, pre, table, download } from "./ui.js";

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
  const preparation = preparationPanel(base, () => view.isConnected);
  const view = node("div", { className: "retrospective-evidence" },
    heading("复盘改进", "从原交接包明确选择完整材料，保留任务、运行、回执与成本来源。"),
    panel("核对原交接包", "先在正式任务页下载交接包，并保存到控制台所在机器。填写保存路径和该次下载的整包 SHA256；读取不提取文件或改写原包。",
      source, directoryStatus),
    panel("完整复盘材料", "目录不会自动选择原件。明确选择后读取完整 UTF-8 正文；二进制、NUL 或超出原容量时整次拒绝，不截断。",
      choices, result),
    preparation.element,
    panel("后续候选", "准备成功只保存完整输入；本页不调用 Agent、不检查结果、不评价或采用候选。模型调用、候选检查与导出继续按使用手册的原 CLI 明确执行。",
      pre("ergora handoff read HANDOFF.zip --sha256 PACKET_SHA --selection selected-artifacts.json")),
  );
  const active = () => view.isConnected;
  let directorySequence = 0;
  let selectionSequence = 0;
  let directory = null;
  let entries = [];

  function invalidateSelection() {
    selectionSequence++;
    preparation.setEvidence(null);
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
      preparation.setEvidence(selected, observed);
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

function preparationPanel(base, active) {
  const kindField = selectField("候选方向", [["skills", "Skill"], ["memories", "项目记忆"], ["workflows", "工作流"]], "skills", "retrospective_kind");
  const kind = kindField.querySelector("select");
  const target = node("div");
  const sourceNotice = node("p", { "aria-live": "polite" }, "先在上方读取选中的完整材料。");
  const status = node("div", { "aria-live": "polite" });
  const attempted = node("p", { "aria-live": "polite" });
  const submit = node("button", { type: "submit", className: "primary" }, "保存完整候选输入");
  const fields = node("fieldset", { disabled: true },
    node("legend", {}, "准备候选作者输入"), kindField, target,
    field("本次改进目标", "objective", "", "textarea", { required: true }),
    field("作者完整 manifest 路径", "manifest", "", "text", { required: true, autocomplete: "off" }),
    field("作者实例路径", "instance", "root/propose", "text", { required: true }),
    field("新输入目录", "destination", "", "text", { required: true, autocomplete: "off" }),
    field("完整 prompt 字节上限", "max_prompt_bytes", 500000, "number", { required: true, min: 1, step: 1 }),
    row(submit));
  const form = node("form", { onsubmit: (event) => { event.preventDefault(); return prepare(); } }, fields);
  const directoryField = field("已有候选输入目录", "retrospective_input_directory", "", "text", { required: true, autocomplete: "off" });
  const directory = directoryField.querySelector("input");
  const inspectButton = node("button", { type: "submit", className: "secondary" }, "读取完整已有输入");
  const inspection = node("div", { "aria-live": "polite" });
  const inspectForm = node("form", { onsubmit: (event) => { event.preventDefault(); return inspect(); } }, directoryField, row(inspectButton));
  let evidence = null;
  let preparing = false;
  let sequence = 0;
  let baselineSequence = 0;
  let inspectionSequence = 0;
  let baselines = [];

  function targetFields() {
    baselineSequence++;
    baselines = [];
    if (kind.value === "workflows") {
      target.replaceChildren(
        field("目标完整 manifest 路径", "target_manifest", "", "text", { required: true, autocomplete: "off" }),
        field("目标完整 manifest 摘要", "target_digest", "", "text", { required: true, spellcheck: "false" }),
        field("目标根的新版本", "next_version", "", "text", { required: true }),
        node("p", {}, "目标是待改进的完整图；下方作者 manifest 是本次提出候选的图，两者分别填写。"));
      return;
    }
    const chooser = selectField("当前候选基线", [["", "读取目录后明确选择"]], "", "baseline");
    chooser.querySelector("select").required = true;
    const observed = node("div", { "aria-live": "polite" });
    const read = button("读取当前基线", async () => {
      const reading = ++baselineSequence;
      const selectedKind = kind.value;
      sequence++;
      baselines = [];
      const select = chooser.querySelector("select");
      select.replaceChildren(node("option", { value: "" }, "读取目录后明确选择"));
      read.disabled = true;
      observed.replaceChildren(empty("正在读取当前来源…"));
      try {
        const value = await api(`${base}/${selectedKind === "skills" ? "skills/heads" : "memory-catalog"}`);
        if (!active() || reading !== baselineSequence) return;
        baselines = selectedKind === "skills" ? value.active : value.records.filter((item) => item.validity === "valid").map((item) => item.record);
        if (selectedKind === "memories") select.append(node("option", { value: "new" }, "明确新建记忆（revision 0）"));
        baselines.forEach((item, index) => select.append(node("option", { value: index }, selectedKind === "skills"
          ? `${item.name} · revision ${item.revision} · ${item.digest}` : `${item.id} · revision ${item.revision}`)));
        observed.replaceChildren(node("details", {}, node("summary", {}, "完整基线目录与有效性"), pre(value)),
          node("p", {}, "本次读取不是租约；保存输入时重新核对当前来源。重读会清空本次基线选择。"));
      } catch (error) {
        if (active() && reading === baselineSequence) observed.replaceChildren(empty(error.message));
      } finally {
        if (active() && reading === baselineSequence) read.disabled = false;
      }
    });
    target.replaceChildren(row(read), chooser, observed);
  }

  async function prepare() {
    if (!active() || preparing || !evidence) return;
    const values = Object.fromEntries(new FormData(form));
    const payload = { ...evidence, objective: values.objective, manifest: values.manifest,
      instance: values.instance, destination: values.destination, max_prompt_bytes: Number(values.max_prompt_bytes) };
    if (kind.value === "skills") {
      const head = baselines[Number(values.baseline)];
      Object.assign(payload, { name: head.name, digest: head.digest, head_revision: head.revision });
    } else if (kind.value === "memories") {
      const creating = values.baseline === "new";
      const record = creating ? null : baselines[Number(values.baseline)];
      Object.assign(payload, { memory_id: creating ? null : record.id, revision: creating ? 0 : record.revision });
    } else Object.assign(payload, { target_manifest: values.target_manifest, target_digest: values.target_digest, next_version: values.next_version });
    const submittedKind = kind.value;
    const reading = ++sequence;
    preparing = true;
    fields.disabled = true;
    directory.value = payload.destination;
    inspectionSequence++;
    inspectButton.disabled = false;
    inspection.replaceChildren();
    attempted.textContent = `上次明确提交的目录：${payload.destination}。修改表单不撤销已保存的文件。`;
    status.replaceChildren(empty("正在核对原来源并保存完整输入…"));
    try {
      const saved = await api(`${base}/retrospectives/${submittedKind}/prepare`, payload);
      if (!active()) return;
      status.replaceChildren(panel(reading === sequence ? "完整候选输入已保存" : "上次来源的输入已保存",
        reading === sequence ? "仅保存输入；未调用 Agent，也未生成或采用候选。" : "当前来源已变化；下方是上次提交的原结果。请明确复读原目录，不能把它当作新来源的输入。",
        pre(saved)));
    } catch (error) {
      if (active()) status.replaceChildren(panel("准备未获确认", error.message,
        "原提交目录保留；没有自动重发。可明确读取该目录核对是否已经保存，已有目录不会被覆盖。"));
    } finally {
      preparing = false;
      if (active()) fields.disabled = !evidence;
    }
  }

  async function inspect() {
    if (!active() || inspectButton.disabled) return;
    const reading = ++inspectionSequence;
    inspectButton.disabled = true;
    inspection.replaceChildren(empty("正在核对完整已有输入及其项目…"));
    try {
      const observed = await api(`${base}/retrospectives/inputs/inspect`, { directory: directory.value });
      if (!active() || reading !== inspectionSequence) return;
      inspection.replaceChildren(panel("完整已有输入已读取", "这是该目录的原请求与全部继承材料。请核对项目、方向、基线、目标、证据与输入摘要；复读不会重新准备或调用模型。",
        pre(observed), node("p", {}, "按使用手册的 composition run-input 继续调用；检查候选与采用仍分别明确执行。")));
    } catch (error) {
      if (active() && reading === inspectionSequence) inspection.replaceChildren(panel("已有输入读取失败", error.message));
    } finally {
      if (active() && reading === inspectionSequence) inspectButton.disabled = false;
    }
  }

  kind.addEventListener("change", targetFields);
  form.addEventListener("input", () => { sequence++; });
  form.addEventListener("change", () => { sequence++; });
  directory.addEventListener("input", () => {
    inspectionSequence++;
    inspectButton.disabled = false;
    inspection.replaceChildren(empty("目录已更改，请明确读取。"));
  });
  targetFields();
  return {
    element: panel("准备复盘候选输入", "明确保存 Skill、记忆或工作流作者的完整输入。准备不会运行模型、导出候选或改变活动版本。", sourceNotice, form, attempted, status,
      panel("复读已保存输入", "丢回复、切页或换电脑后，可用原目录明确复读；原 input 是保存事实的来源。", inspectForm, inspection)),
    setEvidence(selected, observed) {
      sequence++;
      evidence = selected;
      fields.disabled = preparing || !evidence;
      sourceNotice.textContent = selected ? `使用上方 ${selected.selection.length} 份完整原件，选择摘要 ${observed.sha256}。` : "上方完整证据尚未就绪；原表单保留，须重新读取完整选择才能准备。";
    },
  };
}
