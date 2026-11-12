import { api } from "./api.js";
import {
  $, node, pre, panel, empty, field, form, modal, table,
} from "./ui.js";

// A transient view of the original export; the existing owner validates it.
export function candidateObservation({ base, taskId, record, isCurrent }) {
  const branch = field("远端目标分支（base）", "base_branch", "", "text", {
    required: true, maxlength: 1024, autocomplete: "off",
  });
  const input = branch.querySelector("input");
  const result = node("div", { "aria-live": "polite" },
    empty("填写目标分支后明确查询；打开此页面不会访问远端。"));
  let querySequence = 0;
  const content = node("div", { className: "candidate-observation" },
    node("p", {}, "核对原候选与当前本地／远端分支。每份事实分别读取，不能证明谁推送过、期间是否变化或获得执行批准。"),
    table(["原导出事实", "值"], [
      ["任务 ID", taskId], ["原 run ID", record.run_id],
      ["原候选提交", record.candidate_sha], ["原导出分支", record.branch],
      ["原导出意图 SHA256", record.intent_sha256],
      ["本次项目修订", record.project_revision],
    ]),
    form([branch], "明确查询当前分支", async (values) => {
      if (!active()) return;
      const querying = ++querySequence;
      result.replaceChildren(empty("正在分别读取当前本地与远端事实…"));
      try {
        const observed = await api(`${base}/candidate-observations`, {
          revision: record.project_revision, task_id: taskId,
          run_id: record.run_id, candidate_sha: record.candidate_sha,
          base_branch: values.get("base_branch"),
        });
        if (!current(querying)) return;
        result.replaceChildren(panel("本次分支观察", "相等只表示这次读取值相同；404表示不存在或不可见，比较保持未知。结果没有保存为发布回执。",
          table(["核对对象", "原目标值", "当前读取值", "比较"], [
            ["本地导出分支", record.candidate_sha, observed.local.current_branch_sha,
              observed.comparisons.local_export_ref_matches_candidate],
            ["远端候选分支", record.candidate_sha, observed.remote.head.sha,
              observed.comparisons.head_matches_candidate],
            ["远端目标分支", observed.local.base_sha, observed.remote.base.sha,
              observed.comparisons.base_matches_task_base],
          ].map(([name, original, value, matches]) => [
            name, original, value ?? "未知", matches == null ? "未知" : matches ? "相同" : "不同",
          ])),
          table(["远端事实", "读取时间", "HTTP", "响应 SHA256"],
            ["repository", "head", "base"].map((key) => [
              key, observed.remote[key].observed_at,
              observed.remote[key].http_status, observed.remote[key].response_sha256,
            ])),
          node("p", {}, `汇总时间：${observed.observed_at}。各次读取不是共享快照，不能排除期间变化或ABA。`),
          node("details", {}, node("summary", {}, "完整本次观察（安全文本）"), pre(observed)),
        ));
      } catch (error) {
        if (current(querying)) result.replaceChildren(panel("本次观察失败", error.message,
          node("p", {}, "没有取得新的完整结果。请核对原来源、当前项目修订与远端读取配置，再明确查询。")));
      }
    }),
    result,
  );
  const active = () => isCurrent() && content.isConnected && $("#dialog").open;
  const current = (querying) => active() && querying === querySequence;
  input.addEventListener("input", () => {
    querySequence++;
    result.replaceChildren(empty("目标分支已更改，旧观察已失效；请明确查询新的选择。"));
  });
  modal("观察当前候选分支", content);
}
