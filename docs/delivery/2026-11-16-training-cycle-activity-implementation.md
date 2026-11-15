# c1b2a activity implementation

本记录仅覆盖已批准r2合同的protocol、原worker活动／S-H消费者及原submission/runtime测试；服务命令与Supervisor、联合安装／真实Temporal、自身模板及fresh reviewer由主控分别验收。产品基线为`d5b58912e4f20c96a52f7c0138b8c7c3d1a97b50`，实施工作树初始HEAD为`b7193530f12363aeb0f68daddfa1a6f5774bc86d`。没有正式总Workflow、execution/collect或后继消费者，没有增加账本或改参考文件。

实施中的具体接线：原protocol严格核四活动业务请求、真实SDK来源context、operation与原prepare来源；新冷H复用原controller reconcile、按实际run查询并在receipt前认证；绑定stop保留本地观察。原S在stopped帧后读取真实stdout原始字节并生成准确引用。活动通过实际DataConverter检查包含metadata的protobuf容量。独立normal／stop Worker各一槽、不同queue，normal grace0先shutdown，等待原清理后再关stop与两个run task。

## 已完成验证

- 源码原controller dispatch与一次prepare接缝：8 passed，35.78秒。使用SDK解释器、明确指向本工作树src；不称安装验收。

## 在途与未验

新SDK activity环境到原S/H的wrong-run／started input／memo／type／queue／原attempt恢复反例，ordinal1／attempt2无新offer，以及已有receipt stop离线全分支原始引用正在运行。真实Temporal／Supervisor、32候选fanout、新安装、信号与fatal关机、独立审查均尚未通过，不能以本文件声称交付闭合。

## 源码接缝结果与交接

下列均为本工作树src的源码测试，使用已有SDK解释器；各轮有重叠，不相加冒称全量：

- 原controller dispatch／一次prepare：8 passed，35.78秒。
- 原candidate／pending Popen／取消／cold result read／耗尽stop组：22 passed，272.37秒；保留既有真实S-H、后代和原预算根fixture。
- 新SDK activity全组当时7 passed，65.33秒，包含32候选真实66分支、完整引用、单branch构造失败／peer继续和非重试容量。之后新增的start与source mutation分别如下精准验证。
- 实际SDK start→原独立root交接→duplicate只reconcile：1 passed，19.65秒；原intent／attempt bytes与inode不变，finally显式stop并等待原root终态。
- receipt前冷认证、post-stopped丢result与耗尽stop的最终精准组：3 passed，34.99秒；补充实际query client namespace不符与CONTINUED_AS_NEW拒绝。原post-stopped未知内联明确stopped=true；未spawn的完整六分支未知内联明确stopped=false／returncode=null。
- 原prepare activity_context在attempt同步后被换，最终SDK点拒绝且真实candidate start计数0：最终精准1 passed，16.96秒。此新测试最初两次分别误读H错误层级、把只读describe产生的service记录当作start；两次失败保留为测试断言修正历史，最终按真实`starts=0`与原完整H reason核对，没有为这些失败改产品。
- `py_compile`与`git diff --check`通过。

同SDK来源贯穿prepare／confirm／dispatch与原root请求来源核对。已存在candidate由冷H识别，adapter直接走同一次冷window的reconcile，不重新构造compute执行窗口；竞态下原intent仍只授一次offer。所有SDK历史结果只含紧凑原事实／实际原件引用，不含snapshot；32KiB按实际DataConverter和protobuf Payloads连同metadata检查，巨大inline reason不截断并记完整worker错误。

测试fixtures只扩展原controller service的真实首run／started身份，以及原cycle fault入口；没有替换原supervisor、唯一reaper或真实Popen生命周期。没有改submission/runtime产品owner，没有提交或推送。

仍由主控完成：真实Temporal与Supervisor下双queue／各一槽／normal业务存储阻塞时stop领取；SIGTERM／SIGINT、重复cancel、单Worker fatal与stop取消的完整资源收尾；新的非editable core／SDK安装、自身模板、新fresh-context两轴审查、准确CI。上述源码／SDK服务替身结果不认证这些范围，也不认证正式总Workflow、execution/collect、接受／后继候选、自动循环或训练质量。
