# F6.1：编辑器比较独立审查

日期：2026-11-05。审查者：新的 fresh-context agent `/root/f6_editor_comparison_review`；未继承实施对话。按根 `AGENTS.md`、`maintainable-project-delivery` 及其 independent-review 指引审查。范围为 [F6 计划 E1–E6](../plans/2026-11-05-low-code-editor.md) 的比较原型、实测选型和复现材料；F6.2 编辑缓冲、撤销重做、修订冲突及 F6.3 容量不是本次生产功能验收。

## 本地结论

**需求符合性暂不通过，存在两项 P2，须修复后复审。** 原始三方案六旅程、原后端语义一致性、成本和许可证据在所检查条件下成立；公开全新安装步骤缺少服务器依赖，另有图形连线起点跨模板残留的可达故障，因此尚不能关闭 E2/E3/E6。

**可维护性暂不通过，仅需局部修正生命周期边界。** 实际所有者和复用方向合理，未发现需要新增框架、生产依赖、测试框架或 CI job 的依据。保留现有栈的 ADR 有限范围内有证据支持；不因本报告认可选型而推断未实现的正式编辑功能通过。

## 检查身份和范围

Git 基线与审查时 HEAD 均为 `df0a908893970d12208b3a2026d19b4591f83989`，分支 `refactor/architecture-foundations`。独立重算 `.ergora/checks/f6-editor/review-scope.json` 所列 **25 文件**的字节数及 SHA256，全部一致；实际 tracked diff 逐字等于 `review-tracked.diff`，实际未忽略新文件恰为清单中的 18 文件。清单 SHA256 为 `5875f74306a0e51f845388e2d827541eb0e74060cfae33b48fe9d29ebca39ad1`；diff SHA256 为 `2424669efb09f202924da94d6f973a930c24f14a2c53a314992c147209d5067e`。这些身份指本报告写入前的候选。

完整读取新增 15 个例子文件：`examples/editor-comparison/` 下 `README.md`、`THIRD_PARTY.md`、`package.json`、`package-lock.json`；`prototype/` 下 `app.js`、`build.mjs`、`serve.py`、`cytoscape.js`、`react-flow.jsx`、`schema-form.jsx`、`native.jsx`、`flow.jsx`、`schema.jsx`、`index.html`、`style.css`。完整读取新增比较研究、ADR0003 和 F6.1 交付记录。

另检查 7 个 tracked 文档的完整差异：根 `README.md`、`docs/PLAN.md`、`docs/architecture/current.md`、两份 V5 交付/审查记录、all-in-one 计划、F6 计划；读取当前检查点和本片验收条件。V5 追加终结作为上一片的归档事实处理，没有递归重审其 CI 或 G0。邻近源码核查包括默认 `workflow.js` 所有者、`api.js`、`web.py` 的模板/草稿路由和 CSP、`drafts.py`、`reference.template_details/validate_input`、两模板输入/schema、`pyproject.toml` 及原 Cytoscape 资产。

`src/`、`tests/`、`pyproject.toml`、`.github/` 相对基线没有差异，构建输出和安装目录实际被忽略；没有把私有验证脚本或生成资产混进这次新源码集合。

## Findings

### F6-01 · P2：公开全新安装步骤未安装 Web extra

位置：[例子 README](../../examples/editor-comparison/README.md) 第 19 行；关联 [服务器入口](../../examples/editor-comparison/prototype/serve.py) 第 5–7 行和 [包依赖](../../pyproject.toml) 第 11、20 行。

可达场景：读者按 README 建立默认不继承系统包的全新 venv，执行 `pip install .`，随后启动 `prototype/serve.py`。默认依赖只有 PyYAML/jsonschema，FastAPI 和 Uvicorn 属于 `[web]` extra；服务器直接导入两者，因此该公开路径不能启动。现有成功 HTTP 命令使用已有 G0 Web 环境，只能证明服务器在那里能运行，不能证明公开的新环境步骤成立。`bash -n` 和 CLI parser 检查也不会发现 Python extra 缺失。

后果：违反 E2/E6 的开发者可复现入口要求；已成功的 npm clean install/build 不覆盖这个缺口。

最小修复：把例子安装命令改为 `pip install '.[web]'`；用基础新 venv 验证该公开安装命令、Web 导入及比较入口正常启动后关闭，更新复现记录与候选身份。无需改变默认依赖或重跑未变的重型矩阵。本审查没有安装新环境，将依赖声明与入口的确定性不一致作为 finding。

### F6-02 · P2：Cytoscape 待连接起点跨模板或重命名残留

位置：[Cytoscape 适配器](../../examples/editor-comparison/prototype/cytoscape.js) 第 20–27、31–42 行；关联 [连接回写](../../examples/editor-comparison/prototype/app.js) 第 123–126、142–145 行。

可达场景：在 native 或 schema 页面 Shift 点选治理模板的 `knowledge-map` 作为起点，切换到 large-change，再点击 `integration-tests`。`update()` 已重建全部节点，却保留旧 `source`；下一次点选仍触发 `onConnect('knowledge-map', 'integration-tests')`。回调将不存在的起点写入新模板的 `depends_on`，随后重绘失败。相同问题可由待连接节点被重命名后再点终点触发。

独立小型检查使用交付适配器实际注册的 tap handler、正常事件形状、真实两模板输入和原 Cytoscape 3.33.1 headless 投影，在同一 Node 24.18.0 realm 中确认：新模板不含 `knowledge-map`，回调仍返回它，实际库抛出 `Can not create edge ... with nonexistant source knowledge-map`。这是源码/真实库层复现，未冒称 live 浏览器复现；前两次探针的模拟事件及 VM 跨 realm 问题不计为产品失败。

后果：一次普通模板切换后的连线操作污染未保存输入并中断图重绘；依赖下拉框只列新模板节点，无法直接选到这个残留起点以移除它。现有 20 请求的图边界旅程没有覆盖这条状态转换。

最小修复：在图的 `update()` 重建生命周期取消待连接起点，避免旧交互意图跨重建继续使用；沿现有适配器局部处理即可。补一条真实浏览器的“Shift 起点→切模板/重命名→再点节点”验收，确认不加入不存在的依赖、无 pageerror，并确认正常 Shift 连线仍可用。无需引入通用交互状态框架或生产测试套件。

## 已核实的行为、结构和成本

安装/构建记录的真实参数、工作目录和退出可核：例子 `npm ci --ignore-scripts --no-audit --no-fund` 实际 exit0，安装 36 包；默认 `npm run build` 实际 exit0，记录约 1.37 秒。锁包含 61 条非根包记录，其中含未安装平台可选包，registry/integrity 和固定直接版本齐全。独立逐字比对实际安装包的完整 LICENSE/NOTICE 与生成许可总文件，36 包及原 Cytoscape 均覆盖，许可总文件 SHA256 为 `04df8e89fe33099733b3415cbf2ba8a85129c4191a35473f42fed5b06f4cf050`。

三份 `final-journey-{native,flow,schema}` 的实际命令脚本逐字等于脚本文件，stdout 中原 Result 等于保存的 JSON，实际 exit0；每份 29 请求/22 POST、两模板、零 pageerror。原始结果包含真实拖动位置变化、环和越界路径的原服务端 400、输入/非法 JSON 保留、JSON 往返及保存摘要一致。键盘证据是选择器 End/Tab 和按钮 Enter 的 smoke；窄屏结果均为 390/390，抽看桌面原生及两候选 390px 截图，主要表单、依赖、校验和保存控件可见。滚轮手势后摘要不变有记录，未独立记录前后 zoom 数值，不把它扩大为完整缩放或无障碍审计。

额外图边界的原命令/脚本/stdout/result 相符，20 请求/2 POST，覆盖实际 Shift/端口连线、自引用重命名后的后端拒绝、重复 ID 不改输入及 NoValidation 空 ID 保护。合计 107 请求/68 POST，POST 只指向原 `drafts/validate` 或 `drafts`。这些既有通过结果不覆盖 F6-02 的遗漏路径。

独立通过 immutable 只读 SQLite 核实：16 表中仅 projects=1、drafts=6，其余为 0；六草稿均 r2，治理三份摘要均为 `629e49553fd8b7ef05739d1f3249b9f00c88a3cc12c7a3523cb2a77643cceccd`，大型开发三份均为 `9817eea773d8a0d4cac7af4ec5bb17fa1be2531cb9c82200c9b2ebf1130d314c`，与原结果一致。数据库 SHA256 仍为 `78d2c0ce28902aaa6bd36ee4615e0dbb90a1ead8a6cac1fafd23018a6e8776e8`，试验 Git 项目干净。未向该库写入。

HTTP 逐字同构建、原 CSP 和无 Content-Encoding 的证据绑定最终源码；独立重算现有资产 raw 和同参数 Node `gzipSync` 字节，全部等于构建表。三独立入口自动资产集合 raw/gzip 分别为 447,556/144,194、408,566/128,660、907,329/291,000 字节。法律文件另列，API 响应和实际 transfer/encoded 字节分别保留；没有将估算 gzip、模块记录数或开发依赖体积说成实际下载/生产复杂度。React Flow 此构建确实较小，ADR 没有反向宣称它必然更重。396/384/486ms 是固定 Chromium155、loopback 和逐次草稿库条件下的单次观测，未用于速度排名或容量承诺。

默认 JSON Forms 失败保留为实际 exit1：原源码 SHA 与失败记录一致，console 明确是 Ajv `new Function` 被原 CSP 拒绝。三份已保存官方来源的字节/SHA 独立一致，其内容分别支持 CSP 限制、standalone 路径和 NoValidation 的定义。最终入口确实使用 NoValidation，只生成固定 schema 控件，显式校验仍由原后端拥有；没有将其混为默认 Ajv、预编译或任意 schema 成功。

结构上，`start()` 有三个真实入口消费者，原生表单有两个，Cytoscape 适配器有两个；React Flow/JSON Forms 各单入口适配器是对应库投影/React root 生命周期的合理私有所有者。DOM helper 留在例子，未造跨项目工具层。构建直接读原 schema/API/Cytoscape，服务挂载原 `create_app`，原 `reference.validate_input` 和 `drafts.save` 继续拥有领域规则、摘要及 revision。没有第二个 validator、执行器或 DSL。

空 ID/重复 ID 保护对应无法可靠投影的外部编辑输入，不能因服务端另有校验而删掉；自引用/路径/环仍交后端，未重复实现领域算法。epoch 只保护已声明的快照路径，资料没有把它写成 F6.2 完整迟到失败/编辑缓冲保护。许可缺失显式失败、可选平台 ENOENT、资源 destroy 和错误可见处理有实际边界用途。未发现本片新增冗余生产 tests、CI 或断言；私有同旅程断言检查的是合同/服务端摘要及实际操作结果，不应为本次两个修复扩建测试基础设施。

两轮 HTTP 原日志均含 shutdown complete，SIGTERM 子进程 -15 与包装 241 分开记账，浏览器 close 实际 exit0。审查时另核两 owned PID 已消失、8981 拒绝连接，DB 摘要保持；未重启或停止任何服务。现有 `git diff --check` 也独立 exit0；12 文档/340 链接、30 条 README parser 及例子 Bash 语法检查的原记录可核，但它们的边界不覆盖 F6-01 的依赖安装。

## 未验范围及后续终结

本次没有安装依赖、启动服务器/浏览器/模型、重跑生产全套或矩阵、提交或推送。没有新增真实任务、Agent、Windows/其他浏览器原型或 50/200/500 容量结论；并发/跨标签冲突、完整编辑缓冲、撤销重做、任意 schema、standalone Ajv 仍未验。默认沙箱曾因 bwrap 挂载权限失败，若干只读自动审批曾超时；获准的后续有界读取已完成所需身份与证据核查，没有把这些工具问题写成产品失败。

实施者应保留本轮两项 finding 及原结果，修复 F6-01/F6-02、完成受影响的精简验收，更新交付/计划与完整 scope 后交同一审查者复核。修复后的 bundle 体积/HTTP 源码身份如有变化应重新绑定，不沿用旧通过覆盖新资产。

本地复审通过后，仍待普通精确提交/推送、精确远端及该候选自动 CI 的实际结果，再由同一审查者作同片终结；此前不能登记 F6.1 完成。本报告只写指定审查文件，不替实施者修改源码、记账或执行交付。

## 两项修复的同片复审

2026-11-05，同一独立审查者保留以上初审原文并复核修复。**F6-01、F6-02 在本次已读源码及结构化回归记录的范围内关闭；需求与可维护性在该范围通过，无新增 finding。当前候选的独立身份复算及精确交付仍未完成，F6.1 尚不能登记全部完成。**

实际 Git 读取仍为原 HEAD `df0a908893970d12208b3a2026d19b4591f83989` 和原分支。已读 `fix-review-scope.json` 的26文件清单，包含初审报告原11,848字节身份。提供的清单 SHA256 为 `3628007b4b0655ba890a50e465058ba60af879d6a348602ea9668c9f736604ab`，tracked diff 为 `4f9a306143d2238c5d4cee43dbfa4c4232f15fa1f127090cf41c34fc02ee307c`；本次未成功独立重算这两个摘要、26个文件身份或当前diff相等性，不能将提供值冒称自己的复算结果。

完整读取当前例子 README 和 Cytoscape 适配器。F6-01 的安装命令已正确改为 `pip install '.[web]'`，与既有服务器导入需求一致，没有改变默认依赖。读取新venv创建原命令exit0、`fix-local-verification.json`及生成脚本：记录不继承system-site-packages，实际安装位置中的Web/FastAPI0.162.0/Uvicorn0.54.0导入及pip check通过。专用HTTP原日志确有startup/shutdown complete。原pip安装工具成功没有完整落盘stdout，本次不补造回执，也不把venv创建回执当作安装回执。

F6-02 仅在图 `update()` 重建前清除 `source`，生命周期边界正确，正常第二次tap仍能取走当前起点并提交连接。完整读取红/绿脚本和绿例结果：真实Shift/鼠标覆盖native/schema两入口的跨模板取消、重命名取消及正常连接，语义输入比较和原后端校验通过；结构化结果18请求/2校验POST、零pageerror，无save/task。核验JSON内嵌实际命令为exit0，内容与已读脚本相符。红例stdout保留原不存在source异常；辅助匹配遗漏错误消息反引号而失败，不得写成完整红例通过。另一次只读eval没有本次可审的原回执，不作为新增通过依据；绿例独立stdout读取审批超时，未宣称已逐字核对它与结果文件。

完整读取修后本地/离线核验JSON、生成脚本、停止请求和HTTP日志。它们记录15源、13资产逐字匹配、原CSP/无压缩、两16表库（旧库六r2及原摘要、新库零草稿/Agent）、正式SIGTERM及新shell143/浏览器0；这些是本次已读的验收记录，再次校对实际资产、两库、venv配置和关闭状态的独立命令未执行成功，本次未将其重标为审查者再次实测。

读取当前研究、交付和检查点：修后入口raw/gzip已更新为447,564/144,198、408,566/128,660、907,336/291,001字节，表内加总与核验记录自洽；旧107请求、六r2和396/384/486ms明确保留修前源码范围，修后另记18请求。没有新增框架、helper、生产tests、CI或默认依赖；局部修复和行为断言足以保护已发现路径，未扩大选型、容量或性能承诺。

`static-after-fixes.json`记录13文档347链接/30parser，但PLAN、F6计划、交付三份SHA早于新scope的后续状态追加，不能冒称覆盖新scope逐字身份。应在本节追加后运行最终静态并刷新scope。默认沙箱仍实际报bwrap挂载权限失败，多项只读自动审批连续超时，包括原生sha256sum；超时没有风险否决理由，不是产品失败。未完成的候选身份、实际资产/库及原回执核对保留为终结前条件。

后续须从普通精确提交的实际Git对象核文件、唯一父节点和source/build身份，补齐上述未验项，再核实时远端及该候选自动CI必要步骤。当前尚无这些终结证据。F6.2/F6.3、容量/其他OS等原未验边界继续保持；本次仅追加报告，未安装、启动服务、改源、提交或推送。

## 固定候选身份与 CI 待终结

2026-11-05，独立核固定普通候选 `b1dbe48a1b14e8e2ec59d4f44e30b2ea367fa1fe`。**本地需求、可维护性和精确候选身份通过，两项P2保持关闭；CI具体必要步骤仍pending，F6.1尚未全部终结。** 没有将未来HEAD或下一片计划当作本片候选。

07:15:07 UTC实际核Git对象：唯一父为原df0a908，恰改26文件，集合及每个blob的bytes/SHA逐项等于candidate-scope；清单自身SHA256为`c47c3c144ca8444d64454e92ceb74f319442c7e0668cb3aa3f40ccc8de70fc7d`。15例子源码全等修后验收记录，src/tests/pyproject/.github相对唯一父无差异。候选初审报告前11,848字节摘要仍等原f96efc8，历史未改。最终static-after-fixes的SHA等候选绑定值`32e5053f58b1355301a1132bd79d55f0db5dd5b641b85dfc4123d9f75787d5c6`，13文档摘要逐一等候选blob、347链接无缺失/30parser。它是复审后实际重跑的新记录；旧同名静态文件的历史叙述不代表旧字节仍在。

上轮其余未验现已补齐：实际13资产bytes/SHA及完整许可等修后记录；两库immutable只读摘要/16表计数相符，旧六份r2及两模板摘要保持、新库零草稿/Agent。green原stdout的Result等保存JSON，实际命令脚本相同、exit0、18请求/2校验POST、零pageerror。新venv实际配置为Python3.12.3且不继承system-site-packages；owned PID3148771消失、8981拒绝连接。未安装、启动服务、重跑浏览器或写数据库。

读取07:00:49 UTC普通push回执exit0、远端df0a908→b1dbe48；审查者复用已授权的每命令SSH设置，于 **2026-11-05 07:26:47.876834 UTC** 独立实际ls-remote exit0，分支完整SHA为b1dbe48，与候选一致。没有输出或落盘认证设置、读取私钥内容或修改认证配置；此为该明确时点事实，不推断未来分支不会继续提交。

官方 [Portability 41984232370](https://github.com/626619403/Ergora/actions/runs/41984232370) 原run HTML含精确b1dbe48完整SHA及Success，163,665字节，独立SHA256为`6c0200d85d6611887194c271e7ffc5cea5115f5f1b64c88f58c6007e46e825a0`。Ubuntu原HTML为168,329字节、SHA256 `14c81c7b575072a37df84fa3f1a30d5d92be4fad2d0b2cb3d90799fa1754ec28`，selectedJobId127101114113，包含精确候选/run。jobGroups记此Ubuntu completed/success，也明确totalCount=2、hasMore=true；一项可见不等于Windows未运行。

**尚待两个job的实际必要步骤核对，尤其Windows。** 已读候选Ubuntu3.11/Windows3.12矩阵和wheel安装、包身份、原生回归、Windows安装升级步骤；尚未读到Windows最终job HTML，具体步骤只读定位连续自动审批超时。没有用总体Success或配置推断逐项通过。取得最终两job证据后再追加完整终结；当前无新增代码finding，但精确CI验收仍pending。本次只追加报告，未重跑CI、改规则、提交或推送。
