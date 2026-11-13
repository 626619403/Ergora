# 模板入门旅程

这份指南串起安装、专家组合、正式开发与训练实验。先读[安装与日常使用](USAGE.md)，Windows使用[Windows手册](WINDOWS.md)。基础控制台包含CLI、SQLite和本地页面；完整六阶段还需要Linux/WSL2参考执行环境、所选服务和已认证Agent。选择development或research安装组合只补SDK，服务、模型、项目检查和GPU按需准备。

先按[源码分支选择](USAGE.md#从空环境安装)安装本文对应的开发分支或固定提交；包版本号相同不保证具有下文的preset／组合命令。

|模板／preset|根ID，除标注外1.0.0|专家关系与入口|
|---|---|---|
|repository-governance|`ergora-governance-delivery`|knowledge-map与boundary-test并行，接可信集成／验证及结构、正确性、测试价值审查|
|large-change|`ergora-large-change-delivery`|contract→server／client并行→integration-tests，再接可信集成／验证和三审查|
|training-optimization|`ergora-training-proposal`|实验设计／性能分析→kernel设计→测量审查；独立只读提案，实际实验由可信runner执行|
|training-optimization-v2|`ergora-training-proposal@2.0.0`|跨域实验约束／关键路径诊断→kernel与wrapper设计→独立测量证据审查；显式新版本，保留v1|
|optimization-memory-tuning|`ergora-opt-memory-tuning-proposal`|容量／allocator方向资料＋共享设计／诊断专家，接独立测量证据审查|
|optimization-activation-recompute|`ergora-opt-activation-recompute-proposal`|重计算边界、数值与图／卸载约束；复用v2专家的只读子模板|
|optimization-cpu-offloading|`ergora-opt-cpu-offloading-proposal`|分开三种卸载接口及host／传输／计算成本；复用v2专家的只读子模板|
|refactoring|`ergora-refactoring-template`|准备→rewrite→compatibility→原可信集成／验证→三审查；普通父引用一个原生large-change六阶段实例|

每个Agent是独立版本包，可有自己的专长、初始指令、Skill和后端。结构父链完整累加资料并限制子权限；依赖边安排执行先后，具名端口传递结果。这三种关系可在“Agent 与组合库”展开查看。[定义格式与继承规则](WORKFLOW_DEFINITIONS.md)。

重构配方是独立新入口，使用[definition6／input10操作说明](USAGE.md#使用重构配方)和[完整示例](../examples/composition/refactoring/README.md)。下面的旧两域页面向导仍生成原v6工作材料合同；原生v10定义通过CLI／HTTP提交。选择该配方前先固定实际caller、需要保持的行为、迁移顺序和回退检查；它沿原task／run／candidate及批准流程执行。

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
ergora composition show ergora-governance-delivery 1.0.0 --material > "$WALKTHROUGH_HOME/root.json"
python3 - "$WALKTHROUGH_HOME" <<'PY'
import json, pathlib, sys
directory = pathlib.Path(sys.argv[1])
definition = json.loads((directory / "root.json").read_text())["definition"]
grant = {"schema_version": 1, "permissions": definition["permissions"], "limits": definition["limits"]}
(directory / "grant.json").write_text(json.dumps(grant, indent=2) + "\n")
PY
ergora composition preview ergora-governance-delivery 1.0.0 --grant "$WALKTHROUGH_HOME/grant.json"
```

审阅完整预览，确认实例、祖先资料和授权上限。把实际返回的`preview_sha256`填入下面的`PREVIEW_SHA256`：

```bash
ergora composition freeze-manifest ergora-governance-delivery 1.0.0 --grant "$WALKTHROUGH_HOME/grant.json" --preview-sha256 PREVIEW_SHA256
```

保存返回的完整包`path`、包`digest`和`manifest.preview_sha256`，随后运行`ergora composition verify-manifest FULL_MANIFEST_DIRECTORY`。更换领域时使用上表对应根ID，重新取得并审阅该根的grant；训练根不请求shell或写权限。页面也可预览后选择“保存当前预览为完整 manifest”。下载的preview JSON用于阅读，分享或备份时带上完整目录。[完整包说明](WORKFLOW_DEFINITIONS.md#保存和分享完整组合)。

## 2. 登记自己的项目

每个业务项目使用自己的Git仓库和tracker。先建立真实Git提交，再按[项目定义手册](PROJECTS.md)配置绝对执行路径、允许修改范围和实际可信检查，执行`ergora project register project.json --revision 0`。无需先提供GitHub／GitLab仓库，可以使用local tracker；后续导出每任务自己的本地分支。代码分支与工单记录各有身份，不用一个共享业务仓库容纳所有项目。

正式运行开发组合与训练task-mcp叶都需要Linux/WSL2及可选`task-mcp`依赖；control／development／research安装组合都不会自动添加这个extra。静态导入／预览／冻结和合同创建不要求它，因此创建成功仍需完成运行准备。在所安装版本的仓库根，用运行Ergora及其executor的同一Python环境安装。默认Bash安装器对应命令为：

```bash
"$HOME/.local/share/ergora-app/venv/bin/python" -m pip install '.[task-mcp]'
```

自建环境或自定义安装目录使用自己的Ergora解释器；只在另一个Python环境安装不会补齐executor依赖。原生Windows可先使用控制台、定义和text-only能力，固定task MCP读取与完整开发执行使用Linux/WSL2环境。完成所选Agent的[安装与认证](USAGE.md#安装与认证-agent-cli)，并将对应认证／推理配置提供给实际启动Ergora和执行器的环境；Claude task-mcp的bare模式使用其支持的API环境认证。凭据值不写入任务或定义。服务、角色和项目检查分别核验，不能以单个版本或认证检查代替实际任务。

治理需behavior／architecture／knowledge检查，大型变更还需integration／compatibility／migration-rollback。这些是项目的可执行验收，使用本项目实际命令；完整运行环境、服务、模型认证分别按[部署步骤](USAGE.md#三个模板与正式任务)准备。`doctor`、服务RUNNING或创建成功分别只说明各自状态。

## 3. 页面创建开发任务

运行`ergora serve`，在本机打开`http://127.0.0.1:8977`。在“正式任务”中：

1. 打开“预览与创建”，选择登记模板，点击“载入所选模板”。等“已载入模板输入”完成后，再填写任务ID、工单和真实输入；修改模板会使旧预览失效。
2. 选择“完整manifest · 组合执行与审查”，填入第一步的`manifest.preview_sha256`，点击“读取完整 manifest”。审查实例选`root/review`，执行实例选`root/work`。
3. 点击“从当前输入载入工作单元”，将每个unit分配到对应完整路径。治理为`knowledge-map`、`boundary-test`；大型变更为`contract`、`server`、`client`、`integration-tests`，对应`root/work/UNIT_ID`。
4. 为每个writer显式选择支持的后端、执行边界和覆盖理由。当前可写组合使用Codex与“已信任的当前容器 / 用户”，仍需可信Linux环境。该边界允许Agent访问当前用户文件，权限路径检查不提供逐次文件访问的OS隔离。
5. reviewer可沿用默认Claude Code请求，也可逐实例覆盖。执行与审查优先选不同后端；确需同后端时记录原因并选择相应策略。配置认证的shell应与启动Ergora的环境一致，密钥放外部环境或工具认证配置。
6. 点击“预览冻结合同”，核全部分配、后端／政策、祖先资料、路径与输入，再“确认创建冻结合同”。默认work-units-v2发布正式v6信封；创建只发布合同。显式work-units-v1及旧v5任务保持原合同。

同一模板可有多个同职责专家实例；新增／替换专家先发布独立Agent及沿父链更新的精确工作流版本，再重新预览与冻结新任务。图形页面展示已发布图，拖动布局不会修订合同。详细CLI配置见[工作单元协议](WORKFLOW_DEFINITIONS.md#专长执行者与原工作单元)。

## 4. 运行、批准、验收与恢复

按[正式任务顺序](USAGE.md#正式任务的操作顺序与恢复)启动所选服务并提交原任务。保留task ID、创建／提交intent SHA和原workflow／run ID；运行到plan后阅读实际计划，以稳定decision ID明确批准精确plan SHA，再继续work→integrate→verify→review。

`REVIEW_READY`表示有待维护者检查的精确候选。核candidate、真实检查、所有必需审查与原产物，再导出每任务本地分支，独立复验并走项目自己的MR／合入。模型approve、进程exit0、工单关闭各自都不能替代该流程。

如果新任务使用工单来源v7，导出后还可按[候选远端核对](USAGE.md#核对候选与当前远端分支)比较本地与远端head／base；这只读取当前事实，不推送／关联PR或替代人工审查。无来源的默认v6任务继续走原导出和项目自己的发布流程。

回复丢失时沿原ID查询：创建用`task creation`，提交用`task submission`，批准用`task approval`，导出用`task export-status`；按返回的原意图使用对应resume命令。未知状态先对账，不改ID重发。闭合后再核外部作业和租约。控制目录、执行CONFIG／STATE、Git仓库和Temporal持久数据联合备份；[恢复表](USAGE.md#正式任务的操作顺序与恢复)及[联合备份](BACKUP_RECOVERY.md)给出完整步骤。

## 5. 训练提案与实际实验

训练模板先准备真实workload、baseline、精确实验清单和正确性标准。若只需要专家提案，可用轻量项目`ergora project add PROJECT_ID --repo ABSOLUTE_REPO`，按第一步保存训练完整manifest，并准备UTF-8任务正文，包含所选叶子所需的全部前驱材料。

先完成[第2步的共用运行准备](#2-登记自己的项目)：Linux/WSL2、同一Ergora解释器的task-mcp依赖及所选后端认证。

先完成所选后端支持的认证。Codex可另加`--codex-config ABSOLUTE_CONFIG_PATH`，配置中引用外部凭据环境变量；Claude的bare模式要求其支持的API环境认证。在任务正文要求Agent通过固定task MCP完整读取自己和全部结构祖先的Skill／上下文，长附件连续UTF-8分页到`next_offset: null`。准备好依赖、认证及正文后执行：

```bash
ergora composition prepare-from-manifest TRAINING_MANIFEST_DIRECTORY root/analysis/design --task experiment-task.txt --directory ./prepared-design --max-prompt-bytes 50000
ergora composition check-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend"
ergora composition run-input PROJECT_ID ./prepared-design --mode task-mcp --backend codex --backend-reason "Explicit experiment-design backend" --timeout 300
```

`check-input`只检查能力与输入，不调用模型。完整流程见[单叶调用与读取核验](WORKFLOW_DEFINITIONS.md#调用一个准备好的叶子)。

其他叶子为`root/analysis/profile`、`root/kernel`、`root/measurement/review`。单叶调用没有自动执行前驱，操作者应在新任务正文中明确提供完整来源和前驱回复。审查尽量使用另一后端；调用失败后保留原run，再用明确的`--backend`和`--backend-reason`建立回退调用，不会自动更换后端。认证检查成功仍需真实小调用确认推理可用；上游API错误不能用放宽工具权限来证明已修复。

若任务涉及显存、重计算、CPU卸载、CUDA Graphs或sequence packing，可选[五个独立优化方向根](TRAINING.md#独立的优化方向子模板)。它们保留design／profile／measurement三叶，读取所选方向的完整context并复用v2专家，不含kernel叶；将前两份完整原结果手动交给measurement。安装这些提案包不会安装GPU工具、开启原生搜索或运行整个图。

提案和模型审查供操作者准备实验。实际流程为固定workload／baseline／experiment→可信runner执行→独立正确性／性能复验→人工批准原evidence SHA→该项目开发任务集成复验。ForgeKernel是可选候选生成器，有独立版本、模型与设备要求；生成器完成不代表性能通过或采用。CPU／GPU、数据、ML依赖按项目安装，控制台不会配置CUDA或申请设备。[训练手册](TRAINING.md)说明runner、负结果、取消与采用。

完整Linux参考发行保留两份详细手册：[部署与日常使用](../src/ergora/data/reference/platform/README.zh-CN.md)、[训练优化](../src/ergora/data/reference/platform/docs/TRAINING.md)。它们对应冻结v2.2参考层；新的控制台、组合及v6用法以本指南链接的当前手册为准。单文件HTML内嵌旧参考包及两手册，新增控制面需另外安装当前仓库版本。
