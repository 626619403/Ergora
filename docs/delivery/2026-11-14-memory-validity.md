# F10a：记忆有效期交付

日期：2026-11-14；固定基线`f47cd50fcce600fba92f64aff73982012f6e31c9`。[合同](../plans/2026-11-14-memory-validity.md)／[证据摘要](evidence/2026-11-14-memory-validity.json)。最终r1安装、实际CLI／HTTP／页面、自身模板与收尾已验；新的独立两轴最终本地approve，开放0／0。普通发布及自己的CI待。

沿原memory／State／backup／CLI／HTTP／页面owner实现；省略有效期的更正保留原期限，null明确清除，恢复原过期修订不会续期。schema v5只更新原writer fence，不重写记录或增加表。需先停止旧进程再升级，不能撤销旧reader已取的资料。

## 实施与现有调用

`memory.py`新增可见catalog、时间校验及有效性判定，records／sync／search沿原owner消费；ReMe返回后重新读本地，丢弃在途变化的revision。v5不增表，仅更新21表原fence。CLI增加catalog、显式时间／清除选项，HTTP按字段是否存在转交；页面显式读目录、有效期表单、历史原期限及本地read序号，原dashboard保留有效快照。文档已补升级停止旧进程与旧reader不可撤销界限。

两项新增记忆回归覆盖时区归一、到期边界／更正继承／明确清除／历史恢复及ReMe在途到期／删除／更正；原迁移suite扩展独立v4夹具、旧writer和两journal模式，原backup完整往返夹具带过期字段，原HTTP旅程补省略与null。没有新增CI分组或依赖。

## 当前检查与保留失败

源码六suite78通过／1平台跳过，14.22秒；JS语法与diff空白检查通过。该次早于最终时间归一的OverflowError错误转换，最终非editable安装回归另验。首次误用上一片已安装旧包执行新测试，结果7失败／19夹具错误，不能作为本片验收；修正到源码后首轮发现一处字典闭括号笔误，collection失败，修正后上述源码回归通过。原日志及范围分别保留，不重标为成功。

F10b正式Task上下文选择、F9d完整旅程和真实B3另验，不借本片关闭。

## 安装与CLI阶段

最终候选r1非editable wheel SHA256 `493e735b49e3741430211d07999754f058cd3968c3083a6015334c0aed82d3b2`，575产品与快照／wheel／安装逐字一致；两RECORD583／588、283冻结通过。安装七suite78通过／7平台跳过，48.96秒（原monitor50.538秒）；Windows原生尚待本片自己的CI，Linux跳过不冒称Windows成功。

实际安装CLI与固定C3原State完成v4→v5：原记忆行保持、原v4备份schema与记忆行保持，旧实例重开拒绝v5、旧已开writer触发原fence；已开reader仍能读，符合停止旧进程的界限。实际保存／list／catalog／更正省略／明确清除／历史恢复／检索、完整离线backup／verify／原home恢复均通过；原过期历史保持、演示Git状态保持。18条记录含Git、旧／新CLI，不能全称18次memory命令。

## 实际页面、自身模板与收尾

最终安装包实际页面创建过期记录、确认UTC与文本安全、预填期限、更正清空为无限期、从原历史恢复成过期、删除／全部历史清空与只读目录、检索排除和空查询读取有效列表均通过。完整原HTTP记录仅四次mutation（新建／更正／恢复／删除），均200，同一记录修订1–4连续，没有重复提交。原CLI过期历史与legacy记忆保持，beta目录为空，演示Git状态不变。

首次basic脚本在明确清除已成功后，抢在dashboard刷新完成前断言默认卡片内容而失败；fresh snapshot确认原修订2已正确显示，调整私有等待后只读续接同一记录并完成原历史／删除／检索。原失败与continuation分别保留，不称首脚本无人干预通过。

真实loopback响应延后验证三类读生命周期：较早全部目录不覆盖后发检索；切换项目后旧历史不弹出modal；切tab后旧catalog不影响新页。1440／960／390目录和更正表单均无document横溢，六截图已实际目视。最终浏览器console零error／warning，浏览器daemon已停、loopback端口关闭，原process monitor按stop文件收尾web，未留后台服务。

原`ergora-structure-review`模板、用户授权Codex回退，完整10文件215,539B及全部祖先资源实际进入同一prompt／stdin；34.835秒approve。原结果SHA256 `700c49fdba308eab776980f85097f5c379a21d121aa488a666f20c7c26f87d29`，prompt SHA256 `59c8e13c39be76e08dab3faeb7aecd5510395b61598fa1fa043f6febf2a6cbe9`。这是工具自身模板调用，独立审查由新fresh-context两轴另验，不称异后端成功。

## 界限与后续

ReMe真实本地HTTP原suite验证协议与projection，三类在途变化由同owner故障注入验证，不声称外部ReMe部署。默认dashboard与catalog是观察快照，已打开旧reader或旧缓存不可撤销；无计时刷新或未来仍有效保证。本片未增加正式Task字段、未修改原运行归档，未做GPU／训练／质量／性能或真实业务采用。Windows原生能力由本片自己的CI另验。

新的[需求](2026-11-14-memory-validity-spec-review.md)／[结构](2026-11-14-memory-validity-structure-review.md)最终本地核对通过、开放0／0；两轴均直接核86原引用、最终包、原行／实际旅程／模板及收尾。普通发布、完整Ref和自己的CI另验。C3自己的CI已独立关闭，仅解除推下一片的依赖，不借给本片。
