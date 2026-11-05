# G0.1：全新用户安装、登记与无模型旅程

日期：2026-11-05。状态：全新安装、两项目登记、无模型CLI/浏览器、数据保持与正式退出本地验收及[新的独立审查](2026-11-05-new-user-onboarding-review.md)通过，无未解决finding；纯文档提交推送与同片终结待完成。前置F5.5精确文档`cd0b5a0a7d5301e30ba5febe45e4e73ba7e218a4`普通推送及综合独立审查者的远端终结已通过；生产资源仍为F5.4接受身份。来源：[G0分片计划](../plans/2026-11-05-new-user-acceptance.md)。

## 设计与验收

1. 通过公开Bash安装器，以development组合安装到从未存在的持久路径，核非editable来源和352资源/冻结283。另建基础无SDK接收者，使用已接受wheel，记录其真实归档身份。
2. 新控制home、原生Python3.12依赖venv、参考runtime/config/state和两个业务Git根，原生依赖按原lock/hash同步。参考源码来自随包资产，固定Temporal/Symphony来自已校验缓存；Python/Git/uv/Node/Codex及用户认证是复用前置。旧一键完整安装器的系统包预检缺zip/sqlite3/psmisc，保留实际exit1；本轮没有系统安装权限，不运行apt/sudo，不把手动用户目录准备称为完整空OS一键安装通过。
3. 原生init/templates/模型元数据/可信当前容器enable使用公开命令；仅在配置中选择阶段墙钟600秒/并行2，记录实际人工配置。凭据只引用已有变量名/登录，不复制或公开密钥；不启动服务或模型。
4. 两个业务repo各一次完整`project register`；项目可信检查在操作者目录，来自固定行为/依赖/知识及集成/兼容/回滚合同。模板copy及输入使用公开格式，不直接写DB、不手改生成的Supervisor ini。
5. 公开CLI读取profiles/配置/发布/诊断与停止状态；模板预览/创建/同意图重复、旧revision拒绝。无服务时start实际失败、保留原prepared/unknown意图，按原ID查询；不伪造运行或自动重发。关闭服务时本地合同/创建仍可读取。新HTTP/浏览器可显示新项目/任务/原记录和明确失败，桌面/390px可用。
6. 文档/记录每步更新，新fresh-context独立审查、普通文档提交推送与同片终结。后续G0.2恢复同一新数据旅程并实际运行模型；本片不代替真实六阶段、空OS/Windows本机或GPU验收。

实施只使用忽略的`.ergora/checks/g0-onboarding/`私有辅助脚本/日志及持久home目录；浏览器产物在`output/playwright/g0-onboarding/`。没有计划新增生产抽象、测试框架、CI作业或重复全量矩阵；发现产品缺陷再划独立修复子片。

## 安装前调查

当前参考`agent_platform.cli.task_action`在任何本地提交前调用原doctor，后者明确检查Temporal和A2A监听；旧README和Agent手册示例只列temporal/worker/executor，会在全新环境被准入拒绝。已将完整示例补a2a，并说明MLflow观测可后配，服务管理仍不隐式补依赖。此为源码可证的文档修正，实际新环境启动/提交留G0.2验证；未改变冻结准入或声称本地执行已与通信解耦。后续F7跟进其版本化adapter边界。

## 安装检查点

公开Bash development安装器在全新持久app/bin路径实际exit0（58.78秒）；另建无SDK基础接收者并安装原f644858归档，新原生Python3.12 venv按原requirements.lock/hash同步exit0（54.62秒）。两个安装都不是editable，352资源逐项等于已接受源码/包，冻结283及新runtime Python源码身份通过；原生venv是新目录而非指向旧环境的symlink。安装/初始化结束时control home和新Temporal库均未创建，四服务端口关，没有模型/服务启动。这里的秒数仅是当前已有工具/cache条件下的实际命令耗时，不是空OS安装性能。

参考源码复制、固定二进制缓存校验、依赖同步及公开native init/templates/configure-model/可信enable均有独立原命令exit0；仅写模型元数据和新本地A2A令牌，未复制旧密钥/数据库/state/workspace。Python/Git/uv/Node/Codex与已有用户认证继续是复用前置，完整系统一键安装器未执行。下一两项目公开登记及无模型CLI/浏览器旅程。

## 无模型CLI检查点

两个新业务Git根各通过一次完整project register（revision1）、一次公开reviewer选择保存（revision2）；原生投影一致，无双注册或手改ini。原fixture基线的9项项目可信检查通过，两个模板复制/preview/create与相同意图重复通过，旧revision1被拒绝。四端口始终关闭时，两次start按原准入实际exit2，submission保持prepared、attempt_saved=false/run_id=null；重复start返回同一原prepared记录并按CLI合同exit1，没有派工或盲目重发。原合同/创建记录仍可离线读取，profiles/配置/doctor/主动探测/服务停止状态均有原命令证据。

首轮辅助脚本误将重复prepared的exit1预期为0，因此整条脚本exit1；CLI行为正确，原源码/记录/日志保留。修正脚本预期后只读回22个已成功命令、不重做已有登记/创建，以新标签补后续命令并exit0。两轮合计53个实际子命令（40次ergora CLI、9次可信检查、4次Git）；归一旅程52条记录不包含额外那一次正确exit1的重复start。未修改产品或将首轮失败改写为通过。下一新浏览器核本地合同、原prepared和显式缺服务错误；真实运行仍归G0.2。

## 模型配置边界

本片仅准备Codex的`gpt-6.1-sol`/medium元数据，阶段墙钟600秒、最大并行2，尚无模型调用，不据此推断认证或模型可用。公开configure-model helper未暴露provider的`supports_websockets`，因此在新codex.toml中手工保留已知HTTP provider所需的`supports_websockets=false`，变更前后SHA与理由单独保存；没有复制凭据。实际人工配置面为platform.json的墙钟/并行与codex.toml的HTTP选项，供G0.3计数。后续真实模型token与费用未知时继续显示未知。

## 新浏览器、数据保持与退出

新HTTP与独立浏览器会话从新控制库读取两个项目的合同、任务及原prepared记录；恢复窗口显示的submission SHA逐项等于原CLI。测量交互阶段共14个API GET、零POST、零pageerror，没有模拟响应或派发动作；另有HTTP readiness的一次bootstrap GET及页面初载请求，此14次不代表全部HTTP流量。桌面与390px截图通过，长SHA及恢复窗口没有水平溢出。

两任务尚无真实run ID。为核实服务不可达的显式错误，在运行查询框填写测试opaque值`unsubmitted-g0-read-probe`，两次真实status请求均400/connection refused；该值不是原生run ID，也不作为真实运行观察。恢复按钮可达但未点击，prepared意图保持不变。

浏览器正式close exit0、owned进程退出。HTTP身份核验后SIGTERM、有序关闭，工具session取回实际shell143；临时根空。本片四执行服务端口及owned HTTP共五端口关闭，尚无Temporal库、claim库或托管Supervisor socket；新control库保留。两个业务repo仍为固定基线且干净，原生任务文件语义与creation intent一致，submission只有原intent、没有attempt/result，requests/receipts/artifacts/approvals/fences均空。原F5的139文件、两旧repo内容/HEAD/refs/worktrees及3条claim/0 active lease未改变；新原生文件SHA与原Supervisor ini身份已保存，作为G0.2增量基线。

最终核验命令`python3 .ergora/checks/g0-onboarding/run-check.py verify-onboarding python3 .ergora/checks/g0-onboarding/verify-onboarding.py`实际exit0（0.78秒）。私有结果为`onboarding-verified.json`；浏览器原结果、生命周期及6张截图分别在本片checks目录和`output/playwright/g0-onboarding/`。这些结果只覆盖新安装与无模型旅程，G0.2的真实六阶段/批准/取消/导出尚未运行。

## 本地独立审查与精确交付

新的fresh-context审查者独立核11文档/368链接与锚点/30 README parser命令、现存两安装352资源/283冻结、新runtime/依赖与固定二进制、53子命令/22只读恢复、浏览器原结果及三张代表截图、新旧数据与生命周期，需求符合性及结构/复用/必要守卫/成本均通过，无findings。未重跑模型或重型矩阵，精确提交/普通推送与实时远端终结仍单独收口。安装日志的新app归档为`40064f8b1c186caffd2dbced6a18722e5c238c86b68383b108ddc85e8ef56c11`，其352资源同已接受内容；只有基础接收者使用原f644858归档，不把二者混称为相同wheel字节。
