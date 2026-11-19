# Use bounded research and schedules

English · [Documentation](../README.md)

## Bounded source checks and scheduled triggers

The default research layer is `{"tool":"urls"}`. It accesses only explicitly specified HTTP(S) materials, saving original snapshot SHAs and sources and proposing a new candidate only when content changes. It checks source changes; it does not automatically write model research conclusions, execute web instructions, write active memory, or modify Skills.

```bash
ergora research run my-project https://example.com/official-doc --id docs-check-r1 --max-bytes 1000000 --timeout 30
ergora research list my-project
ergora research show my-project docs-check-r1
ergora research proposal my-project PROPOSAL_ID
ergora research review my-project PROPOSAL_ID --status reviewed --revision 1 --reason '核对来源与适用版本'
ergora research cancel my-project docs-check-r1
```

Inputs freeze under the same ID; repeating a terminal invocation returns the original result without refetching. After process interruption, use the same ID and input to recover recorded sources, preserving cumulative byte and runtime budgets. Unprovable runtime after the last checkpoint is charged conservatively and may exhaust remaining time. Unconfirmed transfers retain their remaining byte allowance (`reserved_bytes`), and recovery fails visibly; to fetch again, explicitly create a new task with a new budget. Each task has 1–10 sources; bytes bound the total response bodies received for the entire task, and redirect bodies are closed immediately. Fetch failures, limits, timeouts, and cancellation retain status. DNS, headers, and body fetching use terminable Linux child processes that also terminate when the parent dies. After requesting cancellation, still inspect the confirmed actual terminal state. Reviewing materials does not adopt them automatically; save a summary you have confirmed through `memory save`, using the source URL and snapshot SHA as source/revision.

By default, DNS results are checked and private addresses rejected; redirects receive the same checks. Explicitly add `--allow-private` for trusted intranet materials. This is not a network sandbox or DNS-rebinding isolation; operators must trust sources and apply actual network policies. HTML previews are plain text without script execution; raw data is retained only as download / evidence files.

### Temporal durable scheduling

Install `.[temporal]` to use SDK `1.34.0`, matching the reference release. First provide a reachable Temporal service; local development can use `temporal server start-dev --db-filename "$HOME/.local/share/ergora/temporal.sqlite"`, while production deployments should follow official Temporal documentation. Example binding:

```json
{"tool":"temporal","address":"127.0.0.1:7233","namespace":"default","task_queue":"ergora-my-project-research"}
```

```bash
ergora project bind my-project scheduler --binding scheduler-binding.json --revision CURRENT_PROJECT_REVISION
ergora research worker my-project
# 另一个终端；创建时保持暂停
ergora research schedule my-project create official-docs --url https://example.com/official-doc --interval 86400 --max-bytes 1000000 --timeout 30
ergora research schedule my-project trigger official-docs
ergora research schedule my-project status official-docs
ergora research schedule my-project resume official-docs
ergora research schedule my-project pause official-docs
ergora research schedule my-project delete official-docs
```

Workers use the same persistent `ERGORA_HOME` and project bindings; different projects use different task_queue values. Use Supervisor to manage this foreground command. Schedules are stored in Temporal, and workers can restart; retries of the same activity reconcile using the same research ID. Each scheduled invocation has a separate budget; overlap policy is SKIP, schedules default to paused and pause after failure, and do not catch up large backlogs. Frequency and per-invocation budgets together determine long-term totals; the operator confirms these before enabling.

Pausing a Schedule does not cancel observations already started; cancel the corresponding research record through `research cancel` and confirm its terminal state. The reference local Temporal service connection configuration targets trusted environments; this entry point does not yet wrap production TLS / service identity management. Research IDs, snapshots, and candidates are visible in CLI / console, while Temporal UI shows workflow history; they do not depend on GitHub / GitLab issues or chat channels.
