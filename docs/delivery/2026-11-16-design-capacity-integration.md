# WA5-S1／M6-V2b：联合安装与开发分支发布

2026-11-16。联合新安装及32项定向验证完成，尚未普通推送或取得新候选自己的CI结果。旧公开 `04af234` 的CI不转授本片。所有设计执行、schema3训练效果和可信人类批准继续关闭。

## 接纳的准确输入

|输入|身份与验收范围|
|---|---|
|共同产品基线|`c540939d3b3f38f3851b0de965c9cd0f969eea77`；原公开后继文档提交为04af234。|
|WA5-S1|`b28cd316b63bb788c502a026f1ec971d5572242a`；[交付](2026-11-16-design-policy-registration.md)与[新fresh完整独审](2026-11-16-design-policy-registration-r4-review.md)。原F1/P2已独立关闭，原-I回执probe与17项新安装通过，Codex原模板78.706秒approve。|
|M6-V2b|`919a38064f9e692ced4e6c2c8e70b0bd4b936a8e`；[交付](2026-11-16-training-cycle-v2-capacity.md)与[源码独审](2026-11-16-training-cycle-v2-capacity-source-review.md)。41项与两场N32新安装通过，Codex原模板65.349秒approve。仅closed容量子片，不是完整M1c。|
|普通合入|容量片merge `329237958c0c93dbf121388a0e04d9b05ccf7283`，S1 merge及准确联合产品 `6cec589f404b17f4828a70807d5e33d89fad3fa0`；无冲突。两原候选的19个source／test文件在联合树逐字节相同，没有merge-resolution产品改动。|
|相邻文档|首批13文件含独审明确提交 `eb14df13a101681043fc8e94084ee3e409518b5b`；双语后端研究F1修正并同片复核后明确4文件提交 `fc632ad`。这些文档不改变联合产品身份，也不声明preset／planner／automatic已实现。|

只读固定树为 `.ergora/worktrees/design-capacity-integration-r1`。新证据根 `.ergora/checks/design-capacity-integration/` 保存全部tracked输入、完整diff、原候选同一映射、包／安装、选择和运行原件；这些是本机忽略文件，未上传GitHub，换机器须另行保留需要的原件。未改用户现有运行home、原作者树、旧冻结、原参考／锁或其他owner服务。

## 新非editable联合安装

`package-r1/`：新wheel SHA256 `20068f1aea74b5168f672e6c59b888fead77efc4b4085a7c2852cab2f99e2199`。core／SDK各669 runtime文件，source／wheel／site-packages完整字节与执行位相同；三训练owner从实际site-packages导入，core无SDK、SDK1.34.0。原283参考与两环境依赖检查通过。相对c540939仅新增原S1 schema，六个原owner文件变化，无删除；打包按原规则排除包内AGENTS，不把670源输入与669 runtime混计。

在copied-tests cwd使用绝对SDK解释器、`-I -B`并移除PYTHONPATH，选择原S1五入口展开17节点，再选SDK controller两次完整input／Memo gate、最终编码不延原窗口、完整Failure树以及实际SDK lifecycle接线。原fixture时限、选择来源与完整argv保存在 `installed-selection.json`。**32 passed／135.20秒**，JUnit32／0 failure／0 error／0 skip，runner136.369秒；709个采样自有进程身份终核均absent。运行后2,095份tracked输入与core／SDK各669runtime文件字节和执行位再次核同一，固定树仍clean；见 `post-check-identity.json`。各原片未变化的广泛矩阵／完整N32不重复转授为联合运行。

## 发布与下一步

联合定向完成后显式提交本片交付／PLAN与交接状态，普通推送开发分支，核远端完整OID及该提交自己的适用CI；不自动合main，不强推，不删远端。真实Temporal／server追加Failure包装、完整M1c-V/R、10MB晚期reader、CPU两候选、S2实现与F/J/G另按原计划验收，不能从本片安装或supplied-text审查推出完成。
