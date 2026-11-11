# 부산 동계체전 결과 앱 (초안)

대한체육회 전국동계체육대회 사이트에서 **부산(`searchSidoCd=02`)** 메달 명세만 수집해 보여 줍니다.

## 구조
- `config.json` : 주소·메뉴 번호·시도 코드·수집 간격 (사이트 개편 시 여기부터 수정)
- `collector/parse.py` : HTML 표 → 데이터 변환 (사이트 구조가 바뀌면 여기만 수정)
- `collector/run.py` : 수집, 변경 감지(`data/events.json`), 저장
- `web/index.html` : 메달 현황 화면 (60초마다 갱신)
- `tests/` : 파서 테스트 (※ 샘플 HTML은 가정한 구조)

## 실행
```bash
pip install -r requirements.txt
python -m unittest discover tests      # 파서 테스트
python -m collector.run                 # 1회 수집
python -m collector.run --loop          # 주기 수집
python -m http.server 8000              # 브라우저: http://localhost:8000/web/
```

## 남은 일 (TODO)
1. 실제 응답의 `<table>`로 `tests/test_parse.py` 샘플 교체, `summarize()` 컬럼 규칙 확정
2. 일정·결과(시·도 기록경기일정, 선수검색) 수집기 추가
3. `events.json` 기반 푸시 알림
4. 108회 사이트 개설 후 `config.json` 갱신
5. 대한체육회에 데이터 활용 문의, 수집 간격은 보수적으로 유지

## v0.2 변경
- 일정(`/schedule/scheduleT.do`) 수집 추가, 종목별 구역 인식, 일정/메달 탭
- PDF 저장(인쇄), CSV 저장, 공유 버튼
- 진단 도구: `python -m collector.dump <schedule_t|medal> [Y]`, `python -m collector.inspect_html <이름>` (직접 추가한 파일)
- 미구현: 경기 결과(종목별 결과) 메뉴, 기록경기일정, 푸시 알림

## v0.3 변경
- 기록경기일정(`/schedule/scheduleR.do`, 메뉴 1505) 수집 추가: 날짜 지정 필수라 `config.json`의 `date_ranges` 날짜를 하루씩 조회
- 108회에는 `date_ranges`를 새 대회 기간으로 수정할 것
- 진단: `python -m collector.dump schedule_r 2026/02/25` → `python -m collector.inspect_html schedule_r`

## v0.4 변경
- 메달집계(`/medal/medalTotal.do`, 메뉴 1301) 수집: 종목 코드 12개를 돌며 부산 행만 추출 → 공식 집계 기준 금/은/동/합계
- 종목 코드: W1 빙상스피드, W2 쇼트트랙, W3 피겨, W4 아이스하키, W5 스키알파인, W6 크로스컨트리, W7 바이애슬론, W8 컬링, W9 스노보드, WD 봅슬레이스켈레톤, WE 산악, WL 루지

## v0.5 GitHub Actions + Pages 배포
1. GitHub에 저장소 생성(무료 계정은 **공개(Public)** 필수) 후 push
2. Settings → Pages → Source: **GitHub Actions**
3. Settings → Secrets and variables → Actions → **Variables**
   - `ACTIVE_FROM`, `ACTIVE_UNTIL` : 예약 수집 기간(예: 2027-01-10 / 2027-02-20). 없으면 예약 실행은 수집하지 않음
   - `COLLECTOR_UA` : (선택) 연락처가 담긴 User-Agent. 공개 저장소에 이메일을 올리지 않기 위함
   - `DROP_COLUMNS` : (선택) 기본 `none`(모든 컬럼 포함). 숨길 컬럼이 있으면 `소속,학년` 처럼 입력
4. Actions 탭 → collect-and-deploy → **Run workflow** 로 수동 시험 → 주소: `https://<아이디>.github.io/<저장소>/`
- 예약 실행은 기본 브랜치에서만 동작, 저장소 활동이 60일 없으면 자동 중지, 시작 시각은 지연될 수 있음
- 108회 대회 전 `config.json` 의 `date_ranges` 갱신 필수

## v0.6 변경
- 메달 명세 파서: 종목별로 나뉜 표를 모두 읽도록 수정(기존에는 가장 큰 표 하나만 읽었음)
- 메달 탭: 학생/일반부 구분 집계, 공식 집계와 상세 집계 비교
- 일정·메달 탭: 구분(전체/학생/일반부), 종별, 세부종목, 텍스트 검색 필터 (인쇄·CSV에도 반영)
- 학생 = 종별에 '일반부'가 없는 것(초·중·고·대학부). 기준은 web/index.html 의 ADULT 상수

## v0.6.1 변경
- 메달집계: 종목명을 제목 태그가 아닌 종목 코드(`class_names`)로 지정. 제목이 모두 '전체'라 서로 다른 종목의 같은 행이 중복으로 버려져 메달이 모자라던 문제 수정
