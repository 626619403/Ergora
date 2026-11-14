# 控制面数据库的升级与回退

`ergora.state.State` 拥有本地 SQLite 的初始化、连接和有序迁移；领域模块继续拥有查询、修订冲突和事务。这里的数据库 schema 版本与 Python 包版本、项目 JSON 版本、正式工作流合同版本分别管理。

## 初始化与所有权

当前数据库schema为 **5**，由`state.py`的有序迁移列表决定。早期同为0.2.0的程序可能创建`user_version: 0`数据库；包版本号不能标识数据库版本。当前库有21个应用表，已知表的INSERT／UPDATE／DELETE由63个v5触发器保护。

|迁移|内容|迁移后应用表数|
|---|---|---|
|v1|补齐原16表，核旧列布局，建立已知旧writer保护|16|
|v2|增加`issue_snapshots`、`issue_task_links`及关联目标索引；替换全部writer fence|18|
|v3|增加`issue_writebacks`、`issue_writeback_observations`；替换全部writer fence|20|
|v4|增加`candidate_review_links`；替换全部writer fence|21|
|v5|记忆有效期改变持久语义；不增加表或改列布局，全部writer fence更新至v5|21|

已有行、JSON字节、原SQL语义及额外用户对象保留；不匹配已知旧列布局的库拒绝升级。打开旧库时从其版本依次执行后续迁移，例如v0执行v1至v5，v4只执行v5。已是当前版本不重复迁移或产生额外升级备份。应用表和触发器的数量不包含用户额外对象。

```mermaid
flowchart TD
  Open[打开持久 State] --> Lock[跨进程初始化锁]
  Lock --> Version{数据库版本}
  Version -->|当前版本| Ready[连接核对版本并注册 writer 函数]
  Version -->|不支持的版本| Stop[明确拒绝，使用兼容发行]
  Version -->|旧版本| Tx[BEGIN IMMEDIATE]
  Tx --> Backup[独立只读连接备份原库并核验]
  Backup --> DDL[补齐表与旧 writer 保护，设置版本]
  DDL --> Commit[同一事务提交]
  Commit --> Ready
  Backup -->|失败| Rollback[回滚；不继续升级]
  DDL -->|失败或中断| Rollback
```

DDL 只在存储初始化执行。工单、记忆、Skill、评价、优化、研究、草稿和kernel不自行CREATE TABLE；没有新增 ORM 或通用记录封装。新代码每次连接都检查版本，已存在的 State 实例也不能忽略后续出现的不支持版本。revision 的读/比较/写仍在各领域的 BEGIN IMMEDIATE 内，不靠初始化锁代替。

## 升级前备份

先停止 CLI 工作、控制台、研究 worker 和可选执行器，并对账在途外部工作；再备份整个持久 home。SQLite 与本地资产、业务仓库、完整参考发行 / Temporal / MLflow 状态分别需要相应备份。不能在文件正在变化时把一次目录复制称为一致恢复点。

迁移非空旧库时会在 home 的 `backups/` 下生成 `schema-vN-<随机身份>.sqlite3`，N为本次打开前的原库版本，例如v4。一次打开只保存一份原库快照，后续迁移在同一事务内依次执行。迁移连接持有 SQLite 写锁，另一个只读连接用标准库 SQLite backup API 获取原库，包括 WAL 中已提交的数据；经过 integrity_check 后，临时 `.part` 文件才改为正式文件。备份失败时不开始迁移。已有行和文件资产不会被迁移重写。

这个自动文件仅覆盖数据库，不包含 Skill、来源快照、运行输出或外部服务。它是升级前的数据库恢复点；升级后新增的数据也不会自动出现在此旧快照。完整离线资产备份与核对属于独立恢复流程，不能用一个 `.sqlite3` 文件替代。

迁移步骤和 user_version 在同一显式事务内提交；中断后依赖 SQLite 的 journal 恢复。失败信息包含完成的数据库备份路径或明确说明没有完整备份；不要采用遗留 `.part` 文件。保留失败原因，确认磁盘与原库可用后用兼容程序重新打开，不删除未知状态来假装升级成功。

## 离线完整备份与恢复

`ergora state info` 读取版本而不创建/升级库。`state backup DIRECTORY --offline` 在原始 SQLite 上操作，可用于 schema 0 升级之前；`state verify-backup DIRECTORY` 不需要原 home 仍然存在。命令默认沿用 ERGORA_HOME / 平台用户数据目录，全局 `--home` 可明确选择目标，位置解析与正常 State 共用。

`ergora.backups` 拥有以下流程，CLI 只解析参数和输出结果：

```mermaid
flowchart LR
  Offline[停止写入与外部工作] --> Lock[初始化锁与 SQLite 写锁]
  Lock --> Snapshot[DB backup API + 普通文件复制]
  Snapshot --> Verify[清单 / SQLite / Skill / 来源身份核对]
  Verify --> Publish[发布新的备份目录]
  Publish --> Stage[原 home 不存在时暂存恢复内容]
  Stage --> Recheck[再次核对清单与资产]
  Recheck --> Restore[发布到原 home]
```

备份是一个含 `manifest.json` 和 `data/` 的目录，根目录权限按用户私有目录创建。清单采用 `state-backup-v1.json` / Draft 2020-12，版本严格为整数 1；记录原 home、平台、数据库 schema、创建时间、每个文件的大小 / SHA-256 / 文件模式和空目录。清单自身的原 UTF-8 字节 SHA 作为快照身份返回，不改变评价、Skill 或正式合同的旧摘要。

控制面数据库通过 SQLite backup API 获取已提交数据，包括 WAL；快照切为独立数据库，不改写原库的领域行和 JSON 内容。根目录的控制面数据库 sidecar 与 `.schema.lock` 不单独复制。其他普通文件、子目录、运行输出和已有迁移快照按文件清单保存；数据资产中的符号链接、Windows junction / reparse point 和特殊文件明确拒绝，在下降到子目录前检查。备份目标必须在 home 外，且是新路径，避免将快照递归装进自身。

复制前后比较源文件清单，核对复制内容，再验证暂存备份。SQLite 检查完整性和版本；Skill 目录复用原 digest_tree（含执行位），来源原文SHA必须符合数据库source_snapshots；工单域核snapshot／link字段、内容摘要、SQL列与引用，v0／v1没有新表仍可离线验证。增改、缺失、额外文件/目录、模式变化或领域身份不一致均拒绝，复制失败不发布残缺目标。所有这些检查仍以已停止写入为前提，不是在线事务跨文件保证。

恢复先校验备份，再在目标父目录暂存复制并重新校验清单身份与内容，完成后才发布到原 home。要求同平台、原绝对 home 和不存在的目标，不自动重定位或覆盖现有数据；用户应先将现有 home 移到另一处持久位置保留。恢复旧库保留其原版本；由兼容的State正式打开时才依次执行后续迁移。`state info`、备份与核包本身不升级。暂存中断最多遗留临时目录，不把它当成完成的备份或 home。

清单覆盖控制面 home 的本地文件，不代表业务仓库、模型认证、外部 evaluator、Temporal / MLflow、reference 运行状态或远端 ReMe 已恢复。恢复后仍须核对它们的路径、可信文件和在途任务；不要让运行状态行触发自动重提。ReMe 投影使用已有显式 rebuild，不修改 canonical 记忆。

## 旧程序访问和回退

早期v0程序不检查user_version，单独设置版本号无法阻止它修改新库。各次迁移为已知表建立或替换INSERT／UPDATE／DELETE触发器，要求连接提供匹配的`ergora_writer_schema_version()`；v5目前为21表的63个保护。当前State注册版本5并在每次连接检查库版本；未修改的v0程序因缺函数拒写，已经打开且仍返回旧版本的连接也不能写这些表。原始SQLite读取不依赖writer函数，但旧Ergora入口可能在版本检查时直接拒绝打开新库。

这个机制保护已知旧二进制的数据库 DML，不隔离同一用户，也不会停止旧进程写文件、运行 Agent 或提交外部作业。因此停旧服务是升级步骤的一部分。手工注册函数、删除触发器或降低 user_version 不能作为受支持的降级方法。

若要回到旧二进制，先停止所有新旧进程，单独备份并保留当前完整 home，再恢复升级前彼此匹配的数据库和文件资产到原位置，最后启动对应旧版本。旧快照不含其后的变更，不能用它覆盖唯一的新数据副本；仅 git revert 不会回退数据。目录中存在绝对路径的运行记录和可信 evaluator 身份，不应为了换目录而静默重写 JSON / 摘要。外部 ReMe 是检索投影，恢复后可通过 `ergora memory sync PROJECT --rebuild` 重建；canonical 记忆与修订仍来自本地库。完整任务栈还需按[联合备份手册](../BACKUP_RECOVERY.md)保存外部执行目录和服务。
