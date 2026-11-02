# F1.3：旧注册预览、显式采用与恢复

日期：2026-11-02。源码基线`a6fd29162bc066cd8954275032bc103b3f11fc66`，已推送且远端一致；F1.2独立审查及最终本地255项回归通过，精确两OS CI待核。用户授权继续完成F1。本切片从该提交开始实现，保留F1.2审查者补充的最终本地证据文档。

## 范围与设计

导入spec仅声明schema_version、id、预期业务repo、execution、templates及可选bindings。从所选配置目录有界读取同名project/scope及可选execution策略，不读取模型凭据、platform设置或在途任务。复用F1.2的项目校验、注册定义、跨资源意图/reserve/publish/resume，不另造项目所有者。

默认dry-run，展示规范化定义、JSON pointer差异、文件采用/补建意图、源原始字节SHA和预览摘要。执行时必须携带预览摘要与当前控制项目revision，重新读取并核对源身份；源变化（包括仅格式变化）、不同Git根、未知旧字段/版本、归属或不可变内容冲突拒绝。与旧语义兼容的pretty JSON保持原字节，只补建明确缺失的execution策略和归属记录。

恢复记录含来源文件身份、preview摘要、控制项目前后文档；中断后继续原resume命令，不用新的导入输入替换pending意图。保留旧文件和在途任务，不做双向同步、删除迁移或自动切换服务；回退参考运行时可继续使用未改写的旧配置。未知/不兼容格式不静默猜测。

## 验收

- CLI默认预览/API预览等价且不生成投影/控制项目/恢复记录；apply只有匹配preview SHA和revision时执行。
- 缺可选execution策略显式展示补建；已有兼容策略采用且原字节不变；三模板与原必需检查/能力边界保持。
- 源语义或空白变化、旧revision、不同Git根、未知字段/版本、重复tracker、已归属其他控制目录均拒绝；不读取敏感配置。
- 导入发布中断可在重新打开State/新进程恢复，恢复记录保存源身份与before/after；不覆盖冲突、不重写旧注册、不迁在途任务。
- 原F1.2登记/六阶段、旧轻量项目、非editable包与283冻结资源身份保持；完成后安排新的fresh-context结构/维护性审查。

## 进度

F1.3已实现，审查发现的容量兼容P2已修正并源码复核关闭，最终非editable包验收中。`registrations`增加preview/apply，沿用同一_prepare/reserve/finish/resume；import spec与旧项目格式复用现有schema属性。私有执行目录规范化供注册/导入共用。reference边界只补严格UTF8读取及采用文件原始SHA核验，避免接受原runtime无法读取的BOM/UTF16文件，也避免预留后/恢复时偷偷采用已改变的旧字节。

预览绑定控制home、修订、完整规范化定义、源原始SHA及各投影语义摘要，差异使用JSON Pointer。既有execution allowlist按成员集合匹配并保留旧顺序/字节；同一登记以后只改绑定时保留已批准投影。缺失策略在预览中标为create，已有文件标为adopt。仅生成配置，不读platform/credentials，不迁任务、不调用服务。

首次源码定向53项通过（新预览/采用/字节保持、两类编码拒绝、错误格式/根/归属、源变化、旧revision、预留后变化及跨进程恢复、CLI/API一致性）；随后补入目标控制home绑定、策略成员冲突、三个模板分别导入和两开发模板真实旧注册导入六阶段，当前组合定向尚未结束。新证据目录`.ergora/checks/f1-import/`，不与F1.2最终包混用。

预审验收：组合定向72项通过；非editable wheel SHA256`5d5eb60011d69f7e544a665208ae736b260c2ef98ea0b5a9fccdd2aee7629db6`，源码/wheel/开发环境及独立基础环境337文件一致。完整适用回归278 passed、18 skipped、36 subtests passed（`wheel-regression.log`），命令范围同F1.2，PYTHONPATH仅选冻结upstream、没有src。实际fixture包括两开发模板经旧原register→预览→显式采用→CLI保存目录入口→六阶段，后续新登记不影响原runtime里的在途快照。受控command/伪Codex不代表真实模型/外部服务/GPU验收。开始新的fresh-context独立审查；精确两OS CI与推送尚待实施。

独立基础环境CLI旅程通过8次操作（reference info、默认导入预览、带SHA采用、状态、幂等恢复、改reviewer绑定、有效配置及再次状态）；确认采用前没有归属投影，采用后旧文件原字节不变，绑定revision更新且投影继续一致。结果记录`base-journey.json`。当前独立审查进行中，尚未声明F1.3交付完成。

审查发现容量兼容P2：原始紧凑JSON小于1MiB、假设indent2后大于1MiB时，原边界错误地拒绝无需重写的采用文件。新增回归先复现失败（`compact-source-before-fix.log`），再将生成大小校验限制到observed缺失、确实新建的文件；已有文件仍通过原reader上限、源SHA和语义冲突检查。修正后的定向/最终包验收与复审待记录，预审278项不能替代修正后结果。

修正后定向：合法紧凑源可采用/恢复/状态一致、新建超限仍拒绝，2项通过；注册/导入及静态边界58项通过（`fixed-registration-regression.log`）。独立审查者以4个无写入探针复核旧大文件PASS、新建同内容超限拒绝、源字节变化拒绝和语义冲突拒绝，P2源码修正关闭；未提出其他结构/维护性阻塞。最终包及CI/远端证据仍待完成。

最终本地验收（2026-11-03）：修正wheel SHA256`6d1ef44aa2d71988e21930cc7908aa5fb6e398bf057106d8907b3e8e79e5319f`，源码/wheel/两安装337文件一致；`final-wheel-regression.log`为279 passed、18 skipped、36 subtests passed。最终基础8次CLI旅程保持原字节、绑定修订及状态一致。新的[独立结构/维护性复审](2026-11-02-project-import-review.md)通过，容量P2关闭、无未解决源码finding，最终包/安装/基础旅程已由审查者另行核对。接下来提交推送并核对该候选精确两OS CI，再关闭完整F1。

实现/测试提交`62c4d696396942fbad86fc21f56f9e854e3ed4d1`已推送到`refactor/architecture-foundations`，`git ls-remote`已核远端一致。[精确CI41480569812](https://github.com/626619403/Ergora/actions/runs/41480569812)两OS已通过，已按官方HTML核对完整SHA、对应job和安装/冻结身份/回归实际步骤，WindowsPowerShell5.1安装升级也通过；证据为`ci-html-status.json`及原页面。最终独立交付复核进行中。

收口合同对齐补修（2026-11-03）：原JSON Schema正则的`$`可匹配末尾LF，使`local/demo\n`在注册/导入被接受，但冻结执行合同的fullmatch拒绝该tracker，导致登记后无法创建任务。新增两条回归先实际失败（`tracker-before-fix.log`），再在共享tracker.project属性以标准`not/pattern: \\s`显式禁止空白；新注册和旧项目结构共同复用，无新领域分支或冻结修改。两项修正测试通过；需要对新包、源码修正复审及精确候选CI重验。62c候选的279项/两OS CI保留原范围，不套用到补修后。其wheel和包清单已保存在`.ergora/checks/f1-import/accepted-62c4d69/`。

补修安装与基础旅程（2026-11-03）：新非editable wheel SHA256为`4fa5adac91721adfd6e274a544336d492800494b82339658d321ff63d0b9dd63`，源码/wheel/开发及基础安装337文件一致。`tracker-base-journey.log/json`记录独立基础环境8次CLI、原字节保持、绑定修订和状态一致。原审查者已完成schema最小修正及13个独立词法边界复核，两项源码P2均关闭。补修后的完整回归进行中，提交/远端及精确两OS CI待核，不能沿用62c结果。

补修完整本地验收：`tracker-wheel-regression.log`最终为281 passed、18 skipped、36 subtests passed，147.11秒；从已安装的新wheel执行，PYTHONPATH仅选冻结upstream。`tracker-reference-verify.log`确认283冻结文件PASS且未启动runtime。当前源码/测试相对62c仅共享schema和两条参数化回归变化，独立审查的修正结论保持，包/安装/回归证据已交原审查者复核；新提交精确两OS CI与最终远端复核待完成。
