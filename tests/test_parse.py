# 일정 샘플은 실제 응답에서 확인된 행(컬럼 7개, \xa0, '경기>부산')을 바탕으로 만든 것.
# 종목 제목 태그(h4)와 메달 표는 [가정]입니다. 실제 HTML로 교체하세요.
import unittest
from collector.parse import parse_rows, parse_schedule, summarize

SCHEDULE = """
<h4>컬링</h4>
<table><thead><tr><th>종별</th><th>세부종목</th><th>경기구분</th><th>상태</th><th>일시</th><th>경기장</th><th>시도</th></tr></thead>
<tbody>
<tr><td>남자15세이하부</td><td>단체전</td><td>준준결승경기 1</td><td>종료</td><td>2026/02/19&nbsp;16:00</td><td>강릉컬링센터</td><td>경기&gt;부산</td></tr>
<tr><td>남자18세이하부</td><td>단체전</td><td>준준결승경기 2</td><td>종료</td><td>2026/02/21&nbsp;14:00</td><td>강릉컬링센터</td><td>부산&gt;전남</td></tr>
</tbody></table>
<h4>아이스하키</h4>
<table><thead><tr><th>종별</th><th>세부종목</th><th>경기구분</th><th>상태</th><th>일시</th><th>경기장</th><th>시도</th></tr></thead>
<tbody><tr><td colspan="7">조회된 내용이 없습니다.</td></tr></tbody></table>
<h5>경기기록</h5>
<table class="tablesaw"><thead><tr><th>세부종목</th><th>경기구분</th><th>상태</th><th>순위</th><th>메달</th><th>기록</th><th>신기록</th><th>일자</th></tr></thead><tbody></tbody></table>
"""

MEDAL = """<table><thead><tr><th>종목</th><th>선수명</th><th>메달</th></tr></thead>
<tbody><tr><td>빙상스피드</td><td>홍길동</td><td>금</td></tr><tr><td>컬링</td><td>부산선발</td><td>은</td></tr></tbody></table>"""

class T(unittest.TestCase):
    def test_schedule(self):
        rows = parse_schedule(SCHEDULE)
        self.assertEqual(len(rows), 2)                       # 빈 표, 경기기록 표는 제외
        self.assertEqual(rows[0]["종목"], "컬링")
        self.assertEqual(rows[0]["일시"], "2026/02/19 16:00")  # \xa0 정리
        self.assertEqual(rows[0]["시도"], "경기>부산")

    def test_medal(self):
        s = summarize(parse_rows(MEDAL))
        self.assertEqual((s["gold"], s["silver"], s["total"]), (1, 1, 2))

    def test_empty(self):
        self.assertEqual(parse_schedule("<html></html>"), [])

RECORD = """<h4>바이애슬론</h4><table><thead><tr><th>종별</th><th>세부종목</th><th>경기구분</th><th>상태</th><th>일시</th><th>경기장</th><th>시도</th></tr></thead>
<tbody><tr><td>남자12세이하부</td><td>스프린트3KM</td><td>결승</td><td>종료</td><td>2026/02/25&nbsp;09:00 ~ 17:00</td><td>평창 알펜시아 바이애슬론 센터</td><td></td></tr></tbody></table>"""

class R(unittest.TestCase):
    def test_record(self):   # 기록경기: 시도 칸이 비어 있어도 행이 유지되어야 함
        rows = parse_schedule(RECORD)
        self.assertEqual((len(rows), rows[0]["종목"], rows[0]["시도"]), (1, "바이애슬론", ""))

    def test_dates(self):
        from collector.dates import iter_dates
        self.assertEqual(list(iter_dates([["2026/02/27", "2026/03/01"]])), ["2026/02/27", "2026/02/28", "2026/03/01"])

# 일자별 메달명세 화면처럼 종별/세부종목이 병합(rowspan)된 표
ROWSPAN = """<table><thead><tr><th>종별</th><th>세부종목</th><th>메달</th><th>시도</th><th>선수명</th></tr></thead><tbody>
<tr><td rowspan="3">남자12세이하부</td><td rowspan="3">싱글D조</td><td>금</td><td>서울</td><td>민윤하</td></tr>
<tr><td>은</td><td>인천</td><td>하지후</td></tr>
<tr><td>동</td><td>부산</td><td>김부산</td></tr>
<tr><td colspan="5">조회된 내용이 없습니다.</td></tr></tbody></table>"""

TEAM = """<table><thead><tr><th>종별</th><th>세부종목</th><th>메달</th><th>시도</th><th>선수명</th></tr></thead><tbody>
<tr><td rowspan="2">일반부</td><td rowspan="2">믹스더블</td><td>금</td><td>부산</td><td>갑</td></tr>
<tr><td>금</td><td>부산</td><td>을</td></tr></tbody></table>"""

class M(unittest.TestCase):
    def test_rowspan(self):
        rows = parse_rows(ROWSPAN)
        self.assertEqual(len(rows), 3)                      # 은·동 행이 버려지지 않아야 함
        self.assertEqual((rows[2]["종별"], rows[2]["세부종목"], rows[2]["시도"]), ("남자12세이하부", "싱글D조", "부산"))
        s = summarize(rows)
        self.assertEqual((s["gold"], s["silver"], s["bronze"]), (1, 1, 1))

    def test_team_medal_counts_once(self):
        s = summarize(parse_rows(TEAM))
        self.assertEqual((len(parse_rows(TEAM)), s["gold"]), (2, 1))

TOTAL = """<h4>빙상쇼트트랙</h4><table><thead><tr><th>시도</th><th>금</th><th>은</th><th>동</th><th>합계</th></tr></thead><tbody>
<tr><td>서울</td><td>11</td><td>14</td><td>12</td><td>37</td></tr><tr><td>부산</td><td>1</td><td>2</td><td>2</td><td>5</td></tr></tbody></table>"""

class Tot(unittest.TestCase):
    def test_total(self):
        from collector.parse import parse_medal_total, keep_rows, tally_summary
        rows = keep_rows(parse_medal_total(TOTAL), {"시도": "부산"})
        self.assertEqual((len(rows), rows[0]["종목"]), (1, "빙상쇼트트랙"))
        self.assertEqual(tally_summary(rows), {"gold": 1, "silver": 2, "bronze": 2, "total": 5})

if __name__ == "__main__":
    unittest.main()
