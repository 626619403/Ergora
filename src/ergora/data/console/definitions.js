import { api } from "./api.js";
import { app } from "./state.js";
import { node, button, pre, heading, panel, empty, row, select, field, lines, badge, download, table } from "./ui.js";

// Library assets belong to the control directory, independently of project selection.
const library = {
  controlDirectory: null, started: false, loading: false, installing: null, installRequest: 0, error: "", message: "",
  agents: [], workflows: [], presets: [], request: 0,
  selection: null, detail: null, detailLoading: false, detailError: "", detailRequest: 0,
  grant: "", preview: null, previewLoading: false, previewError: "", previewRequest: 0,
  restoreSelection: null,
};
const selections = new Map();
const currentLibrary = (home) => home === library.controlDirectory && home === app.bootstrap?.state_directory;
const editors = new Map();
const textOf = (value) => JSON.stringify(value, null, 2) + "\n";
const referenceText = ({ kind, id, version, digest }) => JSON.stringify({ kind, id, version, digest });
const editorKey = (home, kind, base) => JSON.stringify(["ergora-definition-editor-v1", home, kind, base.id, base.version, base.digest]);
const currentEditor = () => library.detail && editors.get(editorKey(library.controlDirectory, library.selection.kind,
  { ...library.selection, digest: library.detail.digest }));
const pendingText = (current, except) => ["json", "yaml"].some((format) => format !== except && current.texts[format] !== current.appliedTexts[format]);
const pendingResources = (current) => current.fileDraft !== null || current.resourceBuffer !== null;
const pending = (current) => pendingText(current) || current.formBuffer !== null || pendingResources(current);
const workingResources = (current) => current.resourceBuffer ?? current.resourceChanges ?? { schema_version: 1, operations: [] };
const editorBuffer = (current) => ({ version: 2, home: current.home, kind: current.kind, base: current.base,
  definition: current.definition, texts: current.texts, appliedTexts: current.appliedTexts,
  formBuffer: current.formBuffer, selectedNode: current.selectedNode, publication: current.publication,
  resourceChanges: current.resourceChanges, acceptedCandidate: current.acceptedCandidate,
  resourceBuffer: current.resourceBuffer, fileDraft: current.fileDraft });
const resourceByteLimit = 10_000_000;

function base64Size(value) {
  if (typeof value !== "string" || value.length > Math.ceil(resourceByteLimit / 3) * 4 || value.length % 4 ||
      !/^[A-Za-z0-9+/]*={0,2}$/.test(value) || (value && btoa(atob(value.slice(-4))) !== value.slice(-4)))
    throw new Error("资源字节不是完整的标准 base64");
  return value.length / 4 * 3 - (value.endsWith("==") ? 2 : value.endsWith("=") ? 1 : 0);
}

function resourceBudget(operations, replacement) {
  let count = replacement ? 1 : 0, bytes = replacement?.bytes || 0;
  for (const item of operations) {
    if (replacement && item.path === replacement.path) continue;
    count++;
    if (item.op === "write") bytes += base64Size(item.content_base64);
    if (count > 1500 || bytes > resourceByteLimit) break;
  }
  if (count > 1500 || bytes > resourceByteLimit)
    throw new Error("完整资源操作超过 1500 项或 10MB 写字节；原缓冲已保留，请使用 CLI --resources。");
  return bytes;
}

function resourceBytes(value) {
  base64Size(value);
  return Uint8Array.from(atob(value), (char) => char.charCodeAt(0));
}

function resourceBase64(bytes) {
  const parts = [];
  for (let offset = 0; offset < bytes.length; offset += 8192)
    parts.push(String.fromCharCode(...bytes.subarray(offset, offset + 8192)));
  return btoa(parts.join(""));
}

function resourceTextBytes(text, limit = resourceByteLimit) {
  const bytes = new Uint8Array(Math.min(limit + 1, text.length * 3));
  const { read, written } = new TextEncoder().encodeInto(text, bytes);
  if (read !== text.length || written > limit)
    throw new Error("完整 UTF-8 文本超过资源写预算；原草稿已保留，请使用 CLI --resources。");
  const result = bytes.subarray(0, written);
  if (new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(result) !== text)
    throw new Error("文本无法无损编码为 UTF-8；原草稿已保留。");
  return result;
}

function checkResourceChanges(value) {
  if (!value || value.schema_version !== 1 || Object.keys(value).sort().join() !== "operations,schema_version" ||
      !Array.isArray(value.operations) || value.operations.length > 1500)
    throw new Error("资源操作缓冲格式无法读取");
  for (const item of value.operations) {
    if (!item || typeof item.path !== "string" || !["write", "delete", "mkdir"].includes(item.op) ||
        Object.keys(item).some((key) => !["op", "path", ...(item.op === "write" ? ["content_base64", "executable_bits"] : [])].includes(key)) ||
        (item.op === "write" && typeof item.content_base64 !== "string") ||
        (Object.hasOwn(item, "executable_bits") && (!Number.isInteger(item.executable_bits) || item.executable_bits < 0 || item.executable_bits > 0o111 || (item.executable_bits & ~0o111))))
      throw new Error("资源操作缓冲格式无法读取");
  }
  resourceBudget(value.operations);
}

function checkResourceDraft(value, operations) {
  if (!value || Object.keys(value).sort().join() !== "content,executableBits,op,path" ||
      !["write", "delete", "mkdir"].includes(value.op) || typeof value.path !== "string" ||
      typeof value.executableBits !== "string" || !value.content ||
      !["text", "base64"].includes(value.content.encoding) ||
      Object.keys(value.content).sort().join() !== "encoding,value" || typeof value.content.value !== "string")
    throw new Error("文件草稿格式无法读取");
  const used = resourceBudget(operations, { path: value.path, bytes: 0 });
  const limit = value.op === "write" ? resourceByteLimit - used : resourceByteLimit;
  if (value.content.encoding === "base64") {
    if (base64Size(value.content.value) > limit) throw new Error("文件草稿超过完整资源写预算；请使用 CLI --resources。");
  } else resourceTextBytes(value.content.value, limit);
}

function sameValue(left, right) {
  if (left === right) return true;
  if (!left || !right || typeof left !== "object" || typeof right !== "object" || Array.isArray(left) !== Array.isArray(right)) return false;
  return Object.keys(left).length === Object.keys(right).length && Object.keys(left).every((key) => Object.hasOwn(right, key) && sameValue(left[key], right[key]));
}

function rememberEditor(current) {
  if (editors.get(current.key) !== current || current.restoreError) return;
  try {
    sessionStorage.setItem(current.key, JSON.stringify(editorBuffer(current)));
    current.storageError = "";
  } catch (error) {
    current.storageError = `浏览器未能保存编辑缓冲：${error.message}。请下载缓冲后再离开页面。`;
  }
}

function editorSnapshot(current) {
  const text = textOf(current.definition);
  // Pending raw text belongs to the checkpoint, never to applied undo history.
  const texts = { ...current.appliedTexts };
  const resources = JSON.stringify({ resourceChanges: current.resourceChanges, acceptedCandidate: current.acceptedCandidate });
  return { text, texts, canonicalTexts: { ...current.canonicalTexts }, resources, selected: current.selectedNode,
    bytes: new TextEncoder().encode(text + texts.json + texts.yaml + current.canonicalTexts.json + current.canonicalTexts.yaml + resources).length };
}

async function restoreEditor(kind, detail, home) {
  const base = { id: detail.definition.id, version: detail.definition.version, digest: detail.digest };
  const key = editorKey(home, kind, base);
  if (editors.has(key)) return;
  let saved, raw, storageError = "";
  try { raw = sessionStorage.getItem(key); }
  catch (error) { storageError = `浏览器无法读取编辑缓冲：${error.message}。请下载本次编辑后再离开页面。`; }
  if (raw !== null && raw !== undefined) {
    try {
      saved = JSON.parse(raw);
      // Validate only our persisted UI shape; definition admission stays with the library.
      const object = (value) => value && typeof value === "object" && !Array.isArray(value);
      const resourceKeys = ["resourceChanges", "acceptedCandidate", "resourceBuffer", "fileDraft"];
      const legacy = saved.version === 1 && !resourceKeys.some((name) => Object.hasOwn(saved, name));
      if (!(legacy || (saved.version === 2 && resourceKeys.every((name) => Object.hasOwn(saved, name)))) ||
          saved.home !== home || saved.kind !== kind || textOf(saved.base) !== textOf(base) ||
          !object(saved.definition) || !object(saved.texts) || !object(saved.appliedTexts) ||
          !["json", "yaml"].every((format) => typeof saved.texts[format] === "string" && typeof saved.appliedTexts[format] === "string") ||
          !Number.isInteger(saved.selectedNode) || saved.selectedNode < 0 ||
          !(saved.formBuffer === null || (object(saved.formBuffer) && Object.values(saved.formBuffer).every((value) => typeof value === "string"))) ||
          !(saved.publication === null || (object(saved.publication) && ["id", "version", "digest"].every((key) => typeof saved.publication[key] === "string"))) ||
          !sameValue(JSON.parse(saved.appliedTexts.json), saved.definition)) throw new Error("编辑缓冲格式或已应用正文无法读取");
      if (legacy) Object.assign(saved, { resourceChanges: null, acceptedCandidate: null, resourceBuffer: null, fileDraft: null });
      for (const name of ["resourceChanges", "resourceBuffer"]) if (saved[name] !== null) checkResourceChanges(saved[name]);
      if (saved.fileDraft !== null) checkResourceDraft(saved.fileDraft,
        (saved.resourceBuffer ?? saved.resourceChanges ?? { operations: [] }).operations);
      const candidate = saved.acceptedCandidate;
      if (candidate !== null && (!saved.resourceChanges || !object(candidate) ||
          Object.keys(candidate).sort().join() !== "digest,directories" || !/^[0-9a-f]{64}$/.test(candidate.digest) ||
          !Array.isArray(candidate.directories) || candidate.directories.length > 500 ||
          !candidate.directories.every((name) => typeof name === "string") || new Set(candidate.directories).size !== candidate.directories.length))
        throw new Error("资源接受身份无法读取");
    } catch (error) {
      editors.set(key, { key, home, kind, base, restoreError: error.message, raw });
      return;
    }
  }
  let converted;
  try {
    converted = await api("/api/definition-documents/convert", { text: saved ? saved.appliedTexts.json : textOf(detail.definition) });
    if (saved) {
      const yaml = await api("/api/definition-documents/convert", { text: saved.appliedTexts.yaml, format: "yaml" });
      if (!sameValue(converted.definition, yaml.definition)) throw new Error("缓冲内已应用的 JSON / YAML 正文不一致");
    }
  } catch (error) {
    if (!saved) throw error;
    if (!editors.has(key)) editors.set(key, { key, home, kind, base, restoreError: error.message, raw });
    return;
  }
  // A newer selection may have opened this same version during conversion.
  if (editors.has(key)) return;
  const current = { key, home, kind, base, definition: converted.definition,
    texts: saved ? saved.texts : { json: converted.json, yaml: converted.yaml },
    appliedTexts: saved ? saved.appliedTexts : { json: converted.json, yaml: converted.yaml },
    canonicalTexts: { json: converted.json, yaml: converted.yaml },
    formBuffer: saved?.formBuffer || null, selectedNode: saved?.selectedNode || 0, publication: saved?.publication || null,
    resourceChanges: saved?.resourceChanges ?? null, acceptedCandidate: saved?.acceptedCandidate ?? null,
    resourceBuffer: saved?.resourceBuffer ?? null, fileDraft: saved?.fileDraft ?? null, resourcePreview: null,
    revision: 0, sequence: 0, request: null, error: "", message: "", check: null, storageError,
    expanded: { fields: true, json: true, yaml: false }, history: [], historyIndex: 0 };
  if (current.formBuffer) {
    const defaults = formValues(current);
    if (!defaults || Object.keys(defaults).length !== Object.keys(current.formBuffer).length ||
        !Object.keys(defaults).every((name) => Object.hasOwn(current.formBuffer, name))) {
      editors.set(key, { key, home, kind, base, restoreError: "字段缓冲无法归属当前正文", raw });
      return;
    }
  }
  current.history.push(editorSnapshot(current));
  editors.set(key, current);
}

function touchEditor(current, acceptedCandidate = null) {
  current.revision++;
  current.check = null;
  current.resourcePreview = null;
  current.acceptedCandidate = acceptedCandidate;
  current.error = "";
  current.message = "";
  rememberEditor(current);
}

function applyEditor(current, converted, format, original, resources) {
  current.history[current.historyIndex].selected = current.selectedNode;
  const unchanged = sameValue(current.definition, converted.definition);
  const texts = unchanged ? { ...current.texts } : { json: converted.json, yaml: converted.yaml };
  if (format) texts[format] = original;
  if (!unchanged) current.canonicalTexts = { json: converted.json, yaml: converted.yaml };
  else if (format) current.canonicalTexts[format] = converted[format];
  current.definition = converted.definition;
  current.texts = texts;
  current.appliedTexts = { ...texts };
  current.formBuffer = null;
  if (resources) {
    current.resourceChanges = resources.changes;
    current.acceptedCandidate = resources.candidate;
    current.resourceBuffer = null;
  } else current.acceptedCandidate = null;
  current.selectedNode = Array.isArray(current.definition.nodes) && current.definition.nodes.length
    ? Math.min(current.selectedNode, current.definition.nodes.length - 1) : 0;
  const snapshot = editorSnapshot(current);
  const previous = current.history[current.historyIndex];
  if (snapshot.text !== previous.text || snapshot.texts.json !== previous.texts.json || snapshot.texts.yaml !== previous.texts.yaml || snapshot.resources !== previous.resources) {
    current.history.splice(current.historyIndex + 1);
    current.history.push(snapshot);
    let bytes = current.history.reduce((total, item) => total + item.bytes, 0);
    while (current.history.length > 1 && (current.history.length > 50 || bytes > 4 * 1024 * 1024))
      bytes -= current.history.shift().bytes;
    current.historyIndex = current.history.length - 1;
  } else current.history[current.historyIndex] = snapshot;
  touchEditor(current, current.acceptedCandidate);
}

async function editDefinition(current, operation, render, work) {
  if (!currentLibrary(current.home) || currentEditor() !== current) { redraw(render); return; }
  if (current.request) return;
  const revision = current.revision, sequence = ++current.sequence;
  current.request = { operation, sequence };
  current.error = "";
  current.message = "";
  redraw(render);
  try {
    await work(revision);
  } catch (error) {
    if (editors.get(current.key) === current) current.error = error.message + (operation === "publish"
      ? "。发布结果可能未知；可用相同基准和正文显式重试以核对，系统不会自动重发。" : "");
  } finally {
    if (editors.get(current.key) === current && current.request?.sequence === sequence) {
      current.request = null;
      rememberEditor(current);
      if (currentLibrary(current.home) && currentEditor() === current) redraw(render);
    }
  }
}

async function convertCandidate(current, render, { text, format, rename }) {
  await editDefinition(current, "convert", render, async (revision) => {
    let converted = await api("/api/definition-documents/convert", { text, format: format || "json" });
    if (rename && rename.from !== rename.to) {
      const definition = converted.definition;
      if (definition.nodes.filter((item) => item.id === rename.to).length > 1) throw new Error("实例 ID 已存在，不能合并引用");
      for (const item of definition.nodes) {
        item.depends_on = item.depends_on.map((id) => id === rename.from ? rename.to : id);
        for (const binding of Object.values(item.inputs || {}))
          if (binding?.node === rename.from) binding.node = rename.to;
      }
      for (const binding of Object.values(definition.outputs || {}))
        if (binding?.node === rename.from) binding.node = rename.to;
      converted = await api("/api/definition-documents/convert", { text: textOf(definition) });
    }
    if (editors.get(current.key) !== current) return;
    if (current.revision !== revision) {
      current.message = "转换期间有较新编辑；原文已保留，请重新应用。";
      return;
    }
    if (!confirmDefinitionSync(current, converted.definition, format)) {
      current.message = "未应用修改；各处原文与字段缓冲均已保留。";
      return;
    }
    applyEditor(current, converted, format, text);
  });
}

function confirmDefinitionSync(current, definition, format) {
  const replaced = ["json", "yaml"].filter((name) => name !== format && current.texts[name] !== current.canonicalTexts[name]);
  return sameValue(current.definition, definition) || !replaced.length || window.confirm(
    `本次修改将重新生成 ${replaced.map((name) => name.toUpperCase()).join(" / ")} 原文，原注释和排版会被替换。要保留请取消并先下载原文；是否继续同步？`);
}

function revisionRequest(current, suffix, body) {
  if (new TextEncoder().encode(JSON.stringify(body)).length > 4_000_000)
    throw new Error("完整请求（含 base64）超过 4,000,000 字节；编辑缓冲已保留，请下载并使用 CLI --resources。");
  const { id, version } = current.base;
  return api(`/api/${current.kind}-definitions/${encodeURIComponent(id)}/${encodeURIComponent(version)}/revisions${suffix}`, body);
}

async function reviseDefinition(current, publish, render) {
  if (pending(current) || (current.resourceChanges !== null && current.acceptedCandidate === null)) return;
  const definition = structuredClone(current.definition);
  const resources = current.resourceChanges === null ? {} : {
    resource_changes: structuredClone(current.resourceChanges), accepted_candidate: structuredClone(current.acceptedCandidate),
  };
  await editDefinition(current, publish ? "publish" : "check", render, async (revision) => {
    const result = await revisionRequest(current, publish ? "" : "/check", { base_digest: current.base.digest, definition, ...resources });
    if (editors.get(current.key) !== current) return;
    if (publish) {
      current.publication = { id: result.definition.id, version: result.definition.version, digest: result.digest };
      current.message = `已发布 ${current.publication.id} @ ${current.publication.version}。` +
        (current.revision === revision ? "可明确以该版本继续编辑。" : "发布期间的较新编辑已保留，尚未发布。");
      if (currentLibrary(current.home)) await loadLibrary(render);
    } else {
      current.check = { revision, result };
      current.message = current.revision === revision ? "当前已应用正文和资源检查通过；尚未发布。" : "检查期间有较新编辑；请重新检查当前候选。";
    }
  });
}

const resourceReplyCurrent = (current, revision) => editors.get(current.key) === current && currentLibrary(current.home) &&
  currentEditor() === current && current.revision === revision;
const newFileDraft = () => ({ op: "write", path: "", executableBits: "", content: { encoding: "text", value: "" } });

async function previewResources(current, render) {
  if (pendingText(current) || current.formBuffer !== null || current.fileDraft !== null) return;
  const changes = structuredClone(workingResources(current)), definition = structuredClone(current.definition);
  await editDefinition(current, "preview-resources", render, async (revision) => {
    const result = await revisionRequest(current, "/preview-resources", { base_digest: current.base.digest, definition, resource_changes: changes });
    if (!resourceReplyCurrent(current, revision)) {
      current.message = "资源预览期间有较新编辑或切换；原缓冲已保留，请重新预览。";
      return;
    }
    current.resourcePreview = { revision, changes, result };
    current.message = "资源差异已预览；请核对并明确采用摘要，尚未应用或发布。";
  });
}

async function adoptResources(current, render) {
  const preview = current.resourcePreview;
  if (!preview || preview.revision !== current.revision || pendingText(current) || current.formBuffer !== null || current.fileDraft !== null) return;
  await editDefinition(current, "adopt-resources", render, async (revision) => {
    const converted = await api("/api/definition-documents/convert", { text: textOf(preview.result.definition) });
    if (!resourceReplyCurrent(current, revision) || current.resourcePreview !== preview) {
      current.message = "采用期间有较新编辑或切换；原缓冲已保留，请重新预览。";
      return;
    }
    if (!confirmDefinitionSync(current, converted.definition)) {
      current.message = "未采用资源摘要；原正文和完整操作缓冲均已保留。";
      return;
    }
    applyEditor(current, converted, null, null, { changes: preview.changes, candidate: preview.result.candidate });
    current.message = "正文、完整资源操作和接受身份已共同应用；请检查后再明确发布。";
  });
}

async function stageResource(current, render) {
  await editDefinition(current, "stage-resource", render, async () => {
    const draft = current.fileDraft;
    if (!draft) return;
    const operations = workingResources(current).operations;
    const used = resourceBudget(operations, { path: draft.path, bytes: 0 });
    const operation = { op: draft.op, path: draft.path };
    if (draft.op === "write") {
      if (draft.content.encoding === "text") operation.content_base64 = resourceBase64(resourceTextBytes(draft.content.value, resourceByteLimit - used));
      else {
        if (used + base64Size(draft.content.value) > resourceByteLimit)
          throw new Error("完整资源操作超过 10MB 写字节；原草稿已保留，请使用 CLI --resources。");
        operation.content_base64 = draft.content.value;
      }
      if (draft.executableBits.trim()) {
        if (!/^[01]{1,3}$/.test(draft.executableBits.trim())) throw new Error("执行位须为空或八进制 000–111（每位仅 0/1），例如 100。");
        operation.executable_bits = parseInt(draft.executableBits.trim(), 8);
      }
    }
    current.resourceBuffer = structuredClone({ schema_version: 1, operations: [...operations.filter((item) => item.path !== draft.path), operation] });
    current.fileDraft = null;
    touchEditor(current);
    current.message = "文件操作已暂存到完整工作集合；预览并采用摘要后才进入已应用历史。";
  });
}

async function uploadResource(current, file, render) {
  const draft = structuredClone(current.fileDraft || newFileDraft());
  const path = draft.path || file.name;
  await editDefinition(current, "upload-resource", render, async (revision) => {
    resourceBudget(workingResources(current).operations, { path, bytes: file.size });
    const bytes = new Uint8Array(await file.arrayBuffer());
    if (!resourceReplyCurrent(current, revision)) {
      current.message = "上传期间有较新编辑或切换；已有草稿保留，请重新选择文件。";
      return;
    }
    if (bytes.length !== file.size) throw new Error("上传文件的完整大小发生变化，未替换草稿。");
    current.fileDraft = { ...draft, op: "write", path, content: { encoding: "base64", value: resourceBase64(bytes) } };
    touchEditor(current);
    current.message = "完整上传字节已进入文件草稿；尚未暂存操作或应用。";
  });
}

async function readResource(current, path, edit, render) {
  if (edit && current.fileDraft !== null) return;
  const expected = library.detail.files[path];
  await editDefinition(current, "read-resource", render, async (revision) => {
    const { id, version, digest } = current.base;
    let bytes, offset = 0;
    do {
      const result = await api(`/api/${current.kind}-definitions/${encodeURIComponent(id)}/${encodeURIComponent(version)}/files/read`,
        { base_digest: digest, path, offset, limit: 65536 });
      if (!resourceReplyCurrent(current, revision)) {
        current.message = "读取期间有较新编辑或切换；片段未进入文件草稿，请重新读取。";
        return;
      }
      const size = base64Size(result.content_base64);
      if (!sameValue(result.base, { kind: current.kind, ...current.base }) || result.path !== path ||
          result.sha256 !== expected.sha256 || result.executable_bits !== expected.executable_bits ||
          !Number.isInteger(result.size_bytes) || result.size_bytes < 0 || result.size_bytes > resourceByteLimit ||
          result.offset !== offset || result.bytes_read !== size || size > 65536 || offset + size > result.size_bytes ||
          result.next_offset !== (offset + size < result.size_bytes ? offset + size : null) ||
          result.complete !== (offset === 0 && size === result.size_bytes) ||
          (size === 0 && result.size_bytes !== 0) || (bytes && bytes.length !== result.size_bytes))
        throw new Error("文件窗口身份、大小或连续性不一致；片段未进入编辑缓冲。");
      if (!bytes) {
        if (edit) resourceBudget(workingResources(current).operations, { path, bytes: result.size_bytes });
        bytes = new Uint8Array(result.size_bytes);
      }
      bytes.set(resourceBytes(result.content_base64), offset);
      offset += size;
      if (result.next_offset === null) break;
      current.message = `正在完整读取 ${path}：${offset} / ${bytes.length} 字节；片段不可编辑。`;
      redraw(render);
    } while (true);
    const digestBytes = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
    if (Array.from(digestBytes, (value) => value.toString(16).padStart(2, "0")).join("") !== expected.sha256)
      throw new Error("完整文件 SHA256 不一致，未进入编辑缓冲或下载。");
    if (!resourceReplyCurrent(current, revision)) return;
    if (!edit) {
      download(path.split("/").pop(), bytes, "application/octet-stream");
      current.message = `已下载原包完整文件 ${path}（${bytes.length} 字节）。`;
      return;
    }
    let content;
    try { content = { encoding: "text", value: new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes) }; }
    catch (error) {
      if (!(error instanceof TypeError)) throw error;
      content = { encoding: "base64", value: resourceBase64(bytes) };
    }
    current.fileDraft = { op: "write", path, executableBits: "", content };
    touchEditor(current);
    current.message = `完整文件已读入草稿（${bytes.length} 字节）；` + (content.encoding === "text" ? "严格 UTF-8，尚未暂存。" : "二进制字节原样保留，尚未暂存。");
  });
}

function synchronizeLibrary() {
  const home = app.bootstrap.state_directory;
  if (home === library.controlDirectory) return;
  if (library.selection) selections.set(library.controlDirectory, library.selection);
  library.request++;
  library.detailRequest++;
  library.previewRequest++;
  library.installRequest++;
  Object.assign(library, {
    controlDirectory: home, started: false, loading: false, installing: null, error: "", message: "",
    agents: [], workflows: [], presets: [], selection: null, detail: null, detailLoading: false, detailError: "",
    grant: "", preview: null, previewLoading: false, previewError: "", restoreSelection: selections.get(home) || null,
  });
}

function redraw(render) {
  if (app.tab === "definitions") render();
}

async function loadLibrary(render) {
  const home = library.controlDirectory;
  if (!currentLibrary(home)) return false;
  const selectionRequest = library.detailRequest;
  const request = ++library.request;
  library.loading = true;
  library.error = "";
  redraw(render);
  try {
    const [agents, workflows, presets] = await Promise.all([
      api("/api/agent-definitions"), api("/api/workflow-definitions"), api("/api/composition/presets"),
    ]);
    if (!currentLibrary(home) || request !== library.request) return false;
    Object.assign(library, { agents, workflows, presets });
    const selected = library.selection;
    if (selected && !library[selected.kind === "agent" ? "agents" : "workflows"].some(
      (item) => item.id === selected.id && item.version === selected.version,
    )) {
      library.detailRequest++;
      library.previewRequest++;
      Object.assign(library, { selection: null, detail: null, preview: null, detailLoading: false, previewLoading: false });
    }
    if (!library.selection && library.restoreSelection && selectionRequest === library.detailRequest) {
      const previous = library.restoreSelection;
      library.restoreSelection = null;
      if (library[previous.kind === "agent" ? "agents" : "workflows"].some(
        (item) => item.id === previous.id && item.version === previous.version,
      )) await openDefinition(previous.kind, previous, render);
    }
    return true;
  } catch (error) {
    if (currentLibrary(home) && request === library.request) library.error = error.message;
    return false;
  } finally {
    if (currentLibrary(home) && request === library.request) {
      library.loading = false;
      redraw(render);
    }
  }
}

async function openDefinition(kind, reference, render) {
  const home = library.controlDirectory;
  if (!currentLibrary(home)) { redraw(render); return; }
  const request = ++library.detailRequest;
  library.previewRequest++;
  Object.assign(library, {
    selection: { kind, id: reference.id, version: reference.version }, detail: null, detailLoading: true,
    detailError: "", grant: "", preview: null, previewLoading: false, previewError: "", restoreSelection: null,
  });
  selections.set(home, library.selection);
  redraw(render);
  try {
    const result = await api(`/api/${kind}-definitions/${encodeURIComponent(reference.id)}/${encodeURIComponent(reference.version)}`);
    if (!currentLibrary(home) || request !== library.detailRequest) return;
    await restoreEditor(kind, result, home);
    if (!currentLibrary(home) || request !== library.detailRequest) return;
    library.detail = result;
    if (kind === "workflow") library.grant = JSON.stringify({ schema_version: 1,
      permissions: result.definition.permissions, limits: result.definition.limits }, null, 2);
  } catch (error) {
    if (currentLibrary(home) && request === library.detailRequest) library.detailError = error.message;
  } finally {
    if (currentLibrary(home) && request === library.detailRequest) {
      library.detailLoading = false;
      redraw(render);
    }
  }
}

async function installPreset(identity, render) {
  if (library.installing) return;
  const home = library.controlDirectory, request = ++library.installRequest;
  if (!currentLibrary(home)) { redraw(render); return; }
  library.installing = identity;
  library.message = "";
  library.error = "";
  const selectionRequest = library.detailRequest;
  const previewRequest = library.previewRequest;
  redraw(render);
  try {
    const result = await api(`/api/composition/presets/${encodeURIComponent(identity)}/install`, {});
    if (!currentLibrary(home) || request !== library.installRequest) return;
    library.message = `${identity} 的精确版本已导入；后续可在任务中显式选择。`;
    const loaded = await loadLibrary(render);
    if (loaded && currentLibrary(home) && request === library.installRequest && selectionRequest === library.detailRequest && previewRequest === library.previewRequest)
      await openDefinition("workflow", result.root, render);
  } catch (error) {
    if (currentLibrary(home) && request === library.installRequest) library.error = error.message;
  } finally {
    if (currentLibrary(home) && request === library.installRequest) {
      library.installing = null;
      redraw(render);
    }
  }
}

async function previewDefinition(render) {
  const home = library.controlDirectory;
  if (!currentLibrary(home)) { redraw(render); return; }
  const request = ++library.previewRequest;
  const selected = library.selection;
  library.previewLoading = true;
  library.previewError = "";
  library.preview = null;
  redraw(render);
  try {
    const grant = JSON.parse(library.grant);
    const result = await api("/api/composition/preview", { id: selected.id, version: selected.version, grant });
    if (currentLibrary(home) && request === library.previewRequest) library.preview = result;
  } catch (error) {
    if (currentLibrary(home) && request === library.previewRequest) library.previewError = error.message;
  } finally {
    if (currentLibrary(home) && request === library.previewRequest) {
      library.previewLoading = false;
      redraw(render);
    }
  }
}

function formValues(current) {
  const definition = current.definition;
  const values = { version: definition.version, description: definition.description };
  if (typeof values.version !== "string" || typeof values.description !== "string") return null;
  const strings = (value) => Array.isArray(value) && value.every((item) => typeof item === "string");
  if (current.kind === "agent") {
    if (!strings(definition.roles) || !strings(definition.specialties) || !definition.backend || typeof definition.backend !== "object") return null;
    return { ...values, roles: definition.roles.join("\n"), specialties: definition.specialties.join("\n"), backend: textOf(definition.backend) };
  }
  if (!strings(definition.inputs) || !Array.isArray(definition.nodes) || !definition.nodes.length ||
      !definition.nodes.every((item) => item && typeof item.id === "string" && strings(item.depends_on) &&
        (item.ref ? ["agent", "workflow"].includes(item.ref.kind) &&
          ["id", "version", "digest"].every((key) => typeof item.ref[key] === "string") : item.join === "all"))) return null;
  const selected = definition.nodes[current.selectedNode];
  if (!selected) return null;
  Object.assign(values, { inputs: definition.inputs.join("\n"), outputs: textOf(definition.outputs),
    permissions: textOf(definition.permissions), limits: textOf(definition.limits),
    nodeId: selected.id, dependencies: selected.depends_on.join("\n") });
  if (selected.ref) Object.assign(values, { reference: referenceText(selected.ref), nodeInputs: textOf(selected.inputs) });
  if (selected.ref?.kind === "agent") {
    values.role = selected.role;
    values.nodePermissions = textOf(selected.permissions);
    if (definition.schema_version === 2) values.requirement = selected.review_requirement || "required";
  }
  return Object.values(values).every((value) => typeof value === "string") ? values : null;
}

// Raw JSON fields are spliced as text so the shared strict decoder sees duplicate keys.
function jsonObject(value, fragments) {
  return "{" + [...new Set([...Object.keys(value), ...Object.keys(fragments)])].map((key) =>
    JSON.stringify(key) + ":" + (Object.hasOwn(fragments, key) ? fragments[key] : JSON.stringify(value[key]))).join(",") + "}";
}

function formDocument(current, values) {
  const definition = structuredClone(current.definition);
  Object.assign(definition, { version: values.version, description: values.description });
  const fragments = {};
  if (current.kind === "agent") {
    definition.roles = lines(values.roles);
    definition.specialties = lines(values.specialties);
    fragments.backend = values.backend;
  } else {
    definition.inputs = lines(values.inputs);
    Object.assign(fragments, { outputs: values.outputs, permissions: values.permissions, limits: values.limits });
    const selected = definition.nodes[current.selectedNode];
    Object.assign(selected, { id: values.nodeId, depends_on: lines(values.dependencies) });
    const nodeFragments = {};
    if (selected.ref) Object.assign(nodeFragments, { ref: values.reference, inputs: values.nodeInputs });
    if (selected.ref?.kind === "agent") {
      selected.role = values.role;
      nodeFragments.permissions = values.nodePermissions;
      if (definition.schema_version === 2 && selected.role === "reviewer") selected.review_requirement = values.requirement;
      else delete selected.review_requirement;
    }
    fragments.nodes = "[" + definition.nodes.map((item, index) => index === current.selectedNode
      ? jsonObject(item, nodeFragments) : JSON.stringify(item)).join(",") + "]";
  }
  return jsonObject(definition, fragments);
}

function definitionForm(current, render, action, updateControls) {
  const defaults = formValues(current);
  if (!defaults) return empty("当前正文尚不能生成字段表单；请在 JSON / YAML 中修正后应用。检查与发布仍由定义库校验。");
  const values = current.formBuffer || defaults;
  const fields = node("form", { onsubmit: (event) => event.preventDefault() },
    field("新版本", "version", values.version), field("描述", "description", values.description, "textarea"));
  if (current.kind === "agent") {
    const roleTools = app.agentRoles.flatMap((role) => app.bootstrap.tools[role] || []);
    const tools = [...new Set(roleTools.map((item) => item.tool))];
    const choice = select(tools, current.definition.backend.tool, null);
    choice.setAttribute("aria-label", "后端基础请求");
    fields.append(field("职能（每行一个）", "roles", values.roles, "textarea"),
      field("专长（每行一个）", "specialties", values.specialties, "textarea"),
      field("后端请求 JSON", "backend", values.backend, "textarea", { className: "workflow-json", spellcheck: "false" }),
      row(choice, button("填入所选后端的基础请求", () => {
        fields.elements.backend.value = textOf({ tool: choice.value });
        fields.dispatchEvent(new Event("input", { bubbles: true }));
      })), node("p", {}, "填入基础请求会替换此字段；模型、选项和凭据变量引用可在 JSON 中补充。目录可选不代表已安装或认证。"));
  } else {
    const selected = current.definition.nodes[current.selectedNode];
    fields.append(field("工作流输入端口（每行一个）", "inputs", values.inputs, "textarea"),
      field("工作流输出绑定 JSON", "outputs", values.outputs, "textarea", { spellcheck: "false" }),
      field("根权限 JSON", "permissions", values.permissions, "textarea", { spellcheck: "false" }),
      field("根预算 JSON", "limits", values.limits, "textarea", { spellcheck: "false" }),
      field("实例 ID", "nodeId", values.nodeId), field("先行依赖（每行一个）", "dependencies", values.dependencies, "textarea"));
    if (selected.ref) {
      const available = library[selected.ref.kind === "agent" ? "agents" : "workflows"].map((item) => ({
        kind: selected.ref.kind, id: item.id, version: item.version, digest: item.digest,
      }));
      if (!available.some((item) => referenceText(item) === values.reference)) available.unshift(selected.ref);
      const references = select(available.map((item) => [referenceText(item), `${item.kind} · ${item.id} @ ${item.version} · ${item.digest.slice(0, 12)}`]), values.reference, "reference");
      fields.append(node("label", {}, "实例精确引用", references),
        field("实例输入绑定 JSON", "nodeInputs", values.nodeInputs, "textarea", { spellcheck: "false" }));
    }
    if (selected.ref?.kind === "agent") {
      const roles = [...new Set([values.role, ...app.agentRoles])];
      fields.append(node("label", {}, "实例职能", select(roles, values.role, "role")),
        field("实例权限 JSON", "nodePermissions", values.nodePermissions, "textarea", { spellcheck: "false" }));
      if (current.definition.schema_version === 2) fields.append(node("label", {}, "审查职责（仅 reviewer 生效）",
        select([["required", "必需"], ["advisory", "建议"]], values.requirement, "requirement")));
    }
  }
  const retainFields = () => {
    const buffer = Object.fromEntries(new FormData(fields));
    current.formBuffer = Object.keys(defaults).every((key) => defaults[key] === buffer[key]) ? null : buffer;
    touchEditor(current);
    updateControls();
  };
  fields.addEventListener("input", retainFields);
  fields.addEventListener("change", retainFields);
  fields.append(row(action("应用字段文本", () => {
    const values = current.formBuffer || defaults;
    const selected = current.definition.nodes?.[current.selectedNode];
    return convertCandidate(current, render, { text: formDocument(current, values),
      rename: selected ? { from: selected.id, to: values.nodeId } : null });
  }, () => pendingText(current) || Boolean(current.request)),
  action("放弃字段文本", () => { current.formBuffer = null; touchEditor(current); redraw(render); }, () => Boolean(current.request))));
  if (current.kind !== "workflow") return fields;
  const nodes = current.definition.nodes;
  const picker = select(nodes.map((item, index) => [String(index), `${item.id} · ${item.ref?.kind || "all-join"}`]), String(current.selectedNode), null);
  picker.setAttribute("aria-label", "编辑实例");
  picker.disabled = pending(current) || Boolean(current.request);
  picker.addEventListener("change", () => { current.selectedNode = Number(picker.value); rememberEditor(current); redraw(render); });
  const add = (kind) => {
    const next = structuredClone(current.definition);
    let index = 1;
    while (next.nodes.some((item) => item.id === `${kind}-${index}`)) index++;
    const item = { id: `${kind}-${index}`, depends_on: [] };
    if (kind === "join") item.join = "all";
    else {
      const reference = library[kind === "agent" ? "agents" : "workflows"][0];
      if (!reference) throw new Error("请先导入可引用的精确版本");
      item.ref = { kind, id: reference.id, version: reference.version, digest: reference.digest };
      item.inputs = Object.fromEntries(next.inputs.map((port) => [port, { input: port }]));
      if (kind === "agent") {
        item.role = reference.roles[0];
        item.permissions = structuredClone(next.permissions);
        if (next.schema_version === 2 && item.role === "reviewer") item.review_requirement = "required";
      }
    }
    next.nodes.push(item);
    return convertCandidate(current, render, { text: textOf(next) });
  };
  return node("div", {}, row(node("label", {}, "编辑实例", picker),
    ...[["agent", "增加 Agent 实例"], ["workflow", "增加子工作流实例"], ["join", "增加 all-join"]].map(([kind, label]) =>
      action(label, () => add(kind), () => pending(current) || Boolean(current.request)))), fields,
    action("删除当前实例", () => {
      const next = structuredClone(current.definition), id = nodes[current.selectedNode].id;
      next.nodes.splice(current.selectedNode, 1);
      for (const item of next.nodes) item.depends_on = item.depends_on.filter((value) => value !== id);
      return convertCandidate(current, render, { text: textOf(next) });
    }, () => pending(current) || Boolean(current.request) || nodes.length <= 1, "secondary danger"),
    node("p", {}, "重命名会同步依赖和具名绑定。删除后请检查剩余端口引用；新增实例的端口、职能和权限须按实际用途调整。"));
}

function resourceEditor(current, render, action, updateControls) {
  const draft = current.fileDraft || newFileDraft();
  const path = node("input", { value: draft.path, "aria-label": "资源文件路径", placeholder: "context/notes.md" });
  const operation = select([["write", "完整写入文件"], ["delete", "明确删除文件"], ["mkdir", "增加空目录"]], draft.op, null);
  operation.setAttribute("aria-label", "资源文件操作");
  const bits = node("input", { value: draft.executableBits, "aria-label": "资源文件执行位", placeholder: "留空保留；例如 100" });
  const text = draft.content.encoding === "text" ? node("textarea", {
    className: "workflow-json", value: draft.content.value, "aria-label": "资源文件完整文本", spellcheck: "false",
  }) : null;
  const retain = (event) => {
    const content = event.target === text ? { encoding: "text", value: text.value } : (current.fileDraft || draft).content;
    const proposed = { op: operation.value, path: path.value, executableBits: bits.value, content };
    try { checkResourceDraft(proposed, workingResources(current).operations); }
    catch (error) {
      current.error = error.message;
      redraw(render);
      return;
    }
    current.fileDraft = proposed;
    touchEditor(current);
    updateControls();
  };
  path.addEventListener("input", retain);
  bits.addEventListener("input", retain);
  text?.addEventListener("input", retain);
  operation.addEventListener("change", (event) => { retain(event); redraw(render); });
  const busy = () => Boolean(current.request);
  const upload = node("input", { type: "file", "aria-label": "上传完整资源文件", disabled: busy(),
    onchange: (event) => event.target.files[0] && uploadResource(current, event.target.files[0], render) });
  const draftView = node("div", {},
    node("label", {}, "包内相对路径", path), node("label", {}, "文件操作", operation),
    draft.op === "write" ? [node("label", {}, "可移植执行位（八进制；每位 0/1）", bits),
      node("label", {}, "选择完整文件字节", upload),
      text ? node("label", {}, "完整 UTF-8 文本", text) : node("p", {}, `完整二进制草稿：${base64Size(draft.content.value)} 字节；原字节保留。`),
      !text ? action("将完整字节按 UTF-8 编辑", () => editDefinition(current, "decode-resource", render, async () => {
        const value = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(resourceBytes(current.fileDraft.content.value));
        current.fileDraft = { ...current.fileDraft, content: { encoding: "text", value } };
        touchEditor(current);
      }), busy) : null,
    ] : node("p", {}, draft.op === "delete" ? "只明确删除指定普通文件；不递归删除目录。" : "明确增加空目录；父目录由原库创建。"),
    row(action("暂存文件操作", () => stageResource(current, render), () => busy() || current.fileDraft === null),
      action("放弃文件草稿", () => { current.fileDraft = null; touchEditor(current); redraw(render); }, () => busy() || current.fileDraft === null)));
  const operations = workingResources(current).operations;
  const preview = current.resourcePreview;
  const previewView = node("div", { "data-resource-preview": "", hidden: !preview }, preview ? [
    node("h3", {}, "资源候选差异（尚未应用）"), pre({ candidate: preview.result.candidate,
      changes: preview.result.changes, directory_changes: preview.result.directory_changes }),
    node("details", {}, node("summary", {}, "建议标准正文"), pre(preview.result.definition)),
    action("采用资源摘要", () => adoptResources(current, render), () => busy() || !current.resourcePreview ||
      current.resourcePreview.revision !== current.revision || pendingText(current) || current.formBuffer !== null || current.fileDraft !== null, "primary"),
  ] : null);
  const editOperation = (item) => {
    current.fileDraft = { op: item.op, path: item.path,
      executableBits: Object.hasOwn(item, "executable_bits") ? item.executable_bits.toString(8).padStart(3, "0") : "",
      content: item.op === "write" ? { encoding: "base64", value: item.content_base64 } : { encoding: "text", value: "" } };
    touchEditor(current);
    redraw(render);
  };
  return node("div", {},
    node("p", {}, "先应用正文声明与新版本，再暂存完整文件操作、预览差异并采用摘要。新增 instructions/context/skill 的声明在 JSON/YAML resources 中填写；预览会更新合法占位摘要。普通附件无需声明。Skill 的所有子文件须逐一完整加入。"),
    draftView,
    node("h3", {}, current.resourceBuffer !== null ? "未应用的完整工作操作集合" : "已采用的完整资源操作集合"),
    node("p", {}, `${operations.length} 项 · ${resourceBudget(operations)} 写字节。集合相对固定原包；追加保留此前已采用操作，移除某项会恢复该路径的原包行为。`),
    table(["路径", "操作", "完整字节 / 执行位", "调整"], operations.map((item) => [item.path, item.op,
      item.op === "write" ? `${base64Size(item.content_base64)} B / ${Object.hasOwn(item, "executable_bits") ? item.executable_bits.toString(8) : "保留原值"}` : "—",
      row(action(`编辑操作 ${item.path}`, () => editOperation(item), () => busy() || current.fileDraft !== null),
        action(`移除操作 ${item.path}`, () => {
          current.resourceBuffer = structuredClone({ schema_version: 1, operations: operations.filter((other) => other.path !== item.path) });
          touchEditor(current);
          redraw(render);
        }, () => busy() || current.fileDraft !== null)),
    ])),
    row(action("放弃未应用资源操作", () => { current.resourceBuffer = null; touchEditor(current); redraw(render); },
      () => busy() || current.resourceBuffer === null),
    action("预览资源候选", () => previewResources(current, render),
      () => busy() || pendingText(current) || current.formBuffer !== null || current.fileDraft !== null)),
    previewView,
    current.resourceChanges !== null ? node("details", {}, node("summary", {}, "已应用的资源接受身份"),
      pre(current.acceptedCandidate || "正文或资源已变化；请重新预览并采用摘要。")) : null,
    node("details", {}, node("summary", {}, "原包文件：完整读取与下载"),
      node("p", {}, "读取固定原包，经有界窗口完整合并并核 SHA 后才可编辑或下载。未完成片段不会进入草稿；未修改的附件仍由原库保留。"),
      table(["原包路径", "SHA256 / 执行位", "操作"], Object.entries(library.detail.files).map(([name, details]) => [name,
        `${details.sha256} / ${details.executable_bits.toString(8)}`,
        row(!["agent.json", "workflow.json"].includes(name) ? action(`完整读取 ${name}`, () => readResource(current, name, true, render),
          () => busy() || current.fileDraft !== null) : node("span", {}, "经标准正文编辑"),
        action(`下载原文件 ${name}`, () => readResource(current, name, false, render), busy)),
      ]))),
    node("p", {}, "HTTP 请求含 base64 最多4,000,000字节，较大变更请下载缓冲后使用 CLI --resources。完整操作最多1500项／10MB写字节；最终包的路径、文件/目录、Skill与权限仍由原库检查。"));
}

function editorView(render) {
  const current = currentEditor();
  if (!current) return null;
  if (current.restoreError) return panel("定义编辑缓冲无法打开", current.restoreError,
    button("下载定义原始缓冲", () => download("definition-editor-buffer.txt", current.raw)),
    button("重新核对定义缓冲", async () => { editors.delete(current.key); await openDefinition(current.kind, current.base, render); }),
    button("明确清除此定义缓冲", async () => {
      sessionStorage.removeItem(current.key);
      editors.delete(current.key);
      await openDefinition(current.kind, current.base, render);
    }));
  const controls = [];
  const disclosure = (name, label, ...children) => {
    const details = node("details", { open: current.expanded[name] ? "" : null }, node("summary", {}, label), ...children);
    details.addEventListener("toggle", () => { if (details.isConnected) current.expanded[name] = details.open; });
    return details;
  };
  const action = (label, run, disabled = () => false, className = "secondary") => {
    const element = button(label, run, className);
    controls.push({ element, disabled });
    return element;
  };
  const notice = node("p", { role: "status" });
  const storage = node("p", { className: "error", role: "alert" });
  const error = node("p", { className: "error", role: "alert" });
  const message = node("p", { role: "status" });
  let fields;
  const updateControls = () => {
    controls.forEach(({ element, disabled }) => { element.disabled = disabled(); });
    const picker = fields?.querySelector('[aria-label="编辑实例"]');
    if (picker) picker.disabled = pending(current) || Boolean(current.request);
    const resourcePreview = resources?.querySelector("[data-resource-preview]");
    if (resourcePreview) resourcePreview.hidden = !current.resourcePreview;
    notice.textContent = pending(current) ? "有未应用的字段、JSON / YAML、文件草稿或资源操作；请应用／采用或放弃后再检查、发布或撤销。"
      : current.resourceChanges !== null && current.acceptedCandidate === null ? "资源候选接受已失效；请重新预览并采用资源摘要。"
      : current.check?.revision === current.revision ? "当前正文和资源已检查，可明确发布。" : "正文已应用；检查完整候选后才能发布。";
    storage.textContent = current.storageError || "";
    storage.hidden = !current.storageError;
    error.textContent = current.error;
    error.hidden = !current.error;
    message.textContent = current.message;
  };
  fields = definitionForm(current, render, action, updateControls);
  const resources = resourceEditor(current, render, action, updateControls);
  const busyOrPending = () => pending(current) || Boolean(current.request);
  const uncheckedResources = () => current.resourceChanges !== null && current.acceptedCandidate === null;
  const move = (direction) => {
    current.historyIndex += direction;
    const snapshot = current.history[current.historyIndex];
    current.definition = JSON.parse(snapshot.text);
    current.texts = { ...snapshot.texts };
    current.appliedTexts = { ...snapshot.texts };
    current.canonicalTexts = { ...snapshot.canonicalTexts };
    current.selectedNode = snapshot.selected;
    Object.assign(current, JSON.parse(snapshot.resources), { resourceBuffer: null, fileDraft: null });
    touchEditor(current, current.acceptedCandidate);
    redraw(render);
  };
  const editorsView = ["json", "yaml"].map((format) => {
    const label = format.toUpperCase();
    const input = node("textarea", { className: "workflow-json", value: current.texts[format], "aria-label": `定义 ${label} 原文`, spellcheck: "false" });
    input.addEventListener("input", () => { current.texts[format] = input.value; touchEditor(current); updateControls(); });
    return disclosure(format, `${label} 原文`, input,
      row(action(`应用 ${label} 原文`, () => convertCandidate(current, render, { text: current.texts[format], format }),
        () => pendingText(current, format) || current.formBuffer !== null || Boolean(current.request)),
      action(`放弃 ${label} 原文`, () => { current.texts[format] = current.appliedTexts[format]; touchEditor(current); redraw(render); }, () => Boolean(current.request)),
      button(`下载 ${label} 原文`, () => download(`${current.kind}.${format}`, current.texts[format]))));
  });
  const view = panel("编辑定义并派生新版本", "编辑基于此精确原包，原附件与目录全部保留。发布增加不可变版本，不修改原定义或在途任务。",
    pre({ base: current.base }), notice, storage, error, message,
    row(action("检查定义候选", () => reviseDefinition(current, false, render), () => busyOrPending() || uncheckedResources()),
      action("发布新定义版本", () => reviseDefinition(current, true, render),
        () => busyOrPending() || uncheckedResources() || current.check?.revision !== current.revision, "primary"),
      button("下载定义编辑缓冲", () => download("definition-editor-buffer.json", textOf(editorBuffer(current))))),
    row(action("撤销定义编辑", () => move(-1), () => busyOrPending() || current.historyIndex === 0),
      action("重做定义编辑", () => move(1), () => busyOrPending() || current.historyIndex === current.history.length - 1)),
    node("p", {}, "本页历史最多50份、合计4MiB（含完整资源操作字节）；单份超限时仅保留当前已应用快照。刷新后保留编辑缓冲并重新建立历史。"),
    current.publication ? panel("已发布版本回执", "此处保留最近一次成功发布的精确版本；后续编辑仍须重新检查和发布。",
      pre(current.publication), button("以已发布版本继续编辑", () => openDefinition(current.kind, current.publication, render))) : null,
    current.check ? node("details", {}, node("summary", {}, "上次检查的快照结果"), pre(current.check.result)) : null,
    disclosure("fields", "字段编辑", fields),
    ...editorsView,
    disclosure("resources", "资源与附件编辑", resources),
    node("p", {}, "缓冲按控制目录与原定义版本隔离，关闭标签页前请发布或下载。下载含全部已应用／未应用正文和资源字节，不含未编辑原包；完整独立包另用 CLI export。YAML 采用 JSON 数据模型，日期等字符串请加引号，不支持别名。"));
  updateControls();
  return view;
}

function instancesView(preview) {
  return panel(
    "静态组合与完整祖先指令",
    "结构父链决定资源继承和权限上限；依赖决定先后，端口决定数据来源。此处尚未调用 Agent。",
    row(badge(`${preview.usage.instances} 个实例`), badge(`${preview.usage.material_bytes} 指令字节`)),
    pre({ root: preview.root, preview_sha256: preview.preview_sha256, pending: preview.pending }),
    table(["实例路径", "职能 / 类型", "后端请求", "结构父级", "先行依赖"], preview.instances.map((item) => [
      item.path, item.role || item.kind, item.backend_request?.tool || "—", item.parent || "根", item.depends_on.join("\n") || "—",
    ])),
    preview.instances.map((item) => node("details", { className: "definition-details" },
      node("summary", {}, `${item.path} · 权限、端口${item.kind === "agent" ? "与完整指令" : ""}`),
      pre({ ref: item.ref, role: item.role, backend_request: item.backend_request, permissions: item.permissions,
        limits: item.limits, usage: item.usage, concurrency_scopes: item.concurrency_scopes,
        inputs: item.inputs, outputs: item.outputs, review_requirement: item.review_requirement }),
      item.kind === "agent" ? [
        pre({ material_bytes: item.material_bytes, prompt_sha256: item.prompt_sha256 }),
        ...item.resources.map((resource) => node("details", {},
          node("summary", {}, `${resource.kind} · ${resource.ids.join(", ")}`),
          pre({ content_digest: resource.content_digest, sources: resource.sources }), pre(resource.text),
        )),
        node("details", {}, node("summary", {}, "完整装配后的提示正文"), pre(item.prompt)),
      ] : null,
    )),
    button("下载 composition-preview.json", () => download("composition-preview.json", JSON.stringify(preview, null, 2) + "\n")),
  );
}

function detailView(render) {
  if (library.detailLoading) return [panel("精确版本", "正在读取定义…")];
  if (library.detailError) return [panel("定义读取失败", library.detailError,
    button("重试读取定义", () => openDefinition(library.selection.kind, library.selection, render)))];
  if (!library.detail) return [panel("选择一个精确版本", "先导入内置组合，或从列表选择 Agent / 子工作流。版本详情和静态预览均不执行任务。")];
  const { definition, resources, digest } = library.detail;
  const selected = library.selection;
  const contents = [editorView(render), panel(
    `${definition.id} @ ${definition.version}`, definition.description,
    pre({ kind: selected.kind, digest, roles: definition.roles, specialties: definition.specialties,
      backend_request: definition.backend }),
    node("details", {}, node("summary", {}, "标准定义 JSON"), pre(definition),
      button("下载定义 JSON", () => download(`${selected.kind}.json`, JSON.stringify(definition, null, 2) + "\n"))),
    resources.map((resource) => node("details", {}, node("summary", {}, `自身资源 · ${resource.id}`),
      pre({ kind: resource.kind, path: resource.path, digest: resource.digest, sha256: resource.sha256 }), pre(resource.text))),
    node("details", {}, node("summary", {}, "完整包文件身份（含 Skill 附件）"), pre(library.detail.files)),
  )];
  if (selected.kind !== "workflow") return contents;
  const result = node("div", {},
    library.previewError ? panel("预览未通过", library.previewError) : null,
    library.preview ? instancesView(library.preview) : empty("预览后查看所有叶实例继承的指令、来源、权限和预算。"),
  );
  const grant = node("textarea", { className: "workflow-json", value: library.grant,
    "aria-label": "静态预览上限 JSON", spellcheck: "false" });
  const previewAction = button(library.previewLoading ? "正在预览…" : "预览完整组合", () => previewDefinition(render),
    "primary", { disabled: library.previewLoading });
  grant.addEventListener("input", () => {
    library.grant = grant.value;
    library.previewRequest++;
    Object.assign(library, { preview: null, previewLoading: false, previewError: "" });
    previewAction.disabled = false;
    previewAction.textContent = "预览完整组合";
    result.replaceChildren(empty("上限已修改；重新预览后查看当前结果。"));
  });
  contents.push(panel(
    "预览整个嵌套组合",
    "初始上限来自该根定义，可修改后显式预览。这是静态校验上限；正式任务仍需项目授权、冻结输入与后端能力准入。",
    node("label", {}, "静态预览上限 JSON", grant),
    previewAction,
  ), result);
  return contents;
}

export function definitionsView(render) {
  synchronizeLibrary();
  if (!library.started) {
    library.started = true;
    const home = library.controlDirectory;
    queueMicrotask(() => { if (currentLibrary(home)) loadLibrary(render); });
  }
  const selected = library.selection;
  const agentIndex = selected?.kind === "agent" ? library.agents.findIndex(
    (item) => item.id === selected.id && item.version === selected.version) : -1;
  const workflowIndex = selected?.kind === "workflow" ? library.workflows.findIndex(
    (item) => item.id === selected.id && item.version === selected.version) : -1;
  const agentChoice = select([
    ["", "选择 Agent 精确版本…"], ...library.agents.map((item, index) => [String(index), `${item.id} @ ${item.version} · ${item.roles.join(", ")}`]),
  ], agentIndex < 0 ? "" : String(agentIndex), "agent_definition");
  agentChoice.setAttribute("aria-label", "Agent 精确版本");
  agentChoice.addEventListener("change", () => {
    if (agentChoice.value !== "") openDefinition("agent", library.agents[Number(agentChoice.value)], render);
  });
  const workflowChoice = select([
    ["", "选择子工作流精确版本…"], ...library.workflows.map((item, index) => [String(index), `${item.id} @ ${item.version}`]),
  ], workflowIndex < 0 ? "" : String(workflowIndex), "workflow_definition");
  workflowChoice.setAttribute("aria-label", "子工作流精确版本");
  workflowChoice.addEventListener("change", () => {
    if (workflowChoice.value !== "") openDefinition("workflow", library.workflows[Number(workflowChoice.value)], render);
  });
  return [
    heading("Agent 与组合库", "复用专长 Agent 与嵌套子工作流。此库在同一控制目录内共享，可在注册项目之前使用。",
      button(library.loading ? "正在读取…" : "刷新定义库", () => loadLibrary(render), "secondary", { disabled: library.loading })),
    library.error ? panel("库操作未完成", library.error) : null,
    library.message ? node("p", { role: "status" }, library.message) : null,
    panel("内置领域组合", "导入版本化定义以供后续选择；执行时另行确认项目授权与后端能力。后端工具的安装和认证在工具绑定中处理。",
      table(["组合", "支持范围", "操作"], library.presets.map((item) => [
        node("div", {}, node("strong", {}, item.id), node("p", {}, item.description)),
        item.runtime === "development-v5" ? "原六阶段开发运行；writer 信任须显式选择" : "静态组合与只读提案叶；实验由可信 runner 执行",
        button(library.installing === item.id ? "正在导入…" : `导入 ${item.id}`, () => installPreset(item.id, render),
          "secondary", { disabled: Boolean(library.installing) }),
      ])),
      library.loading && !library.presets.length ? empty("正在读取内置组合…") : null,
    ),
    panel("选择定义", `${library.agents.length} 个 Agent 版本 · ${library.workflows.length} 个工作流版本。后端字段表示默认请求，可用性由实际调用核验。`,
      node("label", {}, "Agent 精确版本", agentChoice), node("label", {}, "子工作流精确版本", workflowChoice)),
    ...detailView(render),
  ].filter(Boolean);
}
