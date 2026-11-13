# D2-B2c：并行策略、Megatron FSDP 与分层 CP

基线为B2b普通提交`a711539617ca8d2892d240079e76cb243784c55d`；承接[D2方向计划](../plans/2026-11-13-specialist-presets.md#b2按决策粒度发布资料子模板)和[R4固定来源研究](../research/2026-11-12-optimization-parallelism-agents.md)。本片为三个独立只读资料根，复用精确analysis／measurement v2及原design／profile／measurement三个专家，不新增Agent类、schema、runner、调度或状态账本。

|节点|可验收出口|当前状态|
|---|---|---|
|B2c.0 来源及合同|普通mesh的两组整除／rank映射；FSDP实际flag／checkpoint／恢复；HCP路径／组／独立数值门槛分别明确|三个根九份文件及catalog已实现；R4旧flag已按同pin源码修正，完整知识provenance保留|
|B2c.1 发行及资料继承|三个catalog根，完整祖先、只读权限、原版本／283保持；隔离noneditable安装及受影响preset检查|521产品／两RECORD／283相等；安装20项／84.42秒通过，控制器86.600秒，旧十条catalog及共享包保持|
|B2c.2 实际叶及交接|每根三次独立调用，完整资源和两个原始前驱手动交接；缺硬件／模型／测量仍保留|九叶真实Codex成功，54资源94,170B完整连续UTF8及两份原前驱手动交接通过；三measurement均缺证据request-changes，不宣称自动图或GPU实验|
|B2c.3 审查和交付|自身原结构模板、fresh-context两轴、文档和计划；普通发布／自己的CI另记|原结构模板44.874秒approve，十一文件51,577B完整输入；最终17文件及包／九叶／来源／公开投影获fresh-context两轴终核，开放0／0，本地出口完成|

新增文件由既有catalog安装Module的CLI和HTTP两个生产调用者消费；每方向的context被三个实际叶完整继承，技术差异只在数据包。继续扩展原方向参数化检查，针对漏装、精确引用／材料来源遗漏和离线manifest恢复的可达静默风险，不另建文本算法测试框架。

保留旧十个catalog条目、共享v2包及冻结参考身份。固定来源是知识provenance而非安装栈；新资料需纠正R4表内旧`dist.use_megatron_fsdp`字段，以同pin实际`ddp.use_megatron_fsdp`和源码为准。普通两mesh的LCM仅为共同整除下界，不宣称足以运行任意GTP／自定义layout。HCP需要真实MPU／hierarchical groups与attention调用证据；源码的TE最低版本不等于任意新版组合认证。FSDP的权重reshard与完整续训分别验收。

本片不变更可信训练runner、Forge原生流程、后端准入或执行／采用权限；实际实验与未知恢复留在原所有者。没有实际模型、checkpoint、GPU或多节点运行证据时，交付只授予提案和材料链，不借前片、CPU合成场景或成功调用声明训练收益。

隔离wheel SHA256 `e91f7d2daf15dd0a8bd58afd366670909af43b9f6aa004c598ae64c1aa312837`；从完整基线归档只覆盖本片11份产品／测试文件。521产品在source／wheel／installed相等，wheel529文件和安装534行RECORD分别核hash／size，283冻结参考逐项通过。原preset suite20项覆盖新三方向及旧五方向／原三配方、重构和v2；不称完整suite／CI通过。私有原件保存在本片checks的`install-r1/`及明确source-manifest。

自身审查使用原已安装`ergora-structure-review`，十一份产品／测试完整内联51,577B；实际prompt／stdin57,443B相等，三份结构／自身资源和protocol／结果原件已核。结果SHA256 `8888966502c43f41052c6344c08e03019c2398de8e3da6d56591235f678205bd`，44.874秒approve。原判词明确未直接核共享包／上游／安装身份，调用时preset及实际叶证明仍待核；后续20项安装事实和独立来源核对各自记账，不扩写原模型的审查范围。

## 实际叶、完整材料与边界

三方向各用独立State和三会话；parallelism18资源32,900B、FSDP18资源30,806B、HCP18资源30,464B。原input树摘要、所有结构祖先／自身Skill内容与来源、prompt／实际stdin／protocol、固定scope、native连续UTF8末页null和原result均由同片审计核准。三个measurement任务明确包含design／profile完整原结果，内容及各自SHA一致。[公开投影](evidence/2026-11-13-optimization-parallelism-directions.json)保存调用、输入／结果和原审计身份；不含本机配置或密钥。

输入只是一份未来MoE decoder／BF16／AdamW／8-rank／TP2／PP2／CP1／EP4／ETP1场景，模型／mesh／checkpoint均未实例化；另有两mesh大小4／6的纯整除示例，不称它是已支持的原生layout。三个measurement均为request-changes：保留真实stack／有效配置／拓扑和组、独立loss／梯度／update质量、checkpoint及完整恢复、配对step／token和全rank显存证据缺项。parallelism仅说明LCM必要条件，FSDP不以权重reshard代表续训，HCP不以最低TE版本或建组代表数值通过。已授权的显式Codex回退原因保留，不声称异构后端验收。

原自身审计r1的scope标签沿用旧“focused8”，其实际packet_files、全文与结果始终是11；原件保留，r2仅修正该标签／输出文件名后重新读取原链通过，没有重跑模型或改变产品。原Codex还发起两次内置MCP元资源查询，返回均为空；text-only／mcp=false指没有Ergora task-MCP服务，不写成完全没有工具调用。

[新独立双轴终核](2026-11-13-optimization-parallelism-directions-review.md)已完成，Spec／Standards各自零finding。最终17文件manifest SHA256 `b531c864e3690206a3c5abefbe9dc898be9ee5e2619527af6ca6f7c1431e7650`；包、十条旧catalog／共享包／283、九叶完整原链与所有判词、固定来源及公开投影逐项核准。初始资料／安装与当时真实叶仍待核的观察保留，后续补核不改写早期范围。本地资料片出口通过，普通发布和本候选自己的必要CI另记。
