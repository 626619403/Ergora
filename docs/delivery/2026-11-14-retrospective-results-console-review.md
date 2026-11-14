# F10d3b2 独立审查

主审：fresh-context `retrospective_results_console_review`。需求与维护性按独立 fresh-context 子审分别核对；本记录属于本片，不包含前片 F10d3b1 发布／CI 记账。

固定基线与审查时 HEAD 均为 `f7a4d28e82f2db99245885eaa24229299f7f73d7`，候选为未提交差异：`src/ergora/retrospectives.py`、`src/ergora/web.py`、`src/ergora/data/console/retrospectives.js`、`tests/test_skills_evaluation.py`、`tests/test_memory.py`、`tests/test_workflow_definitions.py`；同时核对本片计划／交付及 USAGE／当前架构说明。主审先读 AGENTS、PLAN 与[原要求](../plans/2026-11-14-retrospective-results-console.md)，再读源码／原调用者，最后读作者交付叙述。

## Spec

需求轴最终本地 **approve，0 actionable finding**。原 fresh-context 需求子审已完成同片原件补核，主审独立复核一致。发布及本片自己的 CI 不在本地结论内。

项目与显式 input digest 约束在原 `_read_request` 内、同次完整 input 读取后核对；三个 checker／exporter 共用此路径，结果 SHA 与候选 digest 仍由原 reader／专用 checker 核对。HTTP 没有先 inspect 再重读，CLI 省略新可选约束时保留原离线调用及 schema，也没有新增 State 或后端准入。

原 view 内的局部表单清除已失效选择；代际与 mounted-view 检查阻止旧读恢复，null 检查保留且不可导出。明确导出捕获原选择与目录，防重入且不自动重发；来源变化中的完成回执标为上次检查。完整文件、执行位、scratch 与原子不覆盖继续归原 owner。

## Standards

维护性轴最终本地 **approve，0 hard-rule finding／0 smell finding**。原 fresh-context 维护子审已完成同片原件补核，主审独立复核一致。

共享传输 payload 只转换路径，消费方为六条同族 HTTP 路由；新增局部 `resultPanel` 只有原 view 一个生产调用者，其保留理由是将该表单自己的异步状态和事件处理内聚于原 JS owner。没有新文件、目标注册器、调度器、评分器或候选账本。新 project/input guards 对应 URL 项目和用户显式冻结身份两个可达外部输入风险；它们复用原完整 reader，不重复 source／容量／导出验证。

## 最终本地原件补核

主审已将[最终证据清单](evidence/2026-11-14-retrospective-results-console.json)的原 480 个引用逐文件核对大小与 SHA，全部存在且无重复／不符；六文件与初审身份保持。三个源码 owner 连同其余全部 603 产品文件，在当前源码、r1 冻结快照、wheel 与安装件间逐字节相同。两 RECORD 的 611／616 行摘要与大小、283 冻结参考均直接核过，非 editable wheel SHA 仍为 `6fb0aef16690784c2cf6b98d4886a17e931a3b9f4909a07ad16b5a1ac499e572`。

原安装件五 suite 为 213 passed／118.08 秒，monitor 119.649 秒且 exit0。主页面 r2 的 94 检查／41 样本／11.421 秒与生命周期的 21／3／4.713 秒均已读取原脚本、结果及捕获；新 44 个样本与原 HTTP 逐对象相符。三方向正候选、null、项目／input／result／candidate 身份反例、已有／input 内部目标拒绝及 source 更换后原 reader 拒绝均有实际证据。

71 条原 HTTP 捕获含五条 owner 完成后的受控延迟和一次原导出 200 后夹具递送 503；原脚本没有替代产品 checker／exporter。来源／类型更改、新失败、切 view／项目的旧读不能恢复旧成功，旧来源导出另标且旧 finally 不启用失效选择；丢回复后目录保留且没有自动重发。早探针的 17 检查／7 样本保留为失败历史：其中 403 在原 middleware 消费 body 前拒绝，空体捕获不充作完整已接收请求；实际发送 payload 独立保留在 browser sample。文档已明确这一区别。

三份实际下载的完整检查 JSON（62,100／108,978／129,074B）与原 CLI 检查对象一致；六次原 CLI 输出与六个页面物理导出目录已直接比对，包括早停正例、丢回复和旧来源完成。Skill 原 UTF-8／CRLF／执行位、memory BOM／CRLF 正文及 receipt 坐标、workflow 全部文件与空目录保持；memory receipt 仅有明确 destination 不同。CLI unused State 不存在。

21 个原文件／树在 before、cleanup 和当前读取间相同；三份 SQLite 以 `mode=ro` 直接核得逻辑摘要一致，无模型／评价／采用运行记录。仅三方向 mutable-result 各有一次明确 summary 替换。原服务／浏览器 PID 不存在，三线程记录关闭，内核端口表没有三原端口监听。三宽原图均已目视，1440／960／390px 捕获与无横溢记录相符。

自身原结构模板的实际 Codex 回退 45.702 秒／approve 已核原输入与回复：10 份完整文件共 270,672B，三份继承资料及完整 task 均进入实际 275,347B stdin，且 stdin 与冻结／运行 input prompt 逐字节相同。源／测试身份仍是本候选；当时的计划／交付历史文本没有冒充最终运行验收。

本轮仅做只读源码／原件、摘要／目录、SQLite 与内核状态检查；没有安装、重跑测试、浏览器、CLI、HTTP、模型或网络调用。详细独立证明保存在本片 local `independent/`，分别记录 references、package、runtime、exports、self-template 及两子轴原报告。

## 处置与范围

开放需求 finding **0**，开放维护性 finding **0**；无阻断本地验收的问题。补核发现的文档状态歧义已通过历史检查点标签和当前终态说明修正，早拒绝请求捕获限制也已修明，未改产品或原 480 原件。

仅通过当前 Linux 合成原输入／候选的本地范围。Home 切换、全键盘、所有并发／故障排列及规模性能仍未验；不证明真实训练、质量、可信评价或采用。原冻结 input 单叶调用、完整 F10／F9d／G1／真实 B3／完整 Forge C2 仍按后续计划实施。固定发布、远端 Ref 与本片自己的必要 CI 尚待单独验收，不借前片成功。
