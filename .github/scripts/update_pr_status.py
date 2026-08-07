import json
import os
import re
import subprocess
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

GH_TOKEN = os.environ["GH_TOKEN"]

one_year_ago = (datetime.now(timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")
query = f"is:pr author:bferd created:>={one_year_ago}"
encoded_query = urllib.parse.quote(query)

url = (
    f"https://api.github.com/search/issues?q={encoded_query}"
    f"&sort=created&order=desc&per_page=10"
)

req = urllib.request.Request(
    url,
    headers={
        "Authorization": f"Bearer {GH_TOKEN}",
        "Accept": "application/vnd.github+json",
    },
)

with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

lines = ["| PR | Status |", "|---|---|"]
for item in data.get("items", []):
    repo = item["repository_url"].split("/repos/")[1]
    num = item["number"]
    title = item["title"].replace("|", "\\|")
    url_ = item["html_url"]
    badge = f"https://img.shields.io/github/pulls/detail/state/{repo}/{num}"
    lines.append(f"| [{repo}#{num} \u2013 {title}]({url_}) | ![PR status]({badge}) |")

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

print(f"Updated README.md with {len(data.get('items', []))} PR(s).")
