# c1d M1b：新版本授权出生与兼容交付

日期：2026-11-16。状态：具体[计划](../plans/2026-11-16-training-cycle-v3-birth.md)的 storage-only 范围已接纳，[fresh 设计审查](2026-11-16-training-cycle-v3-birth-design-review.md)修订后需求／维护性两轴 approve、开放0；隔离实施已开始，源码和真实检查尚未交付。

实施基线为 M1a 后 `bd479050ddd2d9c6b6964f89fe44cfc895273d6b`，持久隔离分支 `feat/training-cycle-v3-birth`。仅允许内部显式新出生 schema3、原件读取和本地 controller intent，缺省 schema2 及旧ID不变；新版本的 live／manual／native 执行全部明确关闭。native 拒绝须沿真实 executor admission callback 验证，不把外层 schema2 permission 分支说成 schema3 已执行。

来源四项、原clock／ID／完整字节恢复、边界关闭、旧历史和最小测试接缝见计划。后续源码、测试、安装、自身模板、fresh 实施审查和发布分别记录，不由设计审查代记成功。没有 V2 Workflow／activities／collect／measurement acceptance 或 ordinal1。
