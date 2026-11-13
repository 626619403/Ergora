# F9b4b 原可信 runner 登记交付

日期：2026-11-14；基线 `fe26796a54b3804aac9272a9ea86643320a7f0b3`。[实施计划](../plans/2026-11-14-training-runner.md)。

原register_runner／core.write／executor占位符路径已核。复用原register_runner在隔离临时CONFIG中的预览及其真实不可变发布，不复制字段／argv／timeout验证，不执行命令。CLI `runner-preview / register-runner`、HTTP及训练页已沿同一training应用入口接入，基线与runner共用原setup模块、短本地DB预留及局部表单生命周期。原基线算法机械收为局部函数，SDK-free／Windows预览范围保持；runner需Linux／WSL2及可选SDK，无需服务。

规范化runner的canonical SHA与当前项目revision绑定确认；真实登记传规范化repo以固定已验证Git根。同内容可重试、不同内容拒绝；跨项目占用同ID时只报冲突，不展示外项目命令。原schema会把True视作1但正式start拒绝，支持入口明确要求整数，避免登记不可提交合同。CLI原文件与原生JSON各1MiB，不增runner数据库或替换开关。

源码首轮实际 **27 passed／45.25秒**：runner七用例、原baseline六用例及架构十四用例，使用明确PYTHONPATH和已有依赖环境；覆盖真实原publisher、规范化与同内容字节保持、错误SHA／旧revision／不同命令、真实写后丢回复与并发同内容、共享config归属、原件漂移／容量与symlink拒绝、CLI／HTTP共用入口。命令未运行，状态目录未创建。最终noneditable包／安装回归、真实CLI／页面及SDK-free受影响回归、自身模板、新独立两轴、普通发布与自己的CI仍待。F9b4a发布／CI另按固定候选收口，当前已补原两轴固定Git发布身份，自己的CI运行43520929146尚在途。

## 最终安装与实际交互

r1非editable wheel SHA `8d53c60ee378fecfdbbb994cbe174e6eda5657211bcede3fe46050ce59222860`；570产品逐字等于当前源码／快照／安装，两RECORD（wheel578行／安装583行）、283冻结均通过。安装四suite：runner／baseline／原训练观察／架构，**40 passed／65.54秒**，原monitor67.543秒，600秒界限未触。分组5的原CI插件收集 **364／1817，1453 deselected**，新七用例唯一归属；收集不是364项执行。

真实安装CLI的预览／错误SHA零registry写入／原register_runner登记／同内容重试通过，规范化repo与字节SHA均核对；完整原命令未执行。受影响baseline分支在实际`-P -S`、无site-packages／找不到Temporal SDK的进程完成原perfctl首次初始化。原生Windows未本地实测。

真实浏览器三组均返回passed：runner完整预览、错误SHA零POST、编辑输入后的迟到preview丢弃、连续两次点击只一次登记、同ID不同内容无替换按钮；真实服务写入后扣掉回执，重新预览读取原件再同内容确认，原文件SHA保持；真实preview与已成功发布的回执延迟到切另一项目后均不污染新页面。共享config外项目ID返回400且不展示命令。基线共用表单的原预览／错误SHA／编辑／双击／冲突行为完整回归。长argv与基线在1440／960／390均无横向溢出，390未发送runner表单也通过，已实际查看截图。

最初默认Chrome不存在导致browser open失败，保留原件后沿已有私有Chromium配置完成全部实际检查，无产品改动。浏览器仅两预期console错误：刻意丢弃的真实登记回复，以及外项目ID的400。原32份配置／基线／CLI runner原件SHA全部保持，四独立项目的runner与规范化输入一致，两个原baseline一致，其他项目runner未创建；无manifest／spec／job／fence／approval／integration-ticket，marker命令未执行，验收Git仓库clean。原monitor结束web进程组，浏览器关闭，原端口不监听。

## 自身模板、独立审查与发布

原`ergora-structure-review`模板实际审查10完整文件／214,529B，approve／53.359秒；全部内联文件及祖先／叶资源核实际stdin，结果SHA `b972a28c8ff913ff8d43e129da4eb98af8859a6749d383e80162a49f536b32d0`。用户授权Codex回退，不称异后端成功。该包涵盖全部新增第一方产品、测试／CI及原计划交付，未内联未改的原native owner；原owner实现由独立评审者实际读取，自身模型也明确保留其范围及当时尚待的运行证据。

新的独立[需求](2026-11-14-training-runner-spec-review.md)／[结构](2026-11-14-training-runner-structure-review.md)首轮源码及最终实际原件补核均通过、开放finding 0／0；未建议新增guard、抽象或额外测试。[公开证据](evidence/2026-11-14-training-runner.json)保留原30份私有原件SHA，并追加27份固定发布／CI原件，集中在`.ergora/checks/training-runner/`。产品8路径组合SHA `43634fafdf354cb60f212face64c28caa27e7d5f0979c32362dacfcf64f8f583`保持，后续状态记账不冒称新产品重测。最终普通发布 `80236fe8957c0704a3c73c7ea1440f7f288ff563`，23件Git blob及完整Ref均核对，原两轴补固定发布身份通过。自己的[CI43523861953](https://github.com/626619403/Ergora/actions/runs/43523861953)第三官方run HTML为Success，八job／30必要步骤全部success且有完整候选SHA日志路径与完成时间；原结构轴已直接核原HTTP／HTML、固定Git配置及全部步骤终核通过，开放0。未代称需求轴另作CI复核。F9b4c prepare继续独立推进。
