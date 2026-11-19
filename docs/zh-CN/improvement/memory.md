# 记忆有效期与检索

简体中文 · [English](../../improvement/memory.md) · [文档目录](../../README.zh-CN.md)

记忆可设置带时区的ISO 8601到期时间，保存为UTC。服务端判定时刻达到到期时间便退出新检索；到期保留正文和历史，默认`memory list`、dashboard及`memory search`只返回有效的当前修订。`memory catalog`或`GET /api/projects/PROJECT_ID/memory-catalog`显式读取全部状态、原记录与`observed_at`，用于审阅，不能当成自动召回结果。判定时刻是一次观察，此后可能到期。

```bash
ergora memory save my-project --text observation.md --source git:docs/design.md --source-revision COMMIT_SHA --expires-at 2027-01-01T00:00:00+08:00
ergora memory list my-project
ergora memory catalog my-project
ergora memory search my-project "性能基线"
# 更正省略有效期时，保留最新修订的期限
ergora memory save my-project --text correction.md --source git:docs/design.md --source-revision NEW_COMMIT_SHA --id MEMORY_ID --revision CURRENT_REVISION
# 明确移除期限；也可用 --expires-at 指定新时间
ergora memory save my-project --text correction.md --source git:docs/design.md --source-revision NEW_COMMIT_SHA --id MEMORY_ID --revision CURRENT_REVISION --no-expiry
```

原HTTP保存接口`POST /api/projects/PROJECT_ID/memories`接受可选`expires_at`：缺失时更正保留原期限，新建无限期；明确`null`移除期限。新时间创建新修订，仍核原revision。恢复历史修订会复制其有效期，包括已到期时间；恢复本身不会续期。删除沿原规则清空全部历史正文／来源且不可恢复；已归档输入及独立备份分别保留。

ReMe同步会清理已到期／已删除的投影；无需定时器。远端检索返回后重新核本地有效性与revision，丢弃在途到期、删除或更正的命中，远端正文始终不作为canonical。远端索引清理仍受watcher延迟影响，不保证瞬时删除，可显式同步或重建。

数据库当前为schema v6，升级不改写旧记忆且先保存原库备份。**先停止旧CLI任务、控制台及worker，再统一升级并显式重启**；重新打开的旧客户端拒绝新版本，已打开的旧writer被原触发器拒绝。SQLite不能撤销旧reader已取的资料或缓存，不支持新旧进程并行使用同一home；回退需在原home恢复升级前完整离线备份，新版本产生的数据应另行保留。
