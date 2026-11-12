# F8-H1：DeepSeek 有界探针与可选只读后端

文档基线 `a35123e4ea3f24b091774f1476c2e159804de560`，产品基线 `784da65da89bdd2fed4742e57e3f904c0f295216`；承接[H0研究与选择](2026-11-12-harness-admission.md)，不改写其冻结审查范围。

## 当前决定

仅评估 `deepseek-harness-sdk`／`runtime-bin` 0.2.2rc2、Python 3.12 独立环境的只读叶调用。先完成 H1a 原生探针，再在现有 `AgentBackend` 添加 H1b 实现和一个独立 SDK 驱动；共用原结果验证、调用记录、MCP 与进程所有者。基础依赖、调度器、数据库和六阶段合同保持原所有者。

固定公开 `sdk-minimal` 与末层 patch，显式每调用新 home／session，移除原生 shell、文件、工作目录和共享 MCP 工具。凭据只用外部环境变量名；不提供任意 patch／原生 argv。首轮仅支持 `text-only`／`task-mcp` 的只读审查及提案；工作区修改、原生自由执行、交互会话与恢复另属 H2/H3，不因工具目录新增而宣称已经验收。

实测发现：`failOnStartupError=true` 的 MCP 插件启动失败后，宿主仍可能继续模型调用并返回 completed；断连也可能得到 completed 和有效 JSON。故正式适配不得只信任终值：原 MCP readiness 必须核对，原生工具任一 `isError` 本次调用保守失败，不按错误文案猜测可恢复性。未知结果沿原调用 ID 保存，不自动重跑。

## 节点与出口

|节点|可验收出口|状态|
|---|---|---|
|P1 原生正向与拒绝|固定 SDK／runtime、home／patch；只出现原 list/read；原 manifest/input/scope 全链、全文分页；未授权工具／未知 URI／超页／坏结果|MCP 五份72,162字节／九次调用已核；三种拒绝及原schema拒绝通过；两个启动前私有夹具错误保留|
|P2 失败与生命周期|启动失败／断连不能被接受为正式结果；慢模型超时／主动取消，原进程owner与受控 MCP 孙进程清理；记录采样边界|原CLI／用例拒绝启动失败和断连；原非supervised超时／取消、supervised取消通过；另补MCP前启动0.50秒、慢MCP取消1.50秒／超时10.51秒及脱离组孙进程取消6.65秒，均按采样／受控子进程范围清理|
|P3 最小接入|现有后端合同＋局部注册、描述驱动配置和独立驱动；固定版本诊断；严格JSON／原生状态／工具错误拒绝；原记录与可信资源|已实现；原只读叶入口，native／workspace明确unsupported；独立ST1诊断误读已red并最小修正、源码及真实doctor原件复核关闭；完整十九件独立Spec／Standards开放0／0、本地出口通过|
|P4 行为与交付|必要受影响suite／新非editable包／283；通过原CLI／用例实际调用新后端，正向与失败／清理；自身模板与新的独立Spec／Standards；手册、普通push／自己的必要CI|r1安装189通过7跳过／五段SDK调用及完整链核过；r2只改README元数据，452产品相同／两RECORD／283通过，新增实际CLI的HTTP500仅一次请求并failed；实际自身159.93秒approve／26完整附件及五scope全文链核过；完整十九件独立两轴／本地出口通过，提交／自己的CI待完成；无新CI工作流|

每步更新[交付记录](../delivery/2026-11-12-harness-probes.md)和[PLAN](../PLAN.md)。模型调用兼容、同模板正式审查及原生会话持久续接在 H2/H3 分别验收；本片不借本地合成响应证明真实模型质量、计费、Windows 或 OS 隔离。
