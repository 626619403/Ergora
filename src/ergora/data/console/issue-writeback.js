import { api } from "./api.js";
import {
  $, node, button, pre, panel, empty, row, field, select, form, modal, table,
} from "./ui.js";

export function issueWriteback({ base, revision, taskId, record, isCurrent }) {
  const digest = field("原回写意图的 SHA256", "intent_sha256", "", "text", {
    required: true, pattern: "[a-f0-9]{64}", maxlength: 64, autocomplete: "off",
  });
  const input = digest.querySelector("input");
  const result = node("div", { "aria-live": "polite" });
  const recovery = node("div");
  const content = node("div", { className: "issue-writeback" },
    node("p", {}, "准备只保存本地意图。发布评论或追加标签需要另行确认；关闭页面不会撤销已发操作。"),
  );
  let sequence = 0;
  let busy = false;
  const active = () => isCurrent() && content.isConnected && $("#dialog").open;
  const current = (reading) => active() && reading === sequence;

  function show(saved, reading) {
    recovery.replaceChildren();
    let selected = reading;
    const intent = saved.intent;
    const label = intent.kind === "candidate-label-add";
    const descriptions = {
      prepared: "尚未保存发送检查点。核对完整原意图后，可单独确认发送。",
      unknown: "原发送结果未知。保留原记录并观察当前事实；本页不提供补发。",
      acknowledged: "原单次响应已核对且回执已保存；这是历史事实，不代表当前评论或标签仍存在。",
    };
    const confirmation = node("div", {}, saved.status === "prepared" ? form([
      field("我已核对上述意图、原目标、账号及完整请求", "confirm", "yes", "checkbox", { required: true }),
    ], label ? "确认向原工单追加此标签" : "确认向原工单发送此评论", async () => {
      await act(saved.intent_sha256, "send", { revision, confirm: true }, reading);
    }) : null);
    const observation = node("div", {}, saved.latest_observation
      ? panel("最近已保存的观察", "当前可见事实不证明原发送成功，也不改变原状态。", pre(saved.latest_observation))
      : empty("本次返回未附带观察；可离线重读完整状态，或明确查询当前事实。"));
    const observer = label
      ? [field("不透明 cursor（留空读取第一页）", "cursor", "", "text", { autocomplete: "off" })]
      : commentQuery();
    const observeForm = form(observer, "明确观察当前一资源／页", async (values) => {
      const query = label ? (values.get("cursor") ? { cursor: values.get("cursor") } : {})
        : values.get("query_kind") === "comment"
          ? { comment_id: values.get("comment_id") } : { page: Number(values.get("page")) };
      await act(saved.intent_sha256, "observe", query, selected);
    });
    observeForm.addEventListener("input", () => {
      selected = ++sequence;
      confirmation.replaceChildren();
      observation.replaceChildren(empty("查询条件已更改，原发送确认已失效。请明确观察或离线重读状态，再核对新的返回记录。"));
    });

    result.replaceChildren(panel(`工单回写：${saved.status}`, descriptions[saved.status],
      table(["原意图事实", "值"], [
        ["意图 SHA256", saved.intent_sha256], ["动作", label ? "追加一个 GitHub 标签" : "中性工单评论"],
        ["来源平台", intent.source.provider], ["来源项目", intent.source.project],
        ["工单 number／iid", intent.source.issue_id], ["工单原生 ID", intent.source.native_id],
        ["原发送账号 ID", intent.actor_id], ["任务 ID", intent.task.id], ["原 run ID", intent.task.run_id],
        ["原候选", intent.task.candidate_sha], ["原本地导出分支", intent.task.branch],
        ["原准备修订", intent.project_revision], ["本页面项目修订", revision],
      ]),
      label ? panel("固定标签与原生请求", intent.label_name, pre({ native_target: intent.native_target, operation: intent.operation }))
        : panel("固定评论全文", "发送只使用已保存正文。", pre(intent.body)),
      confirmation,
      row(button("离线重读此原意图状态", () => {
        if (current(selected)) read(saved.intent_sha256);
      })),
      panel("明确观察当前事实", label
        ? "每次只查询一页。未在本页看到标签不表示不存在；可将 page_info.end_cursor 填入后明确查询下一页。"
        : "选择一个评论 ID 或一个列表页。可沿 next_page 明确查询下一页；匹配、修改、删除或空页均不确认原请求。",
      observeForm, observation),
      node("details", {}, node("summary", {}, "完整原意图、attempt、收据与返回观察（安全文本）"), pre(saved)),
    ));
  }

  function commentQuery() {
    const kind = select([["page", "一页评论列表"], ["comment", "一个原生评论 ID"]], "page", "query_kind");
    const page = field("列表页码", "page", "1", "number", { required: true, min: 1, max: 10000, step: 1 });
    const comment = field("原生评论 ID", "comment_id", "", "text", { pattern: "[1-9][0-9]*", autocomplete: "off" });
    const update = () => {
      const byId = kind.value === "comment";
      page.hidden = byId;
      page.querySelector("input").disabled = byId;
      comment.hidden = !byId;
      comment.querySelector("input").disabled = !byId;
      comment.querySelector("input").required = byId;
    };
    kind.addEventListener("change", update);
    update();
    return [node("label", {}, "观察范围", kind), page, comment];
  }

  async function read(sha) {
    if (!active() || busy) return;
    busy = true;
    const reading = ++sequence;
    input.value = sha;
    result.replaceChildren(empty("正在离线读取原意图状态…"));
    try {
      const saved = await api(`${base}/issue-writebacks/${encodeURIComponent(sha)}`);
      if (current(reading)) show(saved, reading);
    } catch (error) {
      if (current(reading)) result.replaceChildren(panel("原意图读取失败", error.message));
    } finally {
      busy = false;
    }
  }

  async function act(sha, operation, body, reading) {
    if (!current(reading) || busy) return;
    busy = true;
    const operating = ++sequence;
    result.replaceChildren(empty(operation === "send"
      ? "正在处理原发送；结果不明时请先离线读取原意图状态。"
      : "正在读取所选的一资源／页并保存观察…"));
    try {
      const saved = await api(`${base}/issue-writebacks/${encodeURIComponent(sha)}/${operation}`, body);
      if (current(operating)) show(saved, operating);
    } catch (error) {
      if (current(operating)) result.replaceChildren(panel(operation === "send" ? "发送结果尚未确认" : "本次观察未完成", error.message,
        node("p", {}, "先离线读取此原意图状态。没有回复不表示操作未发生；当前观察不会确认或重发原请求。"),
        pre({ intent_sha256: sha }),
        button("离线读取原意图状态", () => {
          if (current(operating)) read(sha);
        }),
      ));
    } finally {
      busy = false;
    }
  }

  if (record) {
    const kind = select([["comment", "中性工单评论"], ["label", "追加已存在的 GitHub 标签"]], "comment", "action");
    const label = field("完整标签名称", "label_name", "", "text", { autocomplete: "off" });
    const fields = node("fieldset", {}, node("label", {}, "回写动作", kind), label);
    const update = () => {
      label.hidden = kind.value !== "label";
      label.querySelector("input").disabled = kind.value !== "label";
      label.querySelector("input").required = kind.value === "label";
    };
    kind.addEventListener("change", update);
    update();
    let original = null;
    const restore = button("恢复原准备请求", prepare);

    async function prepare() {
      if (!active() || busy) return;
      busy = true;
      const preparing = ++sequence;
      fields.disabled = true;
      restore.disabled = true;
      result.replaceChildren(empty("正在读取身份并保存本地原意图；此操作不发布评论或标签。"));
      try {
        const saved = await api(`${base}/${original.endpoint}`, original.body);
        if (!current(preparing)) return;
        input.value = saved.intent_sha256;
        show(saved, preparing);
      } catch (error) {
        if (current(preparing)) result.replaceChildren(panel("准备结果尚未确认", error.message,
          node("p", {}, "保留原字段并明确恢复同一准备请求。原意图存在时返回它，尚无记录时可能首次读取身份并保存；不会发布工单动作。"),
          pre(original),
        ));
      } finally {
        busy = false;
        restore.disabled = false;
      }
    }

    content.append(panel("准备此原候选的回写", "第一次准备后固定动作与字段；标签名称原样保存，GitLab标签明确不支持。恢复始终沿用原请求，不自动发送。",
      table(["原导出事实", "值"], [
        ["任务 ID", taskId], ["原 run ID", record.run_id], ["原候选", record.candidate_sha],
        ["原导出分支", record.branch], ["本次项目修订", revision],
      ]),
      form([fields], "确认准备本地回写意图", async (values, element) => {
        if (!active() || original || busy) return;
        original = { endpoint: values.get("action") === "label" ? "issue-label-writebacks" : "issue-writebacks",
          body: { revision, task_id: taskId, run_id: record.run_id, candidate_sha: record.candidate_sha,
            ...(values.get("action") === "label" ? { label_name: values.get("label_name") } : {}) } };
        element.querySelector("button[type=submit]").hidden = true;
        recovery.replaceChildren(row(restore), node("p", {}, "恢复原准备请求可能首次保存本地意图。已有槽返回原记录，不覆盖原动作；它不是离线状态查询。"));
        await prepare();
      }), recovery,
    ));
  }

  content.append(panel("按 SHA 离线读取工单回写", "只读取本项目已保存意图、attempt、收据和最近观察，不访问平台或原任务目录。后续发送／观察需另行明确操作。",
    form([digest], "离线读取工单回写", async (values) => read(values.get("intent_sha256"))),
  ), result);
  input.addEventListener("input", () => {
    sequence++;
    result.replaceChildren(empty("SHA已更改，旧读取及动作已失效；请明确读取当前选择。"));
  });
  modal(record ? "准备工单回写" : "读取工单回写与观察", content);
}
