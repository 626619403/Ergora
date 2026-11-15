# Q5.2a 训练测试维护交付

日期：2026-11-15。见[具体计划](../plans/2026-11-15-training-test-maintenance.md)。初始维护已验；现承接前置ac86043自己的Windows CI六个夹具setup错误，最小测试接续未闭合前不推后继产品。

本片只处理提前平台skip与一条内部整句报错断言，保留全部业务／恢复／回收场景。Q4.2c具体合同仍在独立设计审查，与本片源码范围分开。未修改产品或CI；不把静态发现称作已测Windows性能收益。


## 实施与实际静态／setup检查

已在原26个函数增加提前平台skip，原不完整stopped测试只删除完整reason文字相等断言。AST正规化比较确认除此以外函数体／参数／其他装饰器完全相同；Linux收集前后84个nodeid逐项相同。当前这26函数展开为41个case（原发现报告的40只归其75285e3基线），不能沿用旧数量。

原r6 SDK非editable安装执行受控的目标测试模块sys.platform视图，不改变整个Python或其他模块的平台：修改前41 skipped／43 deselected／29.06秒，registration／experiments／prepared共123次进入；修改后相同41节点skip／43 deselected／0.33秒，三fixture零进入；两项可移植读取测试没有新增平台标记。这里只认证真实pytest的收集／setup行为，时长是Linux上的受控视图，不能称实际Windows节省。

第一版私有观察hook在fixture_setup直接抛skip，没有沿pytest默认路径设置cached_result，造成1 skip／40 setup errors；原输出保留。这是验收驱动错误，未据此改产品或测试。驱动改为只记录fixture进入、让pytest正常执行其原setup，修改前r2和修改后才得到上述有效结果。

精准原phase-stopped-incomplete Linux集成回归仍在途；自身原结构模板、新fresh-context审查、普通发布及自己的CI均待。src产品／原安装／CI和kernel路径未改。

原r6 SDK非editable安装上，精确nodeid的phase-stopped-incomplete集成1 passed／29.85秒；另两可移植读取／冲突竞态2 passed／2.01秒。两份JUnit保存实际case、零failure／error／skip；未重跑未改的完整submission suite。Ergora自身原结构模板真实Codex复审已启动，独立审查与最终发布仍待；当前没有实际Windows收益主张。


## 原自身模板结果与 Windows 接续

原13份完整输入252176B／三祖先资源的自身结构模板真实Codex审查34.8399秒，需求／维护性两轴approve；input digest为a3268254afaa69eb6472097fa0fdfe32596f7927440b2d8d76a1184b4c296c3a，原结果SHA256为fe62f519cec6d1bed1dd4d3d0643e0279e0a7fd207920c204627e005134c4713。此结论只归最初26标记／一断言范围，不能提前认证后加的fixture修改。

ac86043自己的Portability 43684533043／attempt1已终态七job成功／Windows失败。六setup错误全来自historical_execution误调用Linux-only prepare；1179通过／876跳过和其原失败保留。现将合成旧intent的构造留在夹具，完整observation复用SDK-free原读取器，既不创建活授权，也不放宽产品执行支持。原所有坏链、SDK-free与缺安装检查保留。新范围的复现／回归、自身补审、新fresh-context两轴、普通发布和自己的CI仍待。


## fixture 修正的实际检查

最终测试全文SHA256为7e268543d7e863d4abb9a6df535069144e592eee5d87cee18f085f4ce31317cc。原r6 SDK非editable安装和独立冻结测试副本上，原历史读取／durability／owner节点8 passed／10.08秒，76 deselected。局部入口替身仅复现原prepare拒绝：固定ac86043旧测试六setup errors／5.68秒，新测试相同六节点6 passed／7.18秒，prepare调用6→0。此替身不模拟Windows文件／目录同步语义，真实Windows仍待自己的CI。原件见私有history-linux-r2、prepare-guard-before-r3及after-r3的JUnit／完整stdout／stderr和观察JSON。

首次guard驱动用隔离Python的`-p prepare_guard`，未将私有plugin目录加入搜索路径，两次均在pytest初始化报导入错误（exit4），未运行测试。原件保持；第二驱动仅把冻结测试目录加入隔离Python的sys.path，实际仍导入原r6 site-packages，才得到上述有效红／绿。静态比较用AST visitor处理原嵌套断言，确认仅26个提前标记／一断言删除及historical_execution夹具改动，其他AST完全相同。src／scripts／CI／pyproject没有改动，不重复构建相同产品或扩大完整suite。

原c2 reviewer已核官方终态原件、固定ac86043的Git blob和全部30必要步骤：29成功／1 Windows regression失败。该原报告保持自己的失败归属。本片自身补审及新的独立审查正在准备，精确发布和自己的CI仍待。


## 最终源码自身模板与新独立审查

同一原r6 SDK安装使用原ergora-structure-review@1.0.0／授权Codex回退，最终16份全文362342B及三份祖先资源全部进入实际stdin，26.5319秒两轴approve，开放0／0。input digest为1a53911062159a05bd495dd1c93164efffb0fe5b9863fe2e0b5829c0ee58b0ef，原result SHA256为bb7482ebd94db05b51e45399989e55fb62fd8cef22bb65b1a1a66facc79301e5。完整结果及请求保存在私有self-review-r2-codex；这只认证供应文本的审查，不代替真实Windows或原件核验，不声称异后端。

新fresh-context reviewer已获得固定12份全文369901B、完整tracked差异与新文档，以及实际原件。scope SHA256为8e451fa5c7d81121f53d6a05a1f51ecd58f0e136d200c7850ef9fd4ff19c4cbc；只有一份测试代码，Q4.2c五份已审纯设计／报告仅随记录同步，不把设计approve称为产品实施。最终独立结论／精确发布和自己的CI继续待，kernel专家与全部产品保持。


最终收集仍为原84个nodeid逐项一致；当前变更文档的237个相对链接可达。当前652产品源码逐个长度／SHA与原r6 SDK安装清单相同，src／scripts／.github／pyproject相对ac86043的diff为空，测试维护不借此改变产品或kernel路径。首次私有collection-final-r2误把venv解释器symlink resolve到base Python，未装pytest而未执行收集；r3保留venv绝对路径后完成。两原stdout／stderr分列保留，不把驱动错误改记成功。


## 新独立最终本地结论

新的fresh-context[独立报告](2026-11-15-training-test-maintenance-review.md)已给需求／维护性两轴approve，开放0／0；唯一P3范围计数已按实际清单修正并关闭。原报告14276B，SHA256为449dd695f129e24f69763b0a31984dea36cc2a85004ff20d4dd35f4613b711f7；后续发布／CI续核会追加，不改变此本地快照身份。该reviewer直接核固定输入、最终测试、原件、652源码／安装逐字、84nodeid、237引用及自身完整stdin；未新增昂贵运行或假称真实Windows通过。

现在进入本片普通提交／推送和自己的CI门禁；不合main、不强推、不提前实施后继控制器。将已独立批准的五份Q4.2c纯设计／报告一并同步，保持“设计完成、产品未实施”。


## 普通发布与自己的 CI 等待

已普通提交／推送e09fd60a635f16e9265b18d1529c4934e687f303，parent为ac86043，tree为966ca4edcb2a1594e3009b1e3095f0499815617e。13个最终staged blob逐项等于commit tree，完整SSH Ref相同；工作树提交时clean。原reviewer先核r1的13blob／242暂存引用，r2只纳入其状态追加报告，其余12blob保持；完整cached diff-check通过，产品／脚本／CI／依赖不变。实际commit／push／Ref命令和完整输出保存在本片私有publication原件。

首次匿名官方API查询返回403、remaining=0，官方reset为2026-11-15T07:22:59Z；原响应／metadata已保存。当前未取得本片自己的CI run或终态，不把配额耗尽称为CI失败或成功，不绕鉴权。等待官方窗口后续核，精确发布与自己的CI由原新reviewer同片接续；c2原失败及控制器未实施状态保持。


原新reviewer已独立核e09固定13blob／单parent／完整tree／diff／242暂存引用及完整SSHRef，固定发布需求／维护性两轴approve／开放0／0；原报告追加后21374B，SHA256为60b79b6f76ac91a13dc3096d74700c70c2cc4e4a3b73a71f24c1377c2a727092，原committed17733B前缀完整保持。403与reset原件也已核，只认证CI未知。本片产品完成状态仍待自己的真实CI与同reviewer终核；等待期间仅细化后继出生授权／父停止计划并作独立设计审查，没有实施其产品。


官方公开Actions页HTTP200的嵌入JSON已核：Portability #234／run43688128824精确链接完整e09 SHA、当前开发分支、push来源与07:02:26Z创建时间，状态IN_PROGRESS。原HTML320113B、HTTP metadata与局部提取另存；这是普通公开网页读取，不使用受鉴权API、日志或artifact，也不替代后续attempt／job／30必要步骤终态。API仍尊重同一官方reset窗口，当前不能称本片CI已通过。
