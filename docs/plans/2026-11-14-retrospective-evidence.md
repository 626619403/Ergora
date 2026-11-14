# F10c1：复盘前的完整证据选择

日期：2026-11-14；基线`f1cfcddd4d0e58b657b810b1f7dc98d070d255d9`。[F10总计划](2026-11-14-evaluated-improvement.md)。F10b已普通发布、原独立固定发布两轴approve／开放0／0，自己的CI43545573942八job／30必要步骤及原结构轴终核通过；上一片终态条件已满足。

## 先复用的事实

原`tasks.evidence_index`／`task handoff`已经绑定原run、连续history、job／receipt／artifact、candidate与原outcome。原`handoff.verify`可离线核标准ZIP／JSON及原字节，失败／取消的完整材料仍可交接，但返回值只含核包摘要，没有资料选择与完整正文入口。重新扫描runtime或让模型自行读任意路径会绕开这些身份，因此先沿原handoff owner提供选择。

`memory.save`／history／ReMe、`skill_assets.import_bundle`／diff／head、`evaluation`及`skills.adopt`／rollback、`research`与GEPA仍各自持有原权威。候选使用已有Agent／Workflow JSON、Agent Skills目录及记忆正文／source格式；不增加图语言、记忆库、候选数据库、评分器或自动采用者。

## 本片合同

新增离线`ergora handoff read PACKET [--sha256 EXPECTED] [--selection FILE]`。不初始化State、不访问服务、不提取ZIP或运行其中代码。省略selection时返回原完整index，供调用方先查job／artifact身份；selection是最多32项的JSON数组，每项仅`job_id`与`name`，明确选择原receipt中的产物。

重复blob alias按每个选择的正文字节分别计入原1MiB必要上限，在读取／decode前拒绝，避免最终检查之前的正文放大。原全包核验继续先完成，读取正文与核验必须使用同一次有界读入的原包，不能先验包再重开路径。输出每件完整UTF-8正文、原artifact／job／receipt身份、完整原index及其SHA、整包／manifest SHA；不截断、不自动摘要、不同job同名产物不混淆。非文本、NUL、未知来源、重复选择或总量超限明确拒绝。复用原1MiB限额约束最终规范JSON，保留原packet／blob限制；较大的资料应重新显式选择，原始完整包不改写。

输出为版本1普通JSON `ergora-handoff-selection`，`sha256`绑定其余输出的原规范JSON；这是内容身份，不是新的执行／采用状态。保留原失败、未知成本、原outcome、`execution_success: null`和`origin_authenticated: false`。外部期望SHA只核包身份，不变成来源签名、质量证明或采用批准。

原`handoff`拥有字节核验与正文读取；共享一次有界读入的内部实现，不复制ZIP／路径／receipt校验。`verify`原返回形状保持。CLI是新公开读接口的当前消费者；下一片复盘输入可直接使用这份输出，不预建通用插件。

## 可验收步骤

- [x] 核原handoff／任务证据与评价／采用owner，固定本合同与接续。
- [x] 在原handoff实现一次核验后的完整选择，接离线CLI；不新增服务／表／迁移／依赖。
- [x] 在原handoff suite回归原核验，并检查不同job同名、完整非ASCII正文、失败／未知成本、选择大小及坏源不泄出部分正文；原离线CLI不创建State。
- [x] 最终r2非editable包577／两RECORD585／590／283身份，安装六suite131通过／6平台跳过／13.93秒；实际八CLI原包读回／坏源拒绝／原完整叶输入及收尾，不把合成包当真实来源认证。
- [x] 原自身结构模板r1确认alias成本finding，最小修复后r2 approve／36.836秒；新fresh-context独立最终本地两轴approve／开放0／0，88原引用已核。测试exact-count改上限仅定向另验1通过／1.20秒，保留原整suite／自身输入身份。
- [x] 已普通发布396e9d1、15blob／完整Ref同一；原固定发布补核及自己的CI43547736558八job／30必要步骤和原独立CI终核approve／开放0／0，不合main。

## 后续F10c与F10d

F10c2再增加有来源的复盘模板／候选合同：沿原readonly Agent调用，保留完整资料与原输入，产生记忆／Skill／流程建议，指出基线、适用范围、负结果、成本和不确定性。候选不能改可信评价器、权限或活动head。模型调用／重试／恢复继续原Agent和Task owner，不另建调度器；原评价与明确采用／回退继续原入口。F10c3完成候选失败／评价／采用／回退的实际旅程；F10d再接受约束的资料选择及候选页面。它们未因本片只读产物入口而完成。

每步结果写入[交付记录](../delivery/2026-11-14-retrospective-evidence.md)，保留原失败与未验平台。真实B3、完整Forge、F9d／G1及P2／P3分别保留。
