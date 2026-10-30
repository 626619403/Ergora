# 多agent训练效率优化套件
研究与版本日期：2026-10-26（新加坡）。目标环境：云端Codex模型＋现有Linux训练集群；重点H200上的PyTorch/DeepSpeed/Megatron、VLM/VAE/DiT/动作模型。

## 先执行
1. 解压到仓库外，阅读主HTML；把prompts/setup.md交给仓库里的Codex。不要整体覆盖现有AGENTS或训练代码。
2. 纯CPU自测：`python3 compare_runs.py --self-test`；`python3 tests/test_perfctl.py`。
3. 演示：`python3 demo.py --out /tmp/perf-demo-unique`。使用合成数据，仅验证工具链，不是GPU结果。
4. 适配训练adapter、计时、调度、artifact store、Temporal Cloud凭证与权限。未适配的入口明确失败。
5. 通过setup PR后，执行prompts/coordinator.md，从一个可逆候选开始。

## 台账命令
`python3 perfctl.py --root /absolute/local-state init --baseline /absolute/baseline.json`
`python3 perfctl.py validate /absolute/experiment.json`
`python3 perfctl.py --root /absolute/local-state register /absolute/experiment.json`
`python3 compare_runs.py /absolute/comparison-input.json --output /absolute/comparison-report.json`
`python3 perfctl.py --root /absolute/local-state gate exp001 --bundle /absolute/evidence.json`
`python3 perfctl.py --root /absolute/local-state archive exp001 --bundle /absolute/evidence.json`
`python3 perfctl.py --root /absolute/local-state status`

## 实现范围
perfctl检查不可变manifest、当前基线、提交/样本/环境绑定、必需检查、独立review记录、集成/质量记录、artifact哈希，并重算性能统计。成功只输出ELIGIBLE_FOR_HUMAN_REVIEW，不合并代码或发布基线。
hash不能证明测试真实、用户身份或质量；runner、SSO/RBAC、受保护检查器与独立审计负责这些事实。
轻量台账仅限单协调主机本地受信磁盘；不当跨主机数据库/资源锁，不在NFS共享写。archive保存通过门禁的快照，负结果与所有原始run仍必须另存artifact store/issue。
统计器默认固定输入/环境和初态，按独立AB/BA配对run重采样。框架升级/不同硬件比较必须另建明确协议，不能绕过指纹检查。
样本不足为INCONCLUSIVE；PASS不代表P99、质量或全局最优。选择候选后另用未用于搜索的确认集。
模板阈值与重复数是可配置起点，不是通用统计定理。项目负责人先定义质量非劣界、绝对时间口径和停止预算。

## 深入资料
agents/按方向给任务；research/含完整排查树与官方链接；docs/负责状态、接口、集成和停止；temporal/提供持久调度模板；symphony/提供原生工单入口、持久bridge和安装/启动脚本。
本套件未访问用户私有仓库或H200，未复现附件中的速度。附件仅作为经验与待复核证据。
