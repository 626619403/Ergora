# U3 日常安装交付

日期：2026-11-14。按[升级计划](../plans/2026-11-14-daily-installation-refresh.md)推进；目标产品为`41dd5aa30f589b5c27a1cc3f09db59d66005a40f`。本片是安装和验证，不修改产品源码或283冻结参考文件。

## 当前状态

原日常452产品／3 preset已完整备份；B2i自己的CI及原独立终核通过后，已将同一551产品／23 preset wheel离线装入原home应用。两RECORD／283冻结、38 distributions及4,550非应用文件／symlink与原启动器保持；实际CLI／HTTP的65命令／72检查／10读取已通过，原fresh-context安装终核已通过，另自身模板补验41.303秒approve及完整原件已获独立核准；文档已随6d4006e普通发布，作者完整SSH Ref核准，本片完成。下文早期未替换／待做记录仅代表其当时状态。

机器路径、依赖原件、备份、配置／状态逐文件身份和可能敏感内容只保存于本片私有验收目录。正式默认业务state保持原位，烟测使用独立state；不将其他项目或参考运行环境纳入本片修改范围。

## U3.1 前像与备份（升级前）

日常启动器解析到原home应用，Python3.12.3，452产品文件／3 preset／38 distributions；一次限定`/proc` argv观察相关活动进程为0，不声称全系统或后代隔离。已知默认业务state不存在，因此没有需归档的业务state，烟测将显式使用独立持久目录。

完整venv备份38,626,813B，SHA256为`a22ee071849df6995ec59f6733dd2a6ac4f77057757d0c2d771fdfedf3a2e735`；6,190归档成员中的5,051普通文件与symlink逐项等于源，归档前后源身份保持，耗时20.638秒。备份保存在用户home持久私有目录；本片未替换应用、未执行恢复，没有修改业务／认证或其他参考环境。默认状态、依赖和启动器原件与归档路径仅保存私有。U3.0发布依赖、U3.2升级和后续日常入口验收仍开放。

原日常依赖的只读`uv pip check`退出0。新fresh-context安装评审者已独立核初始五文件快照、备份归档／原venv逐项等同和候选wheel／551 Git产品／RECORD／283；预审未见阻断问题。待B2i独立CI终核后才写精确release gate并替换；实际安装和CLI／HTTP原件仍待生成，预审不当作安装完成。

## U3.0发布前置与U3.2实际升级

B2i的41dd5aa精确普通发布、自己的CI43459951488八job／30必要步骤与原独立终核均通过。已在私有release gate核报告、发布／作者Ref及独立终核原件SHA，随后再观察相关活动进程、核原venv与备份及默认state，才执行原home应用的离线仅Ergora重装。

安装的wheel SHA256为`34e6b375c8771fa67bb1b02a71070f289ec72d5b0c99badac3afd28373fee208`；551产品精确等于候选Git／wheel／实际Python3.12安装，559wheel文件、564installed RECORD行、两RECORD及283冻结均通过。新包基础及原web／temporal／gepa／task-mcp requirements满足，前后依赖检查退出0；38 distributions的版本及4,550个非应用普通文件／symlink内容身份保持，原启动器symlink／目标及解释器shebang正确。已知默认业务state仍不存在，备份未恢复。

原件installation SHA256为`ed1b63242ca301329a1b4f3923e18d2b9937528f4d80fbd500e6f54e34a49fbd`。此步只升级应用包，没有模型／GPU／native或业务运行；下一沿实际启动器做隔离日常入口验收，再由原fresh-context安装评审者终核。

## U3.3日常CLI与页面

实际默认启动器直接列23个bundled preset且未创建默认业务state；独立持久state中的八代表根为原治理／大型变更／训练v1、重构、训练v2及新cluster／低精度／kernel。逐根实际导入、完整manifest／input复验、全部结构祖先和自身资源正文、Codex task-MCP准入均通过；治理和kernel重复导入身份保持。带真实本地Git初始fixture，所有写入仅在验收state／fixture，无GitHub／GitLab业务写入。

共65命令／72检查通过，10 HTTP读取全200，CLI与页面23条目相等；页面项目／Agent定义／安装组合／OpenAPI及静态资源读取通过。原agent runs为空，未调用模型；所属console进程已回收、所属端口关闭，已知默认业务state仍不存在。本片没有重跑既有六阶段、方向模型或GPU旅程。

[公开小型投影](evidence/2026-11-14-daily-installation-refresh.json)SHA256为`f777e48385ed3cdf79f4bc5dd60f78581acc11649e604252121b4f84ab4e6d51`，原命令／HTTP正文、逐根manifest／input、准入及summary均留私有；不公开inference配置或机器路径。原fresh-context评审正在对这些实际原件独立终核。

## 日常安装自身模板补验（独立于65命令旅程）

按用户每大项使用自身审查模板的要求，追加一个新输入的原结构模板调用，审查本次训练手册及四个私有备份／安装／CLI／投影脚本。使用升级后的日常Python3.12与独立审查state、text-only完整正文、显式已授权Codex回退；不重跑此前各方向模型或原65命令旅程。该补验的模型调用与安装／CLI／HTTP阶段分开记账，不冒称不同后端或完整独立安装审计。新fresh-context独立评审者仍核实际原件。

补验已实际成功：新日常Python3.12／原结构模板run `b3877e22073340d3b3887030cbf99123`，41.303秒，`approve`。五份完整文件54,066B及全部继承资料已核在实际input／prompt／stdin；input digest为`d09257dedbc490298853dd917ea3773e8949da6d267cb0baa1e523e6f2ba832a`，原result SHA256为`d66062a1905ce5f3031c63ef99a3f8a0a90c5b220c366cef69d0679005113f43`。该次原生只读Codex会话只审结构文本，没有MCP读取、GPU、完整独立证据或异后端复验主张。65命令／HTTP原state的零run保持，另一个审查state的一次真实调用单独记账。

## U3.4独立实际终核与本地出口

[同一fresh-context评审者终核](2026-11-14-daily-installation-refresh-review.md)需求／可维护性通过，开放0／0，无阻断finding。实际安装／两RECORD／283、38依赖和4,550非应用文件／symlink、启动器／默认state、原release gate获独立核准；65原命令、16完整manifest／input树、38叶／175资源213,338B的源／祖先／正文与8个选定准入逐项核准，10 HTTP共620,206B及原包静态字节、所属server原结束与后续PID／端口观察均通过。原65命令state没有模型run，额外自身审查state恰一原run；两阶段不混计。

新增自身模板的五文件54,066B、3继承资源、原input／stdin／native终态／result与approve获独立核准。日常3.12解释器路径通过原工具启动argv的作者转录和原环境身份绑定，没有冒称原run新增sys.version字段或独立OS exec trace。报告12,699B，SHA256为`82789760722c9839f3d6619952956bd54610fd7feb3a558046888b3c4aaa23eb`；独立最终11文件／37原件身份快照manifest SHA256为`de118efad1370fa8bb7b935381bc326a606c825cfe0945e7bf5f143f76212b8e`。

本地安装出口完成；公开投影仍为6832B、只覆盖原安装／65命令／HTTP阶段，自身模板补验另记。备份恢复、全home检查、完整原生日志／artifact内容、GPU、业务六阶段重跑与B3／C2不在本片验收内。下一普通提交／推送本批文档，再继续原计划C2和真实workload实验。

## 文档普通发布

本批十七份已审Markdown／证据JSON普通提交并推送为`6d4006e4cde609da90a97b88f0ce871923385c9f`，父为41dd5aa。发布快照manifest SHA256为`4b00445fb6fc14e9b2d955d99909d786d1822321a63320d2d71fdcd82f18140d`；staged／Git blob逐项与快照相等，提交后工作树清洁，普通push退出0，作者SSH完整远端Ref同SHA。208本地目标／17锚点、4凭据值、283冻结与diff检查通过。

只发布文档和小型证据投影，551产品源码及依赖仍为已验41dd5aa；没有把产品CI43459951488冒称该文档提交自己的CI。U3安装／日常入口与自身模板／独立审查及本批文档发布完成，后续C2与真实B3分别验收。
