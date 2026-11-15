# B3.3a 独立阶段监督：逐步交付

日期：2026-11-15。固定产品基线`75d1ee325288527f67fb1ea814332d1522ff4860`，parent为b78。前置B3.2最终本地产品两轴通过、r4两安装648／283及真实控制流程保持自己的范围；本片没有产品变化，不能借用它们宣布B3.3a验收。

## 设计准备

[具体计划r2](../plans/2026-11-15-training-budget-phase-supervision.md)只调整原阶段监督的进程归属：原budget owner保留身份／锁／clock，各phase移到专用supervisor进程，复用原`processes.run`的subreaper／kill／reap。父owner不能因为一次phase结束而杀掉未来并行的另一个phase，也不能在总截止时强杀reaper后宣称后代已收尾。与原B3.2一致，期限后不再启动工作，只等待已经开始的安全回收；未确认或超期分别保持unknown／实际overrun。

独立只读[生命周期调研](../research/2026-11-15-training-executor-lifecycle.md)检查原executor／Sandbox／process_job／processes与六阶段生命周期，补充原executor没有whole-executor单次attempt和锁内准入hook的事实。B3.3执行功能需要另行固定最小协议接缝，不能靠锁外预检或另一个slot包装消除竞态；本片不改283参考、不启用runner、不添加执行权限或自动循环。kernel专家保留在v3路径。

调研还指出完整context可能超过PIPE容量，父owner同步stdin写入或完整stdout文件读回会阻塞停止。r2补可继续的短轮询communicate传输；supervisor在原run实际reap返回后先发送匹配stopped帧，再读helper结果。帧前不硬杀reaper，帧后若后处理跨总截止可停止已无业务后代的该已知supervisor，结果仍unknown；不把这个临时帧当训练执行停止证明。r1原件保持，不用固定headroom缩短有效预算。

## r2独立审查与r3修订

[新fresh-context评审者](2026-11-15-training-budget-phase-supervision-plan-review.md)对固定r2给出需求request-changes／R1、结构维护approve／开放0。独立stdlib探针在受支持Python3.12中向慢reader发送851968B，首次communicate超时后续调13次不能完成，手动关stdin只收到65536B且SHA不同；这不是产品运行验收。接受R1并保留原件，r3使用本地selector与非阻塞PIPE，持续维护唯一发送偏移、完整stdout帧缓冲和原clock／停止检查；明确两帧完整身份／顺序及独立封套容量，旧直接helper仍输出原普通JSON。没有为修计划先改产品或有效配置。

下一步固定r3设计完整原件，送同reviewer续核后再实施。尚无本片source、安装、真实进程或服务验收，不创建新suite或CI矩阵；前置75d自己的CI43665465985在途，单独结算。

## a0设计通过／a1准备

同片独立续核固定r3两轴approve／开放0／0，R1仅设计层面关闭。原r2报告逐字前缀、失败探针和三版计划原件保持，23原来源及strict parser、283参考与22链接已核，未运行产品／测试。开始在原两个owner内实施阶段监督及真实IPC，不改变共享processes／原queue／start slot／native参考或执行权限；新产品验收另行记录。
