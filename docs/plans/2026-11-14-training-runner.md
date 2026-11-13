# F9b4b：原可信 runner 登记

日期：2026-11-14。基线 `fe26796a54b3804aac9272a9ea86643320a7f0b3`；承接[准备总计划](2026-11-14-training-preparation.md)。F9b4a最终本地与固定发布两轴通过、普通推送及完整Ref一致；自己的CI43520929146已Success并获原结构轴终核，不借前片结果。进度与原件见[交付](../delivery/2026-11-14-training-runner.md)。

## 原行为与本片范围

原 `agent_platform.training.register_runner` 校验固定字段、Git根、完整argv及1–82800秒timeout，对repo做resolve，然后经原core.write不可变发布。该函数不运行命令；原executor在以后的逐实验run-local才替换`{manifest}`／`{output}`并执行。新入口仅做可信操作者明确登记；不扩大模板权限、启动训练或自动批准合同。

原函数没有独立validator。预览在独立reference子进程内暂时将该原module的CONFIG指向临时目录，直接调用原register_runner并读取其规范化结果，然后恢复CONFIG；真实项目配置不变。确认登记再调用同一原函数写真实目标，不复制其字段／argv／Git／timeout验证算法，不新建runner数据库。这个临时配置只存在隔离子进程，控制进程不装载原生全局配置。

## 可验收节点

|节点|行为|证据|
|---|---|---|
|R1 完整原预览|输入须属于当前注册项目／同Git根；调用原validator／serializer生成完整规范化runner、canonical内容SHA及当前同ID本项目原件。全局ID属于其他项目时拒绝，不跨项目展示命令|预览不改真实config／state、不执行argv；错误project／repo、原字段与walltime错误沿真实owner失败；原始CLI与原生JSON各1MiB|
|R2 明确不可变登记|当前revision＋规范化runner SHA确认，原safe_file检查真实目标，再调用原register_runner；同内容可重试、不同内容拒绝。已有ID不覆盖，不增替换开关|错误SHA／旧revision零发布；真实写后丢回复，重读／相同内容显式重试保持原字节；两项目共享config的ID冲突与并发保持原core.write语义|
|R3 共用入口与页面|CLI `runner-preview / register-runner`、HTTP同名POST及训练页JSON预览／确认使用同一training应用入口。基线与runner的同一局部表单生命周期实际共用，不增加全局状态框架|编辑／切项目迟到不污染、双击一次、长argv／三视口；基线原页面回归只测受影响公共行为|
|R4 精确交付|最终noneditable包／两RECORD／283、受影响suite、真实安装CLI／页面／原件及收尾；Ergora原审查模板与新的fresh-context两轴，修实证finding后补核|普通提交／推送、精确Git blob／Ref与本片自己的CI，不自动合main；未测维度保留|

## 所有权、支持范围与后续

setup沿原 `_TrainingProject` 核注册／control home／路径；baseline原发布与reader保持，runner新私有算法留该setup owner。需要拆函数时按两个不同原发布算法的凝聚性组织，不引入通用插件、可替代执行器或第二写入协议。应用层短本地DB预留期间核revision，不跨远端I/O；此登记没有RPC。

原training模块导入fcntl和Temporal客户端，runner的预览及登记仅Linux／WSL2且需`ergora[temporal]`；安装或导入不能证明服务可用，但本片无需启动服务。baseline现有SDK-free及Windows预览支持保持。原schema中的布尔值／整数歧义等若与正式start严格合同冲突，须在支持合同边界明确拒绝，不能让登记成功掩盖不可提交的runner。

F9b4c随后接原prepare三件发布／恢复，先查真实owner再定意图与部分发布语义。原job／fence／start／executor、evidence批准、GPU与真实B3均不在本片范围。R1–R3已实现，R4最终r1包570／两RECORD／283、安装40项／65.54秒、实际CLI／SDK-free基线／三浏览器组及原件／收尾、自身模板approve、新独立两轴最终本地补核通过0／0。发布及自己的CI仍待。原CI分组收集364／1817，未冒称全部执行，各原件见交付。
