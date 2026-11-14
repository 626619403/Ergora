# F10c2a：来源绑定的 Skill 复盘候选

日期：2026-11-14；基线`396e9d175cbbcd120dac29b45a2665002984a53b`。[F10总计划](2026-11-14-evaluated-improvement.md)。F10c1已普通发布，自己的CI及原独立终核通过；本片另验自己的发布与CI。每次恢复核本页、交付、PLAN和Git。

## 范围与接缝

先闭合一种可实际导入、评价和回退的候选：标准 Agent Skills 目录。记忆和流程建议保留为后续显式原owner修订；本片不宣称已实现它们的候选采用。原 Skill 库持有版本／活动head，原 handoff 持有来源字节，原组合持有完整输入／权限，原 Agent 持有模型调用与失败；原 evaluation／skills 继续持有评价／采用。本片新增准备和只读检查，不建候选数据库、队列、评分器或采用者。

新增可复用`retrospective` preset：只读候选作者使用Codex，来源／可泛化性审查者默认Claude Code；各叶可沿原backend override替换。是普通嵌套Workflow／Agent定义，沿原串行依赖表达作者→审查。仍为proposal-leaves：本片不声称自动执行所有端口，运行依次使用现有独立叶调用，后继需显式带完整前驱原结果。

新`retrospectives.py`拥有这个顶层用例的两项接口：CLI prepare与check是本片实际消费者；页面不是已实现复用。它聚合原owner的业务合同而不是转发一条调用，放在handoff字节核验或通用Agent运行器内会反向耦合Skill／候选语义。局部快照／摘要算法留在此owner，不创建通用插件层。

## 合同

`retrospective prepare PROJECT PACKET --selection FILE --packet-sha256 SHA --skill NAME --digest DIGEST --head-revision REV --objective FILE --manifest DIR --instance PATH --directory NEW --max-prompt-bytes LIMIT`：先核完整原包／选中资料与项目相同，显式冻结当前活动Skill的精确name／digest／head revision及完整UTF-8文件／执行位。目标必须已存在；初始导入只是baseline。目标元数据／完整文件原字节与原digest必须一致。读取期间源变化、当前head冲突、正文过大或非UTF-8／NUL明确拒绝，原组合完整容量门禁仍为权威；不截断、不修改head、不发模型请求。原`prepare_input_from_manifest`负责最终原叶输入发布，正文含完整证据、完整基线、目标和同一份响应schema。用户可选自有的只读叶与后端，不把模板固定为后端实现。

`retrospective check INPUT RESULT [--result-sha256 SHA]`：离线读取一次有界结构化原Agent结果，原input inspector核冻结任务。返回来源／基线／原input／结果内容身份与有效提案；不认证模型作者或评价质量。响应保留原`summary`／`artifacts.response`合同，response中是标准JSON。响应需精确绑定冻结资料SHA、基线digest／head revision及Skill name；观察引用只能来自完整选中job／name／artifact SHA。保留负结果、原未知成本与不确定性；无改进依据时candidate为null，不能强造改进。

完整基线原文件总量限1 MiB，原结果单独限8 MiB；后者容纳完整文件在原response字符串中的必要JSON转义，不借handoff manifest上限代替此用例容量。各叶完整prompt仍按原门禁单独核验，离线check通过不保证完整checked JSON适合后继prompt。prepare／check面向proposal-producing叶，preset文字审查叶沿原composition接完整checked JSON。

候选是完整标准Skill文件内容与执行位，使用原便携路径和原Skill目录内容身份；只读核文件集／SHA／元数据。候选不持有或改写可信评价器、活动权限或执行／批准权威。资料引用在原选中集合核对；这只能证明声明的来源身份与材料关系，不能证明文本结论为真。评价计划是待执行建议，`check`不将其视为评分。模型结果不直接触及目录、导入、活动head或项目配置。

只读检查无需实时源或State，输入和原结果在源包／Skill后续删除或head变化后仍可核；重新prepare必须重新核当前head。导入候选、同一可信suite评价／明确采用与回退另在F10c3接原接口，已存run继续原输入不自动重发。

## 验收与进度

- [x] 固定原owner／真实消费者、Skill先行范围、完整资料与后续采用边界。
- [x] 新普通preset、Skill指导与单一JSON Schema；沿原输入准备／离线check接入，模型仍由原独立运行接口持有。
- [x] 原suite增量保护来源或引用误绑、current head冲突、完整祖先／Skill文件、拒绝越界路径与不泄出部分候选；不测试固定文案／默认值。
- [x] 最终r4非editable包586／两RECORD594／599／283，八suite291通过／7平台跳过；实际八CLI及真实Codex作者→原结果→Claude审查通过，核完整原输入／stdin／reply。所有harness／调用终态，访问范围内无本片cwd进程；收尾范围见原件。
- [x] 原自身结构模板完整同input授权Codex回退approve，Claude超时保留；新fresh-context独立最终本地两轴approve／开放0／0，236原引用已核，R1–R4关闭。交付／PLAN已更新。
- [ ] 上片CI及原补核通过；已普通发布a60a8f6／28blob／完整Ref同一，原fixed发布补核两轴approve／开放0／0，本片自己的CI43551217945八job／30必要步骤已全部成功，原独立CI终核approve／开放0／0、原CI补核待，不合main。

每项结果写[交付](../delivery/2026-11-14-retrospective-skill-candidates.md)。F10c2b记忆／流程候选、F10c3原评价／明确采用回退、F10d页面、F9d／G1、真实B3与完整Forge分别保留。

后继优先完成F10c3a标准Skill的原评价／采用／回退，先闭合一条可日常使用的完整出口；之后继续F10c2b记忆／流程与F10d。范围保留，顺序理由见[F10总计划](2026-11-14-evaluated-improvement.md#f10c后续顺序调整)。
