# G1a 不可变记忆模板补丁交付

[具体合同](../plans/2026-11-14-memory-preset-patch.md)。基线`593da960f9eb4039518cfae9119ddafc1f7a847b`。恢复时前继F9d1已普通发布，自己的CI／原固定发布补核待。本片先本地实施，不提前推送。

初始只读盘点：原preset目录名用于找包，定义身份由各自ID／version／digest决定；原immutable definition library支持并存导入。记忆复盘准备接收任意精确manifest／instance，没有1.0.0硬编码。故只新增两Agent和root材料及更新原catalog，无需改运行时代码。两个提示首行各一个空格是唯一材料变化；旧1.0.0七文件全部保留。

当前已固定基线和验收节点，尚未生成新包或取得本片运行／审查通过。使用maintainable-project-delivery与writing-for-agents处理交付和提示材料。

## 新不可变版本已生成

已由原agent／workflow inspector计算1.0.1内容地址：author `90e09768e797c95b746892f517676a325c478096f86994043d9c78f8bc6ad1e2`，reviewer `1a6c669477fa24fed91b000914adadcdafd2d8f74965e6ad2c3e37c94ca984ec`，root `f80ea1f1512d5ac0d31ec90cd16a4c1360fd06aeee56a46eca76f04d419cd18b`。7份新材料＋原catalog更新，28个preset保持；7份原1.0.0文件逐字保持，其他27个条目保持。两新提示各只删首行一个空格；root只改version与两个ref，其他资源逐字相同。

接续非editable安装与原preset／memory suites，Skill材料和评价owner未变化，不为机械补丁重复整套Skill评价或真实模型生成。实际旧库升级／旧冻结材料保持另经原CLI验收。

首轮实际24CLI均exit0，19项升级／材料保持检查通过；私有驱动最后误按`ok`／`checked`取reference verify字段而KeyError，未生成passing result。原接口实际为`status: PASS`／`files: 283`，原失败保留。r2只修这处读取并换新的隔离目录，产品不变。最终结果接续。

## 当前安装与实际升级旅程

最终r1非editable wheel包含611产品／619wheel文件／624 installed RECORD行，两RECORD、源／包／安装逐字相同及283冻结参考均通过，wheel SHA256为`a2009e901fefb6e0507d6fedb14dff27c662feabeddf71b5e5f6a6a89f4619f9`。实际隔离r2旅程20项／24CLI／9.561405秒通过：旧客户端明确安装1.0.0，准备原manifest及两完整叶输入；新客户端重复安装默认1.0.1并保留全部旧／新引用，原7 library对象和完整旧manifest／input树逐字保持，旧root／两输入仍原样可读、同旧manifest重准备摘要和完整prompt不变。

新root经原CLI编译／冻结并准备两叶，完整task、root Skill／instructions及叶instructions均在实际prompt，权限／limits／边不变，Codex／Claude Code默认请求保持。此处只准备输入，没有执行模型、记忆采用或训练，也未启动服务。原preset／memory安装回归仍在运行；自身原模板和新fresh-context审查待。

最终原preset／memory两suite共48通过／155.29秒，原进程owner返回succeeded／exit0、156.773716秒。含原默认记忆候选准备／check／export／保存恢复和原其他preset保持；没有新增测试、CI或断言。新fresh-context独立审查已开始，自身原structure-review接续。

## 自身审查、总核与固定引用

最终安装件的原structure-review使用授权Codex回退，run `4f7fd8e3a1284ef582dc092b29268141`，19.567425秒approve；24份完整文件112,775B、原输入／prompt／实际stdin及三份祖先资源直接核相同。该text-only模型结论只审提供的完整正文，不替代fresh-context reviewer的磁盘／原件审计，不冒称异后端验证。

最终audit核604→611的精确产品差异只有7新增及catalog一修改，源／构建快照／安装全同，原7文件／其他27 preset不变；24CLI原输出摘要、48原测试结果、完整模型材料及所属服务进程观察均通过，没有匹配本片服务。没有新服务或业务目录被启动／改动。

[公共摘要与固定原件索引](evidence/2026-11-14-memory-preset-patch.json)共416条／2,700,168B，规范references数组SHA256为`97061b95645d726c19817b1e1104aee05f3eaf427b547da51c063fe5e5e11e38`。r1失败和r2正例均保留，完整测试case／源码副本与认证配置不装入公共索引；原件仍在私有验收目录可直接复核。独立报告不递归指纹，发布／CI之后另列；最终独立本地两轴待。前继自己的CI仍在途，本片先本地完成，不借其成功或取消它。

## 最终本地独立出口

新fresh-context reviewer已完成最终独立两轴：需求approve／维护性approve，开放0／0，无产品finding。611源／快照／包／安装、两RECORD／283、24CLI／旧37件及7对象、两新叶全材料、48原测试、自身原回复和119,658B实际stdin／三资源、416引用及收尾均获直接核准。[原报告](2026-11-14-memory-preset-patch-review.md)已保存本地终态快照；只批准本地，不预批前继CI、本片固定发布／自己的CI或G1b。

前继F9d1精确593da96自己的CI43585798832八job／30必要步骤及原reviewer终态两轴现已闭合，原592／5发布／48CI保持；本片普通固定发布门禁的前继部分已满足。G1b当前仅公开初始合同／计划，不预批后续实际安装或回退。
