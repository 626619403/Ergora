# F4.4a1：原运行的有界事件读取

日期：2026-11-04。状态：CLI/API及专用原生查询入口已实现，源码/非editable包各69项轻量合同/架构、4项既有读取边界、349资源两安装和真实29次只读验收通过；新独立审查及文案复核通过，提交/精确CI待完成。源码基线为D提交`a6ef6e3bcb07ccad5fc259962b639ccc89f7fb81`；D已推送并获精确双OS CI41834815428，同片终结复核中。C2的401bacb已完成精确双OS CI41819895815及独立终结；本片与D分开发行和验证。

## 范围与合同

增加`ergora task events PROJECT TASK --run-id RUN --limit 20 [--after CURSOR]`及同源GET `tasks/{task}/events`。只读投影原运行的Temporal事件元数据，提供明确的事件ID、类型、时间和活动/信号关联字段；不返回原始输入、prompt、活动result或完整payload。阶段/工作单元当前状态仍由原status拥有，事件片段不证明完整六阶段、外部清理或开发成功。页面入口属a2，原job材料/日志属b，完整证据索引属F5。

沿`tasks.py → reference → reference_task_events`专用原生查询入口，原运行归属复用`_Submission.submitted/lookup_run`的spec/memo验证，固定原run而不跟随新run。新模块只拥有事件投影与游标算法；submission依赖原runtime的spec验证，因此事件读取不放回runtime形成反向依赖。运行查无记录与RPC故障分别可见；不能根据空片段重发任务。没有新执行器、账本、数据库、依赖或持久格式。

每次在原运行验证后只读取一个事件SDK物理页并返回最多1–100个事件（默认20），物理页请求上限20，响应最多1MiB、墙钟沿原1–60秒预算。原验证另有connect、describe及page_size=1的启动前缀读取/原spec解码，memo直接来自describe；因此不能声称整个请求仅一次RPC或完全不解码原spec。事件投影本身不解码payload。SDK可能返回更多物理事件，因此响应另行限条数；SDK接收的物理页字节仍由底层服务/SDK控制，不能把响应上限当作网络内存上限。

游标使用标准JSON/base64，绑定原提交/固定run，携带SDK token、原请求页大小、页内位置及下一事件ID；它只是只读导航信息，不是授权或新的证据身份。页内剩余事件必须先返回，不能截断后跳到物理下一页；逐段核连续事件ID，不把用户提供的游标视为完整history证明。已闭合且读到服务尾部才无后续游标；RUNNING读到当前尾部仍保留原位置，后续显式读取新增事件，不自动轮询或无限扫描。

## 验收

1. 轻量使用真实SDK事件/分页类型覆盖物理页超过limit、页内恢复/跨页无遗漏重复、可变显示limit、空页/运行中尾部再读、闭合尾部、错误scope/游标/顺序、查无原run与RPC故障。纯输入反例在重型项目初始化前验证，复用已有spec/memo边界，不重写一套深层准入测试。
2. 既有运行/计划/原生操作调用边界定向检查及架构检查；构建独立noneditable包与基础/开发两安装，核源码/包/安装349资源及冻结283。适当回归只覆盖实际受影响合同，不为每个字符串分支复制重型CI。
3. 在已有两个原run逐页CLI/HTTP读取，对照原SDK完整history的事件ID/类型与next游标，强制小limit检验物理页越界；全过程GET，原139文件（D后）、三history/outcome、Git refs和leases保持。没有新workflow、信号、模型或日志内容暴露。
4. 更新公开使用/架构与主计划后，新fresh-context独立审查正确性、所有权、必要守卫、实际页数/RPC成本及测试冗余；修后复核、提交包身份及精确远端CI分别记账。SSH认证待恢复时继续可独立的本地工作，不将切片标成完整远端交付。

设计证据：私有`.ergora/checks/f4-task-observation/sdk-page-probe.json`来自现有SDK1.34.0与固定原run的三次只读调用，page_size1/3/20实际返回2/5/37事件。它证明必须处理页内剩余内容，不是吞吐或规模性能基准。后续本片验证归`.ergora/checks/f4-task-events/`，不进入公开发行资源。

当前修改4个既有生产文件并新增1个具体原生查询模块；物理页内剩余内容和live尾部位置都在游标中保留。原plan与events只读进程错误文案共用原边界；没有改冻结参考或其他状态机。新测试复用轻量SDK类型和既有纯输入分层。

验证记录：首轮68 passed/1 failed，架构检查发现runtime→submission→runtime循环；移动查询所有者后第二轮68 passed/1 failed，新增模块尚未登记到允许的原生边界清单。两个失败原日志保留，未放宽无环约束。显式登记该边界后`source-contract-v3`为69 passed、2.61秒（完整命令4.13秒），exit0。计划/运行原边界、最终发行及真实只读验收尚待执行。

既有只读边界定向：原plan CLI/API转发、SDK缺失指引和原查询进程失败两反例，共4 passed/1既有Starlette warning、9.12秒（命令10.84秒），未复制重型项目矩阵。

独立发行：wheel SHA256为`3bd104932c2b536877d6cf776556fcc6280efce7bc8db0649386008f5bb27523`；349资源在源码、wheel与基础Web/开发两套noneditable安装逐字相同，冻结283保持。`uv build`22.66秒，整个新venv/构建/两安装/身份核查50.57秒，两者范围分开。基础安装没有Temporal SDK，13既有JS模块语法通过；实际正式查询仍选择项目登记的完整原生运行时。最终wheel轻量合同69 passed、2.83秒（命令7.13秒）。

真实只读验收：两个原run分别以11/12批取得329/348个事件，完整ID/类型序列与原SDK history相同，无遗漏/重复。首批limit20实际物理页37事件，接着limit1再limit100，证明先读取页内剩余再跨页；终态尾部无cursor。四次真实CLI、25次HTTP GET共29次调用（含六个输入/跨run/游标反例），零POST，完整命令50.53秒，调用时间合计49.97秒、最大响应6290字节；不是并发/规模基准。RUNNING尾部增长由真实SDK迭代器类型的轻量合同覆盖，本次未新启workflow。

原生读取前快照：139文件、3已释放claim/0active，三原history329/348/112事件及原outcome保持，无RUNNING workflow；两业务repo的HEAD、工作区、worktree与全部refs已固定。本次不重放批准/取消/对账/导出或模型调用；读取后快照核验及新的独立审查待完成。

读取后`native-snapshot-after`退出0，4.25秒，139文件/三history与outcome/claims及active/两repo全部记录与读取前快照完全相同。新独立审查与提交CI待完成。

## 独立审查与本地收口

[新fresh-context独立报告](2026-11-04-task-events-review.md)已落盘，代码、结构、必要守卫及测试成本通过，无代码findings。审查者另作69项轻量复跑，4.22秒；核五个生产文件的发行摘要、实际wheel SHA及两份快照相同摘要。三个准确文案已修改并由原审查者读回：4既有文件加1模块、事件投影不解码payload、无应用层轮询/重试而SDK传输重试仍受RPC/墙钟约束。无未解决finding，不为文案修订重复行为测试。

首轮静态为10份文档/322链接锚点/27条README parser命令、无缺失，diff空白检查通过；这是本次最终状态追加前的实际范围，提交前再核完整文档身份。生产资源保持3bd104原包，下一保存精确提交归档/最终静态，并取得本片精确双OS CI；尚未关闭完整切片或F4。
