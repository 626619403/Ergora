import { node, field, selectField } from "./ui.js";

// The component catalog owns field structure; callers own selection and saving.
export function bindingFields(component, current = {}, { projectId = "", prefix = "" } = {}) {
  const schema = component.configuration;
  const controls = new Map();
  const element = node("div", {}, Object.entries(schema.properties).flatMap(([name, property]) => {
    if (name === "tool") return [];
    const required = schema.required.includes(name);
    const value = current[name] ?? property["x-ergora-project-default"]?.replace("{project_id}", projectId)
      ?? property.default ?? "";
    const key = prefix + name;
    let label;
    if (property.enum) {
      const labels = property["x-ergora-enum-labels"] || {};
      const entries = property.enum.map((item) => [item, labels[item] || item]);
      if (!required) entries.unshift(["", property["x-ergora-empty-label"] || "使用默认值"]);
      label = selectField(property.title, entries, value, key);
    } else if (property.type === "array") {
      label = field(property.title, key, JSON.stringify(value === "" ? [] : value), "textarea");
    } else if (["number", "integer"].includes(property.type)) {
      const ui = property["x-ergora-ui"] || {};
      label = field(property.title, key, value, "number", {
        min: ui.min ?? property.minimum, max: property.maximum,
        step: ui.step ?? (property.type === "integer" ? 1 : "any"),
      });
    } else if (property.type === "string") {
      label = field(property.title, key, value, property.format === "uri" ? "url" : "text");
    } else {
      throw new Error(`不支持的配置字段类型：${property.type}`);
    }
    const control = label.querySelector("input,textarea,select");
    control.required = required;
    controls.set(name, control);
    return [label];
  }), component.note ? node("p", {}, component.note) : null);
  return {
    element,
    read() {
      const binding = { tool: component.tool };
      for (const [name, control] of controls) {
        const value = control.value;
        if (value === "" && !schema.required.includes(name)) continue;
        const property = schema.properties[name];
        binding[name] = property.type === "array" ? JSON.parse(value)
          : ["number", "integer"].includes(property.type) ? Number(value) : value;
      }
      return binding;
    },
  };
}
