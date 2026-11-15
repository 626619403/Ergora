# c1b1：子预算owner生命周期逐步交付

日期：2026-11-15。准备基线 `f00bfdfd15173ceb0e961681679d6d3d62254bed`，分支 `refactor/architecture-foundations`。承接[本片计划](../plans/2026-11-15-training-cycle-owner-lifecycle.md)，仅进行只读源码／stdlib研究和具体设计；没有产品、服务、总Workflow或训练验收结论，kernel专家保持v3。

c1a2已固定本地十二文件提交，原reviewer固定提交需求／维护性两轴approve／开放0／0；其普通发布仍在原队列。后继只读研究指出：短S-H内直接调用原start，会令长期budget owner成为原reaper的后代；asyncio直接兄弟根又有正常teardown主动kill的风险。先闭合实际生命周期，不能把短暂owner_alive、独立session或两Worker注册当跨重启成功。

私有 `training-cycle-owner-boundary/reaper-probe-r1.py`先因存活观察未处理已退出进程的proc文件而退出1，未启动兄弟case，原脚本／身份／S输出与失败JSON保持。r2只修观察，沿新安装原 `processes.run(supervised=True)`执行：H的独立session惰性后代在S结束后活匹配false；调用方兄弟根在另一个S结束后仍活，随后TERM／wait退出-15、活匹配false。r2退出0／0.582秒，脚本SHA256 `c7a8331e17284133b9d83957eecbeb0b59a3d8db92266fb6157c70e3c3b8ba9a`；安装processes源码SHA256 `56c1961745b03ee4775e75f17dcb5a30a3d105e4bbd0f3fb516451e0fcd55867`。只认证惰性进程与实际Linux reaper，不认证预算owner、服务或重启。

SDK边界研究已有标准sandbox／显式pass-through／core缺SDK与Python Worker构造证据，见[研究报告](../research/2026-11-15-training-cycle-sdk-boundary.md)。它没有RPC或Worker.run，不能作为真实配额验收；公开stdlib根启动的正常teardown／父SIGKILL对照正在追加。拟仅将OS Popen创建异步化，所有业务与原预算执行仍在独立进程；该候选尚未通过设计，未修改产品。下一步固定实际spawn／初始化／确认／取消字段和职责，交新的独立设计审查，再实施。

## Stdlib生命周期观察与设计收窄

研究r2六case退出0／1.469秒，ThreadedChildWatcher下纯async正常teardown／GC及父SIGKILL后的惰性root实际仍活，不能写成必然kill。async transport的close／析构有kill语义且无公开detach；Popen析构无kill，窄的to_thread仅OS创建＋public connect_write_pipe＋非阻塞poll正常退出／SIGKILL对照均存活，六root最后由独立harness精确TERM／wait-15且proc全部消失。原r1的os.pidfd_open缺席失败已按原身份经libc pidfd精确TERM并确认proc消失；恢复者不是其父，未称已wait。原失败与最终六case分别保留。

据实际caller进一步删减设计：原_Submission在锁内prepare仅一次created=True，直接复用原不可变子intent作为根启动offer；created=False而无确认owner就unknown，不Popen，不新增launch.request／进程账本。schema2在实际ensure_owner最后点统一existing-only，schema1原launcher保持。不同H阶段与根传送消费一个原compute∩control窗口；窄线程不承载任何业务文件／预算。具体设计已写回计划，下一步新的fresh-context设计两轴审查；真实预算owner与产品仍未实施。

## r1独立设计finding与r2修正

新的fresh-context reviewer对r1固定六文档／源零diff给需求request changes（R1／R2）、维护性request changes（R2）；[原报告](2026-11-15-training-cycle-owner-lifecycle-design-review.md)保留取消职责与封套／恢复缺口，属于未实施设计问题。R1现明确完整owner确认才交接，之前由本调用方精确收尾根，之后普通活动只收尾短S-H；总controller取消／用户stop另走原b2b veto／通知／drain／实际观察，c1c消费者尚未实现。R2新增四mode／完整字段与结果表；所有H及根传送复用最初prepare请求的同一window，原schema2 submission最后点也核这份上下文。失联后活owner但无attempt只观察，不借resume补SDK start；有attempt只复用原reconcile算法，原唯一offer不重发。

r2还明确原Popen pending的真实句柄必须保留、OS创建卡住时不能保证default executor正常退出有界；root装载native环境后保留原应用＋选定native PYTHONPATH。没有新增持久交接／启动账本，未改产品。下一步冻结完整r2并由同reviewer复核，再实施。

## r2设计独立闭合

原fresh-context reviewer已逐字核最终r2七份快照、218本地链接、原resume无attempt派发路径、b2b独立停止分支及原25个GATE_SOURCES／283参考，需求／维护性设计两轴approve／开放0／0；R1／R2只在设计层关闭。报告SHA256 `e5e986722e5039a2811f48be603f96f1c7b8461a484da66edb6160e8bc39ecc0`，原r1意见和证据保留。产品、实际预算owner跨调用／重启、pending spawn／取消／恢复、新安装与真实cycle配额仍未验。接续固定本地设计／状态文档，再以其准确提交为产品实施基线；不把原惰性probe当预算验收。
