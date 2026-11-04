# F5.3b：显式HTTP交接包下载

日期：2026-11-05。状态：完成。本地实现、发行/真实HTTP下载、[新的独立审查](2026-11-05-handoff-download-review.md)、精确提交/普通推送及双OS CI/同片终结均通过，范围内无未解决findings。仅修改现有Web生产所有者；9项真实红例、25项源码定向及最终包27项通过。源码基线`87538b3dcafb13ca5bbc8191f84e5a4b0fbf0083`；前置[F5.3a](2026-11-05-task-handoff.md)的原生收集/离线校验、本地103项和独立复核通过，精确提交已建立并正常推送、远端一致，精确CI41921284766及同片最终独立终结现已通过，a片完成。前片CI终结前不推下一生产候选，不混归发行身份。来源：[F5计划](../plans/2026-11-05-evidence-handoff.md)。

## 合同与所有权

新增显式`POST /api/projects/{project}/tasks/{task}/handoff`，严格JSON正文只接受原`run_id`及1–60秒`timeout`（默认20）。沿用同源与`X-Ergora-Request: 1`边界，拒绝额外字段，浏览器不能指定服务器源路径或输出路径。该操作只收集已有原材料，不修改注册、任务执行或归属，不增加revision/批准协议。

同一`tasks.handoff`用例负责原run归属、闭合history、FileAdapter和收集。Web只在每次请求的私有临时目录内选择尚不存在的`handoff.zip`，调用用例，读最多72 MiB+1字节，核对实际响应字节与收集元数据的整包SHA，再退出临时目录上下文并返回`application/zip`。成功及普通失败均清理；不使用FileResponse/后台删除留下响应发送与文件关闭的竞争。强制进程退出仍需按运维方式清理残留，不承诺崩溃事务。

响应固定attachment文件名`ergora-handoff.zip`及`X-Ergora-Handoff-SHA256`，保留既有no-store/nosniff。成功响应不返回服务器临时路径；浏览器选择自己的下载位置。响应头只是本次字节摘要，不构成来源认证。受限整包缓冲有内存成本，不声称流式吞吐或峰值内存等于72 MiB；不重复离线ZIP/schema验证，也不新建下载票据、缓存、收集器或持久账本。

## 验收与后续

1. 先为缺失入口建立轻量HTTP反例。真实handoff格式库参与正例，任务/native端口替换，避免为传输验证初始化Git/原生注册。核响应字节/头/离线可验证、临时目录生命周期；正文/同源反例不得调用收集，收集失败、大小超限、字节与元数据不符须拒绝并清理。测试跨平台，复用现有CI。
2. 最终noneditable包、352资源/两安装及283冻结；三个原run实际HTTP下载，独立基础安装离线核对原43材料/索引/SHA和原取消结果，错误run/跨项目拒绝，前后原文件/history/outcome/Git/leases保持、正式退出专用服务并保留数据库。
3. 更新使用手册、架构及计划，新的fresh-context独立审查；精确提交/普通推送、双OS CI和同片终结后关闭b，再以F5.4页面消费统一索引和下载入口。完整F5.3需a与b各自验收，页面或完整F5/G0不在此片关闭。

## 首轮实现与验证

`web.py`新增严格请求模型及一个路由，真实消费者直接复用`tasks.handoff`；未改原生收集、离线格式、Task/State合同或任何冻结资源。`tests/test_handoff_download.py`复用轻量格式数据，端口替换只隔离任务/原生服务，实际ZIP库及collector参与响应/离线正例；避免初始化Git或完整运行时。9项缺入口红例在87538b3精确包均因404失败，保留完整日志；实现后16项下载测试与9项架构共25 passed，保留一个上游TestClient弃用warning。真实下载、最终包和新的独立审查未完成，不把传输端口替换当原生运行验收。

不自动收集，不启动服务/worker/模型，不隐式修改任务或Git；完整F5.3需a/b各自精确验收。

## 最终包与真实HTTP验收

最终wheel SHA256 `54548bc34aeb8cf7d9f55a62cbf3d1ef3f27695f5880afe5898fd99ec53095ae`，352源码/wheel/两noneditable安装逐文件相同，283冻结身份保持；基础安装无Temporal SDK，独立运行离线验证。最终包27项通过：16下载、9架构及2项既有页面/证据索引HTTP代表，保留一个上游弃用warning。未重跑未修改的完整collector/格式矩阵，也未新增依赖、CI作业或测试框架；a的精确包与CI继续保持原身份。

最终包通过CLI serve启动真实loopback HTTP socket服务，每次下载均调用登记原生进程及Temporal RPC；不是以替换端口或进程内ASGI响应代替本段验收。三原run成功下载、基础安装离线校验，每份材料逐字节核原receipt、源产物、前片索引；三个响应与a的原CLI包完全相同：

|原任务|材料引用|材料/整包字节|原结果|
|---|---|---|---|
|repository-governance正常|23|105296 / 135834|REVIEW_READY|
|large-change正常|19|156248 / 185003|REVIEW_READY|
|repository-governance取消|1|59 / 11562|CANCEL_UNCONFIRMED|

另6个真实失败请求：错误原run/跨项目各400、服务器路径字段422、跨源/缺请求头各403、GET405；全部不返回包SHA头、请求临时目录均为空。共9个业务HTTP请求，启动健康读取另计。成功响应含ZIP/content-disposition/no-store/nosniff及正确整包SHA，服务端每次请求临时目录在响应返回前清理；基础verify未创建control home。

HTTP命令整体约1.59–1.88秒，基础CLI离线约0.22–1.02秒，仅本次11–185KB、1–23份材料的小规模观察，不代表最大载荷、并发吞吐或峰值内存。未为本片重新运行agent/worker/模型或改变原业务结果。

前后139原文件、三完整history/outcome、两业务repo内容/HEAD/refs/worktrees及三claims/零active lease完全相同。HTTP服务有序SIGTERM退出，Uvicorn原日志确认application shutdown complete/finished PID，真实返回码-15保留；端口关闭、临时根为空。专用Temporal/Supervisor正式shutdown confirmed，两个owned进程退出、五相关端口关闭、三个持久数据库保留；最终离线原文件/leases重核通过。私有命令、原日志、HTTP/包/字节与生命周期证据分别位于忽略的`.ergora/checks/f5-handoff-download/`，未覆盖a片。

本地验收及新的fresh-context独立审查通过，范围内无findings；审查者独立重核352资源/两安装、原43材料、离线CLI、139文件/Git/leases与正式退出。审查期间a的CI终结和宏观计划更新仅改变文档，生产/测试/最终包身份未漂移；提交前刷新完整清单和全部当前文档静态检查。之后精确提交/普通推送、双OS CI及同片最终终结，再推进F5.4页面。a已完成，完整F5.3/F5/G0仍未完成。

提交前当前10份Markdown的346个本地链接/锚点及README30条CLI parser命令通过；Git差异无空白错误。静态结果绑定包含本片审查报告、a终结和宏观计划更新的当前范围，不沿用初轮8文档身份。

## 精确交付终结

精确提交`bde57e17d84a0063683be9c5c34392072b255853`已普通快进推送，实时远端一致；352资源Git归档与54548b最终wheel完全相同。CI[41925067903](https://github.com/626619403/Ergora/actions/runs/41925067903)的Windows126907187498与Ubuntu126907188269均成功，全部必要步骤及精确日志URL由同片审查者独立核原HTML确认，再核实时远端。范围内无未解决finding，b与前置a各自完成，完整F5.3完成；F5.4页面、完整F5/G0不在此片关闭。
