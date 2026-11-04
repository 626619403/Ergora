# F4.4b2：原job日志与材料页面

日期：2026-11-05。状态：已完成。单独提交推送`77b334c62346f92868c22c067949b0caf2d74d48`，350归档=43e121包；本地/提交/实时远端及精确双OS CI41896900471的同片最终独立审查均通过，无未解决finding。前置b1的1dbe969及其精确双OS CI41892668276、同片独立终结完成；前置a2的8f1489c精确CI41882469707及同片独立终结通过。本片保持独立UI发行与提交身份。

## 最小消费者

在现有原运行事件dialog内，为`dev_submit`调度事件提供“读取原job证据”。使用固定原run及该事件ID打开新dialog，先明确读取job目录和原发布回执；不需要用户输入本地路径。回执显示job/stage/candidate/摘要及published的实际含义，missing/not_found保留未知。产物名称来自回执下拉框，用户明确读取第一段/下一段；固定首次receipt SHA，单次8192个Unicode字符，只保留当前窗口及偏移/完整产物摘要，不累积全文。

复用现有安全文本、select、pre、facts、dialog和GET错误处理，不增加依赖、CSS、持久缓存或后台读取。一个dialog同时最多一条读取；artifact切换使旧回复失效并清窗口，错误保留已读窗口和原偏移以供明确重试。关闭/替换、编辑run、切任务/项目或离开页面后的回复失效；重新打开从job目录读取，不自动重发工作流或恢复写。

## 验收

1. 单模块/全资产语法和独立noneditable发行身份；b1 Python不变，不重复已经通过的重型矩阵。
2. 两个原run通过事件页选择真实plan job，回执=CLI/API；手动读取模型日志和计划，固定回执SHA、UTF-8字符偏移/终态、重开、390px及安全文本可读。仅GET，无新模型/原生写。
3. 受控missing/not_found/网络错误、回执变化/非文本拒绝，以及单在途/切artifact/关闭/替换/编辑run/切任务项目/离开页面迟到隔离；不把模拟数据当真实服务验收。
4. 139原文件/三history/outcome/refs/leases前后保持；新的fresh-context结构/性能/冗余审查，之后单独提交/精确CI/远端终结。完整F4待c组合与专用服务栈正式退出，不由本片代替。

下一：新的独立审查、独立提交推送与精确CI/同片终结，然后推进c组合收口。F4/F5/G0未完成。

## 局部消费者已实现

两次直接源码patch的审批deadline未执行，随后先保存完整私有候选、核当前两个JS等于b1原包、对两个完整候选运行node语法检查，再一次写入现有tasks.js/app.js。现已实现：事件表仅dev_submit调度行提供job入口，原run/事件固定，读取目录/选择产物/手动8192字符窗口、固定原回执SHA、当前窗保留及作用域/选择切换失效。未增加模块、依赖、CSS或持久格式。局部私有函数归现有原运行详情消费者，复用既有modal/facts/pre/select/API；b1 Python及350资源的其余内容保持。

## 实际本地验收

私有证据在`.ergora/checks/f4-task-job-console/`，不提交原生数据或运行配置。

- 最终wheel SHA256：`43e1211ea12c7522b928881d10b1c0497489e6a0a68930bbf86f10eb260c8ca1`。350资源逐文件核源码/wheel/两独立noneditable安装相同，冻结283不变；独立构建安装21.84秒，最终资源/13模块语法0.86秒。基础与development安装分开，HTTP加载该片development安装。
- `browser-real-command.json`/`browser-real-result.json`：真实两原run，经事件页选择原plan调度事件56，47GET、零POST/零pageerror，48.57秒。完整回执与原API/CLI相同；两run的model-log各2窗、execution-plan各1窗，固定回执SHA/偏移、选择不自动读取、单窗/末尾停用/重开清窗/无后台流量通过。`browser-real-verified.json`独立重建四产物，12515/13886字节日志及4002/4198字节计划与原文件/SHA完全相同。桌面及390px页面/弹窗无溢出；已实际查看两张390px目录/计划截图，不扩大为查看全部截图。
- `browser-boundaries-command.json`/`browser-boundaries-result.json`：183GET（24job GET）、零写/零pageerror，85.72秒。目录503/not_found/missing后明确重读；首窗8192 Unicode字符与HTML字面文本安全，下一窗503/not_found/回执变化400/NUL400均保留当前窗和原偏移，重试后末尾停止，无轮询。受控目录/材料GET覆盖单在途和七种迟到隔离：切材料、关闭、替换、编辑run、切任务、切项目、离开页面。modal背景inert控件使用合成事件仅检验作用域失效，不声称普通用户可穿透弹窗；项目/任务/事件/状态仍走原服务只读。
- `native-snapshot-before/after-command.json`、`native-before.json`、`native-after-verified.json`：前5.60秒/后1.92秒，139原证据文件、三完整history/outcome（329/348/112事件）、业务refs/worktrees/工作文件及三claim/零active逐项相同；两正常REVIEW_READY、原取消CANCEL_UNCONFIRMED保持，零Running。没有新模型、信号、取消、对账或导出。

Python后端未变，沿用b1已实际完成的150源码/103包合同/10既有边界各自证据，不重新运行重型回归，也不把旧包CI套给当前UI。新的独立结构/性能/冗余审查与精确CI仍待完成。窗口响应限制不等于后端完整摘要核验的总IO/内存上限，公开手册保留该限制。

## 独立本地审查

新的fresh-context审查者先核原diff/邻接API与DOM生命周期，再独立复算350资源/两安装、283冻结、13语法及当前HTTP实际两JS；真实47GET/四原产物、受控183GET/24job GET和七种迟到作用域的实际执行脚本/日志/Result逐项一致。139当前文件、leases、业务repo及三份保存history摘要重新核对保持。需求与可维护性均通过，无finding；窗口成本只按实际测量说明，没有新增缓存或公共抽象。下一独立提交并核350归档=43e121包，正常推送、精确双OS CI与同片终结，c另行交付。

## 提交与远端身份

独立10文件提交`77b334c62346f92868c22c067949b0caf2d74d48`，生产只有两个JS，另八文档含前片b1状态归档；不含下一c设计。提交前八文档291链接/锚点、27条README parser命令通过。Git archive350逐文件等于43e121包，正常RSA推送前核远端仍为原1dbe969，推送及实时远端核均exit0。原B2审查者独立复算提交/包/文档与实时远端，追加报告通过。精确[CI41896900471](https://github.com/626619403/Ergora/actions/runs/41896900471)正在核对，未继承b1 CI作为本片通过。

官方CI41896900471最终Success，Windows126808727970及Ubuntu126808728539的wheel/参考身份/原生回归全部必要步骤成功，Windows PowerShell 5.1安装升级成功。官方原run/job HTML、完整commit/selectedJobId及必要步骤日志URL均持久归档，verify-ci退出0。原B2审查者独立重核原HTML/来源字节SHA及实时RSA远端77b334c，再次通过、无未解决finding；终结报告已落盘，B2完成。F4.4c与完整F4保留单独审查范围。
