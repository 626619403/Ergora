# F10d3a：在页面选择完整复盘证据

日期：2026-11-14；固定基线 `6b7ebcc83f18c9b5d203eb47735bf3867f73b44d`。前片资料选择已普通发布，自己的 CI 与原固定发布补核另核，未闭合前不发布本片。[F10 总计划](2026-11-14-evaluated-improvement.md)／[当前计划](../PLAN.md)。

## 已核接缝与范围

原 `handoff.evidence` 已拥有完整整包 SHA、全部内部引用、显式 job/artifact 选择、原正文 UTF-8／NUL／1 MiB 准入及离线只读结果。CLI 已可用，正式任务页可下载原 handoff，但没有页面入口核包并选择完整复盘材料。本片先补这个共同前置旅程，不生成或采用候选，不调用模型／调度，不写记忆、Skill head、定义或第二账本。

增加“复盘改进”页面，由 `app.js` 的既有 view 接口调用；新增 `retrospectives.js` 是该页面内聚 owner，持有本次来源、目录、显式选择和迟到读取失效规则，不建立通用 UI DSL 或持久浏览器队列。后续 Skill／记忆／流程 prepare/check/export 共用此原证据入口。新页面不宣称这些尚未接入的操作已可点击。

只加实际消费者需要的一条 `POST /api/projects/{project_id}/handoff/evidence`，直调原 `handoff.evidence`；空 selection 读取原索引而不返回 artifact 正文，明确 selection 再读取完整正文。原 State 只检查当前项目，结果 index.project 不同则拒绝关联。本机可信文件路径和预期整包 SHA 须由用户明确提供；不上传、不提取 archive、不建立文件缓存或远端存储。保留原全包读取上限，选择上限不复制为第二校验器。

输入变化／重读先使旧目录和选中材料不可用；成功重读清空勾选。目录和选中正文分别有异步代际，迟到回复不得恢复旧来源／选项；失败保留输入，重读成功前不能使用旧观察。artifact 状态、原 run／outcome／取消结果与成本缺失原样显示，正文通过安全文本 DOM 全量披露，不把日志窗口当完整材料。可下载与 CLI 兼容的精确选择数组及完整原 evidence JSON；后者的 sha256 是原 canonical selection 身份，不冒称下载文件的字节 SHA。下载只由用户点击，切换页面／项目／控制目录后迟到结果不下载。

## 可验收节点

- [x] 核原 handoff／CLI／下载页面与缺少的实际消费路径，固定单一路由和 view owner。
- [x] 实现项目绑定的原只读入口和完整证据选择页面，原所有者／字段／来源身份不变。
- [x] 最终 r3 非 editable 603 产品／两 RECORD 611／616／283，原 web9通过；同原包实际下载→CLI／HTTP完整对象同一，原文件与数据库保持。
- [x] 错 SHA／跨项目／非 UTF-8／NUL／完整超容量拒绝；主旅程39／生命周期31、4真实迟到回复／两夹具503／三宽／两次Tab及服务浏览器收尾通过；Home与完整键盘／生命周期矩阵未动态验。
- [x] 自身原审查模板 Codex58.062秒approve；新 fresh-context 独立最终本地两轴／266原引用终核approve，开放0／0，R1／R2关闭。
- [ ] 普通推送／完整 Ref／本片自己的 CI 与原 reviewer 后继补核；前片自己的 Windows 安装升级 CI 仍在途，不预批发布。

每节点更新[交付记录](../delivery/2026-11-14-retrospective-evidence-console.md)和[当前计划](../PLAN.md)。F10d3b 再接三类候选 prepare/check/export，原单叶调用页面与完整评价／明确采用／回退旅程另续；不因本片可选证据而关闭完整 F10、F9d、G1 或真实 GPU／业务验收。
