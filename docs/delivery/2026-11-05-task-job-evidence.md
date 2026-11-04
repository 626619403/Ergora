# F4.4b1：原 job 回执与文本证据 CLI/API

日期：2026-11-05。状态：b1首轮CLI/API、专用原生边界及轻量合同已实现，验证和发行进行中。前置a2页面`8f1489cb0a85fc75ea6e6f3cbb42172ba37ba98c`已正常推送，精确CI及同片终结进行中；本片使用另一发行身份。b2网页消费者及c综合收口另行验收。

## 合同与所有权

用户从原事件中的`dev_submit`调度事件ID选择一个job，沿已保存原提交/run/spec/memo核归属；不接收本地路径，不把当前模板补写为历史。新`task job`及同源GET只读入口读取该原调度事件的context，验证原request envelope，再复用既有`FileAdapter.verify_receipt`的原job/终态回执/摘要及安全路径合同。回执是当前可信目录发布的原job事实，不能仅凭其SUCCEEDED声称workflow已采用、六阶段成功或外部已清理。

首读只返回原job、回执摘要及产物目录，不返回prompt/spec输入。按回执中产物名称及首次观察的receipt SHA选择文本，完整原产物不超过既有16 MiB上限；先核完整摘要与严格UTF-8、拒绝NUL，再按Unicode字符窗口返回，避免切断UTF-8。每窗默认8192/最多16384字符，偏移为Unicode字符序号；返回完整产物字节数/SHA、窗口及下一偏移，不冒充完整文本。窗口后续须固定receipt SHA，变化明确失败。

原history流式从前缀验证至所选事件；只解码该事件context。事件ID限定1–10000，单请求既有1–60秒墙钟、20秒RPC和父进程额外5秒回收，JSON最多1 MiB。不自动轮询、重试、发任务或改账本。SDK的物理页内存和原生回执逐产物16 MiB验证成本分别说明，不以响应窗口夸大总读取内存边界。

新专用reference边界依赖既有Submission/Creation/原生adapter；tasks拥有外部参数验证，CLI/Web只消费同一用例。a1 events元数据不解码payload的合同保持；a2消费者源码/发行不混入本片。既有计划审阅、外部对账和完整证据/成本导出各保持原所有权。

## 可验收节点

1. b1 CLI/API：合同反例覆盖原run/context/envelope、事件类型/前缀/限额、回执/产物身份、路径/符号链接/大小、UTF-8/字符窗口与原回执固定、缺失/未知及无写；使用既有SDK和文件adapter，不重复构建执行栈。
2. 独立noneditable包/两安装/冻结内容、无SDK基础入口指导，两个已有原run各选择真实job/日志/材料只读CLI/API核摘要和窗口重建；139原文件/三history/outcome/refs/leases不变，无新模型调用。
3. 新fresh-context审查源码结构/性能成本与测试冗余，修复后正常独立提交推送、精确两OS CI和同片终结。
4. b2在已有事件页面选择原job/材料、手动窗口及错误/迟到隔离/390px，另用新独立审查；再进入c完整页面和专用栈正式关闭。

## 实现与首轮验证

新增`reference_task_evidence`拥有调度事件选择、原job回执/文本窗口；tasks统一外部参数，CLI/Web只转交。原events不改。adapter配置/注册根目录核对从既有Inspection原样移到Creation的`file_adapter`，当前有原外部对账及新job读取两个实际生产消费者；机械移动与新算法分别看diff、原外部边界与新合同分别验证，不改变旧回执合同或冻结实现。

首轮99通过/1失败（命令8.05秒，pytest5.69秒）：实际SDK converter配合单一类型hint会忽略额外payload，新入口遗漏原payload数量验证，合同反例捕获。已在解码前要求原调度事件仅一个payload，修后100项通过（命令4.35秒，pytest3.08秒），既有Starlette警告保留；后续补了原history NOT_FOUND与timeout/RPC可见失败，和已有事件/计划/外部证据的必要回归，结果待归档。不把首轮失败写成通过。

公开README/手册补了选择原事件ID、固定回执SHA、Unicode窗口、published不代表workflow采用、10k事件/16MiB单产物/1MiB响应及同步IO的父进程回收边界。独立包/两安装、真实两个原job只读、快照、新独立审查及提交/精确CI尚待完成。下一完成这些验收，再做b2。完整F4/F5/G0未完成。

## 本地最终发行与真实验收

最终wheel `087aea1838886dd12e6a5d56220dc28b6440276608b9464232527a39f738c115`的350资源与源码/两个noneditable安装相同，283冻结保持，基础Web无Temporal SDK；发行安装总命令25.42秒。源码联合150项通过（命令5.30/pytest3.81秒），必要既有外部证据/对账10项通过（66.33/65.71秒）；wheel合同103项通过（5.19/2.78秒），既有Starlette警告范围保持。

同一最终包只读两个既有原plan job（均原history调度事件56），CLI与GET回执完全一致；model-log12515/13886字节各2窗、execution-plan4002/4198字节各1窗，全部重建字节及SHA等于原产物。错误回执SHA、非job事件和错误run均明确失败。8CLI+12GET=20次调用，零POST；命令45.00秒，不当作单次RPC或文件吞吐基准。原生读后139文件、三history/outcome、业务refs/worktrees/工作文件、3claim/零active与读前逐项相同，零Running（2.57秒）；350资源/两安装及13JS语法终核通过（1.95秒）。无新模型调用或原生写。

后端/测试和公开文档均已完成本地验收，新的独立审查待进行；尚未提交或声称本片精确CI通过。b2网页消费者和c综合收口继续待办。

## 独立本地审查完成

[新的独立审查](2026-11-05-task-job-evidence-review.md)本地需求/可维护性均通过，无未解决findings；实际复算087aea包/350资源/两安装/283冻结，检查原日志与真实证据、共享adapter所有权/实际双消费者、必要守卫和验证成本。审查脚本未完成的额外复算以及无SDK父环境额外原生查询均未声称成功。当前文档初核17份/328链接锚点/27README命令通过；提交前再核暂存范围。b1尚待提交/精确CI/同片终结，b2只设计，源码写入两次审批deadline未执行。
