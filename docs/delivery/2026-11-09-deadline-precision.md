# C1 CI 修正：研究耗时的浮点比较

固定基线 `61ccc2cce8bfcc3a46b4a069c78ea660f76063d9`。仅修正 `tests/test_research.py` 中已有超时回归的数值断言；C2 编辑器继续留在工作树，本候选不包含其产品实现。[C1 原交付](2026-11-09-definition-console.md)与[独立原失败记录](2026-11-09-definition-console-review.md)保留。

## 原失败与最小修正

基线自己的 [CI 42612128319](https://github.com/626619403/Ergora/actions/runs/42612128319) 已终态 Failure：Windows 四必要步骤成功，Ubuntu 三步骤中 Native application regression 失败。原日志为 1 failed、1304 passed、84 skipped、36 subtests passed / 838.44 秒；失败只有 `test_wall_deadline_covers_response_headers`，状态已为 `timed_out`，但实际耗时 `29.99999999999997` 不精确等于 `30`。

保留原测试的真实单调时钟起点、真实 spawned 网络进程、实际响应头 started 握手、推进 30 秒、结果等待 10 秒及严格 `timed_out` 状态。唯一修正为耗时使用已有 pytest 的 `approx(30)` 默认数值比较，在此尺度容差为 30 微秒，不引入依赖或调整运行预算/速度阈值。运行时代码、包、CI 配置和 283 冻结文件不变。

独立算术核验 `(226.4 + 30) - 226.4` 恰为原失败数值；原精确比较为 false、近似比较为 true，29.9 仍被拒绝。这只复现 IEEE-754 算术，不声称本地重演官方网络失败。早期固定伪起点的诊断没有成功复现：首次 harness 缺少 spawn main guard，修正 harness 后仍因父端绝对 deadline 与子端真实 monotonic 不同域而在响应头前超时。两次原失败保留，不据此修改产品或改成零起点。

## 实际验证与交付门禁

使用 C1 R4 原非 editable 安装包运行：

```bash
python -I -m pytest -q tests/test_research.py --basetemp=<persistent-check-directory>
```

结果 **11 passed、1 skipped / 11.79 秒**；跳过项因未显式选择专用隔离 Temporal 测试服务，保留原理由。该包 wheel SHA256 `7c122ff9979b224bfbcf67defea1dadf935a6609043039628e2f3431f9c89b63`。本次不重复模型/浏览器/服务验收，不将仅测试修正视为新的产品实现。

[新独立两轴审查](2026-11-09-deadline-precision-review.md)本地通过，DP-D1候选外链接及DP-D2跳过理由已修正复核，0开放finding。精确选择提交、自己的新 CI 和明确 HTTPS 远端身份待取得；原 61ccc2c 的 CI Failure 不改写为成功。

## 精确交付终结

已普通提交推送 `03f1f583f91c6f1b2f35b89ff8d0d513f40c519d`，唯一父61ccc2c，恰七文件。独立按Git对象核435包文件与原R4 wheel/安装相同，283冻结相同，C2产品未纳入。自己的[CI42616678385](https://github.com/626619403/Ergora/actions/runs/42616678385)已Success，双OS七必要步骤全部成功；独立2026-11-09 12:41:08.475411→12:41:09.857455 UTC明确HTTPS核远端同完整SHA，12:41:11.657510 UTC核官方终态。首次In progress与终态分别保留，原61ccc2c的Failure不改写。独立两轴0开放finding，本片精确终结。
