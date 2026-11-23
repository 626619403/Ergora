# 模板入门旅程

简体中文 · [English](../../development/templates.md) · [文档目录](../../README.zh-CN.md)

这份指南串起安装、专家组合、正式开发与训练实验。先读[安装与日常使用](../../install/linux.md)，Windows使用[Windows手册](../../install/windows.md)。基础控制台包含CLI、SQLite和本地页面；完整六阶段还需要Linux/WSL2参考执行环境、所选服务和已认证Agent。选择development或research安装组合只补SDK，服务、模型、项目检查和GPU按需准备。

先按[源码分支选择](../../install/linux.md#install-in-a-clean-environment)安装本文对应的开发分支或固定提交；包版本号相同不保证具有下文的preset／组合命令。

|模板／preset|当前随包根身份|专家关系与入口|
|---|---|---|
|repository-governance|`ergora-governance-template@1.1.6`|knowledge-map与boundary-test并行，接可信集成／验证及结构、正确性、测试价值审查|
|large-change|`ergora-large-change-template@1.1.6`|contract→server／client并行→integration-tests，再接可信集成／验证和三审查|
|training-optimization|`ergora-training-proposal@4.2.9`|源码流程→跨域规划／诊断→kernel实施方案→测量审查；全部五叶继承库／环境选择，独立只读建议，原runner执行实验|
|optimization-memory-tuning|`ergora-opt-memory-tuning-proposal@1.2.1`|容量／allocator方向资料＋共享设计／诊断专家，接独立测量证据审查|
|optimization-activation-recompute|`ergora-opt-activation-recompute-proposal@1.2.0`|重计算边界、数值与图／卸载约束；复用v2专家的只读子模板|
|optimization-cpu-offloading|`ergora-opt-cpu-offloading-proposal@1.2.0`|分开三种卸载接口及host／传输／计算成本；复用v2专家的只读子模板|
|optimization-tp-dp-overlap|`ergora-opt-tp-dp-overlap-proposal@1.2.0`|实际TP／DP／PP overlap路径、关键路径和独立测量；只读提案|
|optimization-moe-dispatcher|`ergora-opt-moe-dispatcher-proposal@1.2.0`|固定backend／ABI／拓扑、路由与全rank证据；只读提案|
|optimization-moe-overlap|`ergora-opt-moe-overlap-proposal@1.2.0`|普通EP overlap／delayed wgrad分别归因，复用同一组v2专家|
|optimization-profiling|`ergora-opt-profiling-proposal@1.2.1`|稳态trace／rank／区间并集及真实依赖证据，共享设计／诊断接独立测量审查|
|optimization-memory-snapshot|`ergora-opt-memory-snapshot-proposal@1.2.0`|受信摘要的allocator／历史／step差异分析，解析／采集继续交原所有者|
|optimization-recipe-model|`ergora-opt-recipe-model-proposal@1.2.0`|任务／模型／配方匹配、语义不变量与真实框架适配缺项；共享v2专家只读提案|
|optimization-model-verification|`ergora-opt-model-verification-proposal@1.2.0`|逐项核转换／forward／训练／恢复／质量声明，消费原指标而非只看exit0；执行交原所有者|
|optimization-cluster-resiliency|`ergora-opt-cluster-resiliency-proposal@1.2.0`|启动／原job身份、日志与checkpoint／恢复证据，复用三位v2只读专家；集群动作仍交原执行器|
|optimization-low-precision|`ergora-opt-low-precision-proposal@1.2.0`|design／profile→kernel→measurement的只读低精度方案；原实验与质量／性能门禁保持|
|optimization-kernel|`ergora-opt-kernel-proposal@1.2.0`|design／profile→kernel→measurement的算子／wrapper及独立验证方案；原生流程与真实测量另验|
|refactoring|`ergora-refactoring-template@1.3.6`|准备→rewrite→compatibility→原可信集成／验证→三审查；普通父引用一个原生large-change六阶段实例|
|optimization-performance-diagnosis|`ergora-opt-performance-diagnosis-proposal@1.2.1`|同症状反馈命令与按实际报告选择工具；design／profile→measurement只读提案|

每个Agent是独立版本包，可有自己的专长、初始指令、Skill和后端。结构父链完整累加资料并限制子权限；依赖边安排执行先后，具名端口传递结果。这三种关系可在“Agent 与组合库”展开查看。[定义格式与继承规则](../../definitions/workflows/compose.md)。

重构配方使用[原生六阶段操作说明](../../development/preparation.md#use-the-refactoring-recipe)和[完整示例](../../../examples/composition/refactoring/README.md)。下面的两域页面步骤包含独立盘点／规划和原工作／审查合同；重构可在同一表单选择“完整manifest · 原生六阶段”，配置准备叶／原生实例／工作与审查子图及预算，先明确授权准备，再预览与创建。选择该配方前先固定实际caller、需要保持的行为、迁移顺序和回退检查；它沿原task／run／candidate及批准流程执行。若追加项目记忆或活动Skill，再沿[资料选择](../../development/preparation.md#select-project-memories-and-active-skills-for-a-formal-task)冻结当前精确来源。

这些工程角色、初始提示与组合由Ergora维护，参考[Agent定义](../../definitions/agents.md#built-in-specialists)；它们与具体Codex／Claude Code后端分别版本化和选择。优化方向的完整表见[训练手册](../../training/specialists.md#independent-optimization-direction-subtemplates)，不是每个模板都直接导入一个上游原生Agent。

## 当前执行边界

Preset和静态图不实现一般Repeat、混合图调度器或统一fixed／preset／planner／automatic思考强度选择。当前显式后端字段只能请求模型支持的选项，不证明实际生效强度；完整祖先资料及逐级收窄权限仍按受支持任务／单叶输入冻结，见[当前后端边界](../../agents/backends.md#current-configuration-evidence-and-pending-capabilities)。

schema2设计policy登记仍仅存储且拒执行。只读[source-journal存取](../../development/design-and-approval.md#store-complete-design-sources-and-reported-answers)仅Linux／WSL2，要求真实原design-packet。可信新自然人保证与F/J/G仍不可用。有限训练控制器使用独立的[明确授权与提交流程](../../training/controllers.md#start-a-local-training-budget-and-recover-original-authorization)；导入定义或保存manifest不授执行权。

## 1. 准备模板与完整组合

以下命令适用于已安装的CLI，不需要模型或后台服务。将持久目录放在用户目录或持久卷，保留业务仓库、控制数据和完整manifest；避免临时目录。

```bash
export PATH="$HOME/.local/bin:$PATH"
export ERGORA_HOME="${ERGORA_HOME:-$HOME/.local/share/ergora}"
WALKTHROUGH_HOME="$HOME/.local/share/ergora-walkthrough"
mkdir -p "$WALKTHROUGH_HOME"
ergora composition presets
ergora composition install-preset repository-governance
ergora composition install-preset large-change
ergora composition install-preset training-optimization
ergora templates copy repository-governance "$WALKTHROUGH_HOME/governance-template"
ergora templates copy large-change "$WALKTHROUGH_HOME/development-template"
ergora templates copy training-optimization "$WALKTHROUGH_HOME/training-template"
```

复制输出目录必须是新目录；重复导入同身份preset可以保持原版本。模板复制与preset导入分别准备领域输入和专家定义，不授予模型、文件写入或批准权限。

以治理组合为例，先读取原根声明，将明确审阅的权限和预算写成grant：

```bash
ergora composition show ergora-governance-template 1.1.6 --material > "$WALKTHROUGH_HOME/root.json"
python3 - "$WALKTHROUGH_HOME" <<'PY'
import json, pathlib, sys
directory = pathlib.Path(sys.argv[1])
definition = json.loads((directory / "root.json").read_text())["definition"]
grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
(directory / "grant.json").write_text(json.dumps(grant, indent=2) + "\n")
PY
ergora composition preview ergora-governance-template 1.1.6 --grant "$WALKTHROUGH_HOME/grant.json"
```

审阅完整预览，确认实例、祖先资料和授权上限。把实际返回的`preview_sha256`填入下面的`PREVIEW_SHA256`：

```bash
ergora composition freeze-manifest ergora-governance-template 1.1.6 --grant "$WALKTHROUGH_HOME/grant.json" --preview-sha256 PREVIEW_SHA256
```

保存返回的完整包`path`、包`digest`和`manifest.preview_sha256`，随后运行`ergora composition verify-manifest FULL_MANIFEST_DIRECTORY`。更换领域时使用上表对应根ID，重新取得并审阅该根的grant；训练根不请求shell或写权限。页面也可预览后选择“保存当前预览为完整 manifest”。下载的preview JSON用于阅读，分享或备份时带上完整目录。[完整包说明](../../definitions/workflows/compose.md#save-and-share-a-complete-composition)。

## 2. 登记自己的项目

每个业务项目使用自己的Git仓库和tracker。先建立真实Git提交，再按[项目定义手册](../../projects/registration.md)配置绝对执行路径、允许修改范围和实际可信检查，执行`ergora project register project.json --revision 0`。无需先提供GitHub／GitLab仓库，可以使用local tracker；后续导出每任务自己的本地分支。代码分支与工单记录各有身份，不用一个共享业务仓库容纳所有项目。

正式运行开发组合与训练task-mcp叶都需要Linux/WSL2及可选`task-mcp`依赖；control／development／research安装组合都不会自动添加这个extra。静态导入／预览／冻结和合同创建不要求它，因此创建成功仍需完成运行准备。在所安装版本的仓库根，用运行Ergora及其executor的同一Python环境安装。默认Bash安装器对应命令为：

```bash
"$HOME/.local/share/ergora-app/venv/bin/python" -m pip install '.[task-mcp]'
```

自建环境或自定义安装目录使用自己的Ergora解释器；只在另一个Python环境安装不会补齐executor依赖。原生Windows可先使用控制台、定义和text-only能力，固定task MCP读取与完整开发执行使用Linux/WSL2环境。完成所选Agent的[安装与认证](../../agents/configuration.md#install-and-authenticate-agent-clis)，并将对应认证／推理配置提供给实际启动Ergora和执行器的环境；其他后端仅适用于未声明该模型下限的自定义定义，Claude task-mcp的bare模式需要其支持的API环境认证。凭据值不写入任务或定义。服务、角色和项目检查分别核验，不能以单个版本或认证检查代替实际任务。

治理需behavior／architecture／knowledge检查，大型变更还需integration／compatibility／migration-rollback。这些是项目的可执行验收，使用本项目实际命令；完整运行环境、服务、模型认证分别按[部署步骤](../../development/templates.md#the-three-templates-and-formal-tasks)准备。`doctor`、服务RUNNING或创建成功分别只说明各自状态。

## 3. 页面创建开发任务

运行`ergora serve`，在本机打开`http://127.0.0.1:8977`。在“正式任务”中：

1. 打开“预览与创建”，选择登记模板，点击“载入所选模板”。等“已载入模板输入”完成后，再填写任务ID、工单和真实输入；修改模板会使旧预览失效。
2. 选择“完整manifest · 组合执行与审查”，填入第一步的`manifest.preview_sha256`，点击“读取完整 manifest”。审查实例选`root/review`，执行实例选`root/work`；在“盘点与计划”中选择`root/preparation/inventory`与`root/preparation/plan`，填写足以覆盖工作单元的仓库读取路径。两名准备专家默认使用gpt-6.1-sol max。
3. 点击“从当前输入载入工作单元”，将每个unit分配到对应完整路径。治理为`knowledge-map`、`boundary-test`；大型变更为`contract`、`server`、`client`、`integration-tests`，对应`root/work/UNIT_ID`。
4. 为每个writer显式选择支持的后端、执行边界和覆盖理由。当前可写组合使用Codex，model／effort预填模板值；仍须明确选择“已信任的当前容器 / 用户”，并使用可信Linux环境。该边界允许Agent访问当前用户文件，权限路径检查不提供逐次文件访问的OS隔离。
5. reviewer沿用gpt-6.1-sol high，覆盖须满足定义最低线；内置专家同后端时记录独立会话理由并选择相应策略。配置认证的shell应与启动Ergora的环境一致，密钥放外部环境或工具认证配置。
6. 点击“预览所选执行路线”核对所选阶段。原生六阶段任务须授权准备，再次预览完整冻结结果后确认创建。核对分配、后端与政策、祖先资料、路径和输入。页面一并冻结盘点、规划、工作和审查成员；漏选准备阶段会明确拒绝。创建只发布合同，不启动模型或任务。

同一模板可有多个同职责专家实例；新增／替换专家先发布独立Agent及沿父链更新的精确工作流版本，再重新预览与冻结新任务。图形页面展示已发布图，拖动布局不会修订合同。详细CLI配置见[工作单元协议](../../definitions/workflows/contracts.md#specialist-writers-and-original-work-units)。

## 4. 运行、批准、验收与恢复

按[正式任务顺序](../../development/tasks.md#formal-task-sequence-and-recovery)启动所选服务并提交原任务。保留task ID、创建／提交intent SHA和原workflow／run ID；运行到plan后阅读实际计划，以稳定decision ID明确批准精确plan SHA，再继续work→integrate→verify→review。

`REVIEW_READY`表示有待维护者检查的精确候选。核candidate、真实检查、所有必需审查与原产物，再导出每任务本地分支，独立复验并走项目自己的MR／合入。模型approve、进程exit0、工单关闭各自都不能替代该流程。

如果新任务使用工单来源v7，导出后还可按[候选远端核对](../../projects/candidate-actions.md#check-the-candidate-and-current-remote-branches)比较本地与远端head／base；这只读取当前事实，不推送／关联PR或替代人工审查。未选择来源的任务继续走原导出和项目自己的发布流程。

回复丢失时沿原ID查询：创建用`task creation`，提交用`task submission`，批准用`task approval`，导出用`task export-status`；按返回的原意图使用对应resume命令。未知状态先对账，不改ID重发。闭合后再核外部作业和租约。控制目录、执行CONFIG／STATE、Git仓库和Temporal持久数据联合备份；[恢复表](../../development/tasks.md#formal-task-sequence-and-recovery)及[联合备份](../../operations/backup-recovery.md)给出完整步骤。

## 5. 训练提案与实际实验

训练模板先准备真实workload、baseline、精确实验清单和正确性标准。若只需要专家提案，可用轻量项目`ergora project add PROJECT_ID --repo ABSOLUTE_REPO`，按第一步保存训练完整manifest，并准备UTF-8任务正文，包含所选叶子所需的全部前驱材料。

先完成[第2步的共用运行准备](#2-登记自己的项目)：Linux/WSL2、同一Ergora解释器的task-mcp依赖及所选后端认证。

先完成所选后端支持的认证。Codex可另加`--codex-config ABSOLUTE_CONFIG_PATH`，配置中引用外部凭据环境变量；Claude的bare模式要求其支持的API环境认证。在任务正文要求Agent通过固定task MCP完整读取自己和全部结构祖先的Skill／上下文，长附件连续UTF-8分页到`next_offset: null`。准备好依赖、认证及正文后执行：

```bash
ergora composition prepare-from-manifest TRAINING_MANIFEST_DIRECTORY root/analysis/design --task experiment-task.txt --directory ./prepared-design --max-prompt-bytes 50000
ergora composition check-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend"
ergora composition run-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend" --timeout 300
```

`check-input`只检查能力与输入，不调用模型。完整流程见[单叶调用与读取核验](../../definitions/workflows/leaf-calls.md#call-a-prepared-leaf)。

其他叶子为`root/analysis/profile`、`root/kernel/assess`、`root/measurement/review`。单叶调用没有自动执行前驱，操作者应在新任务正文中明确提供完整来源和前驱回复。内置叶的覆盖必须满足模型下限，审查使用独立会话；调用失败后保留原run，不自动换后端或降档。其他后端示例仅适用于未声明该下限的自定义定义。认证检查成功仍需真实小调用确认推理可用；上游API错误不能用放宽工具权限来证明已修复。

若任务需要细方向知识，可按[独立优化方向表](../../training/specialists.md#independent-optimization-direction-subtemplates)选择已提供的方向。它们读取所选方向完整context并复用v2专家；多数保留design／profile／measurement三叶，手动把前两份完整原结果交给measurement。低精度和kernel方向还含kernel叶，先接收两份完整分析，再把三份完整原结果交给measurement。安装这些提案包不会安装GPU工具、开启原生搜索或运行整个图。

提案和模型审查供操作者准备实验。实际流程为固定workload／baseline／experiment→可信runner执行→独立正确性／性能复验→人工批准原evidence SHA→该项目开发任务集成复验。ForgeKernel是可选候选生成器，有独立版本、模型与设备要求；生成器完成不代表性能通过或采用。CPU／GPU、数据、ML依赖按项目安装，控制台不会配置CUDA或申请设备。[训练手册](../../training/overview.md)说明runner、负结果、取消与采用。

完整Linux参考发行保留两份详细手册：[部署与日常使用](../../../src/ergora/data/reference/platform/README.zh-CN.md)、[训练优化](../../../src/ergora/data/reference/platform/docs/TRAINING.md)。它们对应冻结v2.2参考层；当前控制台与组合用法以本指南链接的当前手册为准。单文件HTML内嵌旧参考包及两手册，新增控制面需另外安装当前仓库版本。

## 三个模板与正式任务

```bash
ergora templates list
ergora templates copy repository-governance ./governance-task
ergora templates copy large-change ./development-task
ergora templates copy training-optimization ./training-task
ergora workflow --help
ergora reference verify
ergora reference info
```

复制目标必须是新目录。模板定义任务与证据要求；示例中的 PASS、SHA 和指标不构成任何真实结果。治理与大型开发沿用 `inventory → plan → work → integrate → verify → review`；计划批准和最终证据仍由完整参考运行时处理。

需要 Temporal、MLflow、Symphony、A2A、Supervisor 和完整执行器时，使用 [单文件安装发行](../../distribution/multi-agent-development-platform.html)，或随包参考入口提供的安装器。HTML 内嵌完整安装脚本、源码 ZIP、三个模板和两本完整参考手册。其部署基础为 Ubuntu 24.04 / Linux x86_64，安装需要联网及目标系统内的包管理权限。

- [完整部署与日常使用参考手册](../../../src/ergora/data/reference/platform/README.zh-CN.md)
- [完整训练优化参考手册](../../../src/ergora/data/reference/platform/docs/TRAINING.md)
- [新入口的训练说明](../../training/overview.md)

这些冻结参考文件保持 v2.2 内容身份，便于校验；本手册和接入手册说明新的控制面能力。它们不会自动回写旧 HTML 内嵌包。 使用本地参考任务 CLI 前，还需在当前 shell 配置 Temporal 连接，见 [首个开发任务](tasks.md)。
