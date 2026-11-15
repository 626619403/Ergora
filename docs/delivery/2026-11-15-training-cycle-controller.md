# Q4.2c：有限训练循环控制器逐步交付

日期：2026-11-15。需求／边界见[准备草案](../plans/2026-11-15-training-cycle-controller.md)，具体决策见[c0.1合同](../plans/2026-11-15-training-cycle-controller-contracts.md)。kernel 专家继续保留在 v3 路径；原实验、算法／模型／数据、比较门禁、单次 start／launch、独立人工 release 与 283 参考文件保持。

## 准备审查与源码调查

准备草案已获新的 fresh-context 独立需求／维护性两轴 approve／阻塞 0／0，仅许可进入 c0.1；不认证后续字段或产品。调查基线固定 `ac86043d9e11983750bf63b90c0dfcbeea05ea41`，30 份相关源码／schema／native delta 的完整 bytes 共 414,552B，均与该 commit 相同。ignored `training-cycle-controller/contracts-r1/source-manifest.json` 的 SHA256 为 `18c3ef33ccddee87b369b0ddf4996cba946d802e365e1d81a40b2e5eb4ffb393`。此时该前置固定发布已独立通过，自己的 CI 43684533043／attempt 1 仍 in_progress；本片未改产品或测试。

实际沿原授权、start、worker 最后创建、execute／native 最后 gate、唯一 reaper、完整 evidence／Workflow phase、rounds 索引读取，发现普通 schema1 授权没有自动同意、总 Workflow 尚未注册、completion 不核实际 phase、失败 gate 无可信细分类、索引完整嵌入且项目漂移会阻断新采集。具体合同逐项给出最小已有 owner 与原件兼容方案。

本地实际 binary `--version` 为 CLI 1.9.1／Server 1.32.0／UI 2.54.1，`start-dev --help`、原 service argv与该版本官方默认限制均已读取；没有启动新服务或探测任意远端配置。官方常量原响应 HTTP200／170,266B／SHA256 `3fdabe4ec1649bd11b473966e522be18905a6394f1255fd4580b369353e1dd67`；官方 limits 页 HTTP200／57,924B／SHA256 `825fa05319ea71574f99169a75b3ba61a058a8e38556a405ceb41a83b9cad536`。二者原件及请求来源保存于 ignored `contracts-r1`。

## c0.1 当前决策与待验收

提出出生式 schema2 明确自动同意，保留原 schema1／旧 owner 的观察；总投递 intent→attempt→receipt 与完整 history／memo 对账；per-round binding 归原 start；父 stop 可见拒绝、持久化、共享准入排空与原子树回收分别观察。新动作使用原 owner／锁和 SDK 用例，不复制原执行器，不新增本地可变轮次状态。32 KiB 传输、原 10 MB完整输入／索引和 history 上限分别处理；只有原 accepted archive＋实际 phase＋durable stop＋原索引允许继续。

具体设计尚待静态核验及新的 fresh-context 两轴审查；c0.2a／b、c1、公共交互和新可信CPU示例均未实施。普通 schema1 的 `cycle-authorize` 不能执行整个循环；当前没有可宣称通过的自动循环、真实训练／GPU／质量或收益结果。

## c0.1 独立R1与r2修订

新fresh-context reviewer对固定r1两轴request-changes，唯一阻塞R1：不同queue／Worker配额不能隔离原async adapter的同步registry／State／文件阻塞，且原表把stop配额留到公共交互，晚于自动派发。原报告12,178B／SHA256 `da3ff58387b32be95ae0d6d42aab71ba2a6ef5f0d103532f2eac7a600cdafb48` 保留其r1身份。

r2已明确原training-budget-worker与新training-cycle-worker是不同PID／event loop；新进程的全部业务操作在独立受监管子进程，非阻塞loop注册总Workflow和独立配额stop Worker。实际运行入口／queue／取消验收上移到c1.0，先于自动派发；c2只补公共交互。待原reviewer复审，不将文档修订记作产品或持锁取消已通过。

另一个Q5.2a测试维护片独立处理已登记的提前平台skip／一行文字断言，不改变本合同或30份产品源码；其实际范围／验收另记，不混入本片设计身份。

原reviewer已对固定r2复审，需求／维护性两轴approve／开放0／0，R1在设计层关闭。r1原文保持逐字前缀，最终报告16,915B／SHA256 `4f444b59a6e1a338f11f0a41b0780caf151810531070a3635602acca8dada317`；五份固定输入／30份产品和191个本地目标已独立核验。真正分离PID／loop、锁／fsync阻塞下SDK父取消及并行通知仍归产品验收，未预记成功。下一片可按合同进入c0.2，前置c2自己的CI门禁继续独立处理。


2026-11-15 接续状态：前置ac86043自己的CI43684533043／attempt1现已终态七job成功／Windows六个历史夹具setup错误，原reviewer已核失败归属。Q5.2a仅测试接续，自己的CI和独立终核闭合前不进入本控制器产品实施；本片仍只有已独立批准的具体合同。Kernel专家保留在v3路径。


## c0.2a 准备计划与纯文档同步

已将下一片细化为[出生同意／父停止计划](../plans/2026-11-15-training-cycle-admission.md)的a1–a6；新的fresh-context设计审查两轴approve，开放0。五份纯Markdown记录已普通发布a10e69389e228d311df56bad182b9798f4ca236d，parent e09fd60，五blob／194个暂存引用／完整SSHRef同一；原设计reviewer固定发布两轴approve／开放0／0。其报告原10047B前缀完整保持，追加后12671B，SHA256为18ae0795b9ff18d91b3aaa2b23d4a29c5c1f680898b906999235b663ca1e5d61。产品／测试／脚本／CI／依赖未改，a10沿既有Markdown过滤，不称新产品CI成功。

Q5.2a自己的e09/run43688128824仍待终态与其原独立终核；本控制器产品继续未实施。准备调查明确了普通temp-fsync/link与stop先可见O_EXCL的不同语义，并把阻止schema2经旧三字段binding派发列为a5共同关闭条件；不以设计批准代替真实竞态或原子树停止验收。Kernel专家保留在v3路径。
