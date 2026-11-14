# F10d6b 工作流候选导入页面交付

[具体合同](../plans/2026-11-14-workflow-improvement-console.md)。基线 `0fd74b16c98185081e06c4ef356700b881c781e7`；前继已普通推送且固定发布补核通过，前继自己的 CI 独立等待。初始盘点时尚未修改产品或运行验收，后续实施如下。

已核原 `workflow_definitions.import_bundle`／`DefinitionLibrary.import_bundle` 不可变发布与原 CLI；原定义页有精确选择、祖先资源／权限预览和完整 manifest 保存，但没有用户工作流目录的 HTTP／GUI 导入入口。本片补此缺口，复用原 owner 与共享局部表单，不引入第二采用账本。验收原件保存在忽略目录 `.ergora/checks/workflow-improvement-console/`，公开文档不含凭据或用户业务材料。

## 实施与首包检查

原 web 增加仅含 directory 的 DTO 和薄 POST，原定义页增加绑定 DOM view／控制目录的明确导入窗口，复用局部 submissionForm；共享提示不再指定某页刷新按钮。无新模块、依赖、schema、tests 或 CI。进一步直接核 import_inspector 确认原导入会先编译并核完整依赖；已纠正初始设计中只把依赖检查归给后续 preview 的描述。缺依赖直接拒绝，不发布部分根。

首包 r1 非 editable 604 产品／两 RECORD612／617／283 通过，原 workflow-definitions／web 两 suite 107 通过／72.71秒；最终 r2 仅澄清依赖提示，604 产品／两 RECORD／283 同样通过。浏览器首次默认启动因未指定已有 Chromium 路径失败；随后使用既有本地浏览器配置正常打开。r2 驱动首次启动与预建输出目录冲突，在原 owner 运行前退出；只修驱动 mkdir，产品不变。完整最终浏览器旅程、自身模板与独立审查仍待，不以这些启动检查宣称通过。

## 原模板发现 R1 与实际红例

自身原 `ergora-structure-review` 通过 Codex 读取十个完整文件207,881B与全部继承资料，52.709秒返回 request-changes：已发出的 modal 表单在来源 view 被并发定义库／详情读回重绘后，会丢弃成功／失败回执。最终 r2 安装件实际红例4项／1样本／2.484秒复现：原 import 返回200与精确digest，原窗口仍打开却继续显示等待；`receipt-red-r2`保留原件。接受 R1，保持发送前 current/view/窗口准入，只让已发出请求的回执跟随仍连接的原表单；不会操作替代窗口、自动刷新或重发。等待最终新包绿例与共享 caller 复验。

早期主驱动在默认720px高度时导航超出视口，另一试跑把 JSON 键顺序误当语义差异；前者未进入导入，后者已有原成功导入回执，均保留为驱动失败，不当作完整旅程通过。最终使用新夹具从头验证。

## 最终 r3 首轮结果

最终 r3 非 editable 包604产品／两 RECORD612、617／283冻结通过，wheel SHA256 `304a2898c1d6fb5d3c285aea3786be4aeba4eb81e582d2bfe801d9dce9e33f8c`；原 web 九项11.73秒通过。原 Python owner 与 r1 安装107项的源码相同，最终 JS 行为另以真实网页验证。

新夹具的完整页面主旅程31项／15样本／8.452秒一次通过：原CLI prepare/check/export 的完整根候选→原HTTP同digest导入→明确刷新和精确选择→原grant预览→明确新manifest冻结；幂等、版本内容冲突、缺目录、缺依赖不发布、单次请求、迟到成功／错误不动替代Help、执行后503与原精确读回、跨项目共享库、旧tab/home表单不发送、无项目定义库及三宽页面／窗口均通过。R1绿例、共享caller、CLI全文读回与收尾仍待。

修后自身原结构模板用Codex37.295秒approve，十二完整文件234,292B及全部祖先资料已核实际stdin；原r2 request-changes及实红保留。run `3f0bcfb49d2c45d195a49d85bf8c9f1b`。新的fresh-context reviewer已独立开始源码与合同核查，尚不预批完整交付。

## 最终本地出口

R1 原成功与错误两条完整绿例各4项／1样本，2.376／2.271秒通过；共享记忆保存与 Skill 导入两真实 caller 在后台全局刷新重绘后仍展示原回执，8项／2样本／2.811秒通过。合计最终47项／19样本，三宽六张截图已实际目视；截图存同一浏览器 daemon 初始 cwd 的 browser-r1/output/playwright，内容明确为最终 r3，不能按目录名误判包身份。

原 CLI prepare/check/export 与旧叶准备四次，随后六次完整 readback 共十次：14,100B Unicode／CRLF正文、完整文件／执行位／空目录、导入 digest、新 manifest及原 grant 一致；原定义、全部既有边／引用／权限／limits、旧manifest和旧叶材料保持。`cli-r3/result.json`与完整stdout分别保存。

只读 audit-r3 直接核当前604产品＝构建快照＝安装件；原r1／r2／r3夹具分别2／19／75个原HTTP，全部request／response／记录摘要与原trace一致。最终r3有6次held、1次执行后503夹具；三组原候选、source、作者input、manifest、旧叶／task／Git保持，三个服务PID／端口及一个观察到的浏览器daemon PID均已退出。原 r2 红例与r3正例分别保留，不拼接早期失败片段冒充完整主旅程。

产品与本地验收已固定。新独立源码两轴approve、开放0／0，R1直接核红／绿后关闭；新独立最终本地两轴已approve／开放0／0，143固定引用、96组原HTTP、原件／收尾、CLI、239,167B完整stdin及三祖先资源均已直接核。固定发布／自己的CI尚待，143原引用保持。合成提案只验合同，不证明工作流改进的质量或性能，也未执行训练、GPU、ReMe或完整原生Forge。

## 普通发布

已普通发布 `3a56508791a33871016acff4a7cad268aaf0be50` 至当前开发分支，15固定blob与完整远端Ref一致；未合main。143固定原引用保持，五份发布调用／回执单列。前继自己的CI及原reviewer终态已闭合；本片原固定发布补核两轴approve、开放0／0；自己的CI43580979082在途，不借前片通过。

## 精确交付闭合

固定`3a56508791a33871016acff4a7cad268aaf0be50`自己的CI43580979082终态Success，八job／30必要步骤全部通过。原reviewer直接核完整SHA官方run与原job HTML、52条单列CI引用，两轴approve／开放0／0，R1保持关闭；本地、普通发布和自己的CI三门禁均闭合。143固定引用及五发布引用保持，后继WIP不属于本片固定结论。
