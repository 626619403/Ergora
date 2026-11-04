# F4.2a 独立审查

日期：2026-11-04。审查者：`/root/task_creation_console_review`，全新上下文。先读 AGENTS、PLAN、原始 F4/LC1 及交付、独立审查、review-pr 技能，再读实际差异和邻近合同，最后读作者记录。

## 当前结论

需求/代码、可维护性和资源成本审查均无高置信 finding。该结论限于已审代码及已读本地证据；最终产物核验和交付尚未收口。

基线及源码审读时 HEAD 为 `2137a95418879d48cce557016caa5c7f0d6a6a1b`。生产差异仅 `src/ergora/data/console/tasks.js`、局部 `style.css` 和 `app.js` 帮助文案；另读 README、USAGE、当前架构、PLAN 及作者记录。没有后端、测试、依赖、CI 或冻结 reference 改动。

## 代码与维护依据

`tasks.js:133` 限定项目已登记开发模板和兼容草稿，训练保持独立；`:161` 复用服务端编译，`:179` 展示完整 snapshot、冻结角色、修订和摘要。`:219`、`:246` 使编辑立即废弃旧确认。`:189` 使用原返回快照明确创建，发出前保存原 ID、锁定输入，没有 start 调用。

`:56` 仅 pending 开放恢复，携当前项目修订及原 intent SHA；conflict 无覆盖入口。`:107` 查询不依赖列表包含任务，`:307` 合同失败保留原 ID 查询入口。`:127`、`:217` 检查页面/内容连接、open 状态和请求代际，结合 ui 内容替换及 app 项目切换，阻止旧结果恢复确认或写新视图。

已追踪 web/tasks/reference_task_creation、definition schema、既有创建测试和工作流草稿所有者。服务端继续拥有修订、不可变意图、幂等性及冲突语义。新增流程内聚于任务视图，复用 api/ui；不需要新通用框架。guard 对应可达的编辑、离页、重复点击及迟到响应，没有重复实现后端验证，没有新增生产断言、测试或 CI。

没有自动创建重试、轮询、模型或执行服务启动。完整预览成本随已有服务端文件上限增长；本次未测最大输入性能，不声称性能提升。

## 已检查证据

最终 wheel 记录为 `421c81f203292610173a0885163c15297e018df93b11c805adede1f5328ed7b7`。已读 package.py、身份 JSON 和实际 build/install 命令及原日志；其记录为348文件=源码=wheel=两非editable安装、冻结283、13语法通过。审查者亲算三生产文件 SHA 与记录一致；348文件全量重新核算未执行成功，不能称为审查者再次独立算过。

已读保存脚本、原 CLI 结果及 JSON：最终 normal-final 为34页面请求/5真实POST（3 preview、2 create），另2只读helper；输入=服务端snapshot=DOM，修订2、重载选择、390px无溢出、0 pageerror。最终 lost-response 为8/2：一次真实发布后abort回复，重载保留原ID并GET同一published intent，没有自动重发。最终 late 为14/5：真实回复持留时编辑/关闭/替换不恢复确认；create已发布后关闭并切训练项目，不覆盖新页面/提示，回原项目GET同一intent。

初包 normal/duplicate/prepare-recovery/recovery-real 保留原身份：真实子进程发布中断保存intent及3文件，GET pending后明确恢复，当前修订2/原创建修订1及旧角色保持；一份实际文件冲突不可覆盖。它们没有在最终包重新执行；首个normal脚本等待失败未计通过。已亲看最终桌面治理预览和390px大型任务预览截图，中文可读，截图可见区域无横向问题。

## 待续核

- 最终9份intent、8份完整发布合同与result内容SHA；conflict/recovery原字节；原F3的416文件前后身份。
- 最终新增合同读取失败原ID按钮及帮助文案的额外浏览器复验；lost/late不扩大为这两个入口的验收。
- 文档静态终核、作者状态更新、本片提交、精确CI及远端核对。

本审查未运行测试、浏览器、应用/API、模型、构建、安装或服务，未改生产源码、提交或推送。此前授权静态核算及reviewer产物写入遭自动审批deadline，均未执行；超时不证明动作不安全。没有生成或引用 verify-created.py/browser-final-readback.js 为已运行证据。V4 CI及历史711后端结果不证明新DOM；F4.2b/c、完整F4及真实运行仍在本片之外。

## 2026-11-04 补充证据续核

审查者仍为`/root/task_creation_console_review`；审查者两次续写审批deadline未执行，本节由根代理根据其最终原文转录归档，覆盖前文待续核列表。需求/代码、可维护性及资源成本的本地审查通过，无新增确认finding。

已只读审查`verify-created.py`和`verified-created.json`：9份intent中8份各七文件内容等于原intent，result逐项匹配intent、compiled及各文件canonical SHA；1份conflict保持task.json实际冲突、2份匹配、4份缺失、无result。canonical编码已与既有contracts.canonical_sha对照。recovery记录的35个既有文件字节保持；原F3的416个文件与native-before.json摘要一致；最终421c81包身份表内348份源码/wheel/两安装文件逐项一致。pending-f4原修订1及旧reviewer保持。上述核算由实现方成功执行并保存，审查者只读检查，未重新运行。

已读`browser-final-readback.js`、原CLI及command/result，exit0：重新加载后7真实GET、0POST、0pageerror。实际合同失败面板保留conflict-f4原ID，按钮进入readonly原ID查询，真实conflict无恢复按钮；pending-f4当前published仍为原创建修订1/当前项目修订2及旧reviewer；最终app帮助文案实际DOM已查。原ID失败入口和帮助文案的本地待验项已补齐，初包pending恢复仍保留原执行身份，没有提升为最终包重新执行。

已读复用的`.ergora/checks/f4-task-console/check-documents.py`及`static-documents.json`：比较基线2add1bf并包含未跟踪文档，13份Markdown、328本地链接/锚点、26条README命令parser，missing为空。该结果有保存的文档SHA；本次报告续写后，由实现方按最终文档身份再核。

此前审批deadline的命令没有执行；新增成功证据来自之后另行完成的操作，未追溯改写失败尝试。审查者没有运行测试、浏览器、应用/API、模型、构建、安装或服务，也没有修改生产源码。

剩余门禁为最终文档身份核对、作者状态收口、本片提交，以及该精确候选的CI和实时远端核对。V4 CI和历史711后端结果不替代新DOM证据；F4.2b/c、完整F4及真实运行仍在本片之外。
