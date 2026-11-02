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

继续通过既有`agentflow task`命令创建、启动与批准任务，执行器可直接选择统一项目保存的目录：

```bash
ergora reference executor --project my-project
```

只对新任务启用选择式执行器，不要与原执行器同时运行。新任务核对发布状态、目录和投影后冻结有效配置；已有任务继续使用原绑定快照。完整批准、六阶段与证据要求见[Agent手册](AGENT_BACKENDS.md)。F1提供项目配置入口，正式任务的统一页面入口由后续F3/F4提供。

切换执行配置目录后，旧任务仍需原配置/状态和安装；重启旧执行器时显式设置原`AGENTFLOW_CONFIG_DIR`、`AGENTFLOW_STATE_DIR`并用`--installation`。`--project`选择当前登记的目录，不自动迁移旧任务或服务。

本地HTTP入口（沿用同源及`X-Ergora-Request: 1`保护）：

|方法与路径|输入/输出|
|---|---|
|`POST /api/project-registrations`|`{"definition": {...}, "revision": 0}`，返回项目|
|`GET /api/projects/ID/configuration`|有效绑定、注册定义、修订与摘要|
|`GET /api/projects/ID/registration`|发布状态、逐文件一致性、恢复记录位置|
|`POST /api/projects/ID/registration/resume`|`{"revision": CURRENT_REVISION}`|

已有reference注册需要显式导入，不能通过`register`自动接管。导入功能的交付状态见[计划](PLAN.md)。
