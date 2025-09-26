
"""Utilities to enrich modules with commit-based (behavioral) metrics from GitHub.

Requires a GitHub Personal Access Token in env var GITHUB_TOKEN.
Usage (example):
    from github_features import fetch_commit_metrics
    df_commits = fetch_commit_metrics(owner='org', repo='name', since='2024-01-01', until='2024-12-31')
    # Join df_commits with your modules using filenames or paths.

Notes:
- This module uses the REST API via requests (no external deps).
- In this offline environment, calls won't execute; integrate and run locally.
"""
import os, time, math, requests
import pandas as pd

GITHUB_API = "https://api.github.com"

def _headers():
    token = os.getenv("GITHUB_TOKEN", "")
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h

def fetch_commit_metrics(owner: str, repo: str, since=None, until=None, path=None, per_page=100, max_pages=10):
    """Fetch commit-level activity metrics for a repo/path window.
    Returns a DataFrame with per-file churn and activity stats.
    """
    commits = []
    page = 1
    params = {"since": since, "until": until, "per_page": per_page}
    if path: params["path"] = path
    while page <= max_pages:
        resp = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits", headers=_headers(), params={**params, "page": page})
        if resp.status_code != 200:
            break
        batch = resp.json()
        if not batch:
            break
        commits.extend(batch)
        page += 1
        time.sleep(0.5)
    # For each commit, get details to compute churn (additions, deletions) and files changed
    rows = []
    for c in commits:
        sha = c.get("sha")
        if not sha: continue
        detail = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/commits/{sha}", headers=_headers())
        if detail.status_code != 200:
            continue
        d = detail.json()
        stats = d.get("stats") or {}
        files = d.get("files") or []
        for f in files:
            rows.append({
                "commit_sha": sha,
                "date": d.get("commit", {}).get("author", {}).get("date"),
                "filename": f.get("filename"),
                "additions": f.get("additions", 0),
                "deletions": f.get("deletions", 0),
                "changes": f.get("changes", 0)
            })
        time.sleep(0.2)
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Aggregate per file
    agg = df.groupby("filename").agg(
        commit_count=("commit_sha", "nunique"),
        additions=("additions", "sum"),
        deletions=("deletions", "sum"),
        changes=("changes", "sum"),
        last_change=("date", "max")
    ).reset_index()
    # Derive churn_rate and activity_index
    agg["churn_rate"] = agg["changes"] / (agg["additions"] + agg["deletions"] + 1e-9)
    # Simple activity index combining commits and churn (normalize later in pipeline)
    agg["activity_index"] = agg["commit_count"] * np.log1p(agg["changes"])
    return agg
