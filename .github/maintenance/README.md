# Repository branch maintenance

Daily branch expiry uses this repository's built-in token. Only merged branches
inactive for strictly more than three calendar months may expire. Default/protected
and open PR head/base branches are preserved; the observed tip is rechecked and
deletion is lease-guarded. PR activity refreshes the inactivity timestamp.

The script defaults to dry-run. Manual workflow dispatch also defaults to dry-run.
Scheduled activation requires this workflow on master. Read-only tests run on PRs:

```text
python -m unittest discover -s .github/maintenance -p 'test_*.py' -v
python .github/maintenance/maintenance.py --repo LeefyNetwork/LunarClient-ServerMappings --output report.json
```

Use the workspace's .work folder for local reports and fixtures, rather than source.
GitHub retains sanitized cleanup reports for 90 days. The workspace's hidden
Windows task ingests deletions into .notes review PRs and handles local cleanup
and manifest-authorized project merges using the existing gh login. See the ai
repository's .github/maintenance/README.md for setup, policy and recovery.
