import { api } from "./api.js";
import { app, bindingFor } from "./state.js";
import { submissionForm, recordRefreshNote as refreshNote } from "./submissions.js";
import {
  $, node, button, pre, short, heading, panel, empty, row, select,
  field, badge, status, modal, table,
} from "./ui.js";

// Only this window's unresolved HTTP submissions; original evaluation records remain authoritative.
const pendingEvaluations = new Map();

export function skillsView(data, base) {
  const active = () => view.isConnected;
  const evaluationKey = JSON.stringify([app.bootstrap.state_directory, base]);
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
  let diffSequence = 0;
  let comparisonSequence = 0;
  const evaluationResult = node("div", { "aria-live": "polite" });
  const suites = data.evaluations.suites;
  const suite = select(
    suites.map((item) => [
      item.digest,
      `${short(item.digest)} · ${item.manifest.cases.length} cases`,
    ]),
    suites[0]?.digest,
    "suite",
  );
  let evaluating = pendingEvaluations.has(evaluationKey);
  function allowEvaluation(request) {
    return button("已核原记录，允许新的评价", () => {
      if (!active() || pendingEvaluations.get(evaluationKey) !== request) return;
      pendingEvaluations.delete(evaluationKey);
      evaluating = false;
      evaluationButtons.forEach((item) => { item.disabled = !suites.length; });
      evaluationResult.replaceChildren(empty("已明确解除本窗口的未决请求锁；新的评价仍须单独提交。"));
    });
  }
  const previousEvaluation = pendingEvaluations.get(evaluationKey);
  if (previousEvaluation) evaluationResult.append(
    empty(previousEvaluation.unknown ? "上次评价回复不确定；先刷新并核对原记录。" : "本窗口已提交评价，等待完整回复；稍后明确刷新核对原记录。"),
    pre(previousEvaluation.submitted), refreshNote(),
    previousEvaluation.unknown ? allowEvaluation(previousEvaluation) : null,
  );
  async function evaluate(digest) {
    if (!active() || evaluating || pendingEvaluations.has(evaluationKey)) return;
    if (!suite.value || !digest) throw new Error("先导入 Skill 并注册评价集");
    const submitted = { digest, suite: suite.value };
    const request = { submitted, unknown: false };
    pendingEvaluations.set(evaluationKey, request);
    evaluating = true;
    evaluationButtons.forEach((item) => { item.disabled = true; });
    evaluationResult.replaceChildren(node("p", {}, "正在执行可信 evaluator；以下为本次提交的版本与 suite。"), pre(submitted));
    let observed = false;
    try {
      const result = await api(`${base}/evaluations/run`, submitted);
      observed = true;
      pendingEvaluations.delete(evaluationKey);
      if (active()) {
        evaluationResult.firstChild.textContent = "以下为本次提交与评价原记录；进程完成不代表通过采用门禁。";
        evaluationResult.append(pre(result), refreshNote());
      }
    } catch (error) {
      request.unknown = true;
      if (active()) {
        evaluationResult.firstChild.textContent = "未取得完整评价结果；该请求可能已经执行。";
        evaluationResult.append(node("p", { className: "error" }, error.message), refreshNote(), allowEvaluation(request));
      }
    } finally {
      if (active() && observed) {
        evaluating = false;
        evaluationButtons.forEach((item) => { item.disabled = !suites.length; });
      }
    }
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
  function invalidateComparison() {
    comparisonSequence++;
    compareButton.disabled = !runOptions.length;
    comparison.replaceChildren();
  }
  for (const input of [baseline, candidate]) input.addEventListener("change", () => {
    diffSequence++;
    diffButton.disabled = false;
    diffResult.replaceChildren();
    invalidateComparison();
  });
  for (const input of [suite, baseRun, candidateRun])
    input.addEventListener("change", invalidateComparison);
  async function compare() {
    if (!active() || compareButton.disabled) return;
    if (!baseRun.value || !candidateRun.value)
      throw new Error("先完成双方评价");
    invalidateComparison();
    const sequence = comparisonSequence;
    const current = () => active() && sequence === comparisonSequence;
    compareButton.disabled = true;
    const baselineId = baseRun.value,
      candidateId = candidateRun.value;
    try {
      const result = await api(
        `${base}/evaluations/compare?baseline=${encodeURIComponent(baselineId)}&candidate=${encodeURIComponent(candidateId)}`,
      );
      if (!current()) return;
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
            ? submissionForm(
                [
                  pre({ baseline_run: baselineId, candidate_run: candidateId, revision: head?.revision || 0 }),
                  field("采用理由", "reason", "", "textarea", { required: true }),
                ],
                "采用候选",
                `${base}/skills/adopt`,
                (values) => ({
                    baseline_run: baselineId,
                    candidate_run: candidateId,
                    revision: head?.revision || 0,
                    reason: values.get("reason"),
                }),
                current,
              )
            : null,
        ),
      );
    } catch (error) {
      if (current()) comparison.replaceChildren(node("p", { className: "error" }, error.message));
    } finally {
      if (current()) compareButton.disabled = !runOptions.length;
    }
  }
  const items = versions.map((item) => {
    const head = data.skills.active.find((active) => active.name === item.name);
    const isActive = head?.digest === item.digest;
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
            isActive ? `活动修订 ${head.revision}` : "候选 / 历史",
            isActive ? "green" : "gray",
          ),
        ),
        button("版本详情", () => modal("Skill 版本", pre(item)), "text-button"),
      ),
      node("div", { className: "version-meta mono" }, item.digest),
      node("p", { className: "form-note" }, item.hypothesis),
      !isActive && data.skills.history.some((event) => event.to === item.digest)
        ? button(
            "回退到此版本",
            () =>
              modal(
                "回退活动 Skill",
                submissionForm(
                  [
                    pre({ name: item.name, digest: item.digest, revision: head.revision }),
                    field("回退理由", "reason", "", "textarea", {
                      required: true,
                    }),
                  ],
                  "确认回退",
                  `${base}/skills/rollback`,
                  (values) => ({
                      name: item.name,
                      digest: item.digest,
                      revision: head.revision,
                      reason: values.get("reason"),
                  }),
                  active,
                ),
              ),
            "text-button",
          )
        : null,
    );
  });
  const diffButton = button("比较版本", async () => {
    if (!active() || diffButton.disabled) return;
    if (!baseline.value || !candidate.value) throw new Error("先导入两个版本");
    const sequence = ++diffSequence;
    const current = () => active() && sequence === diffSequence;
    const selected = { baseline: baseline.value, candidate: candidate.value };
    diffButton.disabled = true;
    diffResult.replaceChildren();
    try {
      const result = await api(`${base}/skills/diff?baseline=${selected.baseline}&candidate=${selected.candidate}`);
      if (!current()) return;
      const diff = pre(result.diff || "SKILL.md 无文本变化；请核对其他文件。");
      diff.className = "diff";
      diffResult.replaceChildren(pre(selected), node("p", { className: "form-note" },
        `变更文件：${result.changed_files.join(", ") || "无"}`), diff);
    } catch (error) {
      if (current()) diffResult.replaceChildren(node("p", { className: "error" }, error.message));
    } finally {
      if (current()) diffButton.disabled = false;
    }
  });
  const evaluationButtons = [
    button("评价基线", () => evaluate(baseline.value), "secondary", { disabled: evaluating || !suites.length }),
    button("评价候选", () => evaluate(candidate.value), "secondary", { disabled: evaluating || !suites.length }),
  ];
  const compareButton = button("比较评价证据", compare, "primary", { disabled: !runOptions.length });
  const controls = panel(
    "比较与评价",
    "固定评价集，检查完整目录变更；双方证据使用相同 suite。",
    node(
      "div",
      { className: "form-grid" },
      node("label", {}, "基线版本", baseline),
      node("label", {}, "候选版本", candidate),
    ),
    row(diffButton),
    diffResult,
    node("hr"),
    node("label", {}, "固定评价集", suite),
    row(evaluationButtons),
    evaluationResult,
    node("hr"),
    node(
      "div",
      { className: "form-grid" },
      node("label", {}, "基线评价记录", baseRun),
      node("label", {}, "候选评价记录", candidateRun),
    ),
    row(compareButton),
    comparison,
    node(
      "details",
      {},
      node("summary", {}, "注册评价集 JSON"),
      submissionForm(
        [
          field("评价集 JSON", "manifest", "", "textarea", {
            required: true,
            placeholder:
              "按 docs/INTEGRATIONS.md 的 schema 填写；使用可信评分命令与独立保留集",
          }),
        ],
        "固定并注册评价集",
        `${base}/evaluations/suites`,
        (values) => JSON.parse(values.get("manifest")),
        active,
      ),
    ),
  );
  const view = node("div", { className: "skill-workbench" },
    heading(
      "用证据改进 Skill",
      "导入完整 Agent Skills 目录。新版本先成为候选，通过正确性、验证集和保留集门禁后再采用。",
      button(
        "＋ 导入目录",
        () =>
          modal(
            "导入 Skill",
            submissionForm(
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
              `${base}/skills/import`,
              (values) => Object.fromEntries(values),
              active,
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
      `当前优化工具：${bindingFor(data, "optimizer").tool}。优化只产生候选，采用继续使用上方证据门禁。`,
      bindingFor(data, "optimizer").tool === "gepa"
        ? submissionForm(
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
            `${base}/optimizations`,
            (values) => {
              if (!baseline.value || !suite.value)
                throw new Error("先选择基线和评价集");
              return {
                baseline: baseline.value,
                suite: suite.value,
                objective: values.get("objective"),
                max_evaluations: Number(values.get("max_evaluations")),
                max_proposals: Number(values.get("max_proposals")),
                timeout: Number(values.get("timeout")),
              };
            },
            active,
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
  );
  return [view];
}
