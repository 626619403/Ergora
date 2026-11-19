# Prepare and verify exact review material

English · [Documentation](../README.md)

`ergora review` saves exact local Git changes as a complete, offline-readable packet. It can also read an explicit GitHub / GitLab PR / MR source and bind it to the same source packet. Material collection and review input preparation require no Agent login, project registration, database, or Temporal; actual model calls use the existing composition entry point. See [coverage, limitations, and further review](invoke-and-aggregate.md#coverage-limitations-and-further-review) for complete reports and the scope of remote comments.

## Prepare materials

First install a version containing this command using the [installation manual](../install/linux.md), and confirm `ergora review --help` is available. Python 3.11+ and Git 2.43+ are required, and the source repository must already contain all required local objects; this command does not fetch. Requirements and optional original check files must be NUL-free UTF-8 files; original line endings are preserved.

Save the original requirements as `request.md` in a persistent directory, describing goals, semantic invariants, and expected checks. Explicitly select callers, configuration, and local standards relevant to the actual changes; the command does not infer all dependencies. Below, `BASE_FULL_SHA` is the target branch commit and `HEAD_FULL_SHA` is the candidate commit; both must be full lowercase IDs. `--repository-id` is an operator-declared identity such as `github.com/org/project`; it is neither inferred from a remote nor authenticated.

```bash
ergora review prepare /path/to/project \
  --repository-id github.com/org/project \
  --base BASE_FULL_SHA --head HEAD_FULL_SHA \
  --requirements ./request.md \
  --context src/caller.py --context config/training.toml \
  --evidence ./baseline-check.txt --evidence ./candidate-check.txt \
  --directory ./reviews/candidate-01 > ./reviews-receipt.json
```

`--context` and `--evidence` can be repeated or omitted. Context must be an **exact regular file** relative to the repository, present in at least one of base, the comparison starting point, or head; directory selection is unsupported. The packet automatically includes every changed path and ancestor `AGENTS.md` files for those paths, reading complete contents from all three commits. Worktree, index, and untracked files are not collected; requirements and evidence are read from the explicit local files above and must not be mistaken for versions in Git.

By default, the unique merge-base is computed and saved as `diff_base`; `base` remains the original target branch tip and `head` remains the candidate. These three IDs can differ after divergence. Explicitly use `--comparison base` to compare two commits directly. Multiple merge-bases are not silently resolved by choosing one; without a common ancestor, the default fails, and direct comparison can be selected after checking requirements. Renames are explicitly represented as deletion plus addition without similarity inference; original contents on both sides are retained.

stdout is a receipt, and the material directory contains only `packet.json`. `packet_sha256` is this file's **byte digest**; provide it through another trusted channel when sharing. The directory must be new; even an existing empty directory is not overwritten. New heads / selections / requirements belong in a new packet; old packets remain unchanged.

## Verify and read offline

Copy the entire material directory to another machine with Ergora installed to run the following without the source repository, Git command, model service, or control state:

```bash
ergora review verify ./reviews/candidate-01 --sha256 PACKET_SHA256
ergora review read ./reviews/candidate-01 --sha256 PACKET_SHA256 > ./review-material.json
```

`verify` outputs commit identities, file count, explicit context, and coverage boundaries; `read` outputs the same digest and complete packet. The application's JSON Schema is `data/schemas/local-review-packet-v1.json`. Text and Git blobs are content-addressed without duplicate copies of identical content; `base / diff_base / head` in `source` reference the complete `blobs` table through `git_object`. `requirements`, each `evidence`, the diff, and every blob retain SHA256 values; blobs also verify Git IDs for the repository's object format.

Verification checks content digests, source references, and consistency between changes and selected before / after files. It proves the received bytes are internally consistent; an independent whole-packet digest also checks that this is the same packet. It does not prove repository provenance, commit ancestry, collector identity, that no repository paths were withheld, or that all callers were selected. The diff body digest detects byte changes without corresponding digest updates; this command does not replay Git diff offline or use the body digest to prove the diff's actual relationship to tree members. Identical commit labels must have identical file tables, but source-path membership in commits remains bound by the original collection and independent whole-packet digest. An internally consistent file without an independent digest can be recreated and does not authenticate provenance.

## Collect an external PR / MR

Save an explicit source binding as `tracker.json`, for example this GitHub configuration. For GitLab, use `"tool": "gitlab"` and the complete namespace/project; optional `api_url` can point to `https://host/api/v4` on a self-hosted instance. Set `token_env` only to the name of a credential variable already present in the runtime environment; public sources can omit it. Credentials are not written into materials.

```json
{"tool": "github", "project": "org/project", "token_env": "GITHUB_TOKEN"}
```

```bash
ergora review collect /path/to/project \
  --binding ./tracker.json --number 42 \
  --requirements ./request.md \
  --context src/caller.py --context config/training.toml \
  --evidence ./candidate-check.txt \
  --directory ./reviews/pr-42-observation-01 > ./source-receipt.json

ergora review read-source ./reviews/pr-42-observation-01 \
  --sha256 SOURCE_SHA256 > ./complete-review-source.json
```

`--number` is the PR number in this GitHub repository or MR iid in this GitLab project. Collection performs two platform GETs (repository metadata and the selected PR / MR), preserving normalized native observations, complete body, actual native ID, original response digests, and observation time. It does not search lists, query the current branch, read platform diffs / all comments, or fetch CI logs automatically. Source still comes from a local Git repository already containing the required objects; a worktree with the same name cannot replace complete objects. The operator must explicitly obtain missing objects before collecting again.

GitHub uses the response's base / head SHAs to compute the unique merge-base; the initial version rejects merged GitHub PRs because the current base cannot reliably reconstruct the historical comparison before merging. GitLab uses `diff_refs.start_sha` as the target commit, checks that its head matches the original `sha`, and that the local unique merge-base equals `diff_refs.base_sha`. Missing diff_refs or inconsistent observations are rejected without automatic retries or combining fields observed at different times. The initial version supports only same-repository endpoints on both platforms; forks or deleted source repositories fail visibly.

The directory contains `source.json` and `material/packet.json`. Receipt field `source_sha256` is the source envelope's byte digest; the envelope fixes the original local packet with `packet_sha256`. `read-source` verifies both digest layers, source / native repository ID / request address / exact comparison relationships, and returns both complete layers. The local packet's repository id is `native-repository-sha256:` followed by the SHA256 of canonical JSON containing source and native repository identity; the complete identity remains in the source envelope. Valid long platform addresses / project paths are not truncated, and ownership is not inferred from a local remote. You can separately read the `material` subdirectory using `review read` / `verify`, supplying the receipt's `packet_sha256`.

Use a new directory for a new head or requirements; old observations remain unchanged. Share the entire source directory and an independently obtained `source_sha256`; reading requires no Git, credentials, network, State, or SDK. Source metadata and PR / MR are sequential observations, not an atomic snapshot across requests. Missing local objects / source capacity / unsupported file rules are as above; the complete source envelope has a separate 2,000,000B limit. Source GET response digests are observation receipts from collection; the packet does not store all raw HTTP responses or reauthenticate them offline. Offline consistency does not prove platform provenance, current head, the target local repository's remote ownership, or the authenticity of original checks. It has no formal candidate / approval effect.

Continue: [Invoke and aggregate frozen reviewers](invoke-and-aggregate.md) · [Review pretraining and posttraining code](training.md).
