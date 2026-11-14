# F9d1 训练控制面组合验收交付

[验收合同](../plans/2026-11-14-training-control-journey.md)。固定基线 `8d739c298668ab9f7d88fdaa205a21f304d9586c`；初始状态仅完成既有接口、前片驱动和原 F9d 合同的只读盘点，尚未运行本片验收。后续结果在本页逐步记录。

原 F9d 的真实 GPU／B3 比较保持开放，本片不以 CPU 控制或合成归档替代它。原 `training`、操作 checkpoint、Temporal 与证据批准 owner 保持；演示项目独立于用户业务仓库。计划复用 F10d7 最终安装件，运行前直接重核产品身份。

立项时 F10d7 已固定普通发布并获原独立两轴补核，自己的 CI `43583053417` 尚在途，因此当时不推送后继。现其八job／30必要步骤及原 reviewer 终态两轴已全部通过，前继精确交付闭合。

## 首轮控制与浏览器探针

已直接核当前604产品等同F10d7最终非editable安装件。r1沿公开HTTP初始化baseline、登记runner、准备三实验，三次CLI与原件相同；真实Temporal启动alpha／beta，重复与恢复保留原run；alpha精确取消／原回执恢复与原执行器启动前围栏观察通过。beta用明确合成归档经原writer／锁进入AWAITING_RELEASE。

首个浏览器启动未指定现有Chromium配置，缺默认Chrome而退出；复用原浏览器配置后可打开。browser-r1已真实提交gamma，随后整段详情文本比较时未等待beta并行的本地提交记录读取，比较失败；未保存betaBefore，不能重建具体差异或据此判产品缺陷，也不算完整浏览器通过。保留原stdout、被动HTTP和失败快照。主r1以SIGINT进入原finally，三自有服务及浏览器已收尾；未运行runner。r2只调整私有驱动的读取就绪条件，使用新隔离项目从头执行，产品不变。

## r2 完整控制与原终态重启

r2新演示一次35项／125.394526秒、7CLI／28聚合HTTP通过；浏览器13项／21完整样本、三个真实成功回复held及一个私有503、无pageerror。原history三输入／memo／run与checkpoint完全绑定，三run各唯一个预期信号。alpha终态CANCELLED；beta明确合成原归档经精确owner批准只生成原本地集成／复验票据；gamma控制结果CANCEL_UNCONFIRMED，而后原执行器观察CANCELLED，二者分列。28份原准备材料逐字保持，runner未执行。

restart-r1真实从r2同一持久DB重启Temporal，无worker，16项／7CLI／7.936528秒读回三原终态；完整history字节保持，原取消／批准回执不重发，之后服务端口关闭。只证明原终态重启读回，不冒称活动workflow恢复或训练。

## 自身审查实证与私有驱动修正

原structure-review用授权Codex回退，12完整文件140,246B／所有祖先材料直接核实际stdin，57.411577秒request-changes。唯一P2为私有驱动先写passed再finally，且future.result推导式首个异常会跳过其余收集和清理记录；独立reviewer核实，产品finding为0。r2实际exit0、完整cleanup与端口关闭事实保留，不能据此称驱动缺陷已修。原restart驱动同型问题一并修正。

r3只改私有驱动：执行结果先标execution_passed；逐项收集进程／errors并尝试shutdown，保存cleanup后才发布最终passed。新项目一次35项／90.444476秒、7CLI／28聚合HTTP，浏览器13项／21样本／三held／一503／0pageerror通过，最终cleanup errors为空、两端口关闭且父进程exit0。三个原run各一个预期信号；本轮gamma控制终态为CANCELLED，r2的CANCEL_UNCONFIRMED保持原身份，不能混写。源、安装、原准备资料和runner未执行均保持。

针对r3的首个重启驱动误固定了r2的CANCEL_UNCONFIRMED预期，因此断言失败；实际清理仍执行且没有发布passing结果。保留失败，后续按r3实际原outcome比较，不限制有效取消时序。最终重启、自身复审、总引用／进程总核及独立终核接续记录。

## 最终重启、原审查复核与收尾

最终restart-r3以r3同一持久DB真实重启Temporal，无worker，16项／7CLI／7.658418秒通过。读取原三终态和完整Outcome；三份完整history字节与本轮原件相同；原取消恢复保持同一requested，原批准仍可读。cleanup errors为空、端口关闭后才写最终passed。原r2未知停止读回与中间restart失败均保留，未混入r3事实。

自身原模板复审55.810448秒approve，run `37938051fbd34eb5a1416fd71c2f8f94`；17全文162,522B、三个祖先资源、task／prompt／实际stdin经原件审计相同。原模板是text-only，未授磁盘工具；外部文件与运行事实由独立reviewer直接核，模型approve不替代它。原request-changes及P2修正保持记录。

最终audit直接核604源／安装与原固定映射、92组被动HTTP request／response字节、21浏览器样本与28聚合HTTP、17全文实际stdin及祖先资料；原283参考verify成功。四个观察端口均关闭，三成功浏览器daemon已退出，没有匹配本片web／Temporal／原worker的进程。原浏览器r2两张1440px截图已实际目视，最终r3另有同布局截图；本片不扩大为三宽／全部迟到矩阵。

本片沿既有公开接口未发现需要修改产品的行为，既有[训练手册](../TRAINING.md)的准备、提交、取消、证据批准与原票据步骤继续适用，不增加另一份命令参考或冗余测试。G1安装／升级／换机仅立下一阶段计划。最终公共原件索引与新独立两轴终核接续，不以CPU控制或合成归档关闭真实GPU／B3。

## 私有驱动落盘失败边界补核

独立评审补充指出：r3先把execution赋值后再写execution.json，若这次暂存写失败而收尾成功，仍可能写出passing结果。接受同一P2的补充，原r3源码与真实正例保持不改写。私有r4候选仅把该两句合为 `execution = save(...)`，赋值只在完整写成功后发生。没有重跑未变化的产品／Temporal／网页，也不称完整r4原生验收。

finalization-probe-r1从修正源码经AST提取实际赋值和原except／finally，分别注入暂存写失败、首个future结果失败；明确使用假future，不启动服务。两种情况均实际取完全部三个future、尝试shutdown、保存cleanup；原暂存异常继续传播且failure.json存在，清理异常单独保存，均无最终result.json。提取来源及字节SHA、实际calls／原输出保留，作为这个私有错误分支的针对性验证；独立reviewer继续直接复核。自身55.810448秒approve在这次两句私有修正前，不能宣称模型已审后来的r4；产品源码始终相同。

## 原件索引与独立出口准备

[公共摘要与原件索引](evidence/2026-11-14-training-control-journey.json)已生成592条固定引用，共4,766,781B；规范数组SHA256为 `3b0173c12f7e26e5ba4679be833830bfb9f1a74e3bc96c3ff3ef48fb6fb53e9f`。原r1／r2、最终r3及r4私有异常探针的身份和范围分列，不重新生成旧原件。独立报告不递归写入此索引，发布与CI之后另列。产品／schema／依赖／test／CI没有改动，后继G1仅立计划。新独立两轴对最终公共聚合的终核已通过，随后普通发布当前分支，不强推或合main。

前继F10d7固定8d739c2自己的CI43583053417八job／30必要步骤与原reviewer终态两轴现已全部通过，原214／发布5／CI52分列不变，本片发布门禁的前继部分已满足。

## 最终本地独立结论

原fresh-context reviewer已直接全核592引用、实际调用链、最终清理及r4异常路径，需求／维护性两轴均approve，开放0／0，唯一私有驱动P2关闭。[原报告](2026-11-14-training-control-journey-review.md)的本地终态已保存独立快照；该结论不含尚未发生的固定发布、本片自己的CI、G1安装升级或真实GPU／B3。
