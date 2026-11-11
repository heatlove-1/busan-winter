"""HTML 표 -> dict 목록. 사이트 개편 시 이 파일만 고치면 되도록 분리."""
import re
from bs4 import BeautifulSoup

MEDAL_WORDS = {"금": "gold", "금메달": "gold", "은": "silver", "은메달": "silver",
               "동": "bronze", "동메달": "bronze"}
HEADINGS = ["h1", "h2", "h3", "h4", "h5", "h6"]


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()   # \xa0 포함 공백 정리


def _span(td, attr: str) -> int:
    try:
        return max(1, int(td.get(attr, 1)))
    except (TypeError, ValueError):
        return 1


def _table_rows(table) -> tuple[list[str], list[dict]]:
    """rowspan(병합 셀)을 펼쳐서 모든 행이 컬럼 수만큼의 값을 갖도록 만든다."""
    heads = [_clean(th.get_text()) for th in table.select("thead th")] \
        or [_clean(th.get_text()) for th in table.select("tr:first-child th")]
    rows, carry = [], {}                      # carry: {열 번호: [남은 행 수, 값]}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not heads or not tds or any(_span(td, "colspan") > 1 for td in tds):
            continue                          # 헤더 행, '조회된 내용이 없습니다' 행 제외
        vals, col, pending = [], 0, list(tds)
        while col < len(heads):
            if carry.get(col, [0])[0] > 0:    # 위 행에서 병합된 칸
                carry[col][0] -= 1
                vals.append(carry[col][1])
            elif pending:
                td = pending.pop(0)
                text = _clean(td.get_text(" "))
                if _span(td, "rowspan") > 1:
                    carry[col] = [_span(td, "rowspan") - 1, text]
                vals.append(text)
            else:
                break
            col += 1
        if len(vals) == len(heads) and not pending:
            rows.append(dict(zip(heads, vals)))
    return heads, rows


def parse_rows(html: str) -> list[dict]:
    """메달명세: 행이 가장 많은 표 하나."""
    best: list[dict] = []
    for table in BeautifulSoup(html, "html.parser").find_all("table"):
        _, rows = _table_rows(table)
        if len(rows) > len(best):
            best = rows
    return best


def parse_tables(html: str, required: set) -> list[dict]:
    """required 헤더를 모두 가진 표만 읽고, 표 앞 제목을 '종목'으로 붙임."""
    out = []
    for table in BeautifulSoup(html, "html.parser").find_all("table"):
        heads, rows = _table_rows(table)
        if not required <= set(heads):
            continue                     # 경기기록, 참가기록 등 다른 표는 건너뜀
        h = table.find_previous(HEADINGS)
        sport = _clean(h.get_text()) if h else "기타"
        out += [{"종목": sport, **r} for r in rows]
    return out


def parse_schedule(html: str) -> list[dict]:
    return parse_tables(html, {"일시", "경기장"})


def parse_medal_total(html: str) -> list[dict]:
    return parse_tables(html, {"시도", "금", "은", "동", "합계"})


def keep_rows(rows: list[dict], keep: dict) -> list[dict]:
    return [r for r in rows if all(r.get(k) == v for k, v in keep.items())]


def tally_summary(rows: list[dict]) -> dict:
    """메달집계 행들의 금/은/동/합계를 더한다(공식 집계 기준)."""
    t = lambda k: sum(int(r[k]) for r in rows if str(r.get(k, "")).isdigit())
    return {"gold": t("금"), "silver": t("은"), "bronze": t("동"), "total": t("합계")}


def summarize(rows: list[dict]) -> dict:
    """메달 수 추정. (종목, 종별, 세부종목, 메달) 조합 하나를 메달 1개로 센다(단체전은 선수 여러 명이 한 메달).
    [가정] 값이 금/은/동인 컬럼이 있음. 종별·세부종목 컬럼이 없으면 행마다 1개로 센다."""
    s = {"gold": 0, "silver": 0, "bronze": 0}
    seen = set()
    for i, r in enumerate(rows):
        m = next((MEDAL_WORDS[v] for v in r.values() if v in MEDAL_WORDS), None)
        if not m:
            continue
        k = (r.get("종목"), r.get("종별"), r.get("세부종목"), m) if r.get("종별") and r.get("세부종목") else ("row", i)
        if k not in seen:
            seen.add(k)
            s[m] += 1
    s["total"] = sum(s.values())
    return s
