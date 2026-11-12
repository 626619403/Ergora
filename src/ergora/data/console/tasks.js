import { api } from "./api.js";
import {
  $, node, button, pre, heading, panel, empty, row, field, select, badge, form, modal, table, download,
} from "./ui.js";
import { app, stages } from "./state.js";
import { taskComposition } from "./task-composition.js";
import { candidateObservation } from "./candidate-observation.js";
import { candidateReview } from "./candidate-review.js";

const stageForPhase = {
  INVENTORY: "inventory", PLANNING: "plan", IMPLEMENTING: "work",
  INTEGRATING: "integrate", VERIFYING: "verify", REVIEWING: "review",
};
const disclosure = (title, value) =>
  node("details", {}, node("summary", {}, title), pre(value));
const facts = (items) =>
  node("dl", { className: "task-facts" }, items.map(([name, value]) => [
    node("dt", {}, name), node("dd", {}, value ?? "未返回"),
  ]));

export function tasksView(data, base, { sourceSnapshot = "" } = {}) {
  const actions = row(button("按 SHA 读取 PR／MR 关联", () =>
    candidateReview({ base, isCurrent: () => title.isConnected })));
  const title = heading("正式任务", "查看冻结合同、原运行和候选结果。工作流设计中的草稿另行保存。", actions);
  if (data.project.registration?.status !== "published")
    return [title, panel("先完成项目登记", "正式任务需要统一注册的执行目录、模板和可信检查。按仓库docs/PROJECTS.md准备项目定义，通过CLI发布或恢复登记后刷新页面。",
      pre(`ergora project register project.json --revision ${data.project.revision}\nergora project registration ${data.project.id}`))];

  const selectionKey = `ergora-task:${data.project.id}`;
  let selected = sessionStorage.getItem(selectionKey) || "";
  let listSequence = 0;
  let detailSequence = 0;
  let pageIndex = 0;
  const cursors = [null];
  let page;
  const entries = node("div", { "aria-live": "polite" });
  const pageNote = node("p", { className: "form-note" });
  const detail = node("div", { className: "task-detail", "aria-live": "polite" }, empty("选择一个任务查看合同。"));
  const previous = button("上一页", () => { pageIndex--; loadPage(); });
  const next = button("下一页", () => {
    cursors[++pageIndex] = page.next_after;
    loadPage();
  });
  const view = node("div", { className: "task-layout" },
    panel("任务合同", "每页最多扫描20条记录；运行状态需单独查询。", entries, pageNote,
      row(previous, next, button("重新读取列表", () => { pageIndex = 0; loadPage(); }))),
    detail,
  );
  actions.prepend(
    button(sourceSnapshot ? "从所选快照预览与创建" : "预览与创建", () => creationDialog(sourceSnapshot), "primary"),
    button("按 ID 读取创建记录", () => creationLookup()),
  );

  function selectPublished(record) {
    if (record.status !== "published") return;
    inspect(record.task_id);
    pageIndex = 0;
    loadPage();
  }

  function creationRecord(record, target, active) {
    const descriptions = {
      not_recorded: "没有统一创建记录；目录存在也不能证明创建成功，旧任务不由恢复入口接管。",
      pending: "原意图已保存，合同尚未完整发布。恢复将沿用原冻结内容和角色。",
      published: "冻结合同已完整发布；创建操作没有提交运行。",
      conflict: "现有合同与原意图冲突。请检查原文件；页面不会覆盖冲突内容。",
    };
    target.replaceChildren(panel(`创建记录：${record.status}`, descriptions[record.status],
      facts([
        ["任务 ID", record.task_id], ["项目当前修订", record.project_revision],
        ["原创建修订", record.created_revision], ["原意图 SHA256", record.intent_sha256],
        ["编译结果 SHA256", record.compiled_sha256],
      ]),
      disclosure("完整创建记录与冻结角色", record),
      record.status === "pending" ? form([], "确认恢复原创建", async () => {
        if (!active()) return;
        let resumed;
        try {
          resumed = await api(`${base}/tasks/${encodeURIComponent(record.task_id)}/resume-create`, {
            revision: record.project_revision, intent_sha256: record.intent_sha256,
          });
        } catch (error) {
          if (active()) creationUnknown(record.task_id, error, target, active);
          return;
        }
        if (!active()) return;
        creationRecord(resumed, target, active);
        selectPublished(resumed);
      }) : null,
      row(
        button("重新读取原创建记录", () => {
          if (active()) creationLookup(record.task_id);
        }),
        record.status === "published" ? button("查看正式任务", () => {
          if (!active()) return;
          $("#dialog").close();
          inspect(record.task_id);
        }) : null,
      ),
    ));
  }

  function creationUnknown(taskId, error, target, active) {
    target.replaceChildren(panel("操作结果尚未确认", error.message,
      node("p", {}, `请保留原任务 ID：${taskId}。先读取原创建记录，再决定是否恢复；不要据此更换 ID 或重发创建。`),
      button("按原 ID 读取创建记录", () => {
        if (active()) creationLookup(taskId);
      }),
    ));
  }

  function creationLookup(taskId = "") {
    let sequence = 0;
    const result = node("div", { "aria-live": "polite" });
    const idField = field("原任务 ID", "task_id", taskId, "text", {
      required: true, maxlength: 80, autocomplete: "off", readonly: taskId ? true : null,
    });
    const content = node("div", {},
      node("p", {}, "未完整发布的任务可能不在列表中。此入口只读创建记录，不查询或启动执行。"),
      form([idField], "读取创建记录", async (values) => {
        if (!active()) return;
        const reading = ++sequence;
        result.replaceChildren(empty("正在读取原创建记录…"));
        try {
          const record = await api(`${base}/tasks/${encodeURIComponent(values.get("task_id"))}/creation`);
          if (current(reading)) creationRecord(record, result, () => current(reading));
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("创建记录读取失败", error.message));
        }
      }), result,
    );
    const active = () => view.isConnected && content.isConnected && $("#dialog").open;
    const current = (reading) => active() && reading === sequence;
    idField.addEventListener("input", () => { sequence++; result.replaceChildren(); });
    modal("按原 ID 读取与恢复创建", content);
  }

  function creationDialog(initialSource = "") {
    const kinds = data.project.registration.definition.templates.filter((kind) =>
      ["repository-governance", "large-change"].includes(kind));
    if (!kinds.length) {
      modal("没有已登记的开发模板", node("p", {}, "此项目使用独立训练合同；请使用工作流设计中的训练优化入口。"));
      return;
    }
    const kind = select(kinds, kinds[0], "task_type");
    const draft = select([
      ["", "选择已保存草稿…"],
      ...data.drafts.filter((item) => kinds.includes(item.kind)).map((item) =>
        [item.id, `${item.id} · ${item.kind} · r${item.revision}`]),
    ], "", "saved_draft");
    const inputField = field("完整任务输入 JSON", "input", "", "textarea", {
      required: true, className: "workflow-json", spellcheck: "false",
    });
    const input = inputField.querySelector("textarea");
    const issueField = field("工单编号 / IID（正整数）", "issue_id", "", "text", { required: true, maxlength: 160 });
    const issueId = issueField.querySelector("input");
    const sourceField = field("来源快照 SHA256（可选）", "source_snapshot_sha256", initialSource, "text", {
      maxlength: 64, autocomplete: "off", spellcheck: "false",
    });
    const sourceSha = sourceField.querySelector("input");
    const sourceResult = node("div", { "aria-live": "polite" });
    let savedSource = null;
    let sourceSequence = 0;
    const result = node("div", { "aria-live": "polite" });
    let sequence = 0;
    let creationLocked = false;
    const compositionEditor = taskComposition({
      tools: app.bootstrap.tools, projectId: data.project.id,
      input: () => JSON.parse(input.value), active: () => active(), invalidate,
    });
    const fields = node("fieldset", { className: "task-creation-fields" },
      node("label", {}, "已登记开发模板", kind),
      row(button("载入所选模板", loadTemplate), node("label", {}, "从草稿载入输入", draft)),
      field("新任务 ID", "task_id", "", "text", { required: true, maxlength: 80, autocomplete: "off" }),
      sourceField,
      row(button("读取来源快照", loadSource), button("清除来源选择", () => {
        sourceSha.value = "";
        resetSource();
        invalidate();
      })),
      node("p", { className: "form-note" }, "来源仅提供上下文；读取后固定工单编号。须选择完整执行与审查组合；预览与创建不会启动任务或回写工单。"),
      sourceResult,
      issueField,
      field("起始提交 SHA（可选，留空使用登记基线）", "starting_sha", "", "text", { maxlength: 40 }),
      inputField,
      compositionEditor.element,
    );
    const editor = form([fields], "预览冻结合同", async (values) => {
      if (!active() || creationLocked) return;
      const reading = ++sequence;
      result.replaceChildren(empty("正在编译预览…"));
      let snapshot;
      try {
        const definition = {
          schema_version: 1, task_id: values.get("task_id"), task_type: values.get("task_type"),
          issue_id: values.get("issue_id"), input: JSON.parse(values.get("input")),
        };
        const composition = compositionEditor.read();
        if (composition) Object.assign(definition, { schema_version: 2, composition });
        if (sourceSha.value.trim()) {
          if (savedSource?.sha256 !== sourceSha.value.trim()) throw new Error("请先读取当前 SHA256 对应的来源快照。");
          if (!composition?.execution) throw new Error("来源任务须选择完整 manifest 的组合执行与审查，并分配工作单元。");
          Object.assign(definition, { schema_version: 3, source: { snapshot_sha256: savedSource.sha256 } });
        }
        if (values.get("starting_sha")) definition.starting_sha = values.get("starting_sha");
        snapshot = await api(`${base}/tasks/preview`, { definition, revision: data.project.revision });
      } catch (error) {
        if (current(reading)) result.replaceChildren(panel("预览失败", error.message));
        return;
      }
      if (!current(reading)) return;
      const bindings = snapshot.files["agent-bindings.json"];
      const frozen = snapshot.files["task.spec.json"].composition;
      result.replaceChildren(panel("审阅冻结预览", "确认后只发布此合同，启动运行另行操作。",
        facts([
          ["项目修订", snapshot.project_revision], ["任务 ID", snapshot.definition.task_id],
          ["模板", snapshot.definition.task_type], ["工单", snapshot.definition.issue_id],
          ["来源快照 SHA256", snapshot.definition.source?.snapshot_sha256 ?? "未选择"],
          ["基线提交", snapshot.files["compiled.json"].spec.request.repository.base_sha],
          ["预览 SHA256", snapshot.preview_sha256],
        ]),
        node("h3", {}, "冻结项目角色"),
        table(["角色", "工具", "模型"], Object.entries(bindings.bindings).map(([role, binding]) =>
          [role, binding.tool, binding.model ?? "未指定"])),
        frozen ? node("div", {}, node("h3", {}, "本任务组合成员"),
          table(["实例", "职能", "工具", "模型", "模式", "选择理由"],
            Object.entries({ ...frozen.execution?.members, ...frozen.members }).map(([path, member]) =>
              [path, member.role, member.binding.tool, member.binding.model ?? "采用工具配置", member.mode, member.backend_reason])),
          disclosure("完整组合后端、信任和差异策略", { review: frozen.members, execution: frozen.execution, diversity: frozen.diversity }),
        ) : null,
        disclosure("完整服务端预览与冻结文件", snapshot),
        form([], "确认创建冻结合同", async () => {
          if (!current(reading) || creationLocked) return;
          creationLocked = true;
          // Keep the original ID across reloads even if the publication reply is lost.
          sessionStorage.setItem(selectionKey, snapshot.definition.task_id);
          fields.disabled = true;
          editor.querySelector('button[type="submit"]').disabled = true;
          result.replaceChildren(empty(`正在创建 ${snapshot.definition.task_id}；请保留此原任务 ID。关闭页面不会撤销已发出的操作。`));
          let record;
          try {
            record = await api(`${base}/tasks`, {
              definition: snapshot.definition, revision: snapshot.project_revision,
              preview_sha256: snapshot.preview_sha256,
            });
          } catch (error) {
            if (current(reading)) creationUnknown(snapshot.definition.task_id, error, result, () => current(reading));
            return;
          }
          if (!current(reading)) return;
          creationRecord(record, result, () => current(reading));
          selectPublished(record);
        }),
      ));
    });
    const content = node("div", {},
      node("p", {}, "载入模板或兼容的已保存草稿，再编辑输入。可保留项目角色，或明确选择已保存的完整组合。修改字段会废弃旧预览；训练优化使用独立入口。"),
      editor, result,
    );
    const active = () => view.isConnected && content.isConnected && $("#dialog").open;
    const current = (reading) => active() && reading === sequence;
    function invalidate() {
      sequence++;
      result.replaceChildren(empty("输入已更改，请重新预览后确认。"));
    }
    function resetSource() {
      sourceSequence++;
      savedSource = null;
      issueId.readOnly = false;
      sourceResult.replaceChildren(empty(sourceSha.value.trim() ? "摘要已更改，请重新读取来源快照。" : "未选择来源快照。"));
    }
    async function loadSource() {
      if (!active() || creationLocked) return;
      resetSource();
      invalidate();
      const reading = sourceSequence;
      const digest = sourceSha.value.trim();
      if (!digest) return;
      sourceResult.replaceChildren(empty("正在读取本地来源快照…"));
      try {
        const saved = await api(`${base}/issue-snapshots/${encodeURIComponent(digest)}`);
        if (!active() || creationLocked || reading !== sourceSequence) return;
        savedSource = saved;
        const observed = saved.payload.observation;
        issueId.value = observed.source.issue_id;
        issueId.readOnly = true;
        invalidate();
        sourceResult.replaceChildren(panel("已选来源上下文", "当前绑定与登记命名空间仍由服务端在预览时重新核对。",
          facts([
            ["快照 SHA256", saved.sha256], ["首次保存时间", saved.first_observed_at],
            ["来源", `${observed.source.provider} · ${observed.source.project} · ${observed.source.issue_id}`],
            ["来源项目修订", observed.project.revision],
          ]), node("h3", {}, observed.issue.title), pre(observed.issue.body),
          disclosure("完整来源快照", saved),
        ));
      } catch (error) {
        if (active() && !creationLocked && reading === sourceSequence)
          sourceResult.replaceChildren(panel("来源快照读取失败", error.message));
      }
    }
    sourceSha.addEventListener("input", resetSource);
    async function loadTemplate() {
      if (!active() || creationLocked) return;
      invalidate();
      const reading = sequence;
      result.replaceChildren(empty("正在读取模板…"));
      try {
        const template = await api(`/api/templates/${encodeURIComponent(kind.value)}`);
        if (!current(reading)) return;
        input.value = JSON.stringify(template.input, null, 2);
        draft.value = "";
        result.replaceChildren(empty("已载入模板输入，请填写任务标识并审阅。"));
      } catch (error) {
        if (current(reading)) result.replaceChildren(panel("模板读取失败", error.message));
      }
    }
    kind.addEventListener("change", () => { draft.value = ""; input.value = ""; });
    draft.addEventListener("change", () => {
      const saved = data.drafts.find((item) => item.id === draft.value);
      if (!saved) return;
      kind.value = saved.kind;
      input.value = JSON.stringify(saved.input, null, 2);
    });
    editor.addEventListener("input", invalidate);
    editor.addEventListener("change", invalidate);
    modal("预览与创建正式任务", content);
  }

  function renderPage() {
    previous.disabled = pageIndex === 0;
    next.disabled = !page?.next_after;
    if (!page) return;
    pageNote.textContent = `第${pageIndex + 1}页 · 本页匹配${page.items.length}项，扫描${page.inspected_entries}条记录`;
    entries.replaceChildren(...[
      ...(page.items.length ? page.items.map((item) =>
        node("article", { className: "list-item" },
          button(item.task_id, () => inspect(item.task_id), "text-button task-choice", {
            "aria-current": item.task_id === selected ? "true" : null,
          }),
          node("small", { className: "muted" }, item.task_type),
          node("p", {}, item.goal),
        ),
      ) : [empty(page.next_after ? "本页没有匹配任务，可继续下一页。" : "本页没有匹配任务。")]),
      page.unreadable_count || page.errors.length
        ? disclosure(`读取异常：${page.unreadable_count}条无法读取，${page.errors.length}条合同无效`, page.errors)
        : null,
    ].filter(Boolean));
  }

  async function loadPage() {
    const sequence = ++listSequence;
    const query = new URLSearchParams({ limit: "20" });
    if (cursors[pageIndex]) query.set("after", cursors[pageIndex]);
    page = null;
    previous.disabled = true;
    next.disabled = true;
    pageNote.textContent = "";
    entries.replaceChildren(empty("正在读取任务合同…"));
    let result;
    try {
      result = await api(`${base}/tasks?${query}`);
    } catch (error) {
      if (view.isConnected && sequence === listSequence) {
        entries.replaceChildren(panel("任务列表读取失败", error.message));
        previous.disabled = pageIndex === 0;
      }
      return;
    }
    if (!view.isConnected || sequence !== listSequence) return;
    page = result;
    renderPage();
    if (!selected && page.items.length) inspect(page.items[0].task_id);
  }

  async function inspect(taskId) {
    const sequence = ++detailSequence;
    selected = taskId;
    sessionStorage.setItem(selectionKey, taskId);
    renderPage();
    detail.replaceChildren(empty(`正在读取 ${taskId}…`));
    const path = `${base}/tasks/${encodeURIComponent(taskId)}`;
    const [contract, submission] = await Promise.allSettled([api(path), api(`${path}/submission`)]);
    if (!view.isConnected || sequence !== detailSequence) return;
    if (contract.status === "rejected") {
      detail.replaceChildren(panel("任务合同读取失败", `${taskId} · ${contract.reason.message}`,
        button("按原 ID 读取创建记录", () => creationLookup(taskId)),
        button("重试任务详情", () => inspect(taskId))));
      return;
    }
    const task = contract.value;
    const request = task.spec.request;
    const input = request.input;
    const bindings = task.agent_bindings;
    const saved = submission.status === "fulfilled" ? submission.value : null;
    const runtime = node("div", {}, empty("尚未查询运行状态。查询会读取所登记的Temporal，合同存在不代表已经提交或完成。"));
    const runKey = `ergora-run:${data.project.id}:${taskId}`;
    const runField = field("原 run ID", "run_id", sessionStorage.getItem(runKey) || saved?.run_id || "", "text", {
      required: true, maxlength: 128, autocomplete: "off",
    });
    const runInput = runField.querySelector("input");
    let runSequence = 0;
    runInput.addEventListener("input", () => {
      runSequence++;
      runtime.replaceChildren(empty("run ID已更改，请重新查询。"));
    });

    function jobDialog(runId, eventId, selectedRunSequence) {
      if (!view.isConnected || sequence !== detailSequence || selectedRunSequence !== runSequence) return;
      let record = null;
      let busy = false;
      let artifactSequence = 0;
      let offset = 0;
      let finished = false;
      let failed = false;
      const description = node("div", {});
      const message = node("div", { "aria-live": "polite" });
      const choice = node("div", {});
      const textWindow = node("div", {});
      const artifact = select([["", "选择原回执中的材料…"]], "", "artifact");
      const indexButton = button("重新读取原job回执", readIndex);
      const readButton = button("读取所选材料第一段", readWindow);
      readButton.disabled = true;
      const content = node("div", {},
        facts([["任务 ID", taskId], ["原 run ID", runId], ["原调度事件 ID", eventId]]),
        node("p", {}, "只读原job发布的回执与文本材料。published或SUCCEEDED不表示工作流已采用、任务成功或外部已清理；这些事实需另核原运行和候选证据。"),
        row(indexButton), description, choice, message, textWindow,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        selectedRunSequence === runSequence && content.isConnected && $("#dialog").open;
      const updateButton = () => {
        readButton.disabled = busy || !artifact.value || finished;
        readButton.textContent = busy ? "正在读取材料…" : failed ? "重试原位置"
          : finished ? "已读至材料末尾" : offset ? "读取下一段材料" : "读取所选材料第一段";
      };
      artifact.addEventListener("change", () => {
        artifactSequence++;
        offset = 0;
        finished = false;
        failed = false;
        textWindow.replaceChildren();
        message.replaceChildren(empty("已切换材料；明确读取后才会请求文本。"));
        updateButton();
      });

      async function readIndex() {
        if (!active() || busy) return;
        busy = true;
        indexButton.disabled = true;
        message.replaceChildren(empty("正在读取原job回执…"));
        try {
          const query = new URLSearchParams({ run_id: runId, timeout: "20" });
          const observed = await api(`${path}/jobs/${eventId}?${query}`);
          if (!active()) return;
          if (observed.runtime_status === "not_found") {
            message.replaceChildren(panel("原运行历史未知", "未找到当前原run；不能据此判断job没有执行。"));
            return;
          }
          description.replaceChildren(facts([
            ["原 job ID", observed.job_id], ["阶段", observed.stage], ["job SHA256", observed.job_sha256],
            ["发布回执", observed.receipt_status], ["回执 SHA256", observed.receipt_sha256],
            ["候选提交", observed.receipt?.candidate_sha], ["回执状态", observed.receipt?.state],
          ]));
          if (observed.receipt_status === "missing") {
            message.replaceChildren(empty("尚无可验证的已发布回执，稍后可手动重新读取。"));
            return;
          }
          record = observed;
          indexButton.hidden = true;
          artifact.replaceChildren(node("option", { value: "" }, "选择原回执中的材料…"),
            ...record.receipt.artifacts.map((item) => node("option", { value: item.name }, item.name)));
          artifact.value = "";
          choice.replaceChildren(node("label", {}, "原job文本材料", artifact), row(readButton),
            node("p", { className: "form-note" }, "每次最多8192个Unicode字符，只保留当前窗口。固定本次回执SHA；回执或产物变化时停止，关闭重开可重新核目录。"),
            disclosure("完整原job回执", record.receipt));
          message.replaceChildren(empty("已读取原回执。选择材料后明确读取第一段。"));
        } catch (error) {
          if (active()) message.replaceChildren(panel("job回执读取失败", error.message));
        } finally {
          busy = false;
          if (active()) indexButton.disabled = false;
        }
      }

      async function readWindow() {
        if (!active() || busy || finished || !artifact.value) return;
        const reading = artifactSequence;
        const name = artifact.value;
        busy = true;
        updateButton();
        message.replaceChildren(empty("正在核对原回执并读取材料窗口…"));
        const current = () => active() && reading === artifactSequence;
        try {
          const query = new URLSearchParams({ run_id: runId, artifact: name,
            receipt_sha256: record.receipt_sha256, offset: String(offset), limit: "8192", timeout: "20" });
          const observed = await api(`${path}/jobs/${eventId}?${query}`);
          if (!current()) return;
          if (observed.runtime_status === "not_found") {
            message.replaceChildren(panel("原运行历史未知", "当前窗口只代表先前观察；原位置保留，可明确重试。"));
            failed = true;
            return;
          }
          const value = observed.artifact;
          textWindow.replaceChildren(facts([
            ["材料", value.name], ["完整产物 SHA256", value.sha256], ["完整产物字节数", value.bytes],
            ["完整文本字符数", value.characters], ["本窗起始字符", value.offset], ["下一字符位置", value.next_offset],
          ]), pre(value.text));
          finished = value.next_offset === null;
          offset = value.next_offset ?? offset;
          failed = false;
          message.replaceChildren(empty(finished ? "已读至此材料末尾。" : "这是原文本的一个窗口，可手动读取下一段。"));
        } catch (error) {
          if (current()) {
            failed = true;
            message.replaceChildren(panel("材料读取失败", error.message,
              node("p", {}, "已读窗口和原位置保留；可明确重试，回执变化时请关闭并重新核目录。")));
          }
        } finally {
          busy = false;
          if (active()) updateButton();
        }
      }

      modal("原job回执与文本证据", content);
      readIndex();
    }


    function evidenceDialog(runId, selectedRunSequence) {
      if (!view.isConnected || sequence !== detailSequence || selectedRunSequence !== runSequence) return;
      let busy = false;
      const message = node("div", { "aria-live": "polite" });
      const observation = node("div", {});
      const collected = node("div", {});
      const readButton = button("读取证据索引", readIndex);
      const collectButton = button("收集并下载交接包", collect);
      const content = node("div", {},
        facts([["任务 ID", taskId], ["原 run ID", runId]]),
        node("p", {}, "按需读取原闭合运行。打开此窗口不会收集材料；索引与下载分别操作，无需先读取索引。材料校验、原结果、候选审查和外部清理各自独立。"),
        row(readButton, collectButton), message, collected, observation,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        selectedRunSequence === runSequence && content.isConnected && $("#dialog").open;
      const setBusy = (value) => {
        busy = value;
        readButton.disabled = value;
        collectButton.disabled = value;
      };

      function showIndex(index) {
        const usage = index.usage;
        const budget = index.budget;
        const span = usage.workflow_span;
        let page = 0;
        const jobs = node("div", {});
        const pageNote = node("p", { className: "form-note" });
        const previous = button("上一页原job", () => { page--; showJobs(); });
        const next = button("下一页原job", () => { page++; showJobs(); });
        function showJobs() {
          jobs.replaceChildren(table(["阶段 / 原job", "请求", "回执", "原结果引用", "材料"],
            index.jobs.slice(page * 20, (page + 1) * 20).map((job) => [
              node("div", {}, node("p", {}, job.stage), node("p", {}, job.job_id),
                button("原job回执与材料", () => {
                  if (active()) jobDialog(runId, job.history_event_ids[0], selectedRunSequence);
                })),
              job.request_state, job.receipt_state, job.outcome_reference_state,
              job.receipt?.artifacts.length ?? "无可验证回执",
            ])));
          pageNote.textContent = `第 ${page + 1} 页 · 共 ${index.jobs.length} 个原job · 每页最多20项`;
          previous.disabled = page === 0;
          next.disabled = (page + 1) * 20 >= index.jobs.length;
        }
        showJobs();
        observation.replaceChildren(
          panel("原结果与材料观察", "verified只表示当前发布材料完整且摘要可核；SUCCEEDED回执不等于原workflow采用，matches表示该回执与原outcome引用一致。外部清理需另核原对账。",
            facts([
              ["原服务状态", index.temporal_status], ["原业务结果", index.original_outcome?.status ?? "未记录业务结果"],
              ["候选提交", index.original_outcome?.candidate_sha], ["发布材料完整性", index.published_evidence],
              ["未决job数量", index.unresolved_jobs.length], ["额外job数量", index.unexpected_jobs.length],
              ["外部协议证据确认", index.external_confirmed ? "已确认" : "未确认"],
              ["本次读取释放租约", String(index.lease_released_by_operation)],
              ["执行成功推断", index.execution_success === null ? "未知（未推断）" : String(index.execution_success)],
              ["原请求 SHA256", index.request_sha256], ["原profile SHA256", index.profile_sha256],
              ["原history jobs SHA256", index.history_jobs_sha256], ["原结果 SHA256", index.original_outcome_sha256],
            ]), disclosure("完整原结果", index.original_outcome)),
          panel("冻结预算", "这些是工作流准入与等待策略，不是外部进程运行时间、模型调用或费用的硬上限。",
            facts([
              ["来源", budget.source], ["适用范围", budget.scope],
              ["最大工作单元数", budget.limits.max_work_units], ["最大并行单元数", budget.limits.max_parallel_units],
              ["阶段等待上限（秒）", budget.stage_timeout_seconds], ["批准等待上限（秒）", budget.approval_timeout_seconds],
              ["轮询间隔（秒）", budget.poll_seconds],
            ])),
          panel("原history用量事实", "调度事件、活动start及独立job不是模型调用次数，也不能作为重试或计费量。服务跨度包含等待、并发及调度时间。",
            facts([
              ["计数来源", usage.source], ["history事件数", usage.events],
              ["活动调度数", usage.scheduled_activities], ["已记录活动start数", usage.recorded_activity_starts],
              ["信号事件数", usage.signal_events], ["dev_submit调度数", usage.dev_submit_events],
              ["独立job数", usage.unique_jobs], ["合同工作单元数", usage.configured_work_units],
              ["跨度状态", span.state], ["跨度来源", span.source],
              ["起始事件 / 时间", `${span.start_event_id} / ${span.started_at ?? "未记录"}`],
              ["闭合事件 / 时间", `${span.close_event_id} / ${span.closed_at ?? "未记录"}`],
              ["服务history跨度", span.value === null ? "未知" : `${span.value} ${span.unit}`],
            ]),
            table(["用量", "值", "单位", "记录状态", "来源"],
              [["模型调用", usage.model_calls], ["Token", usage.tokens], ["费用", usage.cost]].map(([name, metric]) =>
                [name, metric.value ?? "未知", metric.currency ?? metric.unit, metric.state, metric.source ?? "未记录"])),
            disclosure("冻结预算与完整用量来源", { budget, usage })),
          panel("原上下文关联", "未记录的评价、Skill、记忆或来源采用不会用当前项目配置补写。",
            facts(Object.entries(index.context_snapshots).map(([name, value]) => [name, value.state]))),
          panel("原job与回执", "只显示本页目录。明确打开原job后才读取回执；选择材料后仍需点击读取文本窗口。",
            jobs, pageNote, row(previous, next)),
          disclosure("完整只读索引与冻结合同", index),
        );
      }

      async function readIndex() {
        if (!active() || busy) return;
        setBusy(true);
        message.replaceChildren(empty("正在读取并核对原证据索引…"));
        try {
          const query = new URLSearchParams({ run_id: runId, timeout: "20" });
          const index = await api(`${path}/evidence?${query}`);
          if (!active()) return;
          showIndex(index);
          message.replaceChildren(empty("索引读取完成。这是本次只读观察，材料正文尚未读取。"));
          readButton.textContent = "重新读取证据索引";
        } catch (error) {
          if (active()) message.replaceChildren(panel("证据索引读取失败", error.message,
            node("p", {}, "先前观察如有则保留，不能视为本次已核。可明确重新读取。")));
        } finally {
          setBusy(false);
        }
      }

      async function collect() {
        if (!active() || busy) return;
        setBusy(true);
        message.replaceChildren(empty("正在收集原回执引用的材料；关闭或切换窗口后不交付迟到下载…"));
        try {
          const packet = await api(`${path}/handoff`, { run_id: runId, timeout: 20 }, "POST", async (response) => {
            const bytes = await response.arrayBuffer();
            const digest = await crypto.subtle.digest("SHA-256", bytes);
            const sha256 = Array.from(new Uint8Array(digest), (value) => value.toString(16).padStart(2, "0")).join("");
            if (sha256 !== response.headers.get("X-Ergora-Handoff-SHA256"))
              throw new Error("交接包响应摘要不匹配；未触发下载。请重新收集并独立核对来源。");
            return { bytes, sha256 };
          });
          if (!active()) return;
          download("ergora-handoff.zip", packet.bytes, "application/zip");
          collected.replaceChildren(panel("已交给浏览器下载", "请在浏览器确认保存位置；此处不证明文件已落盘。摘要只核本次响应字节，不认证来源，不推断执行成功，也不改变原取消结果。",
            facts([["整包 SHA256", packet.sha256], ["响应字节数", packet.bytes.byteLength]]),
            pre(`ergora handoff verify ergora-handoff.zip --sha256 ${packet.sha256}`)));
          message.replaceChildren(empty("已核响应字节摘要；可在独立环境使用上方命令离线核包。"));
        } catch (error) {
          if (active()) message.replaceChildren(panel("交接包下载失败", error.message,
            node("p", {}, "本次未触发下载。关闭窗口不会取消服务器已发出的收集请求，重新操作需明确点击。")));
        } finally {
          setBusy(false);
        }
      }

      modal("证据、预算与交接", content);
    }

    function eventsDialog(runId, selectedRunSequence) {
      if (!view.isConnected || sequence !== detailSequence || selectedRunSequence !== runSequence) return;
      let after = null;
      let busy = false;
      let finished = false;
      let received = 0;
      let displayed = [];
      const message = node("div", { "aria-live": "polite" });
      const summary = node("p", { className: "form-note" });
      const entries = node("div", {});
      const readButton = button("读取第一批事件", read);
      const content = node("div", {},
        facts([["任务 ID", taskId], ["原 run ID", runId]]),
        node("p", {}, "每次最多读取20条，保留最近200条显示记录。关联字段超长时显示前256字符与省略号。执行结果由原运行结果与候选证据确认。"),
        row(readButton), message, summary, entries,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        selectedRunSequence === runSequence && content.isConnected && $("#dialog").open;

      async function read() {
        if (!active() || busy || finished) return;
        busy = true;
        readButton.disabled = true;
        readButton.textContent = "正在读取事件…";
        message.replaceChildren(empty("正在读取原运行的当前事件片段…"));
        const query = new URLSearchParams({ run_id: runId, limit: "20", timeout: "20" });
        if (after !== null) query.set("after", after);
        try {
          const page = await api(`${path}/events?${query}`);
          if (!active()) return;
          if (page.runtime_status === "not_found") {
            message.replaceChildren(panel("未找到原运行", "当前事件历史未知；已显示的片段仅代表先前观察。请核对原run与提交回执。"));
            readButton.textContent = "重新读取原运行事件";
            return;
          }
          const clip = (value) => {
            let prefix = "";
            let length = 0;
            for (const character of value) {
              if (length++ === 256) return prefix + "…";
              prefix += character;
            }
            return value;
          };
          const rows = page.events.map((event) => [
            event.event_id, event.type, event.time ?? "未返回",
            [
              event.activity ? `Activity ${clip(event.activity.id)} · ${clip(event.activity.type)}` : null,
              event.scheduled_event_id == null ? null : `对应事件 ${event.scheduled_event_id}`,
              event.signal_name == null ? null : `Signal ${clip(event.signal_name)}`,
            ].filter(Boolean).join("；") || "—",
            event.activity?.type === "dev_submit"
              ? button(`原job证据 · ${event.event_id}`, () => jobDialog(runId, event.event_id, selectedRunSequence)) : "—",
          ]);
          received += rows.length;
          displayed = displayed.concat(rows).slice(-200);
          after = page.next_after;
          finished = after === null;
          summary.textContent = `累计读取 ${received} 条，显示最近 ${displayed.length} 条。重新打开后从原运行第一批读取。`;
          entries.replaceChildren(displayed.length
            ? table(["事件 ID", "类型", "时间（UTC）", "关联", "Job 证据"], displayed)
            : empty("当前没有新增事件。"));
          message.replaceChildren(
            facts([["本轮 Temporal 状态", page.temporal_status], ["原运行已闭合", page.terminal ? "是" : "否"]]),
            empty(page.at_current_end
              ? page.terminal ? "已读至原运行闭合后的尾部。" : "已读至本次可见尾部，稍后可手动读取新增事件。"
              : "还有未读事件，可继续读取下一批。"),
          );
          readButton.textContent = finished ? "已读至闭合尾部"
            : page.at_current_end ? "读取新增事件" : "读取下一批事件";
        } catch (error) {
          if (active()) {
            message.replaceChildren(panel("事件读取失败", error.message,
              node("p", {}, "已读片段和原位置保留；可明确重试本批事件。")));
            readButton.textContent = "重试原位置";
          }
        } finally {
          busy = false;
          if (active()) readButton.disabled = finished;
        }
      }

      modal("原运行事件", content);
      read();
    }

    async function approvalDialog(pending = null, selectedRunSequence = null) {
      if (!view.isConnected || sequence !== detailSequence ||
          pending && selectedRunSequence !== runSequence) return;
      const decisionKey = `ergora-decision:${data.project.id}:${taskId}`;
      const decisionField = field("决策 ID（用于恢复）", "decision_id",
        sessionStorage.getItem(decisionKey) || "", "text", {
          required: true, maxlength: 80, autocomplete: "off", disabled: Boolean(pending),
        });
      const decisionInput = decisionField.querySelector("input");
      const materials = node("div", {}, pending ? empty("正在读取完整计划材料…") : null);
      const result = node("div", { "aria-live": "polite" });
      let plan = null;
      let readingSequence = 0;
      let writing = false;
      const reader = form([decisionField], "读取批准记录", read);
      const readButton = reader.querySelector('button[type="submit"]');
      readButton.disabled = Boolean(pending);
      const content = node("div", {},
        node("p", {}, "请保留本次决策 ID。先读取原记录，再明确批准或恢复；关闭页面不会撤销已发出的操作，未知结果不能直接重发。"),
        materials, reader, result,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        content.isConnected && $("#dialog").open && (!pending || selectedRunSequence === runSequence);
      const current = (reading) => active() && reading === readingSequence;
      decisionInput.addEventListener("input", () => {
        readingSequence++;
        result.replaceChildren(empty("决策 ID已更改，请重新读取原记录。"));
      });

      function show(record, reading, decisionId) {
        const descriptions = {
          not_recorded: "此 ID没有批准记录。完整材料已读后，才能明确批准所选计划。",
          prepared: "原批准意图已保存，尚无信号检查点；明确恢复可能首次投递原决策。",
          unknown: "原投递结果尚未确认。恢复只在原run核对精确信号，不重新发信号。",
          requested: "原信号投递事实已保存；这不代表批准已被采用或六阶段已完成。",
        };
        const canApprove = plan && record.status === "not_recorded";
        const canResume = !plan && ["prepared", "unknown"].includes(record.status);
        const action = canApprove ? "确认批准此计划"
          : record.status === "prepared" ? "确认恢复原批准意图" : "确认核对原批准信号";
        result.replaceChildren(panel(`批准记录：${record.status}`, descriptions[record.status],
          facts([
            ["决策 ID", decisionId], ["项目当前修订", record.project_revision],
            ["原 run ID", record.run_id], ["计划 SHA256", record.plan_sha256 ?? plan?.plan_sha256],
            ["原意图 SHA256", record.intent_sha256], ["Owner回执 ID", record.owner_receipt_id],
            ["回执有效期", record.expires_at ? new Date(record.expires_at * 1000).toLocaleString() : null],
            ["信号投递依据", record.signal_delivery], ["原信号恢复查询", record.reconciliation],
          ]),
          disclosure("完整原批准记录", record),
          plan && record.status !== "not_recorded"
            ? node("p", {}, "该 ID已有原决策。请单独查看原记录，不以当前显示的材料覆盖它。") : null,
          canApprove || canResume ? form([], action, async () => {
            if (!current(reading) || writing) return;
            writing = true;
            decisionInput.readOnly = true;
            readButton.disabled = true;
            sessionStorage.setItem(decisionKey, decisionId);
            result.replaceChildren(empty(`正在处理原决策 ${decisionId}；请保留该 ID，回复未知时先读取原记录。`));
            try {
              const observed = await api(`${path}/approvals/${encodeURIComponent(decisionId)}${canApprove ? "" : "/resume"}`, {
                revision: record.project_revision, confirm: true, timeout: 20,
                ...(canApprove ? { run_id: plan.run_id, plan_sha256: plan.plan_sha256 }
                  : { intent_sha256: record.intent_sha256 }),
              });
              if (current(reading)) show(observed, reading, decisionId);
            } catch (error) {
              if (current(reading)) result.replaceChildren(panel("批准结果尚未确认", error.message,
                node("p", {}, `原决策 ID：${decisionId}。先读原记录，再决定是否恢复；不要改用新 ID绕过未知结果。`),
                button("重新读取原批准记录", read),
              ));
            } finally {
              writing = false;
              if (active()) {
                decisionInput.readOnly = false;
                readButton.disabled = false;
              }
            }
          }) : null,
          row(
            button("重新读取原批准记录", read),
            plan && record.status !== "not_recorded"
              ? button("查看原批准记录", () => approvalDialog()) : null,
            record.status === "requested" ? button("返回原任务与运行", () => {
              if (!current(reading)) return;
              sessionStorage.setItem(runKey, record.run_id);
              $("#dialog").close();
              inspect(taskId);
            }) : null,
          ),
        ));
      }

      async function read() {
        if (!active() || writing) return;
        const decisionId = decisionInput.value;
        if (!decisionInput.reportValidity()) return;
        const reading = ++readingSequence;
        sessionStorage.setItem(decisionKey, decisionId);
        result.replaceChildren(empty(`正在读取原决策 ${decisionId}…`));
        try {
          const record = await api(`${path}/approvals/${encodeURIComponent(decisionId)}`);
          if (current(reading)) show(record, reading, decisionId);
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("批准记录读取失败", error.message,
            node("p", {}, `原决策 ID：${decisionId}。记录未读成功，不提供批准或恢复确认。`),
            button("重新读取原批准记录", read),
          ));
        }
      }

      modal(pending ? "审阅计划与批准" : "按原 ID 检查批准记录", content);
      if (pending) {
        try {
          const observed = await api(`${path}/plan?${new URLSearchParams({ ...pending, timeout: "20" })}`);
          if (!active()) return;
          plan = observed;
          materials.replaceChildren(
            panel("待批计划身份", "以下是原运行已接受的完整计划材料。请审阅范围、工作单元、风险和回退措施，再明确决定。",
              facts([["原 run ID", plan.run_id], ["计划 SHA256", plan.plan_sha256],
                ["请求 SHA256", plan.request_sha256], ["Profile SHA256", plan.profile_sha256]]),
              disclosure("完整计划回执与身份", { ...plan, materials: undefined })),
            ...plan.materials.map((material) => panel(material.name, `${material.bytes}字节`,
              facts([["SHA256", material.sha256]]), pre(material.text))),
          );
          decisionInput.disabled = false;
          readButton.disabled = false;
        } catch (error) {
          if (active()) materials.replaceChildren(panel("完整计划材料读取失败", error.message,
            node("p", {}, "未取得完整材料，不能在此批准。请返回查询原运行；已有决策可按原 ID单独读取。"),
            button("按原 ID 检查批准记录", () => approvalDialog()),
          ));
          return;
        }
      }
      if (decisionInput.value) await read();
    }

    async function cancellationDialog(runId = null, selectedRunSequence = null) {
      if (!view.isConnected || sequence !== detailSequence ||
          runId && selectedRunSequence !== runSequence) return;
      const requestKey = `ergora-cancel:${data.project.id}:${taskId}`;
      const requestField = field("取消请求 ID（用于恢复）", "request_id",
        sessionStorage.getItem(requestKey) || "", "text", {
          required: true, maxlength: 80, autocomplete: "off",
        });
      const requestInput = requestField.querySelector("input");
      const result = node("div", { "aria-live": "polite" });
      let readingSequence = 0;
      let writing = false;
      const reader = form([requestField], "读取取消记录", read);
      const readButton = reader.querySelector('button[type="submit"]');
      const content = node("div", {},
        node("p", {}, "取消是协作请求；投递回执不确认运行或外部作业已停止。请保留原请求 ID，先读取原记录，再明确请求或恢复。关闭页面不撤销已发出的操作。"),
        runId ? facts([["本次选择的原 run ID", runId]]) : null,
        reader, result,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        content.isConnected && $("#dialog").open && (!runId || selectedRunSequence === runSequence);
      const current = (reading) => active() && reading === readingSequence;
      requestInput.addEventListener("input", () => {
        readingSequence++;
        result.replaceChildren(empty("取消请求 ID已更改，请重新读取原记录。"));
      });

      function show(record, reading, requestId) {
        const descriptions = {
          not_recorded: "此 ID没有取消记录。从已查询的原运行进入时，可填写原因并明确请求取消。",
          prepared: "原取消意图已保存，尚无信号检查点；明确恢复可能首次投递原请求。",
          unknown: "原投递结果尚未确认。恢复只在原run核对精确信号，不重新发信号。",
          requested: "原取消信号投递事实已保存；运行终态和外部清理仍需分别核对。",
          already_closed: "原运行在发送前已闭合，本次没有投递取消信号。此记录不确认外部作业已清理。",
        };
        const canRequest = runId && record.status === "not_recorded";
        const canResume = ["prepared", "unknown"].includes(record.status);
        const action = canRequest ? "确认请求取消此运行"
          : record.status === "prepared" ? "确认恢复原取消意图" : "确认核对原取消信号";
        result.replaceChildren(panel(`取消记录：${record.status}`, descriptions[record.status],
          facts([
            ["取消请求 ID", requestId], ["项目当前修订", record.project_revision],
            ["原 run ID", record.run_id], ["原取消原因", record.reason],
            ["原意图 SHA256", record.intent_sha256], ["信号投递依据", record.signal_delivery],
            ["原信号恢复查询", record.reconciliation], ["发送时已闭合状态", record.temporal_status],
            ["取消请求投递", record.cancel_requested == null ? "未知" : record.cancel_requested ? "是" : "否"],
            ["取消已确认", record.cancellation_confirmed == null ? "未确认" : record.cancellation_confirmed ? "是" : "否"],
          ]),
          disclosure("完整原取消记录", record),
          canRequest || canResume ? form(canRequest ? [field("取消原因", "reason", "", "textarea", {
            required: true, maxlength: 1000,
          })] : [], action, async (values) => {
            if (!current(reading) || writing) return;
            writing = true;
            requestInput.readOnly = true;
            readButton.disabled = true;
            sessionStorage.setItem(requestKey, requestId);
            result.replaceChildren(empty(`正在处理原取消请求 ${requestId}；回复未知时先读取原记录，关闭页面不取消本次操作。`));
            try {
              const observed = await api(`${path}/cancellations/${encodeURIComponent(requestId)}${canRequest ? "" : "/resume"}`, {
                revision: record.project_revision, confirm: true, timeout: 20,
                ...(canRequest ? { run_id: runId, reason: values.get("reason") }
                  : { intent_sha256: record.intent_sha256 }),
              });
              if (current(reading)) show(observed, reading, requestId);
            } catch (error) {
              if (current(reading)) result.replaceChildren(panel("取消结果尚未确认", error.message,
                node("p", {}, `原请求 ID：${requestId}。先读原记录，再决定是否恢复；不要改用新 ID绕过未知投递。`),
                button("重新读取原取消记录", read),
              ));
            } finally {
              writing = false;
              if (active()) {
                requestInput.readOnly = false;
                readButton.disabled = false;
              }
            }
          }) : null,
          row(
            button("重新读取原取消记录", read),
            ["requested", "already_closed"].includes(record.status) ? button("返回原任务与运行", () => {
              if (!current(reading)) return;
              sessionStorage.setItem(runKey, record.run_id);
              $("#dialog").close();
              inspect(taskId);
            }) : null,
          ),
        ));
      }

      async function read() {
        if (!active() || writing) return;
        const requestId = requestInput.value;
        if (!requestInput.reportValidity()) return;
        const reading = ++readingSequence;
        sessionStorage.setItem(requestKey, requestId);
        result.replaceChildren(empty(`正在读取原取消请求 ${requestId}…`));
        try {
          const record = await api(`${path}/cancellations/${encodeURIComponent(requestId)}`);
          if (current(reading)) show(record, reading, requestId);
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("取消记录读取失败", error.message,
            node("p", {}, `原请求 ID：${requestId}。记录未读成功，不提供请求或恢复确认。`),
            button("重新读取原取消记录", read),
          ));
        }
      }

      modal(runId ? "请求取消原运行" : "按原 ID 检查取消记录", content);
      if (requestInput.value) await read();
    }

    async function reconciliationDialog(runId = null, selectedRunSequence = null) {
      if (!view.isConnected || sequence !== detailSequence ||
          runId && selectedRunSequence !== runSequence) return;
      const observations = node("div", {});
      const result = node("div", { "aria-live": "polite" });
      let readingSequence = 0;
      let writing = false;
      let observation = null;
      const readButton = button(runId ? "重新读取外部证据与原对账记录" : "重新读取原对账记录", read);
      const content = node("div", {},
        node("p", {}, "读取不发布fence或释放租约。明确对账会重验原运行、建立或复用同一fence，只有外部作业全部确认后才释放原工单租约。关闭页面不撤销已发出的操作。"),
        runId ? facts([["本次选择的原 run ID", runId]]) : null,
        row(readButton), observations, result,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        content.isConnected && $("#dialog").open && (!runId || selectedRunSequence === runSequence);
      const current = (reading) => active() && reading === readingSequence;

      function show(record, reading) {
        const descriptions = {
          not_recorded: "尚无原对账意图。从已查询的闭合原运行进入并读到外部证据后，才可明确发起对账。",
          prepared: "原意图已保存，尚无写前检查点。明确恢复将重验同一原运行和claim。",
          unknown: "原对账尚未取得完整清理证据。请保留原意图，取得可信终态回执后再明确恢复。",
          confirmed: "原清理证据已保存，租约释放回执尚未保存。请按原意图明确恢复。",
          reconciled: "原清理证据及租约释放回执已保存。这是历史记录，实时外部状态需另行读取。",
        };
        const canRequest = runId && observation && record.status === "not_recorded";
        const canResume = ["prepared", "unknown", "confirmed"].includes(record.status);
        result.replaceChildren(panel(`对账记录：${record.status}`, descriptions[record.status],
          facts([
            ["项目当前修订", record.project_revision], ["原 run ID", record.run_id],
            ["原意图 SHA256", record.intent_sha256], ["原 Temporal 状态", record.temporal_status],
            ["原结果", record.original_outcome?.status], ["原清理证据 SHA256", record.evidence_sha256],
            ["租约释放依据 SHA256", record.release_evidence_sha256],
            ["原清理证据已确认", record.external_confirmed == null ? "未知" : record.external_confirmed ? "是" : "否"],
            ["原租约已释放", record.lease_released == null ? "未知" : record.lease_released ? "是" : "否"],
            ["开发成功", record.execution_success == null ? "未知" : record.execution_success ? "是" : "否"],
          ]),
          disclosure("完整原对账记录", record),
          canRequest || canResume ? form([], canRequest ? "确认外部对账并释放原租约" : "确认恢复原对账意图", async () => {
            if (!current(reading) || writing) return;
            writing = true;
            readButton.disabled = true;
            observation = null;
            observations.replaceChildren(empty("本次对账可能改变fence或租约；先前观察已失效，实时外部状态需重新明确读取。"));
            result.replaceChildren(empty("正在处理原对账意图；回复未知时先读取原记录，关闭页面不撤销操作。"));
            try {
              const observed = await api(`${path}/${canRequest ? "reconcile" : "resume-reconcile"}`, {
                revision: record.project_revision, confirm: true, timeout: 20,
                ...(canRequest ? { run_id: runId } : { intent_sha256: record.intent_sha256 }),
              });
              if (current(reading)) show(observed, reading);
            } catch (error) {
              if (current(reading)) result.replaceChildren(panel("对账结果尚未确认", error.message,
                node("p", {}, "先读取此原任务的对账记录，再决定是否恢复。没有回复不证明未建立fence或未释放租约。")));
            } finally {
              writing = false;
              if (active()) readButton.disabled = false;
            }
          }) : null,
          button("返回原任务与运行", () => {
            if (!current(reading)) return;
            sessionStorage.setItem(runKey, record.run_id);
            $("#dialog").close();
            inspect(taskId);
          }),
        ));
      }

      async function read() {
        if (!active() || writing) return;
        const reading = ++readingSequence;
        observation = null;
        result.replaceChildren(empty("正在读取原对账记录…"));
        observations.replaceChildren(runId ? empty("正在只读核对原运行的外部证据…") : empty("这里只读本地原记录；实时外部证据请返回查询闭合原run后单独读取。"));
        const [savedRecord, external] = await Promise.allSettled([
          api(`${path}/reconciliation`),
          runId ? api(`${path}/external-status?${new URLSearchParams({ run_id: runId, timeout: "20" })}`) : Promise.resolve(null),
        ]);
        if (!current(reading)) return;
        if (runId) {
          if (external.status === "fulfilled") {
            observation = external.value;
            observations.replaceChildren(panel("本轮只读外部证据", "本次读取没有释放租约，也不改写原workflow结果。",
              facts([
                ["原 run ID", observation.run_id], ["原 Temporal 状态", observation.temporal_status],
                ["原结果", observation.original_outcome?.status], ["History job SHA256", observation.history_jobs_sha256],
                ["当前外部已确认", observation.external_confirmed ? "是" : "否"],
                ["Fence 状态", observation.fence.state], ["Fence SHA256", observation.fence.sha256],
                ["未确认 Job", observation.unresolved_jobs.join("、") || "无"],
                ["原运行外的 Job", observation.unexpected_jobs.join("、") || "无"],
              ]),
              table(["阶段", "Job ID", "请求", "回执", "Job SHA256", "回执 SHA256"], observation.jobs.map((job) => [
                job.stage, job.job_id, job.request_state, job.receipt_state, job.job_sha256, job.receipt_sha256 ?? "未记录",
              ])),
              disclosure("完整本轮外部证据", observation),
            ));
          } else observations.replaceChildren(panel("外部证据读取失败", external.reason.message,
            node("p", {}, "不能在此发起新对账；已有原意图仍可从本地记录查看并明确恢复。")));
        }
        if (savedRecord.status === "fulfilled") show(savedRecord.value, reading);
        else result.replaceChildren(panel("原对账记录读取失败", savedRecord.reason.message,
          node("p", {}, "记录未读成功，不提供对账或恢复确认。")));
      }

      modal(runId ? "外部证据与对账" : "检查原对账记录与恢复", content);
      await read();
    }

    async function exportDialog(candidate = null, selectedRunSequence = null) {
      if (!view.isConnected || sequence !== detailSequence ||
          candidate && selectedRunSequence !== runSequence) return;
      const result = node("div", { "aria-live": "polite" });
      let readingSequence = 0;
      let writing = false;
      const readButton = button("重新读取原导出记录", read);
      const content = node("div", {},
        node("p", {}, "导出将原候选保存到登记仓库的本地分支，不checkout、merge或推送。先读原记录，再明确确认；关闭页面不会撤销已发操作，回复未知时先读原记录。"),
        candidate ? facts([["本次选择的原 run ID", candidate.run_id],
          ["本次选择的精确候选", candidate.candidate_sha]]) : null,
        row(readButton), result,
      );
      const contextActive = () => view.isConnected && sequence === detailSequence &&
        (!candidate || selectedRunSequence === runSequence);
      const active = () => contextActive() && content.isConnected && $("#dialog").open;
      const current = (reading) => active() && reading === readingSequence;

      function show(record, reading) {
        const descriptions = {
          not_recorded: "尚无原导出意图。从已查询的REVIEW_READY原运行进入时，可填写目标分支并明确导出固定候选。",
          prepared: "原导出意图已保存，尚无写前检查点；明确恢复可能首次创建原目标分支。",
          unknown: "原导出结果尚未确认。恢复只核原分支；分支不存在时保持未知，不隐式重新创建。",
          exported: "原导出回执已保存。这是历史事实，不证明当前分支仍指向原候选；维护者仍需复验。",
        };
        const canExport = candidate && record.status === "not_recorded";
        const canResume = ["prepared", "unknown"].includes(record.status);
        const action = canExport ? "确认导出此候选至本地分支"
          : record.status === "prepared" ? "确认恢复原导出意图" : "确认核对原导出分支";
        result.replaceChildren(panel(`导出记录：${record.status}`, descriptions[record.status],
          facts([
            ["项目当前修订", record.project_revision], ["原 run ID", record.run_id],
            ["原意图 SHA256", record.intent_sha256], ["原候选提交", record.candidate_sha],
            ["原目标仓库", record.repo], ["原目标分支", record.branch],
            ["原分支核对", record.reconciliation], ["恢复说明", record.instruction],
            ["原租约已释放", record.lease_released == null ? "未知" : record.lease_released ? "是" : "否"],
            ["已切换工作区", record.checked_out ? "是" : "否"], ["已合并", record.merged ? "是" : "否"],
            ["开发成功", record.execution_success == null ? "未知" : record.execution_success ? "是" : "否"],
          ]),
          disclosure("完整原导出记录", record),
          record.status === "exported" && task.admission_envelope?.schema_version === 7
            ? button("观察当前候选分支", () => {
              if (!current(reading)) return;
              candidateObservation({ base, taskId, record, isCurrent: contextActive });
            }) : null,
          record.status === "exported" && task.admission_envelope?.schema_version === 7
            ? button("关联已有 PR／MR", () => {
              if (!current(reading)) return;
              candidateReview({ base, taskId, record, isCurrent: contextActive });
            }) : null,
          candidate && record.status !== "not_recorded"
            ? node("p", {}, "此任务已有原目标；恢复只沿原意图，不用本次选择覆盖它。") : null,
          canExport || canResume ? form(canExport ? [field("目标本地分支", "branch", "", "text", {
            required: true, maxlength: 1024, autocomplete: "off",
          })] : [], action, async (values) => {
            if (!current(reading) || writing) return;
            writing = true;
            readButton.disabled = true;
            result.replaceChildren(empty("正在处理原候选导出；回复未知时先读取原记录，关闭页面不撤销操作。"));
            try {
              const observed = await api(`${path}/export${canExport ? "" : "/resume"}`, {
                revision: record.project_revision, confirm: true, timeout: 20,
                ...(canExport ? { ...candidate, branch: values.get("branch") }
                  : { intent_sha256: record.intent_sha256 }),
              });
              if (current(reading)) show(observed, reading);
            } catch (error) {
              if (current(reading)) result.replaceChildren(panel("导出结果尚未确认", error.message,
                node("p", {}, "先读取此原任务的导出记录，再决定是否恢复。没有回复不证明未创建分支或未释放租约，请保留原候选和分支。")));
            } finally {
              writing = false;
              if (active()) readButton.disabled = false;
            }
          }) : null,
          button("返回原任务与运行", () => {
            if (!current(reading)) return;
            sessionStorage.setItem(runKey, record.run_id);
            $("#dialog").close();
            inspect(taskId);
          }),
        ));
      }

      async function read() {
        if (!active() || writing) return;
        const reading = ++readingSequence;
        result.replaceChildren(empty("正在读取原导出记录…"));
        try {
          const record = await api(`${path}/export`);
          if (current(reading)) show(record, reading);
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("原导出记录读取失败", error.message,
            node("p", {}, "记录未读成功，不提供导出或恢复确认。")));
        }
      }

      modal(candidate ? "导出精确候选" : "检查原导出记录与恢复", content);
      await read();
    }

    function submissionDialog() {
      let readingSequence = 0;
      const result = node("div", { "aria-live": "polite" });
      const content = node("div", {},
        node("p", {}, "先读取本地创建与提交记录，再明确提交或恢复。关闭页面不会撤销已经发出的操作，未知结果不能直接重发。"),
        result,
      );
      const active = () => view.isConnected && sequence === detailSequence &&
        content.isConnected && $("#dialog").open;
      const current = (reading) => active() && reading === readingSequence;

      function showSubmission(creation, record, reading) {
        const descriptions = {
          not_recorded: "没有统一提交记录。确认后沿原生准入提交此冻结合同一次。",
          prepared: "原提交意图已保存，尚无派发检查点。明确恢复后，由原生流程决定是否继续首次派发。",
          unknown: "派发结果尚未确认。恢复只核对原工作流，不重新发起start；not_found仍不证明从未提交。",
          submitted: "本地回执已保存原run；这不代表六阶段完成。请按原run单独查询运行状态。",
          rejected: "原提交归属已被拒绝。请核对冲突记录，页面不会覆盖、重提或更换任务ID。",
        };
        const canStart = creation.status === "published" && record.status === "not_recorded";
        const canResume = creation.status === "published" && ["prepared", "unknown"].includes(record.status);
        if (record.status === "submitted") sessionStorage.setItem(runKey, record.run_id);
        result.replaceChildren(panel(`提交记录：${record.status}`, descriptions[record.status],
          facts([
            ["任务 ID", taskId], ["项目当前修订", creation.project_revision],
            ["创建状态", creation.status], ["原创建修订", creation.created_revision],
            ["原创建意图 SHA256", creation.intent_sha256],
            ["请求 SHA256", task.request_sha256], ["合同文件 SHA256", task.spec_file_sha256],
            ["原提交意图 SHA256", record.intent_sha256], ["原提交修订", record.submitted_revision],
            ["工作流 ID", record.workflow_id], ["原 run ID", record.run_id],
            ["原工作流恢复查询", record.reconciliation],
            ["归属拒绝原因", record.reason], ["冲突 run ID", record.conflicting_run_id],
          ]),
          disclosure("完整创建记录与冻结角色", creation),
          disclosure("冻结合同、输入与验收", task.spec),
          disclosure("完整本地提交记录", record),
          creation.status !== "published" ? empty("创建尚未完整发布；请先按原ID检查创建记录，不能提交运行。") : null,
          canStart || canResume ? form([], canStart ? "确认提交此冻结任务" : "确认恢复原提交意图", async () => {
            if (!current(reading)) return;
            result.replaceChildren(empty(`正在处理 ${taskId} 的原提交；关闭页面不取消操作。回复未知时先重新读取原记录。`));
            let observed;
            try {
              observed = await api(`${path}/${canStart ? "start" : "resume-start"}`, {
                revision: creation.project_revision, timeout: 20,
                ...(canStart ? { creation_sha256: creation.intent_sha256 }
                  : { intent_sha256: record.intent_sha256 }),
              });
            } catch (error) {
              if (current(reading)) result.replaceChildren(panel("提交结果尚未确认", error.message,
                node("p", {}, `请保留原任务 ID：${taskId}。先重新读取原提交记录；不要更换ID或重发start。`),
                button("重新读取原提交记录", read),
              ));
              return;
            }
            if (current(reading)) showSubmission(creation, observed, reading);
          }) : null,
          row(
            button("重新读取原提交记录", read),
            record.status === "submitted" ? button("查看原任务与运行", () => {
              if (!current(reading)) return;
              $("#dialog").close();
              inspect(taskId);
            }) : null,
          ),
        ));
      }

      async function read() {
        if (!active()) return;
        const reading = ++readingSequence;
        result.replaceChildren(empty(`正在读取 ${taskId} 的原创建与提交记录…`));
        let creation, record;
        try {
          [creation, record] = await Promise.all([api(`${path}/creation`), api(`${path}/submission`)]);
        } catch (error) {
          if (current(reading)) result.replaceChildren(panel("提交检查读取失败", error.message,
            node("p", {}, `原任务 ID：${taskId}。两份记录未完整读取，不提供写入确认。`),
            button("重新读取原提交记录", read),
          ));
          return;
        }
        if (current(reading)) showSubmission(creation, record, reading);
      }
      modal("检查提交与恢复", content);
      read();
    }

    detail.replaceChildren(
      panel(taskId, input.goal,
        row(badge(request.task_type), badge("冻结合同 · 本地读取")),
        facts([
          ["项目当前修订", task.project_revision],
          ["冻结角色修订", bindings?.project_revision],
          ["工单", `${request.tracker.kind} · ${request.tracker.project} #${request.tracker.issue_id}`],
          ["基线提交", request.repository.base_sha],
          ["请求 SHA256", task.request_sha256],
          ["合同 SHA256", task.spec_file_sha256],
        ]),
        disclosure("输入、验收与约束", input),
        disclosure("完整冻结合同", task.spec),
      ),
      panel("冻结角色与工作单元", "后续项目绑定调整不会更换此任务已冻结的选择。",
        bindings
          ? table(["角色", "工具", "模型"], Object.entries(bindings.bindings).map(([role, binding]) => [role, binding.tool, binding.model ?? "未指定"]))
          : empty("旧任务没有角色快照；这里不使用当前绑定补写历史。"),
        table(["工作单元", "前置依赖", "允许路径"], input.work_units.map((unit) => [
          unit.id, unit.depends_on.join("、") || "无", unit.paths.join("、"),
        ])),
        bindings ? disclosure("完整角色快照", bindings) : null,
      ),
      panel("本地提交回执", "回执记录操作事实；submitted不代表六阶段通过。",
        saved ? disclosure(`提交状态：${saved.status}`, saved)
          : node("p", { className: "task-error" }, `提交回执读取失败：${submission.reason.message}`),
        button("检查提交与恢复", submissionDialog),
        saved?.status === "submitted" ? button("按原 ID 检查批准记录", () => approvalDialog()) : null,
        saved?.status === "submitted" ? button("按原 ID 检查取消记录", () => cancellationDialog()) : null,
        saved?.status === "submitted" ? button("检查原对账记录与恢复", () => reconciliationDialog()) : null,
        saved?.status === "submitted" ? button("检查原导出记录与恢复", () => exportDialog()) : null,
      ),
      panel("原生运行", "按固定run读取。关闭页面不会取消任务；取消后的外部清理需另行对账。",
        form([runField], "读取原运行", async (values) => {
          const runId = values.get("run_id");
          sessionStorage.setItem(runKey, runId);
          const reading = ++runSequence;
          runtime.replaceChildren(empty("正在查询原运行…"));
          let observed;
          try {
            observed = await api(`${path}/status?${new URLSearchParams({ run_id: runId, timeout: "20" })}`);
          } catch (error) {
            if (view.isConnected && sequence === detailSequence && reading === runSequence)
              runtime.replaceChildren(panel("运行查询失败", error.message));
            return;
          }
          if (!view.isConnected || sequence !== detailSequence || reading !== runSequence) return;
          const state = observed.status || observed.outcome;
          const currentStage = observed.terminal ? null : stageForPhase[observed.phase];
          runtime.replaceChildren(...[
            row(badge(observed.runtime_status), observed.phase ? badge(observed.phase) : null),
            observed.runtime_status === "not_found"
              ? empty("未找到所选原运行；这不证明任务从未提交。请核对原run和提交回执。")
              : facts([
                ["工作流 ID", observed.workflow_id], ["原 run ID", observed.run_id],
                ["原运行已闭合", observed.terminal ? "是" : "否"],
                ["候选提交", state?.candidate_sha], ["计划 SHA256", state?.plan_sha256],
              ]),
            observed.runtime_status === "queried"
              ? button("读取原运行事件", () => eventsDialog(observed.run_id, reading)) : null,
            !observed.terminal && observed.phase === "AWAITING_PLAN_APPROVAL"
              ? button("审阅计划与批准", () => {
                if (!view.isConnected || sequence !== detailSequence || reading !== runSequence) return;
                return approvalDialog({ run_id: observed.run_id, plan_sha256: observed.status.plan_sha256 }, reading);
              }, "primary") : null,
            !observed.terminal && observed.runtime_status === "queried"
              ? button("请求取消此运行", () => cancellationDialog(observed.run_id, reading)) : null,
            observed.terminal && observed.runtime_status === "queried"
              ? button("证据、预算与交接", () => evidenceDialog(observed.run_id, reading)) : null,
            observed.terminal && observed.runtime_status === "queried"
              ? button("外部证据与对账", () => reconciliationDialog(observed.run_id, reading)) : null,
            observed.terminal && observed.runtime_status === "queried" && observed.outcome?.status === "REVIEW_READY"
              ? button("导出精确候选", () => exportDialog({ run_id: observed.run_id,
                candidate_sha: observed.outcome.candidate_sha }, reading), "primary") : null,
            node("div", { className: "stage-strip", "aria-label": "六阶段位置" }, stages.map((stage) =>
              node("span", { className: currentStage === stage ? "current" : null }, stage))),
            observed.status ? facts([
              ["活动阶段/单元", observed.status.active_stages.join("、") || "无"],
              ["已完成阶段/单元", observed.status.completed_stages.join("、") || "无"],
            ]) : null,
            disclosure("原始运行与结果", observed),
          ].filter(Boolean));
        }),
        runtime,
      ),
    );
  }

  loadPage();
  if (selected) inspect(selected);
  return [title, view];
}
