import { api } from "./api.js";
import { node, field, select, button, pre, empty, row, lines, checkbox } from "./ui.js";
import { bindingFields } from "./binding-fields.js";

// This editor collects choices; tasks._composition owns formal admission.
export function taskComposition({ tools, projectId, base, input, active, invalidate, prepare }) {
  const source = select([
    ["project", "项目角色（原入口）"], ["review", "完整 manifest · 仅组合审查"],
    ["delivery", "完整 manifest · 组合执行与审查"],
    ["native", "完整 manifest · 原生六阶段（Linux／WSL2）"],
  ], "project", "agent_selection");
  const shaField = field("已保存组合的预览 SHA256", "manifest_preview_sha256", "", "text", {
    required: true, autocomplete: "off", spellcheck: "false",
  });
  const sha = shaField.querySelector("input");
  const status = node("div", { "aria-live": "polite" });
  const review = select([], "", "review_instance");
  const work = select([], "", "work_instance");
  review.required = work.required = true;
  const native = select([], "", "native_instance");
  const inventory = select([], "", "inventory_instance");
  const plan = select([], "", "plan_instance");
  native.required = inventory.required = plan.required = true;
  const preparationMode = select([["task-mcp", "固定任务 MCP 资料读取"], ["text-only", "完整文本输入"]], "task-mcp", "preparation_mode");
  const repositoryPaths = field("准备阶段可读取的仓库相对路径（每行一个）", "repository_paths", "", "textarea", { required: true });
  const nativeSection = node("fieldset", {},
    node("legend", {}, "原生六阶段调用与准备"),
    node("p", {}, "选择普通父模板中的六阶段调用，以及其内部的盘点、计划、执行和审查实例。完整父链和全部阶段由服务端核对。原生执行支持 Linux／WSL2。"),
    node("label", {}, "六阶段工作流实例", native),
    node("label", {}, "盘点 Agent 实例", inventory),
    node("label", {}, "计划 Agent 实例", plan),
    node("label", {}, "准备资料模式", preparationMode), repositoryPaths,
  );
  const contextMode = select([
    ["inherited", "仅继承模板资料"], ["selected", "继承模板并追加项目资料"],
  ], "inherited", "context_selection");
  const rootVersion = field("派生根精确版本（须不同于原根）", "context_root_version", "", "text", { required: true, maxlength: 64 });
  const contextStatus = node("div", { "aria-live": "polite" });
  const contextCount = node("p", { className: "form-note", "aria-live": "polite" }, "已选 0 条记忆、0 个 Skill。");
  const contextChoices = node("fieldset", { disabled: true });
  const readContext = button("读取当前资料目录", loadContext);
  const contextFields = node("fieldset", { disabled: true, hidden: true },
    rootVersion, row(readContext), contextStatus, contextChoices,
  );
  const contextSection = node("fieldset", { disabled: true, hidden: true, className: "task-context-selection" },
    node("legend", {}, "追加项目记忆与活动 Skill"),
    node("p", {}, "全部父模板资料始终继承。追加资料不会扩大权限。目录是读取时快照；授权准备与后续准入会重新核来源和完整附件，失效或超出容量会明确拒绝。带 Skill 的成员需使用受支持的任务 MCP 资料模式。"),
    node("label", {}, "本任务资料来源", contextMode), contextFields,
  );
  let contextSequence = 0;
  let contextReady = false;
  let memoryChoices = [];
  let skillChoices = [];
  const budgetSection = node("fieldset", {},
    node("legend", {}, "总任务预算"),
    node("p", {}, "填写总时间、预留清理时间和模型调用次数。预算由服务端核对；授权准备后开始计时，预览和重读不会重置预算。"),
    field("总时间（秒）", "wall_seconds", "", "number", { required: true, min: 2, step: 1 }),
    field("清理时间（秒）", "cleanup_seconds", "", "number", { required: true, min: 1, step: 1 }),
    field("模型调用次数上限", "model_invocations", "", "number", { required: true, min: 1, step: 1 }),
    row(button("准备原生六阶段", prepare)),
  );
  const mode = select([["task-mcp", "固定任务 MCP 资料读取"], ["text-only", "完整文本输入"]], "task-mcp", "review_mode");
  const diversity = select([
    ["prefer-distinct", "优先不同后端 · 同后端需理由"], ["require-distinct", "必须不同后端"],
    ["allow-same", "允许相同后端"],
  ], "prefer-distinct", "diversity_policy");
  const diversityReason = field("后端差异策略说明（同后端回退时填写）", "diversity_reason", "", "textarea", { maxlength: 2000 });
  const assignments = node("div");
  let assigned = null;
  let manifest = null;
  let lookupSequence = 0;
  const memberEditors = new Map();
  let visibleMembers = [];
  const members = node("div", { className: "composition-members" });
  const workSection = node("fieldset", {},
    node("legend", {}, "执行子流程与工作单元"),
    node("label", {}, "执行工作流实例", work),
    node("p", {}, "选择执行子流程后，从当前任务输入载入工作单元，再逐个分配实例。输入和依赖由服务端按原 work_units 合同核对。"),
    button("从当前输入载入工作单元", loadAssignments), assignments,
  );
  const settings = node("fieldset", { disabled: true, hidden: true },
    node("legend", {}, "正式任务组合配置"),
    nativeSection, contextSection,
    node("label", {}, "审查工作流实例", review),
    node("label", {}, "审查资料模式", mode), workSection,
    node("label", {}, "执行与审查后端策略", diversity), diversityReason,
    node("p", {}, "执行者须显式覆盖后端并配置可信执行边界，静态定义不会自动授信。审查者可沿用定义或单独覆盖；每份覆盖需理由。服务端会重新检查模式、权限、全部成员和依赖。"),
    members, budgetSection,
  );
  const composition = node("fieldset", { disabled: true, hidden: true },
    node("legend", {}, "读取完整组合"),
    node("p", {}, "在定义库保存当前预览为完整 manifest，再复制其预览 SHA256 到这里。读取只核包身份；正式任务预览会重新准入。"),
    shaField, row(button("读取完整 manifest", loadManifest)), status, settings,
  );
  const element = node("div", {}, node("label", {}, "本任务 Agent 来源", source), composition);

  function applySource() {
    lookupSequence++;
    composition.disabled = composition.hidden = source.value === "project";
    workSection.disabled = workSection.hidden = !["delivery", "native"].includes(source.value);
    nativeSection.disabled = nativeSection.hidden = source.value !== "native";
    budgetSection.disabled = budgetSection.hidden = source.value !== "native";
    contextSection.disabled = contextSection.hidden = source.value !== "native";
    resetContext();
    renderMembers();
  }

  function resetContext() {
    contextSequence++;
    contextReady = false;
    contextChoices.disabled = true;
    readContext.disabled = false;
    contextFields.disabled = contextFields.hidden = contextMode.value !== "selected";
    contextStatus.replaceChildren(empty("读取当前资料目录后，明确选择精确修订。已有目录仅保留显示。"));
  }

  async function loadContext() {
    if (!active() || source.value !== "native" || contextMode.value !== "selected" || readContext.disabled) return;
    resetContext();
    const reading = contextSequence;
    readContext.disabled = true;
    invalidate();
    contextStatus.replaceChildren(empty("正在读取当前项目资料…"));
    try {
      const [catalog, heads] = await Promise.all([api(`${base}/memory-catalog`), api(`${base}/skills/heads`)]);
      if (!active() || reading !== contextSequence) return;
      memoryChoices = catalog.records.map(({ record, validity }, index) => {
        const label = checkbox(`${record.id} · 修订 ${record.revision} · ${{ valid: "有效快照", expired: "已到期", deleted: "已删除" }[validity]}`, `context-memory:${index}`);
        const choice = label.querySelector("input");
        choice.disabled = validity !== "valid";
        return { selection: { id: record.id, revision: record.revision }, choice,
          element: node("div", {}, label,
            node("details", {}, node("summary", {}, "完整记忆正文与来源"),
              pre({ text: record.text, source: record.source, expires_at: record.expires_at, validity }))) };
      });
      skillChoices = heads.active.map((head, index) => {
        const label = checkbox(`${head.name} · 修订 ${head.revision}`, `context-skill:${index}`);
        return { selection: { name: head.name, digest: head.digest, revision: head.revision }, choice: label.querySelector("input"),
          element: node("div", {}, label, pre(head)) };
      });
      contextChoices.replaceChildren(
        node("legend", {}, "明确选择要追加的资料"),
        contextCount,
        node("h3", {}, "项目记忆"),
        ...(memoryChoices.length ? memoryChoices.map((item) => item.element) : [empty("项目没有记忆记录。")]),
        node("h3", {}, "活动 Skill"),
        ...(skillChoices.length ? skillChoices.map((item) => item.element) : [empty("项目没有活动 Skill。")]),
      );
      contextChoices.disabled = false;
      contextReady = true;
      contextCount.textContent = "已选 0 条记忆、0 个 Skill。";
      contextStatus.replaceChildren(node("p", {}, `记忆观察时刻：${catalog.observed_at}。本次读取 ${memoryChoices.length} 条记忆、${skillChoices.length} 个活动 Skill；重新读取会清空本次勾选，须重新选择。`));
    } catch (error) {
      if (active() && reading === contextSequence)
        contextStatus.replaceChildren(empty(`资料目录读取失败：${error.message}。已有选择仅保留显示，重新读取成功前不能使用。`));
    } finally {
      if (active() && reading === contextSequence) readContext.disabled = false;
    }
  }

  async function loadManifest() {
    if (!active()) return;
    const reading = ++lookupSequence;
    const digest = sha.value;
    const selectedSource = source.value;
    settings.disabled = true;
    invalidate();
    status.replaceChildren(empty("正在核验完整包…"));
    try {
      const checked = await api(`/api/composition/manifests/${encodeURIComponent(digest)}?material=true`);
      if (!active() || reading !== lookupSequence || sha.value !== digest || source.value !== selectedSource) return;
      if (manifest?.digest !== checked.digest) {
        clearManifest();
        const choices = [["", "选择精确工作流实例…"], ...checked.composition.instances
          .filter((item) => item.kind === "workflow").map((item) => [item.path, `${item.path} · ${item.ref.id}@${item.ref.version}`])];
        for (const target of [review, work, native]) target.replaceChildren(...select(choices, "").children);
        const leaves = [["", "选择精确 Agent 实例…"], ...checked.composition.instances
          .filter((item) => item.kind === "agent").map((item) => [item.path, `${item.path} · ${item.role}`])];
        for (const target of [inventory, plan]) target.replaceChildren(...select(leaves, "").children);
      }
      manifest = checked;
      settings.disabled = settings.hidden = false;
      status.replaceChildren(node("p", {}, `完整包已核验：${checked.manifest.root.id}@${checked.manifest.root.version}`),
        pre({ preview_sha256: checked.manifest.preview_sha256, manifest_digest: checked.digest }));
    } catch (error) {
      if (active() && reading === lookupSequence)
        status.replaceChildren(empty(`完整包读取失败：${error.message}。原任务输入及已有配置保持，核对摘要并重读前不可使用旧配置。`));
    }
  }

  function clearManifest() {
    manifest = null;
    memberEditors.clear();
    visibleMembers = [];
    members.replaceChildren();
    for (const target of [review, work, native, inventory, plan]) target.replaceChildren();
    assigned = null;
    assignments.replaceChildren();
    settings.disabled = settings.hidden = true;
  }

  function memberEditor(leaf, role) {
    const writer = role === "work";
    const prefix = `member:${leaf.path}:`;
    const choices = tools[leaf.role];
    const choice = select([
      ["", writer ? "请选择覆盖后端及执行边界…" : `沿用定义 · ${leaf.backend_request.tool}`],
      ...choices.map((item) => [item.tool, item.supported === false ? `${item.tool} · WSL2/Linux` : item.tool]),
    ], "", prefix + "tool");
    choice.required = writer;
    const reason = field("覆盖理由", prefix + "reason", "", "textarea", { required: true, maxlength: 2000 });
    const options = node("fieldset", { disabled: true, hidden: true });
    let editor;
    choice.addEventListener("change", () => {
      editor = null;
      options.disabled = options.hidden = !choice.value;
      if (!choice.value) { options.replaceChildren(); return; }
      const component = choices.find((item) => item.tool === choice.value);
      // Writers must choose their binding explicitly, including any trust field.
      const current = !writer && leaf.backend_request.tool === choice.value ? leaf.backend_request : {};
      editor = bindingFields(component, current, { projectId, prefix });
      options.replaceChildren(editor.element, reason);
    });
    return {
      element: node("fieldset", { "data-member-path": leaf.path },
        node("legend", {}, `${{ work: "执行", review: "审查", preparation: "准备" }[role]} · ${leaf.path}`),
        node("details", {}, node("summary", {}, "定义请求的后端"), pre(leaf.backend_request)),
        node("label", {}, "本实例后端", choice), options),
      read() {
        if (!choice.value) {
          if (writer) throw new Error(`请为执行者 ${leaf.path} 显式选择后端和执行边界。`);
          return null;
        }
        return { binding: editor.read(), reason: reason.querySelector("textarea").value };
      },
    };
  }

  function renderMembers() {
    visibleMembers = [];
    if (manifest && source.value !== "project") {
      for (const leaf of manifest.composition.instances.filter((item) => item.kind === "agent")) {
        const writer = ["delivery", "native"].includes(source.value) && work.value && leaf.path.startsWith(work.value + "/");
        const reviewer = review.value && leaf.path.startsWith(review.value + "/");
        const preparing = source.value === "native" && [inventory.value, plan.value].includes(leaf.path);
        if (!writer && !reviewer && !preparing) continue;
        const role = writer ? "work" : reviewer ? "review" : "preparation";
        const key = `${role}:${leaf.path}`;
        if (!memberEditors.has(key)) memberEditors.set(key, memberEditor(leaf, role));
        visibleMembers.push({ path: leaf.path, editor: memberEditors.get(key) });
      }
    }
    members.replaceChildren(...visibleMembers.map((item) => item.editor.element));
  }

  function loadAssignments() {
    if (!active() || !manifest) return;
    invalidate();
    try {
      const units = input().work_units;
      if (!Array.isArray(units)) throw new Error("当前输入须含 work_units 数组。");
      if (!work.value) throw new Error("先选择执行工作流实例。");
      const choices = [["", "选择执行 Agent 实例…"], ...manifest.composition.instances
        .filter((item) => item.kind === "agent" && item.path.startsWith(work.value + "/"))
        .map((item) => [item.path, item.path])];
      const previous = new Map((assigned ?? []).map(({ id, choice }) => [id, choice.value]));
      const loaded = units.map((unit) => {
        const choice = select(choices, previous.get(unit.id) ?? "", `unit:${unit.id}`);
        choice.required = true;
        return { id: unit.id, choice };
      });
      assignments.replaceChildren(...loaded.map((item) => node("label", {}, `工作单元 ${item.id}`, item.choice)));
      assigned = loaded;
    } catch (error) {
      assignments.prepend(node("p", { role: "alert" }, `载入失败：${error.message} 已有输入及分配保持。`));
    }
  }

  source.addEventListener("change", applySource);
  contextMode.addEventListener("change", resetContext);
  contextChoices.addEventListener("change", () => {
    contextCount.textContent = `已选 ${memoryChoices.filter((item) => item.choice.checked).length} 条记忆、${skillChoices.filter((item) => item.choice.checked).length} 个 Skill。`;
  });
  sha.addEventListener("input", () => {
    lookupSequence++;
    settings.disabled = true;
    status.replaceChildren(empty("摘要已更改。已有配置仅保留显示，重新读取完整包后才可使用；不同包会重新选择实例。"));
  });
  review.addEventListener("change", renderMembers);
  inventory.addEventListener("change", renderMembers);
  plan.addEventListener("change", renderMembers);
  work.addEventListener("change", () => {
    assigned = null;
    assignments.replaceChildren(empty("执行子流程已更改，请重新载入当前工作单元。"));
    renderMembers();
  });
  applySource();
  return {
    element,
    read() {
      if (source.value === "project") return null;
      if (!manifest || settings.disabled || manifest.manifest.preview_sha256 !== sha.value)
        throw new Error("请先按当前预览 SHA256 读取完整 manifest。");
      const backend_overrides = Object.fromEntries(visibleMembers.flatMap(({ path, editor }) => {
        const override = editor.read();
        return override ? [[path, override]] : [];
      }));
      const composition = {
        manifest: manifest.path, manifest_digest: manifest.digest, review_instance: review.value,
        mode: mode.value, review_protocol: "dag-v1", backend_overrides,
        diversity: { policy: diversity.value },
      };
      const reason = diversityReason.querySelector("textarea").value;
      if (reason) composition.diversity.reason = reason;
      if (["delivery", "native"].includes(source.value)) {
        if (!assigned) throw new Error("请从当前任务输入载入并分配工作单元。");
        composition.execution = {
          protocol: "work-units-v2", instance: work.value, mode: "workspace-task-mcp",
          assignments: Object.fromEntries(assigned.map(({ id, choice }) => [id, choice.value])),
        };
      }
      if (source.value === "native") {
        composition.native = { protocol: "six-stage-v1", instance: native.value };
        composition.preparation = {
          protocol: "preparation-v1", inventory: inventory.value, plan: plan.value,
          mode: preparationMode.value,
          repository_paths: lines(repositoryPaths.querySelector("textarea").value),
        };
        const budget = Object.fromEntries([...budgetSection.querySelectorAll("input")]
          .map((item) => [item.name, item.valueAsNumber]));
        if (contextMode.value === "selected") {
          if (!contextReady || contextChoices.disabled) throw new Error("请读取当前资料目录并明确选择本次资料。");
          return { composition, budget, context: {
            root_version: rootVersion.querySelector("input").value,
            memories: memoryChoices.filter((item) => item.choice.checked && !item.choice.disabled).map((item) => item.selection),
            skills: skillChoices.filter((item) => item.choice.checked).map((item) => item.selection),
          } };
        }
        return { composition, budget };
      }
      return { composition };
    },
  };
}
