# F9b4c C2：训练页实验准备与原意图恢复

日期：2026-11-14。基线`92e7c24dbeb6847fe20c00e69c89c04b17702d5e`；[C1精确准备计划](2026-11-14-training-experiment-preparation.md)。C1最终本地两轴0／0、普通推送及完整Ref已核，自己的CI43527240748及原结构轴终核通过；本片不继承其CI。

## 行为与所有权

训练页接入已经实现的四个CLI／HTTP应用入口；不更改C1或283冻结参考文件。新项目在登记baseline／runner后填写完整experiment JSON、已登记runner ID、可选窗口，预览完整原manifest／spec／source及三目标计划，核项目revision并粘贴完整preview SHA后明确准备。页面只反映原本地文件状态，prepared不表示已start／训练成功／批准。

独立按稳定实验ID读取本地preparation，在完整原意图、逐件状态及SHA可见后，粘贴原intent SHA显式恢复intent_saved／partially_prepared；冲突／旧原生文件无意图不提供自动接管或覆盖。完整已准备状态可查看原件，无需重新prepare；不把读取或恢复变成自动提交。Linux／WSL2与可选SDK的支持范围沿C1。

局部面板拥有一份编辑／请求序列和发送状态；使用原trainingView的home／project／tab／DOM有效性，编辑任一输入／切项目／离开页面后旧preview及迟到回执失效。mutation时禁用该面板控制并防双击；未取得确认时保留稳定ID入口，先GET原意图，不假定零写入、不自动重发。完整JSON以文本呈现，复用现有api／ui helpers，原baseline／runner／列表／start／cancel保持职责。

## 验收节点

1. 独立内聚的页面算法，只有trainingView一个真实消费者；不为复用配额加插件／状态框架，不在浏览器重算native binding／验证字段。原http应用入口不改。
2. 最终noneditable包／当前源码／两RECORD／283；沿受影响现有Python检查与真实服务，不为静态DOM／默认文案堆镜像测试。
3. 实际浏览器完整draft→preview→错误SHA零POST→双击一次prepare→原文件匹配；真实四边界至少以原部分发布记录验证显式resume；丢实际成功回复后GET原意图恢复。编辑和切项目的迟到preview／publish／read／resume均不污染新视图，1440／960／390无横向溢出，实际查看截图；原baseline／runner表单及详情不受破坏。
4. 核原件、无job／fence／start／批准或runner命令，原monitor停止web进程组、browser关闭及端口不监听。Ergora自身原结构审查模板实际调用，新的fresh-context需求／结构评审；按finding修复及复核。
5. 普通提交／推送当前分支、精确Ref、自己的CI；每步更新本页与[交付](../delivery/2026-11-14-training-preparation-console.md)。F9c证据批准与真实F9d／B3仍另片。

当前：最终r2包572／两RECORD／283及当前源码一致，实际basic／lifecycle第三轮／visual、自身原模板、原件保持与服务收尾通过。新的fresh-context需求／结构两轴最终本地通过、开放0／0；首轮非法指数窗口P2已修复关闭。r1安装三suite38项84.27秒仅保留旧包范围；前两次lifecycle验收脚本失败保留，最终第三轮使用新稳定ID完成真实原写入中断与完整handler收尾。实际home／tab未逐项另跑，相关结论限原active／DOM源码检查。

剩余：普通提交／推送、精确Ref、原两轴固定发布补核与本片自己的CI；之后F9c。历史证据与失败详见交付，CPU文件／页面合同不替代真实训练／GPU、质量／性能或采用。

普通发布：已推送`2181cc5c6ab92ac01664f8e769298cce350f65a5`，16件Git blob逐字匹配最终清单、完整远端Ref一致。原两轴固定发布身份补核和自己的CI随后核，未借C1成功。
