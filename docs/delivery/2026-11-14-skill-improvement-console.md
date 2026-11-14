# F10d5 原 Skill 评价采用页面旅程交付

固定实施基线 `055b0c44d7bd2bb7c1375b82471ec7ca00c40605`；[具体合同](../plans/2026-11-14-skill-improvement-console.md)／[完整证据索引](evidence/2026-11-14-skill-improvement-console.json)／[独立审查](2026-11-14-skill-improvement-console-review.md)。最终r2本地流程验收完成，新的独立最终本地两轴approve／开放0／0、R1/R2关闭；普通发布／自己的CI分别待；前片自己的终态CI另核，不借其成功。

## 改动与原权威

产品仅改原 `skills.js`。版本／suite／run变化撤下旧比较与采用表单，diff／compare分别按当前选择代际读取。评价使用按控制目录／项目隔离的本窗口未决HTTP锁，跨标签／项目往返及页面内刷新保留；完整回复释放，未知回复由用户读取原记录后明确解除。浏览器重载丢弃临时界面锁，仍须先查原记录。

导入、注册、采用、回退与有限GEPA共用本页局部submissionForm，沿原ui.form提交锁显示完整请求／结果，提交后当前表单撤下按钮。异步结果只更新原存活view／form；明确提交陈旧但仍可见的modal时，局部说明关闭重开且不发请求。取得结果后由用户明确刷新，不自动关闭窗口、刷新后来页面或发迟到全局通知。重开表单是新的用户动作，原业务owner仍治理完整性。

未新增HTTP、评价器、持久账本或采用权威。完整资产归skill_assets，可信suite／完整评价／正确性／成本／validation及holdout归evaluation；skills.adopt重新compare并经原move_head核baseline／revision；rollback沿曾活动版本与理由。公开使用说明和架构已同步。

## 实际验证

|证据|身份与范围|
|---|---|
|基线复现|F10d4最终r3安装件的skills.js等于本片基线；6项／3样本／3.630秒实际复现旧采用表单、旧评价跨项目弹窗、旧导入关闭Help。原head1未变，进程端口收尾|
|r1安装／主旅程|603产品、两RECORD611／616、283冻结；原Web＋Skill两suite44通过／46.78秒。主旅程23项／10样本、三宽、原采用revision2→回退baseline3；只证明r1|
|r1 finding|自身原结构模板Codex59.162秒request-changes：R1跨view锁、R2刷新后仍可见form静默失效；另实证3项／两回包sample。两listener均取第二回包，两个distinct run由原HTTP27／28与DB证明，不能借sample声称两对象不同。独立确认后修复|
|最终r2包|wheel SHA256 `889f8b59eba6b4c7305d135869e6e170a5c82b36b31b1db5efec1cf8ffe465e8`；603产品／两RECORD611／616／283。源码、wheel和非editable安装逐字相同；75个原Python／测试文件r1／r2同一|
|最终原suite|安装原Web9通过／11.73秒；此前44项保持r1身份，不冒称在r2重跑|
|最终真实页面|主旅程23项／10样本，生命周期24项／15样本，负例／并发21项／21样本；共68项／46样本，97原HTTP、10真held、1夹具503；1440／960／390px均适配并目视核图|
|原CLI读回|原prepare/check/export三次、单独可信负例suite注册一次、最终读回／完整导出七次，共11操作。页面、HTTP、CLI与原owner完整对象同一；完整候选目录导出同一|
|自身原模板r2|真实Codex59.561秒approve，run `dfa7da6baa4b433c9d45842774bb860d`；9完整文件60,759B与完整继承资源均在原stdin，使用已授权回退。独立fresh-context另验|
|收尾|原来源包、完整baseline／candidate／input／result、原scorer及单独负例scorer保持；最终原head baseline revision9，9历史／10评价，另项目无版本／suite／run；服务线程、浏览器／服务PID与端口全部关闭|

主旅程从原复盘合成结果经原CLI完整导出，在页面导入、注册可信fixture suite、双方完整评价、比较、给理由明确采用，再原回退。后继并发场景再次追加原历史，最终revision9仍为原baseline。确定性提案和评分器只验证合同，不宣称真实模型提出改进或质量／性能收益。

边界实际覆盖选择失效、迟到diff／compare成功与错误、跨标签／项目的评价锁和阻止重复dispatch、503后原记录与明确解锁、迟到import成功／错误隔离Help、刷新使旧form失效的明确提示。负例覆盖真实原holdout退化／正确性失败／错suite／跨项目／失败scorer记录，以及并发head变化、比较后scorer变化、迟到adopt与rollback不污染新页面／窗口。没有宣称全错误排列。

## 保留的驱动／夹具失败

r1服务finally在uvicorn已关闭socket后读取getsockname报错；原HTTP已逐个保存，另只读cleanup-finish-r1原件／head3／进程端口核通过，不伪造原finally成功。r2浏览器首次填错端口连接失败，随后按before.json真实端口导航并完成独立旅程；该错误不属产品。首次负例fixture未在case input给split，产生保留的原failed run；原scorer不改，另登记有明确split的可信scorer／suite验证holdout和正确性负例。所有旧件、修正和身份分开。

## 待完成与限制

新的fresh-context独立reviewer已核最终649原引用、全部97原HTTP、68项／46样本、11原CLI／完整目录／DB／原件与收尾和真实自身模板，最终本地需求／维护性均approve，开放0／0、R1/R2关闭。八份独立证明与五个发布调用器另追加，662引用保留原649前缀；本片普通发布和自己的必要CI另验。有限GEPA只跑原安装回归，未新增GEPA页面提案全流程主张；未知回复的前端锁不推断run归属。原form防重入，不构成跨窗口／跨浏览器的执行去重协议。记忆／流程的原保存／import旅程、完整F10／F9d／G1及真实B3／原生Forge C2仍分别接续，不借本片关闭。
