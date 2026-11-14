import { api } from "./api.js";
import {
  $, node, button, pre, short, heading, panel, empty, row, field,
  badge, notify, form, modal,
} from "./ui.js";

export function memoryView(data, base, { refresh }) {
  const cards = node("div", { className: "memory-grid" });
  const observation = node("p", { className: "form-note" },
    "当前为最近刷新时的有效记忆快照。检索或读取目录以核对服务端当前状态；时间继续流逝后可能到期。",
  );
  let readSequence = 0;
  const read = async (path, display) => {
    const sequence = ++readSequence;
    try {
      const result = await api(path);
      if (sequence === readSequence && cards.isConnected) display(result);
    } catch (error) {
      if (sequence === readSequence && cards.isConnected) notify(error.message, true);
    }
  };
  const expiry = (item) => item.expires_at ? `到期 ${item.expires_at}` : "无到期限制";
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
                node("small", { className: "muted" }, short(item.id)),
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
                  () => memoryDialog(data, base, refresh, item),
                  "text-button",
                ) : null,
                button(
                  "修订历史",
                  () => read(
                      `${base}/memories/${item.id}/history`,
                    (history) => modal(
                      "记忆修订历史",
                      history.map((version) =>
                        panel(
                          `修订 ${version.revision}`,
                          version.observed,
                          node("p", { className: "form-note" }, expiry(version)),
                          pre(version.text),
                          version.revision !== item.revision &&
                            version.status === "active"
                            ? button("恢复此修订", async () => {
                                await api(
                                  `${base}/memories/${item.id}/restore`,
                                  {
                                    from_revision: version.revision,
                                    revision: item.revision,
                                  },
                                );
                                $("#dialog").close();
                                await refresh(data.project.id);
                                notify("已创建恢复修订");
                              })
                            : null,
                        ),
                      ),
                    ),
                  ),
                  "text-button",
                ),
                item.status === "active" ? button(
                  "删除",
                  () =>
                    modal("删除项目记忆", [
                      node(
                        "p",
                        {},
                        "将清空此记忆的全部历史正文和来源。配置过 ReMe 时，随后执行同步确认远端删除。",
                      ),
                      button(
                        "确认删除",
                        async () => {
                          await api(
                            `${base}/memories/${item.id}`,
                            { revision: item.revision },
                            "DELETE",
                          );
                          $("#dialog").close();
                          await refresh(data.project.id);
                          notify("本地记录已删除；按需同步远端");
                        },
                        "secondary danger",
                      ),
                    ]),
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
  return [
    heading(
      "让项目经验持续积累",
      "记录带来源与有效期的观察。默认检索排除已到期和已删除记录，使用当前绑定的记忆后端。",
      button("＋ 新增记忆", () => memoryDialog(data, base, refresh), "primary"),
    ),
    searchForm,
    observation,
    cards,
    row(
      button("同步记忆投影", async () => {
        const result = await api(`${base}/memory-sync`, {});
        modal("记忆同步结果", pre(result));
      }),
      button("重建远端投影", async () => {
        const result = await api(`${base}/memory-sync?rebuild=true`, {});
        modal("投影重建结果", pre(result));
      }),
    ),
    node(
      "p",
      { className: "form-note" },
      "到期保留历史，恢复历史修订会保留其原有效期。同步会清理到期或已删除的远端投影，索引可见性由 ReMe 决定。删除不改写已归档的工具输入和独立备份。",
    ),
  ];
}
function memoryDialog(data, base, refresh, item) {
  modal(
    item ? "更正项目记忆" : "新增项目记忆",
    form(
      [
        field("记忆正文", "text", item?.text || "", "textarea", {
          required: true,
          maxlength: 100000,
        }),
        field("来源 URI", "uri", item?.source.uri || "", "text", {
          required: true,
          placeholder: "git:docs/design.md 或资料 URL",
        }),
        field(
          "来源版本 / SHA",
          "source_revision",
          item?.source.revision || "",
          "text",
          { required: true, placeholder: "提交 SHA、快照 SHA 或明确版本" },
        ),
        field("到期时间（含时区，留空为无限期）", "expires_at", item?.expires_at || "", "text", {
          placeholder: "2027-01-01T00:00:00+08:00",
        }),
        node("p", { className: "form-note" }, "更正会保留填入的有效期；清空此栏将明确移除限制。"),
      ],
      "保存记忆",
      async (values) => {
        await api(`${base}/memories`, {
          text: values.get("text"),
          source: {
            uri: values.get("uri"),
            revision: values.get("source_revision"),
          },
          id: item?.id || null,
          revision: item?.revision || 0,
          expires_at: values.get("expires_at").trim() || null,
        });
        $("#dialog").close();
        await refresh(data.project.id);
        notify("记忆已保存");
      },
    ),
  );
}
