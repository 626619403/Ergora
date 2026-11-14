# F9c C2 精确 owner 批准与恢复：独立需求评审

日期：2026-11-14。评审者：`/root/training_release_spec_review`，本片新 fresh-context；先读原合同及实际差异，再读取作者交付与原始验证产物。基线：`c3c7c3e218e9d2efc89498e8c208bf5981b9a0d9`。

## 范围与当前结论

原要求为按计划持续交付、沿既有 owners 解耦复用、每大项自身与新独立审查、适度测试／guard，并保持业务试用仓库与 283 冻结参考不变。本评审以[本片原合同](../plans/2026-11-14-training-release.md)验收；不把前片 C1 的发布／CI 当成本片证据。

独立检查当前五件产品 `reference_training_release.py`、`reference.py`、`training.py`、`cli.py`、`web.py`，新 release suite／服务 fixture、architecture 名单与 Linux group 5；补核相邻 C1 evidence 测试一行 CRLF 预期修正，按原字节 decode 与生产语义一致。相邻核对原批准 CLI、原 adapter 授权及票据、原 release 客户端、start／cancel checkpoint、runtime lookup、完整 history matcher、immutable writer、项目 revision 预约与 HTTP 本地请求 guard。

- **需求轴：最终本地 approve。** 原 P2 已修并完成最终安装级验证，当前需求阻断 0；发布／本片 CI 单独待验。
- **维护性轴：本次需求检查范围内无另加 finding。** 批准 checkpoint 留在独立 release owner；CLI／HTTP 共用应用用例；原 adapter 继续拥有授权和票据。该结论不代替本片独立结构轴。

## Finding

### P2：ready 前恢复未固定原 receipt 字节与 expiry

位置：`src/ergora/reference_training_release.py:83`、`:200`、`:215`。检查时该文件 SHA-256 为 `86c0c93ff1f6d512fd49af8cf6a0d39aac6920afe060503b3a652a6078225c46`。

创建 `.receipt-attempt.json` 只保存 intent SHA、operation 和 receipt ID。原 writer 已发布 receipt、但 `.receipt-ready.json` 尚未写入时中断，随后如果原件仍具有相同 actor／binding／evidence，却改变了仍有效的 `expires_at` 或原始字节，恢复没有原 digest／expiry 可比。`check_owner()` 用当前原件的 `value['expires_at']` 构造 expected，且 saved ready 为 `None`，因而把变更后的原件登记为首次 ready 并发送。这违反原合同要求的“原字节与原 expiry”“不续期”“漂移拒绝首次发送”。

已对当前 `dispatch` 源码做纯内存反例：checkpoint／receipt／transport 使用内存 seam，不修改文件或网络。原 writer 仅调用一次，保存 `expires_at=2000.0` 后在 ready 前抛出中断；将内存原件改为 `expires_at=9000.0`，其余身份不变，恢复结果保存 ready expiry `9000.0` 且发送一条信号。现有 after-owner 的过期／撤销／公开／actor／evidence 反例只能拒绝无效原件，未检测仍有效但已延期的原件。

最小修正：在调用原 writer 前的创建 checkpoint 中冻结该次原 writer 输入所对应的原始字节 SHA 与 expiry；ready 前恢复也必须与它匹配。ready 应继续表示实际原件已验证落盘。保留原件，不续期、不重建；新增一次 ready 前中断后修改仍有效 expiry／字节的针对性反例即可。

修复源码 SHA-256：`bba8cd011f7aec0a79f596e7898e3daa84afa7f375c8f0394a622c4255b5ab62`。已独立核相对 r1 包的完整修复差异：复用 `_native_bytes` 按原 writer 序列化规则计算输入字节 SHA，创建 attempt 在调用 writer 前记录 digest／expiry；原件、ready、status 均与创建 attempt 交叉匹配。原缺失 receipt 拒绝重建路径保留，新增 future-expiry／raw-bytes 两个真实反例。独立纯内存执行当前实际 checkpoint 函数：正常原件复用原 `2000.0` expiry；延期至 `9000.0` 或仅追加空白均在 ready 前拒绝；三个场景原 writer 均只调用一次。

最终 r2 安装两项反例均通过，已独立读取对应产物：原件仍在有效期内、漂移字节保持未覆盖，创建 checkpoint 保持原 digest／expiry，ready／signal attempt 均不存在，service signals 为零。**P2 关闭。**

## 已核行为与证据

固定 start 摘要、完整 run、完整 evidence、actor、operation UUID 与项目／注册身份均进入意图；原批准 CLI 的 phase／binding／evidence 检查和原 release 信号被复用。phase 与 release 的连接各由完整原 spec、固定 run、start memo 验证。发送前重读 C1 原证据、baseline／fence 与完整 spec；signal attempt 在原 signal 调用前落盘。已有 signal attempt 的显式恢复走完整原历史匹配，不重新调用原批准 writer，也不要求原 manifest／runner／baseline／archive 仍在。原缺失 receipt 的创建 attempt 会阻止重新 mint；这一点不消除上述仍存在原件的漂移漏洞。

状态区分本地记录、投递、授权与集成；CLI mutation 需要 `--confirm`，HTTP mutation 需要严格布尔 `confirm: true` 且复用本地请求 guard；requested 退出 0、prepared／unknown 退出 1、输入／运行错误沿通用退出 2。

已读取原始运行产物，没有新跑昂贵 suite 或修改安装：

- `source-r1`：原 180 秒 monitor 停止，`cancelled/-9`；不能作全套成功。
- `source-r2`：修后 release suite 原 stdout 为 `23 passed in 205.16s`，result 为 `succeeded/0`；该结果属于上述 P2 修正前产品。
- `install-r1`：独立只读重算当前源码产品、wheel 与安装内容一致，574 产品；wheel RECORD 582 行、安装 RECORD 587 行逐行哈希与大小一致；283 参考逐件匹配 manifest。noneditable wheel SHA-256：`9db0b643eddfdcd20e8e088ebe57b7c4b3c2c21f378fe150112a695d629f66e6`。
- `install-r1/regression-r1`：六 suite 原 result 为 `succeeded/0`、stdout 为 `80 passed in 445.97s`；仍属于 P2 修正前身份，不能代替修后验证。
- `native-r1`：已读取实际 CLI／loopback HTTP、原 worker 创建的集成票据及 lost-ack 原始材料；验收脚本在读取 `integration_ticket.automatic_merge` 时失败，实际字段为 `integration_ticket.record.automatic_merge`，原失败 `KeyError: 'automatic_merge'` 保留，不能作完整旅程成功。cleanup 显示 Temporal／worker／web 均已收尾，7233／web 不再监听。合成 archive 不代表 GPU 训练、质量、性能、真实集成复验或采用。

后续已只读核 `native-continuation-r1`：它继续同一 Temporal DB、同三 run，不重新 start／批准／发送，只修正私有验收的 ticket envelope 预期。独立离线解码三份完整 history 并重算其 SHA，alpha／beta／gamma 各恰一条完整 release（均 event 35），完整 start input 与原 spec 一致；run 与 attempt 一致，receipt 字节 SHA／expiry 与 ready 一致，原 outcome 均为 `INTEGRATION_TASK_CREATED`。24 件准备原件、105 件读取原件逐件哈希保持；SDK-free 原输出 requested；六次实际 HTTP 状态为 200／400／400／200／200／200。continuation 的 result 为 passed、cleanup 无残留监听。这完成 r1 原旅程的验收尾段，仍属于上述 P2 修正前身份，不能传递为修后验收。

已读自身原模板实际结果：原 structure-review 模板的运行 `02242b1bc43a49eba8cceb6c661ffac3` 返回 `request-changes`，原回复同样指出 ready 前的 receipt digest／expiry 缺失。它是自身审查证据；本 finding 先经独立源码检查与纯内存复现后才读取此回复，两者不互相替代。

修后 r2 已完成以下独立只读复核：

- `install-r2`：当前 574 件产品与 noneditable wheel／安装逐字一致，两 RECORD 582／587 行逐行哈希和大小正确，283 冻结参考匹配原 manifest；最终 wheel SHA-256：`173be7d224743fa85cf8992820e86ab181dab6e1e6680a5cb803a49230ff6617`。release 源码仍为上述 `bba8cd…`。
- `native-r2`：原 result 为 passed／70.482 秒。再次离线解码三份完整 history，三个固定 run 各恰一条 release、均 event 35；完整 start input、intent／attempt／run 和实际 payload 一致，receipt 原字节 SHA／expiry 与创建 attempt 及 ready 均精确匹配；原 outcome 均为 `INTEGRATION_TASK_CREATED`，原票据 automatic_merge 为 false。24／105 件原件逐件哈希保持、六次真实 HTTP、实际 SDK-free 状态读取及三进程收尾均通过。依旧只证明合成 archive 上的真实本地控制链。
- 自身原 structure-review 模板运行 `878979bbad26408aa9cdcc8ac60f27c8` 实际返回 approve；15 份完整文件／281,510B，53.813 秒。已直接读取原回复和候选输入摘要，包含修后 `bba8cd…` 产品；原回复明确 r1 成功不等于 r2 验收，未将后续 CI 称为通过。
- `install-r2/regression-r1`：最终包中以 `python -I -m pytest -v --tb=short --durations=15 tests/test_training_release.py tests/test_training_evidence.py tests/test_architecture_boundaries.py` 执行；原 result 为 `succeeded/0`，stdout 为 `49 passed in 248.18s`（monitor 250.292 秒）。包含修后 release 25 项、evidence 10 项、architecture 14 项。未把 r1 的 start／cancel／web suite 重称为 r2 已重跑。

## 证据引用补核

已只读补核[公开证据清单](evidence/2026-11-14-training-release.json)：初始 87 条引用及随后追加的 3 条 CI collection 引用，共 90 条路径唯一、文件存在，逐件字节数与 SHA-256 均匹配。范围含原源码检查及中止、r1／r2 安装与 suite、两轮自身原回复、r1 私有脚本失败及同 run 续验、最终 r2 原 history／HTTP／SDK-free／收尾；不把历史范围提升为修后验收。清单的最终包、49 项、原旅程 scope 与本报告已核事实一致。

九件 C2 产品／测试／CI 当前文件逐件匹配 packet；重算其映射 SHA-256 为 `9485aaaec5042b912fe1847d15b3babcb6b78610a364736583827d4bb5b3b150`，与公开清单一致。相邻 C1 换行预期修正文件 SHA 也匹配。公开清单保持合成 archive／本地控制链、投递不等于授权／集成／采用、当前用户信任范围、无真实训练／质量／性能验收等限制，且发布为 not_committed、自己的 CI 为 pending。

新增 collection 三原件的 request 明确 `--collect-only --ci-group 5`，result 为退出 0，stdout 为 `414/1867 tests collected (1453 deselected) in 4.39s`；只证明收集与分组，未执行测试，不能作为 CI 成功。本次仅补证据状态，不更改本地 approve 或发布／CI 待验结论。

## 剩余验收

本报告检查范围内无开放需求 finding，最终本地需求验收通过。终读交付／主计划已区分最终 r2 的 49 项与修前 80 项、保留原失败，并明确精确发布／自己的 CI 待验。普通精确发布、完整 Ref、本片自己的必要 Windows／Linux CI 与原结构轴终核在后续发布检查中独立验收。本报告不将本地通过等同于整片精确交付完成，不关闭 C3、真实 F9d／B3 或 G1。
