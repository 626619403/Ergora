# 预训练与后训练代码审查

`pretraining-review` 和 `posttraining-review` 在原结构、正确性、测试价值三位 reviewer 旁各增加一位领域专家。两个根均为只读、四叶 required、显式 all-join，领域专家也有独立子模板。它们复用原定义、权限继承、后端和正式 ReviewDAG，没有安装另一套训练器或审查服务。

这是 Ergora 根据固定 Bridge／slime 方法编写的 reviewer 配方。来源与具体借鉴点随完整 Skill 提供；上游实现身份见 [领域研究](research/2026-11-15-pr-mr-review-tools.md)。它们不代表 NVIDIA／slime 官方 Agent，也不表示通过 GPU、数值、分布式或收敛验收。实际实现与验证进度见 [本片交付](delivery/2026-11-15-training-domain-reviews.md)。

## 选择专家和后端

|Preset／根|领域叶|主要关注|
|---|---|---|
|`pretraining-review`／`ergora-pretraining-review`|`root/domain/review` → `ergora-pretraining-reviewer`|有效 token 与 loss／mask、累积／更新时钟、精度、mesh／collective、状态与恢复|
|`posttraining-review`／`ergora-posttraining-review`|`root/domain/review` → `ergora-posttraining-reviewer`|实际 SFT／偏好／RL 算法、样本／分组／反馈／mask、policy／reference／reward、版本／异步恢复|

两个根还包含 `root/general/structure/review`、`root/general/correctness/review` 和 `root/general/test-value/review`。每个实例继承自己的结构祖先材料和权限上限；领域专家的 Skill 归它自己的 Agent 定义。需要改变专长时导出、派生新版本，再从新根引用，沿 [定义手册](WORKFLOW_DEFINITIONS.md)操作；原版本和在途任务保留。

默认后端为 Claude Code，可按 [后端手册](AGENT_BACKENDS.md)逐实例选择当前支持的后端。执行者／审查者优先使用不同后端；同后端回退记录原因、独立会话与覆盖，不能以多个模型同意替代可信检查。

## 准备完整本地输入

先按 [本地审查包手册](LOCAL_REVIEW.md)保存原需求、精确 base／head、全部变更及显式调用者／配置／检查原件，并 verify。把完整 `review read` 输出作为 task；不能只传回执、作者概述或 diff。

```bash
ergora review read ./candidate-packet --sha256 PACKET_SHA256 > ./review-task.json
ergora composition install-preset pretraining-review
```

下面的 Python 从当前库读取原根的权限／限制生成新 manifest，不预填机器路径或凭据。后训练把 preset 名改为 `posttraining-review`。

```python
from pathlib import Path
from ergora import workflow_definitions as workflows
from ergora.state import State

state = State()
selected = workflows.install_preset(state, "pretraining-review")
root = workflows.get(state, selected["root"]["id"], selected["root"]["version"])["definition"]
grant = {"schema_version": 1, "permissions": root["permissions"], "limits": root["limits"]}
workflows.prepare_manifest(state.root, root["id"], root["version"], grant, Path("pretraining-review-manifest"))
```

为该仓库登记项目后，明确准备和调用一个领域叶。这里使用 Codex 示例；如已有 Claude 认证可选择 `claude-code`。`--backend-reason` 应填写实际选择原因。

```bash
ergora project add training-review --repo /path/to/project
ergora composition prepare-from-manifest ./pretraining-review-manifest root/domain/review \
  --task ./review-task.json --directory ./domain-review-input --max-prompt-bytes 1000000
ergora composition check-input training-review ./domain-review-input --backend codex --mode text-only
ergora composition run-input training-review ./domain-review-input --backend codex \
  --backend-reason 'Use the configured review backend in an independent session' --mode text-only --timeout 600
```

完整输入超限会拒绝，调整所选资料／预算后重新准备；不可静默摘取摘要称完整。`text-only` 将声明的完整资源放进提示词，不提供任意 shell、文件系统或网络工具。返回原 run／输入摘要／结果路径，结果中的 response 保存发现与覆盖缺口。

独立 `run-input` **只调用指定叶**；不会因根有 all-join 而自动运行另外三路。需要互补意见时对三个 general 路径分别准备相同完整 task 并明确调用，保留每份结果和缺失分支。Q2.3 的统一运行／本地报告入口另片。正式开发任务则可按原 `review_protocol: dag-v1` 选择整个根，交原六阶段执行四路及 all-join，保留精确候选、required 分支、批准和恢复；方法见 [原模板旅程](TEMPLATE_WALKTHROUGHS.md)。

## 一次生成 CPU 合同样例

从含此脚本的源码 checkout，使用安装了 Ergora 的解释器运行：

```bash
python examples/review/training_domains.py --directory ./training-review-demo
```

目录须不存在。脚本只创建两份新 Git 样例仓库，执行**本脚本编写的 CPU 算术函数**，保存手工推导 oracle 和 base／regression／valid 三个提交，生成四个精确审查包：

- `pretraining/regression-packet`：不等有效 token 的 microbatch 均值改变了全 token 平均目标；`valid-packet` 改变分组但保留同一目标。
- `posttraining/regression-packet`：固定 response-token contribution 的 mask 丢失，使 prompt／padding 参与目标；`valid-packet` 改变被屏蔽项的数值、位置和数量，保留 response 目标。

`examples.json` 包含完整提交、scalar 结果、各包回执和 SHA256；每个包有原需求、完整源码／调用者／配置／规范和检查原件。按前述 read／prepare／run-input 逐一审阅即可。示例没有模型／数据下载、GPU、真实训练、PPO／GRPO 实现或多卡证明；它检验输入交付和这些具体算术问题，不代表总体检出率。包采集器本身仍不执行项目检查。

## 理解结论

确认问题应带提交／源码位置、实际配置下的可达场景、后果和最小修正；假设、缺资料、未运行检查另列。预训练避免平均口径或更新时钟悄然变化；后训练先识别算法，再核样本／权重／反馈关系。当前结果沿原 reviewer 的 `approve / request-changes` 合同，在 response 中保留覆盖和缺口；独立外部审查的意见不会发表平台 review、合并分支或授予采用权限。
