# F9c C1 原训练证据只读入口交付

日期：2026-11-14；基线`2181cc5c6ab92ac01664f8e769298cce350f65a5`。[计划](../plans/2026-11-14-training-evidence.md)。

已明确原archive／gate／owner批准／Temporal release与集成票据的职责，C1只接只读原件与有界文本窗口；精确批准和页面另片。立片时尚未修改产品、运行验收或取得独立评审结论；不把前片页面或CI成功作为本片证明。

首版产品已实现：原归档观察／单artifact摘要核对后Unicode窗口、同binding／evidence原本地票据；CLI／HTTP共用入口，未改283原参考。首轮源码三suite为26通过／9失败／2跳过、24.15秒；九失败均在新正例fixture仍遗留父fixture旧binding负记录时被原reader拒绝，尚未进入目标归档断言。已在正例构造前移除该旧synthetic负场景；保留首轮原输出，不改产品身份检查。修后运行待。

第二轮34通过／1失败／2跳过、25.44秒：原归档gate没有独立绑定原字节SHA，沿原owner比较JSON内容；追加空白仍为同一gate，测试不应期待内容冲突。已改反例为真正改变gate status。两轮产品代码未改变；原失败输出保留，修后再验。

修后源码三suite35通过／2跳过、24.32秒（原monitor25.361秒），两个跳过属于当前源码环境缺少可选web依赖的现有HTTP段；将由带web extra的最终非editable包运行。CLI／HTTP与原子进程共用读取算法，元数据与内容寻址／文本SHA／容量／路径等反例通过；原始两轮测试准备或预期失败均保留其历史范围。最终安装、实际CLI／loopback HTTP／SDK-free／原件收尾、自身与新独立评审仍待。

最终首版noneditable安装已完成：wheel `85b232ca0e5ae98e41749c26b4aa8bc9482d1f0112eb81c4bcc3edc014e160b1`，573产品／wheel581行与安装586行两RECORD／283冻结逐件一致，构建快照与安装产品逐字匹配。产品／测试／CI组合SHA `04bedeecd11502c2dbf600b451a0326b18117b08238a4b021902f850be2a0b76`。安装包四suite（evidence／training／web／architecture）运行中；真实CLI／HTTP／SDK-free、自身及新的fresh-context需求／结构评审待。

首轮安装四suite45通过／1失败、40.23秒（monitor41.853秒）：新HTTP测试漏用原loopback Host／Origin请求合同而先获400；原有training HTTP测试通过。已复用其既有headers/base_url修正新测试，不放宽产品guard。r1包产品未修改；最终r2快照／安装检查将包含该测试修正。

私有实际入口脚本已完成原init／runner／prepare、原adapter本地job request及原perfctl archive（真实POSIX锁）和前两条读取；错误evidence SHA被产品正确拒绝，但脚本误按退出1判断，原CLI通用错误实际退出2，故尚无最终passed。保留原archive／文件与stdout，续验仅修脚本退出码预期并从既有同一原件继续读，不重建归档／换ID或改产品。没有运行executor、训练／GPU或真实质量测量。

最终r2 wheel `d67ced0f3f65e21db69ee34a113552e9af64413f3384edcb5efe080dc785a98a`，573产品／两RECORD581／586／283核对通过，安装四suite46通过／38.99秒（monitor40.629秒），首轮Host验收问题修后关闭；产品5文件仍与r1逐字相同，最终测试快照含原headers修正。私有SDK-free续验首次把整个site-packages加进PYTHONPATH，仍能找到其中SDK，故自身“无SDK”断言失败而未作SDK-free通过主张；保留stderr，改为仅复制已安装ergora到独立搜索根再用-P -S续验。原归档与所有读取前原件保持。

## 最终本地原件与入口验收

实际原init／runner／prepare、原adapter本地job request与原perfctl archive（POSIX锁）构成合成归档，未运行executor。最终安装CLI四操作：两次原证据／Unicode窗口读取成功、两次错误SHA／越界路径按原CLI通用退出2拒绝；真实-P -S仅提供已安装ergora与原参考源码，找不到Temporal SDK且原读取结果逐字等完整CLI JSON。前两私有验收脚本失败保留，续验不重建或改已发布原件。

真实loopback HTTP六次GET（完整证据、文本窗口及错误SHA／路径／二进制／容量）全部按原合同返回，两个成功JSON与真实CLI相等，零mutation。原14件准备记录保持，所有37件原config／runtime字节与文件集合保持，验收Git clean；无executor started、workflow submission、fence、owner receipt／approval、integration ticket或命令marker，已有本地job request单列。原monitor停止web组且原端口不监听。

Ergora自身原结构模板实际审12完整文件／240,476B、44.448秒approve，完整实际stdin及祖先资源匹配；原结果SHA `4de644590c23cbd128bb855028afc861c69e08d888341ee5c0d6205355630517`。用户授权Codex回退，不称异后端或独立审查成功；该包包含Host修前的测试文件，之后只有最小测试配置修正，最终46项和新评审按当前文件核，不声称模型重审过该修正。

[公开证据](evidence/2026-11-14-training-evidence.json)列54份原件摘要，原失败与最终scope分别保留。当前最终产品／测试／CI组合SHA `bca645238f08d12e639da8b8f3732cdda651bd31e5aae735b97ee025a345aca9`；最终573产品与r2快照／wheel／安装及当前源码一致。新的fresh-context两轴待最终原件补核，普通发布与自己的CI待；CPU合成归档不代表真实训练／GPU或质量与性能验收。

## 最终独立本地结论

新的fresh-context[需求](2026-11-14-training-evidence-spec-review.md)／[结构](2026-11-14-training-evidence-structure-review.md)已直接核最终r2全部产品与两RECORD／283、安装46项及首轮失败、实际CLI／SDK-free／HTTP两侧原响应、14／37原件与收尾、自身原完整输入和54原件摘要；需求轴Host验收测试P2修后关闭，最终本地通过、开放0／0。初轮三个报告链接改为仓库#L行锚，未改产品。随后仅补原CI插件的collection：分组5选中389／总1842、1453 deselected，6.75秒；新增10项唯一归属，不称389项执行。公开证据现57引用（增加三个collection原件），产品／测试／CI组合bca645…保持。

剩余：普通提交／推送、固定Git blob与完整远端Ref、原两轴固定发布补核和本片自己的CI。C2批准／C3页面、真实F9d／B3、GPU／质量／性能与采用继续另验。

C1已普通发布`c3c7c3e218e9d2efc89498e8c208bf5981b9a0d9`，23件Git blob与最终清单逐字一致，完整远端Ref匹配。公开证据增四份静态／commit／push／ref原件摘要；原两轴固定发布补核与自己的CI待。产品／测试／CI组合及最终包不变。

原两轴已直接核固定c3c7c3e的23blob／573产品／283与57原引用、普通push及完整Ref，通过0／0；自己的CI43532534314已发现，六Linux组必要步骤成功、Windows在途，尚不作完整终态成功主张。

自己的CI43532534314已终态Failure：六Linux组必要步骤全部success；Windows原回归1030通过／756跳过／16 subtests，一项新正例失败。原artifact按Windows写入为CRLF，产品按原字节UTF-8解码正确返回24字符；测试read_text通用换行归一化后期待22。应修测试为read_bytes().decode，保留原fixture与产品字符语义；先本地CRLF复现／修后验证，随下个完整候选再验Windows，不称原候选CI成功。

换行预期最小修正已做：仅test用原bytes.decode；私有windows-fix-r2在原C1已安装573产品上用CRLF归档，原测试明确复现24／22失败，修后同场景1通过。windows-fix-r1误resolve虚拟环境解释器而缺pytest，原失败保留、不称复现成功。后续C1修正与C2完整候选一并精确发布，再验该候选自己的Windows／Linux；原c3的Failure保持。
