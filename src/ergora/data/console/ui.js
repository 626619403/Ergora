// Source documents and model output enter the DOM as text.
export const $ = (selector, root = document) => root.querySelector(selector);
let noticeTimer;

export function node(tag, properties = {}, ...children) {
  const element = document.createElement(tag);
  // Avoid the single-select default choosing the first dependency on insertion.
  if (properties.multiple) element.multiple = true;
  for (const child of children.flat(Infinity)) {
    if (child !== null && child !== undefined && child !== false)
      element.append(
        child instanceof Node ? child : document.createTextNode(String(child)),
      );
  }
  for (const [name, value] of Object.entries(properties)) {
    if (name.startsWith("on"))
      element.addEventListener(name.slice(2).toLowerCase(), (event) => {
        try {
          Promise.resolve(value(event)).catch((error) =>
            notify(error.message, true),
          );
        } catch (error) {
          notify(error.message, true);
        }
      });
    else if (
      ["value", "checked", "disabled", "selected", "hidden"].includes(name)
    )
      element[name] = value;
    else if (value !== null && value !== undefined)
      element.setAttribute(
        name === "className" ? "class" : name,
        String(value),
      );
  }
  return element;
}
export const button = (text, action, className = "secondary", extra = {}) =>
  node(
    "button",
    { type: "button", className, onclick: action, ...extra },
    text,
  );
export const pre = (value) =>
  node(
    "pre",
    {},
    typeof value === "string" ? value : JSON.stringify(value, null, 2),
  );
export const lines = (value) =>
  value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
export const short = (value) => (value ? value.slice(0, 12) : "—");
export const heading = (title, description, action) =>
  node(
    "div",
    { className: "page-heading" },
    node(
      "div",
      {},
      node("div", { className: "eyebrow" }, "Ergora workspace"),
      node("h1", {}, title),
      node("p", {}, description),
    ),
    action,
  );
export const panel = (title, description, ...children) =>
  node(
    "section",
    { className: "panel" },
    title ? node("h2", {}, title) : null,
    description ? node("p", {}, description) : null,
    ...children,
  );
export const empty = (text) => node("div", { className: "inline-empty" }, text);
export const row = (...children) =>
  node("div", { className: "button-row" }, ...children);
export const select = (options, value, name) =>
  node(
    "select",
    { name, value },
    options.map((item) =>
      node(
        "option",
        { value: Array.isArray(item) ? item[0] : item },
        Array.isArray(item) ? item[1] : item,
      ),
    ),
  );
export const field = (label, name, value = "", type = "text", extra = {}) =>
  node(
    "label",
    {},
    label,
    type === "textarea"
      ? node("textarea", { name, value, ...extra })
      : node("input", { name, type, value, ...extra }),
  );
export const selectField = (label, options, value, name) =>
  node("label", {}, label, select(options, value, name));
export const checkbox = (label, name, checked = false) =>
  node(
    "label",
    { className: "field-check" },
    node("input", { type: "checkbox", name, checked }),
    label,
  );
export const badge = (label, color = "gray") =>
  node("span", { className: `badge ${color}` }, label);
export function status(value) {
  const color = ["succeeded", "reviewed"].includes(value)
    ? "green"
    : ["failed", "native_failed", "timed_out", "budget_exhausted"].includes(
          value,
        )
      ? "red"
      : ["running", "pending", "outcome_unknown"].includes(value)
        ? "amber"
        : "gray";
  return badge(value, color);
}
export function notify(message, error = false) {
  const notice = $("#notice");
  clearTimeout(noticeTimer);
  notice.textContent = message;
  notice.className = error ? "error" : "";
  notice.hidden = false;
  noticeTimer = setTimeout(
    () => {
      notice.hidden = true;
    },
    error ? 16000 : 7000,
  );
}
export function form(children, text, submit) {
  const action = node("button", { className: "primary", type: "submit" }, text);
  const element = node(
    "form",
    {
      onsubmit: async (event) => {
        event.preventDefault();
        if (action.disabled) return;
        action.disabled = true;
        action.textContent = "正在处理…";
        try {
          await submit(new FormData(element), element);
        } finally {
          action.disabled = false;
          action.textContent = text;
        }
      },
    },
    children,
    row(action),
  );
  return element;
}
export function modal(title, content) {
  const dialog = $("#dialog");
  if (dialog.open) dialog.close();
  $("#dialog-content").replaceChildren(
    node(
      "div",
      { className: "dialog-header" },
      node("h2", {}, title),
      button("×", () => dialog.close(), "close", { "aria-label": "关闭" }),
    ),
    node("div", { className: "dialog-body" }, content),
  );
  dialog.showModal();
}
export function download(name, content) {
  const url = URL.createObjectURL(
    new Blob([content], { type: "text/plain;charset=utf-8" }),
  );
  const link = node("a", { href: url, download: name });
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function table(headers, rows) {
  return rows.length
    ? node(
        "div",
        { className: "table-wrap" },
        node(
          "table",
          {},
          node(
            "thead",
            {},
            node(
              "tr",
              {},
              headers.map((text) => node("th", {}, text)),
            ),
          ),
          node(
            "tbody",
            {},
            rows.map((cells) =>
              node(
                "tr",
                {},
                cells.map((cell) => node("td", {}, cell)),
              ),
            ),
          ),
        ),
      )
    : empty("还没有记录。完成一次操作后，结果会显示在这里。");
}
