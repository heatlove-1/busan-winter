import unittest
from unittest import mock
import collector.run as R

# 제목이 모두 '전체'인 응답에서, 다른 종목의 똑같은 행이 중복으로 버려지지 않아야 함
HTML = ('<h4>전체</h4><table><thead><tr><th>시도</th><th>금</th><th>은</th><th>동</th><th>합계</th></tr></thead>'
        '<tbody><tr><td>부산</td><td>0</td><td>0</td><td>1</td><td>1</td></tr></tbody></table>')

class S:
    headers = {}
    def get(self, *a, **k): pass

class T(unittest.TestCase):
    def test_same_rows_in_different_sports_are_kept(self):
        with mock.patch.object(R.requests, "Session", S), mock.patch.object(R.time, "sleep", lambda x: None), \
             mock.patch.object(R, "fetch_page", lambda s, ep, page, date=None, cls=None: HTML):
            rows = R.fetch_all("medal_total")
        n = len(R.CFG["endpoints"]["medal_total"]["class_codes"])
        self.assertEqual(len(rows), n)
        self.assertEqual(len({r["종목"] for r in rows}), n)
        self.assertIn("컬링", {r["종목"] for r in rows})

def detail_html(name):
    return ('<h4>전체</h4><table><thead><tr><th>종별</th><th>세부종목</th><th>메달</th><th>선수명</th><th>소속</th><th>학년</th><th>기록</th><th>신기록</th><th>일자</th></tr></thead>'
            f'<tbody><tr><td>남자15세이하부</td><td>x</td><td>금</td><td>{name}</td><td>학교</td><td>2</td><td>1</td><td></td><td>2026/02/25</td></tr></tbody></table>')

class Detail(unittest.TestCase):
    def run_medal(self, fake):
        with mock.patch.object(R.requests, "Session", S), mock.patch.object(R.time, "sleep", lambda x: None), \
             mock.patch.object(R, "fetch_page", fake):
            return R.fetch_all("medal")

    def test_class_filter_honored(self):      # 종목 필터가 적용되면 종목명이 붙고 중복 없음
        rows = self.run_medal(lambda s, ep, page, date=None, cls=None: detail_html("선수" + str(cls)) if page == 1 else "")
        n = len(R.CFG["endpoints"]["medal"]["class_codes"])
        self.assertEqual((len(rows), len({r["종목"] for r in rows})), (n, n))

    def test_class_filter_ignored(self):      # 종목 필터가 무시되면 중복 없이 기존 방식으로 복귀
        rows = self.run_medal(lambda s, ep, page, date=None, cls=None: detail_html("같은선수") if page == 1 else "")
        self.assertEqual((len(rows), rows[0]["종목"]), (1, ""))

if __name__ == "__main__":
    unittest.main()
