# S11 / M1 独立审查

日期：2026-11-01。审查者：Codex 独立审查 agent（mainline_review）。上下文为 fresh-context，仅收到原需求、切片验收、源码身份和验证证据简报，未继承实施对话。遵循仓库 `AGENTS.md`、`maintainable-project-delivery` 及其 independent-review 规范；本次唯一写入为本报告。

## 范围与身份

原需求是将 Windows 纳入主线，随后先审计和渐进重构、再按优先级补 all-in-one 能力；用户已批准开始，并要求每完成一步更新文档。本次仅审查 M1：保留历史、建立 main 并纳入 Windows、公开安装入口、推送、CI 和可恢复记录。GitHub 默认分支元数据为 M2；A1 前置为 M1，未要求先完成 M2。

- 精确基线：`01d134492c557ec1458de44248a6cb3c5954ca9c`（Windows / A0 交接）。
- 审查时 HEAD、本地 main、origin/main 及实际远端 main：`ae5319d57f1a647c8ab8874039fd6245ce423e5f`；父提交为上述基线。
- 检查基线至 HEAD 的提交差异及完整工作区差异。改动仅以下六份文档；其中 PLAN、详细计划、主线交付记录含未提交的验证/状态更新。另读 A0 交付、原验收、现有 CI 和 reference 验证实现。

下列 SHA-256 固定本次实际审查的文档内容；后续审查状态及交接记账由实施者更新。

|文件|审查内容 SHA-256|
|---|---|
|README.md|`d72f9a863ef0d30ab7d9f4f85736cb1a7bd16ea38ad734e7c9e40e7005a32006`|
|docs/USAGE.md|`a1064edf12214789810234214168b730346a46e7efe89337ad7f5965c4f7a9a5`|
|docs/WINDOWS.md|`b932b55f39d97d8f0c57ff9429f01e4a832b6fffeaf105ec0e66577a626a3dd5`|
|docs/PLAN.md|`bba73cb045ca4866a4a60802e8322ba7006dc57d693f4ba6ce8f4c15fc0e3edd`|
|docs/plans/2026-11-01-all-in-one.md|`773f260744f27799a1b69ed1ac1ff0a28f91a2056539f01a056d8ee5e06e67ed`|
|docs/delivery/2026-11-01-mainline.md|`22aca8a3d6dda2881a7e21a9c22ff4b9bfcb785a08e9ebb1f0c7fd3e72818a63`|

## 两类结论与 findings

**需求符合性：通过（限 M1）。** main 实际包含 Windows 和原有历史；安装说明已提交到 main；远端身份与当前 CI 对应。记录明确区分代码合入、默认分支元数据、历史运行验证和本轮检查，没有把后续重构或功能规划写成已实现。

**可维护性：通过（限本切片）。** 无生产代码、依赖或数据迁移；状态权威仍在详细计划，PLAN 与交付记录可恢复当前身份、验证、待办和下一动作。M2 被单列且未成为 A1 的隐含阻断；文档改动均在现有责任文件内。

在上述审查范围内无已确认 findings，无阻断 M1 的问题。此结论不构成 A1/A2、后续重构或完整 all-in-one 产品的验收。

## 独立执行的检查

- `git status`、完整 changed-file diff、提交父链及 main reflog：从研究基线 `3b52365fe56d79c7b467a73e369b5a42c2b5afc9` 建分支、快进到 Windows 基线，再增加文档提交；三个祖先检查（研究、evolution、Windows）退出码均为 0。`src/`、`scripts/`、`tests/`、`.github/`、`pyproject.toml` 与旧 HTML 的 Git 对象均与 Windows 基线相同；完整工作区无生产差异。
- 实际 `git ls-remote --symref origin ...`：main 为 `ae5319d57f1a647c8ab8874039fd6245ce423e5f`，Windows 保持基线，evolution 保持 `4c7426a4ce5b733bb32b32fc6fa2fe8438e05e9d`；远端 HEAD 仍为研究分支及 `3b52365`。现状与“保留旧分支、M2 待办”一致。
- 核对三份已提交的安装文档：clone 均明确指定 main，Windows ZIP 指向 main。独立 HTTP HEAD 读取 main README 和源码 ZIP 均为 200，ZIP 重定向到对应 main 的 codeload 地址。
- 独立请求 [CI 41319564418](https://github.com/626619403/Ergora/actions/runs/41319564418)，HTTP 200：页面含精确提交链接、main、Portability、Success、2 jobs completed、2m 34s。核对现有工作流实际包含 Ubuntu 3.11、Windows 3.12、wheel 安装、冻结身份、应用/合同回归和 Windows 安装/升级步骤。另读本地保存的公开 HTML，结论一致。
- `git diff --check` 通过；独立 pathlib/正则检查六份文档共 71 个本地文件/章节链接、围栏配对和尾随空白，无错误；graphlib 检查 33 节点唯一、前置存在、无环，A1 依赖集合为 M1。
- 禁用字节码写入后从当前 `src` 执行 `reference.verify()`：PASS，283 个文件，版本 2.2，冻结发行 ZIP SHA-256 为 `8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`。

## 限制与收口

公开 CI 页面要求登录才可读取完整日志；本审查确认页面状态、提交和工作流内容，未声称逐条读取测试日志或确认测试条目数。未另跑全量生产测试、真实模型/GPU、Windows 空白系统安装或 Mermaid 渲染；本轮无运行代码变更，历史验收仍以原记录为准。未测试 GitHub 管理 API 凭据或执行默认分支变更；当前远端 HEAD 已独立证实 M2 尚未完成。

M1 的验收证据与独立审查已具备，实施者可记录本报告并收口该切片，再从 main 进入 A1。M2 仍需维护者或获授权的管理接口实际设置，并以远端 HEAD 指向 main 单独验收。报告、审查状态及交接记账属于 M1 收口，无需递归审查。
