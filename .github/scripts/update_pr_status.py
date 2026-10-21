import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

GH_TOKEN = os.environ["GH_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
}


def get_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
query = f"is:pr author:bferd created:>={one_year_ago}"
encoded_query = urllib.parse.quote(query)

search_url = (
    f"https://api.github.com/search/issues?q={encoded_query}"
    f"&sort=created&order=desc&per_page=15"
)
data = get_json(search_url)

lines = ["| PR | Status |", "|---|---|"]
skipped = 0
for item in data.get("items", []):
    repo = item["repository_url"].split("/repos/")[1]
    num = item["number"]

    # The search API doesn't reliably report whether a closed PR was merged,
    # so for closed items, check the PR's own endpoint for the real answer.
    if item.get("state") == "closed":
        pr = get_json(f"https://api.github.com/repos/{repo}/pulls/{num}")
        if not pr.get("merged"):
            # Closed without merging - leave these off the table entirely.
            skipped += 1
            continue

    title = item["title"].replace("|", "\\|")
    url_ = item["html_url"]

    # Live, auto-refreshing state badge (open/draft/merged all render
    # correctly here, since it reflects GitHub's own PR state).
    state_badge = f"https://img.shields.io/github/pulls/detail/state/{repo}/{num}"
    status_cell = f"![PR status]({state_badge})"

    lines.append(f"| [{repo}#{num} – {title}]({url_}) | {status_cell} |")

table = "\n".join(lines) + "\n"

with open("README.md", "r") as f:
    readme = f.read()

new_block = f"<!-- PR-STATUS:START -->\n{table}<!-- PR-STATUS:END -->"
updated = re.sub(
    r"<!-- PR-STATUS:START -->.*?<!-- PR-STATUS:END -->",
    new_block,
    readme,
    flags=re.DOTALL,
)

with open("README.md", "w") as f:
    f.write(updated)

kept = len(data.get("items", [])) - skipped
print(f"Updated README.md with {kept} PR(s); skipped {skipped} closed-without-merge.")
