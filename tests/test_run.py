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

if __name__ == "__main__":
    unittest.main()
