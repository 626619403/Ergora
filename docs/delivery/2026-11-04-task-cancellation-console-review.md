# F4.3c1 网页取消与原请求恢复：独立审查

日期：2026-11-04。审查者：`task_cancellation_console_review`，本片新的 fresh-context 独立审查者。先读原始 diff、调用方和既有后端合同，再读作者的[交付记录](2026-11-04-task-cancellation-console.md)与实证；未参与实现。遵循仓库 `AGENTS.md`、`maintainable-project-delivery` 的 independent-review 要求及 `review-pr` 分轮审查。

## 结论与范围

**需求符合性：本地范围通过。可维护性：通过。已检查范围内无未解决 findings，也无阻塞源码项。** 本结论不关闭最终交付：当前仍是未提交工作树，精确提交树、该提交的双 OS 必要 CI 步骤及实时远端尚待同片终结复核；不能继承 F4.3b 的 CI。

基线为 `c54230eb8a6d3468ef33e6365c874a4e3a2407d6`，分支 `refactor/architecture-foundations`。实际生产变化仅 `src/ergora/data/console/tasks.js` 的 115 行局部取消消费者及 `app.js` 的帮助说明；没有 Python、测试、CI、依赖或冻结 reference 改动。审查时源码 SHA256 为：

|文件|SHA256|
|---|---|
|`src/ergora/data/console/tasks.js`|`51dd185a36bb0c1ac8a7d1cebb9c1867e5a67080ba2b52c8b48a928181ab5eb6`|
|`src/ergora/data/console/app.js`|`987b9b04ec0a4cb844e09a4bea5a9c044be5d501e904b22ea88e9c88965032f2`|

文档范围包含 `README.md`、`docs/USAGE.md`、`docs/architecture/current.md`、`docs/PLAN.md`、`docs/plans/2026-11-01-all-in-one.md`、`docs/delivery/2026-11-03-formal-task-console.md`、新 C1 交付记录，以及 B 片两个交付/审查文件的最终状态追加。后者是 B 的归档，未据此扩大 C1 生产验收。审查中指出总 F4 当前检查点仍称真实取消待验，作者已同步为本地通过、审查及提交/CI待收口；复读确认修正，没有改变源码。

## 合同与可到达边界

|检查点|代码与独立判断|
|---|---|
|新请求入口|`tasks.js:726` 仅在明确查询成功且非终态时显示入口；`:466`、`:485` 固定详情和所选 run 代际。先 GET 原请求，只有运行入口的 `not_recorded` 才提供必填原因与明确 POST（`:501`、`:515`、`:556`）。服务端继续拥有原提交/run归属、修订、原因和状态竞态校验。|
|原意图恢复|`:502`、`:525` 仅为 `prepared/unknown` 提供 `/resume`，发送原 `intent_sha256`，不发送可编辑原因或替换 run。沿调用链核过 `web.py`、`tasks.resume_cancel`、`reference_task_cancellation._Cancellation`：prepared可首次投递，unknown只查原run精确信号；页面未复制 journal/Transport 状态机。|
|无再次投递与事实语义|`:493`–`:512` 分别表达投递与取消确认；`requested/already_closed` 只读，不渲染写表单。已闭合说明明确未发信号，返回原任务后仍需再次查询原运行。回执没有被解释为六阶段成功、外部清理或租约释放。|
|迟到与写中保护|`:485`–`:490` 同时检查视图/详情归属、内容连接、dialog open、读取及run代际，覆盖关闭、替换、编辑ID、换run、切任务/项目。`:518`–`:541` 写前保留原ID、锁输入与读取，回复未知只提供原记录读取；finally只解锁仍活动的工作区。|

这些守卫都有实际边界：读取代际处理编辑与并发读取，run代际处理旧运行选择，内容连接/open处理共享模态框替换与关闭，`writing`同时约束独立重读按钮和写表单。`reportValidity()` 还服务于绕过表单 submit 的重读按钮；HTML 的必填/长度限制改善操作，后端仍负责严格校验。未发现应删除的重复断言、无关参数检查或无可达故障的兜底。

## 所有权、重复与成本

`cancellationDialog` 两处生产调用均在 `tasks.js` 的同一任务详情所有者内，不构成跨文件复用。`show/read/active/current` 是共享该详情、run与请求代际的局部闭包，位置合理。既有 `api.js`、`ui.js` 的表单、文本 DOM、modal 和布局已复用；新代码没有增加模块、导出包装层或通用操作框架。批准与取消虽有相近的读取/写入外形，但材料准入、字段与已闭合语义不同，当前没有必须同步维护的抽象合同证据，不建议为外观相似强行提取。

没有新增自动轮询、自动重试或任务列表逐项运行查询。取消工作区只在打开且已有保存ID时自动读一次记录；新操作为先一 GET、再明确一 POST，操作继续使用原20秒后端预算。独立从原始请求数组重算四段合计118页面请求/11POST，其中10POST被受控拦截、1POST真实转发；另2辅助GET不混入页面总数。取消相关为28GET/11POST；真实段顺序为一GET、一POST、其后四次原记录GET，没有第二次取消或恢复POST。

最终只读段24GET包含三任务各自的自动选择与手工重复选择，合计6次详情及6次submission读取；这是已有 `loadPage/inspect` 与演练导航组合的成本，C1没有新增该调用。交付记录已把代表性加载/重开成本测量留给F4.4，当前没有单请求延迟或规模性能保证。无测试/CI修改，也没有引入镜像页面实现的测试框架；现有浏览器断言针对状态、原payload、无再投递、迟到隔离和布局等外部合同，未发现需要删除的冗余门禁。

## 核验实证与限制

私有原始实证在 `.ergora/checks/f4-task-cancellation-console/`。本审查实际读过四段浏览器脚本、command/result、真实恢复检查脚本及最终不变量记录；没有只依据测试通过作结论。

- 独立重哈希实际 wheel、348源码资源和两份 noneditable 安装，逐文件一致，wheel 为 `a4081f8d52acbc867e93f4933741438771c01c5df56298fed33f62ed02460664`。构建记录另核283冻结身份和基础Web无SDK；终核13模块语法exit0，既有架构检查日志为8 passed。
- 浏览器原始记录分别为40/6、27/1、27/4、24/0请求/POST，pageerror均空。核受控写payload、必填原因、prepared→unknown→requested、原intent不可编辑、读取失败、旧revision、ID/run更改、关闭替换、跨项目迟到及写中锁定；受控写没有转发。桌面丢回复和390px真实记录截图已由审查者查看，记录中的390px页面宽390、dialog宽/scroll均352。
- 独立重哈希104份旧文件，逐项保持；解码112个连续原history事件，唯一 `request_cancel` 为事件101，其request SHA、原因、signal SHA与原intent/attempt/result相符，原intent SHA为 `123da41c12423458d47fe4413ba4bdaede1ea93e8556ddb01a158d0d74ccf109`。唯一排队job的实际回执为 `CANCELLED` / `Task is fenced`，产物摘要匹配；没有据此改写原workflow结果。
- 审查者另执行只读SDK实时核三个精确原run：旧run为COMPLETED/REVIEW_READY、329/348事件且各仅一个approve_plan；新run为COMPLETED/CANCEL_UNCONFIRMED、112事件且仅一个request_cancel；无RUNNING workflow。实时GET原取消记录与浏览器丢回复后取回的record完全相同，确认/成功字段仍为null。此检查没有发信号、启动模型或改变持久数据。
- 核首个native证明脚本exit1与修正后v2 exit0为不同尝试，两个parser参数失败亦保留；未把失败尝试记成产品成功，未以换ID/重发取消修复验收。最终不变量记录还核无fixture journal落盘、原取消目录恰好三份journal、executor已恢复RUNNING。
- `git diff --check`由审查者实际执行通过。作者的文档初核为9份Markdown、316本地链接/锚点、27条README parser命令；本报告及最后登记变化仍需纳入终核。

没有重跑重型Python回归、安装或整段浏览器旅程。真实验证覆盖一次成功POST后丢回复及纯GET原ID恢复；prepared/unknown恢复、already_closed的无信号显示、旧revision和迟到行为以明确标注的传输fixture演练，未宣称这些分支均有本片原生故障注入。没有验证外部对账、lease释放、非Chromium浏览器、Windows页面实际交互或高并发性能；这些不由本地通过推导。

下一步：将上述范围提交、推送后，由本审查者核精确提交资源/已验包身份、该提交双OS必要CI步骤与实时远端。c2外部证据/显式对账、d候选导出和F4.4继续独立验收，完整F4尚未完成。

## 提交身份追加复核

2026-11-04，同一审查者只读核验已推送候选 `759c27ed06b781ca768a53c1e9e8c0eb1377e296`，唯一父提交为本片基线 `c54230eb8a6d3468ef33e6365c874a4e3a2407d6`。本次固定读取提交与 `git archive`，未用随后 C2 工作树代替 C1 生产身份。

- `git show`、`diff-tree` 确认12个文件：两个已审生产JS和十份范围内文档，包含本报告与B终结归档；无Python、测试、CI、依赖或冻结reference变更，没有main合入。
- 审查者实际在内存读取该提交归档并独立重算全部348个包文件，与保留的 `a4081f8d52acbc867e93f4933741438771c01c5df56298fed33f62ed02460664` wheel、原 `package-identity.json`、development/base两份noneditable安装逐项一致；两份实际direct_url仍指向此wheel。283冻结文件另与父提交归档逐项相同。
- 实际执行 `git ls-remote origin refs/heads/refactor/architecture-foundations`，实时返回完整 `759c27ed06b781ca768a53c1e9e8c0eb1377e296`，确认本次远端身份。
- 已读固定提交内的 `portability.yml`，核Ubuntu/Python3.11、Windows/Python3.12矩阵、20分钟界限和构建安装/冻结身份/原生回归及Windows专用安装升级步骤，未变更门禁。
- 直接解析本片 `ci/` 保存的官方run/job原HTML：[CI41808523543](https://github.com/626619403/Ergora/actions/runs/41808523543)有完整候选提交链接，实际可见 `Status` 为 **In progress**。初始job groups仅含Ubuntu126501521848且 `totalCount=2/hasMore=true`；该job原HTML的 `selectedJobId`匹配，但这些材料不能证明双OS或必要步骤已成功。未将作者状态摘要、抓取exit0或前片CI当作本片成功证据。

本阶段结论：精确提交、已验包/两安装和当次实时远端核验通过，无新增findings；**精确双OS CI及终结远端复核仍待完成**。本次只追加报告、读取固定提交/包及官方证据，没有重跑重型回归、安装或操作原run；待补齐官方最终HTML后继续同片复核，无需持续轮询。

## 精确CI与远端终结复核

2026-11-04 09:55:46 UTC，同一审查者独立解析更新后的官方Actions列表、run及两个job原HTML，固定候选仍为 `759c27ed06b781ca768a53c1e9e8c0eb1377e296`。本段是本片最新终结状态，前述未提交及CI In progress段落保留其当时范围。

[CI41808523543](https://github.com/626619403/Ergora/actions/runs/41808523543)在官方Actions原HTML的同一行显示完成成功并链接完整候选提交；run原HTML的提交链接一致、实际可见 `Status` 为 **Success**。两job原HTML各自的JSON props包含正确 `selectedJobId`，可见矩阵名与固定提交内workflow一致。下表每个必要步骤都恰好有一个 `check-step`，具有 `data-conclusion=success` 与 `data-job-completed`，其日志URL逐字等于 `/626619403/Ergora/commit/759c27ed06b781ca768a53c1e9e8c0eb1377e296/checks/JOB_ID/logs/N`。

|实际矩阵/job|必要步骤及精确日志序号|结果|
|---|---|---|
|Ubuntu / Python3.11，[126501521848](https://github.com/626619403/Ergora/actions/runs/41808523543/job/126501521848)|Build and install wheel:4；Packaged reference identity:5；Native application regression:6|全部success/completed|
|Windows / Python3.12，[126501522208](https://github.com/626619403/Ergora/actions/runs/41808523543/job/126501522208)|Build and install wheel:4；Packaged reference identity:5；Native application regression:6；Windows PowerShell 5.1 installer and upgrade:7|全部success/completed|

两个job全部步骤均无failure/cancelled/timed_out/action_required；Ubuntu的Windows专用安装步骤按workflow条件skipped。当前job groups单页仍为 `totalCount=2/hasMore=true`，本次以两个选中job的原HTML分别证明双OS，没有把单页groups当作完整矩阵。作者验证命令exit0与本次结论一致，但不是独立结论的替代品；未读取逐例日志正文，不由步骤状态新增测试数量、性能或延迟结论。

独立重算原HTML摘要并与保存摘要逐项一致：Actions为 `68ae9ad18780e4bddecebd9530ef7583c1172d23ddd3f8a6c53451f49b47725a`；run为 `f6586b802faabe8b79e0817a9ca2207767c3cf6e8bad841bc3219d0b0f9a519b`；Ubuntu为 `119e28588063aff01449549eedc1c8f9bdc85b64b9b1f356d59359762ad3e5eb`；Windows为 `940dd705759eb5dbdcf4e7a900a92cae3c9e72b7a4caee4d2c4a20fc9b960f31`。

终结轮另实际重读固定提交归档、保留的a4081f完整wheel和两份noneditable安装，348文件身份仍逐项一致，唯一父提交仍为c54230e；没有用当前C2工作树或其独立包替代。实际SSH执行 `git ls-remote origin refs/heads/refactor/architecture-foundations` 再次返回完整 `759c27ed06b781ca768a53c1e9e8c0eb1377e296`。本轮没有安装、重跑重型测试、修改源码/CI、发送信号或操作原run，只追加本报告及只读核验。

**终结结论：F4.3c1需求符合性与可维护性均通过；精确提交、已验包/两安装、实际双OS必要CI步骤及实时远端已闭合，无未解决findings。** 此结论仅关闭C1取消页面，不表示main已合入；c2外部证据/明确对账、d候选导出、F4.4及完整F4仍按各自切片验收。
