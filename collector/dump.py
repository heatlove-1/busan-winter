"""진단용: 응답 HTML 저장.
  python -m collector.dump schedule_r 2026/02/25
  python -m collector.dump medal_total - W2      (날짜 없음은 '-', 종목 코드는 세 번째)"""
import sys
import requests
from collector.run import CFG, ROOT, fetch_page

name = sys.argv[1]
date = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
cls = sys.argv[3] if len(sys.argv) > 3 else None
s = requests.Session()
s.headers["User-Agent"] = CFG["user_agent"]
s.get(CFG["base"] + "/main.do", timeout=10)
html = fetch_page(s, CFG["endpoints"][name], 1, date, cls)
out = ROOT / "data" / f"raw_{name}.html"
out.write_text(html, encoding="utf-8")
print("길이", len(html), "| 저장:", out)
