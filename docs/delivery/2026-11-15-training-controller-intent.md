# c1a1：控制器意图准备逐步交付

日期：2026-11-15。基线`fbafd8d7fc442acb8c52e0646ada327cdfb49fa3`，分支refactor/architecture-foundations。[小片计划](../plans/2026-11-15-training-controller-intent.md)承接已批准c1设计；kernel专家保持v3。

## 实施前

已核根／源码／测试AGENTS与组件协议、原CycleAdmission完整生成／读取、原status对可见ready与publisher锁的区分、原State本地reservation及_record无覆盖发布。选定两个原owner，准备结果包含最后cycle观察；不把准备等同SDK投递或训练执行。新验证复用现有controller_admission／cycle_selection，不新建测试框架或CI组。

当前只有本计划与记录，产品、源码验证、安装、自身模板和新的独立审查均待实施。长期原件位于ignored `.ergora/checks/training-controller-intent/`；公开记录不含凭据或机器状态。前置b2a自己的CI仍在途，后继普通发布保持逐片顺序。

## 实现与首轮源码检查

已在原protocol提取纯`intent_record`，原reader和cycles producer共用，字段与SHA保持；`prepare_controller`使用原State短本地reservation、原status的publisher锁／ready／clock与原父许可，无覆盖发布并最终观察。三项新接缝复用原fixture，包含可见ready仍持锁、同步错误后同原件恢复、link前null-intent stop与真实同步耗尽计算窗口。源码r1终态23通过／34.54秒，外层35.964秒；原stdout／stderr／JUnit及运行前后源码SHA保留。

自查发现原status的可选SHA参数允许传None表示不筛选，而新准备用例必须始终要求精确SHA；已改为在新用例比较实际原SHA，不复用可选筛选语义，并把该接缝并入原幂等测试。r1产品身份不覆盖此修正，r2与新安装待验；SDK／attempt／receipt仍未实现。

## 最终源码与新安装

最终r2同一接缝23通过／34.07秒，外层34.863秒，运行前后源码SHA同一。新的非editable core与SDK两安装各652个产品文件，均与源码／同一wheel逐字一致；283冻结参考及两依赖检查通过，core确无temporalio，只有原cycles／protocol两个产品文件不同于基线。冻结178份测试／示例，用安装包运行原授权／publisher锁／完整父binding与history／停止／原ready恢复及架构回归，当前在途。自身原结构模板与新的fresh-context产品两轴审查待完成；不预授其结论。

新的fresh-context独立产品审查已启动，自身原结构模板也已通过实际composition准入后调用Codex，终态另记。10:47UTC前置b2a官方REST403／remaining0，reset为11:23:13UTC；保留原响应，重置前不重复查询，远端顺序门禁继续等待，不影响本片本地实施／验收。

## 安装回归与自身模板终态

原安装回归终态33通过／124.71秒，外层125.772秒；覆盖三新接缝、原schema2出生模式、三个父锁发布恢复、原ready／父完整binding、真实固定history与单次start、attempt后stop拒绝重发、null-intent stop及最终drain、两种旧手工binding拒绝、原ready持久恢复、SDK-free历史与全部架构检查。完整stdout／stderr／JUnit、确切节点及178份输入SHA保留，不扩大为全仓库／真实训练验收。

真实core安装中从同一既有schema2授权幂等准备0.091秒通过：无SDK、5份原cycle文件逐字及数据库rows保持、原clock保持，无attempt／receipt／训练。Ergora原`ergora-structure-review`模板实际Codex33.545秒approve，16份完整文件484,867B及3原资源完整进入同一stdin；这是完整所供文本审查，不替代独立reviewer对私有原件／实际安装的终核，不宣称异后端审查。新的独立产品审查仍在途。

## 独立初审R1与修正

新的reviewer实际复现R1：最终status计算剩余后，显式父check的authorization读取可耗尽窗口，旧代码仍返回ready／work2秒，而同一最终clock已exhausted／work−4秒。原只读顺序探针、原输出及初审SHA保存在[唯一独立报告](2026-11-15-training-controller-intent-review.md)；需求needs changes一项P2、维护性approve零项，不能用上段r1验收替代关闭。

已作原owner最小修正：最终check移到最终status之前；原`_status`先作同一次schema2 stop观察、再读取原clock，保持stop对unknown／exhausted的原覆盖优先级。没有新clock、reader或helper；schema1原顺序保持。原耗尽测试加最后check／stop观察接缝，配置仍从实际fixture预算取。修后源码、新wheel／两安装、相关原回归、自身模板及同reviewer终核待验；旧r1原件不覆盖。

修后source-r3终态25通过／54.94秒（外55.786秒），前后source SHA同一；同reviewer独立重跑原只读失败探针，已返回exhausted／work−4，与最后原clock一致，R1先在源码层关闭。修后新wheel及core／SDK安装r2各652逐字／283／依赖通过；35项安装回归及新自身模板在途，最终本地两轴结论仍待原件终核。

为核新增接缝确能发现原问题，保留r1旧安装不变，用r2冻结测试的final-check／stop-observation两节点实际运行：两项均因返回ready而实红，23.33秒（外24.046秒），产品`package-r1-sdk.json`与测试`installed-tests-final-r2-inputs.json`分别绑定。首次私有调用器误用参数ID，exit4／零测试；原错误保留，随后从真实source-r3 JUnit取得节点ID再运行，不能把首轮当作产品失败。修后core实际幂等准备0.070秒通过，5原件／rows／clock保持。修后自身模板31.493秒approve，16完整文件488,529B／3资源完整stdin；仍为文本范围，不替代安装终态与独立原件终核。

## 修后安装终态

最终r2安装回归35通过／145.43秒（外146.497秒），同一新wheel与178冻结测试／示例绑定，包含目录／最后授权读取／stop读取三个实际clock耗尽接缝。旧r1两项同接缝实红、修后r2两项与整体实绿分别保留原JUnit和完整身份。后续只核最终源码／两安装／冻结输入与已知actor收尾、同reviewer最终本地两轴；无新的产品变更。

## 最终本地独立门禁

最终7文件快照、source／wheel／两安装各652、178冻结输入与7完整已知actor活匹配0已由原fresh-context reviewer直接重核；最终需求／维护性两轴approve，开放0／0，R1关闭。[唯一报告](2026-11-15-training-controller-intent-review.md)16,430B／SHA256 `39a703e96393399f9bd55f76a3c5e7e25a825dc18262cb8bd7390f9f1110759c`，保留初审、独立顺序探针、旧安装实红与修后实绿。文档链接与完整diff检查通过；随后仅作本地状态记账和固定提交，不改变产品／测试。普通发布及自己的CI仍等待前片准确门禁；下一片接总投递attempt／SDK／固定run对账，不把本片准备等同自动循环已可运行。
