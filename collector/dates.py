from datetime import date, timedelta


def iter_dates(ranges):
    """[["2026/02/27","2026/03/01"], ...] -> 날짜 문자열을 하루씩 생성"""
    for a, b in ranges:
        d, end = (date(*map(int, x.split("/"))) for x in (a, b))
        while d <= end:
            yield d.strftime("%Y/%m/%d")
            d += timedelta(days=1)
