# F9c C1 原训练证据只读：独立需求／正确性评审

日期：2026-11-14。评审者：fresh-context 独立 agent `training_evidence_spec_review`。先读 `AGENTS.md`、[主计划](../PLAN.md)、[C1 原始合同](../plans/2026-11-14-training-evidence.md)、maintainable-project-delivery 及 independent-review brief，再读实际差异、原训练／archive／gate／release owner，最后核作者交付与验收原件。没有继承实现对话；只读产品、Git 和已有原件，仅写本文。未安装、重跑 suite、启动服务、访问远端、执行训练或修改业务项目。

**最终本地结论：需求／正确性通过，首轮验收测试 Host 问题已由最终 r2 实跑关闭，开放 finding 0。** 当前产品、r2 包／安装四 suite、真实 CLI／loopback HTTP／SDK-free、原件保持与收尾、自身原模板均已独立补核；所查维护性无新增 finding，但不替代另一结构轴结论。普通精确发布、完整 Ref 与本片自己的 CI 仍待，不能称全部精确交付完成。前片 C2 的发布／CI 记账不构成本片验证。

## 固定身份与检查范围

基线与本轮 `HEAD` 均为 `2181cc5c6ab92ac01664f8e769298cce350f65a5`，分支 `refactor/architecture-foundations`；对象为未提交工作树。亲读完整 tracked diff，并以 `git ls-files --others --exclude-standard` 核新增内容。

- 产品：`src/ergora/{cli.py,reference.py,reference_training_evidence.py,training.py,web.py}`，其中 evidence 模块为新文件。
- 测试／CI：`tests/test_training_evidence.py`、`tests/fixtures/training_evidence_archive.py`、`tests/test_architecture_boundaries.py`、`scripts/ci/linux-groups.json`，前两件为新文件。
- 本片文档：README、TRAINING、current 架构、PLAN、新计划与交付；另读上一片 preparation-console 的计划／交付／两轴评审／公开证据纯发布补记。
- 相邻权威：`reference_training_context._TrainingProject`、`reference._training_records/_training_process`、`training._project`、原 `dev_platform.adapter.safe_file/read_raw`、Windows bounded reader、原 `perfctl` 全部 archive／gate 算法、`agent_platform.training` 与 `training_executor`、Temporal 纯数据模型及原 evidence-format。

五个产品按上述路径排序，以 `path + NUL + raw bytes + NUL` 连接后的 SHA256 为 **`029d69cb701d116c3d9899cac463dff44938b9d802bcf6b017dde0c805e19604`**。新 evidence 模块 8,455B，SHA256 **`1ffce17c7a6e7747d33e9544f5eade399565f6bf9443eb94a00083feb681580a`**。这些产品与下述 r1 wheel／snapshot／实际安装逐字相同。

首版九件产品／测试／CI 组合为 `04bedeecd11502c2dbf600b451a0326b18117b08238a4b021902f850be2a0b76`。作者修 HTTP 测试后，本轮重算为 `bca645238f08d12e639da8b8f3732cdda651bd31e5aae735b97ee025a345aca9`，唯一不同是 `tests/test_training_evidence.py`，当前 SHA256 `bc1913057c9fe20be3eabdba3db0853c15711b9213bb2771c8ecb3187703b2a4`；没有将 r1 运行改称修后测试通过。

## 首轮 Finding：验收测试的 loopback Host（P2，最终 r2 已关闭）

位置：[test_training_evidence.py](../../tests/test_training_evidence.py#L133) 的 r1 版本；原生产边界 [web.py](../../src/ergora/web.py#L330)。

可达场景：装有 web extra 的最终非 editable 安装运行 `test_no_archive_and_cli_http_share_the_observation`。r1 使用默认 `TestClient(create_app(state.root))`，其 Host 是 `testserver`；原 `TrustedHostMiddleware` 仅接受 `127.0.0.1`／`localhost`，请求先返回 400，未到达新 evidence handler。原 `install-r1/regression-r1/process/stdout.txt` 明确记录此处 `400 == 200`，四 suite 实际 **45 passed／1 failed，40.23s**，monitor 41.853s。

后果：本片的带 web 安装验收与新增 CI 测试失败，不能以源码环境的可选 HTTP skip 作为入口通过证据。没有证据表明 evidence 产品故障，也不应放宽原 Host guard。

最小修正：复用已有 [test_training.py](../../tests/test_training.py#L180) 的 loopback `base_url`、Origin 与 `X-Ergora-Request` headers。作者现有源码正是此修正，本轴已读。最终 r2 安装 snapshot 中该测试与当前源码逐字相同，`install-r2/regression-r1/process/stdout.txt` 明确记录该测试通过，四 suite **46 passed／38.99s**、monitor **40.629s**，没有 skip；据此关闭本项。原 r1 失败与产品 Host guard 保持。

## 产品合同核查

1. CLI 与 HTTP 均进入 `training.evidence`，只允许已发布且选择 training-optimization 的项目。注册配置仍由 `_TrainingProject.registration` 核同项目／control home；原 reader 核原 manifest 原字节、spec／runner／job／gate 的完整 binding。没有另建 registry 或实验账本。
2. accepted archive 路径由选定项目／experiment／完整 evidence SHA 构造，不采用调用方路径。job 原 gate 的字节 SHA 由原 reader 核；archive gate 按原 JSON 内容与 job 内 archive_report 对照，并核 experiment／baseline／candidate／manifest／evidence。该 gate 本身没有独立归档字节摘要，改变空白不能当内容污染失败；源码第二轮相应测试预期修正符合原 owner。
3. evidence、归档 manifest、baseline、comparator 分别核原字节 SHA；baseline 快照与 manifest 的关系由原 `baseline_ok` 核。当前 baseline 适用性另列，旧证据不会因读取而获得当前采用资格。没有调用原 gate、比较器、runner、release、receipt 写入或 Temporal connection。
4. 原 artifact index 只验证规范路径、存在性与声明摘要，原内容继续标记 `not_read`。路径检查复用原 `perfctl.local_file` 与 `safe_file`，后者拒绝 symlink／越界。显式选择必须提供当前完整 evidence SHA，并在原 index 中命中；整个目标文件经 bounded reader 读取并核完整 SHA 后才 UTF-8 解码、拒 NUL、返回 Unicode 字符窗口。offset／limit、16MiB 单件、1MiB JSON 与 8MiB 序列化响应边界可由代码直接追到原 owner；超限走明确失败，没有截断完整证据的成功路径。
5. 原本地 integration ticket 按原命名读取；完整 JSON 内容匹配 project／binding／evidence／schema／kind／automatic_merge 与合法 receipt ID 引用。不存在返回 `None`，未创建 Task、issue 或票据。只报告该 receipt 引用，不重验批准资格；`approval_currently_valid: None`、`integration_verified: None` 和 `runtime_status: not_queried` 与合同一致。
6. 新模块只由 reference 子进程入口消费，内聚归档身份／内容读取算法有明确 owner；CLI／HTTP 共用应用函数。复用原 registration、reader、process monitor，未引入单用通用接口、旁路调度器或另一批准服务。283 原参考不变。

## 已亲核原件与验证边界

私有原件均相对 `.ergora/checks/training-evidence/`；它们是本地 CPU 合同和合成证据，不是真实训练／GPU／质量／性能验收。本轴直接读 result、stdout、stderr，而非仅采用作者摘要：

|运行|实际结果|原 stdout SHA256|
|---|---|---|
|`source-r1` 三 suite|26 passed／9 failed／2 skipped，24.15s；正例 fixture 留有旧 binding 的 negative record，被原 reader 拒绝|`249474bacee62e124fef25154d31d35f267d7799144864b1d8f360c49fc116b8`|
|`source-r2` 同三 suite|34 passed／1 failed／2 skipped，25.44s；追加 gate JSON 空白仍为同内容，失败的是测试预期|`5f58bbe2f852db9a6d2ec90ec8735de3420ac7331345eee2f11add73dd317c70`|
|`source-r3` 同三 suite|35 passed／2 skipped，24.32s；可选 web 段未运行|`eb8a3cf88d988bde2cfc7eef2398d57124a02ac97862aafe75429b4ae54b76eb`|
|`install-r1/regression-r1` 四 suite|45 passed／1 failed，40.23s；失败见上述 P2|`cb1d1a487f47b4bb0e82db9a9676c57646cffcdc660ffe5ecfd370b0eb1f1b09`|

四份 stderr 均为空；全部失败原件保持。亲读新 fixture，确认正例确由原 `perfctl.main(... archive ...)` 生成，并有原比较／attestation 结构，未手写一个自称已归档的目录替代 owner。Windows fixture 仅跳过 POSIX writer lock；这不是原生 Windows 产品实跑证明。

亲读 `install-r1.py`、`source-manifest.json`、安装／校验脚本，并独立重新读取 wheel、snapshot、安装内容、两份 RECORD 和 reference manifest：

- wheel SHA256 **`85b232ca0e5ae98e41749c26b4aa8bc9482d1f0112eb81c4bcc3edc014e160b1`**；573 个产品，全部与当前产品源码、构建 snapshot 和实际 site-packages 逐字相同。
- wheel RECORD 581 行、安装 RECORD 586 行；逐件摘要／大小重算无差异。
- 283 个冻结原件按 manifest 逐件重算一致，产品无 editable 替代；这些身份结论没有把 r1 失败运行变成成功。

首轮待验项曾包括修后最终包／实跑、真实 CLI／loopback HTTP／SDK-free、原件收尾及自身原模板；本轮已取得下述原件并逐项补核。另一新独立结构轴仍按其自身报告裁定；最终普通精确发布、原完整 Ref 与本片自己的 CI 尚待，不以源码推理或前片运行补造结果。

## 最终 r2 安装与实际入口补核

本轮继续只读同片原件，没有安装、重测或启动服务。再次核工作树 Git 状态与产品字节；五产品 SHA 仍为 `029d69cb701d116c3d9899cac463dff44938b9d802bcf6b017dde0c805e19604`。九件产品／测试／CI 组合仍为 `bca645238f08d12e639da8b8f3732cdda651bd31e5aae735b97ee025a345aca9`，全部与最终 r2 source snapshot 逐字一致；进度／交付文档随后补记不改变该产品身份。

直接读取 r2 wheel **`d67ced0f3f65e21db69ee34a113552e9af64413f3384edcb5efe080dc785a98a`**，独立重算全部条目和两份 RECORD：573 产品、wheel 581 条／安装 586 行，全部摘要与大小相符；573 产品同时与当前源码、r2 snapshot、实际 site-packages 和 r1 产品相同。283 冻结文件逐件匹配原 manifest。`setup.json` 的 build／venv／offline install 均退出 0，实际四 suite 使用 r2 解释器 `-I -m pytest`，完整 stdout 与 result 一致为 46 项通过、38.99s，未把 r1 失败改写为成功。

亲读 `native-r1.py`、两版 continuation 和归档 fixture，确认真实原 init／runner／prepare 与原 adapter 本地 job request 后，由原 `perfctl archive` 使用 POSIX 锁生成 accepted archive。这里的比较输入、attestation、job gate／result 明确为合成材料；没有执行 executor，不能称真实训练或质量通过。相同原归档 evidence SHA 始终为 **`cc009ef87e56605b9b970ead7cb9be33fb4d7c5be434217373c6337ddb485ce3`**。首脚本把正确拒绝的 CLI 退出 2 误期待为 1，首 SDK-free continuation 又将整个 site-packages 暴露给 `-S`；原脚本／拒绝 stderr／SDK 断言 stderr 保留。最终 continuation 只从既有原件继续只读，没有重建归档或更换 ID。

最终 `commands.json` 记录 r2 安装解释器 `-I -m ergora` 的四次实际 CLI：完整证据与选中窗口退出 0，错误完整 SHA 与 index 外路径退出 2。亲读成功 JSON、两个拒绝 stderr；窗口是 `notes.txt` 原 33B／22 个 Unicode 字符，offset 2、limit 4、text `窗口 🧪`、next_offset 6。最终 SDK-free 使用仅复制已安装 ergora 的独立搜索根，加原参考源码并实际 `-P -S`，SDK 不存在断言通过；其完整结果与最终 CLI JSON 逐字相等，stderr 为空。没有用仅 monkeypatch SDK 探测代替此次实际 SDK-free 原件。

亲读 `http-r1/{service.py,client.py,steps.json,requests.jsonl,result.json}` 和六个 body：实际 uvicorn 绑定 loopback 原 socket，六次 GET 的客户端与服务端状态、body 大小及 SHA 逐件一致；200 的完整证据与窗口分别与最终 CLI JSON 相等，400 的错误 SHA、index 外路径、NUL 二进制、65,537 字符 limit 均明确报错。实际六条请求均为 GET，零 mutation。超大 artifact、symlink、元数据字节污染、foreign ticket、当前 baseline 漂移及项目身份等由最终安装 suite 的实际原用例补证，范围以各原断言为准，没有宣称重验所有 artifact 内容或统计。

独立重算 `protected-before.json` 的 **14** 件准备原件与 `read-before.json` 的 **37** 件 config／runtime 原件：当前摘要全部一致，37 件文件集合也完全相等。原本地 `request.json` 单列存在；executor started、workflow submission、fence、owner receipt／approval、integration ticket 及命令 marker 都不存在；只读 Git status 为空。亲读 `cleanup.json`，原 process monitor 停止 web 组，最终观察记录原端口 connect result 111；没有借页面请求成功推断进程已清理。

本片自身原结构模板也已补核：`native.stdout` 原 run／原协议命令使用用户授权 Codex 回退；实际 stdin 与保存 prompt 的 **245,299B** 完全相等，SHA **`4096afe20c9ab6f9c533ffb429931e474dbc45d8ec704982dd59ffc0967f92ef`**。从 task 中逐件提取 **12** 份完整 inline 文件、合计 **240,476B**，与 packet-index 的大小／SHA 全部相等；三份祖先资源都完整进入实际 stdin。原回复 approve、44.448s，原 result 与 run 指向文件逐字相等、SHA **`4de644590c23cbd128bb855028afc861c69e08d888341ee5c0d6205355630517`**。packet 含 Host 修前测试和当时进度文档；后续测试最小配置修正与进度补记不追称原模型已重审，也不把自身调用当独立或异后端审查。

直接重算[公开证据](evidence/2026-11-14-training-evidence.json)所引 **54** 份私有原件的长度／SHA，全部相符；失败与成功均保留。另修正本文三处源码链接由本地 `:行号` 格式改成仓库 Markdown 的 `#L行号`，本轮按完整相对路径重新确认文件存在与行号有效。

**最终本地需求／正确性通过，首轮 P2 已关闭，开放产品／验收 finding 0；所查维护性无新增问题。** 普通精确发布、原完整 Ref 与本片自己的 CI 尚待。C2 批准／C3 页面、Temporal 终态、实际集成复验、采用、F9d／B3、真实训练／GPU／质量／性能及原生 Windows 均保持各自未验范围。
