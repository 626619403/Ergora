# 第三方依赖与校验模式

锁定依赖在 [package-lock.json](package-lock.json)。React / React DOM 19.2.0、React Flow 12.12.1、JSON Forms 3.8.0 及构建工具 esbuild 0.28.2 的直接许可证均为 MIT。Cytoscape 3.33.1 复用仓库已有资产及其原许可，没有新增下载副本。当前安装的传递依赖包含 MIT、ISC 和 BSD 许可。

构建从实际安装包读取完整 LICENSE / NOTICE 文本，连同 Cytoscape 许可写入 `prototype/dist/THIRD_PARTY_LICENSES.txt`；esbuild 可选平台二进制使用主包的 MIT 许可。未安装的平台可选包不在当前构建产物中。esbuild 还为每个 bundle 输出链接式法律注释文件。分发构建产物时应保留这些文本，不能仅以本仓库的许可证替代第三方条款。构建遇到已安装依赖没有许可文本会显式失败。

依赖安装使用 `--ignore-scripts`；本轮已实际确认锁定 esbuild 平台二进制可在该模式构建。Node/npm 仅用于这个开发者例子，不改变默认 Python 发行的运行要求。

[Ajv 官方 CSP 说明](https://ajv.js.org/security.html#content-security-policy)指出浏览器动态编译需要 `unsafe-eval`，并给出[构建时 standalone 预编译](https://ajv.js.org/standalone.html)方案。本轮默认编译确实被原安全头拒绝；本例没有放宽它。

[JSON Forms 官方验证配置](https://jsonforms.io/docs/validation/)支持 `NoValidation`。本例在固定的、没有动态规则或组合分支的工作单元 schema 上使用该模式，只生成字段，把完整校验交给现有服务端 API。这会失去客户端错误展示；不能据此声称已接入预编译 Ajv 或支持任意 schema。默认编译失败和调整后的实际旅程在[比较报告](../../docs/research/2026-11-05-editor-comparison.md)分别记账。
