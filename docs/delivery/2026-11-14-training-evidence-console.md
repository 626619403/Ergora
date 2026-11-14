# F9c C3：训练证据与批准页面交付

日期：2026-11-14；基线 `1eef90d7453c64579ddc25bd5a7775eecd20c2cc`。[合同](../plans/2026-11-14-training-evidence-console.md)／[证据摘要](evidence/2026-11-14-training-evidence-console.json)。页面已实现，最终本地验收完成；新的独立两轴最终本地通过，开放0／0；普通发布及自己的CI尚待。

## 行为与所有权

原训练详情新增内聚的 `training-evidence.js`，唯一生产调用为 `training.js`；复用原 api／ui、selected生命周期和现有正式任务页，不修改Python、HTTP、执行、授权、测试或CI。原实验详情读取失败仍挂载证据／本地批准面板。

- 显式读取原evidence／gate／binding／归档manifest、baseline、comparator和artifact索引；完整身份可展开。索引维持not_read，选择原path、确认完整evidence SHA及Unicode字符offset／limit后才核原SHA读取窗口，沿next_offset继续。HTML validity／safe integer与数值规范化防止无效窗口请求；错误清除旧正文。
- 首次批准确认原完整run／evidence与项目revision；已有prepared／unknown只确认原intent。receipt创建unknown与signal unknown单列；未知发送只查原固定run历史，原manifest／baseline／runner／archive不可读不阻断已有意图对账。Linux／WSL2原owner负责mutation，页面不引入新的授权或实验权威。
- mutation禁本面板、防双击；同一source的pending metadata／text可完成，新控件保持禁用，finally统一重绘批准结果。来源／窗口或选中实验改变时原read序号废弃旧结果；原闭包view和sending不引用新页面控件。丢回复先读原记录，不自动重试或换ID。
- requested仅投递，authorization未评价。原integration_ticket.record及身份可读，手动跳正式任务页不创建Task、工单、合并或采用。README及[训练手册](../TRAINING.md#在控制台审阅证据与批准)已加入实际步骤。

## 最终身份与验收

最终r4非editable wheel SHA256 `0e0518ed2e97eb343fb3866bc8646dc16c3109d2310870ab737c32951544cb16`；575产品与当前源码／快照／wheel／安装逐字一致，两RECORD583／588和283冻结参考全部核对。两产品路径按sorted path + NUL + 原bytes + NUL组合SHA256 `f9f40ac06c9e95a915bba6a9301e80f32b90870fc1ed87121466fa4a388a69d6`。

最终r4安装web／training_evidence／architecture三suite **33通过／25.02秒**，原monitor26.731秒；两JS语法通过。没有新增unit test或CI分组。

|已验范围|实际证据与界限|
|---|---|
|r3首三个原run页面|原metadata与本地记录显式读取，错误SHA／数值零请求，Unicode首段／next_offset、二进制错误清旧正文、有效指数规范化；alpha原批准、防双击及批准后原artifact控件继续GET。beta真实信号已收后丢RPC ack、unknown原history恢复；gamma原receipt落盘中断、prepared与receipt unknown独立显示并复用原件继续。pending metadata／text晚到仍全锁、next完成后可读。|
|r4第四原run页面|实际应用先构造原unknown；暂移原spec／baseline／runner／archive四来源，原详情失败但批准可读并按原intent／固定run历史恢复；原HTTP200真实回复abort后仅GET读回原requested。恢复表单无literal null。|
|r4读生命周期|真实loopback响应经浏览器延后：metadata逆序、字符offset编辑、换实验的metadata／approval、换项目的text及换tab的metadata均不覆盖当前展示。|
|r4视觉与任务入口|1440／960／390展开长metadata及批准原件，无document横溢；三宽截图已实际目视。原ticket跳既有正式任务页，零mutation。|
|原owner与原件|四原run各唯一个request_release／原集成票据；receipt原字节SHA与expiry保持。24准备／109读取原件逐字保持，四暂移来源恢复同字节；Git clean、无runner／executor-start／fence。|
|资源收尾|原monitor停止原Temporal／worker／web及最终r4 web共四组；两个浏览器daemon均不存在，三个loopback端口全闭。最终浏览器console仅原资料缺失的两HTTP400和故意abort，无JS exception。|

r3与最终r4仅可选run输入spread一行展示修正；首三个运行的浏览器证据保留r3身份，不重新标为r4执行。r4第四run与全部读生命周期／视觉是最终安装包实际页面。

最终自身原结构模板审完整10文件／97,136B，48.701秒 **approve**；实际prompt／stdin一致，全部祖先资源全文在stdin。原结果SHA256 `1bcbcbe90d355b8fd62de4d7a2b9f22e9a8fd4e01df3f5e36cff092e7e21b211`。用户授权Codex回退，不称异后端或独立审查成功；较早r3模板10文件95,849B／51.105秒approve另保留。

## 发现、修正与保留失败

1. **S1／P2**：mutation递增metadata世代，已显示artifact闭包会在批准后静默return；废弃pending文本还会留下永久loading。最终保留同source读取，新增控件继承发送锁，批准finally统一重绘；原artifact、两种pending读与next的动态反例通过。
2. **M1／P3**：发送中被恒定抑制的成功重绘已删，仅存结果后finally重绘。**M2／P3**：native append(null)曾显示文字null，改为只追加实际run输入，r4缺源恢复表单已验。
3. 私有native-r1误用归一化registration定义，缺schema_version／repo被原validator拒绝；原三run已创建但浏览器未开始，两组进程和端口已收尾。修正私有夹具后用新state／DB重跑，产品schema不变。native-r2完成bootstrap即正常收尾，未称浏览器成功。
4. 浏览器默认Chrome不存在，显式选已有Chromium及已装依赖后继续，没有安装提权。basic-r1在原alpha批准成功后，私有10字符预期少末尾n而误失败；同DOM／原run只读continuation按原Unicode字符确认…syn，读取原approval／ticket，无重复批准。
5. recovery-r1先填intent再刷新metadata，原表单重建后确认为空。用fresh snapshot／实际CLI重新填当前确认框，继续同原run，最终仅beta／gamma各approve＋resume四POST。原110.277秒脚本与人工交互原件均保留，不称无人干预从头成功。最终HTTP六mutation均是三个首批批准、两个恢复和第四run恢复；第四run原unknown由一次应用故障注入设置，原四history各唯一信号。
6. r1／r2／r3各自既有33项通过，分别27.41／27.57／26.85秒；都保留旧包范围，不冒称最终r4执行。全部143份公开引用摘要可定位本地私有原件，公开摘要不含其私有内容。

## 验收界限与后续

动态生命周期覆盖上述**读响应**；迟到mutation／旧finally隔离及home切换沿selected与局部view／sending静态核对，未动态穷尽。旧start／cancel仅diff与调用链核保持，本片没有其UI mutation旅程，也未执行training_submission／cancellation suite；F9d完整旅程另验。Windows原生页面mutation、真实GPU／训练／质量／性能／实际集成复验与采用均未由此片证明；原归档／attestation是合成材料。本地可信当前用户边界不变。

新的fresh-context[需求](2026-11-14-training-evidence-console-spec-review.md)／[结构](2026-11-14-training-evidence-console-structure-review.md)已直接核最终包／回归／四原history及原件／收尾、143引用及上述界限，最终本地approve、开放0／0；随后普通推送当前开发分支，核固定Git／完整远端Ref及本片自己的必要CI，不合main。C2自己的CI43536265177八job／30必要步骤成功独立归C2，不借给本片。
