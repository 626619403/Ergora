# AC5 C3c D2：资源修订接口纵切片

固定产品基线 `3baa619096a2ff95e2a29aedf179f3c614af103e`，分支 `refactor/architecture-foundations`。[本片计划](../plans/2026-11-10-definition-resource-interfaces.md)与[C3c合同](../plans/2026-11-10-definition-resources.md)是验收依据。

## 准备

C3b第三份官方完整CI采样已观察Success，原件 `ac5-definition-editor/commit-closure/snapshot-03/`，原01/02进行中保留；原独立评审者06:58:51 UTC离线直接解析原件通过，C3b精确交付终结。D1 r1设计审查有四项阻塞，r2固定完整候选/操作/目录复用/历史恢复合同，同片设计复核在途。当前只写本片计划，I1–I5未实施/验收。

产品实现等待这两个门禁；实施后原库继续承担暂存与发布，CLI/HTTP不复制算法。验收原件统一保存在私有 `.ergora/checks/ac5-definition-resource-interfaces/`，不使用易清理临时目录，不公开个人配置或凭据。

## 实施起点

C3c D1 r3新独立Spec/Standards设计复核通过，DRD-1–6关闭；C3b精确交付已终结。门禁满足，开始I1–I3产品实现；I4安装旅程及I5新独立实现审查/自身模板/精确交付仍未验。D1报告不作为本片实现通过。

## I1–I3 初次实现及只读目录发现

已在原五个生产文件接通共同操作/历史文件窗口、可选资源预览/接受、原锁内目录复用核对及两类CLI/HTTP；未增加生产模块/依赖/数据库/schema文件/CI。测试在现有两文件补完整CLI/HTTP往返、接受身份和空目录同摘要冲突等真实合同。

首次命令误用了旧C3b非editable安装包，未设置source导入：11新功能失败（旧包没有入口）/11旧资源相关通过/5.54秒，原 `source-resource.log` 保留；这不是当前产品回归或故意旧包复现。改为明确 `PYTHONPATH=src` 后新11项得到 **9通过/2失败/7.02秒**，原 `source-resource-r2.log` 及五生产源身份 `source-r2-identity.json` 保留。

两失败均实证：原包root目录0555完整复制后，原export将新复制目录跨父目录rename时Linux拒绝更新目录的父关系，资源操作还未开始；Agent/Workflow同路径。修正在原export/import复制出的新root增加必要owner-write后再rename；不改历史对象/源目录，不改文件执行位或摘要。修后完整受影响源码/安装回归待验。

## I1–I3 源码出口

原五生产文件及两现有测试文件实现完成；source-full.log首命令引用不存在的test_reference_package.py，退出4/0 tests，原件保留，纠正为已有test_reference.py后执行五组得到 **183 passed / 1 skipped / 70.94秒**，原件source-full-r2.log。此前9绿/2只读root红及最小修正身份分别保留。当前只有源码出口，不能替代安装或真实CLI/HTTP旅程。

共同库处理严格操作清单、完整字节、执行位/路径重叠、仅临时owner-write、摘要建议、完整候选接受及原锁内目录冲突；两个use case与CLI/HTTP薄接入。只读历史文件窗口不跑当前后端准入；新资源预览/发布仍按今天完整准入。两手册已补资源目录、建议正文、明确接受/检查/发布、base64 HTTP与完整窗口规则，USAGE链接同一合同；页面资源会话仍未提供。

R1独立非editable wheel已离线构建安装，身份/受影响包回归/三域实际CLI和HTTP待验。下一步将固定实现交新的fresh-context reviewer，只读核原要求/所有者/结构/控制流/测试价值/成本；自身模板及提交/CI/HTTPS仍在I5，不提前记完成。

## I4 R1 安装与三领域实际旅程

R1 wheel SHA256 `26dfe4d4034cb26b8082b633dfc3a8155b113d41b7fb93164feddcb173a29396`；435源/wheel/非editable安装/RECORD一致、283冻结原文件与基线一致，原件 `r1/package-identities.json`。六组安装回归 **191 passed / 1 skipped / 82.84秒**，原件 `r1/packaged-tests.log`；与源码183项范围区分，安装多含原web组。无额外CI或新测试框架。

同一安装完成三领域六定义 **81实际隔离CLI / 37真实HTTP / 47.56秒**，原件 `r1/journey/{summary.json,cli-*,http-*,http-identity.json,cleanup.json}`。每类实际从原preset导出/导入增强基准（含原空目录、未声明二进制与完整Skill），再将基准目录/文件设为只读：预览→建议正文→明确接受→JSON/YAML及HTTP同候选检查→变更附件拒绝→明确发布→相同CLI重试→完整导出再导入→二进制分页合并全部字节均通过。新Skill完整多文件、原Skill附件变化、执行位、明确删除、父目录自动创建及新空目录均实测；未编辑文件/原对象全部mode与旧manifest保持。真实超过4MB HTTP请求按原中间件拒绝413；没有绕过同源/写头保护。训练只有定义资源旅程，没有模型/CPU/GPU实验。

唯一owned HTTP进程3095365/starttime231428969按保存身份终止并reap，未动用户服务。I4此范围通过；没有页面变更所以未新增浏览器验收，D3会话/继承整链旅程仍后置。新fresh-context独立实现两轴正在读固定review-r1；实际内置模板、公开证据/最终静态及自己的提交/CI/HTTPS待验。

## I5 独立初审发现（R1仍固定）

新的fresh-context实现审查者使用两轴复核，发现两条可达问题，独立原件均保留：

- RIF-1：Windows删除只读目标需要先清readonly；原代码只改父目录，直接unlink。Linux受控Windows只读unlink语义probe沿实际两类preview在新暂存remove.bin复现PermissionError，原对象/文件mode/索引保持；原件 `independent/readonly-delete-probe.{py,json}`。这是受控平台语义实证，不是原生Windows运行。已有两类完整往返测试把原文件设为只读并删除该附件，后续原生Windows CI会覆盖。
- RIF-2：CLI目录loader在库的总量/重复拒绝前，可按最多1500个write重复读取并保留base64。同一约9MB文件的合法小目录可因此放大内存。低成本独立probe使用8192B×1500，loader实际读1500次、累计12,288,000字节/16,386,000base64字符后才被共同owner拒绝；原件 `independent/cli-loader-budget-probe.{py,json}`，没有实际制造OOM。

R1真实自身模板正在固定源/测试上运行，先保留本轮精确身份和结果再修改。拟最小修正仅在delete新target unlink前加owner-write，以及CLI每次读取后/编码保留前累计并限制10MB。两个分配阶段分别保护CLI表示转换及最终库操作；不复制重复/重叠算法、不新建测试框架/CI/helper。两finding尚未关闭，R1通过的Linux旅程不能代替这些修正。

## 第一轮真实模板及最小修正

R1实际内置structure-review模板run `6f7f4db7bfbe499d99ed47f94703228c`，**332.66秒 / succeeded / request-changes**；原result SHA256 `1ec4f023640458ebd178ce452d8035a0b5353d4b80bedbeeb25d09dea9cd0710`。它独立识别RIF-1只读Windows删除问题，未识别RIF-2，不能用模板意见代替完整独立评审。14完整保护源/测试/配置、464921候选字节、18连续UTF8页和四祖先指令/Skill读取均经原manifest/input/prompt/native stream/result审计通过，无base64重试或失败读取；原件 `self-review-r1.json`、`model-read-audit-r1.json`。仅证明字节送达与原结果身份，不证明推理质量、不同模型独立性或正式批准。

原R1固定源及两条独立红保留。修正只在原库增加：CLI读取后的累计10MB检查（编码保留前）、delete新暂存目标owner-write后unlink。没有新增重复路径算法/生产文件/依赖/测试/CI；已有两类roundtrip继续覆盖只读删除。受影响源码/最终R2包、同片独立复核及第二轮实际模板待验。

## R2 验证及目录分配风险

R2 wheel `60b457c68c3c10253a12a0039063bab3aa0da06b317aa091c85f21f7a12dacac`，435源/包/安装/RECORD与283冻结保持；受影响安装 **43通过/19.94秒**，三域同样 **81CLI/37真实HTTP/49.92秒**、六定义同候选/完整树/只读原对象/旧manifest保持，owned HTTP身份清理。R1六组191通过仍按R1登记，不冒称R2重跑。修正的同片两个受控probe已绿，Windows仍仅受控语义，原生待自己的CI。

为RIF-2增加一个有意义的低成本既有文件回归：8KiB×1500重复write，R1实际安装原红为未抛错（0.60秒），R2转换阶段拒绝；不分配OOM级负载。此例保护输入转换分配，与原库重复路径拒绝不是同一测试面。

作者进一步提出RIF-3，独立受控probe确认：原操作只在全部物理mkdir/write后才做500目录/32层inventory；197B单33层mkdir触发34次mkdir调用，17071B/501平级mkdir触发1002次，均在共同_apply内未拒绝，最后才由inventory失败。原件 `independent/rif3-directory-budget-probe.{py,json}` 及受审源副本；没有实际目录洪泛。最多1500×512字符操作可先分配远超最终限制的目录，故在现有前缀循环维护原目录+mkdir全路径/write父目录的有界集合，超500/32立即拒绝；原最终inventory继续验证，不创建新helper/第二套摘要。delete不产生新目录；合法32目录+第33文件组件保持。

该最小预检及现有测试文件中的3例（33目录、501目录在首次请求分配前拒绝，合法32目录+文件仍通过）进入R3最终候选；R2原证据保持。R3受影响验证/同片复核及第二轮模板待验。

## R3 最终安装候选

R3 wheel SHA256 `1b74ada0caa05f2a1360fa76f7e5b50027ea8ae3fc0c7cdd1819bedf096c1a23`；435源/wheel/非editable安装/RECORD与283冻结身份一致。R3对比R1包逐文件只有 `definition_bundles.py` 的上述三个最小修正不同，其他434文件相同，原件 `r3/package-diff-r1.json`。R1六组191通过的结果保持R1身份，不冒称R3重跑。

RIF-3现有测试在实际R2安装得 **两红/一绿/1.31秒**，分别证明非法目录到达首次分配、合法32目录+文件未被错误拒绝；原件 `r2/directory-regression-red.log`。R3受影响resource/architecture/reference **46 passed / 19.43秒**，含RIF-2转换预算新回归和RIF-3三例；原件 `r3/packaged-tests.log`。R3再完成三域六定义 **81CLI / 37真实HTTP / 49.05秒**，完整候选/资源树/执行位/空目录/只读原对象/旧manifest保持，CLI JSON/YAML与HTTP同身份；owned HTTP也按身份终止reap，原件 `r3/journey/`。三轮累计三owned HTTP已清理，无浏览器或模型服务后台验收进程需清理。

同片独立RIF-3/完整最终候选复核在途，第二轮真实模板及最终公开证据/静态/提交/CI/HTTPS仍待完成。不把Linux受控Windows语义probe当作原生Windows成功。

## 第二轮真实模板与公开材料

R3实际内置模板第二轮run `69f00da988634827a4e1f5687ca1e848`，**323.03秒 / succeeded / approve**，原result SHA256 `0c011a0cfec443acb1f59f348c4adf14aa2fd52c7dc4ec732cc57d88c03152bd`。14完整保护源、527526候选字节、21连续成功UTF8页及四祖先指令/Skill原件已审计，无base64重试/失败读取；原manifest、准备输入、实际输入、prompt、native读取stream和原结果逐项匹配。原件 `self-review-r2.json`、`model-read-audit-r2.json`。首轮request-changes和所有原红保持，完整字节交付不替代推理质量、不同模型独立性或正式批准。

公开证据为[最终包](evidence/2026-11-10-definition-resource-interfaces-package-r3.json)、[最终三领域CLI/HTTP](evidence/2026-11-10-definition-resource-interfaces-journey-r3.json)、[原受控红](evidence/2026-11-10-definition-resource-interfaces-findings-red.json)、[最小修正受控复核](evidence/2026-11-10-definition-resource-interfaces-findings-fixed.json)、[三轮owned HTTP清理](evidence/2026-11-10-definition-resource-interfaces-cleanup.json)。第一轮[身份](evidence/2026-11-10-definition-resource-interfaces-self-review-r1-identity.json)／[原意见](evidence/2026-11-10-definition-resource-interfaces-self-review-r1-result.json)／[完整读取审计](evidence/2026-11-10-definition-resource-interfaces-self-review-r1-reads.json)，第二轮[身份](evidence/2026-11-10-definition-resource-interfaces-self-review-r2-identity.json)／[原意见](evidence/2026-11-10-definition-resource-interfaces-self-review-r2-result.json)／[完整读取审计](evidence/2026-11-10-definition-resource-interfaces-self-review-r2-reads.json)分别保留原native SHA。这11份JSON是去个人目录的格式化投影，其文件SHA与原件SHA不同，私有publish-evidence.py/public-evidence.json逐项记录来源与投影身份。

本片5生产文件、2既有测试文件、原两定义手册/USAGE/架构、D1/D2计划及交付与独立报告、C3b状态续记及11公开JSON构成最终范围。没有页面资源会话/嵌套画布/正式交接/训练实验声明，也没有新依赖/生产文件/CI。RIF-1–3独立本地关闭、R3包/实际旅程已独立原件核验；第二模板/公开投影及最终完整候选同片终核仍待完成。随后普通提交/推送并核自己的必要CI及明确HTTPS，不继承C3b的CI。

## I5 本地出口

原fresh-context实现评审者已终核固定`review-final`全部34文件，Spec/Standards本地通过，RIF-1–3全部关闭、零开放finding。第二轮manifest/input/prompt、14保护源、527526字节/21连续UTF8页和四结构链材料均直接重算；两轮native stream只有list/read，没有command/file_change/web_search。11公开JSON已逐来源bytes/SHA及逐字段投影复核，两原result投影与native身份对应。独立静态检查为**16文档/248链接/107实际CLI parser命令**，零缺失。

本地I1–I5出口完成。提交前只续记状态并固定最终ready清单，产品/测试保持R3与第二轮模板保护源身份；不重跑已通过的安装、整组或模型。下一步普通提交/推送当前分支，分别检查精确对象、自己的双OS七必要CI步骤及明确HTTPS。尚未满足这些精确交付门禁，D3仍只允许设计准备。
