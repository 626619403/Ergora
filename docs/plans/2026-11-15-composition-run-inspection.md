# Q2.3b1：精确读取原组合运行

日期：2026-11-15。基线`f1fc4501b8f15060eee7502caf6531c8f44a1b5f`，643产品／283参考。承接[Q2.3b总合同](2026-11-15-source-review-reports.md)，先完善原run读取，不在本片实现跨分支报告。

## 行为和真实消费者

在原`agent_runs`增加`inspect_run`，由薄`composition inspect-run PROJECT RUN_ID`消费，后继报告也调用该owner。按项目及精确run ID读取原记录，沿控制目录的`runs/<id>.input`、`runs/<id>.protocol/prompt.txt`、`runs/<id>/result.json`核原件，不依赖最近100条、当前后端／认证或历史metadata的绝对文件指针。已有`output`共享原精确记录读取，stdout／stderr及native-history行为保持。

返回原记录、完整冻结input／composition／prompt、原完整结构化result及各自可核状态／错误。input须与原record的digest、input_request和prompt身份相同；protocol prompt独立核原record的SHA／字节数，输入可核时再逐字交叉核冻结prompt，并以input_compared区分；result须匹配原result SHA并以原JSON reader解析。缺件、解析超出递归限制、未记录result身份、超出显式容量或身份不符不截断／不读任意替代路径，保留原状态和仍可核的其它原件。

本片的result校验是完整字节摘要及JSON读取，**不使用今天的后端／schema重新认证历史调用**；后继来源审查报告再用已有可信reviewer结果schema解释response／decision。原生schema文件不是新的可信远端schema入口。run记录不是签名来源认证，也不是正式批准。

`protocol/prompt.txt`是所有原后端共同保留的请求prompt。实际传输不能统一假定为stdin：Codex／Claude用stdin，DeepSeek用原request文件且stdin为空，command可封装JSON。此读取不增加后端名分派、不重新构造命令、不冒称通用传输认证；实际native日志仍归原后端及output。Q2.3a两次实际Codex调用的stdin逐字证据保持其原范围。

## 可验收步骤

|步骤|完成条件|状态|
|---|---|---|
|B1 合同|实际存储、query、prompt传输差异和原结果协议已核；固定计划和基线|已完成|
|B2 实现|原owner完整观察＋CLI；共享精确查询，不新增State/schema/后端或恢复动作|已实现原owner／薄CLI及手册；原output复用精确记录读取|
|B3 接缝|超过100条仍精确读、跨项目拒绝、搬迁后读、完整长回复不截断；输入／原prompt／结果漂移或缺件明确可见，读不改run也不调用模型|r1源码32通过，审查两P2实证后扩展原接缝；红路径3失败保持，修后源码34通过／4.00秒。无新test文件／CI job|
|B4 安装／实用|新wheel／非editable身份、283保持；沿Q2.3a两条原模型run实际CLI读取并核原件不改，无模型重发|r1四suite72／23＋MCP补35保持；r2新wheel／643三方逐字／283保持，原两suite安装69通过／26.50秒，八实际CLI含原run完整读、容量／迁移及隔离副本两finding复现，原件不改／重发0|
|B5 审查／发布|自身原结构模板、新fresh-context两轴、固定发布／Ref和自己的CI／原终核|r1自身及新独立两轴request-changes保持；r2自身45.809秒approve，同reviewer两轴approve／R1和R2关闭／开放0／0。本地验收完成，发布／自己的CI待；前片自己的CI终核前不推后继产品|

显式`--max-result-bytes`默认8,388,608B，只限制这一完整结果的读入，不改变原保存内容。超限返回明确不可核而非摘要；操作者可提高正整数容量后读取。完整input沿原10MB／500文件检查，其prompt沿原1MB合同。本片不改变模型生成预算或增加任意provider限制。

每步更新[交付](../delivery/2026-11-15-composition-run-inspection.md)及PLAN。之后b2／b3据完整原件汇总明确分支，不自动补跑、投票、批准或写平台。
