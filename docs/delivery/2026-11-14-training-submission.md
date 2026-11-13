# F9b2 已准备训练实验的提交与对账

日期：2026-11-14；基线 `106481a80abfd168f5b45fbba7381063505239d0`。[计划](../plans/2026-11-14-training-submission.md)／[需求审查](2026-11-14-training-submission-spec-review.md)／[结构审查](2026-11-14-training-submission-structure-review.md)。产品及最终本地出口通过；修后安装、真实 CPU 控制流程、页面、自身原模板和新的独立两轴已验，开放0／0。精确产品 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34` 已普通推送、完整远端Ref一致，自己的CI `43511152711` 八job／30必要步骤成功且获原结构轴终核。下列各轮证据保留其原身份，不能相互替代。

## 行为与所有权

`ergora training submission/start/resume-start`、HTTP 和训练详情页共用 `training` 应用 Interface。首次操作确认已准备 manifest SHA；原意图冻结项目 revision、home、registration／execution、原 spec／manifest／baseline／可信 runner 与文件摘要。原 Git 提交、comparator、当前 baseline／runner、无 job／fence 由预检核验。短 DB 预留不跨 RPC；原非阻塞文件锁保护该操作。

原 `perf_temporal.client.main` 继续拥有 REJECT_DUPLICATE、FAIL 和 maximum_attempts=1；独立进程局部包装 connect/start，在实际发送前持久 attempt，加入原意图 memo，保存实际 run 回执。一旦存在 attempt，恢复仅查询原 workflow 并固定实际 run，核完整原输入和 memo；NOT_FOUND 仍是 unknown，不能清 attempt、换 ID 或重发。当前来源随后变化不影响既有发送的冻结身份对账。原 reader 与预检共用 `_training_records`，status 与恢复共用 runtime `lookup`；未复制训练调度、实验表、job／fence 或批准。

页面默认仅读；当前详情和原意图各自加载。坏条目仍能读取、确认和恢复旧意图，当前来源错误保留；双击、切项目、换详情及迟到回复各按自己的生命周期处理。Linux／WSL2 可提交／恢复，Windows 原生仅读本地提交记录；离线读取不要求 Temporal SDK。CLI 的 start／resume-start 只有 submitted 退出0，未确认／拒绝退出1并打印原 JSON；观察命令读成功的退出0不等于提交成功。

## 验证与保留的失败

|候选／检查|实际结果与范围|
|---|---|
|source-r1|58项：50通过／8失败，98.50秒。只读 Service 替身缺 SDK `config.identity`；补替身，不修改产品迁就。|
|source-r2|1通过／1失败，10.57秒。RPC 原状态码未保留；由 owner 保留原 RPCStatusCode 后修复。|
|source-r3|新增11＋原 runtime15，共26通过，114.99秒。真实 SDK／Service 替身，不是真实服务旅程。|
|r1 noneditable|565产品／两 RECORD／283；wheel `2ca3d370ca3135d73a390cf34d489d2f15d68e76d5dcaba7b30213de2302f5b9`。六 suite 65通过／4平台跳过，154.87秒，受控156.676秒。|
|r2 构建|未运行回归；大输入测试初稿尚未跨聚合边界，在执行前更正并重建 r3，不能记作 r2通过。|
|r3 noneditable|565／两 RECORD／283；wheel `d912e55903fe07442f6f9277c5aba3c1ef76ec1066fb4c5d09b8269d02b72c69`。submission12＋reference6＋architecture14，共32通过／95.27秒，受控97.040秒。包含近1MiB来源生成超过1MiB意图的真实 SDK 回归。|
|r4 noneditable|565／两 RECORD／283；wheel `70059072867a48bcc46f5fbbbf7cdd4a5cf7053a2bbcfe9490ce999d82aa1378`。submission13通过／95.02秒，受控96.905秒；覆盖 status 并发读序，尚不含随后 load 补读。|
|r5 noneditable|565／两 RECORD／283；wheel `434ff7aa2fb5937501cf4d725be81e0487700e299020726854803af0d3aeccab`。并发两交错、原单次发送、CLI／HTTP 三定向检查通过／21.99秒，受控23.816秒。最终包读取四份原回执一致，不接触 runtime。|
|r6最终 noneditable|565／两 RECORD／283；wheel `d71a44f394325ae5fce08ab36f4e6f3830b34fd1cecca9a324d1f6196409cd5a`。仅CLI退出码与原失败场景断言变更；lost ACK／超时恢复、两冲突和健康CLI／HTTP共5项通过／55.86秒，受控57.627秒。|

原需求轴复现“当前 detail 错误挡住恢复”和合法大 manifest 意图不可重读；结构轴独立复现容量，再实证迟到 detail 覆盖 RPC 错误。修为独立面板／冻结确认资料、单源保留1MiB且聚合意图单独16MiB并在写前核可重读、仅 not_recorded 随来源更新。自身模板发现 status 完成记录读取顺序，结构轴又实证 load 初读无意图后看到新 child 的竞态；修为完成记录先于 attempt、仅发现 child 时重读 intent。一个定向回归覆盖两交错，结构轴另枚举550个合法发布顺序并保留真正孤儿拒绝。最后自身模板指出 CLI 未确认／拒绝仍0退出，现按原任务命令约定修正并扩展已有失败场景。各原始 finding／失败保留在原报告及私有原件，修后结论逐项补核。

## 原生 CPU 与浏览器

初始 r1 真实服务完成正常 start，以及真实服务已接收后由私有 helper 扣住 ACK，再按原 run／完整输入／memo 恢复；helper 没有伪造服务接收。另一真实 lost ACK 在 r3包产生，随后故意移走当前 spec，验证页面仍可读取冻结原意图。初始驱动等待浏览器 marker 600秒超时并停止，失败与原 SQLite 保留；r3 页面当时的两个操作因服务已停返回连接错误，没有把它们记作成功。

后续驱动重开**同一 SQLite 和原 ID**，无 reprepare。r4 页面在当前 spec 仍缺失时按原 SHA 找回同一实际 run；原先未有 attempt 的第三实验已保存 prepared 意图，页面显式确认原 SHA 后继续一次提交。错误 SHA 未发送 POST，两个双击各仅一次 resume。恢复 spec 前后 SHA 相等；22份原准备记录逐字保持。

|实验|原 history 事件数|原控制 Outcome|原执行器收集|
|---|---:|---|---|
|正常提交|254|CANCEL_UNCONFIRMED（队列加执行寿命到期）|CANCELLED|
|实际丢 ACK 后原 ID 恢复|254|CANCEL_UNCONFIRMED（同上）|CANCELLED|
|当前 spec 缺失时页面恢复|178|CANCELLED|CANCELLED|
|prepared 页面继续|46|CANCELLED|CANCELLED|

四个 history 的完整原输入、意图 memo、固定实际 run 与服务中每 ID 唯一列出运行均已核；原 status 查询与原 SDK Outcome 一致。四个作业均没有 started.json、训练命令执行为0。前两个控制已终态，后来原 cancel CLI 退出1，原错误回执保留；后两个 cancel 退出0。前两个控制负结果没有因后来本地收集而改写为已确认取消；monitor 的 -9 也只说明验收服务收尾，不能证明外部训练停止。

浏览器另延迟真实 submission GET，在切项目后放回，旧回执没有覆盖新项目。迟到 resume 检查重放同一真实实验早先的 unknown GET，再延迟实际后端读取既存回执的 POST；切项目后原回复不渲染，无新 start。首个 route 探针因 helper 提前 unroute 失败，保留原件，按已处理完 route 再移除后通过。页面在1440／960／390宽度均无整页横向溢出，实际截图经查看，长 SHA／原结果与操作区可见。r4页面 JS 与最终源码同 SHA，后续 owner 的 load 补读和 CLI 退出码另以安装回归验证，不冒称一次全新 r6 原生旅程。

原生／Web monitor 均完成；7233及三 Web 端口关闭，两个浏览器 PID 已不存在，没有匹配验收执行目录的训练 runtime 残留。浏览器 CLI 的错误配置路径和旧 ref 操作也保留为验收 helper 失败，不算产品通过或新的产品缺陷。

## 自身模板与后续

使用已安装原结构审查模板，18份完整文件及全部祖先资源实际进入 stdin。r1成功调用83.645秒，request-changes，指出 status 读序；r2成功调用62.275秒，request-changes，指出 CLI 退出码。两项均接受并修正。最终 r6 包的原模板完整18文件／259,686B调用成功68.027秒，approve；实际stdin与全部祖先资源核相等，原结果SHA `54bdc7415d79849a477e579fa944478f8357eaddd94d438a8475fe51124aca50`。中间一次私有helper复制了不存在的配置路径，在模型调用前失败，原件保留，修正指向原配置后新目录执行成功。使用用户授权 Codex 回退，原 Claude 超时沿既有证据保留；没有异后端成功主张。

本片不包含 baseline／runner／prepare 控制面入口（F9b4）、取消／停止对账（F9b3）、原 evidence SHA 批准（F9c）或真实 GPU 收益（F9d／B3）。真实原生 CPU 只证明提交与恢复控制语义，没有运行模型、MLflow、GPU、统计性能比较或采用候选。普通发布开发分支，不自动合 main。

[公开精简证据](evidence/2026-11-14-training-submission.json)记录候选轮次、原run／history摘要、页面、自身实际调用及精确发布／CI身份；私有完整stdin、响应、服务数据库、构建和进程日志不入库。产品组合SHA `68a14b81ef3ad8685a7a4aa7b80ee6d134c3706b2fa610f3b0897773418a36bc`，原两轴已独立核最终565包／两RECORD／283、分轮安装成绩、四原history及负结果、18完整文件／祖先stdin、页面和收尾，开放0／0。

## 精确发布与自己的 CI

普通发布产品为 `0d9c0a7a2e0c7d107f3a832fa9492a452df71f34`，唯一父提交为上述基线。原结构轴已按不可变 Git 对象核 24 个变更 blob，逐字匹配冻结清单；r6 wheel 的全部 565 个产品文件也逐字匹配该提交。完整 baseline→candidate 空白检查通过，普通推送后的完整远端 `refs/heads/refactor/architecture-foundations` 等于该 SHA。后续 F9b3 工作树不参与本候选验收。

本片自己的 [Portability run 43511152711](https://github.com/626619403/Ergora/actions/runs/43511152711) 终态为 Success：plan 1 项、Linux 六组各4项、Windows 5项，共八job／30必要步骤全部通过。Windows 原生回归、PowerShell 5.1 安装升级及上传均已终态成功；各组构建安装、包内参考身份和回归／上传也均有原完成时间。新增 submission suite 位于候选原 group5。

原结构轴核 11 份官方 HTTP body／receipt，包含候选绑定的初始 run、UI job 映射、第五轮终态 run 和八份 job HTML，均200且原摘要一致；30份原 log 路径全部含完整候选 SHA／check ID。终态 run body SHA `db14edd48c94bb4d7243f05a43c32dc8d69fc67d4a4c0bb727ebf8e67cb5fb87`，Windows 第四轮 body SHA `ad52756aafc4251cb4c48d1a5f0105c7e6bff683c9ae7622076fb1a1cb56d784`。早期运行中样本及原测试／helper失败保留；没有下载 REST 日志或产物归档，没有将 CI 通过扩展为 Windows 原生提交、GPU、性能或外部作业停止能力。

精确发布、自己的必要 CI 及原独立结构轴终核通过，无剩余必要 CI 项；本节只补 F9b2 状态，不改变已验产品，也不关闭后续片。
