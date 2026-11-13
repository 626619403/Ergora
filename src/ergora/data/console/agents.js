import { api } from "./api.js";
import { node, pre, panel, field, selectField, status, form, modal, button, row } from "./ui.js";
import { app } from "./state.js";

function archivedHistory(base, runId) {
  const content = node("div");
  let nextOffset = null;
  let revision = null;
  const start = button("读取原生历史", () => read(true));
  const next = button("下一页", () => read(false), "secondary", { disabled: true });
  const view = panel("原生历史归档", "按页查看已保存的输入、工具结果和模型回复。", row(start, next), content);
  const displayed = () => view.isConnected && view.closest("dialog")?.open;
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

export function outputPanels(result, base) {
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
  if (base) panels.push(archivedHistory(base, result.id));
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
