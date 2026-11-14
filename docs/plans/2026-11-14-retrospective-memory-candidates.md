# F10c2b1：有来源的记忆复盘候选

日期：2026-11-14；基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`。[F10总计划](2026-11-14-evaluated-improvement.md)／[当前进度](../PLAN.md)。先补记忆，流程候选另立片；前片Skill导出自己的CI因Windows总20分钟上限取消；具体发布依赖调整见[CI预算修正](2026-11-14-windows-ci-budget.md)，原取消保留，新候选仍需自己的完整必要CI。

## 合同与所有权

新增 `retrospective prepare-memory`，显式选择新建记忆或更正某个精确当前有效修订。先核原handoff整包与完整选中证据，再从原`memory.catalog`观察完整canonical记录、来源、有效期、修订和时刻；新建基线明确为null。冻结项目／完整基线身份和原proposal_schema，经原`prepare_input_from_manifest`交付，完整祖先资源与容量规则保持。

新增独立的标准`memory-retrospective` preset：只读Codex作者→Claude审查者。沿原显式叶调用与完整前驱交付，可换原支持的后端；不改已有Skill preset及其身份，也不把静态图依赖称为自动端口执行。

模型只提出完整正文、假设、适用范围和验证计划，可以返回null。正文遵循原记忆的100000字符上限。模型不能选择来源URI、修订、有效期、权限或评价器：写入来源由冻结整包SHA及选择SHA派生，更正仍引用原ID／修订。负结果、未知成本和引用限制保持。

`check-memory`离线检查完整原输入和最多8 MiB的单次原结果读取，核基线／选中证据／逐条引用及完整候选身份；不访问State／实时源。它只证明声明的关联，不证明来源作者、真实效果、当前仍有效或采用批准。共享有界结果／普通Agent封套／证据引用算法留在原retrospectives module；目标专属检查仍本地，不建泛化插件框架。

`export-memory INPUT RESULT DEST --result-sha256 SHA --candidate-digest SHA`明确导出完整`memory.txt`和`receipt.json`到新目录，保留UTF-8原字节。复用原具体no-replace发布器，拒绝既有目标或冻结input内部，失败清理私有staging。导出不保存记忆；receipt含原项目、基线、input／result／candidate、固定来源和原save的ID／expected_revision。命令返回完整receipt，供用户核对后使用原`memory save`。

明确保存仍由原`memory.save`持有，原revision冲突／删除语义、`history/restore`与ReMe投影不变。省略expiry参数以保留原有效期；生成器不续期，过期后的更正仍不进入召回。新记忆沿原默认无有效期行为，用户可在原save中另行指定。保存回复不确定先查原catalog／history，不自动重试新建。记忆没有Skill可信suite的采用合同，不把模型审查称为同等的质量评价。

## 实施与验收

- [x] 核原memory／handoff／retrospective／完整输入／发布器的实际消费者，固定完整baseline与本片合同。
- [x] 原owner上的prepare/check/export及独立标准preset已实现；原Skill入口行为保持，不改数据库schema／依赖／调度器。
- [x] 开发原suite28通过／27.88秒，涵盖必要回归：完整更正与新建／null／来源与expiry不由模型控制；当前陈旧／删除／到期基线；误绑SHA／基线／引用；导出无覆盖／输入污染。复用原记忆有效期与修订／恢复检查，不复制其状态机。
- [x] 最终r2非editable包594／两RECORD602／607／283、安装188通过／6平台跳过／215.43秒；实际16CLI合成新建／更正→原save／冲突拒绝／恢复，完整U+FEFF／换行保持。真实r1模型Codex→Claude null／approve、r2离线check逐字同一，调用身份分别记账；全部祖先／前驱／stdin已核。
- [x] 原自身结构模板41.793秒approve；新的fresh-context最终本地两轴approve／开放0／0，R1已修并独立闭合，259原引用／原件／收尾已核。
- [x] 原前片取消终态与原因补核、单独新reviewer核Windows预算修正后共同普通发布；本片新完整SHA自己的全部必要CI与原reviewer补核，不改写前片历史／不合main。

逐步结果写[交付](../delivery/2026-11-14-retrospective-memory-candidates.md)。流程候选／原修订采用、F10d页面、F9d／G1及真实业务／GPU／完整Forge保留原范围。

已共同普通发布`0f01fdd9736fc456cf1cdcc8d77e64dac916e8a0`，30固定blob／完整远端Ref同一。记忆固定259／发布后263引用及CI预算固定23／发布后27分别保持；原固定发布补核和新SHA自己的全部必要CI待，不覆盖旧c4aa7ac取消历史。

原记忆与CI预算reviewer已分别固定发布补核approve／开放0／0；新候选自己的CI43555532175在途，所有必要检查与原终核待，旧取消身份保持。

## 固定差异样式检查的范围补正

原reviewer固定发布补核发现两份新Agent instructions第1行各有一处行尾空格，完整`git diff --check c4aa7ac 0f01fdd`实际exit2。此前tracked-only检查未覆盖当时untracked的新文件，不能称完整30blob静态检查通过；原local-static-r1回执保留。它不影响行为，两轴仍approve／开放0／0。已发布Agent1.0.0及包／模型／引用身份保持；G1通过新的不可变patch版本清理两处空白，验升级后关闭。后续发布先暂存全部已审文件，再执行`git diff --cached --check`覆盖新增文件。补正原件单列full-fixed-diff-style-r1.json，不改固定259／发布后263列表。

新SHA0f01fdd自己的CI43555532175已由官方最终run／八job原HTML记录为Success：30必要步骤全部成功，包含完整Windows应用、PowerShell5.1安装升级与上传；另列68条CI原引用，不改原固定／发布后引用。原reviewer终态补核待；旧c4aa7ac取消历史保持。

原记忆reviewer已完成固定0f01fdd自己的CI终核：8job／30必要步骤全部成功，两轴approve／开放0／0，固定259／发布后263及另68CI引用全核。原594产品／两RECORD／283重绑固定Git，前片取消与两空白exit2仍保留；该片精确交付完成，G1新patch样式清理另验。
