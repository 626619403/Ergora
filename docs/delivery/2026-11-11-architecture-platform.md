# C6d：架构导航与平台说明

基线 `c1f31fcfa38ac25085e287c507377be422786026`；[分片计划](../plans/2026-11-11-architecture-platform.md)。本片20文件完整独立两轴及本地出口通过，无生产／测试／打包／CI变更；最终冻结与自己的精确交付仍待，C6d及整个AC6/F6未提前关闭。

## 已核与下一步

已读原架构、合同身份说明、Windows说明，以及后端／版本Input／worker／执行材料的相关源码。第一方包只读AST预盘点为53个Python模块、203条本地导入边，包含函数内导入，拓扑无环；console为18个第一方JS，不含vendor。该结果只覆盖静态导入，不推断动态加载、子进程或运行语义；原清单保留源字节摘要。

原架构归档和当前导航／格式／平台说明、实际自身模板、最终20文件独立复核均已完成。复用未变源码的439文件／两RECORD／283冻结非editable包身份，不为文档重建同代码或重跑已过产品旅程。前片自己的CI第四样本已终态成功，四样本／作者Ref精确原件经原评审者离线终核通过，C6b/c精确交付终结；本片本地出口通过，接着冻结、普通提交／推送并核自己的CI与远端身份。

## P1–P3 文档候选

原架构59,761B完整字节归档到[同目录历史](../architecture/current-history-2026-11-11.md)，SHA256 `3231898e9ab6b60e453ad04b4c444876d7f5abdfb867eacbf93a7cc287baf920`，没有插入banner或改相对链接。[源码投影](evidence/2026-11-11-architecture-source-inventory.json)保留原AST回执身份及当前53源文件／18第一方JS的字节摘要；原回执head为f957489，其src树与本片基线相同，不把旧head标签改写成新验收。

新[架构导航](../architecture/current.md)按当前所有者重组，含主要调用、六阶段／审查、正式操作时序、前端与数据归属五图，保留Agent后端接入锚点。明确三个图关系、专长数据包与实际ABC／版本继承、完整祖先读取、逐定义父子修订、局部后端映射、v6材料及原ID恢复；保留差异化生命周期、冻结分发和直接兼容别名的理由。它不是新增调度器或重构源码。

[格式说明](../architecture/contracts-and-identities.md)补Workflow／preview v1/v2、manifest／input／MCP scope v1、用户task-definition v1/v2、正式信封v2–v6、材料v1/v2及handoff各自责任。[Windows](../WINDOWS.md)与[训练](../TRAINING.md)区分原生静态定义／普通调用和Linux task-MCP／完整执行；两份冻结参考手册保持，导航链接可达。README与总计划的旧版本／“未开始”检查点同步到本片实际范围，原失败CI与未验项保持。静态／真实自身模板与完整独立审查通过；精确交付待完成。

## P4 静态与真实自身模板

第一份静态样本核14份公开文件、328个本地文件链接；第二份核完整20文件／413链接，JSON与whitespace及6个已加载秘密值／私有home路径均issue0。没有渲染Mermaid或检查全部锚点。`src / tests / scripts / .github / pyproject`对本片基线无差异，原包／冻结验收只复用于未变源码，不称本片重新运行。状态记账后作最终有限检查与冻结。

实际沿原bundled structure-review模板，在独立控制目录派生证据修订1.0.89，保留原指令／Skill，仅追加candidate-evidence、精确引用和材料限额；按用户既有授权显式选择Codex，Claude历史失败及回退理由保持。run `873f78512f944ad19d018980ff95b1ab` 为208.25秒、succeeded／exit0／approve，意见限定本次附件而非整仓或owner批准。17完整附件文件共393,375B，其中原tracked delta完整、当前／历史架构与版本／Windows／本片文档及所选七个实现模块／pyproject正文完整；其他tracked文档仅提供变更，不声称其未变正文或链接源码／手册全部已读。后续记账与新独立报告不在原附件，原模型措辞和结果不回写。

离线核manifest→prepared／actual input→stdin／protocol→准入→不变模板资产→scope→原结果全链；五份scope实际list完整，连续UTF-8从0读至null，base64同offset重试保留，零失败。四个已采样进程无live，不推导全部短命进程。后端自报input3,503,516（cached3,265,664已含）、output3,887、reasoning1,144单列，不相加推导账单／模型质量。[自身审查公开投影](evidence/2026-11-11-architecture-self-review.json)保留原判词、精确附件与读取／用量身份，省略完整私有原生流和配置／输入路径。

新的fresh-context[独立评审](2026-11-11-architecture-platform-review.md)已核归档直接等于基线原blob、两个src树相同、53Python／203边／静态无环和18第一方JS及公开源SHA，另逐件核283冻结原字节。最终20路径含安装说明增量的完整Spec／Standards开放0／0、P3已关闭；实际模型全链与投影也已直接终核。本地出口通过，未授予尚待的精确提交／CI／远端出口。

独立评审提出阶段命名P3：新图中首阶段曾写inspect，原冻结workflow和日常手册实际为inventory。已将两处新图标记改成inventory／盘点，原归档与原模型输入／判词保持；这项后续修正由独立同片复核，不声称原模型审过修正后的候选，也不为纯标签更正重放模型或产品。

作者另核本地main=cab3a724，未包含当前preset树、CLI对象与当前分支不同；该本地事实不冒称另核远端main。README／日常与Windows原示例clone main，未直接给出本文当前功能所在分支，容易让接收者安装到不同源码。已明确选择`refactor/architecture-foundations`开发分支，Windows空环境ZIP同分支，入门旅程回链；重现验收应固定完整提交，不能只比0.2.0版本号。没有合main、改安装器或重跑产品；此更正晚于原模型快照，完整独立同片复核已过，不计为原模型批准范围。
