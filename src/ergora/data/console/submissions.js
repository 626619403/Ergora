import { api } from "./api.js";
import { $, node, pre, empty, form } from "./ui.js";

export const recordRefreshNote = () => node("p", { className: "form-note" },
  "请用页面右上角“刷新”读取原记录，再进行下一步；请求异常时先核对原记录，不自动重发。");

// Receipts belong to the originating form, including after an unknown outcome.
export function submissionForm(children, label, path, payload, current, method = "POST") {
  const receipt = node("div", { "aria-live": "polite" });
  const element = form(children, label, async (values) => {
    const visible = () => current() && element.isConnected &&
      (!$("#dialog").contains(element) || $("#dialog").open);
    const admit = () => {
      if (visible()) return true;
      if (element.isConnected && $("#dialog").contains(element) && $("#dialog").open)
        element.replaceChildren(empty("来源页面已变化；请关闭此窗口，回到原项目并重新打开。此次未提交请求。"));
      return false;
    };
    if (!admit()) return;
    let submitted;
    try {
      submitted = await payload(values);
    } catch (error) {
      if (visible()) receipt.replaceChildren(node("p", { className: "error" }, error.message));
      return;
    }
    // File decoding may outlive the page or modal that selected it.
    if (!admit()) return;
    element.replaceChildren(receipt);
    receipt.replaceChildren(node("p", {}, `${label}请求已发出；等待原结果。`), pre(submitted));
    try {
      const result = await api(path, submitted, method);
      if (visible()) {
        receipt.firstChild.textContent = `${label}已取得原结果。`;
        receipt.append(pre(result), recordRefreshNote());
      }
    } catch (error) {
      if (visible()) {
        receipt.firstChild.textContent = `${label}未取得完整结果。`;
        receipt.append(node("p", { className: "error" },
          `${error.message}。该请求可能已经执行。`), recordRefreshNote());
      }
    }
  });
  element.append(receipt);
  return element;
}
