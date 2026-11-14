import { api } from "./api.js";
import { node, pre, panel, field, selectField, status, form, modal, button, row, empty, table } from "./ui.js";
import { app } from "./state.js";

function archivedHistory(base, runId, active = () => true) {
  const content = node("div");
  let nextOffset = null;
  let revision = null;
  const start = button("读取原生历史", () => read(true));
  const next = button("下一页", () => read(false), "secondary", { disabled: true });
  const view = panel("原生历史归档", "按页查看已保存的输入、工具结果和模型回复。", row(start, next), content);
  const displayed = () => active() && view.isConnected && view.closest("dialog")?.open;
  async function read(reset) {
    start.disabled = true;
    next.disabled = true;
    try {
      const query = new URLSearchParams({ native_history: "true", history_offset: reset ? 0 : nextOffset });
      if (!reset) query.set("history_revision", revision);
      const result = await api(`${base}/agent-runs/${runId}/output?${query}`);
      if (!displayed()) return;
      const page = result.native_history;
      if (!page.available) {
        content.replaceChildren(node("p", {}, page.reason));
        return;
      }
      revision = page.revision;
      nextOffset = page.next_offset;
      content.replaceChildren(
        node("p", {}, `${page.offset}–${page.offset + page.bytes_read} / ${page.size_bytes} 字节`, nextOffset === null ? " · 已到本次观察末尾" : ""),
        pre(page.content),
      );
      next.disabled = nextOffset === null;
      start.textContent = "从头读取";
    } catch (error) {
      if (displayed()) throw error;
    } finally {
      if (displayed()) start.disabled = false;
    }
  }
  return view;
}

export function outputPanels(result, base, active) {
  const panels = Object.entries(result.streams).map(([name, stream]) =>
    panel(
      name === "stdout" ? "标准输出" : "诊断输出",
      !stream.available
        ? "输出文件尚未产生"
        : stream.truncated
          ? "显示前 64 KiB；完整输出保存在运行归档"
          : "",
      pre(stream.text),
    ),
  );
  if (base) panels.push(archivedHistory(base, result.id, active));
  return panels;
}
export function agentDialog(data, base, refresh) {
  const result = node("div");
  modal(
    "运行 Agent",
    form(
      [
        selectField(
          "角色",
          [...app.agentRoles.map((role) => [role, app.layers[role][0]])],
          "reviewer",
          "role",
        ),
        selectField(
          "模板产物要求（可选）",
          [
            ["", "普通独立调用"],
            ...app.bootstrap.templates.map((kind) => [kind, kind]),
          ],
          "",
          "template",
        ),
        field("任务说明", "prompt", "", "textarea", { required: true }),
        field("活动 Skill 名称（逗号分隔，可选）", "skills"),
        field("项目记忆检索（可选）", "recall"),
        field("超时（秒）", "timeout", 300, "number", { min: 1, max: 3600 }),
        result,
      ],
      "执行调用",
      async (values) => {
        result.replaceChildren(
          node("p", {}, "工具正在执行。可在其他页面刷新查看运行记录。"),
        );
        const response = await api(`${base}/agent-runs`, {
          role: values.get("role"),
          prompt: values.get("prompt"),
          timeout: Number(values.get("timeout")),
          skills: values
            .get("skills")
            .split(",")
            .map((x) => x.trim())
            .filter(Boolean),
          recall: values.get("recall") || null,
          template: values.get("template") || null,
        });
        const output = await api(`${base}/agent-runs/${response.id}/output`);
        result.replaceChildren(
          status(response.status),
          pre(response),
          ...outputPanels(output, base),
        );
        await refresh(data.project.id);
      },
    ),
  );
}

export function compositionDialog(data, base, origin, onResult) {
  const backends = new Map(app.agentRoles.flatMap((role) => app.bootstrap.tools[role].map((item) =>
    [item.tool, item.supported === false ? `${item.tool} · WSL2/Linux` : item.tool])));
  const checkButton = node("button", { type: "submit", className: "primary" }, "检查当前只读准入");
  const checkStatus = node("div", { "aria-live": "polite" });
  const callStatus = node("div", { "aria-live": "polite" });
  const attempted = node("p", { "aria-live": "polite" });
  const checkFields = node("fieldset", {}, node("legend", {}, "原冻结输入与本次后端"),
    field("冻结 input 路径", "directory", "", "text", { required: true, autocomplete: "off" }),
    field("冻结 input digest", "input_digest", "", "text", { required: true, spellcheck: "false" }),
    selectField("叶后端", [["", "使用冻结定义的请求"], ...backends], "", "backend"),
    field("叶模型（可选）", "model"), field("后端选择原因（可选）", "reason"),
    field("Codex 推理配置路径（可选）", "codex_config", "", "text", { autocomplete: "off" }), row(checkButton));
  const checkForm = node("form", { onsubmit: (event) => { event.preventDefault(); return check(); } }, checkFields);
  const runFields = node("fieldset", { disabled: true }, node("legend", {}, "明确调用这个叶"),
    field("单叶超时（秒）", "timeout", 300, "number", { required: true, min: 1, max: 3600, step: 1 }),
    row(node("button", { type: "submit", className: "primary" }, "明确调用这个只读叶")));
  const runForm = node("form", { onsubmit: (event) => { event.preventDefault(); return invoke(); } }, runFields);
  const records = node("div", { "aria-live": "polite" });
  const view = node("div", {},
    panel("冻结 input 的单叶调用", "只运行原 text-only 模式，交付全部冻结祖先资料；不运行图端口、workspace 或正式 Task。准入是当前观察，执行前原 owner 会重新核对。", checkForm, checkStatus, runForm, attempted, callStatus),
    panel("原调用记录", "明确读取当前项目最近最多100条原记录。丢回复或切页不表示没有调用；先核对 input digest、原后端、时间与状态，不自动重发。",
      row(button("读取原调用记录", readRecords)), records));
  const active = () => origin.isConnected && view.isConnected && view.closest("dialog")?.open && app.data === data && app.project === data.project.id;
  let sequence = 0;
  let recordSequence = 0;
  let selected = null;
  let running = false;

  function invalidate() {
    sequence++;
    selected = null;
    checkButton.disabled = running;
    runFields.disabled = true;
    checkStatus.replaceChildren(empty("输入或后端已更改，请明确重新检查。"));
  }

  function resultAction(run) {
    return onResult && run.kind === "composition-agent-run" && run.status === "succeeded" && run.result && run.result_sha256
      ? button("带入原结果检查", () => {
        if (active() && onResult({ directory: run.input_path, input_digest: run.input_digest,
          result: run.result, result_sha256: run.result_sha256 })) view.closest("dialog").close();
      }) : null;
  }

  async function check() {
    if (!active() || running || checkButton.disabled) return;
    const values = Object.fromEntries(new FormData(checkForm));
    const payload = { ...values, backend: values.backend || null, model: values.model || null,
      reason: values.reason || null, codex_config: values.codex_config || null };
    invalidate();
    const reading = sequence;
    checkButton.disabled = true;
    checkStatus.replaceChildren(empty("正在核对完整 input 与当前后端准入…"));
    try {
      const admission = await api(`${base}/composition-inputs/check`, payload);
      if (!active() || reading !== sequence) return;
      selected = { payload, admission };
      runFields.disabled = false;
      checkStatus.replaceChildren(panel("当前只读准入已检查", "下方是原 owner 的角色、requested／actual binding、资料身份与能力范围。只读工具限制不是 OS 隔离；检查不授权正式任务。", pre(admission)));
    } catch (error) {
      if (active() && reading === sequence) checkStatus.replaceChildren(panel("只读准入检查失败", error.message));
    } finally {
      if (active() && reading === sequence) checkButton.disabled = false;
    }
  }

  async function invoke() {
    if (!active() || running || !selected) return;
    const selection = selected;
    const timeout = Number(new FormData(runForm).get("timeout"));
    running = true;
    checkFields.disabled = runFields.disabled = true;
    attempted.textContent = `上次明确提交：${selection.payload.directory} · ${selection.payload.input_digest} · ${timeout} 秒。原后端参数见下方；页面变化不取消已发起的调用。`;
    callStatus.replaceChildren(pre({ ...selection.payload, timeout }), empty("原 owner 正在保存输入并调用单叶；可以明确读取原调用记录。"));
    try {
      const run = await api(`${base}/composition-inputs/run`, { ...selection.payload, timeout });
      if (!active()) return;
      callStatus.replaceChildren(panel(selected === selection ? "单叶调用已返回原记录" : "上次输入的单叶调用已返回",
        "请核对原 status、result 路径／SHA及实际后端；进程成功不等于质量通过或候选采用。", status(run.status), pre(run), row(resultAction(run))));
    } catch (error) {
      if (active()) callStatus.replaceChildren(panel("单叶调用未获确认", error.message,
        "没有自动重发。先读取原调用记录，核对上次 input 与后端；网络错误不证明没有运行。"));
    } finally {
      running = false;
      if (active()) {
        checkFields.disabled = false;
        checkButton.disabled = false;
        runFields.disabled = !selected;
      }
    }
  }

  async function readRecords() {
    if (!active()) return;
    const reading = ++recordSequence;
    records.replaceChildren(empty("正在读取原调用记录…"));
    try {
      const observed = await api(`${base}/agent-runs`);
      if (!active() || reading !== recordSequence) return;
      records.replaceChildren(...(observed.length ? observed.map((run) => node("details", {},
        node("summary", {}, `${run.id} · ${run.role} · ${run.binding.tool} · ${run.status}`),
        table(["原身份", "记录"], [["输入 digest", run.input_digest ?? "普通角色调用"],
          ["result SHA256", run.result_sha256 ?? "尚无原结果"], ["开始", run.started], ["结束", run.finished ?? "未记录"]]),
        pre(run), row(resultAction(run), button("读取原诊断输出", async () => {
          try {
            const output = await api(`${base}/agent-runs/${encodeURIComponent(run.id)}/output`);
            if (active() && reading === recordSequence)
              records.append(panel(`原诊断 ${run.id}`, "诊断按原 owner 有界展示；完整候选使用 result 文件与 SHA，不使用截断诊断。", ...outputPanels(output, base, () => active() && reading === recordSequence)));
          } catch (error) {
            if (active() && reading === recordSequence) records.append(panel("原诊断读取失败", error.message));
          }
        })))) : [empty("原目录中没有调用记录。") ]));
    } catch (error) {
      if (active() && reading === recordSequence) records.replaceChildren(panel("原调用记录读取失败", error.message));
    }
  }

  checkForm.addEventListener("input", invalidate);
  checkForm.addEventListener("change", invalidate);
  modal("调用冻结的只读叶", view);
}
