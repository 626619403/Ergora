# CR3a：可信验证分支与不可变任务投影

日期：2026-11-09。状态：本地实现/最终包和自身模板审查通过，独立材料补核及精确交付在途。基线`8151a1c674fd6c664b4ce6aeba11a5fdf12be426`。本片先完成CR3的E2前置，未开放v2正式提交，也未实现组合reviewer调用。

## 行为与所有权

冻结原执行器的verify分支会向已发布的`task.spec.json`写入legacy spec，与新版wrapper的不可变发布冲突；它还会直接接受已有scope文件，而不核该文件是否属于本次候选/任务/策略。该分支没有投影路径hook，因此在现有`reference_executor.Executor`有限迁入verify；其余五阶段沿原继承实现，六阶段调度、候选、提交、批准和收据仍由原所有者负责。没有修改冻结文件，也没有全局patch写入或subprocess。

新的verify先核已发布任务的legacy投影等于本stage spec，再在私有scratch发布独立投影供原scope harness使用，原v1/v2任务文件不改。新建scope沿原实际harness；每次verify都经原harness重算scope，在私有临时新输出内运行后通过原不可变write发布/比较整个报告，避免只核身份头却接受不完整结果。临时目录是原harness拒绝覆写输出的实际需要，最终scope仍在持久scratch。原可信命令、基线命令集合、失败报告、必需checks和取消终态保持。生命周期/错误包装仅为原verify无hook所需的有限重复，未迁入其他stage算法。

变更位于`src/ergora/reference_executor.py`及现有`tests/test_reference_executor.py`、`tests/fixtures/reference_acceptance.py`。新增私有`_verify`只有同一Executor的实际stage消费者；按所有权保留在原模块，没有新通用框架或虚构复用点。

## 验收

- [x] V1本地：旧两开发模板×command/Codex合成原生协议的真实六阶段、同候选与指令绑定保持；最终R3包全套另核。
- [x] V2源码：保存完整wrapper的投影验证通过、wrapper字节保持；该探针只证明verify seam，不冒充正式v2准入。
- [x] V3源码：无身份/不同候选及仅匹配头的已有scope明确拒绝；可信命令变化/实际失败仍拒绝且不发布pass checks，正常scope失败恢复稳定。
- [ ] V4：源码与非editable包/冻结身份、适量受影响回归；fresh-context独立审查、普通推送和必要CI/远端终结。

首轮源码V1四组合均通过，4 passed（24.42秒）。新四边界正分别在原R3安装包和当前源码上验证，原失败与改后结果分开留存于忽略目录`.ergora/checks/ac3c3-verification/r1/`。CR3大项自身模板实调用在后续E3/E4整合时进行；本片仍要求新的独立审查，不以自检代替。

初版新边界源码13 passed（18.94秒）；原R3包2 failed/2 passed（17.23秒），分别实证wrapper覆盖冲突与假PASS scope被错误接受。初版只核scope身份头后进一步收敛为完整harness重算/不可变发布，新增同身份头但缺实际文件结果的反例；最终源码与发行验证进行中，不把初版13项移记为修改后的通过。

完整重算版源码14 passed（23.47秒），其新增伪造匹配头反例在原包实际1 failed（4.95秒）；R2非editable包368/283一致，executor/架构全套33 passed（109.72秒）。随后新独立评审发现TV-SP1 P2：正常scope失败的stdout携带随机临时输出路径，若error artifact已发布而receipt未发布，同job恢复会因detail不同而冲突。已将正常失败定位改成持久scope路径；对实际启动/读取/超时异常只规范其中的临时前缀，错误仍传播为原FAILED/CANCELLED收据。新增真实protected-path失败、两次中断点恢复及最终receipt发布的一个合同用例；R2红例与修后R3发行/回归进行中。

TV-SP1真实新回归在原R2包1 failed（4.68秒），修后源码六边界/架构15 passed（28.29秒）。R3新包已经建立，最终368/283与完整包回归在途；原生六阶段仍用合成协议Agent，不宣称模型实现质量。实际自身结构模板/MCP Codex审查已启动，沿用户允许的后端回退，结果尚未返回。

最终R3非editable包executor/架构全套 **34 passed / 113.18秒**，源码/包/安装368文件与冻结283身份一致。实际自身结构模板使用任务MCP完整分页提供68,920字节附件，Codex `gpt-6.1-sol`于105.42秒approve；[身份原件](evidence/2026-11-09-cr3a-self-review-identity.json)及[结果原件](evidence/2026-11-09-cr3a-self-review-result.json)保留。结果建议额外覆盖异常分支的重复失败；独立评审已另以内存拦截探针对这五种路径核稳定，不新增同形全套fixture或CI矩阵。该调用只审给定附件，没有运行测试、核包/冻结，也不是正式v2批准。基线已是815；本片实际模型输入包括最终三文件及相关冻结hook，未沿用旧片结果。

[新独立两轴审查](2026-11-09-trusted-verification-review.md)本地通过，TV-SP1已关闭；最终34项及自身原件已由原独立者补核，无新增blocking finding；固定提交后普通推送并等待本候选自身双OS CI。不能以815的CI替代。

最终静态核对：11份变更Markdown的324个本地链接/锚点无缺失，手册75条CLI命令经当前parser解析；`git diff --check`通过。独立者另核实际MCP附件连续0..68,920字节至null，无跳页；公开protocol结果与原run规范化结果JSON相等但编码摘要各属其原件，不混用。
