# 受监管进程的慢读取大输入修正

基线`e2bbde0bec4750b2e3a1d09d8597bf94196ba1bd`。A2两轮review的input约71KB、stdin记录完整但native stdout为空；第二轮在存活Codex的stdin pipe和原Python owner之间仍有打开的写端。原最小复现以425,984B混合UTF8／CRLF正文、启动后350ms才读取的标准库子进程，沿原`processes.run(supervised=True)`运行：3秒外部停止条件触发，状态cancelled、stdout空、全文未送达。独立于模型、provider、Temporal和模板。

Python的首次`communicate(payload, timeout=.2)`可能在输入尚未写完前超时；当前监督循环随后传None，原communicate重入不会继续注册stdin写事件。子进程因此等不到完整输入与EOF。这个可复现条件与A2观测一致；首轮取消的原底层原因没有被事后强行改写为已证明，修正后需新的独立任务验证。

已修改原`processes.run`的公共POSIX输入传递：让子进程直接从已有、已完整记录的stdin快照文件读取，不在监督短轮询中增量写管道。保留原取消回调、进程归属、finalizer、清理与预算owner；Windows原JSON启动gate不变。测试在独立controller进程内调用supervised，防止subreaper影响pytest本身；真实慢reader核完整UTF8／换行字节摘要，不用mock推断交付。

|节点|出口|状态|
|---|---|---|
|S0 最小复现|原安装包独立child失败；源码回归先red|原probe失败已保留；新增真实源码回归1 failed／5.21秒|
|S1 修正／回归|仅原进程owner与一项真实回归；必要输入／取消／后代清理受影响检查|源码回归先red后1 passed／0.50秒；原组合源码检查300秒外部上限停止，未记通过。相同候选的隔离安装分组检查：processes／budget_jobs 18 passed／4 Windows专属skipped／114.69秒；composition_executor 22 passed／204.58秒|
|S2 安装／实际验收|同候选非editable包身份；慢reader原复现变绿；本项目模板审查；A2重新建立独立task／预算|497产品／两RECORD／283冻结身份通过，原probe在安装包0.409秒完整读取；自身原结构模板37.563秒approve，两源码全文内联。新A2等待历史增长依赖修正，仍开放|
|S3 独立审查／交付|新fresh-context完整两轴与原件，记录未验Windows／CI；普通提交／远端及自己的必要CI|四文件初审及安装／自身模板与最终文档同片补核Spec／Standards均0 finding；新A2在独立task运行，远端／自己的CI未验|

## 安装与受影响检查

仅从上述基线叠加`processes.py`和`test_processes.py`构建非editable包，不混入暂存B2a方向数据。wheel SHA256为`e2c0ce33bd576825d19f3526f895225ef9edab56b5d63d94bf49569f8d75d8bb`，497产品文件逐字节等于隔离源码与安装目录，wheel／安装RECORD以及283参考文件摘要通过。该安装的原慢reader复现交付425,984B、同一摘要`287dd78145d9feadcc9d095e8056e05bcff9629c43d9bf8b8620e4d3e39d8f6d`。

安装后的两组受影响检查共40 passed／4 skipped，包含取消、超时、后代清理、原锁与预算恢复，以及原组合六阶段、输入拒绝和失败审查。合并源码检查的原300秒超时保留，不以分组通过改写。Windows运行未验，跳过项只表示平台条件。

以本项目安装的原structure-review模板执行独立Codex会话，用户已授权Claude失败后的回退。两份产品／测试文件共15,247B全文进入prompt，prompt／stdin逐字相等，37.563秒返回approve；不宣称异构后端。原结果SHA256为`4ab3971ba10acbff3b38de851d63e10d0236ef169b4da472378406835b832a18`。该聚焦模型审查没有覆盖其他在途方向数据，完整候选仍由fresh-context评审核对。原件位于本项目本地checks中的`supervised-stdin`，安装身份、分组终态、输入清单和原模型输出均保留。

同片独立补核已核安装三树、两RECORD、283参考文件、40 passed／4 skipped及全部模型输入／protocol／stdin／原结果，Spec／Standards开放0／0。原fixed-r1 probe未自记解释器身份；保留其缺件后新增独立fixed-r2，明确记录已核安装解释器、package位置和`processes.py`摘要，再次0.410秒完整交付相同正文，原件获独立核准。新A2和发布出口继续开放。

B2a方向数据和测试独立保留，未将其混入本片发行；不为该问题增加新调度器或预算。第二轮A2的原cancel入口已尝试，返回服务连接拒绝；其驱动读到TERMINATED／NEEDS_RECONCILIATION后shutdown，不能称取消已确认。原run及预算保持，终止原因和实际owner清理待原件补核。新A2的独立task／预算需先完成[轮询历史增长修正](2026-11-13-workflow-poll-history.md)，不能借修复probe关闭其真实重构出口。Linux CI的20分钟超时尚未定位到具体测试，不凭此复现单方面归因全部CI耗时。

后续实际结果见[A2第三轮](2026-11-13-refactoring-journey.md#第三轮原件补核)：包含本片与轮询修正的已核安装完成7次真实Codex会话／9 job，原串行及三审查到达REVIEW_READY，38资源23,329B完整读取、精确候选复验／handoff／重放／恢复与清理均已补核，新独立A2评审中。第二轮也已沿原A1安装完成原fence／两排队回执／claim收尾并获原评审补核，原TERMINATED保持；本片并未改写其结果。本片代码和受影响验证／独立审查本地出口已过，后续提交、远端和精确候选CI分别记录，不借在途全量计时关闭发布。
