# 通用多 agent 开发平台 · 快速上手

版本 1.3 · 可移植任务契约、Symphony / A2A 双入口与共享开发工作流。模型使用 Codex 云端服务；Temporal Cloud 托管状态服务，worker 和执行器运行在云端/企业 CPU 环境。

**当前交付：**分离任务/模板/策略/绑定的编译器、A2A 1.0 网关和官方 SDK 客户端、共享工单所有权、版本化注册、DAG 编排、计划审批、独立检查/审查、文件交接适配器与仓库 harness。**接入时仍需完成：**项目 CI/Codex 执行器、真实身份与目录权限、账户和服务部署。示例不是已经接通的生产系统。

**新接入优先阅读：**[可移植契约与编译](PORTABILITY.md) → [A2A 快速部署](A2A.md)；现有部署先读 [迁移与回退](MIGRATION.md)。厂商做法和官方资料集中在 [调研记录](STANDARDS_RESEARCH.md)。以下保留完整的开发执行器接入和 Symphony 兼容路径。

## 1. 选类型，填实例

| 类型 | 选择条件 | 模板 |
| --- | --- | --- |
| `repository-governance` | 一个局部结构问题、文档漂移、重复实现或依赖边界；默认小步治理 | [说明](task-types/repository-governance/README.md) · [请求示例](task-types/repository-governance/examples/request.json) |
| `large-change` | 跨模块功能、公共契约演进、分阶段替换；需要依赖与兼容验证 | [说明](task-types/large-change/README.md) · [请求示例](task-types/large-change/examples/request.json) |

普通任务只新增 JSON 实例，不复制服务。新格式示例位于 `portable/examples/<type>/task.json`；下方原 request 示例用于 v2 兼容路径。示例中的项目、SHA 和任务 ID 必须替换为真实值。`allowed_paths` 是规范化相对路径前缀，不是 glob；工作单元在这些范围内声明自己的路径。可能共写同一路径的单元要建立依赖，不能同时运行。

固定顺序：**盘点 → 计划 → 人批准计划 → 按依赖并行实施 → 唯一候选集成 → 可信验证 → 独立审查 → 人工合并**。计划变化使用新修订；缺证据或不满足检查时不进入 `REVIEW_READY`。

## 2. 契约和部署分开维护

| 层 | 由谁维护 | 放什么 |
| --- | --- | --- |
| 共享平台 | 平台维护者 | 调度、恢复、身份入口、证据协议和可信安装包 |
| 任务类型包 | 平台/领域负责人 | manifest 关联独立的 workflow、roles、evidence 与 typed schema |
| 项目策略 | 仓库维护者，经保护分支审查 | 构建测试命令、架构规则、基线、允许路径和服务身份 |
| 任务实例 | 使用者，由准入流程验证 | task：目标、验收、真实提交、约束与工作单元 DAG |
| 运行时绑定 | 部署维护者 | binding：工单和执行能力；地址、队列和凭据留在服务配置 |

代码、知识和权限分别存放。不要让候选分支修改检查器或审批策略来证明自己合格；角色提示词只负责工作方法，不能更改平台边界。

## 3. 在仓库外安装并检查

下载并解压完整包，保留目录结构；以下命令从套件根目录执行。用 Python 3.12，安装目录由平台维护者控制，对编码 agent 只读。

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r platform/requirements.txt
PYTHONPATH=platform python -m unittest discover -s platform/tests -v
# 启用 A2A 时另装固定协议依赖
python -m pip install -r platform/requirements-a2a.txt
```

测试会区分纯单元测试与需要临时 Temporal 服务的集成测试；完整测试方式见平台验证记录。不要把示例任务提交到真实项目来“验证安装”。

查看已注册类型；填写请求后，在可信安装环境验证并编译为不可变 spec：

```bash
PYTHONPATH=platform python -m dev_platform.taskctl types
PYTHONPATH=platform python -m dev_platform.taskctl fingerprint repository-governance
PYTHONPATH=platform python -m dev_platform.taskctl compile request.json --out task.spec.json
```

`fingerprint` 用于取得安装包中 profile 的真实摘要；它不是绕过模板升级审查的方法。Symphony 交接使用原始 request，bridge 会通过同一注册表编译；`task.spec.json` 用于可信操作员查询、审批和结果命令。

## 4. 接入一个仓库

把 [ONBOARDING.md](ONBOARDING.md) 交给现有仓库中的 Codex。它先调查，再提出接入 PR。初始化模板时使用新暂存目录：

```bash
python platform/harness/harness.py init --destination /tmp/repo-harness-staging
```

审阅并合并需要的文件，保留已有 AGENTS。按仓库情况修改受保护的架构/质量策略，真实扫描基准提交，审查历史债务基线；再配置 CI 以同一策略检查候选。完整命令和覆盖边界见 [harness/README.md](harness/README.md)。

首个试点选一项可逆的仓库治理任务。人确认目标、范围和验收；agent 完成小改动并输出证据，再扩大并行度。

## 5. 连接 Symphony、worker 与执行器

1. 按 [Symphony 接入文档](../symphony/README.md) 安装并配置 GitLab 或 GitHub 项目。开发项目使用 `config.development.example.json`，启用两类开发任务，配置独立的仓库状态文件；不需要训练 baseline。
2. 由部署平台注入 `TEMPORAL_ADDRESS`、`TEMPORAL_NAMESPACE`、`TEMPORAL_API_KEY`；`DEV_TASK_QUEUE` 默认 `development-tasks`。模型身份只给 Codex，Temporal 控制身份只给控制服务。
3. 从 [adapter.example.json](adapter.example.json) 建立可信配置。五个目录必须绝对、互不重叠、持久保存并通过 ACL 隔离；编码 agent 不可写回执、证据或批准目录。
4. 把配置路径注入 `DEV_ADAPTER_CONFIG`，启动开发 worker：

```bash
PYTHONPATH=platform python -m dev_platform.worker
```

5. 启动 Symphony 和 bridge，再按 [执行器协议](EXECUTOR_PROTOCOL.md) 接受信 CI/Codex 执行器。执行器消费阶段请求、检查 fence 和 job ID，在隔离工作区运行，再发布证据与回执。**没有这个执行器，worker 只会等待，不会自动产生真实代码或测试结果。**
6. 提交真实不可变请求，通过项目准入。平台在计划阶段等待绑定计划摘要的审批，最终只产出待审阅候选。人工审批和操作命令见 [执行器协议](EXECUTOR_PROTOCOL.md)，故障与权限见 [OPERATIONS.md](OPERATIONS.md)。

无需添加第二套 LangGraph 调度层。将来若某阶段需要复杂的内部推理，可作为执行器子流程接入；任务生命周期和外部副作用仍由这套持久工作流管理。

## 6. 使用者每次只做这些

1. 选类型，说明目标、不能改变的行为与可验证完成条件。
2. 查看盘点与计划：影响面、DAG、兼容/回滚、检查覆盖；批准绑定当前版本的计划。
3. 在任务状态中看当前阶段、证据、阻塞和需要决定的事项。普通受限实施不逐步确认。
4. 在最终候选上核对检查与独立审查结论，确认未决问题和回滚；通过原有分支保护/合并队列合并。

新增类型和版本的具体步骤见 [ADD_TASK_TYPE.md](ADD_TASK_TYPE.md)。多项目隔离、重试、取消、基准漂移和真实接入验收见 [OPERATIONS.md](OPERATIONS.md)。

## 设计参考与边界

[OpenAI Harness engineering](https://openai.com/index/harness-engineering/) 提供了仓库知识导航、可执行架构约束与持续小步治理的实践参考。本套件将这些做法转成可复用模板；没有把文章中某个新仓库的自主合并方式当成所有团队的默认规则。已有仓库先建立可复现基线和受控增量，再提高自主性。

工具入口：[Codex](https://developers.openai.com/codex/) · [Symphony 固定源码](https://github.com/openai/symphony/tree/be10a1b79df723d6d7612b5651c8522704dafb2e) · [Temporal Cloud](https://docs.temporal.io/cloud) · [GitLab CI](https://docs.gitlab.com/ci/) · [GitHub Actions](https://docs.github.com/en/actions)。
