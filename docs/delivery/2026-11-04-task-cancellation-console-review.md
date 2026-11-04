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
