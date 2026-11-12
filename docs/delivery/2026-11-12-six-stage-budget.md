# B2 总预算交付记录

产品基线`f394945db894740ad23a81c62b4ad87c85a84511`；范围和分片以[B2计划](../plans/2026-11-12-six-stage-budget.md)为准。当前只有源码调查、设计与受控进程探针，没有预算产品或正式预算流程的运行通过结论。[新的独立设计审查](2026-11-12-six-stage-budget-design-review.md)同片复核开放0／0；B1自己的CI与精确交付另在[B1记录](2026-11-12-six-stage-materials.md)记录。

## 源码调查与选择

实现者及一位fresh-context调查者分别核了tasks→原creation、submission／VerifiedSpecClient→WorkflowInput／Temporal、Executor→Sandbox／monitor→stage_driver／agent_runs／processes，以及结果收集和fence路径。调查者只写持久私有设计记录，未修改产品或公开文档、安装、测试、请求网络或提交；它不替代后续独立设计／代码评审。

已确认直接在preview填当前时间会破坏完整record的精确确认；从start或workflow开始计时则遗漏完整材料准备。采用原task-creations先保存一次prepare实例，再由只读preview／create／原input消费。单纯clamp模型timeout还会漏掉构造／Git锁、额外monitor等待、只读snapshot、回收与收集；需要先用真实独立进程探针验证接缝。

调用额度拟复用原确定性job／process的有限slot和started-before-launch，不新建计数账本；预留、attempt、实际可核启动分别显示。单composition的`project`并发scope不是多个task共享的项目全局并发，后者不由本片宣称实现。新执行在预算全链贯通前保持unsupported，旧运行版本保持。

## 当前节点与后续

B2.0源码调查及三种受控进程探针已完成，它不作为产品或CI测试。原进程实现依赖外部TERM与无总截止的回收，探针只证明这组可响应进程的实际停止与回收。之后按B2a持久合同、B2b原workflow、B2c实际生命周期逐项实现与验收。预算模型和新字段仍待实现及产品独立审查，不借B1的295／58项或自身approve关闭B2。

## 实际进程探针与范围

探针复用未修改的`processes.run(supervised=True)`，在独立进程用同一固定工作截止请求停止。r2的脱离组孙进程、阻塞flock、入口已过期三例分别在首次授权后2.261／2.314／1.148秒返回；前两例总额度3.2秒、其中清理预留1秒，已先消耗0.8秒模拟准备时间。采样分别为3／2／1个实际身份，同一原预算再次进入均不启动child；观察者manual_cleanup与存活均为空。不是在模型返回后另给完整timeout。

首r1诊断没有单列观察者代清理计数，因此不借其返回无存活字段独立证明监督者已回收。r2修正了此证据缺口，明确在观察者需要清理时拒绝成功；r1原件保持。完整探针、r2原件和来源身份仅放[独立prototype分支](https://github.com/626619403/Ergora/tree/8e160b345adf9eac00fe4142c3fd74bc29a07e97/docs/prototypes/six-stage-budget)，主开发分支只记录决定，不将其并入产品或CI。

探针没有运行真实tasks prepare/create/start、Temporal、Git命令、调用slot或正式receipt门禁，也未证明清理失败有界、不可中断I/O或任意daemon都能停止。结果支持进一步适配单job独立进程接缝；真实准备链和正式终态发布仍各需产品验收。

## 独立设计审查与修正复核

新的fresh-context评审从原九文件设计候选及实际源码提出两处缺口：原材料遍历在编译child之外，不能只给编译30秒就称准备计时闭合；原`process()`会先发布receipt，而FileAdapter.fence把任意有效终态（包括FAILED／CANCELLED）视作停止已确认。

已按最小范围修订计划：完整安装遍历／`tasks._definition`／manifest／编译／收集清理进入受同一deadline监督的prepare worker；whole-job child只返回待核结果，由原job生命周期finalizer在整个拥有树停止且收集验证完成后，唯一发布所有正式终态并更新原ledger。cleanup unknown时保留原attempt与待核证据，不发terminal，原fence继续unresolved。原评审已直接读取修订文件、六份guardian输出、实际采样与Git对象，同片复核关闭SP1／DS1两项P2，Spec／可维护性开放0／0。修正仍是设计，未声称已经实现；[唯一报告](2026-11-12-six-stage-budget-design-review.md)保存原判词、复核原件和限制。
