# Repository branch maintenance

Daily branch expiry uses this repository's built-in token. Only merged branches
inactive for strictly more than three calendar months may expire. Default/protected
and open PR head/base branches are preserved; the observed tip is rechecked and
deletion is lease-guarded. PR activity refreshes the inactivity timestamp.

The script defaults to dry-run. Manual workflow dispatch also defaults to dry-run.
Scheduled activation requires this workflow on master. Read-only tests run on PRs:

```text
python -m unittest discover -s .github/maintenance -p 'test_*.py' -v
python .github/maintenance/maintenance.py --repo LeefyNetwork/LunarClient-ServerMappings --output "../../.work/automation/LunarClient-ServerMappings-dry-run.json"
```

Use the workspace's .work folder for local reports and fixtures, rather than source.
GitHub retains sanitized cleanup reports for 90 days. The workspace's hosted
GitHub Actions coordinator ingests deletions into .notes review PRs and handles
manifest-authorized project merges with a GitHub App limited to the five
repositories. No Windows scheduled task remains. Local cleanup is on demand;
hosted runners cannot access this PC's branches. See the workspace repository's
.github/maintenance/README.md for App setup, policy and recovery.

New project onboarding must update selected App installation access, the hosted
coordinator's explicit repository list, maintenance allowlists and workspace path
map together. Keep credentials only in the workspace repository; follow its setup
guide and coordinated review workflow.
