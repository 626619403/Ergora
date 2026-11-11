# F7a：逐项目指定工单读取

基线 `0252dec5c41be1c1f6f533d86d8f32d30d178ce3`；[计划与验收](../plans/2026-11-11-project-trackers.md)。当前source定向、非editable安装包、实际绑定页面／CLI／HTTP与真实自身模板验收已完成；新的完整独立审查已通过，自己的精确提交／CI出口待。前片C6d自己的CI与精确交付单独登记，不转授本片。

已只读检查项目有效配置／绑定、CLI／HTTP入口、普通诊断、参考提交／Input与旧Symphony。首片采用普通项目read-only来源：描述驱动选择GitHub／GitLab，单个工单number／iid读取，不要求正式参考运行时。后续任务映射、窄提交准入、显式回写与observe分页分片验收。

实现选择与实际验证结果在完成后逐项追加；生产检查只用确定性本地HTTP，不使用真实账号凭据或写操作。工单正文是上下文，当前不触发任务、不提升权限、不改变批准。

## 已实现与定向验证

新`issue_backends`在本族ABC／局部映射下拥有GitHub／GitLab的路径、认证头与原生字段映射；`bindings`委托连接校验、`tools`消费无网络诊断、`issues.show`固定项目配置并供CLI／HTTP直接调用。tracker层默认manual，旧缺字段项目保持manual；描述驱动表单消费同一目录，没有新增JS或CI。

GET保留完整API base／namespace／路由number或iid和另列native ID；只接受普通issue。1MiB完整响应上限、20秒socket I/O超时（非全调用wall-time）、拒绝redirect和明显截断，凭据由外部变量读取且控制字符错误不回显值。注册项目读取前核kind／namespace；注册没有API host，不虚称跨host正式claim已支持。公开观察只作上下文，不写新表、创建任务或调用模型；需要持久化时由操作者显式保存JSON。

首轮source检查为新功能／目录／旧配置25项，9.12秒通过；随后增加响应截断／类型、注册归属和观察时间，并执行新功能、components／project_configuration、registrations、task_creation和composition_tasks，共159项／104.30秒通过。此结果来自`PYTHONPATH=src`与既有独立环境的依赖，尚不算本片新wheel验收；不覆盖旧完整运行或真实外部服务。

[官方调研](../research/2026-11-11-project-trackers.md)另核API／SDK：首片窄GET不新增PyGithub/python-gitlab；两家ETag条件GET只代表读取，未提供issue写CAS。调研的43次公开无凭据GET、404／超时保留，未运行Ergora适配器，不能冒作本片产品接入验收。

## 安装包与绑定页面出口

第一份r1新wheel包含447文件，其中ergora包442文件，SHA256为`0f872c9bde47dfbcd32c25c1661e60ded763ec3467e7ed53a677ff7cce2c504e`。源码／wheel／独立非editable安装逐件字节一致，两份RECORD与283冻结原件核验通过；安装后的新功能、目录和项目有效配置28项／23.29秒通过，独立driver wall24.998秒，`reference verify`通过。

实际页面所有者核对发现tracker新字段缺少title，可能出现无名称输入；已在同一描述中增加GitHub四项／GitLab三项显示名称，不改JS。另用同一schema的`not pattern \s`拒绝正则`$`原可放过的尾换行，在既有binding matrix加四个可达边界；修正文档对integer上限的泛化描述。后补字节不在原模型输入。第二份r2重新构建并独立安装，wheel SHA256为`7d937646df9e7151e5f6c6fa7b830fe0c39380f9885406182bbc2f74ab62bda7`；447／442文件、源码／安装逐字、两RECORD和283冻结继续通过。安装28项实际pytest12.79秒（driver14.39秒）、reference verify通过；未机械重跑无关159项。

真实现有工具绑定页验证manual默认、GitHub字段／默认值、保存修订2和重开读回；随后改GitLab嵌套namespace，保存修订3、整页刷新后重开值保持。读取原HTTP及安装CLI时来源、完整正文与原生ID一致，观察时间另列。两次绑定保存是仅有的应用写请求；其他绑定、既有各工作记录保持、task目录不存在。共57个原应用HTTP请求，56×200及私有driver误路由1×404原样保留；本地tracker3次GET，无认证、外部写或模型。已核全部HTTP字节／摘要、两修订、来源响应摘要与CLI同源；浏览器console零消息。

验收不是一次全过：首次默认Chrome不存在，复用已有Chromium；初次selector未含图标，改用新snapshot ref。第一段driver在GitHub保存后误用不存在的项目GET，9.54秒／3检查后失败；改现有dashboard读回后原修订继续，第二段15.16秒／5检查，在reload后ref从eN变成f1eN被私有正则误拒。保留两次失败和全部命令，修正私有ref解析从原修订3继续，5.33秒／5检查通过，没有重复保存或运行Agent。首次离线audit把结构化skills列表误当`[]`，改为核与原值相同，无产品改动或浏览器重跑。13检查按各段事实结算，自动化wall-time不推导产品加速。显式关闭命名浏览器，7个已采样进程无live；两自有HTTP服务退出／端口关闭，状态变化符合两次绑定保存，不虚称整个目录字节未变。[包与页面公开投影](evidence/2026-11-11-project-issues-acceptance.json)保留身份、失败和限制，完整原件不进入发行包。

## 真实自身模板与独立评审

沿实际bundled structure-review派生证据修订1.0.90，保留原提示与Skill，只追加candidate-evidence、精确引用及材料限额；按用户授权显式Codex回退，Claude既有失败原因保持，不称双后端成功。run `8c8263c0fd2d4317ac2ae55d50c782be` 为228.07秒、succeeded／exit0／approve；19份完整附件（含tracked delta）聚合253,279B。完整新源码／schema／测试／F7文档及所选相邻所有者均在原索引，其他文档为diff-only；未读链接内容及省略的运行原件不自动转授批准。

离线核manifest→prepared／actual input→stdin／protocol→准入→未变模板→scope→原结果全链；五固定scope均列出、连续UTF-8从0至null读取，后续base64 spot-read在同offset重试，零失败。4个已采样进程无live。后端自报input979,742（cached881,920已含）、output5,497、reasoning3,202单列，不重复相加或推导账单／模型质量。[自身审查投影](evidence/2026-11-11-project-issues-self-review.json)保留完整原判词、精确索引／scope与用量；后补字段／空白边界、公开证据及后续状态文档不在原输入，由新的fresh-context完整两轴评审覆盖。[新的完整独立两轴评审](2026-11-11-project-trackers-review.md)已通过：27文件与后补措辞、r2包／原模型／浏览器／research原件均直接终核，Spec／Standards开放0／0；C6d状态和CI步数两历史P3及附件计数措辞已修正关闭。独立子轴另实际运行source工单14项／11.25秒通过。自身原判词不转授后补字节，本地出口完成，未提前结算自己的精确提交／CI。

## 本地出口

完整最终候选的新独立评审已覆盖实现、测试、配置与文档／两公开投影；没有新增依赖、CI或JS。前片CI已终态，本片接着最终有限静态／冻结、普通提交／推送，并核同一候选的Git对象／官方Ref和必要CI。最终有限静态核28文件／328本地文件链接／6已加载秘密值，issue0，未检查全部锚点／Mermaid或外链。完整F7、F8–F10及G1仍按计划推进，不把只读来源称为已处理工单。

## 普通提交与自己的精确交付

最终28文件ready manifest SHA256 `03dd8868ee582d281fc557311b5ab348d45b6d0e507b93830957b78e454c6d39`，独立核冻结／live／模式／Git路径及后补状态通过；最终静态28／328／6值issue0。普通提交并推送`9f010079126f374c01272ecf2f0ec85284e4e2cc`，单父0252dec；Git工作区当时clean。自己的精确Git／远端Ref及CI正在同片终核，原模型／平台／后补范围保持，不借前片CI。

第一次匿名REST查询返回403限流，280B原body保留，未得到CI状态，不称CI失败或通过。随后一次官方公开Actions页面HTTP200（320,338B、SHA256 `bf4f868515b99237faa2697cc55df33e7c2feb6f14a367abfcb00be0f2701b0c`）的原embedded JSON将完整9f01007、分支与[本片CI42974715330](https://github.com/626619403/Ergora/actions/runs/42974715330)精确关联，状态为in_progress；等待自己的终态，继续本地设计且不推下一候选。


同片精确交付现已终结：原评审独立核28Git对象／ready及既有SSH远端同完整9f01007；官方run42974715330页面及其直接各取一次的两job HTML均为终态成功，Linux三／Windows四必要步骤success，原件／精确关联／步数离线核验通过，见[原评审终核](2026-11-11-project-trackers-review.md#同片精确交付终核2026-11-11)。第二匿名REST仍403，两个403与早期In progress均保留；本结论基于官方HTML，不冒称成功终态REST或全日志下载。F7b live源码没有代替原候选包身份。
