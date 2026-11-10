import { node, button, pre, empty, row, badge, panel, table, download } from "./ui.js";

// Compare facts from two admitted previews. Objects ignore key order; arrays
// retain their declared order. This is presentation, not permission inference.
function ordered(value) {
  if (Array.isArray(value)) return value.map(ordered);
  if (value && typeof value === "object")
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, ordered(value[key])]));
  return value;
}

function differences(before, after) {
  return [...new Set([...Object.keys(before), ...Object.keys(after)])].filter(
    (key) => JSON.stringify(ordered(before[key])) !== JSON.stringify(ordered(after[key])));
}

function instanceFacts(item) {
  const { path, resources, prompt, ...facts } = item;
  if (resources) {
    facts.resource_content = resources.map(({ kind, content_digest, text }) => ({ kind, content_digest, text }));
    facts.resource_provenance = resources.map(({ text, content_digest, digest, sha256, ...source }) => source);
  }
  return facts;
}

const labels = {
  ref: "精确引用", kind: "实例类型", parent: "结构父路径", role: "职能", review_requirement: "审查职责",
  backend_request: "后端请求", permissions: "权限声明", limits: "预算上限", usage: "预算用量",
  material_bytes: "装配材料字节", concurrency_scopes: "并发范围", depends_on: "先行依赖",
  inputs: "具名输入绑定", outputs: "具名输出绑定", levels: "原编译层级",
  resource_content: "资源内容身份与顺序", resource_provenance: "资源来源与声明",
  prompt_sha256: "装配提示身份", join: "汇合规则",
};

export function compositionComparisonView(before, after) {
  const oldInstances = new Map(before.instances.map((item) => [item.path, item]));
  const newInstances = new Map(after.instances.map((item) => [item.path, item]));
  const entries = [...new Set([...oldInstances.keys(), ...newInstances.keys()])].map((path) => {
    const oldItem = oldInstances.get(path), newItem = newInstances.get(path);
    const oldFacts = oldItem ? instanceFacts(oldItem) : {}, newFacts = newItem ? instanceFacts(newItem) : {};
    const changed = differences(oldFacts, newFacts);
    return { path, oldItem, newItem, oldFacts, newFacts, changed,
      status: !oldItem ? "新增" : !newItem ? "删除" : changed.length ? "变化" : "相同" };
  });
  const changed = entries.filter((item) => item.status !== "相同");
  const inspector = node("section", { className: "definition-details", "aria-label": "版本比较实例详情" });
  const choices = new Map();
  const value = (item) => item === undefined ? empty("不存在此字段") : pre(item);

  function inspect(entry) {
    for (const [path, choice] of choices) choice.setAttribute("aria-pressed", String(path === entry.path));
    inspector.replaceChildren(node("h3", {}, `${entry.path} · ${entry.status}`),
      entry.changed.length ? table(["变化字段", "比较前", "比较后"], entry.changed.map((key) =>
        [labels[key] || key, value(entry.oldFacts[key]), value(entry.newFacts[key])])) : empty("此实例的编译事实相同。"),
      ...[["比较前", entry.oldItem], ["比较后", entry.newItem]].map(([title, item]) =>
        node("details", {}, node("summary", {}, `${title}完整原实例（含全部资源、来源和提示）`),
          item ? pre(item) : empty("该版本不存在此实例。"))));
  }

  const { instances: oldItems, preview_sha256: oldDigest, ...oldPreviewFacts } = before;
  const { instances: newItems, preview_sha256: newDigest, ...newPreviewFacts } = after;
  const summaryChanges = differences(oldPreviewFacts, newPreviewFacts);
  const element = panel("两个已发布组合的精确比较",
    "按完整实例路径配对，同一引用的重复实例分别比较。对象键序忽略，数组顺序保留；权限只展示原声明差异，不推断包含关系。资源内容、来源和装配提示分别列出。此处尚未执行 Agent。",
    pre({ before: { root: before.root, preview_sha256: oldDigest }, after: { root: after.root, preview_sha256: newDigest },
      common_grant: before.grant }),
    row(...["新增", "删除", "变化", "相同"].map((label) => badge(`${label} ${entries.filter((item) => item.status === label).length}`))),
    summaryChanges.length ? node("details", {}, node("summary", {}, "根引用、总用量与其他预览事实差异"),
      table(["字段", "比较前", "比较后"], summaryChanges.map((key) =>
        [labels[key] || key, value(oldPreviewFacts[key]), value(newPreviewFacts[key])]))) : empty("两份预览的根与总用量事实相同。"),
    table(["完整实例路径", "结果", "变化字段"], entries.map((entry) => {
      const choice = button(entry.path, () => inspect(entry), "text-button", { "aria-pressed": "false" });
      choices.set(entry.path, choice);
      return [choice, entry.status, entry.changed.map((key) => labels[key] || key).join("、") || "—"];
    })),
    inspector,
    row(button("下载比较前 preview.json", () => download("composition-before.json", JSON.stringify(before, null, 2) + "\n")),
      button("下载比较后 preview.json", () => download("composition-after.json", JSON.stringify(after, null, 2) + "\n"))),
    node("p", {}, "差异摘要不替代完整材料；选择实例可逐字段核对并展开两个版本的完整原实例。仅来源版本变化也可能改变装配提示与字节用量，不代表资源正文改变。"));
  inspect(changed[0] || entries[0]);
  return element;
}
