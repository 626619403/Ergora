import { api } from "./api.js";
import {
  $, node, button, pre, short, heading, panel, empty, row, select,
  field, badge, status, notify, form, modal, table,
} from "./ui.js";

export function skillsView(data, base, { refresh }) {
  const versions = data.skills.versions;
  const versionOptions = versions.map((item) => [
    item.digest,
    `${item.name} · ${short(item.digest)}`,
  ]);
  const activeDigest = data.skills.active[0]?.digest || versionOptions[0]?.[0];
  const candidateDigest =
    versions.find((item) => item.digest !== activeDigest)?.digest ||
    activeDigest;
  const baseline = select(versionOptions, activeDigest, "baseline");
  const candidate = select(versionOptions, candidateDigest, "candidate");
  const diffResult = node("div");
  const suites = data.evaluations.suites;
  const suite = select(
    suites.map((item) => [
      item.digest,
      `${short(item.digest)} · ${item.manifest.cases.length} cases`,
    ]),
    suites[0]?.digest,
    "suite",
  );
  async function evaluate(digest) {
    if (!suite.value || !digest) throw new Error("先导入 Skill 并注册评价集");
    notify("正在执行可信 evaluator；请保留页面或稍后刷新查看证据");
    const result = await api(`${base}/evaluations/run`, {
      digest,
      suite: suite.value,
    });
    await refresh(data.project.id);
    modal("评价记录", pre(result));
  }
  const runOptions = data.evaluations.runs.map((item) => [
    item.id,
    `${short(item.skill)} · ${item.status} · ${short(item.id)}`,
  ]);
  const baseRun = select(
    runOptions,
    data.evaluations.runs.find((item) => item.skill === activeDigest)?.id,
    "baseline_run",
  );
  const candidateRun = select(
    runOptions,
    data.evaluations.runs.find((item) => item.skill === candidateDigest)?.id,
    "candidate_run",
  );
  const comparison = node("div");
  async function compare() {
    if (!baseRun.value || !candidateRun.value)
      throw new Error("先完成双方评价");
    const baselineId = baseRun.value,
      candidateId = candidateRun.value;
    const result = await api(
      `${base}/evaluations/compare?baseline=${encodeURIComponent(baselineId)}&candidate=${encodeURIComponent(candidateId)}`,
    );
    const candidateVersion = versions.find(
      (item) => item.digest === result.candidate,
    );
    const head = data.skills.active.find(
      (item) => item.name === candidateVersion?.name,
    );
    comparison.replaceChildren(
      node(
        "div",
        { className: `result-box ${result.eligible ? "" : "rejected"}` },
        node(
          "strong",
          {},
          result.eligible
            ? "评价门禁通过 · 等待审阅采用"
            : "候选尚不满足采用条件",
        ),
        pre(result),
        result.eligible
          ? form(
              [field("采用理由", "reason", "", "textarea", { required: true })],
              "采用候选",
              async (values) => {
                await api(`${base}/skills/adopt`, {
                  baseline_run: baselineId,
                  candidate_run: candidateId,
                  revision: head?.revision || 0,
                  reason: values.get("reason"),
                });
                await refresh(data.project.id);
                notify("候选已采用；下一次工具调用可选择该活动 Skill");
              },
            )
          : null,
      ),
    );
  }
  const items = versions.map((item) => {
    const head = data.skills.active.find((active) => active.name === item.name);
    const active = head?.digest === item.digest;
    return node(
      "div",
      { className: "list-item" },
      node(
        "div",
        { className: "row-between" },
        node(
          "div",
          { className: "version-heading" },
          node("strong", {}, item.name),
          badge(
            active ? `活动修订 ${head.revision}` : "候选 / 历史",
            active ? "green" : "gray",
          ),
        ),
        button("版本详情", () => modal("Skill 版本", pre(item)), "text-button"),
      ),
      node("div", { className: "version-meta mono" }, item.digest),
      node("p", { className: "form-note" }, item.hypothesis),
      !active && data.skills.history.some((event) => event.to === item.digest)
        ? button(
            "回退到此版本",
            () =>
              modal(
                "回退活动 Skill",
                form(
                  [
                    field("回退理由", "reason", "", "textarea", {
                      required: true,
                    }),
                  ],
                  "确认回退",
                  async (values) => {
                    await api(`${base}/skills/rollback`, {
                      name: item.name,
                      digest: item.digest,
                      revision: head.revision,
                      reason: values.get("reason"),
                    });
                    $("#dialog").close();
                    await refresh(data.project.id);
                    notify("活动版本已回退");
                  },
                ),
              ),
            "text-button",
          )
        : null,
    );
  });
  const controls = panel(
    "比较与评价",
    "固定评价集，检查完整目录变更；双方证据使用相同 suite。",
    node(
      "div",
      { className: "form-grid" },
      node("label", {}, "基线版本", baseline),
      node("label", {}, "候选版本", candidate),
    ),
    row(
      button("比较版本", async () => {
        if (!baseline.value || !candidate.value)
          throw new Error("先导入两个版本");
        const result = await api(
          `${base}/skills/diff?baseline=${baseline.value}&candidate=${candidate.value}`,
        );
        const diff = pre(
          result.diff || "SKILL.md 无文本变化；请核对其他文件。",
        );
        diff.className = "diff";
        diffResult.replaceChildren(
          node(
            "p",
            { className: "form-note" },
            `变更文件：${result.changed_files.join(", ") || "无"}`,
          ),
          diff,
        );
      }),
    ),
    diffResult,
    node("hr"),
    node("label", {}, "固定评价集", suite),
    row(
      button("评价基线", () => evaluate(baseline.value), "secondary", {
        disabled: !suites.length,
      }),
      button("评价候选", () => evaluate(candidate.value), "secondary", {
        disabled: !suites.length,
      }),
    ),
    node("hr"),
    node(
      "div",
      { className: "form-grid" },
      node("label", {}, "基线评价记录", baseRun),
      node("label", {}, "候选评价记录", candidateRun),
    ),
    row(
      button("比较评价证据", compare, "primary", {
        disabled: !runOptions.length,
      }),
    ),
    comparison,
    node(
      "details",
      {},
      node("summary", {}, "注册评价集 JSON"),
      form(
        [
          field("评价集 JSON", "manifest", "", "textarea", {
            required: true,
            placeholder:
              "按 docs/INTEGRATIONS.md 的 schema 填写；使用可信评分命令与独立保留集",
          }),
        ],
        "固定并注册评价集",
        async (values) => {
          await api(
            `${base}/evaluations/suites`,
            JSON.parse(values.get("manifest")),
          );
          await refresh(data.project.id);
          notify("评价集已固定并登记");
        },
      ),
    ),
  );
  return [
    heading(
      "用证据改进 Skill",
      "导入完整 Agent Skills 目录。新版本先成为候选，通过正确性、验证集和保留集门禁后再采用。",
      button(
        "＋ 导入目录",
        () =>
          modal(
            "导入 Skill",
            form(
              [
                field("本机 Skill 目录", "directory", "", "text", {
                  required: true,
                  placeholder: "/path/to/my-skill",
                }),
                field(
                  "改进假设",
                  "hypothesis",
                  "Imported candidate",
                  "textarea",
                  { required: true },
                ),
                node(
                  "p",
                  {},
                  "目录名称须与 SKILL.md 中的 name 一致。首次同名导入建立初始基线，后续版本只创建候选。",
                ),
              ],
              "导入 Skill",
              async (values) => {
                await api(`${base}/skills/import`, Object.fromEntries(values));
                $("#dialog").close();
                await refresh(data.project.id);
                notify("Skill 版本已导入");
              },
            ),
          ),
        "primary",
      ),
    ),
    node(
      "div",
      { className: "grid-two" },
      controls,
      panel(
        "版本与活动状态",
        null,
        items.length ? items : empty("还没有 Skill。先导入一个标准目录。"),
      ),
    ),
    panel(
      "有限优化",
      `当前优化工具：${data.project.bindings.optimizer.tool}。优化只产生候选，采用继续使用上方证据门禁。`,
      data.project.bindings.optimizer.tool === "gepa"
        ? form(
            [
              field("优化目标", "objective", "", "textarea", {
                required: true,
              }),
              node(
                "div",
                { className: "form-grid" },
                field("最多 metric calls", "max_evaluations", 20, "number", {
                  min: 1,
                  max: 1000,
                }),
                field("最多提案", "max_proposals", 5, "number", {
                  min: 1,
                  max: 100,
                }),
                field("总时限（秒）", "timeout", 300, "number", {
                  min: 1,
                  max: 3600,
                }),
              ),
            ],
            "运行 GEPA 优化",
            async (values) => {
              if (!baseline.value || !suite.value)
                throw new Error("先选择基线和评价集");
              const result = await api(`${base}/optimizations`, {
                baseline: baseline.value,
                suite: suite.value,
                objective: values.get("objective"),
                max_evaluations: Number(values.get("max_evaluations")),
                max_proposals: Number(values.get("max_proposals")),
                timeout: Number(values.get("timeout")),
              });
              await refresh(data.project.id);
              modal("优化记录", pre(result));
            },
          )
        : node(
            "p",
            {},
            "可手动导入改进候选，或在工具绑定中选择 GEPA 并配置 JSON 提案器。",
          ),
      ...data.optimizations.slice(0, 5).map((item) =>
        row(
          status(item.status),
          node("code", {}, short(item.id)),
          button("查看证据", () => modal("优化证据", pre(item)), "text-button"),
        ),
      ),
    ),
    panel(
      "评价历史",
      null,
      table(
        ["候选", "状态", "报告成本", "证据"],
        data.evaluations.runs.map((item) => [
          short(item.skill),
          status(item.status),
          item.reported_cost,
          button("查看记录", () => modal("评价证据", pre(item)), "text-button"),
        ]),
      ),
    ),
  ];
}
