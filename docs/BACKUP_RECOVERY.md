# 本地任务栈的备份与恢复

完整任务恢复需要同一离线时间窗口中的控制home、执行配置与状态、Temporal数据库和业务Git仓库。`ergora state backup`只管理控制home；它不会备份登记在其他目录的执行数据，也不会停止服务。下面使用原控制备份命令和Linux的GNU tar组合保存本地栈。

## 先确定范围并停止写入

先把下文`CONTROL`设为原数据home的实际绝对路径，再运行`ergora --home "$CONTROL" project show PROJECT`，记录项目revision、repo及`registration.definition.execution`中的`installation`、`config_directory`、`state_directory`。共享相同执行栈的项目必须一起纳入；另存Ergora版本、Python/依赖版本、工具版本和可用认证方式。凭据仍由你管理，不进入Git或公开报告。

先用`ergora --home "$CONTROL" task status PROJECT TASK --run-id ORIGINAL_RUN`逐一核原task/run；`ergora --home "$CONTROL" task external-status PROJECT TASK --run-id ORIGINAL_RUN`仅接受已闭合的原run，再据其处理未决外部作业。仍运行或unknown的任务先保留原意图，按取消与恢复流程处理，不以外部查询失败推断已停止。服务停止不会释放租约，也不能证明外部作业已经结束；`CANCEL_UNCONFIRMED`和unknown必须保留，必要时按[取消与对账说明](USAGE.md#请求取消与恢复未知投递)处理。停止控制台、研究worker、训练任务及其他写者后，用[公开services入口](USAGE.md#显式服务管理)关闭这次备份覆盖的栈。不要停止不属于该栈的进程。

以下目录变量必须替换为登记的实际绝对路径。示例假定目录互不重叠；多项目或多个栈须列出所有目录并去除重叠项。备份目录放在它们之外，且不得放入会清理的临时目录。

```bash
CONTROL="$HOME/.local/share/ergora"
CONFIG="$HOME/ergora-local/config"
STATE="$HOME/ergora-local/state"
INSTALLATION="$HOME/ergora-local/installation"
REPO="$HOME/project/my-project"
BACKUP="$HOME/ergora-backups/snapshot-001"
```

具体要保存的内容：

|位置|恢复所需内容|
|---|---|
|控制home|控制SQLite、项目注册、历史修订、Skill/Agent/Workflow资产、来源及调用快照；由原`state backup`核清单和领域身份|
|CONFIG|完整项目、adapter、权限、后端、服务配置；私密配置与认证引用也须保留|
|STATE|`tasks/`、`ergora/task-*`意图/attempt/回执/对账、原请求根/receipts/artifacts/approvals/fences、全部ledger、Temporal数据库及sidecar、workspaces、mirror、进程记录和日志|
|业务Git库|完整`.git`及工作区，包括未提交文件；只有远端或`git bundle --all`无法保留全部运行态工作区|
|执行安装与外部依赖|兼容的reference与Ergora、原解释器/venv、工具二进制；符号链接只保存链接本身，链接目标必须另存或可按原路径恢复|

Git worktree可能在原STATE中通过绝对路径关联mirror；其他仓库、外置Git目录、LFS对象或工具运行数据也须按实际依赖纳入。不要在备份时解引用链接来替换原工作区结构。

## 生成并核对离线副本

服务和外部作业确认停止后，在同一终端执行。GNU tar保留文件、文件/目录模式、目录和符号链接目标（Linux不以符号链接模式位授权访问）；本配方不承诺ACL、扩展属性、跨平台恢复或在线多库一致快照。

```bash
umask 077
mkdir -p "$(dirname "$BACKUP")"
mkdir "$BACKUP"
ergora --home "$CONTROL" state backup "$BACKUP/control" --offline
ergora --home "$CONTROL" state verify-backup "$BACKUP/control"

tar --create --preserve-permissions --file "$BACKUP/execution.tar" \
  --directory / -- "${CONFIG#/}" "${STATE#/}" \
  "${INSTALLATION#/}" "${REPO#/}"
tar --compare --file "$BACKUP/execution.tar" --directory /
(cd "$BACKUP" && sha256sum execution.tar > execution.tar.sha256)
```

任一命令失败即停止，不继续移动原目录或宣称备份可用。`tar --compare`比较当前原目录与归档；不要在它之前启动写者。保留控制命令返回的manifest SHA，并在可信位置另存归档SHA和目录/版本记录。摘要可核传输完整性，不能自行认证备份来源。包含凭据的本地备份按私密文件保存。

## 在同平台、原路径恢复

先验证原件与归档，再逐一把现有CONTROL、CONFIG、STATE、INSTALLATION、REPO移动到新建保留目录；所有原目录都须保留，目标路径必须不存在。恢复在新机器上也要求原绝对路径和匹配运行依赖，JSON中的路径不会自动改写。符号链接的解释器或工具目标须先核实存在且版本匹配。不要运行`project register`重新生成原任务，也不要新建ledger替代丢失的所有权记录。

```bash
ergora --home "$CONTROL" state verify-backup "$BACKUP/control"
(cd "$BACKUP" && sha256sum --check execution.tar.sha256)
```

确认原目录已经保留、目标均不存在，再执行：

```bash
ergora --home "$CONTROL" state restore "$BACKUP/control" --offline
tar --extract --preserve-permissions --keep-old-files \
  --file "$BACKUP/execution.tar" --directory /
tar --compare --file "$BACKUP/execution.tar" --directory /
```

仅对自己刚验证过的可信归档执行提取，原路径须有当前用户的写权限。`--keep-old-files`遇到已有文件会失败，提取失败可能留下部分文件；保持服务停止，保留这些现场并核清缺失项后再处理。控制home的原接口先暂存重验再发布，且拒绝覆盖；它不让整个外部tar提取变成事务。

启动前先核项目注册和完整任务信封、原创建/提交/取消/对账记录、请求/回执/产物摘要、原owner批准及lease。检查每个业务库、mirror和worktree的原候选SHA、refs和未提交状态；按原数据库工具检查SQLite完整性。数据库的逻辑数据与原任务身份应保持；控制库快照的物理页或启动后的日志字节可能改变。

由`ergora --home "$CONTROL" services start PROJECT temporal --revision N`先启动Temporal，再用同home的services start显式启动需要的worker等服务，然后查询每个原task/run。重复原`ergora --home "$CONTROL" task start ...`（同项目、task、revision及creation SHA）应沿原提交记录返回同一run，不应自动派生新任务；未确认的外部状态先对账，不重发副作用。原outcome、候选、批准及claim不因恢复改写。完成核对后再开放新写入；不要同时启动保留的旧栈和恢复栈。

Windows原生控制home仍可用[Windows备份命令](WINDOWS.md#升级备份与卸载)。本页GNU tar和Supervisor整栈配方用于Linux/WSL2；迁移远端Temporal、MLflow、ReMe、工单系统及跨路径迁移需要各系统自己的恢复流程与另外验收。ReMe检索投影可从控制库按[使用手册](USAGE.md#升级与持久数据)显式重建。
