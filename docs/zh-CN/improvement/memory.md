# 记忆有效期、检索与共享案例

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

## 本地共享案例库

在任意工作区使用已安装的 `ergora`。通过 `--library` 指定现有本地目录的同一个绝对路径。共享命令直接读取该目录下的 `cases/`，独立于项目注册、`ERGORA_HOME` 和 ReMe。

```bash
ergora memory shared search '任务 MCP 启动失败' --library "$case_library" \
  --technology ergora-task-mcp --environment linux --version 0.2.0
ergora memory shared show task-mcp-missing-sdk --library "$case_library" \
  --revision 1 --sha256 SHA256_FROM_SEARCH \
  --technology ergora-task-mcp --environment linux --version 0.2.0
```

检索默认返回最多 5 条当前命中，`--limit` 可设为 1 至 20。每条结果包含 ID、修订、完整 Markdown 的 SHA-256、状态、来源和至多 512 个 UTF-8 字节的匹配摘录。查询包含完整错误签名时，该命中优先于标题和别名匹配。提供 `--project`、`--technology`、`--environment` 或 `--version` 后，`applicability_match` 会列出缺失和不符的字段，并返回 `matched`、`incompatible` 或 `unknown`。项目、技术和环境标签忽略大小写，版本按原字符串精确比较。`unresolved` 表示原因待确认并附有下一项诊断。

两个读取命令均在标准输出返回 JSON。`show` 在 `record` 中返回当前元数据，在 `markdown` 中返回完整 Markdown，文件最多 65,536 字节。使用检索返回的 `--revision` 和 `--sha256` 核验精确选择。未命中时 `results` 为空。未知案例或修订、摘要不符时，命令退出码为 2，并在标准错误输出诊断。过期或撤回的案例退出新检索。此时普通 `show` 返回当前元数据和 `markdown: null`，带修订和摘要的 `show` 拒绝读取。

### 发布已审阅的案例

草稿保存在 `cases/` 之外，采用 UTF-8 Markdown。在两行 `---` 之间填写 JSON 元数据，包括稳定的小写 ID、修订、标题、别名或错误签名、适用范围、状态、来源和 `expires_at`。适用范围包含项目或技术、环境及至少一个确切版本。每条来源包含可共享的 `uri` 和指定的 `revision`。案例库将 `git:docs/design.md`、HTTPS URL 等来源作为文本保存。到期时间使用带时区的时间戳，无期限填 `null`。正文记录症状、原因或待确认问题、处理或下一项诊断，以及验证方式。 [案例样例](../../../tests/fixtures/shared-task-mcp-missing.md)

审阅草稿时记录完整 Markdown 的 SHA-256。发布时按此摘要核对即将发布的原始字节。

```bash
ergora memory shared publish ./reviewed-case.md --library "$case_library" --expected-revision 0 \
  --sha256 REVIEWED_SHA256
```

首次发布在指定目录中初始化 `cases/`。新案例从修订 1 开始，`--expected-revision` 为 0。更正或撤回时保留 ID，将草稿修订号加一，并用 `--expected-revision` 提供当前修订。状态可为 `verified`、`unresolved` 或 `withdrawn`。发布持有同一把锁，以 `cases/ID/REVISION/case.md` 为单位公开完整修订。发布中断后先核对当前修订和摘要，再决定是否重试。暂停发布后可完整离线备份该目录，与 `ERGORA_HOME` 备份分别保留。
