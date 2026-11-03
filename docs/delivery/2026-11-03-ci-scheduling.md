# V3：过时 CI 运行取消

2026-11-03。依据[测试成本计划](../plans/2026-11-03-verification-efficiency.md)及[独立审计](2026-11-03-verification-redundancy-review.md)。V1已交付，V2定向与独立源码审查通过且独立提交`4a6d3d52dbb42dd6fc9328b49596498f812b112a`（未单独触发CI，现已随V3共同推送）。V3以该提交为基线，仅修改本工作流。

## 已核事实与最小选择

当前Portability同时监听分支push、pull_request和手动事件，没有concurrency。只读读取公开的当前分支Actions首结果页，保存原HTML及SHA：`.ergora/checks/verification-ci-scheduling/actions-before.html/json`，观察到25项运行，全部为pushed；此范围不是仓库所有历史，也没有证明实际push/PR重复的频率或浪费量。因此本轮保留触发职责，不因配置同时允许两种事件就删除分支或PR检查。

最小改动只在既有`.github/workflows/portability.yml`增加workflow级concurrency及cancel-in-progress。组按workflow、event_name以及PR号（PR事件）或完整ref（push/手动事件）区分；同类事件同一分支/PR的旧候选可以取消，push、PR合并结果与手动事件不互相取消。不同PR号与不同ref值按GitHub的组名语义隔离；官方组名比较不区分大小写，因此仅大小写不同的分支会共组，不宣称服务提供严格区分大小写的锁。配置遵循已实际读取的[GitHub工作流并发文档](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency)，来源与SHA保留于`github-concurrency-doc.json/html`。

不改测试命令、矩阵、超时、依赖、安装与冻结身份门禁；不增加定时任务、外部服务或重复一套CI。PR合并树与分支HEAD仍有不同验收价值。最新候选的Windows和Ubuntu必需检查均须完成。

## 验收边界

核YAML结构、最小diff及各事件组的实际表达式；保留原矩阵/步骤/触发身份。新独立审查者核事件隔离和取消范围；推送精确候选后核两OS完整CI及远端SHA。若没有自然重叠的在途候选，明确未进行真实取消演练，不为演练额外触发一套即将废弃的完整回归，也不宣称测得runner分钟收益。

实现、本地结构、精确两OS CI及独立最终复核均通过，V3完成；实施基线为4a6d3d5；V2与V3保留各自审查及提交，共同最终候选仅执行一次完整两OS矩阵，并分别核文件身份。后续继续F3.4b2明确终态外部对账。

提案已在独立证据目录用既有PyYAML BaseLoader解析：去掉唯一concurrency键后，其他配置逐字段完全相等；原YAML SHA为`6624db6c6eaa188db8cc96e4487c1d0f61afab59b96930ed792c55fcd6fdb920`，提案SHA为`4d45c728e1f164aeeaabe080b00e5e4c58a19acb35ae4871d0364944647cf0a5`。8个上下文例验证同分支/PR同事件共组、不同事件/PR/ref隔离及GitHub大小写语义，见`proposal-validation.json`和`proposed-portability.yml`。这是本地结构/文档语义检查；未冒充GitHub表达式引擎或真实取消演练，提案时实际工作流尚未修改；随后实施身份见下文。

## 已实现与检查

实际`.github/workflows/portability.yml`已采用上述4行新增配置，SHA与已解析提案相同，为`4d45c728e1f164aeeaabe080b00e5e4c58a19acb35ae4871d0364944647cf0a5`。在实际文件上重新用既有PyYAML BaseLoader解析，删除唯一concurrency键后与Git基线完整相等：触发、权限、两OS/Python矩阵、20分钟超时、测试路径/durations、安装及冻结/PowerShell门禁保持。身份与原diff为`source-identity.json`、`tracked.diff`，V2七测试文件仍绑定b59a9e84…身份；未改生产、依赖或测试。

本地YAML结构/既有配置相等检查及`git diff --check`通过；8上下文例只验证文档规定的分组，不冒充GitHub表达式引擎。未触发真实重叠取消或新CI。下一步新的fresh-context审查，源码确认后独立提交并与V2共同推送；以最终完整40位提交核两OS门禁及两项文件身份，再分别最终复核收口。

[新的独立源码审查](2026-11-03-ci-scheduling-review.md)通过，无findings。审查者独立重读原workflow/diff、复算SHA并用既有PyYAML核配置保持，取得官方contexts/fallback允许范围和并发排序语义；本配置不提供严格按提交新旧排序的远端锁，最终必需步骤仍按实际候选SHA验收。源码门禁已满足，下一步独立提交V3后与V2共同推送；未将解析结果或旧CI当作新CI通过。

## 共同最终候选CI进行中

V2源码提交4a6d3d5及V3源码提交`d5588855be0d5995465caa7e0af4b1b80103cc11`已共同推送，实时远端同名工作分支与最终完整40位候选一致；V2七文件b59a9e84…及V3 workflow 4d45c728…在Git blob/工作树均保持，生产347文件未变。证据统一在`.ergora/checks/verification-ci-scheduling/combined-candidate.json`及`ci/`；只触发一套共同完整矩阵。[精确CI41612623462](https://github.com/626619403/Ergora/actions/runs/41612623462)正在执行，不提前报告两OS通过或节点完成。

## 精确共同CI与最终复核

`d5588855be0d5995465caa7e0af4b1b80103cc11`的官方CI`41612623462`已成功。Windows作业`125838059005`四必需步骤、Ubuntu作业`125838059675`三必需步骤（构建安装/包内reference身份/原生完整回归，Windows另含PowerShell 5.1安装升级）均success。统一`ci/fetch-ci.py`和`ci/verify-ci.py`退出0，完整原HTML/selection/sha日志URL与`ci-html-status.json`绑定该40位候选。

最终Windows页面的起止时间与此前212秒步骤观察一致。V2/V3测试/工作流身份仍为b59a9e84…/4d45c728…；本地原52d26d…包的347生产文件保持。两项各自同审查者最终CI/提交/实时远端复核均已通过；没有额外触发取消演练或另一套完整矩阵。

## V3最终收口

同一fresh-context审查者最终复核通过，无未解决findings：完整候选d558885…、V3最小单文件提交与workflow SHA、两OS七必需步骤及实时远端一致，原[审查报告](2026-11-03-ci-scheduling-review.md)已追加精确证据。本节点完成；共同候选只有一套完整矩阵，V2的独立最终复核另行记账。尚未进行真实重叠取消演练，不报告V3取消节省收益；GitHub大小写/排序语义维持原披露。下一功能仍为F3.4b2。
