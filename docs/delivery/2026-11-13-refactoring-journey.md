# D2-A2：重构配方真实串行旅程

承接[A1重构配方](2026-11-13-refactoring-preset.md)，使用其精确已核非editable wheel，运行产品、父模板及Agent包不修改。A1本地出口后再启动实际模型；准备与运行、独立审查、普通发布各自记录，不借治理旅程的并行writer结果证明本片串行。

## 输入与验收出口

隔离标准库小项目中，`normalizer.aliases`重复`normalizer.normalize`的逻辑，真实`client.request`调用这两个公开函数。目标是让aliases复用既有normalize，并保持Unicode lower、输入类型／TypeError、空值、顺序／去重、generator消费、返回类型和真实caller。一个writer只改normalizer，后续兼容性writer在集成前驱的候选上补一个有价值的caller测试并写实际证据；原可信integrate／verify后接三个必需独立reviewer。

保护真实caller、检查脚本及原baseline参数。可信检查读取精确baseline Git blob，以固定边缘输入和确定性样本作原实现／候选差分，运行真实caller和unittest，再在持久目录下的独立临时子目录恢复精确baseline源码并验证caller。该回退证明本地源码恢复，不是生产部署回退。检查脚本与项目持久数据不放系统或项目tmp目录。

|节点|实际出口|状态|
|---|---|---|
|A2.0 准备|已核安装包；独立Git fixture／baseline及可信原checker预验；原refactoring根完整manifest与definition6准备|驱动及fixture已准备，未执行|
|A2.1 执行|一次总预算、7槽；真实inventory／plan／owner精确批准；rewrite→compatibility串行；可信集成验证／三review，保留实际outcome|待A1本地出口|
|A2.2 恢复与交接|同ID重复start／重启原run；完整history重放；精确候选导出、独立复验及handoff|待运行|
|A2.3 原件与清理|所有实际会话、完整祖先与scope、串行前驱产物／原slot／owner清理；服务停止而持久记录保留|待运行|
|A2.4 交付|新的独立两轴审查、计划和手册同步；普通提交／远端／自己的必要CI|待前项|

显式采用用户已授权的Codex回退，独立会话不宣称异构后端。A2不扩展运行图、GPU优化、远端业务写或Windows服务支持；失败、超时、unknown和未通过审查都保留原结果，不在原任务下换输入或重领预算。
