# AC5 C4b.1：子工作流折叠与专家查找

基线`a60a67e9333316ba094c69a1ed949484fbed8231`，工作分支`refactor/architecture-foundations`。[计划](../plans/2026-11-10-composition-exploration.md)第一片拥有折叠、查找与显示会话；第二片精确版本比较另见[独立交付记录](2026-11-10-composition-comparison.md)。前片C4a精确Git/HTTPS/自己的CI已终结。本片R2行为、实际自身模板及完整20文件独立两轴/本地出口通过，开放0；精确提交/HTTPS/自己的CI已完成，详见文末。

## B0 接口与实施边界

唯一生产消费者仍是`definitions.js`中的已发布preview视图。`composition-graph.js`已拥有完整实例、三种关系、几何、共享完整inspector和Cytoscape生命周期，折叠与查找继续留在这里；不创建单消费者抽象、第二个编译器或图框架。原vendor的headless接口探针证实批量替换显示元素能将compound子工作流投影为可折叠代表；此探针不是产品行为验收。

折叠只隐藏图内后代，原表格/完整inspector和关系表始终保留。每条跨组摘要线维持原类型与具名绑定、完整原始端点；内部边不画伪自环。明确折叠/展开会按原levels重排当前视图，显示状态不进入preview/定义摘要。查找用原精确Agent元数据，按路径、职责、专长、后端等字段进行字面词项匹配；高亮保留未匹配结构，结果动作显式展开结构祖先后定位。

实现尚未开始，未运行本片安装/浏览器/模型，也未授予任何行为或独立审查通过。后续每节点更新此记录，保留实际失败范围；复用既有安装与顺序浏览器驱动，不重复无变化的Python/编译器回归。

## B1/B2 实现与安装准备

一个产品文件内已实现逐实例折叠、原关系ID与摘要线回查、精确元数据字面词项查找、高亮/前后匹配/显式展开祖先定位，以及原会话的fold/query状态。原定义库与app请求/DOM所有者未修改；表格和完整inspector仍直接消费原preview，隐藏实例仍可选择。展开/折叠是明确重排，沿原levels并复用vendor批量更新/resize/fit，没有新依赖或通用展示框架。

两份定义手册、USAGE及架构已更新。JS语法、git空白检查通过；R1离线wheel构建、新venv和非editable安装完成（7.72/0.04/5.07秒），文件身份及实际页面待核，尚未宣称行为验收。前片a60a67e的精确26Git对象/436安装文件/283冻结及一次独立HTTPS同SHA通过；自己的CI42817897236首份官方样本仍In progress，不能当终态。

## B3 R1原件与精简

R1的436包文件/RECORD和283冻结身份通过。独立fresh-context静态两轴Spec 0、Standards无阻塞问题，提出CEX-ST1（P3）：图内复制的`originalSource/originalTarget/originalLabel`只有私有驱动读取，产品关系inspector已经按原ID直接读完整relations。已接受并删除这份重复数据，不为其制造消费者；新R2安装验证进行中，R1结果不能升级为修后包验收。

准备脚本首段误复用了保留的历史旧驱动，读取revise顶级id而KeyError；原输入及stderr保留，改用此前修正的definition.id/version驱动在新隔离目录重备。作者在准备失败后误启动的HTTP管理器因stdin关闭走finally，原服务均reaped/proxy关闭，未进行浏览器验收。

R1实际页面首段4.17秒覆盖三域16/19/9实例的折叠、摘要端点与隐藏叶完整事实/资源/prompt，随后私有驱动用无baseURL的相对API URL而失败。新驱动改完整URL并刷新隔离页面；第二段29.47秒再次覆盖上述行为及重复实例独立/嵌套折叠、原关系inspector、精确旧专长/拒绝latest，之后因测试假定审查后端为Codex而失败。原preview明确为claude-code；页面正确未匹配，不是产品缺陷。最终驱动按原实例实际backend_request构造查询，两份失败均保留，未宣称完整查找/会话验收或模型调用。

## B3 最终R2页面与原件

R2离线构建/新环境非editable安装完成，436文件/RECORD与283冻结一致，wheel SHA256为`0aa34395e655fba62c7160ba8e7e8546b108a74cd02fff3edef42a54e850e0db`；较R1只删除上述三份无产品消费者的字段。没有Python/schema/依赖/CI或永久测试变化，原编译器/运行回归不重复运行。

最终顺序主旅程**12.94秒通过**：三域与重复实例独立/嵌套折叠、按每条原边ID逐条核三类关系投影及摘要端点/无伪自环、四次所选隐藏叶的完整事实/各资源正文/prompt、拒绝latest专长、精确专长/职责/实际后端查找、不隐藏未匹配结构、键盘展开祖先与前后定位、tab/版本会话及未应用编辑缓冲、组件缺失的表格/查找、原preview逐字段不变。四次完整inspector来自三域各一个隐藏叶和重复structure-extra叶，不声称本片遍历了所有叶。跨home旅程**26.44秒通过**：A/B各自query/fold/选择/坐标独立往返恢复，旧图销毁，合成persisted恢复完整显示状态，刷新重置。这里不声称自然BFCache命中或跨浏览器覆盖，也未重复未变的迟到preview算法验收。

受控元数据/视口旅程**3.78秒通过**：仅在浏览器路由移除一个精确Agent索引，页面明确缺口、不虚构专长，原叶完整材料仍可查看；恢复真实索引后精确查找恢复。该故障注入不修改原定义或上游HTTP原响应，原/交付索引均留原件。1440×1000及390×844文档无横向溢出，画布/renderer分别1076/1076、246/246；两截图已人工查看。窄屏全览标签仍需缩放或查找定位，不把全览当逐标签可读保证。

离线核190对原HTTP bytes/SHA，最终R2所有preview逐份等于原编译器，实际四份安装静态资产等于当前源；54个完整旧对象树不变，两个UI控制目录的全部agent_runs均0。失败启动及两轮页面共23个采样owned身份均已消失，只覆盖采样范围。实际自身模板、新独立产品补核、完整最终候选与精确交付尚待完成。

独立原评审及两轴已完成修后产品阶段补核，开放0、CEX-ST1关闭；同时核190对HTTP、12份最终preview、436/283、旧树及清理，保留四次所选隐藏叶/合成恢复/视口耗时的实际范围。自身模板首个run在原MCP预检阶段失败（37.97秒），没有进入推理，不能当模型拒绝；原错误/input/scope保持。同一scope的原只读probe随后1.53秒通过，未改权限/超时或产品；以相同冻结输入重试，实际模型审查在途，结果/成本/完整读取仍待验。

## 实际自身模板与公开投影

R2非editable安装的内置`ergora-structure-review`以证据专用修订`1.0.72`实际运行，Codex / gpt-6.1-sol / high，run `fd460f5c66594f82966a633b1cf1e9fc`为**succeeded / approve，Spec和Standards均通过，finding 0**。原run的started/finished区间**122.91秒**包含快照/预检；外层私有驱动在模型成功后因漏定义`protected`发生NameError、退出1，不能宣称驱动成功。原完整run/result已先保存，故只离线恢复身份和时间记录，不再调用模型。原结果SHA256为`7ecc9cd8129c633daf78f23e32bc22f06607362b16cc28f04cb03d6f644b8242`。最初预检失败原件保留；模型实际只调用一次。不推定短暂预检失败的具体原因。

离线审计原stdin/prompt、manifest/input/native MCP及回执：五scope文件全部完整读取，252,062字节附件用12个连续成功UTF-8页读至`next_offset:null`，一次base64窗口在相同offset减小后重试。18个完整冻结输入原件、四份受保护源身份保持。完整交付不证明理解质量，也不构成正式owner批准；使用用户授权的Codex回退，不声称不同模型独立。模型/CLI五个采样owned身份均已消失。

后端自报input 1,062,144，其中cached input 933,248；output 1,966，另报reasoning output 454。cached已含在input，不重复加总；这是自报用量，不是账单。最初预检没有进入推理。原模型成功后的记账错误、离线恢复来源和真实原件身份均显式记录。

公开投影保存原件bytes/SHA及明确省略范围：

- [页面/历史失败/最终原件审计](evidence/2026-11-10-composition-exploration-browser.json)
- [两轮安装/完整冻结身份](evidence/2026-11-10-composition-exploration-package.json)
- [失败预检/只读诊断/实际自审原结果](evidence/2026-11-10-composition-exploration-self-review.json)
- [五scope与完整逐页读取](evidence/2026-11-10-composition-exploration-reads.json)
- [采样清理与后端自报用量](evidence/2026-11-10-composition-exploration-cleanup-usage.json)
- [桌面截图](evidence/2026-11-10-composition-exploration-desktop.png)、[窄屏截图](evidence/2026-11-10-composition-exploration-mobile.png)

机器路径/端口已替换；省略重复屏幕文字、布局、完整436文件map和原路由索引重复正文，完整原件私有保留，两个截图逐字节复制。四次所选隐藏叶、元数据受控路由、合成恢复及窄屏可读性限制保持原范围。当前只有一个产品文件变化，未改变原定义/权限/调度所有者。第二片版本比较/C5/C6及整个项目未完成。

## 本地最终出口

完整20文件候选已由原fresh-context主审及Spec/Standards两轴补核通过，开放finding 0、CEX-ST1关闭；[独立报告](2026-11-10-composition-exploration-review.md)记录原件范围与限制。216本地链接/锚点、五JSON、JS语法及空白检查通过；公开投影从原件内存重建逐字节相同。主审私有`review-local-final-gate.json`为`local_acceptance:true`、`complete_acceptance:false`；仅待ready冻结、普通提交/推送、精确Git对象/一次独立HTTPS及本提交自己的CI。此终态续记不改变产品或重跑已验行为/模型。


## 精确交付终结

`8ce9aba51c54e368aa8625e6c6535e4ac6ccaa19`已普通推送。原评审独立核20份ready/Git blobs、436包文件与283冻结身份，并以一次HTTPS读取核远端分支同完整SHA。[CI42825342126](https://github.com/626619403/Ergora/actions/runs/42825342126)第三官方样本为Success，双OS两job完成、七必要步骤均success/completed；前两In progress样本原样保持。原主审离线核三样本15份官方原响应，最终`review-exact-delivery-gate.json`为`pass / complete_acceptance:true`。终态仅授予本片；下一片成对比较另行验收，不重复此处产品/模型/远端核验。
