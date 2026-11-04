# F4.4a1 原运行有界事件 CLI/API：独立审查

日期：2026-11-04。审查者：全新上下文 `/root/task_events_review`；按项目 AGENTS、当前 PLAN 及 independent-review/review-pr 流程独立读取原始差异和新文件，没有继承实现者的结论。基线与审查时 HEAD 均为 `a6ef6e3bcb07ccad5fc259962b639ccc89f7fb81`，事件切片未提交。

## 判定与范围

本地功能合同通过；生产结构与可维护性通过，所审代码范围无 findings。完整切片仍待文案收口、最终文档静态、精确提交/发行包及远端 CI 核对，不在此报告宣称交付完成。

实读四个既有生产文件的 git diff：`cli.py`、`reference.py`、`tasks.py`、`web.py`，及新增 `reference_task_events.py` 全文；实读两处测试差异与新增 `tests/test_task_events.py`。同时核对 `_Submission`、原 runtime/VerifiedSpecClient、`_Creation.check_size`、CLI 最终序列化、已安装 SDK 迭代器源码和公开使用/架构差异。C2/D 状态记录不属于本片生产审查范围。

## 正确性与结构

- CLI 与 GET API 共用 `tasks.events`；入口对 run、1–100 limit、1–60 秒预算及 8192 字符 cursor 做外部输入验证。原提交回执、spec、memo 和固定 run 继续由既有所有者验证，没有新执行账本或写操作。
- 原身份验证后只调用一次 SDK `fetch_next_page`，没有应用层翻页或轮询循环。游标保存原页 token、固定 page_size、页内 offset 与下一事件 ID；显示 limit 改变不会丢弃物理页剩余。RUNNING 尾部重读原页，追加后从原位置继续；闭合尾部才清除游标。前缀、offset 锚点和连续 ID 守卫分别覆盖外部服务/用户游标的可达错误，均显式失败而不重置位置。
- NOT_FOUND 返回独立状态，RPC/超时保持失败。SDK 的单次页方法内部使用 `retry=True`；底层传输重试受 RPC 截止时间与外层墙钟预算约束。原验证另外包含 describe、启动前缀读取与原 spec 解码，单事件页不能解释为单次总 RPC。
- 事件投影只选 ID、类型、时间及活动/信号关联字段，不返回原 payload。共享 `check_size` 按 CLI 实际 `indent=2`、UTF-8 和换行计字节；HTTP 紧凑 JSON 不更大，1 MiB 上限没有最终序列化缺口。该上限不限制 SDK 收到的物理页内存。
- 新文件拥有具体原生查询入口和完整私有分页算法，是进程边界与语义所有权所需的单消费者模块；复用 submission 的身份验证，避免 runtime 与 submission 反向成环。没有添加可由现有依赖替代的通用框架。架构测试仅显式登记新边界，没有放宽无环约束。
- 新测试使用真实 SDK 类型配合假服务；输入反例在项目存储前拒绝，不新建重型环境或 CI。源码与 noneditable 包的定向复验分别验证导入环境，成本有界；未发现需删除的生产守卫或冗余重型测试。

## 实际检查与证据

独立执行 `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv-dev/bin/python -m pytest -q -p no:cacheprovider tests/test_task_events.py tests/test_task_inputs.py tests/test_architecture_boundaries.py`：69 passed，4.22 秒（工具墙钟 6.46 秒）；未运行完整套件、安装依赖或访问原服务。

实读私有 `f4-task-events` 中源码/包合同及既有边界命令与日志：实现者的 69/69/4 项通过各有原始成功记录。独立计算五个生产文件摘要并与 package-identity 逐项一致；新增入口及两安装摘要均为 `b8ef882e19b9aa14d0299b7a088aae45ba21f3bbb98299c858ca9f6d6cc87ecd`，wheel 实算为 `3bd104932c2b536877d6cf776556fcc6280efce7bc8db0649386008f5bb27523`。349 资源/两安装与 283 冻结的完整比较依据原身份记录，本审查未另行重算全部资源。

实读原生分页脚本、逐批摘要及命令结果：两原 run 的 329/348 条完整 ID/类型与原 history 对照，11/12 批；首物理页 37 条，显示 limit 20→1→100；4 CLI、25 HTTP GET、0 POST，最大响应 6290 字节。实读快照脚本，确认比较原完整 history JSON、outcome、139 文件、claims/active 和业务 Git 全 refs；两份保存快照独立实算 SHA256 同为 `6ea6cb65b0182896900bec5232d2ec75a76b526082e89b16392f5e8184160b16`。

RUNNING 尾部增长只由真实 SDK 类型与假服务的轻量合同覆盖，未另启 workflow；真实数据为两个已闭合 run。性能数字仅对应这些条件，不推导并发或规模结论。

## 待落盘的准确性文案

以下三项已获主 agent 授权修订，但本次文档补丁因自动审批服务 deadline 未执行，不能记为已修；没有要求改生产代码或添加测试：

1. 详细计划 F4.4a1 的“无自动重试”应限定为无应用层自动重试/轮询，注明 SDK 传输重试仍受 RPC/墙钟约束。
2. 当前架构事件责任行的“不解码 payload”应限定为“事件投影不解码 payload”，与 USAGE 中原 spec 校验仍需解码的说明一致。
3. 本片交付记录的“5 个既有生产文件并新增 1 个”应为“4 个既有生产文件并新增 1 个”。

默认 shell sandbox 初始化失败；受控只读重试取得上述源码与证据。部分较长离线复核、首轮定向复跑及文档写入遇自动审批 deadline；仅成功执行的检查计为通过。审批超时不是安全拒绝。最终文档静态、精确提交/包和 CI 尚未由本报告验收。

## 文案澄清后复核（2026-11-04）

已独立读回三处修订：交付记录为4个既有生产文件加1个新增模块；架构说明限定为事件投影不解码payload；F4.4a1计划明确无应用层自动重试/轮询，SDK传输重试受RPC/墙钟约束。三项与已审实现一致，前述文案待办全部关闭，所审范围无未解决findings。

本次仅核文档并追加记录，未重跑测试、安装或访问原运行。最终文档静态、精确提交/发行包及远端CI仍待单独核对。

## 精确提交与远端复核（2026-11-05，CI待完成）

独立核定e77edca96c9e662d9ce4d96a186e00be9d446672的20文件及树118a816ffa1aa25576191dbbb583313cb8232dd3；349个已提交资源blob身份全部匹配原wheel实际字节，events提交源码摘要保持b8ef882e。实际RSA只读ls-remote确认远端refactor/architecture-foundations精确为e77edca。没有使用A2工作树验收A1，提交/发行/实时远端范围无新增findings。

CI41870385380初次官方记录仍为In progress，job列表未完整，不计通过。最终静态及精确CI待后续终结；本次未重跑测试、安装或访问原运行。

## 精确CI与终结复核（2026-11-05）

本审查者独立解析刷新后的官方run/job原HTML，确认[CI41870385380](https://github.com/626619403/Ergora/actions/runs/41870385380)总体Success，绑定完整提交 `e77edca96c9e662d9ce4d96a186e00be9d446672` 和精确Portability workflow。六份保存源文件的实际字节数与SHA256均逐项匹配 `ci-html-status.json`，不依赖摘要结论代替原HTML。

Windows3.12 job `126715521854`、Ubuntu3.11 job `126715522289` 的selectedJobId与各自原HTML一致；构建安装wheel、包内参考身份和原生回归全部success，必要step均完成且data-log-url精确包含上述完整commit和对应check/job ID。Windows PowerShell5.1安装升级success，Ubuntu该条件步骤skipped符合精确workflow；两job无失败、取消或超时步骤。前述CI待办现关闭。

再次实际以既有RSA传输只读ls-remote，远端分支仍精确为e77edca；结合此前独立核定的20文件/冻结树及349资源与原wheel字节一致，本片实现、结构、精确提交/发行/CI/实时远端的终结审查通过，无未解决findings。结论仅覆盖A1；状态追加后的最终文档静态由主agent单独收口。本次没有重跑测试、安装或业务运行。
