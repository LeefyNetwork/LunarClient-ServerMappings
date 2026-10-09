import datetime as dt
import unittest
from unittest.mock import patch

import maintenance as m

NOW = dt.datetime(2026, 10, 9, 12, tzinfo=m.UTC)
REPO = "LeefyNetwork/workspace"
OLD = "2026-06-01T00:00:00Z"


def pr(*, head="old", base="master", state="closed", updated=OLD, repo=REPO):
    return {"state": state, "head": {"ref": head, "repo": {"full_name": repo}},
            "base": {"ref": base}, "updated_at": updated}


class FakeGh:
    executable = "gh"

    def __init__(self, changed=False, fresh_pr=False, status="ahead"):
        self.changed, self.fresh_pr, self.status = changed, fresh_pr, status
        self.pr_calls = 0

    def api(self, endpoint, **kwargs):
        if endpoint == f"repos/{REPO}":
            return {"default_branch": "master"}
        if "/commits/" in endpoint:
            return {"committer": {"date": OLD}}
        if "/compare/" in endpoint:
            return {"status": self.status}
        if "/branches/" in endpoint:
            name = endpoint.split("/branches/")[1]
            return {"name": name, "protected": False,
                    "commit": {"sha": "changed" if self.changed and name == "old" else "a" * 40}}
        raise AssertionError(endpoint)

    def list(self, endpoint):
        if "/pulls?" in endpoint:
            self.pr_calls += 1
            return [pr(state="open")] if self.fresh_pr and self.pr_calls > 1 else []
        return [{"name": "old", "protected": False, "commit": {"sha": "a" * 40}}]


class PolicyTests(unittest.TestCase):
    def test_calendar_month_boundary(self):
        self.assertEqual(m.cutoff(NOW), NOW.replace(month=7))
        end = NOW.replace(month=5, day=31)
        self.assertEqual(m.cutoff(end), end.replace(month=2, day=28))
        leap = end.replace(year=2024)
        self.assertEqual(m.cutoff(leap), leap.replace(month=2, day=29))
        self.assertEqual(m.cutoff(NOW.replace(month=1)).year, 2025)

    def test_boundary_is_ineligible_until_strictly_older(self):
        branch = {"name": "old", "protected": False}
        exact = m.cutoff(NOW).isoformat()
        self.assertEqual(m.eligible(REPO, branch, exact, [], "master", NOW, True), "recent activity")
        older = (m.cutoff(NOW) - dt.timedelta(seconds=1)).isoformat()
        self.assertIsNone(m.eligible(REPO, branch, older, [], "master", NOW, True))

    def test_recent_closed_pr_activity(self):
        self.assertEqual(m.eligible(REPO, {"name": "old", "protected": False}, OLD,
                                    [pr(updated=NOW.isoformat())], "master", NOW, True), "recent activity")

    def test_protected_default_open_head_and_base(self):
        cases = [({"name": "old", "protected": True}, []),
                 ({"name": "main", "protected": False}, []),
                 ({"name": "master", "protected": False}, []),
                 ({"name": "old", "protected": False}, [pr(state="open")]),
                 ({"name": "old", "protected": False}, [pr(head="new", base="old", state="open")])]
        for branch, prs in cases:
            self.assertIsNotNone(m.eligible(REPO, branch, OLD, prs, "main", NOW, True))

    def test_fork_head_does_not_refresh_local_branch(self):
        self.assertEqual(m.activity(REPO, "old", OLD, [pr(repo="other/workspace", updated=NOW.isoformat())]), m.timestamp(OLD))

    def test_unmerged_branches_are_preserved(self):
        self.assertEqual(m.eligible(REPO, {"name": "old", "protected": False}, OLD,
                                    [], "master", NOW, False), "unmerged commits")
        self.assertEqual(m.remote_cleanup(FakeGh(status="diverged"), REPO, now=NOW)[0]["reason"], "unmerged commits")

    def test_changed_tip_and_new_open_pr_hold_deletion(self):
        for gh, reason in [(FakeGh(changed=True), "changed tip"), (FakeGh(fresh_pr=True), "open PR head or base")]:
            deleted = []
            results = m.remote_cleanup(gh, REPO, apply=True, now=NOW, delete=lambda *args: deleted.append(args))
            self.assertEqual(results[0]["reason"], reason)
            self.assertEqual(deleted, [])

    def test_dry_run_never_mutates(self):
        with patch.object(m, "expected_delete", side_effect=AssertionError("mutation")):
            self.assertEqual(m.remote_cleanup(FakeGh(), REPO, now=NOW)[0]["action"], "would-delete")

    def test_exact_tip_passed_to_delete(self):
        deleted = []
        result = m.remote_cleanup(FakeGh(), REPO, apply=True, now=NOW, delete=lambda *args: deleted.append(args))
        self.assertEqual(result[0]["action"], "deleted")
        self.assertEqual(deleted[0][-1], "a" * 40)

    def test_deletion_is_lease_guarded(self):
        calls = []
        with patch.object(m, "run", side_effect=lambda args, **kwargs: calls.append(args)):
            m.expected_delete(FakeGh(), REPO, "old", "a" * 40)
        self.assertIn("--force-with-lease=refs/heads/old:" + "a" * 40, calls[-1])
        self.assertEqual(calls[-1][-1], ":refs/heads/old")

    def test_unknown_repository_is_rejected(self):
        with self.assertRaises(ValueError):
            m.remote_cleanup(FakeGh(), "other/repo")

    def test_utf8_subprocess_output(self):
        import sys
        self.assertEqual(m.run([sys.executable, "-c", "import sys; sys.stdout.buffer.write('Åäö 😀'.encode('utf-8'))"]), "Åäö 😀")


if __name__ == "__main__":
    unittest.main()
