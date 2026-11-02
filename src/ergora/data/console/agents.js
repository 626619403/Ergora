import { api } from "./api.js";
import { node, pre, panel, field, selectField, status, form, modal } from "./ui.js";
import { app } from "./state.js";

export function outputPanels(result) {
  return Object.entries(result.streams).map(([name, stream]) =>
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
          ...outputPanels(output),
        );
        await refresh(data.project.id);
      },
    ),
  );
}
