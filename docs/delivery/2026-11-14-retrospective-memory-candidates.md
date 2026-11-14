# F10c2b1：记忆复盘候选交付

日期：2026-11-14；基线 `c4aa7acb555a5d55fec7e7a483544834e8afe44f`。[合同](../plans/2026-11-14-retrospective-memory-candidates.md)。本片实现、最终安装／实际CLI与模型／自身模板及独立最终本地审查已通过。原Windows20分钟CI取消已由原reviewer核清，预算修正也获新独立两轴通过；共同普通发布和新SHA完整CI待。详细过程与历史失败保留如下。

已实现原retrospectives上的记忆prepare/check/export、共享本地有界结果／引用核对与导出位置检查；新memory-retrospective preset默认只读Codex作者／Claude审查，不改旧Skill定义。原suite增加完整更正／新建、离线原件、原保存／恢复／expiry、来源I/O后变更及外部提案误绑／越权反例。首轮开发验证25通过／3失败／28.02秒：三失败均因测试假定oneOf会报告内部schema文案，实际原contracts报告候选不满足oneOf；产品已正确拒绝。现修正测试只核原外部候选路径，不改验证器或产品逻辑；原失败保留，修后定向另验。最终安装／模型／独立审查待。

修后开发定向原test_memory与test_skills_evaluation共28通过／22未选／27.88秒。原Skill候选／完整大结果／导出／CRLF行为仍通过，新记忆创建／更正／离线完整正文与原save／恢复及来源I/O后失效均覆盖。新的fresh-context reviewer已启动，最终r1非editable包构建在途；尚未将源码通过称为最终安装或真实模型验收。

r1实际CLI correct-save暴露正文身份丢失：原memory CLI通用换行读取把501处CRLF规范为LF。独立reviewer同步直接核同一原件并报R1（P2）；首个r1旅程停在原save已成功之后，未篡改该失败。已在原CLI owner改为UTF-8原字节解码，保留换行及语义U+FEFF；现有两个正例改为实际公开CLI save，并含开头U+FEFF。原状态／修订／有效期算法保持；手册说明人工UTF-8-BOM也保留U+FEFF。r1安装件不继承修复，另建r2最终包／安装与实际旅程，独立复核待。

最终r2非editable wheel6832763f8f07ccb1c32d130e14e5da4c85dd8ce31bbc9aa607e6b00232e49b9a，594产品／两RECORD602／607／283已核；安装原七suite在途。实际r2 CLI16次通过：精确更正与显式新建完整候选检查／摘要拒绝／导出／目标拒绝，原save／陈旧save拒绝／history／restore；更正1→2→3恢复原正文与有效期，新建revision1；完整U+FEFF／501处CRLF、原包／input／result／Git保持，离线不建State。正候选为明确合成合同，不称真实模型收益。

真实模型旅程保留原r1身份：Codex19.745秒→Claude20.763秒，7CLI，candidate:null、reviewer approve；两叶完整祖先资源／原stdin及完整checked前驱已核，canonical记忆与原包／Git保持。r1→r2全部594产品只原CLI一行memory save读取变化，已逐字核；生成／检查／后端未改，r2另实际离线check原作者结果与r1输出逐字相同，不无理由重复模型请求。这不冒称两模型由r2安装件调用；最终r2完整保存旅程单列。原自身结构模板正在r2包调用，新fresh-context评审在途。

最终r2原七suite **188通过／6平台跳过／215.43秒**（monitor216.942338秒），源码＝快照＝wheel＝安装的全部594产品、两RECORD602／607和冻结283的原manifest／Git blob／执行位已直接核。r1旧包188／6／216.27秒只保留旧身份，不关闭旧CLI失败。最终r2原自身结构模板选授权Codex（依据前两片Claude大输入360秒超时，未虚构本片新Claude失败），实际41.793秒approve；14完整文件157589B、原input／prompt／实际stdin／祖先资源一致。新独立初审R1已闭合、所审范围两轴approve；[最终公开证据](evidence/2026-11-14-retrospective-memory-candidates.json)259原引用和收尾已汇总，11个不可读/proc条目限制保留，未启动服务／端口／浏览器。新的最终本地独立补核待，前片自己的Windows CI仍在途，本片未发布。

新fresh-context最终本地补核已完成：需求／结构与成本均approve，开放0／0，R1闭合；594产品／两RECORD／283、188／6、259原引用和全部原件、CLI、真实模型及自身模板／收尾均直接核。原Codex作者141B非致命本地诊断stderr保持，run仍成功，不称stderr全空。PLAN多余尾空行已去除并获原reviewer静态终核。

前片自己的CI终态因Windows20分钟总上限Cancelled，29／30必要步骤成功，installer未完成。按[具体CI预算计划](../plans/2026-11-14-windows-ci-budget.md)，保留原取消，新的独立CI差异审查与原前片终态核对后，将一行Windows30／Linux20配置与本片共同普通发布；新SHA自身全部必要CI仍须通过及原补核，不因前片29项通过而借验收。该调整不改本片产品／包，未重复模型或suite。
