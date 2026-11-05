# F5.5：证据与交接恢复验收及阶段收口

日期：2026-11-05。状态：恢复组合验收、新的综合独立审查与精确文档交付/远端终结通过，F5.5及既定范围完整F5完成。基线为F5.4精确提交`4c87c2a4d37e567c3e7330bb66d6b0ab086655cc`；本片复用其f644858最终noneditable安装，不改变生产/测试/依赖/CI或冻结283资源，不重新发行同一源码。F5.0–F5.3已各自独立完整终结；F5.4精确推送和双OS CI41929749342已核，同片独立最终终结已通过。来源：[F5分片计划](../plans/2026-11-05-evidence-handoff.md)。

## 可验收节点

1. **离线接收者。** 在本次所有服务/HTTP已正式退出时，基础无SDK安装仍可核三份浏览器保存包；不创建control home、不联网、不执行材料。保留原结果和来源未认证语义。
2. **全新HTTP/浏览器重开。** 显式只启动Temporal，不启动worker/executor/模型；使用同一最终包和原持久目录，在新HTTP/浏览器重取三原run的合同、结果、索引和交接包。保存包与原CLI/浏览器字节完全相同，原43材料及取消结果不变。此处是恢复组合验收，不宣称新用户/空环境或新的业务执行。
3. **真实服务中断与恢复。** 保留一份已核的原取消run索引窗口，正式停止Temporal。明确重读索引、收集均须真实失败、无额外下载，旧索引只能作为先前观察保留，服务不自动启动。明确重启Temporal后从同一窗口重试，索引/包恢复且原结果保持。记录实际请求、失败和重试，不用受控响应代替本段。
4. **原状态与退出。** 原139文件、三完整history/outcome、两业务repo/refs/worktrees和claims/leases保持；正式退出本次owned浏览器、HTTP及专用栈，保留三个持久库。已有各片的源码/原生写/CI证据按原身份引用，不重放批准、取消、对账或候选导出。
5. **公开边界与综合审查。** 同步使用/Windows/项目手册及架构，修正过时页面说明，服务矩阵区分在线闭合索引/收集与完全离线verify。核文档链接/README parser和精确源码身份；新的fresh-context综合审查，普通文档提交/推送及同片实时远端终结后才关闭完整F5。纯记录不重复重型Python/格式矩阵或另建CI作业；F5.4自己的精确两OS CI仍需完成。

本片私有材料在忽略的`.ergora/checks/f5-completion/`，浏览器截图/包在`output/playwright/f5-completion/`；不覆盖各前片记录。下一节点G0需独立全新安装/数据旅程，后续F6–F10不在F5关闭。

## 本片实际验证

本片的`base-venv`和`development-venv`明确指向F5.4两套原noneditable安装；不是两次新安装。复用wheel完整SHA为`f644858498143dc077bf77114235f9896d01f5da6b008dd984684b5a2c521166`，352包资源、冻结283身份与原CI由F5.4负责。本片只新增组合恢复证据，不重复前片Python、格式、平台或模型矩阵。

|节点|实际命令/记录（相对本片私有目录）|结果与范围|
|---|---|---|
|完全离线接收|`verify-all-services-offline.py`、`all-services-offline.json`|专用服务与前片HTTP五端口关闭时，基础无SDK CLI核三包均exit0；原两REVIEW_READY和一CANCEL_UNCONFIRMED保持，无control home创建，未启动服务|
|新会话恢复|正式`service-lifecycle.py start-temporal`、新HTTP、`browser-native.js`|仅Temporal运行，worker/executor停止；新浏览器34 API请求、3收集POST和3实际下载、零pageerror；无新workflow或模型调用|
|独立材料核对|`verify-browser-native.py`，成功标签`verify-browser-native-r2`|三包135834/185003/11562字节，逐字等于原CLI与前片浏览器包；43材料引用、原回执/索引/正文一致；基础CLI三次离线exit0|
|真实中断|`browser-outage-before.js`、正式`temporal-transition.py stop`、`browser-outage-failed.js`|先1 GET读原取消索引，停止后实际GET索引/POST包均HTTP400（connection refused）；无路由拦截，旧观察保留、零下载/零pageerror|
|同窗恢复|正式`temporal-transition.py start`、`browser-outage-restored.js`、`verify-restored.py`|启动前核Temporal仍STOPPED，证明失败请求未自动启动服务；同一窗口2请求/1POST/1实际下载，索引逐字等于中断前；11562字节包与原CLI/前片浏览器完全相同，基础离线exit0，取消原结果保持|
|原状态保持|`native-snapshot.py before/after`|139文件、三完整history/outcome（329/348/112事件）、两业务repo内容/HEAD/refs/worktrees及3 claims/0 active lease完全一致；无运行workflow|
|正式退出|`browser-close`、`stop-http.py`、`shutdown-final`、`final-offline.py`|本片浏览器及HTTP退出；HTTP身份/属主/argv/起时核后SIGTERM，Uvicorn有序退出，工具shell真实exit143；正式services shutdown confirmed、两owned服务进程消失、五端口关/临时根空，三个持久SQLite保留|

本片浏览器合计39 API请求，其中5次POST均为只读交接收集（4成功下载、1真实失败），没有批准、取消、对账、导出或任务派工写。中断产生预期的浏览器资源失败日志，零pageerror不能表述为零网络错误。正常三原run与390px同窗恢复截图已查看；索引/材料/长SHA可读，未增加CSS、UI库、持久状态或后台扫描。

首轮`verify-browser-native`在浏览器尚未结束前尝试读取结果，实际exit1；保留原命令/日志，不覆盖为成功。等待浏览器命令正式exit0后，同脚本以`verify-browser-native-r2`执行exit0。脚本时序失败不归为产品故障，也不从前片继承本片通过。后续依赖验证、快照和服务停止均等待前序命令完成。

## 文档与结构边界

使用手册的服务矩阵新增在线闭合索引/收集和完全离线verify；项目手册改为现有正式任务/交接页面；Windows手册新增基础离线核包与Linux/WSL2收集边界及PowerShell命令，并修正过时的功能分支描述。README主旅程补闭合证据入口，当前架构和总计划同步状态。既有架构图已包含Tasks → reference → Handoff与CLI/Web入口，本片不为相同调用关系重复造图。

F5不宣称未知token/费用/模型调用为0，不补造未记录的Skill、记忆、评价集或来源采用。包内摘要验证不证明来源、完整history或候选可合入；交接ZIP不自动执行。Windows原生可离线核包，正式开发执行与收集仍在Linux/WSL2；本片未做Windows浏览器/WSL2本机或空OS安装验证。MLflow关联和可选OTel投影的扩展不作为当前已交付事实。

下一步：刷新本片完整文件/静态清单，取得新的fresh-context综合审查，完成普通文档提交/推送与同片实时远端终结；同时保留F5.4自己的CI/审查终结。之后独立制定并实施G0新用户旅程，不将本次原run恢复作为G0。

## 综合独立审查

[新fresh-context综合审查](2026-11-05-f5-completion-review.md)已完成，本地需求符合性与可维护性通过，范围内无findings。审查者独立重算352资源、两原安装、三包/43材料、139原文件/两repo/leases及39请求/5收集POST/4下载；另用无SDK基础安装四次离线CLI均exit0、未创建控制目录，实查五端口关/原进程退出/临时根空/三库保留。未重复重型矩阵或启动服务；F5.4精确CI的官方来源摘要也已复核。加入报告后的最终静态/精确文档提交及普通推送后，再登记同片终结与完整F5完成。

## 阶段交付完成

纯文档精确提交`cd0b5a0a7d5301e30ba5febe45e4e73ba7e218a4`已普通推送，唯一父4c87c2a；12份Markdown、370本地链接/锚点和30条README parser命令通过。352资源归档仍等于原f644858包，生产/测试/依赖/CI无变化，复用F5.4自己的精确两OS CI，不伪造本片新运行。原综合审查者已从提交对象、真实普通push及实时远端独立最终核对通过、无findings，见[最终终结](2026-11-05-f5-completion-review.md#精确提交与同片最终终结)。F5.0–5各片保持原包和CI身份，既定范围完整F5完成；下一G0全新用户旅程单独验收，未记录上下文/费用及未验平台仍按原边界保留。
