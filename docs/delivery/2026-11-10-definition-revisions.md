# AC5 C3a：从完整原包派生新修订

固定基线 `0a495aaaa489f838c009820b7cd978bbed0c5e37`，分支 `refactor/architecture-foundations`。[实施计划](../plans/2026-11-10-definition-revisions.md)说明整组修改的发布/中断/并发语义；[AC5](../plans/2026-11-09-composition-console.md)保留 C3–C6 的完整范围。

基线现状：CLI 已能完整 export/check/import，Web 只有库查询、preset 导入和静态预览；尚无从固定原版本直接派生新正文的共同入口。DefinitionLibrary 原导入已拥有不可变索引、完整对象、当前准入和原子索引发布，本片复用这些所有者。

C3a 先接 JSON 正文、基准摘要与 check/publish。完整资源和目录由原 export 保留，不编辑文件内容。Agent/Workflow 用同一原库合同；原库 factory 各自保留 backend/role 或完整组合校验。无效候选不得发布，原版本/活动快照不变。资源追加、JSON/YAML/表单会话及完整链旅程分别在 C3b–d，不提前声称图形编辑完成。

当前状态：原包派生接口、两类 CLI/HTTP 入口和手册已实现；源码/非 editable wheel 回归与实际 CLI/HTTP 旅程通过。独立复核已关闭DR-S1，修后实际自身模板175.68秒approve/完整明文读取通过；完整26文件独立终核通过；已普通推送34afcc2，本候选自己的CI42752730652双OS七必要步骤及独立明确HTTPS同SHA均通过，精确交付终结。C2 的 CI42747066139 在 2026-11-10 03:28:04 UTC 已终态 Cancelled：Linux20m超时，其他六必要步骤成功；原超时保留，不计通过。明确 HTTPS 再核同 0a495aa 完整 SHA。前片CI等待终态条件已满足，本片不沿用其验收。

## 实现与所有者

- `definition_bundles.DefinitionLibrary.revise` 在 State 内暂存完整历史 export，固定 base digest，只重写当前种类的标准 JSON；默认检查，显式发布才沿原 import/index/file_lock。返回候选与 base/published，不返回清理后的临时路径。
- `agent_definitions.revise` / `workflow_definitions.revise` 保留各自原库 factory：前者拥有当前职能/后端准入，后者在当前准入下编译完整递归图；不复制目录摘要、权限或发布算法。
- `cli` 两处命令共用局部参数声明；`web` 四条路由复用原本机请求限制与异常处理，只转交原用例。没有新 schema、数据库、包依赖、CI 或调度器；283冻结文件不改。
- 三个原测试文件补充完整附件/空目录保留、固定基准、无发布检查、重复发布、祖先权限及当前准入、CLI/HTTP 候选一致性；沿原库既有测试检查版本冲突/中断/导出，不另建镜像测试框架。
- [Agent手册](../AGENT_DEFINITIONS.md#从固定原包派生新版本)和[工作流手册](../WORKFLOW_DEFINITIONS.md#修订分享与恢复)列出标准 JSON、check/publish、摘要和逐依赖发布语义；没有页面/YAML/资源变更支持声明。

## R1 验证

源码三组定义测试 **142 passed / 1 skipped / 12.38秒**，包含历史后端准入变化后的四条新拒绝路径；此前 `-k revision` 的6项只能代表筛选范围。

R1 非 editable wheel SHA256 `2f01f15bc422d948912c3097fb9ee7a8992100be8c355d0451abbb6ba837b73e`；**435** 源码/wheel/安装/RECORD文件身份相同，**283** 冻结文件与本片基线相同。安装包运行定义、完整 manifest、Web、架构、reference 七组原回归 **180 passed / 1 skipped / 74.63秒**；平台跳过保持原适用范围。源码结果不替代安装后的实际 CLI。

实际安装包隔离 `python -I -m ergora` 与 owned loopback HTTP 共 **44次调用**：两类 JSON revise 的 CLI/HTTP check 同候选摘要、check 不发布、明确发布/相同重试、原摘要错误拒绝、原定义不变均通过；两类包的未声明二进制文件、Skill 二进制附件与空目录保持。错误后端、子权限越父、缺依赖、错依赖摘要在 check/publish 都拒绝且索引不变；同版本不同内容拒绝。依次发布 Agent→子工作流→新根，原三包字节/执行位及完整旧 manifest 保持，导出到新 State 再导入身份相同。没有项目、Agent运行或正式任务产生；HTTP进程由本次 PID/start identity 确认并清理。该旅程不等同 C3d 的完整页面联合提权或正式任务采用。

原始命令、回执、非 editable 环境、完整文件身份和HTTP清理记录保留在本片私有验收目录；后续公开投影不包含个人目录、凭据或原生缓存。无需浏览器或GPU验收，本片没有页面、执行或训练实现变化。

## 首轮进入审查的门禁安排

更新实际证据后交新的 fresh-context reviewer 独立核 Spec/Standards、真实复用、必要分支、冗余测试与成本；并从安装包的内置结构审查模板显式运行本片完整固定证据。各原始意见和失败分别保留，确认问题后最小修正/受影响回归/同片复核。完成后普通提交推送，再核本候选自己的必要 CI 和明确 HTTPS 身份；C3b–d、C4–C6仍未完成。

## 首轮实际自身模板与 DR-S1

首轮真实模板 run `14c61cb4d2dd4358bf71d88c4ee67eba`，证据修订1.0.1，**231.87秒、succeeded、request-changes**。完整14份受保护源/测试/配置候选323011字节、14连续UTF8页，四份祖先指令/Skill读取、原manifest/input/实际prompt/原结果均一致，无base64或失败读取。原结果SHA256 `398666b2ebee86d47945e1bb4bdfd4b288cc5b5dd67d72e6ddfafa1764cd84d6`。用户授权Codex回退沿用，未改内置默认后端；模型没有执行仓库代码，不构成正式批准或模型错误独立性证明。

模型指出 **DR-S1（P2）**：合法包正文为0444/0555时，完整export保留只读模式，`revise`直接write_text使普通POSIX用户check/publish都PermissionError。新独立审查者在未改R1安装包、普通用户下复现两类0444正文导入/读取/导出均成功、四条修订路径均红；0644对照四条绿，原索引/对象不变。此前独立首审0finding仅代表当时范围，原意见和失败不删除。

先在原三个相关案例强化只读正文及执行位保持，R1原包 **3 failed / 58 deselected / 2.63秒**。最小修正只对暂存标准正文添加owner-write，保留其余模式位、全部其他文件和原库；没有捕获PermissionError回退、改共享所有者或重写原包。受影响源码 **3 passed / 58 deselected / 3.53秒**。R2重新构建，安装回归、真实只读包CLI/HTTP、同片独立复核和第二次实际模板待验；修后结果不覆盖R1原红。

## R2 修后验证

R2 wheel SHA256 `9e4c99abf8206ee0dcf69658f32b6b9436b5c895d8808bd4d4bcd471fcea4f7d`；435源码/wheel/非editable安装/RECORD身份及283冻结身份保持。原七组安装回归 **180 passed / 1 skipped / 74.08秒**。实际44调用旅程 **8.02秒**：此次 Agent 原正文以0555导入，子工作流及根正文以0444导入，CLI/HTTP check/publish/重试、基准错误/越权/错误依赖/当前准入拒绝、完整附件/空目录、原包与旧manifest、独立State导出再导入均通过；标准正文执行位保持。原R1无只读输入的旅程不冒称覆盖此场景，原三红和独立四红分别保留。owned HTTP进程与端口已清理。DR-S1最终关闭、第二轮模板完整读取及最终交付继续待同片独立复核。

同片独立复核已关闭DR-S1：两类定义×0444/0555×check/publish八条实际成功，原包完整模式/文件身份、执行位、check索引和临时目录清理均保持；重新核R2 435/283身份及44原回执。[独立报告](2026-11-10-definition-revisions-review.md)保留首审、原红与修后结论，不复写历史。

## 第二轮模板与公开证据

第二轮实际模板使用证据修订1.0.2，原库移除后从固定manifest准备与运行；14份完整源/测试/配置、343725字节候选、15连续UTF8页、四份祖先指令/Skill、原manifest/input/实际prompt及原结果逐项匹配。运行succeeded/approve，无base64或失败读取；精确run/秒数/原结果SHA见[运行身份](evidence/2026-11-10-definition-revisions-self-review-r2-identity.json)。完整字节交付不证明模型推理质量，模型未执行仓库代码，不替代独立审查、正式批准或本候选CI。

公开八份JSON投影：[R2包与冻结身份](evidence/2026-11-10-definition-revisions-package-r2.json)、[R2只读包真实旅程](evidence/2026-11-10-definition-revisions-journey-r2.json)、首轮[身份](evidence/2026-11-10-definition-revisions-self-review-r1-identity.json)／[request-changes原意见投影](evidence/2026-11-10-definition-revisions-self-review-r1-result.json)／[完整读取审计](evidence/2026-11-10-definition-revisions-self-review-r1-reads.json)，以及第二轮[approve原意见投影](evidence/2026-11-10-definition-revisions-self-review-r2-result.json)／[完整读取审计](evidence/2026-11-10-definition-revisions-self-review-r2-reads.json)。原native结果SHA与格式化公开JSON文件SHA分别记录；个人目录已清理，原回执/模式/进程身份保留在私有验收原件。

最终完整文件清单、静态链接/手册命令、新独立提交前终核，以及普通提交后的本候选必要CI/明确HTTPS身份待验。C2原取消记录及独立CI时长审计仅为原状态续记，不使本片继承旧CI或扩大C3a实现范围。


## 提交前终核

新独立审查者已完成完整26文件两轴终核，DR-S1关闭、开放finding 0；两轮原stream/注册run/manifest/input/完整材料与八份公开投影逐项核对通过，R2受保护14源身份未漂移。第二轮run `6bdde5be958d41f2a88d2491b1081c6a`，175.68秒succeeded/approve，原结果SHA256 `9e2b4914705b1fe7ff4017e9d120ff230c16b7d33114e97f2fc2f4991eabce92`。静态10文档/128链接/98手册CLI parser命令通过，原静态两红保留且修后已核。

提交范围为5生产、3现有测试、10文档、8公开JSON；没有新页面、schema、依赖或CI改动。前片C2原Cancelled保留，本片普通提交推送及其自己的必要CI/明确HTTPS仍待验，不能提前标完整精确交付。后续C3b按原计划继续。


已普通提交推送 `34afcc2cec5a38655cfc93513173d67bbc433c02`，唯一父0a495aa，精确26Git对象与受审清单/435包身份/283冻结保持，提交后工作树clean。首推连接关闭原件保留，同一候选有界重试成功；没有改认证/代理配置或强推。独立已核完整26对象与包/冻结身份，自己的CI与明确HTTPS仍待核，不借推送成功宣称门禁通过。接续[C3b](../plans/2026-11-10-definition-editor.md)工作树不参与本片34afcc2精确身份验收。

## 精确交付终结

最新第三份官方采样为 `34afcc2cec5a38655cfc93513173d67bbc433c02` 的 Portability run `42752730652`，双OS终态Success、七必要步骤全部success。新独立于2026-11-10 05:13:45 UTC逐项核五原响应、精确候选/分支/工作流、完整两job及步骤原结论，并复核自己的明确HTTPS原件，通过终结门禁。原EOF、两份pending和本片R1原红分别保留；本结论只属C3a，不覆盖C3b工作树或整个AC5。详细核验见[同片共享报告](2026-11-10-definition-revisions-review.md)。
