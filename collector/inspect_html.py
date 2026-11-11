"""진단용: 표 구조 출력.  python -m collector.inspect_html schedule_r"""
import sys
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
soup = BeautifulSoup((ROOT / "data" / f"raw_{sys.argv[1]}.html").read_text(encoding="utf-8"), "html.parser")
for i, t in enumerate(soup.find_all("table")):
    prev = t.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
    print(f"--- 표 {i} | 앞 제목: {prev.name + ': ' + prev.get_text(strip=True) if prev else None}")
    for tr in t.find_all("tr")[:3]:
        print([c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"])])
