import { api } from "./api.js";
import { node, button, pre, heading, panel, empty, row, field, form, table } from "./ui.js";
import { app } from "./state.js";

export function issuesView(data, base, { openSourceTask }) {
  const project = data.project;
  const binding = data.configuration.layers.tracker.binding;
  const title = heading("工单来源", "读取指定工单，保存完整上下文，或离线查看历史。保存快照不会启动任务。");
  const detail = node("div", { className: "task-detail", "aria-live": "polite" }, empty("读取工单或选择一份已保存快照。"));
  const entries = node("div", { className: "issue-history", "aria-live": "polite" });
  const pageNote = node("p", { className: "form-note" });
  let detailSequence = 0;
  let pageSequence = 0;
  let pageIndex = 0;
  let page;
  const cursors = [null];
  const previous = button("上一页", () => { pageIndex--; loadHistory(); });
  const next = button("下一页", () => {
    cursors[++pageIndex] = page.next_cursor;
    loadHistory();
  });
  const current = form([
    node("p", {}, binding.tool === "manual"
      ? "当前为手动模式。选择 GitHub 或 GitLab 工具绑定后，可读取指定工单；历史快照仍可离线浏览。"
      : `当前来源：${binding.tool} · ${binding.project}`),
    field("工单 number／iid", "issue_id", "", "text", { required: true, inputmode: "numeric" }),
  ], "读取当前工单", async (values) => {
    const sequence = ++detailSequence;
    const issueId = values.get("issue_id").trim();
    detail.replaceChildren(empty(`正在读取工单 ${issueId}…`));
    try {
      const observed = await api(`${base}/issues/${encodeURIComponent(issueId)}`);
      if (!selected(sequence)) return;
      showObservation(observed);
    } catch (error) {
      if (selected(sequence)) detail.replaceChildren(panel("未取得当前工单", error.message));
    }
  });
  if (binding.tool === "manual")
    current.querySelectorAll("input,button").forEach((element) => { element.disabled = true; });
  current.querySelector("input").addEventListener("input", () => {
    detailSequence++;
    detail.replaceChildren(empty("编号已修改，请读取所选工单。"));
  });
  const view = node("div", { className: "task-layout" },
    node("div", {}, panel("当前工单", null, current),
      panel("已保存快照", "每页最多20条；全文与原始来源可离线读回。", entries, pageNote,
        row(previous, next, button("重新读取列表", () => { pageIndex = 0; loadHistory(); })))),
    detail,
  );
  const active = () => view.isConnected && app.project === project.id;
  const selected = (sequence) => active() && sequence === detailSequence;

  function content(observed, label, record, ...extra) {
    const issue = observed.issue;
    return panel(label, null,
      node("h3", {}, issue.title),
      table(["来源", "值"], [
        ["平台／命名空间", `${observed.source.provider} · ${observed.source.project}`],
        ["API 地址", observed.source.api_url],
        ["工单 number／iid", observed.source.issue_id],
        ["原生 ID", issue.native_id],
        ["工单状态", issue.state],
        ["原更新时间", issue.updated_at],
        ["来源项目修订", observed.project.revision],
        ["响应 SHA256", observed.response.sha256],
      ]),
      ...extra,
      node("h3", {}, "完整正文"), pre(issue.body),
      node("details", {}, node("summary", {}, "完整来源记录"), pre(record)),
    );
  }

  function showSnapshot(saved) {
    detail.replaceChildren(content(saved.payload.observation, "已保存快照", saved,
      table(["保存事实", "值"], [
        ["快照 SHA256", saved.sha256], ["首次保存时间", saved.first_observed_at],
      ]),
      node("p", { className: "form-note" }, "这是保存时的来源，不代表当前平台内容或当前工具绑定。"),
      row(button("以此快照准备正式任务", () => { if (active()) openSourceTask(saved.sha256); })),
    ));
  }

  function showObservation(observed) {
    const save = button("重新读取并保存快照", async () => {
      const sequence = ++detailSequence;
      const historySequence = pageSequence;
      save.disabled = true;
      save.textContent = "正在保存…";
      try {
        const result = await api(`${base}/issues/${encodeURIComponent(observed.source.issue_id)}/snapshots`,
          { revision: project.revision });
        if (!active()) return;
        if (selected(sequence)) showSnapshot(result.snapshot);
        if (pageSequence === historySequence) {
          pageIndex = 0;
          loadHistory();
        }
      } catch (error) {
        if (selected(sequence)) detail.replaceChildren(panel("保存结果未确认", error.message,
          node("p", {}, "重新读取历史列表核对保存结果；项目修订变化时，先刷新项目再操作。")));
      } finally {
        save.disabled = false;
        save.textContent = "重新读取并保存快照";
      }
    }, "primary");
    detail.replaceChildren(content(observed, "本次当前读取", observed,
      node("p", {}, `读取时间：${observed.observed_at}`), row(save),
      node("p", { className: "form-note" }, "保存会再次读取平台内容；首次读取与保存结果可能不同。"),
    ));
  }

  async function inspect(digest) {
    const sequence = ++detailSequence;
    detail.replaceChildren(empty("正在读取已保存快照…"));
    try {
      const saved = await api(`${base}/issue-snapshots/${encodeURIComponent(digest)}`);
      if (selected(sequence)) showSnapshot(saved);
    } catch (error) {
      if (selected(sequence)) detail.replaceChildren(panel("未取得快照", error.message));
    }
  }

  async function loadHistory() {
    const sequence = ++pageSequence;
    previous.disabled = next.disabled = true;
    entries.replaceChildren(empty("正在读取历史…"));
    const parameters = new URLSearchParams({ limit: "20" });
    if (cursors[pageIndex]) parameters.set("after", cursors[pageIndex]);
    try {
      const result = await api(`${base}/issue-snapshots?${parameters}`);
      if (!active() || sequence !== pageSequence) return;
      page = result;
      entries.replaceChildren(table(["工单快照"], result.snapshots.map((item) => [
        node("div", { className: "task-choice" },
          node("strong", {}, `${item.source.issue_id} · ${item.title_preview}${item.title_truncated ? "…" : ""}`),
          node("p", { className: "form-note" }, `${item.source.provider} · ${item.source.project}`),
          node("p", { className: "form-note" }, item.first_observed_at),
          button("查看快照", () => inspect(item.sha256))),
      ])));
      pageNote.textContent = `第 ${pageIndex + 1} 页 · ${result.snapshots.length} 条`;
      previous.disabled = pageIndex === 0;
      next.disabled = !result.next_cursor;
    } catch (error) {
      if (!active() || sequence !== pageSequence) return;
      entries.replaceChildren(empty(error.message));
      pageNote.textContent = "历史未读取成功，可重试或返回上一页。";
      previous.disabled = pageIndex === 0;
    }
  }

  loadHistory();
  return [title, view];
}
