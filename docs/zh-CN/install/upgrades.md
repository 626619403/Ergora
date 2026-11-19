# 升级与持久数据

简体中文 · [English](../../install/upgrades.md) · [文档目录](../../README.zh-CN.md)

升级前停止控制台、worker、执行器和其他 CLI 工作，确认在途任务状态，并备份完整持久目录及业务仓库。首次打开旧控制面数据库时会事务化升级，自动保存升级前的数据库快照；这个快照不包含 Skill、来源和运行文件，不能代替完整备份。新版本数据库拒绝旧程序写入，回退需要恢复匹配的数据库和文件，而不是仅切换代码。具体版本、错误处理和回退步骤见 [数据库升级说明](../../architecture/state-migrations.md)。

已有数据时，可以在停止相关工作后运行（Windows PowerShell 路径示例见 [Windows 手册](../../install/windows.md#upgrade-back-up-and-uninstall)）：

```bash
ergora state info
ergora state backup "$HOME/ergora-backups/snapshot-001" --offline
ergora state verify-backup "$HOME/ergora-backups/snapshot-001"
```

备份目录必须是数据 home 以外的新目录。工具保存数据库一致快照、普通文件、文件模式和空目录，核对 Skill / 来源快照的领域身份，并返回清单 SHA。它不会先升级旧库；没有数据的 `state info` 也不会创建数据库。`--offline` 表示你已停止写入，工具不替你停止服务或外部作业。

恢复前先把现有 home 移到其他位置保留，再执行 `ergora state restore BACKUP_DIRECTORY --offline`；自定义 home 使用全局 `ergora --home ORIGINAL_HOME state restore ...`。首版要求同平台、原 home，目标必须不存在；验证、复制及再次核对成功后才发布目录，不覆盖已有目标。它保留 JSON 中的绝对路径与证据摘要。业务仓库和外部服务另行恢复并对账，ReMe 可用 `ergora memory sync PROJECT --rebuild` 重建检索投影。

安装与数据版本分别管理；当前数据库schema为6，即使两个应用都报告0.2.0，也应保留源码完整提交、安装组合、解释器和依赖版本。升级前的应用与数据各留一份：重新运行所选固定源码的原安装器更新应用；回退时使用兼容的旧应用和它对应的完整状态备份。若新版本已产生资料，先另存新状态，避免旧快照成为唯一副本。完整应用目录可能含指向解释器的链接，不能把venv目录随意搬到新路径后继续使用。

## 换机与新项目重建

在新机器从同一分支或固定提交重新安装，按所选平台准备Python、Git、Agent认证及可选服务。源码、应用、控制home与业务Git各用持久位置；安装位置可用`ERGORA_INSTALL_ROOT`／`ERGORA_BIN_DIR`配置，运行数据另用`ERGORA_HOME`或全局`--home`。新环境只需控制面时，无需部署完整参考栈。

新项目沿[模板入门旅程](../../development/templates.md)重新登记实际repo路径、选择后端、导入精确preset并准备grant／完整manifest。相同定义包可保持版本和内容摘要；项目revision、带绝对路径的配置及调用输入则属于本次新环境。共享完整定义包和必要精确依赖，网页下载的preview JSON不能替代完整manifest。凭据通过工具登录或外部环境重新提供，配置只保存变量名。

要继续历史正式任务，按[联合备份手册](../../operations/backup-recovery.md)恢复同平台、原绝对路径的控制home、外部CONFIG／STATE、兼容应用、Temporal数据库和业务Git／worktree，再核原task/run、候选、批准和外部作业。`state backup`只覆盖控制home；新建项目或重新register不会恢复原运行身份。本地匹配应用／状态回退的验收也不等于活动workflow跨机器恢复。Windows与WSL2分别安装，不共享正在写入的SQLite或复制venv。

更换服务的控制home后，先完整重新加载网页，再读取当前项目和原操作记录。已有页面表单没有跨服务器重启的续用保证；浏览器缓存只是选择，不能替代服务端意图和回执。
