# C2.1 Forge 源身份维护独立终审

日期：2026-11-14。评审者：fresh-context 独立 agent `forge_source_identity_review`，未参与实现。先读原始要求、AGENTS、计划及实际差异，再读作者交付；按 maintainable-project-delivery、codebase-design 和 code-review 两轴规范核查。

## 固定范围与身份

基线为 `f4da08b9ff7c1dae92222677a43d8b56b87c78b0`；审查时分支为 `refactor/architecture-foundations`，候选为未提交改动。初版七文件快照 manifest SHA256 为 `6b4bad6178e058260794cf4add8d0693ac901dc03d7c0f14f4e179b8680b4020`；最终七文件快照为 `0bd91926c679334f5d16a91ce0c681ab136d565c8fca02304ffac6027fd8bca1`。逐文件身份与当前文件相符，两版之间只更新本片计划、交付的实际结果和状态。

完整审查文件为：

- [kernel.py](../../src/ergora/kernel.py)、[test_agents.py](../../tests/test_agents.py)、[后端手册](../AGENT_BACKENDS.md)。
- [PLAN](../PLAN.md)、[本片计划](../plans/2026-11-14-forge-native-admission.md)、[作者交付](2026-11-14-forge-native-admission.md)、[接缝设计调查](2026-11-14-forge-native-seam-design-review.md)。

另核相邻调用者 `tools.py`、组件目录中的 pin、固定 `data/drivers/forge.py`，以及原 Forge pin 下的 agent command、普通 turn／重试、judge、policy、agent／timeout／hook 脚本和 detached runner 源码。`processes.py`、driver、组件与依赖没有本片差异。范围是补齐既有源码门禁，完整 native 子模板、权限隔离和新调度均不在本片实现范围。

## Spec／需求合规

**通过，开放发现 0。**

`kernel.py` 第17–24行的同一私有算法由 `available` 第46行和 `_call` 第90行消费；Git 检查同时覆盖 `src/forgekernel`、`scripts`，明确启用全部非忽略 untracked 文件。实际脚本消费者包括 `agents.agent_command` → `agent-claude.sh` → `timeout-run.py`，以及 `AgentPolicy` → `agent_policy_hook.py`，不是没有执行者的目录扩张。

`available` 第50–51行只在 commit 正确且源码清洁时返回 pinned；`tools.py` 第99–100行将 unsupported 转为 blocked。`installed` 继续表示原导入位置检查。`_call` 第91–94行在请求文件、运行状态及第112行 driver 启动之前拒绝错误 pin 或脏改；plan／prepare／run／status 都进入同一执行入口。两份保留的实际拒绝记录均为 failed，无 operation、campaign 或 native 目录。

Forge pin 仍为 `5030503d3ff71851aa34c14b9caf13ebfa9d9a78`，原安装在只读复核时清洁。global_config 不在新路径检查内，`kernel.create` 第153–154行与 driver 第21–24行仍负责原 campaign 摘要；既有配置漂移回归实际通过。未新增配置取值限制，未改变原 campaign、unknown 对账、process 或 candidate-only 所有权。

公共手册明确源码检查不证明解释器依赖、CLI、环境或 OS 隔离。接缝报告明确区分静态设计、候选 CLI 控制和实际运行，完整材料／权限／预算／停止仍开放；未将本片、只读推理或自身模板成功升级为完整 C2。

## Standards／可维护性

**通过，开放发现 0。**

- 新函数实际只归属一个生产文件，调用者是该文件的两个原入口；这是在同一 Module 内集中身份算法的合理私有实现，不以“两个生产文件复用”包装其价值。没有新增浅层转发、registry、backend 框架或第二账本。
- 新增清洁条件保护可达的 tracked 脚本漂移及 untracked 运行时代码；commit 校验继续保护错误 pin。Git 失败由既有异常出口处理，查询有界。没有不相关断言、不可达分支或多余参数门禁。
- 第238–260行新增一个双参数行为回归，分别覆盖旧门禁的两个静默遗漏。清洁前像、doctor 拒绝和 driver 前无副作用分别保护不同事实；测试不复写 Git 命令。沿用原显式 Forge checkout／Python 接口和独立 clone，没有引入新 fixture 框架或机器路径、模型默认值约束。
- global_config 的有效配置范围及原测试保持；固定路径针对所选 pin 的真实源码布局，不扩展到可配置 task、外部包装程序或全部工具链。

## 实证核对与限制

1. 基线隔离 `kernel.py` 与 Git 原件逐字相同。两项新用例在该基线确实失败，失败点是旧 doctor 返回 pinned；不能把这两条 red 另称基线 prepare 的运行证据。新源码日志为 5 个 Forge CPU 用例通过。
2. 安装原始 stdout／result 为 23 passed、9 skipped，pytest 17.09秒、监督18.845秒；跳过项为3个未选 mini SDK及6个Windows专属用例。没有将跳过计入通过。
3. 独立逐字核准 551 个 tracked 产品文件与 wheel、构建源码、当前源码、安装副本的集合及内容一致；wheel 559 行和安装 564 行 RECORD 的哈希、长度均正确，283 冻结文件及其 manifest 与基线保持。wheel SHA256 为 `27b75368f2bae2def2371c8f1a129428c01a3be9a9dabf05902436a01fe5fdb2`。
4. 只读执行候选的精确 `_source_identity` 算法：原固定安装为 clean；现存 tracked timeout 脚本改动 clone 和 untracked Python clone 均为 dirty，三者 commit 均为既定 pin。没有修改这些源码或启动 driver。
5. 自身原结构模板的两次输入均核全三文件50,239B及三份继承资源，并与实际 input／stdin逐字对应。Claude run `7383a3cae113413aa91a42ea6bc610ff` 在240.495秒超时，无判词；Codex回退 run `251ab86208114773a7b0c2bb053c6861` 在37.233秒成功并 approve，result SHA256 为 `237a6a09291bd6b49809f8eec90cf1f408819b6619eaccd89fb2e2c27d91e6ac`。原判词准确限定为三文件文本审查，本独立评审另核其未读取的组件 pin、driver 与验证原件。不声称异后端审查成功。
6. 简单 Claude 推理的原输出1,697B、SHA、成功字段与5.275秒回执相符；bwrap 原错误也与交付一致。两者与上述结构模板结果分开保留。`git diff --check` 通过。

独立核对摘要保存在本片私有 `independent-review-r1` 审计原件中。本评审未安装、修改生产源码、提交或网络写入，未重跑昂贵测试、模型／GPU／完整 native 旅程，也未读取认证配置。

## 出口

C2.1 源码维护、现有本地验收和独立两轴审查可关闭；阻塞发现为0。普通提交／推送、精确远端身份与本候选自己的 CI 尚需另记，不能借本报告提前关闭。完整 C2 的父合同、全部工作会话与附件继承、权限交集、跨恢复预算、真实停止及外部同候选评价，以及真实训练 B3，保持原开放范围。

## 同片发布补核

2026-11-14，独立核准普通提交 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`，唯一父提交为上述 `f4da08b9ff7c1dae92222677a43d8b56b87c78b0`。改动精确包含已审七文件及本报告，共八个 Git blob；逐项核其对象身份与内容。产品、测试、手册和接缝报告与最终已审快照相同，PLAN／本片计划／交付仅回填实际独立通过状态，未扩大完成声明。新 F8-H2 的两份文档未进入该提交。

从该提交直接读取的551个产品与原已测 wheel 完整集合及字节相同；构建源码、当前源码、安装副本、两份 RECORD 和283个冻结文件再次核准。未重新安装或运行模型／昂贵测试。

普通 push 原回执退出0，随后作者 SSH `ls-remote` 原 stdout 将 `refs/heads/refactor/architecture-foundations` 完整解析为同一 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`。本评审只核保留原件，没有另发网络探测。精确发布补核通过，新增发现0；私有 `publication-audit.json` 保存八对象及发行包、push／Ref原件身份。本候选自己的 CI 尚未核到终态，继续开放；以上补核不关闭完整 C2 或 B3。

## 同片自己的 CI 终态补核

2026-11-14，独立补核 [Portability run 43471215671](https://github.com/626619403/Ergora/actions/runs/43471215671)。官方第六份 run HTML 原件明确为 **Success**，其提交链接是完整 `a0a42ba009bdcd541c9ee42d11838db835e0dcd3`，分支为 `refactor/architecture-foundations`；该原件213,222B，SHA256为 `ea04ed3bd85d9322671b72d69784050d27e182ba4163907250bd7ba30e051b27`。

评审使用独立 HTMLParser 直接提取原页面，不以作者汇总为判据：从官方 `job_groups_batch` 原 JSON 核八个 job 的 ID／名称／run 路径，再逐个核最终 job HTML 的 `succeeded` header、`data-job-status=completed` 和实际步骤。以该提交内的 workflow 及六组配置核必要步骤集合，结果为：

|范围|job 数|必要步骤|原件结果|
|---|---:|---:|---|
|plan|1|1|读取显式测试组成功|
|Linux Python 3.11 六组|6|24|各组构建安装、reference 身份、应用回归、观测上传全部成功；回归139–266秒|
|Windows Python 3.12|1|5|上述四步及 PowerShell 5.1 安装升级全部成功|

八个 job 均 completed／succeeded，三十个必要步骤均 `success` 且带 job-completed 标记；三十条日志路径非空、唯一，逐项包含完整提交 SHA、对应 job ID 与 step number。Windows 回归原时间为 UTC 2026-11-13 17:17:57–17:34:00，共963秒；随后 PowerShell 5.1 阶段17:34:00–17:35:04，共64秒。

最终九份 run／job HTML、原 batch JSON，以及五份较早 run 和四份较早 Windows HTML，共十九份 HTTP 原件的200状态、URL、实际大小与 SHA256 均与收据一致。较早 run 五份仍为 In progress，较早 Windows 四份及旧 batch 的 Windows 仍为 in_progress，未改写成成功；终态分别依据第六份 run 和第五份 Windows 页面。逐项独立提取结果与作者终态汇总一致，私有 `ci-terminal-audit.json` 保存详情，新增发现0。

本补核未发网络请求，未读取日志正文或下载 artifact archive，未运行模型、安装或测试，也未将后续 H2／H3 工作树纳入本候选。C2.1 精确提交自己的 CI 与发布验收可关闭；完整 C2、B3及后续 slice 的各自验收范围保持不变。
