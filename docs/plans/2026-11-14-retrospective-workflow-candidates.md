# F10c2b2：有来源的工作流复盘候选

日期：2026-11-14；固定基线 `0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`。[F10总计划](2026-11-14-evaluated-improvement.md)／[当前进度](../PLAN.md)。前片已普通发布及独立固定发布审查，自己的CI43555532175在途；本片可独立开发，发布等待前片CI终核。

## 合同与所有权

`retrospective prepare-workflow`显式选完整目标manifest／SHA、用户指定的新根版本，以及独立的作者manifest／叶。冻结目标根与全部递归子模板／Agent／资源、原grant和完整选中handoff。模型读取完整UTF-8文件与执行位；合计至多1 MiB，二进制、NUL或容量超限明确拒绝。原完整输入owner仍核提示容量。`--target-digest`是原manifest的文件／执行位身份；冻结的baseline.digest另以canonical{manifest_digest,directories}绑定全部原排序目录，包括空目录，不是仅根JSON摘要。

第一片只允许根description、已声明资源内容和额外依赖边。根ID／schema／权限／limits／输入输出、全部节点引用／职能／权限／输入／审查要求、原有依赖边及资源id／kind／path保持；新版本由用户指定。资源操作沿原resource_changes，仅作用于根声明的文本文件或Skill目录，不改子定义；候选write也须为无NUL的UTF-8完整文本。原图、端口、完整祖先与预算门禁保持。任意图重写／权限迁移仍由原手工修订入口处理。

独立标准`workflow-retrospective` preset：只读Codex作者→Claude审查，原显式叶调用与完整前驱；原后端可选，前27个preset不改。提案含完整根definition、原resource_changes、假设／适用范围／验证计划、精确引用／负结果／未知成本，null有效。审查approve仅为提案审阅。

`check-workflow`离线核完整输入／最多8 MiB原结果及引用，在自动清理的私有scratch中调用原restore_manifest、DefinitionLibrary.revise的preview／明确accepted_candidate，再以原grant编译核预算。检查会写临时scratch，但不构造State、不读实时源、不写用户资料库。冻结根视图须与恢复原根相同。来源认证／质量评价／采用授权均为false。

`export-workflow INPUT RESULT DEST --result-sha256 SHA --candidate-digest SHA`重核原结果及原preview身份，经原library.export与no-replace发布器导出完整根bundle。stdout回执含input／result／baseline／原manifest_digest与目录／candidate／原preview；不采用、不更新项目／旧run。正式`composition check/import`持有依赖／版本冲突门禁，原manifest／项目选择持有使用与回退。图准入不等于效果，可信具体workload另验。

## 实施与验收

- [x] 原manifest／prepare_input／restore／revise／export与资源操作的实际调用者盘点，固定范围。
- [x] 原retrospectives实现prepare/check/export；完整UTF-8读取在Skill与工作流两个真实消费者间共享，不改Task运输或数据库。
- [x] 新标准preset／CLI／文档；前27个preset与283参考文件保持。
- [x] 原suite：完整递归基线／源消失／null／资源修订／导出／原导入／旧manifest保持；误绑SHA／引用／越权／换子引用／移除依赖／跨子资源、原grant容量、无覆盖与清理。
- [x] 最终非editable包／两RECORD／283、相关原suite；实际CLI正候选→原导入／选择与拒绝；真实作者→审查完整祖先／前驱／stdin；自身原结构模板。
- [ ] 新fresh-context独立两轴及修复终核；普通推送当前分支／完整Ref／自己的必要CI／原reviewer终核。

每步写[交付](../delivery/2026-11-14-retrospective-workflow-candidates.md)。F10d、F9d、G1新安装／升级／回退及记忆Agent新patch样式清理后接；真实GPU／业务B3、完整Forge、原生Windows模型运行保留原未验范围。

最终r2安装204通过／6平台跳过／250.00秒；实际native-r3 11CLI、最终r2真实双后端null／approve与自身结构35.499秒approve，修复代码已获原reviewer核包／八探针通过，最终全部证据／独立终核与发布自己的CI仍待。旧r1与调用器fixture失败原件保留。

原fresh-context最终本地两轴及411全部原引用已终核approve／开放0／0，R1／R2关闭；普通推送／固定发布补核／本片自己的CI仍待。

已普通发布`54fcd0b188f1f1dc46229dfe504f5dddb9c4aaea`，28固定blob／完整远端Ref相同；固定411／发布后415原引用，原四回执单独追加。原reviewer固定发布补核与本片自己的必要CI待，不合main。
