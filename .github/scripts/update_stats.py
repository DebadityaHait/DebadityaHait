#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.request

USERNAME = os.environ.get("GITHUB_USERNAME", "DebadityaHait")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch_json(endpoint):
    url = f"https://api.github.com{endpoint}"
    headers = {
        "User-Agent": "GitHub-Stats-Updater",
        "Accept": "application/vnd.github.v3+json",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def get_stats():
    # 1. Total PRs & Unique Repos
    total_data = fetch_json(f"/search/issues?q=author:{USERNAME}+type:pr&per_page=100")
    if not total_data:
        print("Failed to fetch total PR data.", file=sys.stderr)
        sys.exit(1)
    
    total_prs = total_data.get("total_count", 0)
    items = total_data.get("items", [])
    unique_repos = len(set(item["repository_url"].replace("https://api.github.com/repos/", "") for item in items))
    
    # If there are more than 100 PRs, paginate
    page = 2
    while len(items) < total_prs and page <= 5:
        paged_data = fetch_json(f"/search/issues?q=author:{USERNAME}+type:pr&per_page=100&page={page}")
        if not paged_data or not paged_data.get("items"):
            break
        paged_items = paged_data.get("items", [])
        items.extend(paged_items)
        unique_repos = len(set(item["repository_url"].replace("https://api.github.com/repos/", "") for item in items))
        page += 1

    # 2. Merged PRs
    merged_data = fetch_json(f"/search/issues?q=author:{USERNAME}+type:pr+is:merged")
    merged_prs = merged_data.get("total_count", 0) if merged_data else 0

    # 3. Open PRs
    open_data = fetch_json(f"/search/issues?q=author:{USERNAME}+type:pr+is:open")
    open_prs = open_data.get("total_count", 0) if open_data else 0

    return {
        "total_prs": total_prs,
        "merged_prs": merged_prs,
        "open_prs": open_prs,
        "unique_repos": unique_repos,
    }

def update_readme(stats, readme_path="README.md"):
    if not os.path.exists(readme_path):
        print(f"File not found: {readme_path}", file=sys.stderr)
        sys.exit(1)

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    original_content = content

    # Update summary text
    content = re.sub(
        r"Summary:\s*\*\*\d+\s+pull requests across\s+\d+\s+unique repositories\*\*\s*\(\d+\s+merged upstream,\s*\d+\s+active open\)",
        f"Summary: **{stats['total_prs']} pull requests across {stats['unique_repos']} unique repositories** ({stats['merged_prs']} merged upstream, {stats['open_prs']} active open)",
        content,
    )

    # Update Badges
    content = re.sub(
        r"badge/Total%20PRs-\d+-0969da",
        f"badge/Total%20PRs-{stats['total_prs']}-0969da",
        content,
    )
    content = re.sub(
        r"badge/Merged%20Upstream-\d+-238636",
        f"badge/Merged%20Upstream-{stats['merged_prs']}-238636",
        content,
    )
    content = re.sub(
        r"badge/Active%20Open-\d+-8957e5",
        f"badge/Active%20Open-{stats['open_prs']}-8957e5",
        content,
    )

    # Update Quick Stat Table
    content = re.sub(
        r"\|\s*\*\*\d+\s+Pull Requests\*\*<br/>\s*\*?\(\d+\s+Unique Codebases\)\*?\s*\|\s*\*\*\d+\s+Merged PRs\*\*",
        f"| **{stats['total_prs']} Pull Requests**<br/>*({stats['unique_repos']} Unique Codebases)* | **{stats['merged_prs']} Merged PRs**",
        content,
    )

    if content != original_content:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"README.md successfully updated with live stats: {stats}")
    else:
        print(f"No changes detected in README.md. Current stats: {stats}")

if __name__ == "__main__":
    readme_file = sys.argv[1] if len(sys.argv) > 1 else "README.md"
    print("Fetching live GitHub stats...")
    stats = get_stats()
    print(f"Fetched stats: {stats}")
    update_readme(stats, readme_file)
