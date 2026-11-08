# AC1.2：已固定模板说明进入正式提示

日期：2026-11-08。状态：实现、源码104项、非editable包8项及[新独立审查](2026-11-08-template-instructions-review.md)本地通过，普通精确交付及自身CI待完成。基线`bf99bd47220572fd721546a2eeb5b1b2739a57b5`，分支`refactor/architecture-foundations`。问题来自[完整源码评审Q-1](2026-11-08-agent-composition-review.md)，顺序见[AC计划](../plans/2026-11-08-agent-composition.md)。AC1.1已按自身CI与独立远端终结，不用其结果替代本片。

## 范围与合同

Ergora正式selectable executor目前只将通用约束、spec和依赖材料发给Agent。两开发模板的instructions虽在任务`compiled.json`中冻结并有摘要，但正文没有进入实际prompt。

修复归`reference_executor.Executor.model`：用已有`validate_compiled`核当前任务保存的完整编译材料，并要求其spec等于本次stage已核spec；从该快照取instructions正文及profile固定摘要，完整加入实际prompt和原agent-selection追溯信息。沿用原错误回执与可信监控，不创建新的调度/上下文框架或第二份模板副本。

已有正式创建路径都保存编译快照；缺失或篡改它应明确失败，不临时读取活动包替代。一次任务的编译源包被删除不影响其已保存正文，已完成的stage/回执不改写。当前原继承executor仍要求安装profile与任务固定profile一致，安装本身漂移继续按原合同拒绝；本片不声称支持任意上游升级后的在途恢复。

只改非冻结桥接、已有六阶段fixture/检查及必要文档。原283参考文件和直接`agentflow`入口保持原分发身份；本修复覆盖`ergora reference executor`正式桥接，不把旧入口误写为获得同样的新prompt行为。训练模板的原生执行不是本次两开发模板的六阶段路径，按F9/AC4c处理。

## 验收表

|验收|状态|
|---|---|
|治理/大型变更×command/Codex形状实际后端进程的四类模型stage，均收到固定完整说明及正确摘要|源码四组合通过，直接读原生调用保存的stdin；正文/摘要及prompt SHA与回执一致|
|缺失快照、修改正文、借用另一任务的有效编译材料，均失败且未启动Agent进程|源码三种拒绝/无Agent请求检查通过|
|创建后源包不可用仍从该任务快照完成原六阶段；旧binding快照保持可用|源码保存后删除portable源包，完整六阶段通过；原legacy绑定/统一注册检查通过|
|原可信检查、计划批准、候选/作者/session、只读监控、取消及283身份保持|源码原执行器全文件及task_inputs/original_payloads/架构104项通过；283文件源码/wheel/安装身份通过|
|当前源码/非editable包、新fresh-context审查、普通精确交付/CI|本地源码、包及新独立两轴审查通过；提交推送/自身CI与同片终结待完成|

所有运行使用隔离fixture/State和确定性进程，不调用真实模型、服务或用户任务；如需真实模型验证另记，不将fixture成功当质量评价。只有本片通过的检查才归入本片，不借用AC1.1或研究CI结论。

## 本地实现与验证

生产仅修改原`reference_executor.py`，复用原`validate_compiled`完成摘要/语义检查，用已有`require`核stage spec，完整正文和原profile摘要组成`template_instructions`。原通用约束仍规定阶段权限，原`agent-selection`新增正文摘要。没有公共helper、新状态、依赖或自建validator，也没有改冻结文件。

已有六阶段fixture增加实际发出stdin与回执核对。原四模板/后端组合及legacy/统一登记/取消检查复用该fixture；新增三种拒绝和一条源包不可用的完整旅程，不重造模型执行。修复前原command/governance用例真实exit1，原生输入中缺`template_instructions`导致KeyError，保留红例；修后Python3.11.15/pytest9.2.0运行`tests/test_reference_executor.py tests/test_task_inputs.py tests/test_original_payloads.py tests/test_architecture_boundaries.py`，104 passed/零skip，161.54秒。命令显式`PYTHONPATH=src`，不误测旧安装包。

默认隔离构建及新venv安装`[dev,temporal]`均exit0。wheel SHA256为`9cb4793a794d5f85c022c3771c16ee28935b2a1d37f6374226711375058eaaf6`；新进程导入路径在该venv的site-packages，352个包文件与源码逐字一致，283冻结文件的源码/wheel/安装身份及公开`reference verify`均通过。安装后移除`PYTHONPATH`运行原执行器文件中`template_instructions or existing_six_stage_contract`定向检查，8 passed/11 deselected/零skip，pytest实际70.94秒。这八例涵盖四个原六阶段组合、三项拒绝和源包不可用后的恢复，不替代104项源码范围。

记录位于忽略目录`.ergora/checks/ac1-template-instructions/`，含实际命令/退出、红例、源码及测试SHA、wheel身份及安装路径。下一文档静态与新的fresh-context独立审查，随后普通精确交付及本候选CI；没有真实模型质量/速度或Windows正式执行结论。

## 独立审查与处置

已完整读取新fresh-context[评审](2026-11-08-template-instructions-review.md)，需求符合性与可维护性在本地范围内均通过，没有新增finding。评审者从原Q-1及实际差异核compiled/spec/prompt/回执的完整链，复用已有校验和执行所有者的做法得到保留；没有证据要求新增公共helper、缓存或删减本片四种不同合同反例。

评审者在原非editable环境独立复跑三项拒绝和删源包后六阶段：4 passed/零skip，11.80秒；另在内存重算外层及组件摘要的两种篡改均按固定profile拒绝。它独立重核352文件/283身份、首轮203本地链接/30 parser，并准确区分作者104/8项与自身4项。主代理接受结论，原生产/测试身份不改；待归档最终静态和scope后普通提交推送，取得自身双OS CI及同片精确终结再关闭Q-1。新嵌套工作流研究属于后续设计，不扩本片源码或验收范围。
