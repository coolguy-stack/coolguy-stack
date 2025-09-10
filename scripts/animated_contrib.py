#!/usr/bin/env python3
import os, sys, datetime, json, urllib.request

USERNAME = os.getenv("GH_USERNAME") or "coolguy-stack"
TOKEN = os.getenv("GH_TOKEN")  # set in GitHub Secrets
DAYS = 365

# GitHub GraphQL query to fetch daily contributions for last 1 year
query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""

def gh_graphql(q, variables):
  req = urllib.request.Request(
    "https://api.github.com/graphql",
    data=json.dumps({"query": q, "variables": variables}).encode("utf-8"),
    headers={
      "Authorization": f"bearer {TOKEN}",
      "Content-Type": "application/json",
      "User-Agent": "animated-contrib"
    }
  )
  with urllib.request.urlopen(req) as r:
    return json.loads(r.read().decode("utf-8"))

def build_svg(weeks):
  # Grid settings (GitHub-like)
  cell = 11
  gap = 2
  margin_left, margin_top = 20, 20
  width = margin_left + len(weeks)*(cell+gap) + 20
  height = margin_top + 7*(cell+gap) + 20

  # CSS animation: staggered fade/scale-in
  css = """
  <![CDATA[
  @keyframes pop { 0% {opacity:.0; transform:scale(.5)} 100% {opacity:1; transform:scale(1)} }
  rect { shape-rendering:crispEdges; rx:2; ry:2; }
  .t { font: 600 12px system-ui, -apple-system, Segoe UI, Roboto; fill:#0f172a; }
  ]]>
  """

  svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">']
  svg.append(f"<style>{css}</style>")
  svg.append(f'<text class="t" x="{margin_left}" y="14">Last 12 months of commits</text>')

  # Draw cells with per-cell animation delay
  idx = 0
  x = margin_left
  for w in weeks:
    y = margin_top
    for d in w["contributionDays"]:
      color = d["color"] or "#ebedf0"
      svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{color}" '
                 f'style="opacity:0; animation: pop .5s ease {idx*0.02:.2f}s forwards" />')
      y += cell + gap
      idx += 1
    x += cell + gap

  svg.append("</svg>")
  return "\n".join(svg)

def main():
  if not TOKEN:
    print("GH_TOKEN not set", file=sys.stderr)
    sys.exit(1)

  to = datetime.datetime.utcnow().replace(microsecond=0)
  frm = to - datetime.timedelta(days=DAYS)
  data = gh_graphql(query, {"login": USERNAME, "from": frm.isoformat()+"Z", "to": to.isoformat()+"Z"})

  weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
  svg = build_svg(weeks)
  with open("animated-contrib.svg", "w", encoding="utf-8") as f:
    f.write(svg)

if __name__ == "__main__":
  main()
