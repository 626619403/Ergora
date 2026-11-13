import { api } from "./api.js";
import { node, button, pre, panel, empty, table } from "./ui.js";

export function trainingPreparationPanel(base, active, prepared, inspect, platform) {
  if (platform !== "linux")
    return panel("准备实验", "实验准备与恢复请在登记的 Linux／WSL2 环境执行，详见 docs/TRAINING.md。");

  let sequence = 0, sending = false;
  const result = node("div", { "aria-live": "polite" });
  const changed = () => { sequence++; result.replaceChildren(); };
  const source = node("textarea", { rows: 14, "aria-label": "完整 experiment JSON", spellcheck: "false",
    placeholder: "粘贴已审阅的完整 experiment.json", oninput: changed });
  const runner = node("input", { type: "text", "aria-label": "实验 runner ID", autocomplete: "off", oninput: changed });
  const duration = node("input", { type: "number", "aria-label": "实验排队加执行窗口", min: 60, max: 86400,
    placeholder: "省略使用原默认值", oninput: changed });
  const recovery = node("input", { type: "text", "aria-label": "读取准备记录的实验 ID", autocomplete: "off", oninput: changed });
  const view = panel("准备实验", "预览完整合同并确认后，只发布原 manifest／spec；不会 start 或运行训练。需要 ergora[temporal]，无需服务。",
    node("details", {}, node("summary", {}, "预览与准备实验"),
      source, node("label", {}, "已登记 runner ID", runner),
      node("label", {}, "排队加执行窗口（秒）", duration), button("预览实验准备", preview)),
    node("details", {}, node("summary", {}, "读取与恢复原准备记录"),
      node("label", {}, "原实验 ID", recovery), button("读取准备记录", () => read(recovery.value))), result);

  const current = (request) => active() && request === sequence;
  const setSending = (value) => {
    sending = value;
    for (const control of view.querySelectorAll("button, input, textarea")) control.disabled = value;
  };

  function show(observed, request) {
    const id = observed.experiment_id;
    result.replaceChildren(table(["准备记录", "值"], [
      ["实验 ID", id], ["状态", observed.status], ["项目修订", observed.project_revision],
      ["原意图 SHA256", observed.intent_sha256 || "尚无本工具准备意图"],
    ]), node("details", {}, node("summary", {}, "完整原意图与逐件文件状态"), pre(observed)));
    if (observed.status === "prepared") {
      result.append(empty("三份原文件已匹配确认计划；这不表示已经提交、训练成功或获得采用批准。"),
        button("查看已准备实验", () => { if (current(request)) inspect(id); }));
      return;
    }
    if (!["intent_saved", "partially_prepared"].includes(observed.status)) {
      result.append(empty(observed.status === "not_recorded" ? "尚无准备意图。填写完整合同并先预览。"
        : "请核对原文件与来源；此入口不会覆盖冲突或接管没有准备意图的旧原生文件。"));
      return;
    }
    const confirmation = node("input", { type: "text", "aria-label": "确认准备恢复 intent SHA256",
      autocomplete: "off", spellcheck: "false", placeholder: "粘贴上方完整原意图 SHA256" });
    result.append(node("p", {}, "核对完整原意图、来源与文件状态，确认同一 SHA 后显式补齐。已有 job／fence／start 时会拒绝恢复。"),
      confirmation, button("恢复原实验准备", async () => {
        if (!current(request) || sending) return;
        if (confirmation.value !== observed.intent_sha256) throw new Error("请确认完整原准备意图 SHA256。");
        await publish(request, id, `${base}/training/${encodeURIComponent(id)}/resume-prepare`,
          { revision: observed.project_revision, intent_sha256: observed.intent_sha256 });
      }, "primary"));
  }

  async function read(id) {
    if (!active() || sending) return;
    if (!id) throw new Error("请填写原实验 ID。");
    const request = ++sequence;
    recovery.value = id;
    result.replaceChildren(empty("正在读取原准备记录…"));
    try {
      const observed = await api(`${base}/training/${encodeURIComponent(id)}/preparation`);
      if (current(request)) show(observed, request);
    } catch (error) {
      if (current(request)) result.replaceChildren(panel("未取得准备记录", error.message,
        button("重新读取原准备记录", () => read(id))));
    }
  }

  async function publish(request, id, path, payload) {
    setSending(true);
    try {
      const observed = await api(path, payload);
      if (current(request)) {
        recovery.value = id;
        show(observed, request);
        if (observed.status === "prepared") prepared();
      }
    } catch (error) {
      if (current(request)) result.replaceChildren(panel("本次准备操作未取得确认", error.message,
        node("p", {}, "原文件可能已经部分或全部发布。先按原 ID 读取准备意图，再明确恢复；不要自动重发或换 ID。"),
        button("读取原准备记录", () => read(id))));
    } finally {
      setSending(false);
    }
  }

  async function preview() {
    if (!active() || sending) return;
    const request = ++sequence;
    if (!duration.checkValidity()) throw new Error("请填写有效的整数窗口，或清空以使用默认值。");
    const experiment = JSON.parse(source.value);
    const payload = { experiment, runner_template_id: runner.value,
      max_run_seconds: duration.value === "" ? null : Number(duration.value) };
    result.replaceChildren(empty("正在验证完整实验与原生发布计划…"));
    try {
      const observed = await api(`${base}/training/experiment-preview`, payload);
      if (!current(request)) return;
      if (observed.preparation.status !== "not_recorded") {
        recovery.value = observed.experiment_id;
        show(observed.preparation, request);
        return;
      }
      const confirmation = node("input", { type: "text", "aria-label": "确认实验准备 preview SHA256",
        autocomplete: "off", spellcheck: "false", placeholder: "粘贴完整 preview_sha256" });
      result.replaceChildren(table(["准备预览", "值"], [
        ["实验 ID", observed.experiment_id], ["项目修订", observed.project_revision], ["完整计划 SHA256", observed.preview_sha256],
      ]), node("details", {}, node("summary", {}, "完整发布计划、来源与原生文件"), pre(observed)),
      node("p", {}, "核对完整 draft、runner、窗口与三份原文件后，粘贴计划 SHA 确认准备。"), confirmation,
      button("确认准备实验", async () => {
        if (!current(request) || sending) return;
        if (confirmation.value !== observed.preview_sha256) throw new Error("请确认完整实验准备计划 SHA256。");
        await publish(request, observed.experiment_id, `${base}/training/prepare`,
          { ...payload, revision: observed.project_revision, preview_sha256: observed.preview_sha256 });
      }, "primary"));
    } catch (error) {
      if (current(request)) result.replaceChildren(panel("未取得实验准备预览", error.message));
    }
  }

  return view;
}
