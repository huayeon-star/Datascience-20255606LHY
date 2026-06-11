"""
서울시 문화시설 사각지대 - HTML 생성 파이썬 코드 (v22 최종)
=============================================================
이 스크립트는 분석이 완료된 JSON 데이터를 읽어
Leaflet.js 기반 웹사이트(seoul_map_v22.html)를 생성합니다.

사전 필요 파일 (seoul_analysis_v21.py 실행 후 생성됨):
  - gu_v5.json          : 자치구 폴리곤 + 접근성 점수
  - dong_v6.json        : 행정동 폴리곤 + 접근성 점수 + blind_rank
  - facilities_v3.json  : 문화시설 / 버스 / 지하철 통합 데이터

출력 파일:
  - seoul_map_v22.html  : 표지 + 지도 통합 최종 웹사이트
"""

import json

# ============================================================
# STEP 1: JSON 데이터 로드
# ============================================================

with open('gu_v5.json', 'r', encoding='utf-8') as f:
    gu_data = json.load(f)

with open('dong_v6.json', 'r', encoding='utf-8') as f:
    dong_data = json.load(f)

with open('facilities_v3.json', 'r', encoding='utf-8') as f:
    fac = json.load(f)

# JS 인라인 삽입용 직렬화 (</script> 태그 이스케이프 처리)
def to_js(d):
    return json.dumps(d, ensure_ascii=False).replace('</script>', '<\\/script>')

gu_js      = to_js(gu_data)
dong_js    = to_js(dong_data)
culture_js = to_js(fac['culture'])
bus_js     = to_js(fac['bus'])
metro_js   = to_js(fac['metro'])

# 사각지대 통계
blind_total = sum(1 for d in dong_data if d['blind'])
blind_1     = sum(1 for d in dong_data if d['blind_rank'] == 1)
blind_2     = sum(1 for d in dong_data if d['blind_rank'] == 2)
blind_3     = sum(1 for d in dong_data if d['blind_rank'] == 3)
metro_count = len(fac['metro'])

print(f"자치구: {len(gu_data)}개")
print(f"행정동: {len(dong_data)}개")
print(f"문화시설: {len(fac['culture'])}개")
print(f"버스: {len(fac['bus'])}개")
print(f"지하철: {metro_count}개역")
print(f"사각지대: 총 {blind_total}개 (3단계 {blind_3} / 2단계 {blind_2} / 1단계 {blind_1})")


# ============================================================
# STEP 2: HTML 생성
# ============================================================
# 구조: 표지 화면(cover-page) + 지도 화면(header + nav + map)
# 표지에서 탭 카드 클릭 → 해당 탭으로 지도 진입
# 지도 상단 '처음으로' 버튼 → 표지 복귀

html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>서울시 문화시설 사각지대 분석 v22</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css"/>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<style>
/* ── 공통 초기화 ── */
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Malgun Gothic',sans-serif;background:#fff;color:#1a2a3a;
     height:100vh;display:flex;flex-direction:column;overflow:hidden}}

/* ════════════════════════════════
   표지 화면
════════════════════════════════ */
#cover-page{{
  position:fixed;inset:0;z-index:9999;
  background:#ffffff;display:flex;flex-direction:column;
  font-family:'Malgun Gothic',sans-serif;overflow:hidden;
}}
#cover-page.hidden{{opacity:0;pointer-events:none;transition:opacity .6s ease;}}

/* 헤더 */
.cv-header{{
  display:flex;align-items:center;justify-content:space-between;
  padding:18px 28px 14px;border-bottom:1.5px solid #e2e8f0;flex-shrink:0;
}}
.cv-team{{display:flex;align-items:center;gap:10px;}}
.cv-team-icon{{
  width:36px;height:36px;border-radius:8px;
  background:linear-gradient(135deg,#1a3a5c,#2563a8);
  display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:16px;flex-shrink:0;
}}
.cv-team-name{{font-size:15px;font-weight:700;color:#1a2a3a;letter-spacing:-.3px}}
.cv-team-sub{{font-size:11px;color:#6a8aaa;margin-top:1px}}

/* 본문 */
.cv-body{{
  flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:0 40px 80px;position:relative;overflow:hidden;
}}
.cv-seoul-bg{{
  position:absolute;bottom:0;left:50%;transform:translateX(-50%);
  width:100%;max-width:900px;opacity:0.06;pointer-events:none;
}}
.cv-badge-row{{display:flex;gap:8px;margin-bottom:28px;}}
.cv-badge{{padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;}}
.cv-badge.b1{{background:rgba(59,130,246,.10);color:#1a6abf;border:1px solid #bfdbfe;}}
.cv-badge.b2{{background:rgba(22,163,74,.10);color:#166534;border:1px solid #bbf7d0;}}
.cv-badge.b3{{background:rgba(234,88,12,.10);color:#9a3412;border:1px solid #fed7aa;}}
.cv-title{{
  font-size:52px;font-weight:900;color:#0f172a;
  letter-spacing:-1.5px;text-align:center;line-height:1.1;margin-bottom:16px;
}}
.cv-title em{{
  font-style:normal;
  background:linear-gradient(90deg,#1a3a5c,#2563a8);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}}
.cv-sub{{font-size:17px;color:#4a6a8a;text-align:center;margin-bottom:52px;line-height:1.6;}}

/* 탭 카드 3개 */
.cv-tab-cards{{display:flex;gap:14px;}}
.cv-tab-card{{
  display:flex;flex-direction:column;align-items:flex-start;
  padding:16px 20px;border-radius:14px;cursor:pointer;
  border:1.5px solid #e2e8f0;background:#f8fafc;
  transition:all .2s;min-width:190px;
}}
.cv-tab-card:hover{{
  border-color:#3b82f6;background:#f0f5fb;
  transform:translateY(-3px);box-shadow:0 8px 20px rgba(37,99,235,.12);
}}
.cv-tab-card-num{{
  width:28px;height:28px;border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:700;color:#fff;margin-bottom:10px;
}}
.cv-tab-card-label{{font-size:14px;font-weight:700;color:#1a2a3a;margin-bottom:4px;}}
.cv-tab-card-desc{{font-size:11px;color:#6a8aaa;line-height:1.5;}}

/* 하단 통계 */
.cv-stats{{display:flex;gap:40px;margin-top:52px;}}
.cv-stat{{text-align:center;}}
.cv-stat-num{{font-size:28px;font-weight:800;color:#1a3a5c;}}
.cv-stat-label{{font-size:11px;color:#6a8aaa;margin-top:3px;}}
.cv-divider{{width:1px;background:#e2e8f0;align-self:stretch;margin:4px 0;}}

/* ── 표지 복귀 버튼 ── */
#back-to-cover-btn{{
  position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:8000;
  padding:6px 16px;background:rgba(255,255,255,0.92);
  border:1px solid #d0dce8;border-radius:20px;
  font-size:12px;font-weight:600;color:#1a3a5c;
  cursor:pointer;box-shadow:0 2px 8px rgba(0,0,50,.10);
  transition:all .18s;display:none;
}}
#back-to-cover-btn:hover{{background:#e8f0f8;border-color:#3b82f6;}}

/* ════════════════════════════════
   지도 화면 공통
════════════════════════════════ */
header{{background:linear-gradient(90deg,#1a3a5c,#1e4d7b);border-bottom:1px solid #2a5a8a;
        padding:10px 20px;display:flex;align-items:center;gap:14px;flex-shrink:0}}
header h1{{font-size:17px;font-weight:700;color:#fff}}
header .sub{{font-size:11px;color:#a0c0e0;margin-top:2px}}
.hbadge{{margin-left:auto;display:flex;gap:8px}}
.badge{{padding:3px 9px;border-radius:10px;font-size:11px;font-weight:600}}
.bc{{background:rgba(59,130,246,.18);color:#1a6abf;border:1px solid #3b82f6}}
.bt{{background:rgba(22,163,74,.13);color:#166534;border:1px solid #22c55e}}

nav{{background:#1e3a5c;border-bottom:1px solid #2a5a8a;display:flex;padding:0 20px;gap:2px;flex-shrink:0}}
.tab{{padding:9px 18px;font-size:13px;font-weight:600;color:#90b8d8;background:none;
      border:none;border-bottom:2px solid transparent;cursor:pointer;transition:all .18s;white-space:nowrap}}
.tab:hover{{color:#c0d8f0}}
.tab.on{{color:#fff;border-bottom-color:#60a8e0}}
.tab .num{{display:inline-block;background:#2a4a6a;border-radius:8px;padding:1px 6px;
           font-size:10px;margin-left:5px;color:#90b8d8}}
.tab.on .num{{background:rgba(96,168,224,.3);color:#c0e0ff}}

.main{{display:flex;flex:1;overflow:hidden}}

/* 사이드바 */
.sb{{width:280px;background:#f0f4f8;border-right:1px solid #c0d0e0;overflow-y:auto;flex-shrink:0}}
.sb::-webkit-scrollbar{{width:3px}}
.sb::-webkit-scrollbar-track{{background:#e8f0f8}}
.sb::-webkit-scrollbar-thumb{{background:#a0b8d0;border-radius:2px}}
.sec{{padding:14px;border-bottom:1px solid #d0e0f0}}
.sec h3{{font-size:11px;font-weight:700;color:#2a5a8a;text-transform:uppercase;
          letter-spacing:.5px;margin-bottom:8px}}
.tog{{display:flex;align-items:center;gap:9px;padding:7px 8px;border-radius:7px;
      cursor:pointer;transition:background .13s;margin-bottom:3px;user-select:none}}
.tog:hover{{background:#dce8f4}}
.tknob{{width:30px;height:16px;border-radius:8px;background:#b0c8e0;
         position:relative;transition:background .18s;flex-shrink:0}}
.tknob::after{{content:'';position:absolute;left:2px;top:2px;width:12px;height:12px;
               border-radius:50%;background:#7a9ab8;transition:all .18s}}
.tog.on .tknob{{background:var(--c)}}
.tog.on .tknob::after{{left:16px;background:#fff}}
.tlbl{{font-size:12px;color:#2a4a6a;flex:1}}
.tcnt{{font-size:10px;color:#6a8aaa}}
.grade-row{{display:flex;align-items:center;gap:7px;margin-bottom:4px;font-size:11px;color:#4a6a8a}}
.grade-box{{width:28px;height:11px;border-radius:2px;flex-shrink:0}}
.bsi{{border-radius:7px;padding:7px 10px;margin-bottom:4px;cursor:pointer;
      transition:all .13s;border:1px solid transparent}}
.bsi:hover{{filter:brightness(.93)}}
.bsi .bn{{font-size:11px;font-weight:600}}
.bsi .bd{{font-size:10px;color:#888;margin-top:1px}}
.note{{padding:8px 10px;background:rgba(37,99,235,.06);border-left:3px solid #3b82f6;
       border-radius:0 6px 6px 0;font-size:11px;color:#1a3a6a;line-height:1.7;margin-top:6px}}
.note b{{color:#1a4a9a}}
.note .step{{display:flex;align-items:flex-start;gap:4px;margin-bottom:4px}}
.note .step-num{{background:#3b82f6;color:#fff;border-radius:50%;width:16px;height:16px;
                  font-size:9px;font-weight:700;display:flex;align-items:center;
                  justify-content:center;flex-shrink:0;margin-top:1px}}
.abar{{margin-bottom:7px}}
.abar .al{{display:flex;justify-content:space-between;font-size:10px;color:#6a8aaa;margin-bottom:2px}}
.atrack{{height:5px;background:#d0e0f0;border-radius:3px;overflow:hidden}}
.afill{{height:100%;border-radius:3px}}

#map{{flex:1;background:#fff}}

/* 팝업 */
.leaflet-popup-content-wrapper{{background:#fff!important;color:#1a2a3a!important;
  border:1px solid #a0c0e0!important;border-radius:9px!important;
  box-shadow:0 4px 18px rgba(0,0,50,.15)!important}}
.leaflet-popup-tip{{background:#fff!important}}
.ptitle{{font-size:13px;font-weight:700;color:#1a2a3a;margin-bottom:5px}}
.ptag{{display:inline-block;padding:2px 7px;border-radius:9px;font-size:10px;margin-bottom:5px}}
.prow{{font-size:11px;color:#4a6a8a;margin-top:2px}}
.prow span{{color:#1a3a5a}}

.map-label{{background:transparent;border:none;box-shadow:none;pointer-events:none}}
.dong-tooltip{{background:rgba(255,255,255,.95);border:1px solid #90b0d0;border-radius:5px;
               padding:3px 8px;font-size:11px;color:#1a3a5a;
               box-shadow:0 2px 6px rgba(0,0,50,.12);pointer-events:none}}
.cul-icon{{background:transparent;border:none;box-shadow:none}}
</style>
</head>
<body>

<!-- ════════ 표지 화면 ════════ -->
<div id="cover-page">
  <div class="cv-header">
    <div class="cv-team">
      <div class="cv-team-icon">🗺️</div>
      <div>
        <div class="cv-team-name">지도밖문화팀</div>
        <div class="cv-team-sub">서울시 빅데이터 활용 경진대회</div>
      </div>
    </div>
  </div>
  <div class="cv-body">
    <!-- 서울 윤곽선 SVG 배경 -->
    <svg class="cv-seoul-bg" viewBox="0 0 900 300" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M20,220 C60,200 90,210 130,190 C160,175 180,160 220,155 C260,150 280,165 310,150
               C340,135 350,110 390,105 C430,100 450,120 490,115 C530,110 550,90 590,95
               C630,100 650,125 680,120 C710,115 730,95 760,100 C790,105 810,130 840,125
               C865,120 875,105 890,110 L890,300 L20,300 Z" fill="#1a3a5c"/>
      <path d="M20,240 C70,225 100,235 140,215 C170,200 195,185 235,178 C270,172 290,185 325,172
               C358,159 368,138 405,132 C445,126 465,144 505,138 C545,132 562,114 600,120
               C638,126 658,148 688,142 C718,136 738,118 768,124 C798,130 818,152 848,146"
            stroke="#2563a8" stroke-width="2" fill="none" opacity="0.5"/>
    </svg>
    <div class="cv-badge-row">
      <span class="cv-badge b1">425개 행정동</span>
      <span class="cv-badge b2">공공데이터 기반</span>
      <span class="cv-badge b3">사각지대 127개</span>
    </div>
    <h1 class="cv-title">문화시설<br><em>사각지대</em></h1>
    <p class="cv-sub">서울시 문화시설 접근성 분석 · 사각지대 한눈에 알아보기</p>
    <!-- 탭 카드 3개 — 클릭 시 해당 탭으로 지도 진입 -->
    <div class="cv-tab-cards">
      <div class="cv-tab-card" onclick="enterSite(0)">
        <div class="cv-tab-card-num" style="background:#6366f1">01</div>
        <div class="cv-tab-card-label">🏛️ 문화시설 접근성</div>
        <div class="cv-tab-card-desc">단계구분도 · 유형별<br>시설 레이어 필터</div>
      </div>
      <div class="cv-tab-card" onclick="enterSite(1)">
        <div class="cv-tab-card-num" style="background:#16a34a">02</div>
        <div class="cv-tab-card-label">🚌 대중교통 접근성</div>
        <div class="cv-tab-card-desc">버스정류장 · 지하철역<br>분포 시각화</div>
      </div>
      <div class="cv-tab-card" onclick="enterSite(2)">
        <div class="cv-tab-card-num" style="background:#ea580c">03</div>
        <div class="cv-tab-card-label">⚠️ 문화시설 사각지대</div>
        <div class="cv-tab-card-desc">3단계 사각지대<br>127개 행정동 분석</div>
      </div>
    </div>
    <div class="cv-stats">
      <div class="cv-stat"><div class="cv-stat-num">1,086</div><div class="cv-stat-label">문화공간</div></div>
      <div class="cv-divider"></div>
      <div class="cv-stat"><div class="cv-stat-num">11,640</div><div class="cv-stat-label">대중교통 시설</div></div>
      <div class="cv-divider"></div>
      <div class="cv-stat"><div class="cv-stat-num">127</div><div class="cv-stat-label">사각지대 행정동</div></div>
      <div class="cv-divider"></div>
      <div class="cv-stat"><div class="cv-stat-num">25</div><div class="cv-stat-label">자치구 분석</div></div>
    </div>
  </div>
</div>

<!-- 표지 복귀 버튼 (지도 진입 후 상단 중앙에 표시) -->
<button id="back-to-cover-btn" onclick="backToCover()">🏠 처음으로</button>

<!-- ════════ 지도 화면 ════════ -->
<header>
  <div>
    <h1>🗺️ 서울시 문화시설 사각지대 분석</h1>
    <div class="sub">서울시 공공데이터 기반 · 425개 행정동 · 용도지역 인구가중 격자 샘플링</div>
  </div>
  <div class="hbadge">
    <span class="badge bc">문화공간 1,086개</span>
    <span class="badge bt">대중교통 {11237 + metro_count:,}개</span>
  </div>
</header>
<nav>
  <button class="tab on" id="tab0" onclick="switchTab(0)">🏛️ 문화시설 접근성<span class="num">01</span></button>
  <button class="tab"    id="tab1" onclick="switchTab(1)">🚌 대중교통 접근성<span class="num">02</span></button>
  <button class="tab"    id="tab2" onclick="switchTab(2)">⚠️ 문화시설 사각지대<span class="num">03</span></button>
</nav>

<div class="main">
<div class="sb">

  <!-- 패널 0: 문화시설 접근성 -->
  <div id="p0">
    <div class="sec">
      <h3>레이어 선택</h3>
      <label class="tog on" id="p0-choro" style="--c:#6366f1" onclick="p0.toggleChoro(this)">
        <div class="tknob"></div><span class="tlbl">문화접근성 단계구분도</span>
      </label>
      <label class="tog on" id="p0-labels" style="--c:#64748b" onclick="p0.toggleLabels(this)">
        <div class="tknob"></div><span class="tlbl">지역명 표시</span>
      </label>
    </div>
    <div class="sec">
      <h3>문화시설 레이어</h3>
      <label class="tog on" id="p0-lib"  style="--c:#e11d48" onclick="p0.toggleLayer('도서관',this)">
        <div class="tknob"></div><span class="tlbl">🩷 도서관</span><span class="tcnt">246</span>
      </label>
      <label class="tog on" id="p0-art"  style="--c:#7c3aed" onclick="p0.toggleLayer('미술관/갤러리',this)">
        <div class="tknob"></div><span class="tlbl">💎 미술관/갤러리</span><span class="tcnt">234</span>
      </label>
      <label class="tog on" id="p0-mus"  style="--c:#059669" onclick="p0.toggleLayer('박물관/기념관',this)">
        <div class="tknob"></div><span class="tlbl">🍀 박물관/기념관</span><span class="tcnt">162</span>
      </label>
      <label class="tog on" id="p0-perf" style="--c:#d97706" onclick="p0.toggleLayer('공연장',this)">
        <div class="tknob"></div><span class="tlbl">⭐ 공연장</span><span class="tcnt">162</span>
      </label>
      <label class="tog on" id="p0-etc"  style="--c:#0369a1" onclick="p0.toggleLayer('기타',this)">
        <div class="tknob"></div><span class="tlbl">● 문화원/시설/기타</span><span class="tcnt">282</span>
      </label>
    </div>
    <div class="sec">
      <h3>단계구분도 범례</h3>
      <div class="grade-row"><div class="grade-box" style="background:transparent;border:1px dashed #bbb"></div>상위 20% — 표시 없음</div>
      <div class="grade-row"><div class="grade-box" style="background:#fca5a5"></div>20~40% — 연분홍</div>
      <div class="grade-row"><div class="grade-box" style="background:#f87171"></div>40~60% — 분홍</div>
      <div class="grade-row"><div class="grade-box" style="background:#ef4444"></div>60~80% — 빨강</div>
      <div class="grade-row"><div class="grade-box" style="background:#991b1b"></div>하위 20% — 진빨강</div>
    </div>
    <div class="sec">
      <h3>문화접근성 점수 산출 방식</h3>
      <div class="note">
        <b>📐 4가지 지표 가중 합산</b><br><br>
        <div class="step"><div class="step-num">1</div><div><b>인구가중 평균 거리 (35%)</b><br>주거지역 격자점에서 가장 가까운 문화시설까지의 거리를 인구 비율로 가중 평균. 멀수록 낮음</div></div>
        <div class="step"><div class="step-num">2</div><div><b>격자평균 1km 내 시설 수 (30%)</b><br>각 격자점 반경 1km 안 문화시설 수를 인구가중 평균. 많을수록 높음</div></div>
        <div class="step"><div class="step-num">3</div><div><b>면적당 시설 밀도 (20%)</b><br>행정동 면적(km²) 대비 문화시설 수</div></div>
        <div class="step"><div class="step-num">4</div><div><b>만명당 시설 수 (15%)</b><br>인구 1만명당 문화시설 수</div></div>
        <br>→ 4개 지표를 서울 425개 행정동 기준 백분위 정규화 후 가중 합산
      </div>
    </div>
  </div>

  <!-- 패널 1: 대중교통 접근성 -->
  <div id="p1" style="display:none">
    <div class="sec">
      <h3>레이어 선택</h3>
      <label class="tog on" id="p1-choro" style="--c:#6366f1" onclick="p1.toggleChoro(this)">
        <div class="tknob"></div><span class="tlbl">교통접근성 단계구분도</span>
      </label>
      <label class="tog on" id="p1-labels" style="--c:#64748b" onclick="p1.toggleLabels(this)">
        <div class="tknob"></div><span class="tlbl">지역명 표시</span>
      </label>
      <label class="tog on" id="p1-bus"   style="--c:#16a34a" onclick="p1.toggleBus(this)">
        <div class="tknob"></div><span class="tlbl">버스정류장</span><span class="tcnt">11,237</span>
      </label>
      <label class="tog on" id="p1-metro" style="--c:#ca8a04" onclick="p1.toggleMetro(this)">
        <div class="tknob"></div><span class="tlbl">지하철역</span><span class="tcnt">{metro_count}</span>
      </label>
    </div>
    <div class="sec">
      <h3>범례</h3>
      <div style="display:flex;align-items:center;gap:7px;margin-bottom:8px;font-size:11px;color:#4a6a8a">
        <div style="width:9px;height:9px;border-radius:50%;background:#16a34a;flex-shrink:0"></div>버스정류장
        <div style="width:9px;height:9px;border-radius:50%;background:#ca8a04;border:2px solid #78350f;margin-left:10px;flex-shrink:0"></div>지하철역
      </div>
      <div class="grade-row"><div class="grade-box" style="background:transparent;border:1px dashed #bbb"></div>상위 20% — 표시 없음</div>
      <div class="grade-row"><div class="grade-box" style="background:#fca5a5"></div>20~40% — 연분홍</div>
      <div class="grade-row"><div class="grade-box" style="background:#f87171"></div>40~60% — 분홍</div>
      <div class="grade-row"><div class="grade-box" style="background:#ef4444"></div>60~80% — 빨강</div>
      <div class="grade-row"><div class="grade-box" style="background:#991b1b"></div>하위 20% — 진빨강</div>
    </div>
    <div class="sec">
      <h3>교통접근성 점수 산출 방식</h3>
      <div class="note">
        <b>📐 3가지 지표 가중 합산</b><br><br>
        <div class="step"><div class="step-num">1</div><div><b>인구가중 평균 거리 (40%)</b><br>주거지역 격자점에서 가장 가까운 버스·지하철까지의 거리를 인구 비율로 가중 평균. 멀수록 낮음</div></div>
        <div class="step"><div class="step-num">2</div><div><b>격자평균 1km 내 시설 수 (40%)</b><br>각 격자점 반경 1km 안 버스+지하철 합산 수를 인구가중 평균</div></div>
        <div class="step"><div class="step-num">3</div><div><b>면적당 교통 밀도 (20%)</b><br>행정동 면적(km²) 대비 대중교통 시설 수</div></div>
        <br>→ 3개 지표를 서울 425개 행정동 기준 백분위 정규화 후 가중 합산
      </div>
    </div>
  </div>

  <!-- 패널 2: 문화시설 사각지대 -->
  <div id="p2" style="display:none">
    <div class="sec">
      <h3>레이어 선택</h3>
      <label class="tog on" id="p2-labels" style="--c:#64748b" onclick="p2.toggleLabels(this)">
        <div class="tknob"></div><span class="tlbl">지역명 표시</span>
      </label>
      <label class="tog on" id="p2-blind"  style="--c:#ea580c" onclick="p2.toggleBlind(this)">
        <div class="tknob"></div><span class="tlbl">⚠️ 사각지대 강조</span>
      </label>
      <label class="tog" id="p2-pts"   style="--c:#3b82f6" onclick="p2.toggleOvPts(this)">
        <div class="tknob"></div><span class="tlbl">문화시설 점 표시</span>
      </label>
      <label class="tog" id="p2-bus"   style="--c:#16a34a" onclick="p2.toggleOvBus(this)">
        <div class="tknob"></div><span class="tlbl">버스정류장 점 표시</span>
      </label>
      <label class="tog" id="p2-metro" style="--c:#ca8a04" onclick="p2.toggleOvMetro(this)">
        <div class="tknob"></div><span class="tlbl">지하철역 점 표시</span>
      </label>
    </div>
    <div class="sec">
      <h3>사각지대 단계 범례</h3>
      <div class="grade-row"><div class="grade-box" style="background:#fde68a;border:1px solid #d97706"></div>1단계 — 하위 20~30% (주의)</div>
      <div class="grade-row"><div class="grade-box" style="background:#f97316;border:1px solid #ea580c"></div>2단계 — 하위 10~20% (경고)</div>
      <div class="grade-row"><div class="grade-box" style="background:#dc2626;border:1px solid #b91c1c"></div>3단계 — 하위 0~10% (심각)</div>
    </div>
    <div class="sec">
      <h3>사각지대 선정 방식</h3>
      <div class="note">
        <b>📐 종합 점수 기반 단계 분류</b><br><br>
        <div class="step"><div class="step-num">1</div><div><b>종합 점수 산출</b><br>문화접근성 + 교통접근성 평균</div></div>
        <div class="step"><div class="step-num">2</div><div><b>전체 순위 산출</b><br>425개 행정동 기준 백분위 순위</div></div>
        <div class="step"><div class="step-num">3</div><div><b>3단계 분류</b><br>
          하위 0~10% → <b style="color:#b91c1c">3단계(심각)</b><br>
          하위 10~20% → <b style="color:#ea580c">2단계(경고)</b><br>
          하위 20~30% → <b style="color:#d97706">1단계(주의)</b>
        </div></div>
        <br>총 {blind_total}개 행정동 (전체의 30%)
      </div>
    </div>
    <div class="sec">
      <h3>사각지대 목록 ({blind_total}개)</h3>
      <div style="font-size:10px;color:#6a8aaa;margin-bottom:8px">
        🔴 3단계 {blind_3}개 &nbsp; 🟠 2단계 {blind_2}개 &nbsp; 🟡 1단계 {blind_1}개
      </div>
      <div id="blind-list"></div>
    </div>
  </div>

</div>
<div id="map"></div>
</div>

<script>
// ── 데이터 ──
const GU      = {gu_js};
const DONG    = {dong_js};
const CULTURE = {culture_js};
const BUS     = {bus_js};
const METRO   = {metro_js};

// ════════ 표지 ↔ 지도 전환 ════════
function enterSite(tabIdx) {{
  var cover = document.getElementById('cover-page');
  cover.classList.add('hidden');
  setTimeout(function() {{
    cover.style.display = 'none';
    document.getElementById('back-to-cover-btn').style.display = 'block';
    if (tabIdx >= 0 && typeof switchTab === 'function') switchTab(tabIdx);
  }}, 600);
}}
function backToCover() {{
  var cover = document.getElementById('cover-page');
  cover.style.display = 'flex';
  setTimeout(function() {{ cover.classList.remove('hidden'); }}, 10);
  document.getElementById('back-to-cover-btn').style.display = 'none';
}}

// ════════ 지도 초기화 ════════
const SEOUL_BOUNDS = L.latLngBounds([37.413,126.734],[37.715,127.269]);
const map = L.map('map', {{
  center:[37.555,126.980], zoom:11, minZoom:11, maxZoom:18,
  maxBounds:SEOUL_BOUNDS, maxBoundsViscosity:0.85, zoomControl:false
}});
L.control.zoom({{position:'topright'}}).addTo(map);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/light_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution:'© OpenStreetMap © CARTO', maxZoom:19
}}).addTo(map);

// ── 유틸 ──
function zStep() {{ return map.getZoom() <= 11 ? 'gu' : 'dong'; }}
function dotSize(base) {{
  var z = map.getZoom();
  var t = {{11:1,12:1.6,13:2.5,14:3.5,15:5,16:6,17:7,18:8}};
  return Math.max(2, Math.round(base * (t[Math.min(z,18)] || 8)));
}}
function uniColor(s) {{
  if(s>=0.8) return {{f:'transparent',o:0}};
  if(s>=0.6) return {{f:'#fca5a5',o:0.40}};
  if(s>=0.4) return {{f:'#f87171',o:0.45}};
  if(s>=0.2) return {{f:'#ef4444',o:0.50}};
  return {{f:'#991b1b',o:0.55}};
}}
function blindColor(rank) {{
  if(rank===1) return {{f:'#fde68a',o:0.65,stroke:'#d97706',sw:1.5}};
  if(rank===2) return {{f:'#f97316',o:0.65,stroke:'#ea580c',sw:2}};
  if(rank===3) return {{f:'#dc2626',o:0.70,stroke:'#b91c1c',sw:2.5}};
  return {{f:'transparent',o:0,stroke:'#ccc',sw:0.5}};
}}

// ── 팝업 ──
function guPopup(g) {{
  var cb=Math.round(g.culture_score*100), tb=Math.round(g.transit_score*100),
      cs=Math.round((g.culture_score+g.transit_score)/2*100);
  return '<div class="ptitle">'+g.name+'</div>'+
    '<div class="abar"><div class="al"><span>문화접근성</span><span>'+cb+'점</span></div>'+
    '<div class="atrack"><div class="afill" style="width:'+cb+'%;background:#ef4444"></div></div></div>'+
    '<div class="abar"><div class="al"><span>교통접근성</span><span>'+tb+'점</span></div>'+
    '<div class="atrack"><div class="afill" style="width:'+tb+'%;background:#ef4444"></div></div></div>'+
    '<div class="abar"><div class="al"><span>종합점수</span><span>'+cs+'점</span></div>'+
    '<div class="atrack"><div class="afill" style="width:'+cs+'%;background:#6366f1"></div></div></div>'+
    '<div class="prow">👥 인구 <span>'+g.pop.toLocaleString()+'명</span></div>'+
    '<div class="prow">⚠️ 사각지대 행정동 <span>'+g.blind_count+'개</span></div>';
}}
function dongPopup(d) {{
  var cb=Math.round(d.culture_score*100), tb=Math.round(d.transit_score*100),
      cs=Math.round(d.combined_score*100), rp=Math.round(d.combined_rank*100);
  var bh='';
  if(d.blind){{
    var rc={{1:'#d97706',2:'#ea580c',3:'#b91c1c'}};
    var rn={{1:'1단계(주의)',2:'2단계(경고)',3:'3단계(심각)'}};
    bh='<div style="margin-top:6px;padding:4px 8px;background:rgba(234,88,12,.10);'+
       'border-radius:5px;font-size:11px;color:'+rc[d.blind_rank]+'">⚠️ 사각지대 '+rn[d.blind_rank]+' (하위 '+rp+'%)</div>';
  }}
  return '<div class="ptitle">'+d.gu+' '+d.name+'</div>'+
    '<div class="abar"><div class="al"><span>문화접근성</span><span>'+cb+'점</span></div>'+
    '<div class="atrack"><div class="afill" style="width:'+cb+'%;background:#ef4444"></div></div></div>'+
    '<div class="abar"><div class="al"><span>교통접근성</span><span>'+tb+'점</span></div>'+
    '<div class="atrack"><div class="afill" style="width:'+tb+'%;background:#ef4444"></div></div></div>'+
    '<div class="abar"><div class="al"><span>종합점수</span><span>'+cs+'점 (하위 '+rp+'%)</span></div>'+
    '<div class="atrack"><div class="afill" style="width:'+cs+'%;background:#6366f1"></div></div></div>'+
    '<div class="prow">🏛️ 인구가중 1km 내 문화시설 <span>'+d.culture_1km+'개</span></div>'+
    '<div class="prow">🚌 인구가중 1km 내 대중교통 <span>'+d.transit_1km+'개</span></div>'+
    '<div class="prow">📏 인구가중 문화시설 거리 <span>'+d.culture_dist+'km</span></div>'+
    '<div class="prow">🏘️ 주거지역 비율 <span>'+(d.residential*100).toFixed(0)+'%</span></div>'+
    '<div class="prow">👥 인구 <span>'+d.pop.toLocaleString()+'명</span> · 면적 <span>'+d.area+'km²</span></div>'+bh;
}}

// ── 도형 유틸 ──
function mkPoly(coords,fill,fillOp,stroke,w) {{
  var ll=coords[0].map(function(c){{return[c[1],c[0]];}});
  return L.polygon(ll,{{fillColor:fill,fillOpacity:fillOp,color:stroke||'#9a9ab0',weight:w||1,opacity:1}});
}}
function mkGuLabel(text) {{
  return L.divIcon({{className:'map-label',
    html:'<div style="font-size:12px;font-weight:700;color:#1a3a5a;'+
         'text-shadow:1px 1px 2px rgba(255,255,255,.9),-1px -1px 2px rgba(255,255,255,.9);'+
         'white-space:nowrap;text-align:center;">'+text+'</div>',
    iconSize:[80,16],iconAnchor:[40,8]}});
}}

// ── 문화시설 유형별 SVG 아이콘 ──
function mkCultureIcon(type,size) {{
  var s=size,h=s/2,path='',color='#2563a8';
  if(type==='도서관') {{
    color='#e11d48';
    path='<path d="M'+h+' '+(s*.82)+' C'+h+' '+(s*.82)+' '+(s*.1)+' '+(s*.52)+
         ' '+(s*.1)+' '+(s*.36)+' C'+(s*.1)+' '+(s*.14)+' '+h+' '+(s*.14)+
         ' '+h+' '+(s*.36)+' C'+h+' '+(s*.14)+' '+(s*.9)+' '+(s*.14)+
         ' '+(s*.9)+' '+(s*.36)+' C'+(s*.9)+' '+(s*.52)+' '+h+' '+(s*.82)+
         ' '+h+' '+(s*.82)+'Z" fill="'+color+'" stroke="white" stroke-width="1"/>';
  }} else if(type==='미술관/갤러리') {{
    color='#7c3aed';
    path='<polygon points="'+h+','+(s*.1)+' '+(s*.9)+','+h+' '+h+','+(s*.9)+
         ' '+(s*.1)+','+h+'" fill="'+color+'" stroke="white" stroke-width="1"/>';
  }} else if(type==='박물관/기념관') {{
    color='#059669';
    var r=s*.22;
    path='<circle cx="'+h+'" cy="'+(h-r)+'" r="'+r+'" fill="'+color+'" stroke="white" stroke-width="0.5"/>'+
         '<circle cx="'+(h+r)+'" cy="'+h+'" r="'+r+'" fill="'+color+'" stroke="white" stroke-width="0.5"/>'+
         '<circle cx="'+h+'" cy="'+(h+r)+'" r="'+r+'" fill="'+color+'" stroke="white" stroke-width="0.5"/>'+
         '<circle cx="'+(h-r)+'" cy="'+h+'" r="'+r+'" fill="'+color+'" stroke="white" stroke-width="0.5"/>'+
         '<circle cx="'+h+'" cy="'+h+'" r="'+(r*.6)+'" fill="'+color+'"/>';
  }} else if(type==='공연장') {{
    color='#d97706';
    var pts=[],R=s*.42,r2=s*.18;
    for(var i=0;i<10;i++){{
      var ang=(i*36-90)*Math.PI/180,ri=i%2===0?R:r2;
      pts.push((h+ri*Math.cos(ang)).toFixed(2)+','+(h+ri*Math.sin(ang)).toFixed(2));
    }}
    path='<polygon points="'+pts.join(' ')+'" fill="'+color+'" stroke="white" stroke-width="1"/>';
  }} else {{
    color='#0369a1';
    path='<circle cx="'+h+'" cy="'+h+'" r="'+(s*.38)+'" fill="'+color+'" stroke="white" stroke-width="1"/>';
  }}
  return L.divIcon({{className:'cul-icon',
    html:'<svg xmlns="http://www.w3.org/2000/svg" width="'+s+'" height="'+s+'" viewBox="0 0 '+s+' '+s+'">'+path+'</svg>',
    iconSize:[s,s],iconAnchor:[h,h]}});
}}
function getTypeKey(t) {{
  if(t==='도서관') return '도서관';
  if(t==='미술관/갤러리') return '미술관/갤러리';
  if(t==='박물관/기념관') return '박물관/기념관';
  if(t==='공연장') return '공연장';
  return '기타';
}}

// ════════ 탭 0: 문화시설 접근성 ════════
var p0=(function(){{
  var LG={{
    choro_gu:L.layerGroup(), choro_dong:L.layerGroup(), label_gu:L.layerGroup(),
    lib:L.layerGroup(), art:L.layerGroup(), mus:L.layerGroup(),
    perf:L.layerGroup(), etc:L.layerGroup()
  }};
  var showChoro=true,showLabels=true;
  var showLayer={{'도서관':true,'미술관/갤러리':true,'박물관/기념관':true,'공연장':true,'기타':true}};
  var typeToLG={{'도서관':'lib','미술관/갤러리':'art','박물관/기념관':'mus','공연장':'perf','기타':'etc'}};

  function applyChoro(){{
    map.removeLayer(LG.choro_gu);map.removeLayer(LG.choro_dong);
    if(!showChoro)return;
    zStep()==='gu'?map.addLayer(LG.choro_gu):map.addLayer(LG.choro_dong);
  }}
  function applyLabels(){{map.removeLayer(LG.label_gu);if(showLabels)map.addLayer(LG.label_gu);}}
  function applyDots(){{
    var sz=dotSize(10);
    Object.keys(typeToLG).forEach(function(type){{
      LG[typeToLG[type]].eachLayer(function(m){{m.setIcon(mkCultureIcon(type,sz));}});
    }});
  }}
  return{{
    build:function(){{
      GU.forEach(function(g){{
        var c=uniColor(g.culture_score);
        mkPoly(g.coords,c.f,c.o,'#9a9ab0',1.2).bindPopup(guPopup(g),{{maxWidth:270}}).addTo(LG.choro_gu);
        L.marker([g.lat,g.lon],{{icon:mkGuLabel(g.name),interactive:false,zIndexOffset:200}}).addTo(LG.label_gu);
      }});
      DONG.forEach(function(d){{
        var c=uniColor(d.culture_score);
        mkPoly(d.coords,c.f,c.o,'#9a9ab0',0.6)
          .bindPopup(dongPopup(d),{{maxWidth:290}})
          .bindTooltip('<b>'+d.gu+' '+d.name+'</b>',{{sticky:true,className:'dong-tooltip',opacity:0.9}})
          .addTo(LG.choro_dong);
      }});
      CULTURE.forEach(function(d){{
        var tk=getTypeKey(d.주제분류);
        var m=L.marker([d.위도,d.경도],{{icon:mkCultureIcon(tk,10),pane:'markerPane',zIndexOffset:500}});
        m.bindPopup('<div class="ptitle">'+d.문화시설명+'</div>'+
          '<span class="ptag" style="background:rgba(59,130,246,.12);color:#1a4abf">'+d.주제분류+'</span>'+
          '<div class="prow">📍 <span>'+(d.주소||d.자치구)+'</span></div>',{{maxWidth:240}});
        m.addTo(LG[typeToLG[tk]]);
      }});
    }},
    enter:function(){{
      applyChoro();applyLabels();applyDots();
      Object.keys(typeToLG).forEach(function(type){{
        if(showLayer[type])map.addLayer(LG[typeToLG[type]]);
      }});
    }},
    exit:function(){{Object.values(LG).forEach(function(lg){{map.removeLayer(lg);}});}},
    onZoom:function(){{applyChoro();applyLabels();applyDots();}},
    toggleChoro:function(el){{el.classList.toggle('on');showChoro=el.classList.contains('on');applyChoro();}},
    toggleLabels:function(el){{el.classList.toggle('on');showLabels=el.classList.contains('on');applyLabels();}},
    toggleLayer:function(type,el){{
      el.classList.toggle('on');showLayer[type]=el.classList.contains('on');
      showLayer[type]?map.addLayer(LG[typeToLG[type]]):map.removeLayer(LG[typeToLG[type]]);
    }}
  }};
}})();

// ════════ 탭 1: 대중교통 접근성 ════════
var p1=(function(){{
  var LG={{choro_gu:L.layerGroup(),choro_dong:L.layerGroup(),
           bus:L.layerGroup(),metro:L.layerGroup(),label_gu:L.layerGroup()}};
  var showChoro=true,showLabels=true,showBus=true,showMetro=true;
  function applyChoro(){{
    map.removeLayer(LG.choro_gu);map.removeLayer(LG.choro_dong);
    if(!showChoro)return;
    zStep()==='gu'?map.addLayer(LG.choro_gu):map.addLayer(LG.choro_dong);
  }}
  function applyLabels(){{map.removeLayer(LG.label_gu);if(showLabels)map.addLayer(LG.label_gu);}}
  function applyDots(){{
    var bs=dotSize(2),ms=dotSize(5);
    LG.bus.eachLayer(function(m){{m.setStyle({{radius:bs}});}});
    LG.metro.eachLayer(function(m){{m.setStyle({{radius:ms}});}});
  }}
  return{{
    build:function(){{
      GU.forEach(function(g){{
        var c=uniColor(g.transit_score);
        mkPoly(g.coords,c.f,c.o,'#9a9ab0',1.2).bindPopup(guPopup(g),{{maxWidth:270}}).addTo(LG.choro_gu);
        L.marker([g.lat,g.lon],{{icon:mkGuLabel(g.name),interactive:false,zIndexOffset:200}}).addTo(LG.label_gu);
      }});
      DONG.forEach(function(d){{
        var c=uniColor(d.transit_score);
        mkPoly(d.coords,c.f,c.o,'#9a9ab0',0.6)
          .bindPopup(dongPopup(d),{{maxWidth:290}})
          .bindTooltip('<b>'+d.gu+' '+d.name+'</b>',{{sticky:true,className:'dong-tooltip',opacity:0.9}})
          .addTo(LG.choro_dong);
      }});
      BUS.forEach(function(d){{
        L.circleMarker([d.위도,d.경도],{{radius:2,fillColor:'#16a34a',color:'none',
          fillOpacity:.70,weight:0,pane:'markerPane'}})
         .bindPopup('<div class="ptitle">'+d.정류소명+'</div><div class="prow">🚌 버스정류장</div>',{{maxWidth:160}})
         .addTo(LG.bus);
      }});
      METRO.forEach(function(d){{
        L.circleMarker([d.위도,d.경도],{{radius:5,fillColor:'#ca8a04',color:'#78350f',
          fillOpacity:.9,weight:1.5,pane:'markerPane'}})
         .bindPopup('<div class="ptitle">'+d.역사명+'역</div><div class="prow">🚇 <span>'+d.호선+'</span></div>',{{maxWidth:180}})
         .addTo(LG.metro);
      }});
    }},
    enter:function(){{
      applyChoro();
      if(showBus)map.addLayer(LG.bus);     // 버스 먼저 (지하철이 위에 오도록)
      if(showMetro)map.addLayer(LG.metro);
      applyLabels();applyDots();
    }},
    exit:function(){{Object.values(LG).forEach(function(lg){{map.removeLayer(lg);}});}},
    onZoom:function(){{applyChoro();applyLabels();applyDots();}},
    toggleChoro:function(el){{el.classList.toggle('on');showChoro=el.classList.contains('on');applyChoro();}},
    toggleLabels:function(el){{el.classList.toggle('on');showLabels=el.classList.contains('on');applyLabels();}},
    toggleBus:function(el){{
      el.classList.toggle('on');showBus=el.classList.contains('on');
      // 버스 토글 시 순서 보장: 버스 제거→재추가→지하철 재추가
      map.removeLayer(LG.bus);map.removeLayer(LG.metro);
      if(showBus)map.addLayer(LG.bus);
      if(showMetro)map.addLayer(LG.metro);
    }},
    toggleMetro:function(el){{
      el.classList.toggle('on');showMetro=el.classList.contains('on');
      showMetro?map.addLayer(LG.metro):map.removeLayer(LG.metro);
    }}
  }};
}})();

// ════════ 탭 2: 문화시설 사각지대 ════════
var p2=(function(){{
  var LG={{bg_gu:L.layerGroup(),bg_dong:L.layerGroup(),blind:L.layerGroup(),
           ov_pts:L.layerGroup(),ov_bus:L.layerGroup(),ov_metro:L.layerGroup(),
           label_gu:L.layerGroup()}};
  var showLabels=true,showBlind=true,showOvPts=false,showOvBus=false,showOvMetro=false;
  function applyBg(){{
    map.removeLayer(LG.bg_gu);map.removeLayer(LG.bg_dong);
    zStep()==='gu'?map.addLayer(LG.bg_gu):map.addLayer(LG.bg_dong);
  }}
  function applyLabels(){{map.removeLayer(LG.label_gu);if(showLabels)map.addLayer(LG.label_gu);}}
  function applyDots(){{
    LG.ov_pts.eachLayer(function(m){{if(m._typeKey)m.setIcon(mkCultureIcon(m._typeKey,dotSize(10)));}});
    var bs=dotSize(2),ms=dotSize(5);
    LG.ov_bus.eachLayer(function(m){{m.setStyle({{radius:bs}});}});
    LG.ov_metro.eachLayer(function(m){{m.setStyle({{radius:ms}});}});
  }}
  return{{
    build:function(){{
      GU.forEach(function(g){{
        mkPoly(g.coords,'#e8f0f8',0.40,'#3a6a9a',1.5).bindPopup(guPopup(g),{{maxWidth:270}}).addTo(LG.bg_gu);
        L.marker([g.lat,g.lon],{{icon:mkGuLabel(g.name),interactive:false,zIndexOffset:200}}).addTo(LG.label_gu);
      }});
      DONG.forEach(function(d){{
        mkPoly(d.coords,'#f0f5fa',0.30,'#6a9aba',0.6)
          .bindPopup(dongPopup(d),{{maxWidth:290}})
          .bindTooltip('<b>'+d.gu+' '+d.name+'</b>',{{sticky:true,className:'dong-tooltip',opacity:0.9}})
          .addTo(LG.bg_dong);
      }});
      DONG.filter(function(d){{return d.blind;}}).forEach(function(d){{
        var bc=blindColor(d.blind_rank);
        mkPoly(d.coords,bc.f,bc.o,bc.stroke,bc.sw)
          .bindPopup(dongPopup(d),{{maxWidth:290}})
          .bindTooltip('<b>⚠️ '+d.gu+' '+d.name+' ('+d.blind_rank+'단계)</b>',{{sticky:true,className:'dong-tooltip',opacity:0.9}})
          .addTo(LG.blind);
      }});
      CULTURE.forEach(function(d){{
        var tk=getTypeKey(d.주제분류);
        var m=L.marker([d.위도,d.경도],{{icon:mkCultureIcon(tk,10),pane:'markerPane',zIndexOffset:500}});
        m.bindPopup('<div class="ptitle">'+d.문화시설명+'</div>'+
          '<span class="ptag" style="background:rgba(59,130,246,.12);color:#1a4abf">'+d.주제분류+'</span>'+
          '<div class="prow">📍 <span>'+(d.주소||d.자치구)+'</span></div>',{{maxWidth:240}});
        m._typeKey=tk; m.addTo(LG.ov_pts);
      }});
      BUS.forEach(function(d){{
        L.circleMarker([d.위도,d.경도],{{radius:2,fillColor:'#16a34a',color:'none',
          fillOpacity:.60,weight:0,pane:'markerPane'}})
         .bindPopup('<div class="ptitle">'+d.정류소명+'</div><div class="prow">🚌 버스정류장</div>',{{maxWidth:160}})
         .addTo(LG.ov_bus);
      }});
      METRO.forEach(function(d){{
        L.circleMarker([d.위도,d.경도],{{radius:5,fillColor:'#ca8a04',color:'#78350f',
          fillOpacity:.85,weight:1.5,pane:'markerPane'}})
         .bindPopup('<div class="ptitle">'+d.역사명+'역</div><div class="prow">🚇 <span>'+d.호선+'</span></div>',{{maxWidth:180}})
         .addTo(LG.ov_metro);
      }});
      // 사각지대 목록 렌더링
      var cont=document.getElementById('blind-list');
      var rc={{1:'#d97706',2:'#ea580c',3:'#b91c1c'}};
      var rn={{1:'🟡 1단계',2:'🟠 2단계',3:'🔴 3단계'}};
      var html='';
      var blinds=DONG.filter(function(d){{return d.blind;}});
      blinds.sort(function(a,b){{return b.blind_rank-a.blind_rank||a.gu.localeCompare(b.gu);}});
      blinds.forEach(function(d){{
        html+='<div class="bsi" onclick="map.setView(['+d.lat+','+d.lon+'],15)"'+
          ' style="border-color:'+rc[d.blind_rank]+'50;background:'+rc[d.blind_rank]+'12">'+
          '<div class="bn" style="color:'+rc[d.blind_rank]+'">'+rn[d.blind_rank]+' '+d.gu+' '+d.name+'</div>'+
          '<div class="bd">문화 '+Math.round(d.culture_score*100)+'점 · 교통 '+
          Math.round(d.transit_score*100)+'점 · 인구 '+d.pop.toLocaleString()+'명</div></div>';
      }});
      cont.innerHTML=html;
    }},
    enter:function(){{
      applyBg();applyLabels();
      if(showBlind)map.addLayer(LG.blind);
      if(showOvPts)map.addLayer(LG.ov_pts);
      if(showOvBus)map.addLayer(LG.ov_bus);
      if(showOvMetro)map.addLayer(LG.ov_metro);
      applyDots();
    }},
    exit:function(){{Object.values(LG).forEach(function(lg){{map.removeLayer(lg);}});}},
    onZoom:function(){{applyBg();applyLabels();applyDots();}},
    toggleLabels:function(el){{el.classList.toggle('on');showLabels=el.classList.contains('on');applyLabels();}},
    toggleBlind:function(el){{el.classList.toggle('on');showBlind=el.classList.contains('on');showBlind?map.addLayer(LG.blind):map.removeLayer(LG.blind);}},
    toggleOvPts:function(el){{el.classList.toggle('on');showOvPts=el.classList.contains('on');showOvPts?map.addLayer(LG.ov_pts):map.removeLayer(LG.ov_pts);}},
    toggleOvBus:function(el){{
      el.classList.toggle('on');showOvBus=el.classList.contains('on');
      map.removeLayer(LG.ov_bus);map.removeLayer(LG.ov_metro);
      if(showOvBus)map.addLayer(LG.ov_bus);
      if(showOvMetro)map.addLayer(LG.ov_metro);
    }},
    toggleOvMetro:function(el){{el.classList.toggle('on');showOvMetro=el.classList.contains('on');showOvMetro?map.addLayer(LG.ov_metro):map.removeLayer(LG.ov_metro);}}
  }};
}})();

// ════════ 탭 전환 ════════
var TABS=[p0,p1,p2]; var curTab=0;
function switchTab(idx){{
  TABS[curTab].exit(); curTab=idx;
  for(var i=0;i<3;i++){{
    document.getElementById('p'+i).style.display=i===idx?'':'none';
    document.getElementById('tab'+i).classList.toggle('on',i===idx);
  }}
  TABS[curTab].enter();
}}
map.on('zoomend',function(){{TABS[curTab].onZoom();}});
p0.build(); p1.build(); p2.build();
TABS[0].enter();
</script>
</body>
</html>'''

# ============================================================
# STEP 3: 파일 저장
# ============================================================
output_path = 'seoul_map_v22.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ 저장 완료: {output_path}")
print(f"   파일 크기: {len(html)/1024:.0f} KB")
