# Q3.1：流程图谱交付记录

日期：2026-11-15。范围见 [具体计划](../plans/2026-11-15-training-flow-maps.md)。基线 `0b5b5f1ff7a3463fcb10cf5a05e5f7c7bcae7c62`；开始时仅本片两份准备文档未提交。Q2 产品／测试与独立审查原件保留 628 产品身份，本片使用独立安装环境。

|步骤|实际状态|
|---|---|
|研究与 owner 复核|复用 Q0 固定研究，读取原 analyst／designer／kernel／measurement 合同、原 baseline／实验 manifest 和 preset owner。W1 十三份捕获文件仍在私有证据位置。|
|合同|已写最小变化／验收计划：算法图、执行依赖图、生命周期表、可证伪冗余假设、必要依赖与缺证据请求。kernel 评估保留在后续总路径。|
|实现|已新增只读流程 Agent、完整自包含 Skill 和独立 `root/map` 子模板，在原 catalog 注册；31 preset。旧定义及运行 owner 未改，根不会自动调用 kernel 或实验。|
|安装与回归|独立不继承 system-site-packages 的 venv 安装非 editable wheel；633 源／包／安装逐字相同、283 参考 PASS。原 preset／架构及页面全 catalog 用例 **54 passed／76.78 秒**。Skill 原 quick_validate 通过。|
|真实使用与审查|新安装叶已完成 W1 十三份固定真实源码的单次只读图谱调用，218.156 秒／succeeded；两个图、生命周期表、必要依赖与一项有界诊断假设已核源码，保留缺失 runtime 边界。自身原结构模板 39.202 秒／approve；新独立两轴 approve／开放0／0。提交／远端和自己的 CI 未完成。|

本片不声明业务训练流程完整、测得瓶颈或性能收益；不关闭 Q3.2／Q3.3、Q4、真实 B3 或完整 Forge 的验收条件。

## 产品与安装身份

r1 wheel SHA256 `01dc68055211060a3193efb35480178087f549d33787ecfe042c66e38d4d3e28`，633 产品文件与源／实际安装逐字相同；相对 Q2 仅新增 Agent 三文件、workflow 两文件与 catalog 一条目，没有删除或修改旧定义／其他运行代码。Q2 的原 628 安装件保持，不以新环境替代它的验收身份。

安装回归命令为原 `tests/test_presets.py`、`tests/test_architecture_boundaries.py` 及原页面 `test_empty_global_library_imports_all_presets_and_shares_exact_cli_versions`，**54 passed／76.78 秒**，零失败／跳过。新测试保护原 v1／v2 可共装、独立叶权限和冻结后移除活动库仍可完整准备；不对提示词措辞写断言，不新增 CI job。

## 真实源码图谱旅程

原 Codex run `b86f90904e3c4a1b8db1d702a74ccff8`：**218.156 秒／succeeded**，单次显式只读 `text-only`，没有重试或调用其他节点。十三份源原件／93,748B、完整 task 和三份父／叶资源均在实际 stdin，准备 prompt＝stdin；input digest `22c05f2afb3071d3df703260b1a301437cf9b40a2b5c89d4327159248d3dd6b8`，原结果 SHA256 `a3ab076dec7ee92be6455c39f443bed00c0604c3ae40cb7a6c851e67464cd971`。源索引／输入／回复仅存私有证据，不公开分发业务实现。

原回复分别给出算法图、主机执行／依赖图和状态生命周期表，以实际路径／函数／赋值锚点追溯。它用明确标签区分已观察源码、配置／文档合同、条件推断和未给实现；外部 trainer／model／loader／checkpoint 的实际执行、分布式参与和恢复仍未知，未把这十三文件称为完整目标。人工核入口构造顺序、阶段／累计时钟、微步 forward／loss 接口、清理和 profiler 源码与所述锚点相符。

必要依赖包含冻结模块仍可能需保留输入梯度、完整更新边界和新样本贡献。唯一去冗余假设针对诊断器的相邻同步：只有实际调用者能证明中间没有新设备工作、且归因／完成语义不变时才可能复用；实际训练是否使用该诊断器也未绑定。它要求先补调用者，明确诊断开销降低不等于未插桩训练加速；没有提出已证实的训练路径瓶颈或虚构候选收益。

共享业务仓库的 HEAD 与完整 status 字节前后相同；未对所有 WIP 内容逐字取样，不扩大为整仓库认证。没有执行训练／parser／profiler、读取数据／权重、申请设备、修改业务源码或采用候选。Q3.2 的实际 baseline／成对测量仍须原 owner 准入；源图只作为后续调查的材料。

## 自身模板审查

原结构模板 run `a70641055ece4a6a9c1317261d227c95`，39.202 秒／succeeded／approve。21 份完整文件共 424,593B，完整 task 及全部父／叶资源均在实际 stdin，准备 prompt＝stdin；input digest `f257946519a58eeeba9010904f3fcb03809290e0ad403230669e6a837e56153a`，原结果 SHA256 `70fbd0a9e8f5990af03da343acb62cd23ddf10dfa37dae88789f339d8be2ab4e`。使用用户授权的 Codex 替代后端，保留此前大材料 Claude 超时的选择原因，不称异后端验证成功。

它确认新叶沿现有 definitions／preset／manifest／input／run owner，冻结与祖先资料／权限合同保留；未引入调度、训练、指标或批准权威。本次只是所给完整文本的结构审查，不认证安装、摘要、CI 或私有业务运行；这些由实际检查及新 fresh-context 独立审查分别核对。

## 独立本地验收

新 [fresh-context 独立报告](2026-11-15-training-flow-maps-review.md)核完整 17 文件／实际邻近 owner 与原证据，重算 633 产品身份、输入／stdin／结果及共享仓库前后观察；原 Q2 的 628 安装件仍保持。独立源码核对确认真实回复的两图、生命周期、必要梯度／新样本依赖和有条件诊断假设符合已给源码，没有把缺失 runtime 或源码推断称为实测事实。

另行有界安装重验 **8 passed／1.33 秒**，包含新叶冻结共装、四种权限扩大、完整祖先资料、预算／容量拒绝；283 参考另核 PASS。需求／维护性两轴 **approve**，实质 finding／开放记录问题 **0／0**。14 份本片及相关 Markdown 的 362 本地链接与 fragment 检查零错误；此为本地文档检查，不验证外网。普通提交／推送和自己的 CI 尚待完成，不借前片结果认证。

## 本地固定提交

已提交 `2729b81a4c10e4bf8c77bd78ea4165b0a64cb0c0`，唯一父为本片完整基线，19 个实际 blob 与暂存清单逐字匹配，全范围空白检查通过。含新独立报告后的最终文档检查为15份 Markdown／365个本地链接与 fragment／零错误；之前14份／362条是写入报告前的原检查。暂不普通推送，先等待 Q2 自己的 CI 终态，避免既有 concurrency 策略取消前片；不称本片已远端发布或 CI 成功。Q3.2 的合同审计和用户入口在新片继续，不能改变此633产品身份。
