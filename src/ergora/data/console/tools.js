import { api } from "./api.js";
import {
  $, node, button, pre, heading, panel, select, field, selectField,
  badge, notify, form, modal,
} from "./ui.js";
import { app, bindingFor } from "./state.js";

export function toolsView(data, _base, { refresh }) {
  const diagnostics = node("div", {}, pre(data.tools));
  return [
    heading(
      "为每一层选择工具",
      "工具按项目绑定。检查结果区分本地可用性；认证、服务连接和实际效果需要进一步确认。",
    ),
    node(
      "div",
      { className: "tools-grid" },
      Object.entries(app.layers).map(([layer, [title, description, icon]]) => {
        const binding = bindingFor(data, layer);
        const resolved = data.configuration.layers[layer];
        const source = { project: "项目绑定", inherited: "继承实现者", "legacy-default": "旧项目兼容默认" }[resolved.source.kind];
        const check = data.tools.checks.find((item) => item.layer === layer);
        return node(
          "section",
          { className: "panel tool-card" },
          node("div", { className: "tool-icon" }, icon),
          node("h2", {}, title),
          node("p", {}, description),
          node(
            "div",
            { className: "tool-footer" },
            node(
              "div",
              {},
              node("div", { className: "tool-name" }, binding.tool),
              node("div", {}, source),
              badge(
                !resolved.validation.valid
                  ? "配置需修正"
                  : check?.installed === true
                  ? app.agentRoles.includes(layer)
                    ? "本地可用 · 认证待确认"
                    : check.connectivity === "not_checked"
                      ? "组件可用 · 服务待确认"
                      : "本地可用"
                  : check?.supported === false || check?.version === "unsupported_platform"
                    ? "需 WSL2 / Linux"
                  : check?.installed === false
                    ? "尚未安装"
                    : "外部配置待确认",
                !resolved.validation.valid || check?.installed === false ? "amber" : "gray",
              ),
              node("p", {}, `版本：${check?.version || "not_checked"}`),
              node("p", {}, `认证：${check?.authentication || "not_checked"} · 连接：${check?.connectivity || "not_checked"}`),
              node("p", {}, `任务前置条件：${check?.task_availability || "not_checked"}`),
            ),
            button("配置", () => bindingDialog(data, layer, refresh), "text-button", {
              "aria-label": `配置${title}`,
            }),
          ),
        );
      }),
    ),
    node(
      "div",
      { className: "info-bar" },
      app.bootstrap.reference_supported
        ? "独立调用使用当前项目绑定。正式六阶段需显式启用 ergora reference executor；它在新任务首次接入时冻结角色绑定，恢复不换 Agent。集成和可信验证仍由执行器负责。"
        : "当前系统不支持正式六阶段、mini-swe-agent 和 ForgeKernel；请在 WSL2/Linux 中安装运行。切换系统后重新注册项目与工具路径。",
    ),
    panel("检查详情", "已安装、凭据存在、TCP 可达与任务验收分别记录。主动探测共用 5 秒预算，不调用模型。",
      button("主动探测版本、凭据与连接", async () => {
        const result = await api(`/api/projects/${encodeURIComponent(data.project.id)}/doctor`, { timeout: 5 });
        diagnostics.replaceChildren(pre(result));
        notify("诊断完成；请查看分项状态与修复指引");
      }), diagnostics),
    panel(`有效绑定 · 修订 ${data.configuration.project.revision}`, "包含每层来源与校验结果；运行使用保存的快照。", pre(data.configuration)),
  ];
}
function bindingDialog(data, layer, refresh) {
  const current = bindingFor(data, layer);
  const choices = app.bootstrap.tools[layer];
  const choice = select(
    [["", "选择兼容工具"], ...choices.map((item) => [item.tool, item.supported === false ? `${item.tool} · WSL2/Linux` : item.tool])],
    choices.some((item) => item.tool === current.tool) ? current.tool : "",
    "tool",
  );
  choice.required = true;
  const options = node("div");
  let schema;
  function fields() {
    if (!choice.value) {
      schema = null;
      options.replaceChildren(node("p", {}, "请选择可用于这一层的工具，再保存绑定。"));
      return;
    }
    const component = choices.find((item) => item.tool === choice.value);
    schema = component.configuration;
    const same = choice.value === current.tool ? current : {};
    const content = [];
    for (const [name, property] of Object.entries(schema.properties)) {
      if (name === "tool") continue;
      const required = schema.required.includes(name);
      const value = same[name] ?? property["x-ergora-project-default"]?.replace("{project_id}", data.project.id)
        ?? property.default ?? "";
      if (property.enum) {
        const labels = property["x-ergora-enum-labels"] || {};
        const entries = property.enum.map((item) => [item, labels[item] || item]);
        if (!required) entries.unshift(["", property["x-ergora-empty-label"] || "使用默认值"]);
        content.push(selectField(property.title, entries, value, name));
      } else if (property.type === "array") {
        content.push(field(property.title, name, JSON.stringify(value === "" ? [] : value), "textarea", { required: required ? true : null }));
      } else if (["number", "integer"].includes(property.type)) {
        const ui = property["x-ergora-ui"] || {};
        content.push(field(property.title, name, value, "number", {
          required: required ? true : null, min: ui.min ?? property.minimum, max: property.maximum,
          step: ui.step ?? (property.type === "integer" ? 1 : "any"),
        }));
      } else if (property.type === "string") {
        content.push(field(property.title, name, value, property.format === "uri" ? "url" : "text", { required: required ? true : null }));
      } else {
        throw new Error(`不支持的配置字段类型：${property.type}`);
      }
    }
    if (component.note) content.push(node("p", {}, component.note));
    options.replaceChildren(...content);
  }
  choice.addEventListener("change", fields);
  fields();
  modal(
    app.layers[layer][0],
    form(
      [node("label", {}, "选择工具", choice), options],
      "保存绑定",
      async (values, element) => {
        const binding = { tool: choice.value };
        for (const [name, property] of Object.entries(schema.properties)) {
          if (name === "tool") continue;
          const value = values.get(name);
          if (value === null || (value === "" && !schema.required.includes(name))) continue;
          binding[name] = property.type === "array" ? JSON.parse(value)
            : ["number", "integer"].includes(property.type) ? Number(value) : value;
        }
        await api(
          `/api/projects/${encodeURIComponent(data.project.id)}/bindings/${layer}`,
          { binding, revision: data.project.revision },
          "PUT",
        );
        await refresh(data.project.id);
        if ($("#dialog").contains(element)) $("#dialog").close();
        notify("工具绑定已保存");
      },
    ),
  );
}
