"""부산 데이터 수집 -> data/<이름>.json, data/events.json  (실행: python -m collector.run [--loop])"""
import json, os, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests

from collector.dates import iter_dates
from collector.parse import keep_rows, parse_medal_detail, parse_medal_total, parse_rows, parse_schedule, summarize, tally_summary

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
KST = timezone(timedelta(hours=9))
PARSERS = {"medal": parse_medal_detail, "schedule_t": parse_schedule, "schedule_r": parse_schedule,
           "medal_total": parse_medal_total}
IGNORE_FOR_ID = {"schedule_t": {"상태"}, "schedule_r": {"상태"},
                 "medal_total": {"금", "은", "동", "합계"}}      # 상태가 바뀌면 '변경' 이벤트


def dumps(o) -> str:
    return json.dumps(o, sort_keys=True, ensure_ascii=False)


def fetch_page(s: requests.Session, ep: dict, page: int, date: str | None = None, cls: str | None = None) -> str:
    data = {"searchMenuId": ep["menu_id"], "searchMenuNm": ep["menu_name"], "pageIndex": str(page),
            "searchSidoCd": "" if ep.get("no_sido") else CFG["sido_cd"], **ep.get("extra", {})}
    if date:
        data[ep["date_param"]] = date                  # 기록경기일정은 날짜 지정 필수
    if cls:
        data[ep["class_param"]] = cls                  # 메달집계는 종목 코드 지정
    r = s.post(CFG["base"] + ep["path"], data=data, timeout=10)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text


def fetch_all(name: str) -> list[dict]:
    ep, parse = CFG["endpoints"][name], PARSERS[name]
    s = requests.Session()
    s.headers["User-Agent"] = os.environ.get("COLLECTOR_UA") or CFG["user_agent"]
    s.get(CFG["base"] + "/main.do", timeout=10)      # 세션 쿠키 확보
    dates = list(iter_dates(ep["date_ranges"])) if "date_ranges" in ep else [None]
    classes = ep.get("class_codes") or [None]
    seen, out = set(), []
    for date in dates:
        for cls in classes:
            for page in range(1, CFG["max_pages"] + 1):
                rows = keep_rows(parse(fetch_page(s, ep, page, date, cls)), ep.get("keep", {}))
                new = [r for r in rows if dumps(r) not in seen]
                time.sleep(0.7)                        # 서버 부담 최소화
                if not new:                            # 새 행이 없으면 끝
                    break
                seen.update(dumps(r) for r in new)
                out += new
                if ep.get("single_page"):
                    break
    return out


def update(name: str, rows: list[dict]) -> list[dict]:
    """이전 결과와 비교해 신규/변경 행을 반환하고 파일을 갱신. 첫 실행은 이벤트 없음."""
    # 공개 배포 시 개인정보 최소화: DROP_COLUMNS="소속,학년" 처럼 지정한 컬럼은 저장하지 않음
    drop_cols = {c.strip() for c in os.environ.get("DROP_COLUMNS", "").split(",") if c.strip()}
    rows = [{k: v for k, v in r.items() if k not in drop_cols} for r in rows]
    f, ev = ROOT / f"data/{name}.json", ROOT / "data/events.json"
    first = not f.exists()
    old = [] if first else json.loads(f.read_text(encoding="utf-8"))["rows"]
    drop = IGNORE_FOR_ID.get(name, set())
    ident = lambda r: dumps({k: v for k, v in r.items() if k not in drop})
    old_map = {ident(r): r for r in old}
    changes = []
    for r in rows:
        o = old_map.get(ident(r))
        if o is None:
            changes.append({"change": "new", "row": r})
        elif o != r:
            changes.append({"change": "changed", "row": r, "before": o})
    now = datetime.now(KST).isoformat(timespec="seconds")
    body = {"updated_at": now, "rows": rows}
    if name == "medal":
        body["summary"] = summarize(rows)
    elif name == "medal_total":
        body["summary"] = tally_summary(rows)
    f.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    if changes and not first:
        events = json.loads(ev.read_text(encoding="utf-8")) if ev.exists() else []
        events += [{"at": now, "type": name, **c} for c in changes]
        ev.write_text(json.dumps(events, ensure_ascii=False, indent=1), encoding="utf-8")
    return [] if first else changes


def main(loop: bool):
    while True:
        ok = 0
        for name in CFG["endpoints"]:
            try:
                rows = fetch_all(name)
                if not rows:
                    print(f"[{name}] 경고: 표를 찾지 못함. 구조/주소 변경 가능성", file=sys.stderr)
                    continue
                ch = update(name, rows)
                ok += 1
                print(f"[{name}] {len(rows)}행, 변경 {len(ch)}건")
                # TODO: ch 가 있으면 푸시 알림 전송
            except Exception as e:                    # 한 번 실패해도 계속 돌도록
                print(f"[{name}] 수집 실패:", e, file=sys.stderr)
        if not loop:
            sys.exit(0 if ok else 1)                  # 전부 실패하면 Actions 에서 실패로 표시
        time.sleep(CFG["interval_sec"])


if __name__ == "__main__":
    main(loop="--loop" in sys.argv)
