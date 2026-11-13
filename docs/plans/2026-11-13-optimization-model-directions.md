# B2f：模型配方与模型验证方向

日期：2026-11-13。承接 [D2 专家计划](2026-11-13-specialist-presets.md)和 [R9 调查](../research/2026-11-12-optimization-model-recipe-agents.md)。实施基线 `83000a1afbdbd2429efbcebe1e7c65133215ca8e` 是 B2e 的五份同片结案 Markdown；产品基线 `99b953fcff931cda60e4ff41ff66a8870b7f7866` 自己的 CI43420340258 八 job／30必要步骤及独立终核通过，结案普通推送与作者 SSH 完整 Ref 已核准。

## 范围与归属

新增 `optimization-recipe-model` 与 `optimization-model-verification` 两个只读配方，各包含 workflow、instructions 和完整原创方向 context。精确复用 `ergora-training-analysis@2`／`ergora-measurement-review@2`及原 design／profile／measurement 三位专家。CLI／HTTP／页面继续使用原定义库、编译器和单叶调用；measurement 由操作者传入两份完整原前驱。

只增加六个数据文件、catalog 两条及既有方向参数测试两项，同步训练手册和模板旅程。不新增模型下载、转换器、验证卡 validator、搜索器、训练入口、Agent 类、schema、调度器或账本。代码适配交原六阶段，实际实验／质量／恢复／采用交原所有者。保留十八旧 catalog 条目、共享版本、536 旧产品除 catalog 外的字节及 283 冻结文件。

## 固定资料与合同

复用 R9 中 Bridge `55694838ce73cd23b00ff95bd00512aefb963ce0`／0.8.0 的十二份已保存 HTTP200 原件，共 464,656B；长度及 SHA 已再次核准，本片新增 GET 为零。资料包括 recipe Skill、adding-model-support 及四份 patterns、verification-card Skill／validator、forward compare、AutoBridge、Qwen3 bridge、MLM／Bridge correlation。产品是本项目原创综合，不复制第三方实现；URL 只标出处，不代替全文资料，也不授权下载或执行。

|方向|必须保留的区别|
|---|---|
|模型与配方|请求的任务／真实模型与权重／数据／模态／框架栈；library 与 canonical benchmark 配方及真实入口；收敛语义与执行映射，mock／forced routing 不作收敛证据；新 builder-backed config 与完整 mapping／模态支持，保留已有 provider 家族差异；部署导出、训练状态、短关联和独立质量分别验证；压缩／RL／外部原生流程不因引用而安装或执行。|
|模型验证|十二核心验证项与四种状态逐项保留；canonical 性能配方存在性未知时不假定有或无；完整 tensor／checkpoint／真实 mesh、相同输入与激活模态；固定 forward 条件为同 next token 且 cosine≥0.99，max／mean 差仅作诊断；compare helper 的数值比较失败不会自动转非零 exit，必须读原指标；schema-valid card 不是实证；新进程重载、optimizer／RNG／data next-update、独立质量及未 profile 配对性能分别验。|

输出支持的观察、矛盾、假设、缺失证据及最小后续检查；保留 unavailable／unsupported／incomplete／failure／no_gain／noise／unknown。不把路径、声明、exit0、短 mock 或文本审查当真实模型支持、GPU 验证或采用许可。

## 可验收节点

|节点|出口|状态|
|---|---|---|
|B2f.0 前置|B2e 精确候选自己的 CI、独立终核、五 MD 结案与远端 Ref|完成|
|B2f.1 资料与数据|两根、完整 context、catalog／原参数表与两手册，旧条目和产品保持|十二来源及SHA已核；两根／catalog／原参数表和两手册已实现，十八旧条目及536旧产品除catalog外保持|
|B2f.2 安装与合同|新 Python3.11 非 editable 包、source／wheel／installed、两 RECORD／283、原安装 preset suite；正式七次 collection 核新全集与六组并集|非editable542／两RECORD／283通过；七次collection核1715全集＝六组并集、交集0；原安装preset suite27通过／105.35秒|
|B2f.3 真实叶交接|两方向各三次独立 task-MCP，完整祖先 UTF-8 读取至末页，精确 input／stdin／scope／native／result 与完整原前驱|六叶均succeeded，无重试；36资源77,413B完整连续UTF8／手动原前驱核准，两个measurement均request-changes，仅针对synthetic输入|
|B2f.4 审查与发布|自身原结构模板八全文；新 fresh-context Spec／Standards、修正复核；普通提交推送及自己的完整 CI／独立终核|自身25.248秒approve／八全文53,365B核准；新fresh独立双轴完整原件终核通过，开放0／0，本地出口完成；已普通提交／推送2d13c0e，精确16Git／作者SSH Ref核准；自己的CI43426570060官方Success，八job／30必要步骤及完整SHA日志路径获原独立终核通过，精确交付终结|

真实调用只用明确 synthetic fixture：未来 SFT 请求被建议使用 pretrain-only mock，且将 global batch 从32改64；无真实模型／配置／环境。另一份保存文本的 helper exit0，但 token mismatch、cosine0.98低于冻结0.99；操作者声称卡 schema-valid／verified，却未提供卡或运行 validator。审查应识别这些冲突和缺项，不能伪称运行过 helper、validator、转换或训练。每调用240秒、外围290秒；失败原件保留，必要重试另目录，成功调用不无故重跑。进程观察只报告实际覆盖。

后续仍有 cluster resiliency、kernel／low-precision、B3 原实验 manifest／runner 和 Forge 受限内部循环；本片不提前关闭它们。
