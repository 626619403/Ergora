# Q2.1／Q2.2：领域审查组合交付记录

日期：2026-11-15。范围与验收见 [具体计划](../plans/2026-11-15-training-domain-reviews.md)。基线 `ad168810b6caa9ed435d0b3fef833856c286edf9`；开始时 Q1.1 仅有发布／独立补核记录更新，产品与测试干净。

|步骤|实际状态|
|---|---|
|恢复与合同|已核 Q1.1 固定发布、原领域研究、Agent／Workflow／preset／ReviewDAG owners；具体片计划已写。开始时 Q1 CI 在途，随后其 Windows fixture 失败及修正单独发布；新 SHA CI 仍待终态。|
|方法|延续工程／代码质量 Skill，新增领域 Skill 编写采用 writing-for-agents 与 skill-creator；引用 Q0 固定来源，不复制未知许可工具。|
|实现|已新增两位领域 Agent／完整 Skill、两份独立叶与两份四路嵌套 all-join 根，在原 catalog 注册；旧定义未改。标准库 CPU 样例与四次真实领域叶调用均完成。|
|验证／审查／发布|两份 Skill 原 quick_validate 通过；首轮 source-only 45 通过／1 环境失败保留。独立 venv 非 editable 安装后原 preset／ReviewDAG／导入边界 **61 passed／76.43 秒**，零跳过；补 Web 依赖后原页面 suite **21 passed／24.92 秒**。628 产品源／wheel／安装逐字相同，283 参考 PASS；四次真实领域叶均完成。自身模板和新独立两轴 **approve**，开放 0／0；已普通发布 0b5b5f1／完整 Ref 一致，其自己的 CI 在途。|

固定发布独立补核已完成，两轴 approve／开放0／0；下一步完成自己的 CI 终核。Q2.3 自动报告和真实训练均另片。

## 安装与 CPU 样例

首次 source-only 的失败是既有离线 CLI 测试用隔离解释器 `-I` 时没有安装 Ergora；45 项通过不作为安装验收。现已在不继承 system-site-packages 的独立 venv 安装非 editable wheel 与所需测试依赖，以该解释器 `-I -m pytest tests/test_presets.py tests/test_review_dags.py tests/test_architecture_boundaries.py` 实跑，**61 passed／76.43 秒**。

用同一安装解释器执行公开 `examples/review/training_domains.py`，生成两份新 Git 仓库／四个完整包。预训练手工 oracle 为 `30/4 = 7.5`：baseline／有效重分组均 7.5，平均 microbatch 均值的回归为 5.333333333333333；后训练固定 response contribution 的 oracle 为 `6/2 = 3`：baseline／增加重排 masked 项均 3，丢 mask 回归为 51.5。每包均保留原需求、四个源／规范／调用者／配置文件、提交和检查原件；只验证这些具体 CPU 算术合同，不是训练、PPO／GRPO、多卡、质量或性能验收。

随后已按每包原 SHA 完整 read、冻结同一领域根，逐包调用 `root/domain/review`；实际 stdin 的完整 task 和父／叶资源均已核对，缺陷／有效配置结论与覆盖见下节。沿原授权采用 Codex 替代，记录此前较大 Claude 审查超时的选择原因，不宣称本片发生新的 Claude 失败或异后端成功。

## 最终产品包与四次真实叶调用

审查差异固定到 Q1 测试修正提交 `a38dd21891ac200c575e8520c49cc82f97c9d478`；其产品与原起始基线相同。r2 wheel SHA256 `3d7c5e71d4b7b17ece885ce7bf72321d336d351411d4142c9504e433a9b03e60`，**628 产品文件**的源／wheel／安装逐字匹配；r1→r2 产品亦逐字相同，仅 README 包元数据随文档更新。283 冻结参考 PASS。页面 suite 首次因未装可选 Web 依赖而整模块跳过／exit 5，保留；安装声明的 Web 依赖后 **21 passed／24.92 秒**，包含全部 preset 的页面导入与 CLI 精确版本一致。包升级尚未结束时提前启动的身份检查与 reference 检查曾因文件替换窗口失败，原失败保留；确认 pip exit 0 后重验身份与 reference 通过，不作为产品缺陷或旧包验收。

四份 `review read` 的完整 task（6,321／6,193／6,485／6,516B）和各自四份父／叶资源均在实际 stdin；准备 prompt 与 stdin 逐字相同。所有调用都是原 `text-only`／Codex，未授权执行项目代码；四份完整 packet 的 SHA256 和原结果随原 run 保存。

|具体 CPU 合同|原 run|耗时／决策|实际回应|
|---|---|---|---|
|预训练归一回归|`1e418e2974524293bdb0ac057f005938`|24.376 秒／request-changes|指出 `loss.py:3` 的均值之均值，推导 16/3 与 15/2 的偏差及最小修正|
|预训练有效重分组|`1e18b62153d8440bb5b4f31b46cc3de3`|22.975 秒／approve|保留四贡献及全 token 分母，未报告该范围缺陷|
|后训练丢 mask 回归|`5901fefe11ef49b289d27ea5f9fe8f1c`|19.042 秒／request-changes|指出 `loss.py:3` 将 masked 值纳入分子／分母，推导 51.5 与 3 的偏差|
|后训练有效 masked 变体|`70e725dd85c84c8b8103182f4860cbc6`|23.625 秒／approve|推导分子 6、分母 2，未报告该范围缺陷|

回应均说明只读、操作员检查未独立执行、其他三路未运行／all-join 未认证。两个特定缺陷被发现、两个有效变体未见误报；该小例的检查输出本身已带 scalar 结果，证明的是完整输入、Skill 和具体合同的交付／解释，不是盲测、总体检出率或训练数学／分布式／质量／性能认证。自身原结构模板与新 fresh-context 独立终核均通过；Q2.3 自动根运行与汇总未实现。

## 自身模板与独立审查

原 `ergora-structure-review` 真实 Codex run `abecaacd1ac440588153f69506683085`：**24.281 秒／succeeded／approve**；29 份完整文件／365,465B，完整任务与全部声明父／叶资源在实际 stdin，准备 prompt＝stdin。input digest `4f63293d3efb554a2c6ba3753e771f0cf500e71f024db8e8660928ba6a931091`，原结果 SHA256 `61530031b71bc3a6003316a56339389d6189250743756103a6f2a5833ee38e6a`。所供文本 verdict 只覆盖源码合同；未让模型声明它观察了安装、Windows、远端或 CI。

新的 [fresh-context 独立报告](2026-11-15-training-domain-reviews-review.md)已核原要求、固定 `a38dd21…` 基线、24 个 tracked／untracked 全文、实际安装／四调用／自身审查原件。独立重算 628 产品身份及四包／所有输入／结果；另跑四项正式准入／冻结检查 **4 passed／10.27 秒** 与 283 参考 PASS。两轴本地 **approve**，无实质代码／合同／测试 finding；C1 的四处旧状态描述已最小修正并关闭，开放实质／记录问题 0／0。

本地终核后完成下节精确提交／推送，本片自己的适用 CI 待终态。Q1 修正自己的 CI 保持原身份，Q2 发布没有取消它。Q3.1 另片，不纳入本片提交与 628 产品验收。

## 固定发布

已普通发布 `0b5b5f1ff7a3463fcb10cf5a05e5f7c7bcae7c62`，唯一父 `a38dd21891ac200c575e8520c49cc82f97c9d478`，25 个文件含独立报告。暂存全范围空白检查通过，16 份本片 Markdown／325 个本地链接或 fragment／零错误；25 个实际提交 blob 与暂存记录逐字相同，完整远端 Ref 相同。Q3 的新产品／资料保持未提交，未混入该 SHA。

自己的 [Portability 43621692177](https://github.com/626619403/Ergora/actions/runs/43621692177) 仍待终态；第二次官方完整分页观察为 plan／Linux 六组成功，Windows 应用回归仍在运行，不能用前片成功认证 Q2。Q1 修正自己的全部 30 必要步骤已在 Q2 推送前成功。原独立审查者已补核固定提交 25 blob、完整远端 Ref 及 628 固定提交／wheel／安装产品，两轴 approve／开放0／0，未借更新中的 Q3 worktree 认证。真实 B3、完整 Forge、整根四路实际运行及 Q2.3 保持原范围。
