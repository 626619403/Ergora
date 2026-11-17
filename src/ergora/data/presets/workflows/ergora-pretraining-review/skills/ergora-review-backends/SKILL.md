---
name: ergora-review-backends
description: Distinguish Ergora review backends from vendor native commands, plugins and managed PR/MR review when selecting a backend or interpreting findings.
---

# Review backend boundaries

Use the caller's selected backend, supplied exact candidate and existing reviewer result contract. This shared resource is inherited by the general engineering reviewers and the training specialist; it adds guidance, not tools or execution permissions. Backend facts below were checked against official sources on 2026-11-15. Links identify provenance; the guidance requires no network fetch.

## The Ergora call

Ergora's Codex and Claude Code drivers send an ordinary structured Agent request. Selecting either backend does not invoke its native review command, install a plugin, enable cloud review, or publish platform feedback. Installing a preset does not install or authenticate either CLI. Preserve the actual invocation mode: text-only uses supplied material; task-MCP exposes only the granted original list/read resources. Claude task-MCP uses bare-mode API environment credentials; stored Claude OAuth/keychain login alone does not satisfy that mode.

Report the actual backend, mode, independent session, supplied source identity and coverage. Distinguish an executable being present, credentials being configured, account/service entitlement, and a successful invocation. When the supplied evidence establishes only one, leave the others unknown. Retain the actual reason for a same-backend fallback.

## Native alternatives are separate operations

- **Codex CLI**: `/review` reviews a selected base-branch diff, uncommitted changes or commit and returns prioritized findings in the transcript without changing the working tree. It needs a local CLI installation and supported sign-in; local ChatGPT sign-in or API-key access is separate from cloud access. A PR-style diff is not Ergora's complete source/evidence packet. [CLI](https://learn.chatgpt.com/docs/codex/cli), [review](https://learn.chatgpt.com/docs/code-review), [authentication](https://learn.chatgpt.com/docs/auth).
- **Codex cloud integrations**: GitHub PR reviews and the separate GitLab MR beta require their own account/repository connection and review settings. GitLab adds host-specific webhook/environment or service-account prerequisites. An `@codex review` request or enabled automatic review posts remote feedback; an ordinary API call does not enable these services. [GitHub](https://learn.chatgpt.com/docs/third-party/github), [GitLab](https://learn.chatgpt.com/docs/third-party/gitlab).
- **Claude Code session review**: built-in `/code-review` (alias `/review`) works on any plan with the session's authentication and usage billing. Its default asks for a report; `--fix` requests working-tree edits and `--comment` requests platform comments. GitLab posting has Claude version and `glab` requirements. These are distinct side effects, subject to the actual permissions. [Local review](https://code.claude.com/docs/en/code-review-local), [installation](https://code.claude.com/docs/en/setup), [authentication](https://code.claude.com/docs/en/authentication).
- **Public Claude plugins or CI**: installing a marketplace plugin, authenticating its platform tools, and configuring an Action or GitLab runner are separate setup. Read the exact installed command, tools and output behavior; a similarly named command does not identify the managed service. Such workflows may post feedback or change code. [Plugin installation](https://code.claude.com/docs/en/discover-plugins), [Actions](https://code.claude.com/docs/en/github-actions), [GitLab CI](https://code.claude.com/docs/en/gitlab-ci-cd).
- **Anthropic managed Code Review**: Team/Enterprise organizations with supported GitHub repositories need an Owner to enable the service, connect the Claude GitHub App and select repositories. It runs on Anthropic infrastructure, reads code without building/running it, and writes PR comments/checks, including resolving its own earlier threads. Reviews do not push commits or approve/block the PR. Billing is separate from included plan usage; API credentials or a local Claude login do not activate it. [Current service](https://code.claude.com/docs/en/code-review), [setup](https://code.claude.com/docs/en/code-review-setup), [costs](https://code.claude.com/docs/en/code-review-costs). The [March launch article](https://claude.com/resources/articles/code-review) retains historical preview and estimate text alongside its later GA update.

## Interpret the result

Keep findings, assumptions, missing evidence and unexamined scope explicit. A local Ergora `approve` is the existing advisory reviewer result, not a GitHub review submission, GitLab approval, merge permission or proof that training/runtime checks passed. Remote comments, code edits, installation and service activation require their own authorized workflow; this Skill supplies none of those actions. A documented feature, model agreement or a process exit alone cannot certify correctness, quality or performance.
