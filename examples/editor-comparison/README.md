# 编辑器比较原型

这个开发者例子用同一套输入与后端接口比较三个界面：

|入口|关系图|属性表单|
|---|---|---|
|`native.html`|Ergora 已随包的 Cytoscape 3.33.1|原生 HTML|
|`flow.html`|React Flow 12.12.1 / React 19.2.0|原生 HTML|
|`schema.html`|同一 Cytoscape|JSON Forms 3.8.0 / React 19.2.0|

默认 Ergora 安装不依赖这个例子或 Node.js。这里没有 Agent 调用或正式任务提交按钮；只通过现有 API 校验和保存独立试验草稿。字段、依赖和 JSON 编辑同一份输入，图的位置不写入该输入。服务端继续拥有语义摘要、领域校验及修订号。

## 构建与启动

需要 Python 3.11+、Git、Node.js 与 npm。以下 Bash 命令从仓库根目录开始；运行环境、状态和项目使用独立目录。启动端口默认 8981，可用 `--port` 调整。

```bash
python3 -m venv "$HOME/.local/share/ergora-editor-comparison/venv"
"$HOME/.local/share/ergora-editor-comparison/venv/bin/python" -m pip install '.[web]'
mkdir -p "$HOME/projects/ergora-editor-comparison"
git -C "$HOME/projects/ergora-editor-comparison" init
"$HOME/.local/share/ergora-editor-comparison/venv/bin/ergora" \
  --home "$HOME/.local/state/ergora-editor-comparison" \
  project add editor-comparison --repo "$HOME/projects/ergora-editor-comparison"
cd examples/editor-comparison
npm ci --ignore-scripts --no-audit --no-fund
npm run build
"$HOME/.local/share/ergora-editor-comparison/venv/bin/python" prototype/serve.py \
  --home "$HOME/.local/state/ergora-editor-comparison"
```

在浏览器打开 `http://127.0.0.1:8981/comparison/native.html?project=editor-comparison`，通过顶部链接切换方案。服务只监听本机；终端按 Ctrl+C 退出。再次运行时复用自己的试验状态和项目，不重复创建虚拟环境或登记同名项目。

`npm run build` 从本源码树读取既有模板 schema、API 客户端及 Cytoscape 资产。`prototype/dist/` 包含三个独立完整 bundle、每文件 raw/gzip 体积和第三方许可；`node_modules/` 与构建输出不入 Git。不要把这个开发者服务器当成默认产品入口。

## 同一编辑旅程

1. 选择 `repository-governance` 或 `large-change`，选择一个单元，编辑 ID、路径或说明，再点“更新节点”。重命名会同步修改依赖引用。
2. 用依赖起点/终点表单添加或移除依赖。Cytoscape 也支持 Shift 点起点再点终点，React Flow 支持拖动端口连接；表单提供键盘替代。
3. 拖动节点或缩放图，再点“校验当前输入”，确认输入和摘要保持。JSON 编辑后用“校验并载入 JSON”显式载入。
4. 添加环或输入越界路径，观察服务端拒绝及输入保留。修正后点“保存试验草稿”，保存结果使用原有修订检查。

每个方案/模板保存为 `editor-<方案>-<模板>` 草稿。打开页面从模板开始；现有草稿只用于读取保存修订，原型不会自动恢复它的输入。它也没有撤销/重做、完整未保存保护或跨标签修订冲突处理。这些属于后续正式编辑器计划。

JSON Forms 使用官方 `NoValidation` 模式生成控件。其默认 Ajv 浏览器编译实际被现有 CSP 拒绝；本例保持安全头，把显式校验交给同一个后端，不提供客户端 Schema 错误提示。规则/组合 schema、动态 schema 与其他 renderer 没有在本例验收，不能把这个模式推广成完整 JSON Forms 兼容性承诺。详见[第三方说明](THIRD_PARTY.md)。

本轮浏览器验证在 Linux、Node 24 和固定 Chromium 上进行；容量、其他浏览器和原型的 Windows 运行没有由这些结果覆盖。[比较报告](../../docs/research/2026-11-05-editor-comparison.md)区分实际结果、限制与后续选型。
