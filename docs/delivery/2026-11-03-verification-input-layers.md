# V1：纯输入检查与真实任务集成分层

2026-11-03，依据[独立成本审计](2026-11-03-verification-redundancy-review.md)及[V1–V3计划](../plans/2026-11-03-verification-efficiency.md)。前置为F3.4b1发行收口；本记录先固定切片合同，尚未修改测试或CI。生产/测试基线为a2349e8，具体实施HEAD在前置文档提交后记录。

## 范围与所有权

五个任务入口族的36个既有参数案例已在不启动fixture的情况下提取到`.ergora/checks/verification-input-layers/baseline-case-map.json`，包括源文件SHA、原函数、原始参数值和错误期望。29例只需Python服务入口即可拒绝；其余原run归属和Git分支语法仍真实集成。每族再保留一个早期拒绝的真实任务检查，分别验证原生文件/journal/lease/RPC没有副作用。迁移后案例语义并集覆盖原36例，不以减少测试数验收。

新的轻量测试文件只拥有这些公共服务输入案例，直接调用实际tasks入口，在项目读取/原生准备边界设置禁止访问哨兵；不建立通用fixture框架，不mock被测输入校验。原各任务测试保留集成与CLI/API错误映射。B1证据夹具使用原提交基底及真实工作流context/FileAdapter文件，省去与只读查询无关的bare候选Git；导出夹具继续真实Git。复用的SQLite lease测试helper显式close连接，不改变断言为忽略WAL/SHM。

仅测试及CI耗时诊断变更；生产源码、依赖、JSON/六阶段合同、冻结283、CLI/API行为、CI矩阵和触发保持。下一次本就必跑的完整CI输出`--durations=20`，不额外为性能榜单执行全套。Linux提前skip和concurrency分别留V2/V3。

## 验收与记录

先核原案例映射，再跑29个轻量矩阵、每族保留拒绝及代表性正常集成、两模板真实原提交/证据文件；同环境对比审计原三节点的setup/call，不外推整体加速比例。最终完整两OS CI保留原必需门禁；新fresh-context reviewer检查覆盖没有丢失、边界哨兵有效、夹具来源/隔离和资源关闭。生产未改不重建本地同一包或重跑无关CLI旅程，仍核现有包与生产源码身份。

当前状态：合同与原参数清单已记录；实现、验证、独立审查及提交推送均待完成。
