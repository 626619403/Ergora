# 安装与认证 Agent CLI

简体中文 · [English](../../agents/configuration.md) · [文档目录](../../README.zh-CN.md)

控制面安装器不安装模型 CLI。默认角色调用 PATH 中的 `codex`；选择 Claude Code 时调用 `claude`。Linux 可先保存官方安装器，再执行：

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://chatgpt.com/codex/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/codex.sh"
sh "$HOME/.local/share/ergora-tools/installers/codex.sh"
export PATH="$HOME/.local/bin:$PATH"
codex --version
codex
```

在 `codex` 首次交互中选择账号或 API 认证，详见 [OpenAI 官方安装说明](https://learn.chatgpt.com/docs/codex/cli) 与 [认证说明](https://learn.chatgpt.com/docs/auth)。独立角色调用沿用 Codex 自己的配置；当前正式执行需要[另行配置的 current-native 环境（英文）](../../install/linux.md#prepare-the-formal-reference-runtime)，然后进行[当前模型配置（英文）](../../agents/configuration.md#configure-formal-reference-execution)。冻结的 v2.2 安装器不会通过链接获得当前指纹或原生认证行为。

Claude Code 为可选工具，按 [官方安装说明](https://code.claude.com/docs/en/setup) 安装：

```bash
mkdir -p "$HOME/.local/share/ergora-tools/installers"
curl -fsSL https://claude.ai/install.sh \
  -o "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
bash "$HOME/.local/share/ergora-tools/installers/claude-code.sh"
export PATH="$HOME/.local/bin:$PATH"
claude --version
claude
```

在首次交互中完成 [Claude 认证](https://code.claude.com/docs/en/authentication)。上述独立安装器不要求 Node.js；使用 npm 等其他安装方式时以官方依赖要求为准。确认命令在启动 Ergora 的同一 shell 中可用后，再执行 `ergora tools doctor PROJECT` 并运行一个明确的小任务。安装/版本检查不等于认证或模型任务验收；mini-swe-agent 与 ForgeKernel 的固定源码安装、模型和设备要求见 [Agent 手册](../../agents/backends.md)。

## 首个项目与工具选择

页面右上角“新建项目”注册已有 Git 仓库，不要求 GitHub / GitLab。工具绑定页分别选择：

|层|可选实现|实际消费者|
|---|---|---|
|盘点 / 规划 / 实现 / 审查及训练提案角色|Codex、Claude Code、自定义协议；实现也可 mini-swe-agent|独立调用与可选六阶段桥接|
|原生 Kernel 生成|手动、ForgeKernel|本地原生 campaign；独立可信复验另行进行|
|记忆|SQLite、ReMe HTTP|保存、修订、检索、同步|
|Skill 优化|手动导入、GEPA + JSON 提案器|有界候选搜索与证据记录|
|资料来源|明确 URL|有界观察、快照和审阅|
|研究调度|手动、Temporal Schedule|CLI worker / Schedule|
|项目工单|本地手动、GitHub、GitLab|CLI／HTTP读取来源、冻结快照、显式评论已导出候选；GitHub可按原生ID追加一个既存候选标签|

认证使用工具自己的登录或环境变量。配置只保存凭据变量名，不在网页填写密钥。Codex 和 Claude Code 分别选择模型；默认实现与审查均为 Codex。自定义命令接收 stdin 提示，以 argv 启动，不经 shell 拼接。已安装、已连通、已认证和已通过任务验收是不同状态。

## 有效绑定与运行快照

`ergora project config PROJECT_ID` 与 `GET /api/projects/PROJECT_ID/configuration` 返回同一份只读结果。`project show`仍返回保存的原文档。轻量项目的有效视图使用`schema_version: 1`、`resolution_version: 1`和`scope: project-bindings`。统一注册项目使用`scope: registered-project`，并附`registration`中的规范化定义、摘要和发布状态；它包含模板、执行目录及检查/策略。模板输入、工具内部默认值、认证和服务连接仍由各自入口管理。统一注册、旧注册只读预览/显式导入及恢复命令见[项目定义手册](../../projects/registration.md)。

`project` 包含 ID、Git 根和当前 revision；`layers` 中每层含 `binding`、`source`、`validation`。来源 `project` 指向已保存字段，`inherited` 表示旧项目缺角色时继承 `bindings.implementer`，`legacy-default` 表示缺支持层时使用固定兼容默认：memory=sqlite、research=urls，其余支持层=manual。创建新项目仍保存当时的完整推荐绑定。

`sha256` 是去掉自身字段后，对 UTF-8、排序键、紧凑分隔符、保留 Unicode 且拒绝非有限数字的 JSON 计算的 SHA-256。它标识此视图内容，不能替代正式任务、产物或可信检查的证据摘要。视图校验不调用工具；无效继承显示具体层错误，需显式保存兼容绑定；认证与可用性另看 doctor。

独立Agent调用在启动工具前将该视图保存到运行记录的`configuration`，并沿用原`binding/project_revision`；通过主入口创建的正式任务在创建时冻结该视图；旧创建方式在首次接入可选执行器时把它加入`agent-bindings.json`。之后修改项目或推荐默认不会更新在途任务。旧任务没有此附加字段时继续读取原绑定快照，不补造历史来源；旧运行记录也不回写。Skill/记忆实际上下文仍单独保存在调用记录，当前快照不声明冻结所有外部工具内部行为。
