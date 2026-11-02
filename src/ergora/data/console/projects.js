import { api } from "./api.js";
import { $, node, field, notify, form, modal } from "./ui.js";
import { app } from "./state.js";
import { resetWorkflow } from "./workflow.js";

export function projectDialog(refresh) {
  modal(
    "注册项目",
    form(
      [
        node(
          "p",
          {},
          "选择本机已有的 Git 仓库。每个项目保存自己的工具绑定、记忆与证据。",
        ),
        field("项目 ID", "id", "", "text", {
          required: true,
          pattern: "[A-Za-z0-9][A-Za-z0-9_\\-]{0,63}",
          placeholder: "my-project",
        }),
        field("Git 仓库绝对路径", "repo", "", "text", {
          required: true,
          placeholder: "/path/to/my-project",
        }),
      ],
      "注册项目",
      async (values) => {
        const result = await api("/api/projects", Object.fromEntries(values));
        app.project = result.id;
        resetWorkflow();
        $("#dialog").close();
        await refresh();
        notify("项目已注册");
      },
    ),
  );
}
