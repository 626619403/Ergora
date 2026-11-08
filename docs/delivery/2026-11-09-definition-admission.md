# AC3b.1：历史资产完整性与当前准入分离

日期：2026-11-09。状态：DA1–3及修正后源码/包、新独立两轴复审通过；DA4精确交付待验。初始基线 `833d46fd42e2064f8417f30b430c44069ac03a61`；AC3d测试夹具独立修正后，当前基线为 `460702f9866080756883501eefc5132b8a345a38`，分支 `refactor/architecture-foundations`，无历史改写。AC3d精确CI/远端终结仍单独记账；下一候选推送等待其收口。

## 合同与职责

用户要求可长期保存/复用专家与工作流，同时允许每层替换真实工具。当前Agent包检查把可变角色/后端catalog准入和完整性绑定，未来收紧catalog可能阻止历史包查看乃至备份。此片完成AC3a自身审查S1及[AC3b.1计划](../plans/2026-11-08-agent-composition.md#ac3b的下一批可验收切片)，不增加运行、权限、MCP或正式批准能力。

- 已保存Agent/Workflow的get/list/export检查各本包的版本化静态结构、完整树及资源摘要；保留原show本包材料、export当前包的合同，不在这些操作中递归验依赖。`verify_store`及完整备份/恢复另外递归检查精确引用、图/端口、完整材料、权限及预算。两条完整性路径均不要求后端当前可准入；所负责的范围内篡改/缺失/身份漂移仍拒绝。
- Agent check及两类新import、Workflow preview仍核当前角色/后端合同。重复导入也属于新准入，不能借幂等跳过策略；历史可读不表示当前可用。
- 不改变现有schema、包/索引布局、数据身份、DB或旧六阶段。无公开skip-validation入口，不自动修复或重新保存历史对象。
- `definition_bundles`拥有完整发布及身份；Agent所有者拥有当前binding准入；Workflow所有者复用同一有界遍历检查历史静态关系，在新导入/预览明确执行当前Agent准入；backups只消费历史完整性。

复用：两个生产所有者共享DefinitionLibrary的import专用检查；后端规则仍调用现有`agents.validate_binding`。新增私有静态Agent inspector与Workflow准入回调是稳定资产/可变策略的真实seam，不建立新插件框架。

## 可验收步骤

- [x] DA1：拆静态完整性与新导入检查，保留原子暂存/发布、原公开结果形状。
- [x] DA2：证明catalog删除/收紧后，原包及嵌套Workflow可读/导出/备份/恢复，新check/import/preview拒绝；损坏引用仍拒绝，历史字节不变。
- [x] DA3：受影响源码/非editable包、冻结身份及手册说明；新的fresh-context独立审查并解决finding。
- [ ] DA4：普通提交推送、精确必要CI及同片独立远端收口；更新计划后进入AC3b.2。

验证按本片变化选择已有Agent/Workflow/备份/合同测试，不添加镜像断言或新CI。完整AC3b大项结束时再用Ergora自身模板真实审查；本片不以历史模型approve替代新独立审查。

## DA1–2本地实现

三个既有生产所有者变化：DefinitionLibrary增加仅导入时使用的检查者，在源包与暂存副本发布前均执行；历史get/export不调用它。Agent的静态检查与当前`validate_admission`分开；两个库工厂的`.import_bundle`也保持当前准入，不存在低层公开入口绕过。Workflow有界遍历保留所有图/端口/材料/权限/预算检查，历史备份只走该静态检查，新import/preview另加当前Agent准入。无新生产文件、依赖、schema、DB、CI或磁盘身份。

5个新增行为案例覆盖移除角色、移除后端、收紧binding，以及嵌套树在策略变化后的缺失/篡改。源码Python3.11.15的Agent/Workflow/备份/schema四套140 passed、2原生Windows junction skipped，一条既有FastAPI/httpx弃用警告；日志为忽略的`.ergora/checks/ac3b1-admission/source-tests.log`。随后仅删去新增测试中重复的继承顺序断言，保留已有继承测试；最终包会再覆盖这五个案例。下一DA3非editable包/冻结身份、新独立两轴审查与记录更新。

## 初审与修正进行中

初版最终源码四套140/2，Python3.12.3非editable包同四套140/2分别通过；359份源/wheel/安装文件逐字及283冻结身份通过。初版wheel SHA256 `f4346629e92e6e8c8d22e899dc05de97f6b742fdbb65cb3ed2f102d7dea6acad`，不是后续修正版。fresh-context协调者独立新增5案例通过；Standards无finding，Spec指出两项P2，原报告及原探针保留。

1. 历史CLI `agent definition list --role`仍以当前角色catalog限制argparse，移除职能后无法使用历史过滤。已删除仅该历史过滤的choices约束，保留实际run角色校验；在原3个策略变化案例内加入真实`cli.main`调用，源码3通过（52 deselected）。待最终包及同片复核。
2. 本记录初版把get/list/export与完整备份合写为全部检查递归引用，超出既有公开合同。已明确本包完整性与递归备份的分工：原[Workflow手册](../WORKFLOW_DEFINITIONS.md#修订分享与恢复)及AC3d就规定export仅本包、引用包另分享，show只显示本包材料；本片不新增读取的递归拒绝。原AC3b.1目标是去除当前catalog耦合且保留损坏拒绝，并未要求扩大本地查看范围。协调者复现缺失依赖下get/list/export接受、verify_store拒绝，行为与基线相同；将其作为表述承诺过宽修正并请求Spec复核，不抹去原发现或冒称代码已递归检查这些操作。

另AC3d原候选Windows CI发现原测试夹具newline转换，正以独立单行修复候选处理；本片新增嵌套案例复用该夹具。修复不改生产语义，但本片最终scope/测试身份及基线必须随实际Git更新，不能继续沿用初版包身份。

## DA3修正后本地证据

CLI修正和明确合同后，同四套源码140 passed/2 skipped（Python3.11.15）及非editable包140/2（Python3.12.3）通过；两跳过仍为原生Windows junction，已有警告保留。359份源/wheel/安装文件逐字一致，283冻结身份不变；最终wheel SHA256 `f08d482d52b4dd11f691cf1d7d08d4dd502d45be7e3cd842f4ad502f582219bb`。同组案例已包含CLI历史过滤和Windows精确字节夹具，不与初版计数混加。初版包/记录留在忽略目录r1前缀与dist/r1。

原始r2-source-tests.log、r2-wheel-tests.log、r2-build.log、r2-install.log及package-identities.json保留在忽略的本片checks目录；[可分享最终身份](evidence/2026-11-09-ac3b1-local-identity.json)列出六份生产/测试文件SHA与包身份，无本机路径。尚待同片新scope复审、必要精确双OS CI及远端终结；本片未修改算法或增加性能声明，不制造额外基准或模型运行。

[新的独立两轴复审](2026-11-09-definition-admission-review.md)已通过：Standards无新增finding，Spec关闭SP-1代码缺口和SP-2有据文档处置，原发现保留。协调者独立核14项r2输入、六份生产/测试身份、最终359份源/zip/实安装逐字及283 reference.verify；在安装包隔离环境重跑新增5案例通过。两轴另核CLI执行角色仍拒绝移除项、导入暂存拒绝及损坏引用，未重复完整回归或追加无依据抽象。DA3完成，下一DA4普通精确提交、双OS CI及同片远端终结。
