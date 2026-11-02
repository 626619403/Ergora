import { api } from "./api.js";
import {
  $, node, button, pre, short, heading, panel, empty, row, field,
  badge, notify, form, modal,
} from "./ui.js";

export function memoryView(data, base, { refresh }) {
  const cards = node("div", { className: "memory-grid" });
  const show = (items) =>
    cards.replaceChildren(
      ...(items.length
        ? items.map((item) =>
            node(
              "article",
              { className: "panel memory-card" },
              node(
                "div",
                { className: "row-between" },
                badge(`修订 ${item.revision}`),
                node("small", { className: "muted" }, short(item.id)),
              ),
              node("div", { className: "memory-body" }, item.text),
              node(
                "div",
                { className: "source-line" },
                node("strong", {}, item.source.uri),
                ` · ${item.source.revision}`,
              ),
              node(
                "div",
                { className: "memory-actions" },
                button(
                  "更正",
                  () => memoryDialog(data, base, refresh, item),
                  "text-button",
                ),
                button(
                  "修订历史",
                  async () => {
                    const history = await api(
                      `${base}/memories/${item.id}/history`,
                    );
                    modal(
                      "记忆修订历史",
                      history.map((version) =>
                        panel(
                          `修订 ${version.revision}`,
                          version.observed,
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
                    );
                  },
                  "text-button",
                ),
                button(
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
                ),
              ),
            ),
          )
        : [empty("保存第一条带来源的项目记忆。")]),
    );
  show(data.memories);
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
        show(
          query.value.trim()
            ? (
                await api(
                  `${base}/memory-search?query=${encodeURIComponent(query.value)}`,
                )
              ).results
            : data.memories,
        );
      },
    },
    query,
    node("button", { className: "secondary", type: "submit" }, "检索"),
  );
  return [
    heading(
      "让项目经验持续积累",
      "记录可更正、可检索的观察，并保留它来自哪里。检索沿用当前绑定的记忆后端。",
      button("＋ 新增记忆", () => memoryDialog(data, base, refresh), "primary"),
    ),
    searchForm,
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
      "重建适用于远端 workspace 被清空或迁移后。删除不改写已归档的工具输入和独立备份。",
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
        });
        $("#dialog").close();
        await refresh(data.project.id);
        notify("记忆已保存");
      },
    ),
  );
}
