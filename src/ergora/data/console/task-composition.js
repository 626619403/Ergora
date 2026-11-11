import { api } from "./api.js";
import { node, field, select, button, pre, empty, row } from "./ui.js";
import { bindingFields } from "./binding-fields.js";

// This editor collects choices; tasks._composition owns formal admission.
export function taskComposition({ tools, projectId, input, active, invalidate }) {
  const source = select([
    ["project", "项目角色（原入口）"], ["review", "完整 manifest · 仅组合审查"],
    ["delivery", "完整 manifest · 组合执行与审查"],
  ], "project", "agent_selection");
  const shaField = field("已保存组合的预览 SHA256", "manifest_preview_sha256", "", "text", {
    required: true, autocomplete: "off", spellcheck: "false",
  });
  const sha = shaField.querySelector("input");
  const status = node("div", { "aria-live": "polite" });
  const review = select([], "", "review_instance");
  const work = select([], "", "work_instance");
  review.required = work.required = true;
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
    node("label", {}, "审查工作流实例", review),
    node("label", {}, "审查资料模式", mode), workSection,
    node("label", {}, "执行与审查后端策略", diversity), diversityReason,
    node("p", {}, "执行者须显式覆盖后端并配置可信执行边界，静态定义不会自动授信。审查者可沿用定义或单独覆盖；每份覆盖需理由。服务端会重新检查模式、权限、全部成员和依赖。"),
    members,
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
    workSection.disabled = workSection.hidden = source.value !== "delivery";
    renderMembers();
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
        for (const target of [review, work]) target.replaceChildren(...select(choices, "").children);
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
    for (const target of [review, work]) target.replaceChildren();
    assigned = null;
    assignments.replaceChildren();
    settings.disabled = settings.hidden = true;
  }

  function memberEditor(leaf, writer) {
    const prefix = `member:${leaf.path}:`;
    const choices = tools[writer ? "implementer" : "reviewer"];
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
        node("legend", {}, `${writer ? "执行" : "审查"} · ${leaf.path}`),
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
        const writer = source.value === "delivery" && work.value && leaf.path.startsWith(work.value + "/");
        const reviewer = review.value && leaf.path.startsWith(review.value + "/");
        if (!writer && !reviewer) continue;
        const key = `${writer ? "work" : "review"}:${leaf.path}`;
        if (!memberEditors.has(key)) memberEditors.set(key, memberEditor(leaf, writer));
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
  sha.addEventListener("input", () => {
    lookupSequence++;
    settings.disabled = true;
    status.replaceChildren(empty("摘要已更改。已有配置仅保留显示，重新读取完整包后才可使用；不同包会重新选择实例。"));
  });
  review.addEventListener("change", renderMembers);
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
      if (source.value === "delivery") {
        if (!assigned) throw new Error("请从当前任务输入载入并分配工作单元。");
        composition.execution = {
          protocol: "work-units-v2", instance: work.value, mode: "workspace-task-mcp",
          assignments: Object.fromEntries(assigned.map(({ id, choice }) => [id, choice.value])),
        };
      }
      return composition;
    },
  };
}
