# F10b：正式任务上下文选择交付记录

日期：2026-11-14；基线 `a2899e84bc174c9abd331a7c9d01f7c7a63297ae`。[合同](../plans/2026-11-14-task-context-selection.md)。v7／v11已实现并完成最终r2安装、原六阶段材料与实际CLI／HTTP验收；新的独立两轴最终本地approve、开放0／0；普通发布及自己的CI待。

已核实用户定义v1–6与冻结envelope v2–v10的区别，资源修订的 `operations`／`accepted_candidate` 合同、根资源继承和逐叶完整输入准入，以及原预算发布的SQLite写预留与task锁。实施沿原准备树和资源修订派生同id新根，不扩大权限、不导入活动库。具体实现及实际证据完成后逐步补记。


## 实施进度与开发失败

已实现用户v7／冻结v11、原根资源派生和源码来源复核，沿原预算／prepared／intent／锁及原六阶段消费者；Skill YAML只在metadata读取时导入，使原生发布者仍可在标准库环境读取已保存Skill身份。来源临时树显式进入原监督scratch，由原owner在失败／取消后清理。CLI与HTTP使用原任务入口，图形表单留F10d。

首开发回归6失败／36.42秒：原生`-S`桥因新模块顶层引入YAML失败，已改为局部依赖；第二轮6失败／54.52秒是测试夹具仍为text-only reviewer而选中了附件，产品按原合同拒绝，夹具明确选择task-mcp。第三轮6通过／59.96秒，覆盖来源冻结／标准库读取、预览后更正／删除／到期／同digest活动head revision变化，以及持久intent后的丢源恢复。随后调整scratch归属与补v7／context格式一致性，最终安装回归另验。

首实际材料旅程在work阶段失败：确定性fixture仅probe读取附件首段，新增完整Skill未读完；原门禁正确拒绝。已让context fixture沿既有分页reader完整读取各角色固定资源；原失败日志／原任务保留，后续新运行独立记录，不能重标首轮成功。修前扩大源码回归220通过／403.38秒；后续材料第二轮1通过／56.92秒。它们保留修前身份，不替代修后最终安装结果。


## 首轮独立审查修正

原结构轴以不写源文件的时钟注入确认：记忆catalog先采样，后续Skill核验若跨过expires_at，首次intent可能继续沿用旧有效判断。已把完整Skill核验放在前面，再读取原memory.catalog并采样时刻；原expiry参数回归专门在Skill get期间推进至真实期限，不改记录或预览。另按原Skill owner增加heads_only投影，显式选择不再反序列化所有候选和事件；memory-only选择不查Skill。原expiry参数修后1通过／10.07秒；最终包／模板见下文，独立终核仍待。r1包及自身模板只保留原候选身份，不借给修后版本。

修前r1非editable包577产品、两RECORD585／590及283冻结通过；实际材料第二轮通过56.92秒。自身原结构模板15完整文件286,786B及祖先资源进入同一prompt／stdin，42.100秒approve；这是修前原件，不称独立或异后端审查。需求轴先核原七叶prompt／materials／75,600B附件实读以及标准库读入，暂无已证finding，最终验收仍待。


## 修后最终安装与原材料旅程

最终r2非editable wheel SHA256 `3f677bcf50ffcb514c1a029ae9ca78857f12aaf4a72d5d32ecf17f25f79e1a21`，当前源码／构建快照／wheel／安装577产品逐字相等；两RECORD585／590和283冻结blob／执行模式通过。全部14件产品／schema／测试同快照。安装十suite **229通过／6跳过，412.30秒**（原monitor414.163秒），覆盖原native、budget、composition、worker、input、evidence index、Skill评价、架构、兼容及Windows入口。六项是Linux上的原Windows限定测试；v7原生准备仍为Linux／WSL2路径。

修后安装包实际原九job／七model slot完成inventory、plan、两个work与三个review；每叶读取同一冻结来源，七份实际materials指针一致，完整prompt与实际stdin逐字相等，七份所选附件75,600B全部覆盖。原creation intent文件SHA `d9962eee18104398ed180d56d20a7b24e5b8c8a0ae3a3c6002bb59a330a65474`；canonical更改／丢源后继续原件，九owner的stopped及collection-stopped均confirmed。该旅程使用确定性命令夹具，不代表模型理解、GPU、训练质量或性能改善。

修前安装r1也229通过／6跳过／412.98秒，monitored414.866秒；其wheel、修前自身回复与源码回归均保持原身份，不借给r2。

## 实际CLI／HTTP与准入反例

最终安装Python的七条真实CLI均退出0：目录、Skill列表、准备、预览、创建、删除记忆和同digest回退head revision。实际Uvicorn loopback四HTTP为200／200／200／400；CLI／HTTP预览相同，show原envelope相同。首次intent之后删除canonical记忆、移动head并删除原Skill bundle／manifest目录；HTTP resume-create仍与原CLI创建相同，旧选择的新preview400。只读核验原Git status保持、canonical记忆全部删除且正文／来源清空、head revision2、源bundle确已消失，归档仍可由原task_files读回；服务线程已停止、端口关闭。

首CLI／HTTP脚本在全部操作后误用`detail`而真实错误字段为`error`，出现KeyError；首次只读续核又把保留锁的publication父目录当成bundle，断言失败。修正为保存的version document路径后，只读续核通过，零重复mutation／HTTP请求。结果明确为复合旅程，不称首脚本无人干预通过。

安装包另验三反例：完整原v7 prepare分别因祖先同名Skill内容冲突、完整继承材料超过原material_bytes而failed，原process stderr保留具体原因，原outcome确认cleanup；没有creation intent或正式task。精确read反例沿生产selected_manifest作用于可成功编译的静态父图，新增selection.json的URI不在原read授权内，原compiler拒绝，派生临时树已清理；它不是精确read的原生六阶段执行。未新增权限解释器、测试框架或CI组。

准入harness首r2误取不存在的graph键，尚未执行prepare；r3正确观察产品failed后，在aggregate response中找具体worker错误而断言失败。只读续核读取原stderr，不重复conflict prepare；随后完成capacity／read。失败脚本与原failed准备保留，产品正常拒绝未改称产品失败。

## 自身审查与交付边界

修后最终安装环境使用Ergora原结构模板，15完整文件288,364B及全部祖先资源进入同一实际prompt／stdin，38.840秒原回复approve。prompt SHA `68230712f1748039708549eb7c915001655b1efbfab2fede33a1cbec897c2091`，input digest `d60ebb321cbb84b58b55e4589743b230bdffde7958b60e0297e408970c35c9d3`，result SHA `5b0fc07c370c1fbff6f011c54e14a048390bb28760a69ea867de1f222d0bd158`。授权Codex回退，仅源码建议，不替代fresh-context独立审查或异后端验收；输入文档保持当时尚在途的状态。

[公开证据摘要](evidence/2026-11-14-task-context-selection.json)保存上述精确身份和私有原件的大小／SHA。新的[需求轴](2026-11-14-task-context-selection-spec-review.md)与[结构轴](2026-11-14-task-context-selection-structure-review.md)最终本地approve，初审finding已修并复核，开放0／0；两轴各直接核164原引用、最终包、实际旅程和收尾；普通发布、完整Ref和自己的CI后补。F10a自己的CI及原结构轴终核已独立完成，只解除发布依赖。UI选择留F10d，复盘候选留F10c；原六阶段、预算、candidate／approval／attempt-before-send／unknown与283冻结文件保持。

已普通发布固定候选`f1cfcddd4d0e58b657b810b1f7dc98d070d255d9`，唯一父为原基线a2899e8；29份变化Git blob与最终清单逐字匹配，完整远端Ref相同，不合main。固定公开JSON为164原引用，后补四份发布原件为168；原两轴固定发布身份补核均approve／开放0／0；本候选自己的CI43545573942在途。

自己的CI `43545573942` 第三官方run HTML为Success：plan、六Linux组、Windows共八job／30必要步骤全部success，含Windows PowerShell 5.1安装升级及原回归／上传，fullSHA日志路径与完成时间均匹配固定f1cfcdd。早两在途样本保留，CI引用与固定164／发布后168分别列出；未读REST、日志正文或artifact下载。原结构轴CI独立终核approve／开放0，精确交付完成。
