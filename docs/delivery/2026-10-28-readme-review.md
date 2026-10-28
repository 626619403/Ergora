# README 独立审查

- 切片：`2026-10-28-readme`。
- Reviewer：`readme_review`，新建独立上下文；仅接收原始要求、验收条件、文件范围与验证证据，未参与实现。
- 审查方式：先读取实际交付文件，再对照源码与 HTML 内嵌分发物；仅写入本报告，未修改运行平台。
- 适用指令：未发现项目、上级或交付目录的 `AGENTS.md`；按 `maintainable-project-delivery` 的独立审查 gate 与 `review-pr` 执行。

## Verdict

|维度|结论|依据|
|---|---|---|
|需求符合性|**PASS**|覆盖定位、用途、真实组织结构、安装认证、项目检查、人工审批、导出及训练边界；已有实现与解耦、界面规划区分清楚。|
|可维护性|**PASS**|本切片限于文档和既有分发物，复用内嵌安装器与两份完整手册；没有引入运行代码、额外接口或新的安装逻辑。交付记录保留基准、计划、检查范围与下一步。|

## Findings

**无已确认 findings，无阻断项。** 此结论仅覆盖下述文件及静态审查范围，不代表全新安装或真实工作负载已经验收。

核对的主要边界如下：

- `README.md:7`、`:64`、`:260`、`:273` 将参考分发、实际源码布局和未来拆分/图形界面分开，没有虚构 `ergora` CLI、PyPI 包、GitHub Releases、现成后端切换或任意阶段拓扑编辑。
- `README.md:37`、`:148`、`:150` 的固定六阶段、工作单元 DAG、路径所有权、4/2 与 24/4 限制及可信检查 ID 与合同和 profile 一致。
- `README.md:93`、`:111`、`:122`、`:133` 的平台要求、Responses API、凭据注入、默认不启用执行和当前容器信任说明与实际分发实现一致。
- `README.md:141`、`:171`、`:175`、`:188` 的注册 HEAD、输入冻结、精确计划摘要审批及仅 `REVIEW_READY` 可导出分支与代码一致。
- `README.md:41`、`:44`、`:201`、`:232`、`:277` 对独立会话、变更检测、共享 Unix 用户、取消对账、手动训练及团队身份限制的说明准确，没有把摘要绑定或 worktree 当作 OS 隔离。

## 基准与实际检查

目标 Git 仓库尚无 HEAD，交付文件全部未跟踪；审查直接读取完整文件，未把空 tracked diff 当作交付内容。

|审查对象|SHA256 / 身份|
|---|---|
|`README.md`|279 行；`db2ae19a4d31a296f33a98824b134b7e81b2ae072541c4a3b1cfeecbbcc18b90`|
|`docs/delivery/2026-10-28-readme.md`|审查时 50 行；`d70c31200461c4c71ec18ab2a28febbcc04ad31a091fe6fd64d72560f0c9a69e`；后续审查状态更新属于本切片记录维护。|
|`docs/distribution/multi-agent-development-platform.html`|`775490e0caea48abd95be04a6f635605edbb8f01b7a2061ccb82ebd5453b0551`|
|HTML 内嵌 `agentflow-platform-v2.2-linux-x86_64.zip`|`8018be5094623ca0646d28d3671daaf7ac60774280eefc1c5c023bc19dc5c760`|
|HTML 内嵌 `install-agentflow.sh`|`bf42fdc007ee741cdd3ddf21d164fa9738cde80fd753919359dd1780cf3bdf1c`|

对照参考实现并读取相关调用路径：

- `local/agent_platform/`：`cli.py`、`projects.py`、`executor.py`、`process_job.py`、`sandbox.py`、`search.py`、`training.py`、`training_executor.py`、`templates.py`、`core.py`、`setup.py`、`symphony.py`、`doctor.py`。
- `upstream/platform/dev_platform/`：`contracts.py`、`portable.py`、`adapter.py`、`workflow.py`；两个开发任务类型的 `profile.json`。
- `bootstrap/`：`configure-model.py`、`install-multi-agent-linux-deps.sh`、`install-multi-agent-platform.sh`；另读取 `bootstrap/report/install-from-report.sh`。
- `README.zh-CN.md`、`docs/TRAINING.md`，以及 HTML 的下载控件与 JavaScript。

检查结果：

1. 从真实 `cli.py` 的 AST 仅载入 `parser()`；README Bash 块中的 **25 条 `agentflow` 调用均被真实 argparse 接受**，没有执行 CLI。
2. README 的 28 个围栏标记闭合，无行尾空白；2 处相对文件链接和 4 个章节锚点有效。HTML 的 73 个附件下载控件均有对应文件，15 个内部引用均有目标，无重复 ID 或外部运行脚本/样式依赖。下载代码在浏览器本地生成 Blob。
3. 内存解码完整 ZIP：**283 项，`ZipFile.testzip()` 返回 `None`**。安装器、三个模板与部署/训练两份手册均存在。
4. 对上述 24 个源码/手册文件做 ZIP 与参考目录的字节比较，**23 个一致**。公开包的 `local/agent_platform/setup.py` 为预期差异：使用待配置的模型占位，不读取使用者已有 Codex 配置；命令 wrapper 位于平台 `bin/` 并提供用户入口。已读取并核对差异，与本 README 和公开部署手册相符。公开包该文件 SHA256 为 `db82b777cd0b21ea7121588402f27bbdfa8295369c8e5a884a9b44c36060414b`。
5. 递归检查完整 ZIP、附件及其中的 ZIP，共 **955 个文本对象、4 个归档对象**：未检出个人绝对路径、常见私钥或 token 模式，归档成员未见绝对路径或父目录穿越。该模式扫描不是完整安全审计。
6. `git ls-files --others --exclude-standard` 确认审查前仅 README、交付记录和 HTML；`git diff --check` 通过，未跟踪正文另由 Python 检查。`git rev-parse --verify HEAD` 的失败符合初始无提交状态。

## 范围限制与后续证据

未安装依赖、启动服务、运行模型、工单或训练任务，未做浏览器交互测试、网络下载测试、GitHub 写权限检查或完整供应链/安全审计。命令解析仅证明语法；源码追踪仅证明所描述的实现路径存在，不能替代全新 Ubuntu 环境的端到端验收。

本次文档切片没有待补的阻断证据。源码迁入后的下一切片应使用具体业务仓库完成最小本地任务、可信检查、人工审批、独立审查、导出以及取消/恢复验收；许可证、第三方声明和生产接入继续按 README 所列项目状态处理。
