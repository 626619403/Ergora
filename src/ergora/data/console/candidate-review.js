import { api } from "./api.js";
import {
  $, node, button, pre, panel, empty, row, field, form, modal, table,
} from "./ui.js";

export function candidateReview({ base, taskId, record, isCurrent }) {
  const lookupResult = node("div", { "aria-live": "polite" });
  const digest = field("已保存关联的 SHA256", "review_context_sha256", "", "text", {
    required: true, pattern: "[a-f0-9]{64}", maxlength: 64, autocomplete: "off",
  });
  let lookupSequence = 0;
  const content = node("div", { className: "candidate-review" },
    node("p", {}, "关联只保存本地上下文；PR／MR正文不授予批准，也不证明原发送成功或资源由Ergora创建。"),
  );
  const active = () => isCurrent() && content.isConnected && $("#dialog").open;

  function show(saved, target) {
    const payload = saved.payload;
    const review = payload.review_request.review;
    target.replaceChildren(panel("已保存的 PR／MR 上下文", "这是原不可变记录，不表示当前远端仍保持这些值。",
      table(["保存身份", "值"], [
        ["记录 SHA256", saved.sha256], ["候选范围 SHA256", saved.scope_sha256],
        ["原任务", payload.task.id], ["原 run", payload.task.run_id],
        ["原候选", payload.task.candidate_sha], ["原导出分支", payload.task.branch],
        ["原保存项目修订", payload.project.revision], ["首次关联时间", payload.linked_at],
        ["资源种类", review.kind], ["PR number／MR iid", review.number],
        ["平台原生 ID", review.native_id], ["原资源状态", review.state],
        ["原资源地址", review.web_url], ["原关联原因", payload.reason],
      ]),
      panel("完整原评审资料", review.title, pre(review.body)),
      table(["分别保存的基线事实", "值"], [
        ["原任务 base", payload.local.base_sha], ["当时远端 base", payload.base.sha],
        ["PR 响应 base", review.base.response_sha ?? "未知／未提供"],
        ["diff merge-base", review.diff_refs?.base_sha ?? "未知／未提供"],
        ["diff target commit", review.diff_refs?.start_sha ?? "未知／未提供"],
        ["diff head commit", review.diff_refs?.head_sha ?? "未知／未提供"],
      ]),
      node("details", {}, node("summary", {}, "完整原关联记录（安全文本）"), pre(saved)),
    ));
  }

  if (record) {
    const fields = node("fieldset", {},
      field("远端目标分支（base）", "base_branch", "", "text", {
        required: true, maxlength: 1024, autocomplete: "off",
      }),
      field("PR number／MR iid", "review_number", "", "text", {
        required: true, pattern: "[1-9][0-9]*", autocomplete: "off",
      }),
      field("关联原因", "reason", "", "textarea", { required: true, maxlength: 2000 }),
    );
    const result = node("div", { "aria-live": "polite" });
    let originalRequest = null;
    let writing = false;
    const restore = button("恢复原关联请求", save, "primary");
    const recovery = node("div");

    async function save() {
      if (!active() || writing) return;
      writing = true;
      fields.disabled = true;
      restore.disabled = true;
      recovery.replaceChildren();
      result.replaceChildren(empty("正在处理原关联请求；关闭页面不撤销已发出的本地保存。"));
      try {
        const response = await api(`${base}/candidate-review-links`, originalRequest);
        if (!active()) return;
        show(response.record, result);
        result.prepend(node("p", {}, response.fresh_observations
          ? "本次明确读取平台并首次保存本地关联。"
          : "返回原已保存关联；显示的是原不可变记录，新的原因不覆盖原内容。"));
      } catch (error) {
        if (!active()) return;
        result.replaceChildren(panel("关联结果尚未确认", error.message,
          node("p", {}, "保留原字段并明确恢复同一请求。原记录存在时返回它；尚无记录时可能重新读取平台并首次保存本地记录。"),
          node("details", {}, node("summary", {}, "本次固定的原请求"), pre(originalRequest)),
        ));
        recovery.replaceChildren(row(restore));
      } finally {
        writing = false;
        restore.disabled = false;
      }
    }

    content.append(panel("关联此原候选", "仅输入同来源仓库中已经存在的PR／MR；打开和填写不会读取平台。首次发送后固定原字段，回复未知时明确恢复原请求。",
      table(["原导出事实", "值"], [
        ["任务 ID", taskId], ["原 run ID", record.run_id],
        ["原候选", record.candidate_sha], ["原导出分支", record.branch],
        ["本次项目修订", record.project_revision],
      ]),
      form([fields], "确认保存已有 PR／MR 关联", async (values, element) => {
        if (!active() || originalRequest) return;
        originalRequest = { revision: record.project_revision, task_id: taskId,
          run_id: record.run_id, candidate_sha: record.candidate_sha,
          base_branch: values.get("base_branch"), review_number: values.get("review_number"),
          reason: values.get("reason") };
        element.querySelector("button[type=submit]").hidden = true;
        await save();
      }),
      result, recovery,
    ));
  }

  content.append(panel("按 SHA 离线读取原关联", "只读取当前项目保存的原记录，不要求平台、凭据、Git或原任务目录仍可用。",
    form([digest], "读取已保存 PR／MR 关联", async (values) => {
      if (!active()) return;
      const reading = ++lookupSequence;
      lookupResult.replaceChildren(empty("正在读取本地完整原关联…"));
      try {
        const saved = await api(`${base}/candidate-review-links/${encodeURIComponent(values.get("review_context_sha256"))}`);
        if (active() && reading === lookupSequence) show(saved, lookupResult);
      } catch (error) {
        if (active() && reading === lookupSequence)
          lookupResult.replaceChildren(panel("原关联读取失败", error.message));
      }
    }), lookupResult,
  ));
  digest.querySelector("input").addEventListener("input", () => {
    lookupSequence++;
    lookupResult.replaceChildren(empty("SHA已更改，旧读取已失效；请明确读取当前选择。"));
  });
  modal(record ? "关联已有 PR／MR" : "读取已保存 PR／MR 关联", content);
}
