# F5.0：原单参数history的完整性

日期：2026-11-05。状态：完成；SDK红绿反例、独立发行/代表回归、新独立审查、精确da80e777提交及正常推送/实时远端、两OS CI41906996732与同片最终复核全部通过，无未解决finding。基线`f2b93d4daba751a707af43755f2dd30fc19c74f8`，生产基线`77b334c`；历史逐步状态保留各自时间与范围，最终裁定见[审查终结](2026-11-05-original-payload-boundaries-review.md#精确-ci-与同片最终终结)。

## 问题与契约

正式workflow的原输入、approve/cancel信号及dev_submit上下文按既有合同均为单个JSON参数。Temporal SDK1.34.0的单类型hint可能忽略第二个payload；只核解码后的单对象不能证明原输入完整。内存反例实际观察：两个job payload被旧`_Inspection.jobs`接受，两个spec payload通过`VerifiedSpecClient.decode_spec`，两个signal payload被`find_signal_event`匹配。记录在私有`.ergora/checks/f5-evidence-foundations/`，未访问既有服务、业务任务、fence、租约或Git ref。

原job/计划有界读取已有原始payload数量检查。本片在剩余两个现有所有者复用相同不变量：spec/job数量不为1时明确拒绝；单参数信号的恢复匹配跳过非单payload事件，继续查找真正相等的原信号。合法单参数、原codec、JSON身份、原run/memo验证及未知操作恢复语义保持。

## 实施与验收范围

- 生产仅`reference_task_runtime.py`和`reference_task_reconciliation.py`，不增加文件、依赖、基类或通用解析器，不改冻结reference。每个守卫直接保护真实SDK会丢失额外输入的边界。
- 新反例使用真实SDK payload/codec，覆盖缺失/单个/额外原spec、两类信号和job。外部证据/显式对账增加多参数history反例，确认无fence/lease发布。两旧spec夹具改为合法的单占位payload，保留原有错误/中断场景。
- 先在旧生产源码跑新反例记录失败，再修补；按影响选择原runtime/submission/批准/取消/外部对账代表回归和架构检查；完整矩阵交精确CI。发行使用非editable包、资源/283冻结身份及精确双OS CI，不继承77b334c通过为新源码通过。
- 新的独立审查检查单参数守卫所有权、错误与未知语义、必要测试和维护成本。修正/记录/正常提交推送及精确CI终结后关闭本片。

当前：真实SDK红绿反例和包内14项已通过，15项代表路径回归通过，新的独立本地审查通过、无findings；下一提交/精确CI收口。F5.1索引可基于已本地验收/独立审查的da80e77按独立契约实施；本片精确CI终结前不推下一生产候选，结果和发行身份分别记账。本片不启动旧专用服务或重放原模型/操作。

## 本地验证进度

真实SDK/codec的12项新增反例在原生产代码上实测8失败/4通过（pytest 1.84秒、外层4.75秒），不是根据实现推断的失败；缺payload还实际触发SDK AttributeError，多payload会漏掉额外参数。补三个原始数量边界后12项全部通过（pytest0.80秒、外层1.53秒）。合法单参数的codec解码及两类信号在异常事件之后继续匹配，仍使用原SHA身份。

生产增量仅两个文件共三个守卫；两个旧夹具各把空列表改为一个spec占位，新增真实codec反例与外部读/写对账反例。新wheel SHA256为`191cef78663ce545084c8373aa2b6ab35cba4e3b2b70db47efacc199b965788b`，350源码/wheel/两独立noneditable安装及283冻结一致，基础Web安装没有Temporal SDK；包内真实SDK12项和外部只读/显式对账两个多参数反例共14项通过（pytest17.03秒、外层19.97秒）。没有启动原服务或新模型/浏览器旅程；本片不据此声称通用性能提升。

本地原240项矩阵在74个个案已通过时，经独立审查按风险收窄，按精确PID/完整argv给本轮pytest发送SIGINT；exit2/421.69秒和原日志全部保留，不能记为240通过。已完成个案涵盖runtime/submission合法、严格JSON、竞争/未知与CLI/API路径及批准合法/中断代表，未重跑这些个案；新补15项仅涵盖其余信号精确恢复、取消正常/缺marker未知、两模板外部证据/对账和静态架构边界。完整矩阵仍由本片精确两OS CI承接，不删除或放宽任何测试/CI。独立审查另核SDK的PayloadCodec保持单payload数量合同，与新增守卫相容。

补充代表源回归实际15 passed（pytest71.02秒、外层71.92秒），原批准信号精确恢复、取消正常/缺marker未知、两模板FileAdapter完整核验与精确lease对账、8项静态架构边界全部通过，原240中已完成runtime/submission未重复运行。以上分别保留命令/原日志，未把中止套件合并成一次完整通过。代码/包本地验证完成，独立本地审查通过、无findings；精确提交/CI终结待完成。

提交前8文档257个本地链接/锚点和27条README parser命令通过，差异格式通过。精确提交/正常推送、双OS全量CI与同片终结尚待交付；无额外本地扩大测试。

精确提交`da80e777f9ccb1caf6de54f66d245669d953b8d2`已正常RSA推送且实时远端一致；350 Git archive逐项等于191cef包。[精确CI41906996732](https://github.com/626619403/Ergora/actions/runs/41906996732)进行中；同片审查者正续核提交/最终静态/正常推送与远端，未记完整交付完成。

最终收口：精确CI41906996732中Ubuntu126844222428及Windows126844222800的全部必要步骤成功；原独立审查者核官方HTML的完整提交、selectedJobId、实际log URL与来源字节摘要后已通过，无本片剩余验收。F5.0完成；F5.1及后续仍独立验收，不沿用本片包或CI为后片结果。
