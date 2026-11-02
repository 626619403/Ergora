import { api } from "./api.js";
import { node, button, pre, panel, row, status, modal, table } from "./ui.js";
import { app, stages } from "./state.js";
import { agentDialog, outputPanels } from "./agents.js";

export function overview(data, base, { refresh, render }) {
  const counts = [
    ["项目记忆", data.memories.length, "有来源的持久记录", "▤"],
    ["活动 Skill", data.skills.active.length, "明确采用的版本", "◇"],
    [
      "待审资料",
      data.research.proposals.filter((item) => item.status === "pending")
        .length,
      "观察结果需要人工核对",
      "◎",
    ],
    ["工具调用", data.agent_runs.length, "最近最多 100 次调用", "⌘"],
  ];
  return [
    node(
      "section",
      { className: "hero" },
      node(
        "div",
        {},
        node("div", { className: "eyebrow" }, "Project workspace"),
        node("h1", {}, "把协作变成可积累的能力"),
        node(
          "p",
          {},
          "为项目组合适合的工具，让记忆带有来源，让改进经过评价，让每次执行留下证据。",
        ),
        button(
          "配置工具 →",
          () => {
            app.tab = "tools";
            render();
          },
          "primary",
        ),
      ),
      node(
        "div",
        { className: "hero-art", "aria-hidden": "true" },
        node("div", { className: "orbit-node" }, "◇"),
        node("div", { className: "orbit-line" }),
        node("div", { className: "orbit-node center" }, "e"),
        node("div", { className: "orbit-line" }),
        node("div", { className: "orbit-node" }, "◎"),
      ),
    ),
    node(
      "div",
      { className: "stats" },
      counts.map(([label, value, note, icon]) =>
        node(
          "div",
          { className: "stat" },
          node(
            "div",
            { className: "stat-label" },
            label,
            node("span", {}, icon),
          ),
          node("div", { className: "stat-value" }, value),
          node("small", {}, note),
        ),
      ),
    ),
    node(
      "div",
      { className: "grid-two" },
      panel(
        "六阶段协作合同",
        "沿用固定阶段，工作单元可以按依赖关系并行。",
        node(
          "div",
          { className: "stages" },
          stages.map((stage, index) =>
            node(
              "div",
              { className: "stage" },
              node("div", { className: "stage-number" }, `0${index + 1}`),
              node("strong", {}, stage),
            ),
          ),
        ),
        node(
          "div",
          { className: "stage-note" },
          "○ 这是协议阶段说明。正式执行和验收状态由参考运行时产生。",
        ),
        row(
          button("设计工作单元", () => {
            app.tab = "workflow";
            render();
          }),
        ),
      ),
      panel(
        "项目约定",
        null,
        node(
          "div",
          { className: "check-row" },
          node("span", { className: "check-icon" }, "▤"),
          node(
            "div",
            {},
            node("strong", {}, "记忆有来源与修订"),
            node("p", {}, "更正保留历史；删除与远端同步分别确认。"),
          ),
        ),
        node(
          "div",
          { className: "check-row" },
          node("span", { className: "check-icon" }, "◇"),
          node(
            "div",
            {},
            node("strong", {}, "候选先评价再采用"),
            node("p", {}, "固定评分和保留集，采用及回退都记录理由。"),
          ),
        ),
        node(
          "div",
          { className: "check-row" },
          node("span", { className: "check-icon" }, "⌘"),
          node(
            "div",
            {},
            node("strong", {}, data.project.repo),
            node("p", {}, `项目配置修订 ${data.project.revision}`),
          ),
        ),
      ),
    ),
    panel(
      "最近工具调用",
      "进程成功退出仅代表调用完成，正式验收继续使用已有证据门禁。",
      row(button("运行一次 Agent", () => agentDialog(data, base, refresh), "primary")),
      table(
        ["角色 / 工具", "状态", "开始时间", "记录"],
        data.agent_runs.slice(0, 8).map((item) => [
          node("span", {}, item.role, node("small", {}, item.binding.tool)),
          status(item.status),
          item.started,
          button(
            "查看记录",
            async () => {
              const output = await api(`${base}/agent-runs/${item.id}/output`);
              modal("工具调用记录", [pre(item), ...outputPanels(output)]);
            },
            "text-button",
          ),
        ]),
      ),
    ),
  ];
}
