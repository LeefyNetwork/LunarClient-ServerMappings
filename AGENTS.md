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

**Never merge, enable automatic merging, force-push, publish releases or deploy
unless the user explicitly instructs that action.** Leave the PR open for review.
A general request to finish an update does not authorize a merge.
