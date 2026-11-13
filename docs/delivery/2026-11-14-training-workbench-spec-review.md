# F9a 需求与行为独立审查

日期：2026-11-14。Reviewer：`/root/f9a_spec_review`，fresh context；先读原始要求与实现／调用者，再读作者交付。项目及文档归属均为 Ergora。按 `code-review` 的需求轴和 `maintainable-project-delivery` independent-review brief 审查；维护性轴另行判定。

## 范围与身份

基线：`47443840b68693f63ee011dc6fbe29421a42223f`，候选为工作树。原要求为[总计划第8节F9](../plans/2026-11-01-all-in-one.md#8-p1低代码更多真实工具与演进闭环)、该基线的 `docs/TRAINING.md`、[F9a计划](../plans/2026-11-14-training-workbench.md)及 `AGENTS.md`。

r1 精确15文件清单／完整SHA在私有 `review-r1-files.json`（SHA256 `64afde1d9aa92aa5e867c3cbcdd039003c28cc1fab1bedd374d022461ff62094`）；tracked diff SHA256为 `e66af65f93a226d8da42e10dc390e27fecfaccfe2c7c737768b178c69fd35357`。已核15份原SHA，完整读取新增文件。范围包括：

- `src/ergora/{training,reference,cli,web}.py`；`src/ergora/data/console/{training.js,app.js,index.html}`。
- `tests/test_training.py`、`scripts/ci/linux-groups.json`、`README.md`、`docs/TRAINING.md`、`docs/architecture/current.md`、本片 plan／delivery及 `docs/PLAN.md`。

另查原 `agent_platform.training`／`training_executor`、`perf_temporal.models`、`perfctl`、safe/bounded reader及登记／CLI／HTTP／页面调用者。H3b原报告状态追加不进入本片产品结论。

## Findings与修复复核

1. **P2，r1 [reference.py](../../src/ergora/reference.py#L424)**：当前runner与原job request均缺失时跳过两处仓库核对；相同project ID的另一仓库可读到prepared实验。违反计划“runner／job须属于同项目与同Git根”。最小修正是在两见证均缺失时返回归属无法确认错误，保留原request存在时的历史读取。来源为自身模板／结构轴，本审查用r1非editable包独立复现；当前源码已明确拒绝，list保留单条错误，show报错。
2. **P2，r1 [reference.py](../../src/ergora/reference.py#L373)**：合法的config与state同目录使基于路径相等的来源标签全部变为config，随后state摘要取值失败，list／show均失效。违反有效配置范围及只读查询要求。最小修正是显式传入配置来源。来源为结构轴，本审查独立复现；当前源码正确保留两类标签并可读取。

两项源码复核均通过，需求轴源码开放 **0**；其余已查范围未形成finding。当前 `reference.py` SHA256：`31f95d6c48c2a7462c2aa0b7b514e1d4ad21636c55c3619684b9973912d7ec94`；`test_training.py`：`054dd01f52e541164aca666d0fb235be65e8493cfdc143410524ee3905ea7a4e`。后补r2完整15文件快照 `review-r2-files.json` 的SHA256为 `143340070bb3d3c721ee8efeb825475cf804c2c706786f55f4d1ccf7e50f68d4`，已逐项核对；两产品修复及三份说明／进度更新已读，其余仍与r1一致。

## 证据与限制

私有证据根为 `.ergora/checks/training-workbench/`。本审查实际执行 `spec-review-r1/audit.py`：同进程A/B/A目录隔离、原字节不变、缺runner／baseline、坏条目分页及非法输入通过；`recheck.py`对照r1和修复源码复现并关闭上述两项，夹具SHA不变。未安装、运行服务、提交实验或改写原实验。

已读原件：源r2为25通过／12.25秒；r3为仅第一修复的26通过／12.51秒；两修复后的r4为27通过／13.09秒。r1安装身份为563产品文件、两RECORD、283冻结参考；六suite为121通过／87.23秒。原生CPU仅init／runner-add／prepare及原adapter job／fence，18份原文件当前SHA均匹配；没有Temporal查询、runner执行、MLflow查询或GPU证据。浏览器r1详情已读；`late-project-r2.stdout`保存实际详情响应延迟后切另一项目的抑制成功及所用Playwright代码，首轮夹具参数错误原件保留。前端字节未随两修复变化；该记录仍保留r1包范围。

上轮结论为整体F9a验收待完成：当时尚未核定修复后的安装／回归、原生CPU与浏览器、自身模板复审及最终出口。r1安装／自身模板不自动验收修复源码；后补证据如下。

## r3最终本地出口

同一reviewer继续本片复核；只读源码和原件，未安装、重跑大测试、启动服务或调用模型。最终冻结清单 `review-r3-files.json` SHA256为 `58ee20102091738341e33685735dd56638698e96394d375438e2f2858399f6a5`；其中10个产品／测试／CI／README条目均匹配，说明与报告的状态追加另计。核心reference／tests保持上述r2身份；唯一后续产品变化为完整6551B的 `training.js`，SHA256 `f754d2409ec19d002e5e076426b08d7594dc59e48969d2c212ce6da9e765ef44`。已完整读其源码及相对r2差异：基线摘要保留可展开的完整基线／文件摘要，实验卡片保留原详情入口；请求、分页、错误和生命周期语义未变。未形成新finding。

- **安装与回归**：独立逐字重核r2、r3各563份source／wheel／installed产品、两RECORD及283冻结参考SHA。最终noneditable wheel为 `df85fd4c28d502f8d39c1138e317738ee716d090baf9114c1d41db9b538b285a`。r2安装训练／架构／reference三suite原命令、exit和日志为33通过／16.98秒（受控18.616秒）；r3仅展示变化，核心成绩保持r2范围，不声称重跑全套。
- **原生只读回读**：已查 `native-readback-r3.py/json`、原观察及18件原SHA，最终reader得到同一完整观察。浏览器的两份实际详情HTTP响应SHA亦等于该原观察的compact JSON。CPU材料仍只证明原owner prepare／job回执／fence与读取，不证明runner执行、停止或训练收益。
- **实际浏览器**：已查r3 CLI argv／exit／stdout、服务代码、served identity和40条GET 200原请求；实际training资产SHA匹配最终源／包。完整基线40位commit／摘要及实验原件展开、旧详情晚到后切项目、旧列表晚于新列表均有实际代码和成功结果。已视觉检查1440、960、390三视口截图；记录显示无整页横向溢出。cleanup原件与本次只读 `/proc`核对均显示原r1／r3 controller和原监听已停止。
- **自身模板**：r2完整11文件187,590B、r3完整六前端25,122B逐文件SHA已核；实际stdin与prompt逐字一致，三项祖先资源完整进入stdin。原result及持久run result逐字／SHA匹配，分别23.977秒和23.370秒 `approve`。两次仅为所给源码的原模板审查；Codex授权回退与首轮request-changes保留，不扩大为异后端或独立执行验收。

**需求与行为轴本地出口通过，开放finding 0。** 维护性结论见另一独立报告；本报告未核定普通发布、精确远端身份或本候选自己的CI，这些仍须随后补核。[公开验收摘要](evidence/2026-11-14-training-workbench.json)与已查原件范围一致。所有状态仍为原件观察：`not_queried`、started、runner SUCCEEDED和gate摘要SHA匹配均不证明实时运行、重新独立测量或采用。没有Temporal workflow、runner执行、MLflow查询、真实模型／数据、GPU、统计或采用验收；F9b–d、真实B3和完整C2保持开放。
