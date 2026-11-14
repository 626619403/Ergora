import { api } from "./api.js";
import { submissionForm } from "./submissions.js";
import {
  $, node, button, pre, short, heading, panel, empty, row, field,
  badge, notify, modal,
} from "./ui.js";

const expiry = (item) => item.expires_at ? `到期 ${item.expires_at}` : "无到期限制";

export function memoryView(data, base) {
  const active = () => view.isConnected;
  const cards = node("div", { className: "memory-grid" });
  const observation = node("p", { className: "form-note" },
    "当前为最近刷新时的有效记忆快照。检索或读取目录以核对服务端当前状态；时间继续流逝后可能到期。",
  );
  let readSequence = 0;
  const read = async (path, display) => {
    const sequence = ++readSequence;
    try {
      const result = await api(path);
      if (sequence === readSequence && active()) display(result);
    } catch (error) {
      if (sequence === readSequence && active()) notify(error.message, true);
    }
  };
  async function historyDialog(item) {
    const content = node("div", {}, empty("正在读取原修订历史…"));
    modal("记忆修订历史", content);
    const current = () => active() && content.isConnected && $("#dialog").open;
    try {
      const history = await api(`${base}/memories/${item.id}/history`);
      if (!current()) return;
      const versions = history.map((version) => panel(
        `修订 ${version.revision} · ${version.status}`,
        version.observed,
        node("p", { className: "form-note" }, expiry(version)),
        pre({ text: version.text, source: version.source }),
        item.status === "active" && version.revision !== item.revision && version.status === "active"
          ? node("label", { className: "field-check" },
              node("input", { type: "radio", name: "from_revision", value: version.revision, required: true }),
              `恢复修订 ${version.revision}`)
          : null,
      ));
      const identity = pre({ project: data.project.id, id: item.id, revision: item.revision });
      content.replaceChildren(
        item.status === "active" && history.some((version) => version.revision !== item.revision && version.status === "active")
          ? submissionForm(
              [identity, node("p", { className: "form-note" },
                "选择一条原修订并明确恢复。追加新修订，保留所选历史的原有效期；已到期内容不会因此续期。"), versions],
              "恢复所选修订",
              `${base}/memories/${item.id}/restore`,
              (values) => ({ from_revision: Number(values.get("from_revision")), revision: item.revision }),
              current,
            )
          : node("div", {}, identity, versions, empty("没有可恢复的其他修订；已删除记忆不可恢复。")),
      );
    } catch (error) {
      if (current()) content.replaceChildren(node("p", { className: "error" }, error.message));
    }
  }
  const show = (items) =>
    cards.replaceChildren(
      ...(items.length
        ? items.map(({ record: item, validity }) =>
            node(
              "article",
              { className: "panel memory-card" },
              node(
                "div",
                { className: "row-between" },
                badge(`修订 ${item.revision}`),
                badge({ valid: "有效快照", expired: "已到期", deleted: "已删除" }[validity],
                  validity === "valid" ? "green" : "gray"),
                node("small", { className: "muted", title: item.id }, short(item.id)),
              ),
              node("p", { className: "form-note" }, expiry(item)),
              node("div", { className: "memory-body" }, item.status === "deleted" ? "正文与来源已清空。" : item.text),
              node(
                "div",
                { className: "source-line" },
                node("strong", {}, item.source.uri || "来源已清空"),
                item.source.revision ? ` · ${item.source.revision}` : "",
              ),
              node(
                "div",
                { className: "memory-actions" },
                item.status === "active" ? button(
                  "更正",
                  () => memoryDialog(data, base, active, item),
                  "text-button",
                ) : null,
                button("修订历史", () => historyDialog(item), "text-button"),
                item.status === "active" ? button(
                  "删除",
                  () => modal("删除项目记忆", submissionForm(
                    [
                      pre(item),
                      node("p", {}, "将清空此记忆的全部历史正文和来源。配置过 ReMe 时，随后执行同步确认远端删除。"),
                    ],
                    "确认删除",
                    `${base}/memories/${item.id}`,
                    () => ({ revision: item.revision }),
                    active,
                    "DELETE",
                  )),
                  "text-button danger",
                ) : null,
              ),
            ),
          )
        : [empty("此视图没有匹配记忆。可读取全部状态或新增带来源记忆。")]),
    );
  show(data.memories.map((record) => ({ record, validity: "valid" })));
  const showCatalog = (result, all) => {
    show(all ? result.records : result.records.filter((item) => item.validity === "valid"));
    observation.textContent = `${all ? "全部状态" : "有效记忆"} · 服务端判定 ${result.observed_at}。此后可能到期，目录仅供审阅。`;
  };
  const query = node("input", {
    name: "query",
    placeholder: "搜索项目约定、经验与来源…",
    "aria-label": "搜索项目记忆",
  });
  const searchForm = node(
    "form",
    {
      className: "search-row",
      onsubmit: async (event) => {
        event.preventDefault();
        if (query.value.trim())
          await read(`${base}/memory-search?query=${encodeURIComponent(query.value)}`, (result) => {
            show(result.results.map((record) => ({ record, validity: "valid" })));
            observation.textContent = `检索结果 · 服务端判定 ${result.observed_at}。只返回当时有效的当前修订。`;
          });
        else await read(`${base}/memory-catalog`, (result) => showCatalog(result, false));
      },
    },
    query,
    node("button", { className: "secondary", type: "submit" }, "检索"),
    button("读取全部状态", () => read(`${base}/memory-catalog`, (result) => showCatalog(result, true))),
  );
  const projectionDialog = (rebuild) => modal(rebuild ? "重建远端投影" : "同步记忆投影", submissionForm(
    [pre({ project: data.project.id, rebuild }), node("p", {},
      "仅同步原记忆的远端投影，不改变本地正文与有效期。配置与实际远端可用性由原记忆后端判定。")],
    rebuild ? "确认重建投影" : "确认同步投影",
    `${base}/memory-sync${rebuild ? "?rebuild=true" : ""}`,
    () => ({}),
    active,
  ));
  const view = node("div", {},
    heading(
      "让项目经验持续积累",
      "记录带来源与有效期的观察。默认检索排除已到期和已删除记录，使用当前绑定的记忆后端。",
      button("＋ 新增记忆", () => memoryDialog(data, base, active), "primary"),
    ),
    searchForm,
    observation,
    cards,
    row(
      button("同步记忆投影", () => projectionDialog(false)),
      button("重建远端投影", () => projectionDialog(true)),
    ),
    node(
      "p",
      { className: "form-note" },
      "到期保留历史，恢复历史修订会保留其原有效期。同步会清理到期或已删除的远端投影，索引可见性由 ReMe 决定。删除不改写已归档的工具输入和独立备份。",
    ),
  );
  return [view];
}

function memoryDialog(data, base, active, item) {
  const text = field("记忆正文", "text", item?.text || "", "textarea", {
    required: true, maxlength: 100000,
  });
  const originalInput = $("textarea", text).value;
  const file = field("正文 UTF-8 文件（可选；优先于输入框）", "text_file", "", "file", {
    accept: ".txt,text/plain",
    onchange: (event) => { $("textarea", text).required = !event.target.files.length; },
  });
  modal(
    item ? "更正项目记忆" : "新增项目记忆",
    submissionForm(
      [
        pre({ project: data.project.id, id: item?.id || null, revision: item?.revision || 0 }),
        text,
        file,
        node("p", { className: "form-note" },
          "导出的 memory.txt 可在此选择，保存其完整 UTF-8 原文（含 BOM 与换行）。输入框编辑使用浏览器换行；未编辑的更正保留原文。请同时核对导出回执中的来源。"),
        field("来源 URI", "uri", item?.source.uri || "", "text", {
          required: true,
          placeholder: "git:docs/design.md 或资料 URL",
        }),
        field("来源版本 / SHA", "source_revision", item?.source.revision || "", "text", {
          required: true, placeholder: "提交 SHA、快照 SHA 或明确版本",
        }),
        field("到期时间（含时区，留空为无限期）", "expires_at", item?.expires_at || "", "text", {
          placeholder: "2027-01-01T00:00:00+08:00",
        }),
        node("p", { className: "form-note" }, "更正会保留填入的有效期；清空此栏将明确移除限制。"),
      ],
      "保存记忆",
      `${base}/memories`,
      async (values) => {
        const file = values.get("text_file");
        return {
          text: file.size || file.name
            ? new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(await file.arrayBuffer())
            : item && values.get("text") === originalInput ? item.text : values.get("text"),
          source: { uri: values.get("uri"), revision: values.get("source_revision") },
          id: item?.id || null,
          revision: item?.revision || 0,
          expires_at: values.get("expires_at").trim() || null,
        };
      },
      active,
    ),
  );
}
