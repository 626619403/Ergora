# F10d5：原 Skill 评价、明确采用与回退页面旅程

日期：2026-11-14。依赖[F10d4](2026-11-14-frozen-leaf-console.md)固定普通发布；实施基线固定为 `055b0c44d7bd2bb7c1375b82471ec7ca00c40605`；已用原安装件完成实际基线复现：6项／3样本／3.630秒，确定三类静默界面问题，原skills.js已最小修复并完成最终r2本地验收，新的独立最终本地两轴approve／开放0／0，649原引用与R1/R2关闭已核；普通发布／自己的CI待，不继承其他包／CI成功。每步回写本页、[交付](../delivery/2026-11-14-skill-improvement-console.md)与[PLAN](../PLAN.md)。

## 已核的原实现

`skill_assets.import_bundle` 持有完整目录身份、父基线与初次 head；后续导入只登记候选。`evaluation.register/suite/evaluate/get/compare` 持有可信文件身份、同 suite 的完整 train／validation／holdout、正确性、成本与改善门禁；evaluate 在进程前保存原评价记录，失败也是原记录。`skills.adopt` 每次重新 compare，再以 expected revision／baseline digest 调用原 move_head；`skill_assets.rollback` 只回到曾活动版本并记录明确理由。原 CLI 和 HTTP 都已存在，不再增加另一评价器、采用账本或批准者。

`skills.js` 已有导入、diff、双方评价、比较、明确采用／回退与历史，但尚未验冻结候选经页面进入完整闭环。当前 evaluate/compare 完成后可对全局 modal／旧 view 操作，比较后改变选择不会撤回旧采用表单；导入／回退完成也可能关闭后来打开的 dialog。这些是源码观察，需先以受控延迟复现，再在原 owner 内做最小修正，不预设全部需要重写。有限 GEPA 仍是独立候选入口，沿其原支持范围，不借此片声称自动优化质量。

```mermaid
flowchart LR
    A[完整冻结结果] --> B[原检查与明确导出]
    B --> C[原 Skill 导入候选]
    C --> D[同一可信 suite 分别评价]
    D --> E[原完整证据比较]
    E --> F[用户给理由明确采用]
    F --> G[原历史与明确回退]
```

模型回复和来源审查不能跳过 D／E／F；一次评价进程成功不等于 eligible，eligible 不等于已采用。

## 拟实施与验收节点

- [x] 固定 F10d4 普通发布基线，核既有 caller、原字段、最终源码／配置身份与本片变更范围。先复现旧响应／旧比较可达场景，只有实证需要才调整产品。
- [x] 沿原 `skills.js` 收拢当前选择、diff／比较代际与原 view／modal 生命周期；版本／suite／评价记录变化使原比较和采用就绪失效。旧回复、旧 finally、页／项目往返或 modal 替换不恢复旧状态、不关闭新窗口或发旧全局通知。保留一个原业务 owner，不为局部 UI 创建插件框架或页面状态账本。
- [x] 评价、导入、采用、回退均由明确提交触发；对应动作在途防重入，展示原提交的版本／suite／run／head revision，失败或丢回复不自动重发。使用原记录／历史明确刷新核对，不将请求异常当没有执行；原 saved failed 状态如实展示。不得用表单重复验证可信 scorer 或把源 preview 当租约。
- [x] 采用只消费当前完整原比较的精确两 run ID、当前 head revision 和用户理由；调用前后权限与最终并发门禁仍归原 owner。回退沿原曾活动版本／revision／理由；导入、模型 approve、比较 eligible、采用成功与回退成功分别展示。不推断模型有采用权。
- [x] 最终非editable包／两RECORD／283和受影响原suite；实际页面从标准完整导出目录导入候选，可信 fixture suite 双方评价／完整比较／明确采用／回退至原head，原CLI读回全部身份与历史。明确标注确定性提案／scorer，仅验合同；真实模型 null 与本片合成正例分开，不称真实质量或性能改进。
- [x] 真实HTTP／浏览器核不合格候选、跨项目、错 suite／run、stale head／scorer变化、在途重复、丢回复后原记录、迟到成功／错误与页面／modal替换；选择与配置按实际值验证，不断言固定默认。三宽、完整原件／scorer／资料保持及进程／端口收尾；未验排列单列。
- [ ] 运行自身原结构审查模板，另启动本片新的 fresh-context 独立审查并关闭实证 finding。完整证据／进度写入项目文档，再普通发布当前开发分支／核完整 Ref／本片自己的必要CI与原 reviewer 终核，不合 main。

## 后续范围

记忆候选的原 save／修订冲突／有效期／恢复，以及流程候选的原 import／新版本选择／旧 manifest 保持，分别按原语义验收，不能套 Skill 评分或伪造共同采用权威。随后闭合 F10 完整受评价旅程、F9d 的完整实验控制旅程与 G1 新安装／升级回退／跨机交接；真实 B3 与完整原生 Forge C2 保留已有外部条件。

## 实施检查点

原基线的三个可达问题已在真实浏览器复现，6项／3样本；无模型或采用／回退。基线使用F10d4最终r3安装件，skills.js逐字等于055b0c44；服务／浏览器已停止，head保持初始revision1。

已在原页面收拢选择代际、原view与原form生命周期：更换版本／suite／run撤回比较和采用表单，迟到读回复按代际隔离；双方评价共享在途锁。导入／注册／采用／回退与GEPA使用局部明确提交回执，显示原提交与完整返回，只由用户明确刷新读回；异常不自动再提交。原全局UI helper／后端门禁不变。语法静态通过，最终安装、真实页面、原CLI、自身模板和新的独立审查待。

原r1非editable包603／两RECORD611／616／283、原Web＋Skill两suite44通过／46.78秒；页面主旅程23项／10样本及三宽通过，明确采用到revision2、回退至原baseline revision3。自身原结构模板Codex59.162秒request-changes提出R1跨标签在途锁与R2刷新后旧窗口silent submit，另实际复现3项／2样本，独立确认并已在原skills.js修复；旧r1成功及finding均保留原身份。R1加入仅本窗口按控制目录／项目隔离的未决HTTP锁，完整返回释放，unknown须用户读原记录后明确确认，不推断run归属；R2旧form显式提交给局部重开提示且不发请求。最终r2包／对应动态回归与审查待，不借r1证明修复。

## 最终r2本地验收

最终r2包603／两RECORD611／616／283、原Web9／11.73秒；75个原Python／测试文件r1/r2逐字同一。实际页面68项／46样本、97原HTTP／10真held／1夹具503、三宽，原CLI11操作与完整对象／目录同一，自身原模板Codex59.561秒approve；原件保持、原head恢复baseline revision9／9历史／10评价、服务／浏览器／线程／端口全部收尾。R1/R2已实证修复，新的独立649原引用／负例／CLI／收尾均已新独立最终本地两轴approve／开放0／0，R1/R2关闭；8独立证明与5发布调用器追加为662引用，普通发布／自己的CI待。旧r1、端口／socket驱动失败、缺split负例及单独修正suite均保留原身份；GEPA只跑原安装回归，未声称其页面全流程、全故障矩阵或真实质量。细节以交付／证据索引为准。
