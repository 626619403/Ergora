# Q2.3b：原运行读取与完整本地审查报告

日期：2026-11-15。依赖[Q2.3a精确输入](2026-11-15-source-bound-review-inputs.md)；产品实施基线在该片普通发布后固定。当前仅完成owner盘点与分片合同，未实现报告。用户要求的kernel专家继续留在v3优化路径。

## 原接口与缺口

`review_packets`／`review_sources`解释完整原来源；`review_requests`将明确来源绑定原完整input；`workflow_definitions`持有冻结manifest、全部祖先资源／权限和input身份；`agent_runs`持有原调用及恢复。CLI只能取最近100条run或有界stdout／stderr，后者不是完整结构化审查结果；不能据此选择最近一次“成功”或宣称整个组合完成。

`agent_runs.output`已有按project＋run ID查原记录的SQL；应沿这个owner扩展精确读取，不能在报告器复制SQL、猜原文件路径或重发模型。`StageDAG`已解释正式review子树／all-join，`require_root_task`解释独立叶是否直接取根task；本片只汇总显式独立叶，不把串行图静态投影冒充执行。

## 实施片与验收

|子片|行为与所有权|验收|
|---|---|---|
|Q2.3b1 原run精确读取|在`agent_runs`及原Agent CLI增加按项目／精确ID的完整观察。保留原metadata和结果全文，核原sealed input、input_request／digest／prompt、原result SHA及结构；不依赖当前后端可用性、最近100条或原绝对目录仍存在。缺件／未完成／错误明确可见，读取不改run、不调用模型。|旧run排在100条之后仍能读、跨项目不串、重新打开或迁移控制目录可读；输入／stdin／结果缺失或身份不符不认证成功。现有output／归档／续接行为保持。新检查在原invocation fixture内验证真实原状态与文件，保留长回复而非测试截断摘要。|
|Q2.3b2 来源与覆盖报告|扩展原`review_requests`应用用例，显式选择完整来源／SHA、manifest／digest和`实例=原run ID`映射。只接直接根task的只读reviewer组合；按所选图列每个预期叶及其声明专长／后端，与每个原run的实际input和来源task核对。完整原回复和少数意见全部保留。|两领域／三通用分支切换，缺叶、failed／running／preparing、错来源／实例／manifest／输入及重复映射明确可见；完整coverage与全部approve／任一request-changes分别判断，不多数投票，不把不完整报告当完整。|
|Q2.3b3 本地交互与实用|薄CLI输出可保存的完整JSON报告；人可读报告按同一观察生成，不再跑模型。报告带完整材料、原run／input／result身份、覆盖、实际后端及原因、明确未验范围。文件由操作者保存，不引入第二运行账本、持久格式迁移或自动平台动作。|新非editable安装／实际CLI；使用Q2.3a已保留的真实run读回完整领域结果，再明确运行同来源其余分支验完整覆盖。所有源与原run保持，重复生成不自动发请求。原结果不足以宣称训练／GPU／质量／性能验收。|
|Q2.3b4 审查与交付|每片更新计划／交付；原结构模板及新的fresh-context独立评审，处理finding后普通推送当前开发分支并核完整Ref；自己的适用CI和原终核单独闭合。|不合main，不从Q2.3a或其他旧片继承CI身份；不扩大为正式候选／平台批准。|

Q2.3b1先闭合可复用的原件读取合同，b2／b3随后使用，避免同时改运行owner与报告语义后难以定位问题。若一个小片能完整验证所有义务可合并交付，但原状态、身份与证据不能省略。

## 数据与边界

原run记录、完整冻结input、原结构化result和实际stdin各保持自己的身份，报告只是只读观察。读取由原owner使用控制目录中的原存储槽位，不把持久metadata里的绝对路径当作任意文件读取授权；控制目录搬迁不要求把历史metadata重写成新记录。需要新增容量限制时显式拒绝完整报告，不静默截断；沿已有结构化结果schema／JSON reader处理，不自己发明另一种Agent结果协议。

报告应分别呈现覆盖完整性、证据是否可核及模型建议：一个叶的request-changes不能被其余approve抹去，缺失／失败／不可核也不能变成通过。历史运行的已观察后端和资源保持；当前配置变化不触发重新准入或改写原run。

首版不调度图、自动补跑缺叶、远端评论、行级意见、approve／merge或修改目标项目。不接新云服务、通知或工单写入；需要这些功能时沿原intent／attempt／receipt／unknown和Temporal预算另立消费者。完成报告后接Q4.2有界循环及Q5.2按实际维护问题重构，不取消原真实B3／完整Forge的开放条件。

## 当前进度

1. 已读原input编译／校验、根任务约束、原run存储／output及结果schema／实际调用路径。
2. 待Q2.3a本地独立审查和普通发布后固定基线，开始b1，记录实际命令和验收。
3. API参数和报告字段在实施片依据实际消费者固定；上表不是已经可用的CLI声明。
