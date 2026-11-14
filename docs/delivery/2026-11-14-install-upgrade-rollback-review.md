# G1b 安装、升级与回退独立审查

审查者：`install_upgrade_rollback_review`，新 fresh-context。范围为[G1b合同](../plans/2026-11-14-install-upgrade-rollback.md)和[交付](2026-11-14-install-upgrade-rollback.md)，按原始要求先读合同及实际源码，再读作者叙述。只读源码、原始归档、SQLite和Git；本审查不安装、不运行产品或测试、不启动服务、不联网、不提交，仅写本报告。

固定初始HEAD `593da960f9eb4039518cfae9119ddafc1f7a847b` 加G1a最终611文件映射；当前产品候选为 `506cc576874e92bc922644a8dd9f244151b08e4b`，分支 `refactor/architecture-foundations`。固定wheel SHA256为 `a2009e901fefb6e0507d6fedb14dff27c662feabeddf71b5e5f6a6a89f4619f9`。原始证据根为私有 `.ergora/checks/install-upgrade-rollback/`；产品映射、源snapshot及固定wheel沿G1a原件读取。本片未修改产品、测试、依赖声明或CI；同时在途的G1a发布／CI记账不算G1b产品改动。并行G1c的README、USAGE、架构／迁移手册及portable-usage-handoff计划／交付属于下一片，不纳入本片实现或发布通过结论。

|审查轴|最终本地结论|后续门禁|
|---|---|---|
|需求符合性|approve；隔离安装、4→5→4→5匹配应用／完整状态、实际日常替换与两组CLI／HTTP、原自身模板和最终聚合均已核；开放finding 0|G1b普通固定发布、完整Ref、适用自身CI及发布／CI独立终核另列|
|维护性|approve；复用既有owner，无产品／测试／依赖／CI变化；R1–R3已修并经原件与最终结果复核，开放finding 0|不预批后续发布或G1c手册／新路径旅程|

**已关闭finding R1，P2，私有聚合必然拒绝已知历史失败。** `.ergora/checks/install-upgrade-rollback/audit-r1.py` 原草稿第62行遍历r1／r2／r3原operations时无条件要求每条 `exit == expected_exit`。直接读原JSON可见r1第五条 `old-skill` 实际exit2、原expected0，是已如实保留的目录名夹具错误；原聚合必在r1中断。已最小修为只允许这条精确历史失败，并核原AssertionError及目录合同stderr；r2的KeyError和两次无passing result保持。独立重算三旅程71命令／142原输出hash，唯一不匹配与显式历史记录相符；没有改原件／expected、补跑产品或把r1改称通过。最终audit-r1实际exit0／passed，原历史失败显式保留，finding关闭。

**已关闭finding R2，P2，私有聚合进程筛选漏掉实际服务入口。** 同文件原草稿第112行只认argv内精确 `ergora`／`uvicorn` 等token；HTTP原命令使用绝对launcher路径。将原 `http-fresh-r1/server-command.json` 的argv代入原谓词得到False，虽然本片路径存在，因而可能误记本片服务进程数为0。已最小增加两原server-command中的精确launcher匹配，保留限定本片路径、原owner结果及端口检查。修后谓词对原fresh服务argv和配置daily服务argv为True，对audit自身argv为False；没有启动服务。实际两服务原owner均返回，cleanup无错误／端口关闭，修后最终audit记录匹配进程0及两个端口关闭，finding关闭；只认可限定的一次argv观察。

**已关闭finding R3，P3，公开收集草稿重复原CLI计数误差。** `collect-r1.py` 原草稿第40行直接采用r3原result的 `cli=30`；该历史字段由 `state-journey-r3.py:103` 的 `'ergora' in argv` 产生，把 `rollback-app` 和 `restore-new-app` 两条uv pip重装也算作CLI。直接读原35条operations，实际 `-m ergora` 为28条，21检查／35总命令准确。收集器现从原 `argv[3:5]` 派生实际28，公共摘要分列 `original_r3_cli_field=30` 和旧口径说明；原result／自身packet hash与所有命令原件保持，不补跑产品。独立核最终公共字段与原argv一致，finding关闭。

**已直接核验的证据。** 阅读 `AGENTS.md`、`docs/PLAN.md`、G1总交接及本片合同，使用 maintainable-project-delivery 的独立审查要求。检查既有 `scripts/install.sh`／`install.ps1`、`state.py`、`backups.py`、CLI维护命令与HTTP调用路径、`tests/test_state_migrations.py`／`test_state_backups.py`、原PowerShell安装验收及Portability CI。逐字读取本片preflight／cache／fresh／state-journey-r3／两组HTTP／regression／release-gate／install-daily／audit／collect驱动及其原实际产物。

- 以标准库读字节和Git archive逐项核对：当前Git产品、工作树源码、G1a源snapshot、611映射、固定wheel及最终fresh实际产品全部相同；Linux／PowerShell安装脚本、`pyproject.toml`和组件配置也与候选及snapshot相同；283冻结参考文件全部核hash。最终fresh在回退旅程后已实际重装，当前RECORD为624行、623个含hash条目，均逐项通过；原首次安装806行是其当时记录，不能当作当前RECORD行数。原首次构建临时wheel未保留，因此只认可完整产品字节相等，不认可该临时wheel的SHA身份。
- 直接读持久venv归档：38,724,819B、SHA256及6,360成员与记录相符，含5,152文件／symlink和1,208目录，没有提取或恢复。原前像记录551产品、23 preset、38 distributions及默认state不存在；相关argv观察限定清楚，不扩大为整个home／全系统／脱离进程树检查。
- r3的35条命令输出70个SHA256均直接重算通过，21检查记录与实际命令吻合。旧schema4数据库21表／5行与升级schema5的全部原行相同；旧非DB120文件、新非DB135文件的内容及模式直接核对。两完整备份的manifest hash、所有文件／目录／模式、原绝对home与平台相符；两移出状态和最终原home的SQL行／trigger／文件分别与对应旧／新快照相同。唯一自动schema4 DB备份的行和trigger也与原旧库相同。
- 原完整叶输入四次读回（旧、升级、回退、再恢复）JSON逐项相同。五层祖先及叶的六份资源（五instructions／一Skill）全文均在prompt中。旧客户端写入明确exit2，原升级SQL行保持。新资料在回退前独立完整备份及原目录中保留；回退使用旧应用配旧状态，再恢复新应用配新状态，避免以旧客户端解释schema5。新旧记忆、Skill及新root的实际读回与原件一致。
- 11个HTTP原body逐项核字节数与SHA256；目录、完整root与六条CLI原输出相同，首页和五个静态模块与最终安装字节相同。原cleanup记录服务受原process owner取消、errors为空、43607关闭；驱动先收齐cleanup再写passed。只认可CLI／HTTP读取，不推断浏览器旅程。
- 直接核原两suite日志为42通过／1 Windows平台项跳过／30.35秒，原process结果为succeeded／exit0／30.932034秒。r1目录名不符和r2字典形状误读的失败原件仍保留，均没有passing result，r3修正仅在私有驱动，不把这些fixture错误称为产品回归。
- 自身原structure-review模板run `84b88a68d9b94f6c8ff17efcbffcef6a`，授权Codex回退35.985283秒、succeeded／exit0／approve。直接从原task按packet的长度及hash逐字核17份全文／80,922B，三份祖先／叶资源均进入prompt；原实际stdin与prompt相同，原result hash及摘录正文一致。原回复明确仅覆盖给定代码和已完成隔离事实，未批准未来日常替换／发布；本独立磁盘核验承担其未触及范围。
- 日常替换前门禁的六份证据hash直接相符；精确产品候选自己的CI `43587371986` 八job／30必要步骤全部success，包含Windows PowerShell 5.1 installer and upgrade，原reviewer终态完整快照字节及SHA相符、两轴approve／开放0／0，随后才有gate与实际安装。没有以别的候选或自审替代该前置门禁。
- 实际日常611产品直接等于固定wheel；624行RECORD逐项核提供的hash／大小，38 distributions直接读metadata与前像相同。将当前venv与完整原归档直接比较，4,550个非应用文件／symlink全部相同；原launcher symlink、解释器shebang及已知默认state不存在均直接核对。实际离线重装与前后依赖检查exit0，未把归档字节核验说成完整venv恢复演练。
- 日常HTTP另外11原body均核长度／SHA；目录、完整1.0.1正文与六CLI输出相同，首页及五静态模块与实际日常安装字节相同，28 preset与明确的新隔离home可直接核。3.592499秒，原owner返回cancelled、errors为空、45565关闭后才写passed；该服务使用隔离演示home，默认业务state仍不存在。
- 最终audit-r1实际exit0／passed，记录五匹配状态、两安装各624行RECORD、两原owner／端口结果、71命令及142输出、原17全文和87,284B stdin／三资源。独立逐件重读[公共索引](evidence/2026-11-14-install-upgrade-rollback.json)全部1,669条／9,880,492B，路径唯一、长度／SHA全部相同；规范references数组SHA256为 `f2c1666733091f081e6a4009d16170bcce9fb808f25a27eb91391d14aef8541e`，与原collection摘要一致。未收进依赖wheelhouse、完整venv、重复源码／testcase或认证配置；独立报告及后续发布／CI不递归纳入该固定数组。

**维护性判断。** 安装仍由既有平台脚本和profile配置承担；CLI维护命令直接调用原backups owner，不先构造State造成意外迁移；4→5事务、原DB自动快照及旧writer围栏仍归State；恢复沿原同平台、原绝对home、目标不存在的合同。HTTP服务复用原process monitor，未新增产品迁移器、备份协议、调度器或候选／批准权威，也未改变冻结模板、unknown对账和祖先资料语义。本片未增加产品测试或CI，复用原风险相关suite，无新增多余成本finding。

成本建议（非阻断、未实现）：`.github/workflows/portability.yml:6` 仅忽略docs Markdown，新增纯交付证据JSON仍触发完整八job／30必要步骤；直接搜索tests及CI runner，没有读取这类交付JSON的生产／测试消费者。本片611产品及installer不变，后续可单立CI范围片，为纯记录改动使用适量静态核验，保留产品／安装器变化的原平台回归。本片不修改CI，也不以该建议改写精确候选门禁或冒称已减少开销。

**边界与后续门禁。** 先有Python／Git和准备的离线缓存属于明确前提；本机结果不证明空OS已配齐依赖、Windows原生或WSL2。Windows结论仅引用固定产品候选自己的上述原PowerShell CI终态，未声称本机原生执行。原执行目录、业务Git、外部CONFIG／STATE、认证、Temporal活动workflow、GPU与质量／性能均不在本片已验范围；venv归档未实际恢复。G1c负责公开安装及跨机手册，不以控制库原路径恢复冒称跨路径活动任务迁移。

日常替换、独立实际入口及最终原件聚合现已完成，R1–R3全部关闭，本片最终本地需求／维护性两轴approve，开放0／0。后续须单列G1b普通固定发布的精确Git对象／完整Ref、适用自身CI及原reviewer终核；本地结论不预批这些未来事实或并行G1c。首段和历史进度中的“在途／尚未”仅保留当时身份，实施者应同步当前计划入口的最新记账；这类状态同步不需要重跑产品。
