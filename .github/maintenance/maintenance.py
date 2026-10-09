"""Repository-scoped branch expiry. Standard library only; dry-run by default."""
from __future__ import annotations

import argparse
import calendar
import datetime as dt
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
from urllib.parse import quote

REPOS = {f"LeefyNetwork/{name}" for name in (
    "ai", "LeefyMC-Core", "LeefyMC-Gens", "website_and_bot",
    "LunarClient-ServerMappings")}
UTC = dt.timezone.utc


def run(args, *, cwd=None, binary=False, check=True):
    try:
        result = subprocess.run([str(a) for a in args], cwd=cwd, capture_output=True,
                                text=not binary, encoding=None if binary else "utf-8", timeout=180)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{Path(str(args[0])).name} timed out") from None
    if check and result.returncode:
        # Command arguments/output can contain credentials. Do not persist them.
        raise RuntimeError(f"{Path(str(args[0])).name} failed (exit {result.returncode})")
    return result.stdout if check else result


class Gh:
    def __init__(self, executable=None):
        self.executable = executable or os.environ.get("GH_EXECUTABLE", "gh")

    def api(self, endpoint, *, method="GET", fields=None, pages=False):
        args = [self.executable, "api", endpoint, "--method", method]
        if pages:
            args += ["--paginate", "--slurp"]
        for key, value in (fields or {}).items():
            args += ["-f", f"{key}={value}"]
        output = run(args)
        return json.loads(output) if output.strip() else None

    def list(self, endpoint, key=None):
        pages = self.api(endpoint, pages=True)
        return [item for page in pages for item in (page[key] if key else page)]


def timestamp(value):
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def cutoff(now):
    """Three calendar months, clamping the day at the target month's end."""
    month_index = now.year * 12 + now.month - 1 - 3
    year, month0 = divmod(month_index, 12)
    month = month0 + 1
    return now.replace(year=year, month=month,
                       day=min(now.day, calendar.monthrange(year, month)[1]))


def associated(pr, repo, name):
    head_repo = (pr.get("head", {}).get("repo") or {}).get("full_name")
    return head_repo == repo and pr["head"]["ref"] == name


def activity(repo, name, tip_date, prs):
    return max([timestamp(tip_date)] + [timestamp(p["updated_at"]) for p in prs
                                      if associated(p, repo, name)])


def held_by_pr(repo, name, prs):
    return any(p["state"] == "open" and (
        associated(p, repo, name) or p["base"]["ref"] == name) for p in prs)


def eligible(repo, branch, tip_date, prs, default, now, merged):
    name = branch["name"]
    if name in {"master", default} or branch.get("protected", True):
        return "default or protected"
    if held_by_pr(repo, name, prs):
        return "open PR head or base"
    if activity(repo, name, tip_date, prs) >= cutoff(now):
        return "recent activity"
    if not merged:
        return "unmerged commits"
    return None


def expected_delete(gh, repo, name, sha):
    """Lease-guarded deletion, never a history rewrite or unguarded API delete."""
    scratch = Path(".work/automation/tmp")
    scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="branch-expiry-", dir=scratch) as temp:
        run(["git", "init", "--bare", temp])
        # gh supplies the existing keyring login or job's GH_TOKEN to Git.
        helper = "!" + shlex.quote(str(gh.executable).replace("\\", "/")) + " auth git-credential"
        run(["git", "-c", "credential.helper=", "-c", f"credential.helper={helper}",
             "push", f"--force-with-lease=refs/heads/{name}:{sha}",
             f"https://github.com/{repo}.git", f":refs/heads/{name}"], cwd=temp)


def remote_cleanup(gh, repo, *, apply=False, now=None, delete=expected_delete, on_change=lambda event: None):
    if repo not in REPOS:
        raise ValueError("repository is outside the maintenance allowlist")
    now = now or dt.datetime.now(UTC)
    info = gh.api(f"repos/{repo}")
    prs = gh.list(f"repos/{repo}/pulls?state=all&per_page=100")
    branches = gh.list(f"repos/{repo}/branches?per_page=100")
    results = []
    for branch in branches:
        name, sha = branch["name"], branch["commit"]["sha"]
        record = {"repo": repo, "branch": name, "sha": sha}
        if name in {"master", info["default_branch"]} or branch["protected"]:
            results.append(record | {"action": "skip", "reason": "default or protected"})
            continue
        if held_by_pr(repo, name, prs):
            results.append(record | {"action": "skip", "reason": "open PR head or base"})
            continue
        commit = gh.api(f"repos/{repo}/git/commits/{sha}")
        tip_date = commit["committer"]["date"]
        reason = eligible(repo, branch, tip_date, prs, info["default_branch"], now, True)
        if not reason:
            comparison = gh.api(f"repos/{repo}/compare/{sha}...master")
            if comparison["status"] not in {"ahead", "identical"}:
                reason = "unmerged commits"
        if reason:
            results.append(record | {"action": "skip", "reason": reason})
            continue
        # Refresh all guards immediately before even a dry-run deletion decision.
        fresh = gh.api(f"repos/{repo}/branches/{quote(name, safe='')}")
        fresh_info = gh.api(f"repos/{repo}")
        fresh_prs = gh.list(f"repos/{repo}/pulls?state=all&per_page=100")
        master_sha = gh.api(f"repos/{repo}/branches/master")["commit"]["sha"]
        comparison = gh.api(f"repos/{repo}/compare/{sha}...{master_sha}")
        reason = "changed tip" if fresh["commit"]["sha"] != sha else eligible(
            repo, fresh, tip_date, fresh_prs, fresh_info["default_branch"], now,
            comparison["status"] in {"ahead", "identical"})
        if reason:
            results.append(record | {"action": "skip", "reason": reason})
        elif not apply:
            results.append(record | {"action": "would-delete"})
        else:
            try:
                delete(gh, repo, name, sha)
                results.append(record | {"action": "deleted"})
                on_change(results[-1])
            except RuntimeError:
                results.append(record | {"action": "blocked", "reason": "guarded deletion failed"})
                on_change(results[-1])
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, choices=sorted(REPOS))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--output", default=".work/automation/branch-maintenance-report.json")
    args = parser.parse_args()
    report = {"schema_version": 1, "repo": args.repo,
              "time": dt.datetime.now(UTC).isoformat(), "apply": args.apply, "results": []}
    def persist(event=None):
        if event:
            report["results"].append(event)
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    persist()
    try:
        report["results"] = remote_cleanup(Gh(), args.repo, apply=args.apply, on_change=persist)
    except (RuntimeError, ValueError, KeyError):
        report["results"].append({"repo": args.repo, "action": "blocked", "reason": "cleanup API failed; partial audit retained"})
    persist()
    print(json.dumps(report, indent=2))
    if any(r["action"] == "blocked" for r in report["results"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
