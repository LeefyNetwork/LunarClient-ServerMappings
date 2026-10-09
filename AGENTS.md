# Working in LunarClient-ServerMappings

Read README.md and the repository's contribution guidance before changing mappings.
This repository contains public server metadata and assets under `servers/`, JSON
schemas at the root, maintained validation tooling in `.scripts/` and workflows in
`.github/`. Keep those project tools here; they are not temporary editing helpers.

Validate changed metadata against the relevant checked-in schemas and the existing
workflow checks. Preserve existing server assets and identities unless the task
requires a change. Do not add private server addresses. Keep inactive-server data
consistent with the repository's documented process.

## Workspace files and Git workflow

Repository: https://github.com/LeefyNetwork/LunarClient-ServerMappings. In the coordinated workspace,
read [the root instructions](../../AGENTS.md) before making changes. Source belongs in
this repository; temporary change scripts, patches, reference assets, fixtures and
logs belong under the workspace's `.work/`, grouped by project and task. Permanent
build/deployment tools and maintained tests stay here. Record every task, decision,
move, validation result, commit and PR link in the workspace's `.notes/` using
Europe/Stockholm dates. Keep secrets out of notes and commits.

Move unused files to the workspace's dated `.trash/` archive with their original
relative paths and a manifest. Preserve old instructions before rewriting them.
Do not permanently delete files as routine cleanup.

Before editing, inspect the working tree and create a new typed task branch,
normally from current `origin/master`: `feat/`, `fix/`, `refactor/`, `perf/`, `docs/`,
`test/` or `chore/`, followed by a short topic. Preserve existing work; reuse the
task branch for its follow-up fixes. A submodule checkout may be detached, so
create its task branch before editing. Do not push every change to `dev`.

Run relevant checks, review the diff, stage only task files, commit with a typed
subject, push the task branch to this project's repository and open a pull request
targeting **master**. For coordinated work, push project commits first, then record
their exact commits in the ai workspace's submodule pointers and open a linked
workspace PR to master. Keep pending commits reachable on pushed task branches.

Leave the PR open for review. Merging a coordinated ai PR explicitly authorizes
ordinary merges of only the project PRs and exact heads listed in its checked-in
`.github/project-prs.json`, after the entire group's checks, reviews and mergeability
permit merging. Workspace-only ai PRs authorize no project merges. Outside that
authorization, never merge or enable automatic merging unless explicitly instructed.
Never force-push, publish releases or deploy unless explicitly instructed.

## Automatic branch expiry

The daily `.github/workflows/branch-maintenance.yml` uses this repository's own
built-in token. Expire only tips already reachable from master and strictly older
than three calendar months, measured from the newest tip committer date or
associated PR update. Preserve default/protected branches and open PR head/base
branches. Refresh guards and use expected-tip deletion to preserve racing updates.
The workspace's hidden Windows task cleans local branches daily after fetch/prune,
preserving active worktrees and unmerged or unpushed unique commits. It checks
manifest-authorized project merges every five minutes. No administrator override
or check bypass is allowed. Keep permanent tooling/tests in `.github/maintenance/`
and runtime state in the workspace's ignored `.work/automation/`. Record actual
deletions, merges and changed blockers in workspace `.notes` review PRs. Activation
requires merged workflows and trusted ai master; dry-run cleanup first.
