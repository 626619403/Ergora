# G1b：首次安装、旧项目升级与回退

承接[G1总交接](2026-11-14-integrated-handoff.md)及[G1a不可变模板](2026-11-14-memory-preset-patch.md)。本片初始HEAD593da96，产品基线为G1a最终611文件映射与非editable wheel（SHA `a2009e901fefb6e0507d6fedb14dff27c662feabeddf71b5e5f6a6a89f4619f9`）；尚未包含其他产品修改。G1a本地两轴已通过，固定发布／自己的CI待。本片先独立安装和演示，只有G1a自己的固定CI及原reviewer闭合才替换日常应用；开始替换前补精确发布身份。

## 范围与现有所有者

复用原`scripts/install.sh`、平台目录约定、原CLI／HTTP、`State`的4→5事务和writer fence、`backups`完整离线备份／恢复，以及原process monitor。默认业务home、认证、其他任务和业务Git都不用于演示，不建立第二迁移器或恢复协议。原件在`.ergora/checks/install-upgrade-rollback/`；机器路径和完整私有应用备份不公开。

本片无预定产品变化。若现有接口实际失败，保留实红，按原owner最小修正并验证；不为安装文案或普通可见失败增加产品测试。Windows使用固定候选自己的PowerShell CI；本机Linux不冒称原生Windows／WSL2验收。

## 可验收节点

- [ ] 在新的隔离安装／bin／控制home中从固定source运行实际Linux安装器默认control profile；保存实际依赖／包／RECORD／283身份、CLI及HTTP的preset和静态资源一致性。准备离线依赖缓存属于本片准备，不声称空环境原已具备Python／Git。
- [ ] 当前旧日常客户端创建独立schema4演示项目、记忆／Skill／原精确模板及叶输入；新客户端在不迁移前执行原完整离线backup／verify，随后沿正式打开升级到schema5；旧行／文件身份保持，旧客户端写入拒绝。
- [ ] 新状态补一条演示资料并完整备份；保留新状态，隔离应用换旧wheel、同原home恢复原schema4备份，用旧客户端读回原项目／资料／精确冻结包；随后恢复新应用和匹配新状态，核新旧资料及身份。保留两方向快照及移出的状态，不声称迁移活动workflow、外部服务或跨路径恢复。
- [ ] 日常应用替换前观察相关进程、已知默认state、依赖／启动器和完整venv归档，核前后身份；有在途工作则保持安装，继续独立验收，不终止其他任务。前置精确发布／CI门禁闭合后仅离线重装Ergora，保留非应用依赖及用户配置／状态。
- [ ] 实际日常入口列28项和新1.0.1，必要CLI／HTTP和完整材料验证及自有服务收尾；原迁移／备份suite按风险验证，不重复无变化的GPU／模型生成或全部旧网页交错矩阵。
- [ ] 大项调用Ergora自身审查模板，新fresh-context需求／维护性两轴核原件及范围，处理实证finding；更新计划／交付并普通发布、完整Ref、适用CI及原reviewer终核。

依赖边界：控制home的备份不包含业务仓库、外部CONFIG／STATE、Temporal或模型认证。恢复仍要求同平台、原绝对home且目标不存在；旧客户端与新schema不能并行写。G1c再更新公开手册中的实际版本、换机重建及联合恢复说明。
