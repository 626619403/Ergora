# G1c 独立需求与维护性审查

日期：2026-11-14。审查者：fresh-context `portable_usage_handoff_review`，未参与本片实现。先读原始审查要求、`AGENTS.md`、[当前计划](../PLAN.md)、[G1c合同](../plans/2026-11-14-portable-usage-handoff.md)和实际diff，再读作者交付叙述；按maintainable-project-delivery的独立审查要求，以及code-review两轴／codebase-design指导检查。只读源码和原件，仅写本报告，没有安装、模型调用、服务操作、测试／CI修改或Git写操作。

## 两轴结论

|方向|结论|范围|
|---|---|---|
|需求符合性|approve；开放finding 0|当前七份用户文档及G1c计划／交付、已实际保留并重新核对的安装／新项目／完整输入／自身模板证据|
|维护性|approve；开放finding 0|文档归属、既有owner与命令复用、角色及来源说明、资源继承／权限、恢复边界和证据表述|

在上述范围内没有实证finding。安装、状态、定义、任务准备、后端、训练和批准仍沿既有owner；没有加入第二套执行器、资源库、恢复算法或冗余测试。公开入口用链接串接完整手册，数据库迁移表按真实有序迁移展开。角色定义／Skill／组合的本仓库来源、研究借鉴与实际后端分别表述，没有把上游研究、安装或文本审查扩大成实际运行能力。

此结论只覆盖本地被审文档及已核原件；最终交付汇总、固定发布与相应CI事实须在产生后另核，不预批。G1b的发布／CI和另片G1d-CI的paths-ignore变化不属于本片默认审查范围。

## 固定身份与被审文件

产品与diff基线为完整提交`506cc576874e92bc922644a8dd9f244151b08e4b`。审查中邻片G1b发布后，实际HEAD为`6c7c45f79e499dde83d9880043342710a28d7809`；其新增内容是文档。初次完整tracked范围核对仅有README和docs，产品源码、安装器、依赖及测试未变，G1c拥有的变更也没有CI修改。随后另片G1d-CI在共享工作树加入`.github/workflows/portability.yml`改动及自己的计划／交付，明确排除在本结论之外。G1b及早先记忆补丁的文档状态更新不借作G1c验收。

以下是本次本地审查的完整文件字节身份；计划／交付后续仅状态记账的更新需另记录，不改写这次读取身份。

|文件|字节|SHA-256|
|---|---:|---|
|`README.md`|54660|`349e0bba3371b6492e481ef3d65f759994db1492d9e769df8b226c969d123347`|
|`docs/USAGE.md`|169181|`97d69b0bb629e7b31d90bb0913450bc6c34b833cdd7872e4f3624fdd8b3312af`|
|`docs/TRAINING.md`|55988|`4eab180a3d08999fe5767f6863f704608200f21c7ed616e53ce177598ed1d7cd`|
|`docs/WINDOWS.md`|15607|`f1c95d7cc239ec166fd27def1ce62739ffcc786206968fe6e1352c27302f6456`|
|`docs/TEMPLATE_WALKTHROUGHS.md`|16572|`7ef19f9080a02756d04ac965b5289d1e30c582ad1b9f46d9356755a706996b74`|
|`docs/architecture/current.md`|54779|`6c0739d31dfd3eddfff8ba47e2ccbc91e0d5dd6f6f1c512011af1ead20d873fe`|
|`docs/architecture/state-migrations.md`|8744|`95814c52fc0fcde251d8d0782dc78d35a2f420d6617672ea7212b09e1e5159a8`|
|`docs/plans/2026-11-14-portable-usage-handoff.md`|3164|`b3f19a8e7e5813cfb8fd02dddee032f6716fb1fbda39162be4d1f65104873880`|
|`docs/delivery/2026-11-14-portable-usage-handoff.md`|3113|`f8e7b960151eb65804d87a721d1790071a4deb12015d8a4af867071d491f20d7`|

邻近所有者实读包括`state / backups / projects / workflow_definitions / agent_definitions / definition_bundles / task_context / agent_backends`、原Linux／PowerShell安装器、`task-composition.js / tasks.js / web.py`、preset目录与对应完整角色／父Skill包、工程／组合研究及第三方许可说明。数据库v1至v5、21应用表／63 writer保护、仅数据库的自动快照、同平台原home完整恢复、原生页面prepare／预算／definition6及显式context／definition7均与现有实现相符。

## 独立核对与原件

原件根为私有`.ergora/checks/portable-usage-handoff/`；没有把机器绝对路径、认证配置或业务源码写入本报告。

|重新核对的事实|实际结果与限制|
|---|---|
|固定源码归档|重新执行只读`git archive`，SHA为`808e578e4222badab3378508d4d55360379801d4a03ed94a661c09dfe4d00eca`，与source-r1记录相同|
|默认Linux安装原件|读原安装driver／stdout／stderr／result；Python3.12.3、已有Python／Git与预备离线缓存，原安装耗时27.966694秒。重新逐字比较611安装产品与固定G1a wheel，核806条installed RECORD；不声称由空系统盘安装|
|新项目原件|读project-r1 driver、result和35条operations，逐一重新核全部stdout／stderr SHA及exit0；原21检查／35命令／22.218326秒。项目角色revision与独立路径、五preset根、两输入身份相符；没有模型run或正式注册／执行|
|五完整manifest|以该固定611安装件的只读`inspect_manifest`重核全部包／资源／引用和原记录digest；治理16、大变更19、训练9、quality20、诊断8实例|
|两完整叶输入|以同一安装件只读`inspect_input`重核；再直接读祖先定义比对资源、来源和prompt。quality叶有4祖先／7声明资源／7476B prompt；诊断叶有2祖先／5资源／7517B。全部祖先资料保留，各层权限不扩大|
|静态架构清单|独立AST遍历含函数内导入，重新得到73顶层Python／300去重本地边／28第一方JS、无环，所有记录文件SHA匹配；不包含reference／driver／vendor／动态装载或进程边|
|当前九文档链接|独立只读复核323条本地链接／标题fragment，无错误；fenced示例与外网URL不在该检查内。`git diff --check`通过|
|自身原模板|成功run `df7c40dff8fe4be7a0dc697af145a431`，32.893825秒、19文件／485552B、approve。按packet的字节长度和SHA从真实task中重构全部文件，原task／prompt／实际stdin相同；输入digest为`9c2704dbde1ad4614cd65679e9607b3cbbf470fe3e052f190b36a0cae8e10834`，结果SHA为`45a03cd8e924a87d1c4a7828daf98ab736af2ab0c70e6ff30944ba8f93566256`|

五manifest digest依次为`d90d8b82de570216e149ae9cbaef4c78490f557e23f5fe2ea22839b66e38ea5a`、`4bf651f95a2247b57bc246e23d3b0a6c52f005e8e835a9ad1df02b4cf9cfefa0`、`8ecc679575ecc75b44fe9d9ef9cc15043e1dd45875b74a0ee966579fb544cae3`、`25494f79922307c98d262feac32272cce8a539eb30d7338860f79de4c504f059`、`d18cc1dbaac033011a41d84b29a36ae6504880724d446f8745b68c05cf82c55f`。两输入digest为`20d539e9f94a76834dd5db5e886e70315a9bd6acacf0f316ace20a756ce93b56`和`225cec539c9f48c611007d04ae8c2bd1c3bb657c694d83d4b91304a04c3a30f9`。

关键原件的SHA如下，供后续汇总绑定：

|相对原件名|SHA-256|
|---|---|
|`source-r1.json`|`1ad75fc6352bf7094848e8d9716522e393de2faf981886e19fa650959c0e059f`|
|`rebuild-r1/result.json`|`12ecb212f5ddfbe5368090afbc172ada4b658ffc9d13643c90fea051241dab95`|
|`project-r1/result.json`|`8186e777494f94c3c58fb6fc4c84ea0c8d7ba813cf225782eb75b27549718298`|
|`project-r1/operations.json`|`cdd8b9e1295996e8d62b5ec1d145abb717b1bd33a576f145431306f094a9ed6b`|
|`source-inventory-r1.json`|`d1751dc12eddeb666207f981202271958dd54eb55ec3546870d8ae2c2e58c1ea`|
|`check-docs-r1.json`|`9e3e7c9f2ca781d4da4825828cb506ab19930b8ffa37de2f4757b4820403843e`|
|`self-review-r1-codex.json`|`ebde3449f1b09c85043b9d60d084213c2599d15422ed149da754e66e3d45df5e`|

固定G1a wheel整包SHA为`a2009e901fefb6e0507d6fedb14dff27c662feabeddf71b5e5f6a6a89f4619f9`；新安装器临时wheel未保留，只核其安装后的611产品，不借用这个整包身份。

自身审查首次wrapper把venv解释器symlink解析成系统Python，保留的stderr为导入Ergora前`ModuleNotFoundError`，没有据此声称模型run。第二次沿原venv入口用同一driver成功；实际run保存了明确Codex回退理由（此前大Claude审查超时，用户已授权回退）。这个自身模板结果与本报告的fresh-context磁盘／源码核对分别保留。

## 仍需记录的交接事实

作者应在最终计划／交付中写入本报告、自身审查最终结果和最终证据汇总，并把旧check-docs-r1针对较早计划／交付字节的检查与最终文档身份分开；本次独立链接检查已覆盖上表实际九文件。该项是当前计划已明确保留的收尾工作，不作为尚未发生的发布／CI成功。

未重跑安装、模型、浏览器、完整六阶段、真实训练或恢复；原保留执行记录与本次只读复核不等于重新执行。Windows／WSL2实际换机、活动workflow跨机器／跨路径、模型认证、GPU／B3、完整Forge、远端隔离和团队身份继续开放。后续固定发布须核完整Ref、实际发布文件与适用检查；如果CI策略另外变化，由其独立切片审查及实际新SHA检查决定。

## 最终本地汇总补核

同一审查者接续检查新增公共证据索引和更新记录，没有重新执行安装、模型或服务。**最终本地需求符合性approve、维护性approve，开放finding 0／0。** 上节等待的原件汇总与最终链接事实已按下述范围完成；发布、G1b前继CI门禁和本候选CI仍待实际事实，不在本结论内。G1d-CI继续由其独立切片负责。

公共`docs/delivery/evidence/2026-11-14-portable-usage-handoff.json`的391条引用逐项重读：全部为唯一、位于声明私有根内的安全相对普通文件，字节数及SHA均匹配；合计3,736,857B。按原数组顺序、UTF-8、排序键和紧凑分隔符重新计算规范摘要，得到`2bd19647c342b37d6ff3e392ff3d8c49fd014f4b2e1a4d2acb2379e34a607c06`，与collection-r1和collection-audit-r1一致。本轮所读公共索引整文件SHA为`87e104244d0a9fd6df42ae27632442a5f097df233eeb5536cfa4ed3c15a5c0e0`；后续仅审查／发布状态同步须另记文件身份，不改变这391引用的冻结身份。

逐字段比对公共validation与source-r1、rebuild-r1/result、project-r1/result、source-inventory-r1和self-review-r1-codex原记录，投影一致；耗时及final_local_checks也与各原件一致。公共索引没有展开私有原件正文，没有机器绝对路径或明显凭据值。391引用未纳入解释器／应用树、依赖缓存、重复源码树、Git内部文件、字节码、认证toml或可变SQLite；保留的完整输入和调用输出属于该次冻结证据，不当作活动状态数据库。七用户文档仍逐字等于原自身模板packet，本轮没有改写其身份。

原check-docs-r2确实记录16文件／439链接，无错误，其原件SHA为`894f649299ecb14f3d458ec3f1149420fdf9f22ee7277ec53c30033c8ef2f53e`；与原r1的9／323分列。后续G1c及邻片计划／交付又更新，不能把r2记录当作这些新字节的原检查。接续独立扫描当前共享工作树18份变更Markdown的583条本地链接／标题fragment，无错误；对邻片仅作链接检查，不扩大为其语义或CI配置审查。tracked空白检查通过，产品源码／测试／安装器／依赖相对506完整diff仍为空。

本轮曾发现一个P3记录精度问题并已关闭：`docs/delivery/2026-11-14-portable-usage-handoff.md:23`将自身模板的三份总声明资源称为“三祖先资源”。实读原composition显示1份来自父`root`的instructions，2份来自叶`root/review`自身的instructions和Skill；原措辞会误报祖先资料数量。作者已作最小修正为“三份声明资源（含父模板与叶自身）一致”，本轮已直接复核，原输入／输出及391索引均未改。没有由该问题推导新的产品缺陷。

本轮记录快照：G1c计划3274B／SHA`d79415e9af221bcb6c5bc56939d8f7a9490343f5d40a9f77f80accc288d0d06b`，G1c交付5134B／SHA`16c68a8793c1817adcdacabdaf257f262f8c62529b16b17a340610122a5e51f0`；当前PLAN36996B／SHA`c7917923539a2ae439177b083f925f1eea67c053639fdf017dcb7fcef12762d8`的G1c检查点明确本地通过与后续终核，并保留前继CI等待。后续仅状态记账与本报告追加不递归触发新的实现审查；若七用户文档、产品合同或CI配置有实质变化，则按其所属切片提供新身份和证据。
