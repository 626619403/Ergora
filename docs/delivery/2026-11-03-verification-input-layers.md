# V1：纯输入检查与真实任务集成分层

2026-11-03，依据[独立成本审计](2026-11-03-verification-redundancy-review.md)及[V1–V3计划](../plans/2026-11-03-verification-efficiency.md)。前置F3.4b1已收口并推送b55af5d；本切片实施基线`b55af5d89ff2802ff3afd0125d396f80522942f6`，其中生产/测试仍为a2349e8。本记录保留原合同、首轮及修后身份；V1实现、验收、独立审查及候选推送现均完成。

## 范围与所有权

五个任务入口族的36个既有参数案例已在不启动fixture的情况下提取到`.ergora/checks/verification-input-layers/baseline-case-map.json`，包括源文件SHA、原函数、原始参数值和错误期望。29例只需Python服务入口即可拒绝；其余原run归属和Git分支语法仍真实集成。每族再保留一个早期拒绝的真实任务检查，分别验证原生文件/journal/lease/RPC没有副作用。迁移后案例语义并集覆盖原36例，不以减少测试数验收。

新的轻量测试文件只拥有这些公共服务输入案例，直接调用实际tasks入口，在项目读取/原生准备边界设置禁止访问哨兵；不建立通用fixture框架，不mock被测输入校验。原各任务测试保留集成与CLI/API错误映射。B1证据夹具使用原提交基底及真实工作流context/FileAdapter文件，省去与只读查询无关的bare候选Git；导出夹具继续真实Git。复用的SQLite lease测试helper显式close连接，不改变断言为忽略WAL/SHM。

仅测试及CI耗时诊断变更；生产源码、依赖、JSON/六阶段合同、冻结283、CLI/API行为、CI矩阵和触发保持。下一次本就必跑的完整CI输出`--durations=20`，不额外为性能榜单执行全套。Linux提前skip和concurrency分别留V2/V3。

## 验收与记录

先核原案例映射，再跑29个轻量矩阵、每族保留拒绝及代表性正常集成、两模板真实原提交/证据文件；同环境对比审计原三节点的setup/call，不外推整体加速比例。最终完整两OS CI保留原必需门禁；新fresh-context reviewer检查覆盖没有丢失、边界哨兵有效、夹具来源/隔离和资源关闭。生产未改不重建本地同一包或重跑无关CLI旅程，仍核现有包与生产源码身份。

当前状态：完成。测试分层、原36例语义保持、真实副作用修正、独立复审、精确两OS CI及实时远端均已通过。

## 实现与首轮检查

新增`tests/test_task_inputs.py`直接调用五个真实tasks入口；仅mock禁止触达的项目读取/原生准备边界，没有替换输入判定。29个原格式/类型/确认/预算参数保持，首次 **29 passed（0.38秒）**，87份setup/call/teardown计时均小于5ms。该计时属于轻量矩阵，不是全套加速比例，原三用例9.26秒/7.39秒setup成本仍引用原审计测量。

五个原集成函数保留12实例：7个必须读取原run或Git的案例，以及每族1个真实任务上的早期拒绝。逐值/严格JSON类型核对，原36案例的语义并集等于新29轻量＋12集成实例，减少24次重型初始化；没有删除参数反例。原参数、源SHA及映射见baseline-case-map.json/case-parity.json。

原`submitted_creation`夹具增加实际消费的模板参数，默认值仍治理模板；B1复用它及原_start，生成原spec/context与真实FileAdapter记录，candidate采用现有基线SHA，不再为只读证据构建bare候选。导出继续原真实Git夹具。原lease helper改用closing显式释放SQLite连接。CI仅增加durations输出，不变更测试选择、矩阵或触发。生产347个文件及52d26d…安装包保持。

相关集成/输入检查 **91 passed（297.31秒，1个已有Starlette/httpx warning，退出0）**，包括全部48个分层后的B1用例、29纯输入、其他保留拒绝和正常批准/取消/两模板导出。integration.log/command/json与JUnit XML保留精确命令及耗时。第一项B1 setup达6.91秒，不能以本次总时间与旧不同子集比较并宣称B1 fixture整体加速；仅记录省去的无关Git操作和已确认轻量输入成本。

实际重算全部347生产资源与最终B1包清单一致；无生产、依赖或冻结内容变更。七个测试/CI文件身份在source-identity.json，aggregate `3902d0dad8a44ddcd45a62a1cc7230cba0dbec81e301864f4bf90cdf707fb951`。首轮时独立审查和精确两OS完整CI尚未完成，不以该首轮结果独立宣称V1已交付。完整本地包/CLI旅程没有因测试层调整而无理由重跑。

## 独立首审与最小修正

[新上下文首审](2026-11-03-verification-input-layers-review.md)接受输入分层、严格案例并集、两模板真实fixture、SQLite显式close及CI仅诊断改动。独立29项轻量（0.16秒）、10个内存哨兵反证、lease连接生命周期及347生产文件身份均通过；发现一项中等验收缺口：原各族保留的局部not_recorded/signal/connect断言不足以支持完整文件、lease及RPC均不变的合同。

修正仅复用现有`test_task_creation._files`，在五族12个保留集成实例的被拒调用前后比较runtime根的全部文件字节，包括原task、journal、完整lease数据库及SDK fixture调用日志，随后再执行原状态查询。导出另比较真实注册repo全部文件（含`.git`的refs/HEAD/index）及一份未跟踪用户文件；没有增加通用fixture、参数案例或重复等价计数。原正常门禁及反例不变。

修正定向 **12 passed（64.78秒，退出0）**，命令、日志和JUnit为`fix-command.json`、`fix.log`、`fix.xml`，只重验受影响实例，未再运行原91项或重建包。修后七文件aggregate为`b60cd879d9bb7ca0b358ea0490d53c9e45ea88410b3f8e03867931aa736276d1`，见`final-source-identity.json`和`final-tracked.diff`；首候选`3902d0d…`、原91项日志及首审探针保留原身份。修后当时复审与精确CI尚待完成，最终结果见下文。

同切片源码复审通过，原中等finding关闭；独立重算修后七SHA/aggregate、36例严格语义并集、347生产资源及12项日志/XML/退出码均一致。实际测试与原`_files` AST的独立小探针验证7种journal/RPC/lease/Git/用户文件/产物改变均被揭露且先于status查询，5个无变更对照通过；没有新finding。证据为`reviewer/recheck_fix.py`、`fix-recheck.json`，未再执行91项。下一步提交精确测试/CI候选并核两OS完整门禁。

## 精确候选与最终交付

七文件已提交并推送`4e01a4e53b9c1d787cf40ce8650d3397cc83b252`，远端同名工作分支SHA已核一致。CI运行[`41605898404`](https://github.com/626619403/Ergora/actions/runs/41605898404)已完成并成功。候选生产347文件及原52d26d…包身份保持；未改生产而重新构建的本地相同包或重跑基础CLI均无必要。当前6份活动/审查/后续合同文档共117个本地链接已通过，见`document-links.json`。

后续[V2](2026-11-03-platform-test-scheduling.md)与[V3](2026-11-03-ci-scheduling.md)保留独立实施提交和新的源码审查；V2源码审查通过后再实施V3，最终共同推送候选的两OS完整CI可同时验收未再变化的V2测试身份及V3工作流身份，避免为两个相邻测试调度变更连续运行两套完整矩阵。各节点只有获得这一精确候选的最终证据才完成，不借用本V1或旧生产CI。

精确CI最终核验通过：Ubuntu作业`125815505886`的Build and install wheel / Packaged reference identity / Native application regression三必需步骤成功；Windows作业`125815506254`另含PowerShell 5.1 installer and upgrade四必需步骤均成功。`ci/fetch-ci.py`及`ci/verify-ci.py`退出0，原HTML、selection和`ci-html-status.json`均绑定完整40位4e01a4e…候选；源码复审finding保持关闭。独立最终CI/远端核对现已通过。

最终独立复核通过，无未解决finding：审查者从官方Actions原HTML重新选择精确4e01a4e…，核两作业completed、Ubuntu3/Windows4必需步骤、完整SHA日志URL/起止时间及五页面摘要；git提交恰七文件，各blob/工作树/最终identity一致，生产347资源保持。2026-11-03 09:03:04 UTC实时远端仍为同一4e01a4e…；`reviewer/final_ci_review.py`退出0，证据`final-ci-remote-review.json`。没有远端逐例console计时，未报告Windows或全套加速比例。V1完成，下一项V2平台提前skip，随后V3共同最终候选，再接F3.4b2。
