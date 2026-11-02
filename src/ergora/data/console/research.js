import { api } from "./api.js";
import { bindingFor } from "./state.js";
import {
  $, node, button, pre, lines, short, heading, panel, empty, row,
  field, selectField, checkbox, status, notify, form, modal, table,
} from "./ui.js";

export function researchView(data, base, { refresh }) {
  const observing = form(
    [
      field("来源 URL（每行一个，最多 10 个）", "urls", "", "textarea", {
        required: true,
        placeholder: "https://example.com/official-doc",
      }),
      node(
        "div",
        { className: "form-grid" },
        field("正文总预算（字节）", "max_bytes", 1000000, "number", {
          min: 1,
          max: 10000000,
        }),
        field("总时限（秒）", "timeout", 30, "number", { min: 1, max: 300 }),
      ),
      field("观察 ID（可选；相同 ID 的输入被冻结）", "id"),
      checkbox("允许可信内网来源", "allow_private"),
      node(
        "p",
        { className: "form-note" },
        "页面内容只作为资料；不会执行其中指令或自动写入有效记忆。",
      ),
    ],
    "观察指定来源",
    async (values) => {
      const result = await api(`${base}/research-runs`, {
        urls: lines(values.get("urls")),
        max_bytes: Number(values.get("max_bytes")),
        timeout: Number(values.get("timeout")),
        id: values.get("id") || null,
        allow_private: values.has("allow_private"),
      });
      await refresh(data.project.id);
      modal("资料观察结果", pre(result));
    },
  );
  const proposals = data.research.proposals.map((item) =>
    node(
      "div",
      { className: "list-item" },
      node(
        "div",
        { className: "row-between" },
        node("span", { className: "url" }, item.url),
        status(item.status),
      ),
      node(
        "div",
        { className: "version-meta mono" },
        `SHA ${short(item.sha)} · ${item.observed}`,
      ),
      row(
        button(
          "核对资料",
          async () => {
            const source = await api(`${base}/research-proposals/${item.id}`);
            modal("核对来源快照", [
              node("p", { className: "url" }, source.final_url),
              node("small", { className: "mono" }, source.sha),
              pre(source.text),
              form(
                [
                  field("审阅理由", "reason", "", "textarea", {
                    required: true,
                  }),
                  selectField(
                    "处理方式",
                    [
                      ["reviewed", "已核对"],
                      ["dismissed", "不采用此资料"],
                    ],
                    "reviewed",
                    "status",
                  ),
                ],
                "保存资料审阅",
                async (values) => {
                  await api(`${base}/research-proposals/${item.id}/review`, {
                    status: values.get("status"),
                    reason: values.get("reason"),
                    revision: source.revision,
                  });
                  $("#dialog").close();
                  await refresh(data.project.id);
                  notify("资料审阅已记录；活动记忆与 Skill 由你单独决定");
                },
              ),
            ]);
          },
          "text-button",
        ),
      ),
    ),
  );
  return [
    heading(
      "观察资料变化",
      "明确来源与预算，保存可核对的快照。只有内容变化才产生新提案，重复观察保留记录。",
    ),
    node(
      "div",
      { className: "grid-two equal-columns" },
      panel("发起观察", null, observing),
      panel(
        "资料提案",
        null,
        proposals.length
          ? proposals
          : empty("尚无来源快照。先发起一次资料观察。"),
      ),
    ),
    panel(
      "观察记录",
      "操作中可以刷新列表并请求取消；终态由实际执行确认。",
      table(
        ["观察 ID", "状态", "正文计费", "操作"],
        data.research.runs.map((item) => [
          node("code", {}, item.id),
          status(item.status),
          `${item.bytes} bytes${item.reserved_bytes ? ` + ${item.reserved_bytes} reserved` : ""}`,
          row(
            button("记录", () => modal("观察证据", pre(item)), "text-button"),
            item.status === "running"
              ? button(
                  "请求取消",
                  async () => {
                    await api(`${base}/research-runs/${item.id}/cancel`, {});
                    await refresh(data.project.id);
                    notify("取消请求已登记；刷新确认实际终态");
                  },
                  "text-button danger",
                )
              : null,
          ),
        ]),
      ),
    ),
    panel(
      "持久调度",
      `当前调度工具：${bindingFor(data, "scheduler").tool}`,
      pre(
        `ergora research worker ${data.project.id}\nergora research schedule ${data.project.id} create docs-check --url https://example.com/official-doc --interval 86400\nergora research schedule ${data.project.id} trigger docs-check\nergora research schedule ${data.project.id} resume docs-check`,
      ),
      node(
        "p",
        {},
        "Temporal Schedule 默认暂停；先配置 scheduler、启动 worker 并核对一次触发结果，再启用。每次有独立预算，长期总量由频率和预算共同决定。",
      ),
    ),
  ];
}
