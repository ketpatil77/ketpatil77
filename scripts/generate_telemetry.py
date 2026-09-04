import json, os, urllib.request, urllib.parse
from collections import Counter
from pathlib import Path

USER = os.getenv("PROFILE_USER", "ketpatil77")
TOKEN = os.environ["GITHUB_TOKEN"]

def request(url, payload=None):
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": "profile-telemetry", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as response:
        return json.load(response)

query = '''query($login:String!){user(login:$login){repositories(first:100,ownerAffiliations:OWNER,isFork:false){totalCount nodes{primaryLanguage{name} stargazerCount}} contributionsCollection{contributionCalendar{totalContributions weeks{contributionDays{contributionCount date}}}}}}'''
user = request("https://api.github.com/graphql", {"query": query, "variables": {"login": USER}})["data"]["user"]
repos = user["repositories"]
calendar = user["contributionsCollection"]["contributionCalendar"]
days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
counts = [day["contributionCount"] for day in days]
weekly = [sum(counts[i:i+7]) for i in range(0, len(counts), 7)][-52:]
languages = Counter(node["primaryLanguage"]["name"] for node in repos["nodes"] if node["primaryLanguage"])
stars = sum(node["stargazerCount"] for node in repos["nodes"])

def search(q):
    return request("https://api.github.com/search/issues?q=" + urllib.parse.quote(q))["total_count"]

merged = search(f"author:{USER} type:pr is:merged")
open_prs = search(f"author:{USER} type:pr is:open")
peak = max(weekly) or 1
points = " ".join(f"{95+i*(1010/(len(weekly)-1)):.1f},{390-(v/peak)*135:.1f}" for i,v in enumerate(weekly))
area = f"95,390 {points} 1105,390"
bars = []
for i, value in enumerate(weekly):
    height = max(2, (value/peak)*116)
    x = 96 + i*(1008/len(weekly))
    bars.append(f'<rect x="{x:.1f}" y="{520-height:.1f}" width="{max(3,1008/len(weekly)-4):.1f}" height="{height:.1f}" rx="2"/>')

palette = ["#38bdf8", "#3b82f6", "#8b5cf6", "#f59e0b", "#22d3ee"]
lang_total = sum(languages.values()) or 1
lang_rows=[]
offset=0
for index,(name,value) in enumerate(languages.most_common(5)):
    width=285*value/lang_total
    lang_rows.append(f'<rect x="{770+offset:.1f}" y="207" width="{width:.1f}" height="10" fill="{palette[index]}"/><text x="770" y="{245+index*22}" fill="#94a3b8" font-size="12">{name.upper():18}</text><text x="1045" y="{245+index*22}" fill="#e2e8f0" font-size="12" text-anchor="end">{value/lang_total*100:4.1f}%</text>')
    offset += width

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="570" viewBox="0 0 1200 570" role="img" aria-labelledby="t d">
<title id="t">Live GitHub engineering telemetry for {USER}</title><desc id="d">Daily-generated dashboard with contribution, repository, pull request, and language metrics.</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#050914"/><stop offset="1" stop-color="#0c1831"/></linearGradient><linearGradient id="area" x2="0" y2="1"><stop stop-color="#3b82f6" stop-opacity=".42"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></linearGradient><pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse"><path d="M24 0H0V24" fill="none" stroke="#60a5fa" stroke-opacity=".055"/></pattern><filter id="glow"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<rect width="1200" height="570" rx="16" fill="url(#bg)"/><rect width="1200" height="570" rx="16" fill="url(#grid)"/><g font-family="Consolas,Menlo,monospace">
<text x="60" y="55" fill="#f8fafc" font-size="22" font-weight="700">LIVE ENGINEERING TELEMETRY</text><text x="1140" y="55" fill="#38bdf8" font-size="12" text-anchor="end">AUTO-SYNC / 24H</text><circle cx="1118" cy="51" r="4" fill="#22d3ee" filter="url(#glow)" class="pulse"/>
<g>{''.join(f'<g transform="translate({60+i*222} 88)"><rect width="198" height="82" rx="7" fill="#0f172a" stroke="#1e3a8a"/><text x="18" y="26" fill="#64748b" font-size="11">{label}</text><text x="18" y="62" fill="#f8fafc" font-size="28" font-weight="700">{value}</text></g>' for i,(label,value) in enumerate([("CONTRIBUTIONS / 12M",calendar["totalContributions"]),("PUBLIC REPOSITORIES",repos["totalCount"]),("MERGED PULL REQUESTS",merged),("OPEN PULL REQUESTS",open_prs),("REPOSITORY STARS",stars)]))}</g>
<text x="60" y="213" fill="#64748b" font-size="12">52-WEEK CONTRIBUTION VELOCITY</text><path d="M95 390H1120M95 255V390" stroke="#334155"/><polygon points="{area}" fill="url(#area)"/><polyline points="{points}" fill="none" stroke="#38bdf8" stroke-width="3" filter="url(#glow)" class="trace"/><text x="95" y="417" fill="#64748b" font-size="11">T-52W</text><text x="1105" y="417" fill="#64748b" font-size="11" text-anchor="end">NOW</text><text x="1125" y="267" fill="#f59e0b" font-size="11">PEAK {peak}</text>
<g transform="translate(0 0)"><text x="770" y="190" fill="#64748b" font-size="12">PRIMARY LANGUAGE DISTRIBUTION</text>{''.join(lang_rows)}</g>
<text x="60" y="462" fill="#64748b" font-size="12">WEEKLY COMMIT DENSITY</text><g fill="#2563eb" opacity=".72">{''.join(bars)}</g>
</g><style>.pulse{{animation:p 1.6s ease-in-out infinite}}.trace{{stroke-dasharray:1400;animation:d 3s ease-out both}}@keyframes p{{50%{{opacity:.2}}}}@keyframes d{{from{{stroke-dashoffset:1400}}to{{stroke-dashoffset:0}}}}@media(prefers-reduced-motion:reduce){{.pulse,.trace{{animation:none}}}}</style></svg>'''
out=Path("assets/live-telemetry.svg"); out.parent.mkdir(exist_ok=True); out.write_text(svg,encoding="utf-8")
print(f"generated {out} for {USER}: {calendar['totalContributions']} contributions, {repos['totalCount']} repos")
