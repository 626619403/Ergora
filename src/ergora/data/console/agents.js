import { api } from "./api.js";
import { node, pre, panel, field, selectField, status, form, modal, button, row, empty, table, checkbox } from "./ui.js";
import { app } from "./state.js";

function archivedHistory(base, runId, active = () => true) {
  const content = node("div");
  let nextOffset = null;
  let revision = null;
  const start = button("读取原生历史", () => read(true));
  const next = button("下一页", () => read(false), "secondary", { disabled: true });
  const view = panel("原生历史归档", "按页查看已保存的输入、工具结果和模型回复。", row(start, next), content);
  const displayed = () => active() && view.isConnected && view.closest("dialog")?.open;
  async function read(reset) {
    start.disabled = true;
    next.disabled = true;
    try {
      const query = new URLSearchParams({ native_history: "true", history_offset: reset ? 0 : nextOffset });
      if (!reset) query.set("history_revision", revision);
      const result = await api(`${base}/agent-runs/${runId}/output?${query}`);
      if (!displayed()) return;
      const page = result.native_history;
      if (!page.available) {
        content.replaceChildren(node("p", {}, page.reason));
        return;
      }
      revision = page.revision;
      nextOffset = page.next_offset;
      content.replaceChildren(
        node("p", {}, `${page.offset}–${page.offset + page.bytes_read} / ${page.size_bytes} 字节`, nextOffset === null ? " · 已到本次观察末尾" : ""),
        pre(page.content),
      );
      next.disabled = nextOffset === null;
      start.textContent = "从头读取";
    } catch (error) {
      if (displayed()) throw error;
    } finally {
      if (displayed()) start.disabled = false;
    }
  }
  return view;
}

export function outputPanels(result, base, active) {
  const panels = Object.entries(result.streams).map(([name, stream]) =>
    panel(
      name === "stdout" ? "标准输出" : "诊断输出",
      !stream.available
        ? "输出文件尚未产生"
        : stream.truncated
          ? "显示前 64 KiB；完整输出保存在运行归档"
          : "",
      pre(stream.text),
    ),
  );
  if (result.result) panels.unshift(panel("最终回复原文",
    result.result.available ? `${result.result.bytes} 字节 · SHA256 ${result.result.sha256}` : result.result.reason,
    result.result.available ? pre(result.result.text) : null));
  if (base) panels.push(archivedHistory(base, result.id, active));
  return panels;
}
export function agentDialog(data, base, refresh, origin = null) {
  const tab = app.tab;
  const control = app.bootstrap.state_directory;
  const pendingKey = `ergora-agent-pending:${JSON.stringify([control, data.project.id])}`;
  const correctionPendingKey = `ergora-correction-pending:${JSON.stringify([control, data.project.id])}`;
  const pending = () => JSON.parse(sessionStorage.getItem(pendingKey) || "[]");
  const correctionPending = () => JSON.parse(sessionStorage.getItem(correctionPendingKey) || "[]");
  function remember(operation) {
    sessionStorage.setItem(pendingKey, JSON.stringify([...pending(), operation]));
  }
  function observed(intent) {
    sessionStorage.setItem(pendingKey, JSON.stringify(pending().filter((item) => item.intent !== intent)));
  }
  function admissionRejected(error, intent) {
    const rejection = error.response;
    return rejection?.admission_rejected === true && rejection.native_effect_started === false && rejection.intent_id === intent;
  }
  const result = node("div", { "aria-live": "polite" });
  const unresolved = node("div", { "aria-live": "polite" });
  const observationResult = node("div", { "aria-live": "polite" });
  const listing = node("div", { "aria-live": "polite" });
  const detail = node("div", { "aria-live": "polite" });
  const preferenceResult = node("div", { "aria-live": "polite" });
  const preference = data.configuration.correction_suggestions;
  const preferenceFields = node("fieldset", { disabled: !preference },
    checkbox("Suggest reusable corrections in new native sessions", "enabled", preference?.enabled === true));
  const preferenceForm = form([preferenceFields], "Save suggestion preference", async (values) => {
    if (!active() || preferenceFields.disabled) return;
    preferenceFields.disabled = true;
    preferenceNeedsReload = true;
    selectionSequence++;
    startFields.disabled = true;
    detail.replaceChildren(empty("Project preference update is pending. Reload the project configuration before starting or continuing a session."));
    try {
      const project = await api(`${base}/correction-suggestions`,
        { enabled: values.has("enabled"), revision: data.project.revision }, "PUT");
      if (!active()) return;
      preferenceResult.replaceChildren(panel("Suggestion preference saved",
        `Project revision ${project.revision}. Start a new session to use this preference; earlier sessions retain their original revision.`,
        row(button("Reload project configuration", () => refresh(data.project.id)))));
      startFields.disabled = true;
      detail.replaceChildren(empty("Project configuration changed. Reload the project and start a new session."));
    } catch (error) {
      if (active()) preferenceResult.replaceChildren(panel("Preference update unconfirmed", error.message,
        "Reload project configuration to observe the saved value before another explicit update. No automatic resend.",
        row(button("Reload project configuration", () => refresh(data.project.id)))));
    }
  });
  const read = button("读取项目会话", () => readSessions(true));
  const next = button("下一页会话", () => readSessions(false), "secondary", { disabled: true });
  const startFields = node("fieldset", {},
    selectField("角色", app.agentRoles.map((role) => [role, app.layers[role][0]]), "implementer", "role"),
    selectField("模板产物要求（可选）", [["", "普通独立调用"], ...app.bootstrap.templates.map((kind) => [kind, kind])], "", "template"),
    field("任务说明", "prompt", "", "textarea", { required: true }),
    field("活动 Skill 名称（逗号分隔，可选）", "skills"),
    field("项目记忆检索（可选）", "recall"),
    checkbox("保存为可继续的开发会话", "persistent", true),
    field("首次会话的 Codex 配置文件", "codex_config", "", "text", { autocomplete: "off" }),
    field("超时（秒）", "timeout", 300, "number", { required: true, min: 1, max: 3600, step: 1 }));
  const startForm = form([startFields], "开始调用", start);
  const view = node("div", {},
    panel("Correction suggestions", preference
      ? `${preference.enabled ? "Enabled" : "Disabled"} · ${preference.source === "default" ? "project default" : "explicit project setting"}. Availability is reported by each original native turn.`
      : "Preference is unavailable in this project configuration.",
      node("p", {}, "New eligible plain-text native sessions can suggest an exact change to the existing project AGENTS.md. Template and six-stage modes use the explicit manual document-correction workflow. This preference changes the project revision and requires a new session. Native workspace permissions still apply; suggestions do not isolate file writes."),
      preferenceForm, preferenceResult), unresolved, observationResult,
    panel("项目历史会话", "选择原会话后输入任务说明继续。角色、模型、权限和材料沿首次冻结；变更配置需要新建会话。", row(read, next), listing, detail),
    node("details", {}, node("summary", {}, "新建会话或单次 Agent 调用"),
      node("p", {}, "沿当前角色的 native workspace 权限运行。普通开发会话不产生正式任务批准或可信候选；模板选项仅要求该角色的产物。持久化能力与阻断原因以服务器实际返回为准。"), startForm, result));
  const active = () => view.isConnected && view.closest("dialog")?.open && app.data === data &&
    app.project === data.project.id && app.bootstrap.state_directory === control && app.tab === tab && (!origin || origin.isConnected);
  let listSequence = 0;
  let selectionSequence = 0;
  let selected = null;
  let nextAfter = null;
  let starting = false;
  let resultSequence = 0;
  let observationSequence = 0;
  let preferenceNeedsReload = false;
  let previewGeneration = 0;
  const previewCache = new Map();

  function pendingView() {
    if (!active()) return;
    const saved = pending();
    startFields.disabled = preferenceNeedsReload || starting || saved.some((item) => item.kind === "start");
    const corrections = correctionPending();
    unresolved.replaceChildren(...(saved.length ? [panel("提交尚待观察",
      "已保留原 intent 和完整请求，没有自动重发。先观察原操作；当前没有记录也不能证明未运行。",
      ...saved.map((item) => node("details", {}, node("summary", {}, `${item.kind} · ${item.intent}`), pre(item))),
      row(button("观察原操作", observePending)))] : []),
      ...(corrections.length ? [panel("Original document decisions awaiting observation",
        "Only read the original proposal status after an unconfirmed reply. No decision is resent.",
        ...corrections.map((item) => correctionView({ proposal_id: item.proposal_id, candidate_digest: item.candidate_digest, status: "unconfirmed", reason: `${item.action} reply unconfirmed` }, () => true, false)))] : []));
  }

  function correctionView(initial, current, showPreview = true) {
    if (!initial) return empty("Correction suggestions were not recorded for this original turn. Use the explicit manual document-correction workflow if needed.");
    const generation = previewGeneration;
    let observation = { ...initial, preview: null };
    let sequence = 0;
    let preview = null;
    let loadingDigest = null;
    const proposal = initial.proposal_id;
    const originalUrl = `${base}/document-corrections/${encodeURIComponent(proposal)}`;
    const facts = node("div");
    const body = node("div");
    const feedback = node("div");
    const note = node("p");
    const apply = button("Apply exact project change", () => decide("apply"), "primary", { disabled: true });
    const dismiss = button("Use only for this task / dismiss", () => decide("withdraw"), "secondary", { disabled: true });
    const content = panel("Project correction suggestion", "", facts, body, feedback,
      row(proposal ? button("Read original proposal status", readOriginal) : null, showPreview ? apply : null, showPreview ? dismiss : null), note);
    const displayed = () => active() && current() && generation === previewGeneration && content.isConnected;

    function update(message = null) {
      const awaiting = correctionPending().some((item) => item.proposal_id === proposal);
      const canDecide = preview && observation.candidate_digest === preview.candidate_digest && observation.status === "ready" && !awaiting;
      apply.disabled = !canDecide || observation.can_apply !== true;
      dismiss.disabled = !canDecide;
      facts.replaceChildren(node("p", {}, observation.reason || "Read the complete proposed project change before deciding."),
        table(["Original fact", "Value"], [["Preference", observation.enabled === undefined ? "See original turn" : observation.enabled ? "enabled" : "disabled"],
          ["Apply action", observation.can_apply === true ? "available" : "unavailable"],
          ["Source validation", observation.source_validation ?? "The host rechecks the original source and current project before exact apply"],
          ["Proposal", proposal ?? "No proposal"], ["Status", observation.status ?? "unavailable"], ["Candidate digest", observation.candidate_digest ?? "No candidate"]]));
      feedback.replaceChildren(...(message ? [message] : []),
        ...(awaiting ? [empty("The original decision is pending observation. Applying or withdrawing again is disabled.")] : []));
      note.textContent = preview ? "" : loadingDigest ? "Reading the exact saved preview; no model is invoked."
        : "No host preview is displayed. The explicit manual document-correction workflow remains separate.";
    }

    function attach(entry) {
      if (!entry.body) entry.body = previewBody(entry.preview);
      preview = entry.preview;
      if (body.firstChild !== entry.body) body.replaceChildren(entry.body);
      loadingDigest = null;
      update();
    }

    function loadPreview(full = null) {
      const digest = observation.candidate_digest;
      if (!showPreview || !proposal || !digest || preview?.candidate_digest === digest || loadingDigest === digest) return;
      const key = JSON.stringify([control, data.project.id, generation, digest]);
      let entry = previewCache.get(key);
      if (!entry) {
        entry = { preview: null, body: null };
        const validate = (value) => {
          if (value.candidate_digest !== digest || value.request.project !== data.project.id || value.request.proposal_id !== proposal)
            throw new Error("Saved preview differs from the selected project, proposal or candidate digest");
          return value;
        };
        entry.promise = full ? Promise.resolve(validate(full))
          : api(`${originalUrl}/preview?${new URLSearchParams({ candidate_digest: digest })}`).then(validate);
        if (full) entry.preview = full;
        previewCache.set(key, entry);
      }
      if (entry.preview) {
        attach(entry);
        return;
      }
      loadingDigest = digest;
      update();
      entry.promise.then((value) => {
        if (!displayed() || observation.candidate_digest !== digest) return;
        entry.preview = value;
        attach(entry);
      }).catch((error) => {
        if (!displayed() || observation.candidate_digest !== digest) return;
        loadingDigest = null;
        update(panel("Exact saved preview unavailable", error.message));
      });
    }

    async function readOriginal() {
      if (!displayed()) return;
      const reading = ++sequence;
      try {
        const observed = await api(originalUrl);
        if (!displayed() || reading !== sequence) return;
        observation = { enabled: initial.enabled, ...observed, preview: null };
        if (["applied", "withdrawn"].includes(observed.status)) {
          sessionStorage.setItem(correctionPendingKey, JSON.stringify(correctionPending().filter((item) => item.proposal_id !== proposal)));
        }
        update();
        loadPreview();
      } catch (error) {
        if (displayed() && reading === sequence) {
          observation = { ...observation, can_apply: false };
          update(panel("Original proposal observation failed", error.message));
        }
      }
    }

    async function decide(action) {
      if (!displayed() || !preview || observation.candidate_digest !== preview.candidate_digest || observation.status !== "ready" ||
          correctionPending().some((item) => item.proposal_id === proposal) || (action === "apply" && observation.can_apply !== true)) return;
      const deciding = ++sequence;
      sessionStorage.setItem(correctionPendingKey, JSON.stringify([...correctionPending(),
        { proposal_id: proposal, action, candidate_digest: preview.candidate_digest }]));
      update(empty("Waiting for the original decision. No automatic resend."));
      const payload = action === "apply" ? { revision: preview.request.revision, candidate_digest: preview.candidate_digest,
        base_sha256: preview.change.before.sha256, scope_sha256: preview.scope_sha256, confirm: true }
        : { reason: "Operator chose task-only use or dismissed this exact project suggestion." };
      try {
        const response = await api(`${originalUrl}/${action}`, payload);
        if (!displayed() || deciding !== sequence) return;
        observation = { enabled: initial.enabled, ...response, preview: null, candidate_digest: preview.candidate_digest, can_apply: false };
        if (["applied", "withdrawn"].includes(response.status)) {
          sessionStorage.setItem(correctionPendingKey, JSON.stringify(correctionPending().filter((item) => item.proposal_id !== proposal)));
        }
        update(pre(response));
      } catch (error) {
        if (displayed() && deciding === sequence) update(panel("Document decision unconfirmed", error.message,
          "Read the original proposal status. This action will not be resent."));
      }
    }

    observation.candidate_digest ??= initial.preview?.candidate_digest;
    update();
    loadPreview(initial.preview);
    return content;
  }

  function previewBody(preview) {
    return node("div", {}, table(["Exact change", "Original value"], [["Project", preview.request.project],
      ["Source", pre({ result: preview.source, correction: preview.request.correction })],
      ["Prior document operation snapshot", preview.request.parent ? pre(preview.request.parent) : "None"], ["Target", preview.change.path],
      ["Lesson", preview.lesson], ["Applicability", preview.applicability], ["Revision", preview.request.revision],
      ["Candidate digest", preview.candidate_digest], ["Base SHA256", preview.change.before.sha256],
      ["After SHA256", preview.change.after.sha256], ["Before / after mode", `${preview.change.before.mode} / ${preview.change.after.mode}`],
      ["Scope SHA256", preview.scope_sha256]]), panel("Complete before text", "", pre(preview.change.before.text)),
      panel("Complete after text", "", pre(preview.change.after.text)), panel("Full diff", "", pre(preview.change.diff)),
      panel("Exact project scope and authority", "", pre(preview.scope)));
  }

  function runFacts(run) {
    return run.correction_suggestion ? { ...run, correction_suggestion: { ...run.correction_suggestion, preview: null } } : run;
  }

  function showRun(target, run, current) {
    target.replaceChildren(status(run.status), pre(runFacts(run)), correctionView(run.correction_suggestion, current), row(button("读取这轮原输出", async () => {
      try {
        const output = await api(`${base}/agent-runs/${encodeURIComponent(run.id)}/output`);
        if (active() && current()) target.append(...outputPanels(output, base, () => active() && current()));
      } catch (error) {
        if (active() && current()) target.append(panel("原输出读取失败", error.message));
      }
    })));
  }

  const observationOffsets = new Map();
  async function observePending() {
    const reading = ++observationSequence;
    const selection = selectionSequence;
    const current = () => active() && reading === observationSequence && selection === selectionSequence;
    const saved = pending();
    const observations = [];
    try {
      for (const item of saved) {
        if (item.kind === "start") {
          const query = new URLSearchParams({ intent_id: item.intent, limit: 1 });
          const page = await api(`${base}/agent-sessions?${query}`);
          if (!current()) return;
          const session = page.sessions.find((session) => session.birth_intent === item.intent);
          if (session) {
            observed(item.intent);
            observations.push(panel(`原会话 ${session.id}`, "已按原出生 intent 找到。", pre(session),
              row(button("选择这个原会话", () => selectSession(session.id)))));
          } else observations.push(empty(`出生 intent ${item.intent} 尚无可观察记录；仍保留原提交。`));
        } else if (item.kind === "continue") {
          const query = new URLSearchParams({ parent_run_id: item.payload.parent_run_id });
          const receipt = await api(`${base}/agent-sessions/${encodeURIComponent(item.session)}/continuations/${encodeURIComponent(item.intent)}?${query}`);
          if (!current()) return;
          if (receipt.session_id !== item.session || receipt.intent_id !== item.intent ||
              receipt.parent_run_id !== item.payload.parent_run_id) throw new Error("返回的续接回执与原提交不符。");
          if (receipt.dispatch === "unrecorded") {
            observations.push(empty(`续接 intent ${item.intent} 尚无可观察记录；仍保留原提交。`));
          } else {
            const label = { reserved: "已预留原轮次", attempted: "已记录原派发尝试", accepted: "监督进程已接单",
              incomplete: "派发证据不完整" }[receipt.dispatch];
            const native = { running: "原执行子进程正在运行", started: "已核对原执行子进程启动",
              unrecorded: "启动回执暂无记录", incomplete: "启动证据不完整" }[receipt.native_start?.status];
            if (!label || !receipt.run || receipt.run.id !== receipt.run_id) throw new Error("原续接回执不完整。");
            observed(item.intent);
            observations.push(panel(`原续接 ${receipt.run_id}`, [label, native].filter(Boolean).join(" · "), pre(receipt),
              row(button("选择这个原会话", () => selectSession(item.session)))));
          }
        } else {
          const after = observationOffsets.get(item.intent) ?? 0;
          const page = await api(`${base}/agent-sessions/${encodeURIComponent(item.session)}?after=${after}&limit=20`);
          if (!current()) return;
          const run = page.turns.find((turn) => turn.id === item.payload.run_id && turn.stop_request?.intent_id === item.intent);
          if (run) {
            observed(item.intent);
            observationOffsets.delete(item.intent);
            observations.push(panel(`原操作 ${run.id}`, "已按原会话、轮次和 intent 找到。", pre(run),
              row(button("选择这个原会话", () => selectSession(item.session)))));
          } else {
            observationOffsets.set(item.intent, page.next_after ?? 0);
            observations.push(empty(page.next_after === null
              ? `intent ${item.intent} 尚无对应原记录；保留原提交，下次观察从头读取。`
              : `intent ${item.intent} 不在本页；再次观察读取下一页轮次。`));
          }
        }
      }
      if (!current()) return;
      pendingView();
      observationResult.replaceChildren(...observations);
      await readSessions(true);
    } catch (error) {
      if (current()) observationResult.replaceChildren(panel("观察失败", error.message));
    }
  }

  async function start(values) {
    if (!active() || startFields.disabled || starting || pending().some((item) => item.kind === "start")) return;
    const persistent = values.has("persistent");
    const payload = { role: values.get("role"), prompt: values.get("prompt"), timeout: Number(values.get("timeout")),
      skills: values.get("skills").split(",").map((value) => value.trim()).filter(Boolean),
      recall: values.get("recall") || null, template: values.get("template") || null };
    const intent = crypto.randomUUID();
    if (persistent) Object.assign(payload, { session_intent: intent, expected_revision: data.project.revision,
      codex_config: values.get("codex_config") || null });
    if (persistent) remember({ kind: "start", intent, payload });
    starting = true;
    const rendering = ++resultSequence;
    const selection = selectionSequence;
    pendingView();
    result.replaceChildren(empty("已提交原调用。可读取项目历史并停止精确轮次；关闭页面不会撤销调用。"));
    try {
      const run = await api(`${base}/agent-runs`, payload);
      observed(intent);
      if (!active() || selection !== selectionSequence) return;
      if (run.session) {
        result.replaceChildren(empty("原调用已返回；完整建议显示在所选会话中。"));
        await selectSession(run.session.id, 0, null, run);
      } else {
        showRun(result, run, () => rendering === resultSequence && selection === selectionSequence);
        result.append(row(button("刷新项目总览", () => refresh(data.project.id))));
      }
    } catch (error) {
      const rejectedBeforeBirth = persistent && admissionRejected(error, intent);
      if (rejectedBeforeBirth) observed(intent);
      if (active() && selection === selectionSequence) result.replaceChildren(panel(rejectedBeforeBirth ? "会话准入已拒绝" : "调用未获确认", error.message,
        rejectedBeforeBirth ? "原 owner 已明确确认此 intent 未出生、未开始 native effect。可修改配置后明确新建会话。" :
          persistent ? "原请求仍保留。先观察原操作；不会自动重发。" : "单次调用的回复未确认，请从最近工具调用核对原记录；没有自动重发。"));
    } finally {
      starting = false;
      pendingView();
    }
  }

  async function readSessions(reset) {
    if (!active()) return;
    const reading = ++listSequence;
    read.disabled = next.disabled = true;
    try {
      const query = new URLSearchParams({ after: reset ? 0 : nextAfter, limit: 20 });
      const page = await api(`${base}/agent-sessions?${query}`);
      if (!active() || reading !== listSequence) return;
      nextAfter = page.next_after;
      listing.replaceChildren(table(["会话 / 角色", "后端 / 权限", "状态", "操作"], page.sessions.map((session) => [
        node("span", {}, session.id, node("small", {}, session.role)),
        `${session.binding.tool} · ${session.mode} · ${session.sandbox ?? "未记录"}`,
        node("span", {}, status(session.status), node("small", {}, session.can_continue ? "可继续" : session.reason)),
        button("选择会话", () => selectSession(session.id)),
      ])));
    } catch (error) {
      if (active() && reading === listSequence) listing.replaceChildren(panel("会话读取失败", error.message));
    } finally {
      if (active() && reading === listSequence) {
        read.disabled = false;
        next.disabled = nextAfter === null;
      }
    }
  }

  async function selectSession(id, after = 0, expectedSelection = null, completedRun = null) {
    if (!active() || (expectedSelection !== null && expectedSelection !== selectionSequence)) return;
    const reading = ++selectionSequence;
    if (selected !== id) {
      previewGeneration++;
      previewCache.clear();
    }
    selected = id;
    const current = () => reading === selectionSequence && selected === id;
    if (completedRun) showRun(detail, completedRun, current);
    else detail.replaceChildren(empty("正在读取原会话…"));
    try {
      const session = await api(`${base}/agent-sessions/${encodeURIComponent(id)}?after=${after}&limit=20`);
      if (!active() || reading !== selectionSequence || selected !== id) return;
      const callResult = node("div", { "aria-live": "polite" });
      const continueFields = node("fieldset", { disabled: preferenceNeedsReload || !session.can_continue || pending().some((item) => item.session === id && item.kind === "continue") },
        field("继续任务说明", "prompt", "", "textarea", { required: true }),
        field("本轮超时（秒）", "timeout", 300, "number", { required: true, min: 1, max: 3600, step: 1 }));
      const continueForm = form([continueFields], "继续这个会话", async (values) => {
        if (!active() || !current() || continueFields.disabled) return;
        const payload = { parent_run_id: session.latest_run, prompt: values.get("prompt"),
          expected_revision: data.project.revision, intent_id: crypto.randomUUID(), timeout: Number(values.get("timeout")) };
        await submitTurn("continue", payload, callResult, current, continueFields, reading);
      });
      detail.replaceChildren(panel(`会话 ${session.id}`, session.can_continue ? "可以沿此会话继续开发。" : session.reason,
        table(["冻结事实", "原记录"], [["仓库", session.repo], ["角色", session.role], ["模式 / sandbox", `${session.mode} / ${session.sandbox ?? "未记录"}`],
          ["后端 / 模型 / effort", `${session.binding.tool} / ${session.binding.model ?? "见原配置"} / ${session.binding.reasoning_effort ?? session.binding.effort ?? "见原配置"}`],
          ["最新轮次", session.latest_run]]), pre(session.binding),
        row(button("刷新这个会话", () => selectSession(id)),
          session.next_after === null ? null : button("下一页轮次", () => selectSession(id, session.next_after))),
        ...session.turns.map((run) => {
          const output = node("div");
          return node("div", {}, correctionView(run.correction_suggestion, current),
            node("details", {}, node("summary", {}, `${run.id} · ${run.status} · ${run.started ?? ""}`), pre(runFacts(run)),
            row(button("读取这轮原输出", async () => {
              try {
                const result = await api(`${base}/agent-runs/${encodeURIComponent(run.id)}/output`);
                if (active() && current()) output.replaceChildren(...outputPanels(result, base, () => active() && current()));
              } catch (error) {
                if (active() && current()) output.replaceChildren(panel("原输出读取失败", error.message));
              }
            }), button("请求停止这轮", async (event) => {
              if (!active() || !current() || pending().some((item) => item.kind === "stop" && item.payload.run_id === run.id)) return;
              event.currentTarget.disabled = true;
              await submitTurn("stop", { run_id: run.id, intent_id: crypto.randomUUID() }, callResult, current, null, reading);
            }, "secondary", { disabled: run.execution_stopped === true || Boolean(run.stop_request) || pending().some((item) => item.kind === "stop" && item.payload.run_id === run.id) })), output));
        }), continueForm, callResult));
    } catch (error) {
      if (active() && reading === selectionSequence) detail.replaceChildren(panel("会话读取失败", error.message));
    }
  }

  async function submitTurn(kind, payload, target, current, fields, reading) {
    const id = selected;
    remember({ kind, session: id, intent: payload.intent_id, payload });
    if (fields) fields.disabled = true;
    pendingView();
    target.replaceChildren(empty("已保存本次提交意图，正在等待原操作返回。可以刷新原会话观察；不自动重发。"));
    try {
      const response = await api(`${base}/agent-sessions/${encodeURIComponent(id)}/${kind}`, payload);
      observed(payload.intent_id);
      if (!active() || !current()) return;
      target.replaceChildren(panel(kind === "stop" ? "原停止请求已返回" : "原续答记录已返回",
        kind === "stop" ? "stop_requested、notification 和 run 中的停止事实分别核对；请求返回不等于清理完成。" : "沿原会话读取本轮结果。", pre(response.run ? { ...response, run: runFacts(response.run) } : runFacts(response)),
        correctionView(response.correction_suggestion ?? response.run?.correction_suggestion, current),
        row(button("读取本轮后的会话", () => selectSession(id, 0, reading)))));
    } catch (error) {
      const rejected = kind === "continue" && admissionRejected(error, payload.intent_id);
      if (rejected) observed(payload.intent_id);
      if (active() && current()) {
        if (rejected) fields.disabled = false;
        target.replaceChildren(panel(rejected ? "续答准入已拒绝" : "提交未获确认", error.message,
          rejected ? "原 owner 已明确确认本轮未保留执行名额、未开始 native effect。可修改任务说明后明确提交新一轮。" :
            "已保留完整请求和原 intent。先观察原操作；不会自动重发。"));
      }
    } finally {
      pendingView();
    }
  }

  modal("项目 Agent 会话", view);
  pendingView();
  readSessions(true);
}

export function compositionDialog(data, base, origin, onResult) {
  const backends = new Map(app.agentRoles.flatMap((role) => app.bootstrap.tools[role].map((item) =>
    [item.tool, item.supported === false ? `${item.tool} · WSL2/Linux` : item.tool])));
  const checkButton = node("button", { type: "submit", className: "primary" }, "检查当前只读准入");
  const checkStatus = node("div", { "aria-live": "polite" });
  const callStatus = node("div", { "aria-live": "polite" });
  const attempted = node("p", { "aria-live": "polite" });
  const checkFields = node("fieldset", {}, node("legend", {}, "原冻结输入与本次后端"),
    field("冻结 input 路径", "directory", "", "text", { required: true, autocomplete: "off" }),
    field("冻结 input digest", "input_digest", "", "text", { required: true, spellcheck: "false" }),
    selectField("叶后端", [["", "使用冻结定义的请求"], ...backends], "", "backend"),
    field("叶模型（可选）", "model"), field("后端选择原因（可选）", "reason"),
    field("Codex 推理配置路径（可选）", "codex_config", "", "text", { autocomplete: "off" }), row(checkButton));
  const checkForm = node("form", { onsubmit: (event) => { event.preventDefault(); return check(); } }, checkFields);
  const runFields = node("fieldset", { disabled: true }, node("legend", {}, "明确调用这个叶"),
    field("单叶超时（秒）", "timeout", 300, "number", { required: true, min: 1, max: 3600, step: 1 }),
    row(node("button", { type: "submit", className: "primary" }, "明确调用这个只读叶")));
  const runForm = node("form", { onsubmit: (event) => { event.preventDefault(); return invoke(); } }, runFields);
  const records = node("div", { "aria-live": "polite" });
  const view = node("div", {},
    panel("冻结 input 的单叶调用", "只运行原 text-only 模式，交付全部冻结祖先资料；不运行图端口、workspace 或正式 Task。准入是当前观察，执行前原 owner 会重新核对。", checkForm, checkStatus, runForm, attempted, callStatus),
    panel("原调用记录", "明确读取当前项目最近最多100条原记录。丢回复或切页不表示没有调用；先核对 input digest、原后端、时间与状态，不自动重发。",
      row(button("读取原调用记录", readRecords)), records));
  const active = () => origin.isConnected && view.isConnected && view.closest("dialog")?.open && app.data === data && app.project === data.project.id;
  let sequence = 0;
  let recordSequence = 0;
  let selected = null;
  let running = false;

  function invalidate() {
    sequence++;
    selected = null;
    checkButton.disabled = running;
    runFields.disabled = true;
    checkStatus.replaceChildren(empty("输入或后端已更改，请明确重新检查。"));
  }

  function resultAction(run) {
    return onResult && run.kind === "composition-agent-run" && run.status === "succeeded" && run.result && run.result_sha256
      ? button("带入原结果检查", () => {
        if (active() && onResult({ directory: run.input_path, input_digest: run.input_digest,
          result: run.result, result_sha256: run.result_sha256 })) view.closest("dialog").close();
      }) : null;
  }

  async function check() {
    if (!active() || running || checkButton.disabled) return;
    const values = Object.fromEntries(new FormData(checkForm));
    const payload = { ...values, backend: values.backend || null, model: values.model || null,
      reason: values.reason || null, codex_config: values.codex_config || null };
    invalidate();
    const reading = sequence;
    checkButton.disabled = true;
    checkStatus.replaceChildren(empty("正在核对完整 input 与当前后端准入…"));
    try {
      const admission = await api(`${base}/composition-inputs/check`, payload);
      if (!active() || reading !== sequence) return;
      selected = { payload, admission };
      runFields.disabled = false;
      checkStatus.replaceChildren(panel("当前只读准入已检查", "下方是原 owner 的角色、requested／actual binding、资料身份与能力范围。只读工具限制不是 OS 隔离；检查不授权正式任务。", pre(admission)));
    } catch (error) {
      if (active() && reading === sequence) checkStatus.replaceChildren(panel("只读准入检查失败", error.message));
    } finally {
      if (active() && reading === sequence) checkButton.disabled = false;
    }
  }

  async function invoke() {
    if (!active() || running || !selected) return;
    const selection = selected;
    const timeout = Number(new FormData(runForm).get("timeout"));
    running = true;
    checkFields.disabled = runFields.disabled = true;
    attempted.textContent = `上次明确提交：${selection.payload.directory} · ${selection.payload.input_digest} · ${timeout} 秒。原后端参数见下方；页面变化不取消已发起的调用。`;
    callStatus.replaceChildren(pre({ ...selection.payload, timeout }), empty("原 owner 正在保存输入并调用单叶；可以明确读取原调用记录。"));
    try {
      const run = await api(`${base}/composition-inputs/run`, { ...selection.payload, timeout });
      if (!active()) return;
      callStatus.replaceChildren(panel(selected === selection ? "单叶调用已返回原记录" : "上次输入的单叶调用已返回",
        "请核对原 status、result 路径／SHA及实际后端；进程成功不等于质量通过或候选采用。", status(run.status), pre(run), row(resultAction(run))));
    } catch (error) {
      if (active()) callStatus.replaceChildren(panel("单叶调用未获确认", error.message,
        "没有自动重发。先读取原调用记录，核对上次 input 与后端；网络错误不证明没有运行。"));
    } finally {
      running = false;
      if (active()) {
        checkFields.disabled = false;
        checkButton.disabled = false;
        runFields.disabled = !selected;
      }
    }
  }

  async function readRecords() {
    if (!active()) return;
    const reading = ++recordSequence;
    records.replaceChildren(empty("正在读取原调用记录…"));
    try {
      const observed = await api(`${base}/agent-runs`);
      if (!active() || reading !== recordSequence) return;
      records.replaceChildren(...(observed.length ? observed.map((run) => node("details", {},
        node("summary", {}, `${run.id} · ${run.role} · ${run.binding.tool} · ${run.status}`),
        table(["原身份", "记录"], [["输入 digest", run.input_digest ?? "普通角色调用"],
          ["result SHA256", run.result_sha256 ?? "尚无原结果"], ["开始", run.started], ["结束", run.finished ?? "未记录"]]),
        pre(run), row(resultAction(run), button("读取原诊断输出", async () => {
          try {
            const output = await api(`${base}/agent-runs/${encodeURIComponent(run.id)}/output`);
            if (active() && reading === recordSequence)
              records.append(panel(`原诊断 ${run.id}`, "诊断按原 owner 有界展示；完整候选使用 result 文件与 SHA，不使用截断诊断。", ...outputPanels(output, base, () => active() && reading === recordSequence)));
          } catch (error) {
            if (active() && reading === recordSequence) records.append(panel("原诊断读取失败", error.message));
          }
        })))) : [empty("原目录中没有调用记录。") ]));
    } catch (error) {
      if (active() && reading === recordSequence) records.replaceChildren(panel("原调用记录读取失败", error.message));
    }
  }

  checkForm.addEventListener("input", invalidate);
  checkForm.addEventListener("change", invalidate);
  modal("调用冻结的只读叶", view);
}
