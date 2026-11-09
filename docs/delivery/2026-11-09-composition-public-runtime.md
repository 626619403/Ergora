# CR3c / E4：公开单叶组合运行入口

日期：2026-11-09。状态：已调查调用链，待CR3b完成后开始实现；本文件不声明新行为已可用。实现基线须在CR3b普通提交后固定。

本片接通已支持形状的v2 start/status和常驻executor双请求根扫描，复用原Submission的创建核验、attempt-before-send、memo及原run恢复，复用原Temporal六阶段与受监控Executor。它不增加另一套调度或正式账本；Supervisor完整生命周期和备份出口分别仍属CR4/AC3c.4，多成员嵌套执行属AC4。

## 调查与拟定改动

- `CompositionInput.require_submission`目前无条件拒绝；`tasks.status`也拒绝。将单只读review叶、所有结构祖先task直接映射且无依赖的形状检查归到标准库`task_envelopes`，供版本输入和实际Executor共用。创建/历史读取仍能保存并核验未来尚不支持的静态组合；只有执行准入拒绝，不把可读性与可运行性混为一谈。
- `reference_task_runtime._status`目前把原文档当legacy传`workflow_id`/poll；改用`execution_input`的legacy投影计算ID与原transport调用，`VerifiedSpecClient`保留完整原文档核历史身份。公开`tasks.status`向它发送保存的完整admission，不能只发legacy投影。
- 版本输入注册映射拥有请求根；常驻executor从这个合同取得所有根，复用现有active/receipt/rejected处理与并发上限。旧冻结executor继续只读旧根。不能在常驻线程内构造_Creation。
- 历史摘要的runtime_supported只表示当前运行桥支持的静态形状，不能表示后端已认证、服务就绪、完整图端口已执行或任意成员调度已实现。需要公开说明当前限制及实际调用来源。

## 验收节点

- [ ] P1：单形状规则只有一个所有者；可支持单叶通过，多成员/非只读/非直接输入在任何Submission dispatch/intent之前明确拒绝。创建、历史和无SDK诊断顺序保持。
- [ ] P2：v2公开查询同完整历史身份，same-legacy/different-manifest拒绝；原not_found/unknown与只读行为保持，v1合同回归。
- [ ] P3：常驻双根实际消费，不重复执行，原候选/批准/receipt绑定，原型别worker不误消费；未支持形状明确失败。
- [ ] P4：非editable安装包上的真实本地Temporal/worker/常驻executor公开CLI旅程，原owner批准和原回执，至少一条v2和一条v1；模型协议合成与实际模型能力分别记账，不把fixture当真实模型。
- [ ] P5：发行与283冻结身份、相关合同回归、fresh-context独立两轴审查、自身结构模板实际调用、普通推送及精确必要CI/远端。

每一验证结果按真实原件/源身份追加；先完成内部执行桥再开放入口，不能把先前手工调用六阶段fixture当本片Temporal验收。测试和源码范围按实际变更收敛，保持既有CI矩阵。
