# F9b1 需求与行为独立审查

日期：2026-11-14。Reviewer：`/root/f9b1_spec_review`，fresh context。项目与文档归属均为 Ergora；按 `code-review` 需求轴及 `maintainable-project-delivery/references/independent-review.md` 审查。原要求／计划为准，作者交付与测试成绩只作证据。

## 范围与身份

基线 `8182499fa46c61adecea2f6defd2c777a433eed5`，候选为其上未提交工作树；该基线至 HEAD 无新提交。已读 `AGENTS.md`、`docs/PLAN.md`、[F9 总计划](../plans/2026-11-14-training-workbench.md)、[F9b1 计划](../plans/2026-11-14-training-runtime.md)及本片交付。原要求包括：复用原实验／执行／批准 owner；未知按原 ID 对账；资源累加不扩大子权限；不伪造 GPU 收益。本片只增加显式只读实时查询，prepare／start／cancel／approve、模板或后端变更及真实 GPU 均在范围外。

精确 16 文件及 SHA 在私有 `.ergora/checks/training-runtime/review-r1-files.json`，清单 SHA256 `bbafe9e3f73211edc6f862dd6901c95e928f8ebbb7fcb2a7ac880fd9017fc3f7`；tracked diff `review-r1.diff` 的 SHA256 为 `ecb6ed464b240b68e332c17e8c967f0a3d58b89830bc4d6814089a112551e4cd`。范围为：

- `src/ergora/{training,reference,reference_training_runtime,cli,web}.py`、`src/ergora/data/console/training.js`。
- `tests/test_training_runtime.py`、`tests/fixtures/training_runtime_client.py`、`tests/test_architecture_boundaries.py`、`scripts/ci/linux-groups.json`。
- `README.md`、`docs/TRAINING.md`、`docs/architecture/current.md`、`docs/PLAN.md`及本片 plan／delivery。

已完整读新增源码、测试、夹具及本片文档，并沿原 `agent_platform.training/core`、`perf_temporal.models/connection/workflow/client`、canonical JSON、离线 reader、登记／CLI／HTTP／页面及 SDK 调用者核查。当前 14 文件与清单逐字匹配；`docs/PLAN.md` 与本片 delivery 仅有已读的后续进度追加。安装快照内 16 文件均匹配原清单。H3b／F9a 状态附录及其 CI 不进入本片产品结论。

## 源码结论

**需求与行为轴源码审查通过，开放 finding 0。** 在已查路径未发现可达的需求缺失、错误认领运行或越界写操作。维护性轴由另一独立 reviewer 判定；本报告不替代该结论，也不代表 F9b1 整体验收完成。

|已核场景|源码证据与结论|
|---|---|
|CLI／HTTP 选择实验|[training.py:23](../../src/ergora/training.py#L23) 共用 `status`；沿原 `inspect` 核 published 注册、训练模板、manifest／spec、项目与 repo 见证，再校项目 revision。CLI `897` 行与 HTTP `446` 行均调用它，没有第二份准入语义。|
|可选 SDK 与固定安装|[reference.py:358](../../src/ergora/reference.py#L358) 显式检查 SDK，在独立进程导入选定安装；`validate_installation(training=True)` 增核 perf_temporal 家族。原 CONFIG／STATE 在子进程导入前设置，原 `environment()`／`connect()` 保持连接所有权。|
|同 workflow ID、不同输入或 run|[reference_training_runtime.py:28](../../src/ergora/reference_training_runtime.py#L28) 仅 describe 一次，随后 history／query／result 固定实际 run；完整第一事件输入用 `canonical_sha` 与原 spec 比较，字段或 int／float／bool 差异均拒绝。显式 run 不符直接报错。|
|运行、完成及负结果|[reference_training_runtime.py:48](../../src/ergora/reference_training_runtime.py#L48) 返回原 Status／Outcome并核 binding；完成读取 `follow_runs=False`。`GATE_FAILED`／`CANCEL_UNCONFIRMED` 保持，其他 Temporal 终态只报 `NEEDS_RECONCILIATION`，不声称外部作业已停止或采用。|
|不存在、网络与未知|只有 describe 的明确 NOT_FOUND 返回 `not_found`；缺历史、完整输入／binding 不符、UNAVAILABLE 与有界超时均报错。没有离线成功回退、start／signal、原记录写入或自动重发。|
|页面手动查询与迟到响应|[training.js:30](../../src/ergora/data/console/training.js#L30) 仅按钮触发 runtime GET，单独展示离线与实时事实；DOM 连通性、project／home／tab、detail 序号及 runtime attempt 序号共同抑制旧响应。没有轮询或新增服务。实际浏览器验证另列验收。|

## 已查证据与实际执行

私有证据根为 `.ergora/checks/training-runtime/`。本 reviewer 只读产品与既有证据，并在 `spec-review-r1/` 执行小范围探针；未安装、启动服务、调用模型、运行训练或修改产品。

- 独立 `sdk-probe.py/json`：实际 SDK **1.34.0** 的 Client／WorkflowHandle／protobuf／DataConverter，底层使用无网络的只读 Service 替身，**9／9** 场景通过。核原 Experiment dataclass 序列化、描述后固定 run 的 query／result、原负 Outcome、Temporal 终止、三类完整输入碰撞、缺历史及 NOT_FOUND／UNAVAILABLE；不把该替身当真实服务旅程。运行模块 SHA256 为 `23009b31a482bfc22317ba436039c2828f2dc526fc4140222ba062902ad6c9e8`。
- 独立逐项核原 **283** 参考 SHA，无差异。后续安装证据到达后，只读重核当前源码／安装快照／wheel／installed 的 **564** 产品文件逐字相等、两 RECORD 的摘要与大小（572／577 行）及 283 参考，noneditable 身份成立。wheel SHA256 为 `7ac58997490fac91b3ed15d75f6a5c13b7f36b3b4a517b7dcb069f3295e59adf`；结果在 `spec-review-r1/package-audit.json`。首个审计命令的缩进解析错误已保留，未产生验证结果。
- 已读源原件：r1 在 pytest 前失败；r2 **16 失败／32 通过，27.86 秒**，缺完整 training 家族夹具及边界登记；r3 **1 失败／47 通过，47.77 秒**，失败为已加载旧架构清单；r4 只复验新清单，**14 通过，0.31 秒**。原失败未抹除，r4 不冒称重跑前三 suite。
- 已读安装 `regression-r1/result.json` 与实际 stdout：`-I -m pytest`，本片 runtime、原离线、reference、架构四 suite **48 通过，54.67 秒**，受控进程 56.438 秒、退出 0。本 reviewer 未重跑该 suite；以上身份核查将成绩限定在这一候选。

本轮尚未独立核定实际受控 Temporal 及两项目环境旅程、浏览器显式／迟到响应与停止原件、原模板自身审查、另一独立轴的最终结论，以及普通发布、精确远端 Ref 与本候选自己的 CI。它们是本片剩余验收证据，不是本次发现的产品缺陷。真实 GPU、F9b 后续写操作、F9c／F9d、真实 B3 与完整 C2 仍按各自范围开放。

## 最终本地原件补核

同一 reviewer 继续本片复核。产品／测试／CI／README 身份仍为 r1；新增仅计划、交付与审查进度记录，以及公开摘要。上段为初审时未核定范围，本段记录现已到达的实际证据，不把辅助脚本重试写成新产品实现或新的完整训练旅程。本次只读原件、查看三份截图并执行 `spec-review-r1/local-final-audit.py`，未安装、启动服务、调用模型、重跑 suite 或更改产品；交叉核验原件在同目录 `local-final-audit.json`。

- **安装与目录隔离**：上述最终包／两 RECORD／283／48 安装项保持该 r1 身份。已读 `source-manifest-scope-correction.json`，原构建标签误写 F9a 已另行补正，未覆盖原快照或成绩。另读结构 reviewer 的实际 `probe.py/client.py/result.json`：两套不同 config／state 均按选定目录隔离，全部有效非默认 Experiment 时限可经原 converter 保持；拒绝协程取消的替身在外层 6.016 秒被回收并报 unknown。该原件只证明替身与进程边界，不充当第二次实际 Temporal 旅程。
- **原生同一 run 与负结果**：已读首次驱动、三份恢复脚本、原 CLI 命令／stdout／stderr、三次失败说明和四轮 cleanup。首次实际原 owner prepare／start 后，新查询从 `not_found` 到 `QUEUED`；原 CLI 发送取消，原 executor 收集 fence 后写 `CANCELLED`，未生成 started 记录。辅助脚本先后缺 asyncio、缺原生导入路径、错误预设 `CANCELLED`，失败均保留且原 monitor 收尾。最终恢复只沿同一私有 SQLite、`perf-experiment/native-runtime` 与 run `01a1d697-a2a0-7d4d-9a52-37e76b5bc8ad` 读取；没有再次 prepare／start／cancel。
- **完整历史与原件保持**：独立解码 `history.json` 的首输入与末 Outcome，完整 canonical JSON 与原 spec 一致；42 事件中仅一次 workflow start 和一次 `request_cancel`。历史 SHA256 `3c051d136e32d298ad026e1a1d875742d7d4f9beabfe2438f50d79ed75484e4b`，与前一轮留存历史逐字相同。新 `final-query` 的完整 Outcome 等于原 SDK 的 `CANCEL_UNCONFIRMED`，同时离线 `CANCELLED` 保持；确认窗口过期后不从本地结果推断领域成功。21 份原 config／训练文件当前 SHA 全匹配，runner 未启动。3.617 秒为最后一次恢复读取的时间，不是全旅程耗时。
- **实际浏览器**：已读实际 Playwright 参数、运行代码、退出码与 stdout，视觉核对 1440／960／390 三视口截图。首个 status 出现在第 31 次请求，前 30 次导航／详情 GET 没有实时查询；随后完整原 Outcome 可展开，离线 `CANCELLED` 与实时 `CANCEL_UNCONFIRMED` 分开。持有真实响应后切项目、重新选择详情，以及两次手动查询倒序返回三种排列均成功抑制旧响应。总计 45 次 GET／200，其中 6 次 status；六份服务端原回复摘要相同，完整 JSON 等于固定 run 的原 SDK 查询。实际 training.js 为 8,075B、SHA `ded3344bb32ddcb31028d92ae8da999444d0c1d408f470aa7dbe987b9d820060`，与冻结源／包一致；截图与尺寸结果未见整页横向溢出。
- **原模板自身审查**：独立调用原只读 `inspect_input` 复核冻结输入与 assets，digest 为 `125da02d1a62301dd91543a9c42ac124d988bac23ea45e4758caac0952bb7f31`。14 个完整文件共 197,068B，逐项按长度／SHA 核实际 task／prompt／stdin，3 项祖先资源完整存在；子权限等于父与 grant，未扩大。原持久 result 与复制原件逐字相同，SHA `70d3aeb687eeb092dbfa79e1785d241188575f7103c60714cdc1447db4dfa559`；实际授权 Codex 回退、46.248 秒、退出 0、`approve`。原回复明确只批准给定静态源码，未声称独立运行测试、浏览器、服务或 GPU。
- **停止与公开摘要**：实际 browser close 退出 0；四轮原 controller PID／starttime 当前均不在，`/proc/net/tcp{,6}` 无原 7233／42391 监听。已核 `closure-r1.json` 与各轮 monitor 的 `cancelled`／`-9` 原件；仅认定私有验收服务收尾，不扩为远端／GPU 作业停止证明。[公开摘要](evidence/2026-11-14-training-runtime.json) 的包、回归、run／history、负 Outcome、浏览器和自身审查字段与原件一致，原失败及未执行范围保持可见。

**需求与行为轴本地出口通过，开放 finding 0。** 维护性最终结论见[独立结构报告](2026-11-14-training-runtime-structure-review.md)；本报告不代判该轴。普通发布、精确远端 Ref 与本候选自己的 CI 尚未本 reviewer 核定，不能借 F9a 成绩。上述 CPU 控制流不证明 runner 命令、模型训练、MLflow、GPU、数值／性能比较或采用；F9b 后续写操作、F9c／F9d、真实 B3 与完整 C2 继续按原计划开放。

## 发布身份补核

本次只核已提交的 `106481a80abfd168f5b45fbba7381063505239d0` Git 对象，唯一父提交为本片基线 `8182499fa46c61adecea2f6defd2c777a433eed5`；后续 F9b2 工作树不进入判断。独立读取该候选 25 个变更 blob，集合、长度及 SHA 全部等于 `static-r2.json`（该清单 SHA256 `bb7f8b28b96a29a164ab85a63f9d295a667b9a1af2d65157e6f44b7ce360ce67`）。10 个产品／测试／CI 文件按原算法重算 packet SHA256 为 `4399454c62e491baa801638257d437cee0fd49c2c87b0ba8804a82df2c067bf0`；它们与初始 review-r1 相符，其中产品源码亦与已验安装快照／wheel／installed 逐字相等。候选中的 221 个相对 Markdown 链接目标在同一 Git 树内存在，约定的机器私有标识扫描无命中。

F9a 发布／CI 附录仍归原片记账，不成为 F9b1 的 CI 证据；新增 F9b2 文档明确是下一片设计，未混入其提交／对账产品。已读 `commit-r1.json`、`push-r1.json`、`ref-r1.json`：普通 push 退出 0、没有 force 参数，随后原 `ls-remote` 回执的完整 `refs/heads/refactor/architecture-foundations` 为上述候选 SHA。**本轴提交／普通推送身份核对通过，需求与行为 finding 仍为 0。** 该回执证明所记时点的远端身份，不保证之后的分支位置。

本轮另保留一项工具发现的文档空白注记：对已提交的完整候选执行 `git diff --check BASELINE CANDIDATE` 实际退出 **2**，唯一诊断为 `docs/delivery/2026-11-14-training-runtime-structure-review.md:44: new blank line at EOF`。原命令／退出／stdout 在私有 `spec-review-r1/publication-diff-check.json`。提交前 `static-r2.json` 的 `diff_check_exit: 0` 来自当时只覆盖 tracked 差异的命令，不能扩大成 25 个提交文件的检查通过；旧记录未覆盖改写。该空白不改变产品行为，修正归后续普通文档提交与完整静态补核，不回写旧候选成功。本候选自己的 CI 尚未本 reviewer 核定，仍须单独收口。
