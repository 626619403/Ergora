# F10a 记忆有效期：独立需求审查

日期：2026-11-14。固定基线 `f47cd50fcce600fba92f64aff73982012f6e31c9`，候选为其上的未提交工作树，包含新增计划／交付文件。按原始[具体合同](../plans/2026-11-14-memory-validity.md)和[F10 总计划](../plans/2026-11-14-evaluated-improvement.md)独立核对；未预设结论。源码初核后沿同一需求轴补核[最终交付](2026-11-14-memory-validity.md)及[证据摘要](evidence/2026-11-14-memory-validity.json)的实际原件，形成最终本地结论；固定发布及自己的 CI 另验。

## Compliance

**最终本地需求审查 approve，实证 finding 0；固定发布及自己的 CI 待补核。** 没有发现需要提出修正的漏项、错误实现或越界功能。

|核对范围|源码／调用路径与结论|
|---|---|
|时间与持久语义|`memory.py:14` 将带时区输入归一 UTC，缺时区、非法日期和 UTC 归一上下溢均可见拒绝；`:26` 在观察时刻等于到期时刻即判 expired。catalog 不写回修订。|
|省略、清除、冲突与恢复|`memory.py:61` 在原 `BEGIN IMMEDIATE` 中检查 revision 并继承最新期限；只有显式 null 才清除。`:117` 恢复所选历史的期限，已过期历史不会续期。`:96` 仍清空全部历史正文／来源并禁止恢复已删正文。|
|默认读取与显式目录|`records`、CLI list、原 dashboard 与本地 search 只返回 valid；catalog 在一次观察时间下列出当前原记录及 valid／expired／deleted。历史及已归档 run 没有新增改写路径。|
|ReMe 权威与在途变化|`memory.py:147` 清理过期／删除镜像，保留 watcher eventual 界限；`:191` 在远端返回后重读 catalog，只接受仍有效且 revision 未变化的本地原件，排除外项目、重复和远端正文。|
|升级、读写权限与备份|`state.py:99` 只替换原 21 表的 63 个 writer fence，沿原迁移事务及升级前备份；未增加表或改写旧记忆。新版本门禁拒绝旧客户端重新打开；旧已开 writer 被拒绝，旧 reader 与缓存不能撤销，文档明确先停止旧进程再统一重启。原完整离线备份／原 home 恢复合同保持。|
|CLI／HTTP／页面|CLI 的 `SUPPRESS` 与 HTTP 的 `exclude_unset` 保留字段缺失，null 单独转交；页面以文本预填原 UTC 期限，清空显式发送 null。独立 catalog 入口展示到期／删除状态，过期可更正／恢复，删除只读。`memory.js:12` 用 view 内序号与连接状态丢弃逆序／离开视图后的读取。|

核查生产五文件及四个改动测试文件的当前 SHA256，均与私有初始审查清单一致；公开用法／架构也一致。两计划和交付按实际文件读取，交付及进度后续追加不据初始 patch 推断。C3 文档补账不计为 F10a 产品变更。

## Maintainability

**本需求轴可见范围无实证 finding。** 时间解析、继承、catalog 和最终过滤保留在原 memory owner；CLI／HTTP 仅转交显式参数，State 沿原门禁与事务，页面复用原 ui／api。没有引入第二存储、调度、后台轮询、通用日期抽象或依赖。本结论不替代另一个 fresh-context 结构轴。

## 源码初核与证据界限

- 已读 `AGENTS.md`、当前计划、两份原合同、活动交付、基线以来实际差异和 `memory` 的生产调用者；核对新增回归与迁移／备份原实现。源码日志记录六 suite 78 通过／1 跳过、14.22 秒，早于最终 OverflowError 转换，未冒称最终安装结果。
- 使用已有环境显式导入当前源码，仅在 SQLite `:memory:` 执行小反例：负时区跨日、微秒到期边界、八类非法／溢出输入不落盘、省略继承／null 清除／历史恢复、同 revision 冲突、删除不可恢复及项目隔离通过；CLI 三种字段状态与 HTTP 缺失／null 转交通过。
- 纯内存模拟 ReMe 返回期间到期／删除／更正，连同稳定 canonical、重复与外项目命中检查通过；未向外部 ReMe 发请求。内存 v4→v5 核 21 表／63 fence、旧行原字节不变、21 表插入及非空记忆 update／delete 拒绝旧 writer、旧 reader 仍可读，新 writer 可写通过。
- Node 对实际 `memory.js` 配轻量 DOM 替身执行，逆序读取和脱离视图后的结果均被丢弃；这不等同真实浏览器旅程或视觉验收。
- 首次探针所用系统 Python 缺 FastAPI，未执行行为检查；改用已有候选环境通过，未安装依赖。首轮 fence 探针误将空表 DELETE 无操作当成写入，修正为实际行写入后通过；这是探针假设修正，未发现产品失败。

本审查未改源码、测试或 Git 状态，未安装、运行完整 suite 或外部写入；只写本报告。

## 最终本地证据补核

- 直接重算五个产品路径及原字节聚合 SHA256 `d716290cb8293ae4f34e152f37cda0186e65eb2bfe13c2fbbf8d85bca6eb24db`，与初核同一产品候选。最终非 editable wheel SHA256 `493e735b49e3741430211d07999754f058cd3968c3083a6015334c0aed82d3b2`；575 产品在当前源码／构建快照／wheel／安装目录逐字相同，两 RECORD 的 583／588 行与全部283冻结文件独立校验通过。公开摘要86项原引用的实际 bytes／SHA 均直接核对一致。
- 原安装执行参数、monitor 回执及完整 stdout 一致：七 suite 收集85项、78通过／7平台跳过、48.96秒，monitor为50.538秒。此次是最终含 OverflowError 转换的安装包；保留之前误用旧包和 collection 失败，不把 Linux 跳过计作 Windows 成功。本审查只读原件，没有重跑安装或 suite。
- 固定原 v4 State 源码直接与基线 Git blob 逐字核对；实际升级脚本／命令和回执记录旧实例重开、旧已开 writer 拒绝 v5，已开 reader 仍可读。只读实际 SQLite，核原 v4 备份的 schema／原记忆行及 SHA、v5 的21表／63 fence，升级前记忆没有被重写；完整离线备份的原5条记忆修订在 before-restore／snapshot 一致，恢复后的原行仍保持。CLI 原输出及参数覆盖时区归一、默认 list、catalog、省略继承、明确清除、恢复原到期时间和检索排除；18条执行记录包含 Git 和旧／新 CLI。
- 直接核原 HTTP 响应及最终 SQLite：同一浏览器记录只有新建／清除／恢复／删除四次 mutation，均200、修订1–4连续；1和3保留同一期限，2无期限，删除后四条历史正文／来源均清空。legacy 原记录、CLI 过期历史和演示 Git 状态保持，beta记忆行0。
- 首次 basic 脚本的 `renewed memory visible by default` 失败原输出保留。原清除请求已成功返回修订2；随后 fresh snapshot 显示原修订2及无限期，同记录 continuation 只等待／读取后继续恢复与删除，没有重复 save。结论仅为这条有中途确认的实际旅程通过，不称首脚本无人干预通过。
- 原浏览器脚本及结果覆盖实际 loopback HTTP 的目录／检索逆序、切项目后旧历史、切 tab 后旧目录三场景；没有把 DOM 替身结果冒称真实 HTTP 验收。独立目视1440／960／390目录与更正表单六截图，状态／判定时刻／期限及操作可读，无 document 横溢；原测量及 console 0 error／0 warning相符。原 monitor 按 stop 文件收尾；补核时原 web service 进程及浏览器 daemon 不在，loopback端口已关闭。
- 原 `ergora-structure-review` 模板调用实际 succeeded／approve，34.835秒。直接从 prompt 提取10个完整文件，215,539B及各 SHA 与 packet index 相同；原 prompt 与实际 stdin 逐字相等，3份继承资源全文均在其中，input digest相符。prompt SHA256 `59c8e13c39be76e08dab3faeb7aecd5510395b61598fa1fa043f6febf2a6cbe9`，原结果 SHA256 `700c49fdba308eab776980f85097f5c379a21d121aa488a666f20c7c26f87d29`。这是用户授权的 Codex 回退自身模板审查，不称异后端或独立验收；其当时尚待页面／独立审查的范围没有被改写。

## 待补核

自己的固定发布／精确远端及必要 CI、Windows 原生仍待；C3 CI 只解除前置依赖，不代表本候选 CI。ReMe 外部部署、不能撤销的旧 reader／缓存、未来有效保证均不在已验范围。F10b 正式 Task 冻结、F9d 完整旅程、真实 GPU／训练／质量／性能分别保留，不由本地审查通过关闭。
