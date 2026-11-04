# 项目定义与参考执行配置

`project add`创建轻量控制项目，适用于独立Agent、记忆、Skill和研究。`project register`一次登记业务Git根、工具绑定、模板、tracker、执行位置和可信检查，并生成正式执行所需的reference项目/策略文件。CLI和本地API使用同一用例，不需要GitHub或GitLab账号。

## 统一注册

先安装[参考运行环境](USAGE.md)，完成模型认证、平台设置和可信执行边界配置。注册只检查定义和安装身份，不安装服务、不调用模型、不运行检查。仓库必须已有提交；三个执行目录必须使用绝对路径，位于业务仓库之外。路径可以指向用户持久目录；Windows登记与检查配置受支持，正式六阶段执行仍需要Linux/WSL2。

将以下内容保存为`project.json`，把路径换成实际绝对路径。检查使用argv数组，在受信任的检查进程中执行；`{repo}`会替换为任务的checkout。示例检查只适用于小型Python项目，实际使用应配置项目自己的测试、架构与知识检查。

```json
{
  "schema_version": 1,
  "id": "my-project",
  "repo": "/home/USER/projects/my-project",
  "templates": ["repository-governance"],
  "execution": {
    "installation": "/home/USER/multi-agent-platform",
    "config_directory": "/home/USER/.config/multi-agent-platform",
    "state_directory": "/home/USER/.local/state/multi-agent-platform"
  },
  "tracker": {"kind": "local", "project": "local/my-project"},
  "allowed_paths": ["src", "tests"],
  "checks": {
    "behavior": ["python", "-m", "pytest", "{repo}/tests"],
    "architecture": ["python", "{repo}/checks/architecture.py"],
    "knowledge": ["python", "{repo}/checks/knowledge.py"]
  },
  "scope_policy": {
    "schema_version": 1,
    "protected_paths": [".git", ".symphony", ".agent-control", ".agent-platform-private"],
    "max_changed_files": 200,
    "max_changed_lines": 20000
  }
}
```

```bash
ergora project register project.json --revision 0
ergora project config my-project
ergora project registration my-project
```

新项目使用revision 0；升级已有轻量项目时使用`project show`显示的当前revision。已有项目必须使用相同Git根，未指定的工具绑定继续保留。可选`bindings`与`project bind`使用相同格式；缺少正式角色能力或`stage-json-v1`协议会拒绝。定义中的`base_sha`可固定已有commit，省略时取HEAD。未知字段/版本拒绝，项目定义不保存API key。

`large-change`还需`integration`、`compatibility`、`migration-rollback`检查；`scope`和`baseline-regression`由执行器提供。可同时登记多个模板，检查集合必须满足全部开发模板。`training-optimization`登记三种训练角色和执行关联；runner、workload、基线与实验仍按[参考训练流程](AGENT_BACKENDS.md)配置，登记不表示训练已初始化或验收。

配置目录下生成：

- `projects/ID.json`：业务仓库、tracker、基线、允许路径和检查。
- `policies/ID/scope.json`与`execution.json`：scope策略和启用的开发模板。
- `ergora/registrations/ID.json`：控制目录与定义摘要的归属记录。

控制项目文档是定义与绑定的权威来源。这些文件是单向、不可变投影；不要手动双向编辑。`project bind`可继续修订工具。变更基线、模板或可信策略时需使用新的配置目录，保留已有任务的旧配置；原位置内容冲突不会覆盖。一个配置目录中的同一tracker只允许一个业务项目。

## 发布中断与恢复

跨SQLite和多文件的发布会依次记录意图、保存pending项目、发布文件、确认published。注册状态和文件一致性分别展示；published且`consistent: false`仍需处理漂移。

```bash
ergora project show my-project
ergora project registration my-project
ergora project resume-registration my-project --revision CURRENT_REVISION
```

恢复只使用保存的原意图，内容相同的文件可以幂等重试，冲突文件会保留并报错。pending时不能改绑定或启动新正式任务。恢复记录位于Ergora控制目录的`registrations/ID/OPERATION.json`，含修改前/后的项目及来源；`.result.json`是发布回执。完成回执写入失败也可用同一命令补齐。不要删除pending记录后重新提交不同定义。

## 正式任务与API

新任务通过`ergora task`统一入口创建、提交、批准、取消和导出；旧入口任务继续通过原`agentflow task`管理。执行器可直接选择统一项目保存的目录：

```bash
ergora reference executor --project my-project
```

只对新任务启用选择式执行器，不要与原执行器同时运行。新任务核对发布状态、目录和投影后冻结有效配置；已有任务继续使用原绑定快照。完整批准、六阶段与证据要求见[Agent手册](AGENT_BACKENDS.md)。统一入口可先[读取已有正式任务](USAGE.md#读取正式任务合同)的合同和冻结绑定；任务预览、创建和中断恢复使用[统一创建入口](USAGE.md#预览与创建正式任务)，`task status`可[查询原生运行状态](USAGE.md#查询正式任务运行状态)，提交使用[统一提交与恢复入口](USAGE.md#提交正式任务与恢复未知结果)，批准使用[精确计划批准入口](USAGE.md#批准精确计划与恢复投递)，取消使用[原运行取消入口](USAGE.md#请求取消与恢复未知投递)，导出使用[精确候选出口](USAGE.md#导出精确候选与恢复回执)，闭合后可[逐项核对外部作业证据](USAGE.md#核对闭合运行的外部作业证据)，并以当前revision明确[对账与恢复精确claim](USAGE.md#显式终态对账与工单租约释放)；下述参考命令仍可管理旧入口创建的任务。[正式任务页面](USAGE.md#正式任务页面)已提供同一生命周期及原ID恢复；闭合后可按需读取证据、预算与下载交接包，详见[网页交接](USAGE.md#网页证据预算与交接)。

切换执行配置目录后，旧任务仍需原配置/状态和安装；重启旧执行器时显式设置原`AGENTFLOW_CONFIG_DIR`、`AGENTFLOW_STATE_DIR`并用`--installation`。`--project`选择当前登记的目录，不自动迁移旧任务或服务。

本地HTTP入口（沿用同源及`X-Ergora-Request: 1`保护）：

|方法与路径|输入/输出|
|---|---|
|`POST /api/project-registrations`|`{"definition": {...}, "revision": 0}`，返回项目|
|`GET /api/projects/ID/configuration`|有效绑定、注册定义、修订与摘要|
|`GET /api/projects/ID/registration`|发布状态、逐文件一致性、恢复记录位置|
|`POST /api/projects/ID/registration/resume`|`{"revision": CURRENT_REVISION}`|

## 显式导入旧注册

已有reference注册需要显式导入，不能通过`register`自动接管。先停止该配置目录的注册写入者，保留旧任务及原运行目录。导入仅读取同名`projects/ID.json`、`policies/ID/scope.json`和可选`execution.json`，不导入模型密钥或服务设置。

保存`import.json`，填写已有注册的ID、预期Git根、要启用的模板和三个绝对执行目录：

```json
{
  "schema_version": 1,
  "id": "my-project",
  "repo": "/home/USER/projects/my-project",
  "templates": ["repository-governance"],
  "execution": {
    "installation": "/home/USER/multi-agent-platform",
    "config_directory": "/home/USER/.config/multi-agent-platform",
    "state_directory": "/home/USER/.local/state/multi-agent-platform"
  }
}
```

可选`bindings`指定角色/支持工具，未指定时保留已有控制项目的选择，新项目使用默认。基线、tracker、检查、允许路径及scope从旧文件取得；不同Git根、未知字段/版本、不足的角色能力或检查均拒绝。旧execution策略若存在，开发模板的成员集合必须相同，成员顺序和JSON格式保留；不存在时显式生成所选开发模板的allowlist，可能收窄原来未限定的任务类型。

```bash
# 默认只读预览；新控制项目revision为0，已有轻量项目用当前revision。
ergora project import-reference import.json --revision 0
# 审阅上一步的definition、changes、files及目标control_home，再填入其preview_sha256。
ergora project import-reference import.json --revision 0 --apply --preview-sha256 REVIEWED_SHA256
```

预览的`changes`使用JSON Pointer；`files`逐项列出`adopt/create`、源原始字节SHA和预期投影语义SHA。`preview_sha256`绑定目标控制目录、修订、定义和文件意图。执行时重新读取并核验：源文件即使只改变空白也须重新预览。兼容的旧文件原字节保持，只补建缺失策略与归属记录，不扫描或迁移在途任务。

导入同样使用pending意图与`resume-registration`。恢复记录还包含预览SHA、每份源身份和修改前/后的控制项目；它是恢复操作的证据，不是原目录的完整文件备份。若采用文件在预留后被其他进程改动，恢复会拒绝；应先核对并恢复原文件，或保留pending供维护者处理。不要绕过冲突覆盖原配置。已归属其他控制目录的注册不能被再次接管。

|方法与路径|输入/输出|
|---|---|
|`POST /api/project-registration-imports/preview`|`{"definition": IMPORT_SPEC, "revision": 0}`，返回只读预览|
|`POST /api/project-registration-imports`|上述输入加`"preview_sha256": "REVIEWED_SHA256"`，显式采用|
