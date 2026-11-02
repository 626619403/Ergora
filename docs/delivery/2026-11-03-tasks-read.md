# F3.1：现有正式开发任务的只读入口

日期：2026-11-03。分支 `refactor/architecture-foundations`；源码基线 `67d88eccb209ab77b31b13461ff6b237a8224e08`，F2完整验收与独立审计均已完成。用户授权沿计划连续实施；正式任务六阶段与证据合同不变。

## 事实与分段

现有 `agentflow task` 在执行状态目录保存不可变 `task.spec.json`/`project.json`，Temporal为运行状态权威，`DevelopmentTransport`已经校验原始workflow输入并固定run ID。Ergora目前只有草稿和独立Agent调用，没有正式task CLI/API。reference模块已经拥有专用子进程隔离与原有安全读取，CLI/Web不应直接加载reference导入全局或自行拼接文件布局。

F3拆为：F3.1只读本地合同/身份；F3.2显式编译与持久创建；F3.3原生提交/实时状态/精确批准/取消及原ID对账；F3.4两模板端到端、结果导出和恢复验收。每项独立记录实际范围；F3.1不推断workflow状态，不把存在spec或export文件当作任务已通过，不实现第二套调度器。

## 本切片设计与验收

- 新增 `tasks` 为CLI和API的共享项目用例，要求published统一注册；从登记的execution中查询该项目的现有开发任务，返回当前项目修订、持久合同身份和明确的runtime未查询状态。
- reference新增专用只读文件入口，固定随包原合同/读取实现，在隔离子进程中复用safe_file/read_raw/validate_spec。单任务验证目录ID、spec task ID、冻结项目名/Git根/tracker归属；明确拒绝越界、符号链接、过大/篡改合同及其他项目任务。无需Temporal/Web SDK即可读取本地元数据。
- 列表按ID分页，输出最多100项；返回游标和被隔离的无归属/损坏记录计数，不将不可读记录当成功任务。列表不读取完整日志/阶段产物；详情仅返回有界的任务spec与冻结项目和绑定快照。不伪造最新运行状态或已完成状态。源文件/控制项目均不改写。
- CLI `task list PROJECT [--limit N --after ID]` / `task show PROJECT TASK`；API `GET /api/projects/ID/tasks`及`.../TASK`。同一输入同一结果，列表不启动进程执行器或服务。
- 跨平台非editable包运行正常/分页/项目隔离/旧注册任务/错误ID/损坏与大合同/符号链接回归，核对冻结283文件。新基础安装无可选SDK读取成功。实际旧L0任务只读核对，以及固定数量任务的查询开销与输出上限测量；没有测量前不宣称性能改善。

## 结构决定

`tasks.py`由CLI/Web两个真实生产入口复用。路径布局和原合同知识仍在reference中，子进程入口是隔离原导入全局的必要边界；不引入通用Task基类、仓库镜像、第三方运行库或DB索引。新任务写入和Temporal连接另属后续切片，不能借只读入口隐式导入/接管任务。

当前已完成调用与验收盘点，开始实施，尚无本切片通过结论。辅助证据放在 `.ergora/checks/f3-tasks-read/`，最终安排fresh-context结构/性能审计及精确两OS CI。


## 实现与验证进度

共享tasks用例及CLI/API已实现，原生文件布局/合同仍在reference的固定专用子进程中。列表最终使用os.scandir流式枚举及标准库heapq保留最多limit+1个候选名，每页仍需枚举全部N个目录名，但最多读取limit个候选合同；游标跨其他项目、损坏项及非法原生ID前进。详情读取spec、冻结项目和可选绑定，原read_raw的1MiB文件上限/no-follow及Windows句柄实现保持。对FIFO先检查普通文件，避免打开时等待；不加载可选SDK、不查询运行状态或写任务文件。

源码定向31 passed（12.17秒）；覆盖两模板、旧revision绑定快照、分页/坏目录游标、另一项目排除、spec摘要/目录/基线/tracker冲突、超大/坏JSON、缺归属对象/FIFO/符号链接、pending/轻量项目拒绝，以及实际CLI/API结果一致。首轮测试夹具为large-change误用standard风险，被原策略按设计拒绝；按模板改为high后通过，未修改产品策略或冻结合同。初版e238…wheel339文件×源码/两安装一致、冻结283通过；其完整回归在运行，但后续归属对象/游标源码自查修正后的最终包必须重建，不套用旧包结论。

实际旧L0任务在新基础安装中只读成功：复制原项目/策略输入到隔离配置，明确预览/采用后关联原真实task store，读取两个已执行任务的同一spec与绑定快照。原配置和服务未动，逐文件核对原任务目录字节不变；没有安装Web/Temporal/GEPA或查询Temporal。此旅程仅证明旧任务合同可读，不继承其历史模型效果。辅助脚本/摘要为legacy-journey.py/json。

初版实际1000合同fixture/每页100扫描项，20次读取中位355.2ms、最大631.1ms，最大JSON45970字节，十页恰好1000项无重复遗漏。客户端峰值RSS未超过其已有高水位，不能推导零分配或子进程内存上界。源码自查修正后将重测最终包，不将初版数字当优化收益；原始performance.py/json/log保留。

当前准备最终重包/适用回归/基础与旧任务复验，以及新的fresh-context独立结构/性能审计；精确两OS CI及交付待完成。完整F3仍需后续写操作与原生运行接入。


最终候选包SHA256 `df9cacbdf93bab49b916b05e7e8f67594c4c98388435922dc40edd45db38e187`，339文件在源码/包/开发/无可选SDK基础安装完全一致。最终两旧任务复验通过(final-legacy-journey.json)，原任务文件保持不变；冻结参考身份未改变。最终1000任务分页测量(final-performance.json)：20次/每页100扫描项，中位370.6ms、最大595.0ms、最大JSON45970字节，十页共1000项无重复遗漏；客户端峰值RSS相对采样前高水位增加144KiB，不作为进程树总内存界限。独立审查正在进行；最终全量回归和精确两OS CI待完成，完整F3尚未完成。


## 独立审计修正

接受审查者复现的两项问题：POSIX非UTF8字节名会让原始next_after无法经UTF8/JSON入口安全输出；Python3.11的Path.iterdir内部先os.listdir，heapq外层不能证明目录名内存有界。当前改为标准base64url编码原生fsencode名称的不透明ASCII游标，仅在子进程还原并排序比较，不拼接路径；os.scandir在with内流式枚举并关闭句柄，heapq最多持有limit+1个候选名。**每页仍需O(N)枚举，最多校验100份合同**；不新增数据库索引或缓存，性能记录保留此限制。API用inspected_entries明确区分合同检查数与目录枚举量。

同时局部修正自查的进程错误映射：查询子进程超时和无stderr异常退出均转为明确ValueError，经CLI/API现有错误入口呈现，不自动重试。原有registration_io/编译器不在本切片扩改。新增真实非UTF8字节目录、opaque游标连续前进及两种进程错误回归。此前df9c候选的包/全回归/性能仅为历史，修正后统一重包/回归/重测，再进行同切片复审。


## 修正候选与跨平台准备

[独立源码复审](2026-11-03-tasks-read-review.md)通过，三组P2全部关闭。作者源码定向34项通过（13.40秒），reviewer另独立跑26项tasks合同回归，并通过真实非UTF8目录的CLI→API游标及错误映射HTTP400/无重试探针。当前不透明游标只用于排序，既不当作任务ID，也不拼文件路径。

审计后最终wheel SHA256 `2fa1915726503715d312e839c7d0672165503c7f855b23ecdb77c7bdd29da3e7`，339文件在源码/wheel/两安装一致，冻结283文件PASS。完整适用回归、最终1000任务性能及两旧任务无SDK复验正在进行；准备提交推送源码已复审候选触发精确两OS CI，候选推送不表示F3.1已完成。原始记录使用review-fixed前缀，旧包数字保持历史身份。


已推送源码/测试候选 `13e9f33623c5811547bdb43d3b2b0218b62ffda2` 并核对远端一致。审计修正后的完整适用Linux回归 **350 passed、19 skipped、36 subtests passed**（182.00秒）。最终包1000任务/每页100候选合同检查，20次中位396.7ms、最大600.8ms，最大JSON45975字节；十页1000项无重复遗漏。每页仍O(N)流式枚举全部名字，客户端RSS高水位增0不能推导零分配/子进程内存上界。两真实旧任务在无SDK环境读取PASS，原任务字节未变；相关raw证据均review-fixed前缀。

精确候选CI与独立最终身份复核待完成；下一切片[F3.2设计](2026-11-03-task-creation.md)已记录，生产源码尚未进入写操作。此后状态文档不改变本候选验收身份。


精确首候选CI41519399689：Ubuntu成功，Windows回归的24个fixture setup失败，原因是新增task_store夹具直接调用冻结portable的Linux O_NOFOLLOW读取，不是task reader错误。测试子进程增加Ergora包路径，并在Windows复用现有_read_windows_contract映射portable/adapter读取；原编译器/产品源码保持不变。Windows真实支持仍以修正后的精确CI为准，不把此次失败或Linux通过写成两OS通过。最终2fa191…wheel与生产339资源身份保持不变；只需重验修改过的测试路径及新精确CI。


Windows夹具修正后，Linux安装包下34项定向再次通过（13.26秒），339文件×源码/wheel/两安装重新核对一致；最终生产源码仍13e9f33，2fa191…wheel及350项完整Linux结果继续绑定该生产身份。准备推送仅测试/文档修正候选并以新精确CI验证Windows；不重复无变化的Linux完整回归。


## 最终收口

F3.1完成。修正测试候选`e9b53f7d9e0bf5ddf7090ec6a76e8763ca42a732`已推送且远端一致；精确[CI41521060898](https://github.com/626619403/Ergora/actions/runs/41521060898)的Ubuntu job125536888396三必需步骤及Windows job125536888713四必需步骤全部成功。生产源码仍为13e9f33，最终2fa191…wheel及339文件身份没有改变。首轮失败归档与新CI分别保留在ci/及ci-windows-fix/，没有覆盖失败证据。

[独立最终审查](2026-11-03-tasks-read-review.md)已核对精确CI、源码/最终包/两安装和远端身份，通过且无未解决finding。最终Linux350项/36子测试、19跳过及旧任务只读/性能证据范围如上，Windows结果只以本轮CI实际步骤为准。下一项为[F3.2](2026-11-03-task-creation.md)的显式预览、创建和恢复；完整F3仍未完成。
