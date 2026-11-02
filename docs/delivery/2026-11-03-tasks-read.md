# F3.1：现有正式开发任务的只读入口

日期：2026-11-03。分支 `refactor/architecture-foundations`；源码基线 `67d88eccb209ab77b31b13461ff6b237a8224e08`，F2完整验收正做最终独立收口。用户授权沿计划连续实施；正式任务六阶段与证据合同不变。

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
