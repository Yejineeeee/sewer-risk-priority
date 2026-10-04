# 통합 대시보드 v3 — 사이드바 레이아웃 + 인디고 무드 (레퍼런스 분위기 적용)
# 데이터는 survey_priority.html / budget_sim.html 의 내장 JSON 재사용
import os, re

PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"

def grab(path, var):
    t = open(os.path.join(PROJ, path), encoding="utf-8").read()
    m = re.search(r"const " + var + r" = (\[.*?\]);", t, re.S)
    return m.group(1)

ROWS = grab("survey_priority.html", "ROWS")
SEGS = grab("budget_sim.html", "SEGS")

html = r"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>하수관 보수 의사결정 대시보드</title>
<style>
:root{
  --primary:#5A67D8; --primary-weak:#E9EBFB; --primary-ink:#4553C8;
  --ink:#1B2559; --body:#3d4468; --muted:#6B7280; --faint:#9aa3af;
  --red:#D73027; --redbg:#FBEAE8; --blue:#2166AC; --bluebg:#E9F0F8;
  --green:#3B7A3B; --greenbg:#E8F1E8;
  --side:#F7F8FC; --card:#ffffff; --line:#edf0f4; --hover:#F7F8FC;
}
*{box-sizing:border-box}
body{font-family:'Segoe UI','Malgun Gothic',sans-serif;margin:0;background:#fff;color:var(--body)}
.app{display:flex;min-height:100vh}

/* ── 사이드바 ── */
.sidebar{width:284px;flex-shrink:0;background:var(--side);padding:22px 16px;
  display:flex;flex-direction:column;gap:4px;border-right:1px solid var(--line)}
.logo{display:flex;align-items:center;gap:9px;padding:4px 10px 18px}
.logo .mark{width:26px;height:26px;border-radius:8px;background:var(--primary);
  color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center}
.logo .name{font-size:13.5px;font-weight:700;color:var(--ink);line-height:1.25}
.navlabel{font-size:10.5px;letter-spacing:1.2px;color:var(--faint);padding:14px 10px 6px}
.navitem{display:flex;align-items:center;gap:9px;padding:11px 13px;border-radius:10px;
  font-size:14px;color:var(--muted);cursor:pointer;border:none;background:none;
  text-align:left;width:100%;font-family:inherit;text-decoration:none;white-space:nowrap}
.navitem:hover{background:#eef0f8}
.navitem.on{background:var(--primary-weak);color:var(--primary-ink);font-weight:600}
.navitem .ico{width:16px;text-align:center;font-size:13px;opacity:0.75}
.navitem .bdg{margin-left:auto;font-size:9.5px;padding:2px 7px;border-radius:8px;font-weight:600}
.bdg.real{background:var(--greenbg);color:var(--green)} .bdg.sim{background:#ECEEF3;color:var(--muted)}
.sidefoot{margin-top:auto;padding:10px;font-size:10.5px;color:var(--faint);line-height:1.6}

/* ── 본문 ── */
.main{flex:1;padding:30px 38px;max-width:1080px}
h1{font-size:26px;color:var(--ink);margin:0 0 5px;letter-spacing:-0.4px}
.sub{color:var(--muted);font-size:13px;margin-bottom:26px}
.pane{display:none} .pane.on{display:block}
.filters{display:flex;gap:14px;align-items:center;flex-wrap:wrap;margin-bottom:18px}
.filters label{font-size:12.5px;color:var(--muted)}
select{font:13px 'Segoe UI','Malgun Gothic';padding:7px 10px;border:1px solid var(--line);
  border-radius:8px;background:var(--card);color:var(--ink)}
.btn{margin-left:auto;font:600 12.5px 'Segoe UI','Malgun Gothic';padding:9px 16px;border:none;
  border-radius:8px;background:var(--primary);color:#fff;cursor:pointer}
.btn:hover{background:var(--primary-ink)}
.tiles{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:20px}
.tile{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 20px}
.tile .l{font-size:12px;color:var(--muted)}
.tile .v{font-size:27px;font-weight:700;letter-spacing:-0.5px;color:var(--ink);margin-top:3px}
.tile.acc .v{color:var(--red)} .tile.fld .v{color:var(--blue)}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:18px}
.cardtitle{font-size:13px;font-weight:600;color:var(--ink);margin-bottom:4px}
.legend{display:flex;gap:16px;font-size:11.5px;color:var(--muted);margin-bottom:8px}
.legend .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px;vertical-align:0.5px}
table{border-collapse:collapse;font-size:13px;width:100%}
th{font-size:11px;color:var(--faint);font-weight:600;border-bottom:1px solid var(--line);
  padding:8px 10px;text-align:left;background:var(--card);position:sticky;top:0}
td{border-bottom:1px solid #f4f6f9;padding:8px 10px}
tr:hover td{background:var(--hover)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:2px 9px;border-radius:10px;font-size:11px;font-weight:600;margin-right:4px}
.tag.acc{background:var(--redbg);color:var(--red)} .tag.fld{background:var(--bluebg);color:var(--blue)}
.sliderrow{display:flex;gap:16px;align-items:center;margin-bottom:18px}
.sliderrow input[type=range]{flex:1;accent-color:var(--primary)}
.sliderrow .bv{font-size:15px;font-weight:700;min-width:86px;color:var(--primary-ink)}
.chartwrap{position:relative}
canvas{width:100%;height:auto;display:block}
.tooltip{position:absolute;pointer-events:none;background:#2B3157;color:#fff;
  font-size:11.5px;padding:7px 11px;border-radius:8px;line-height:1.55;display:none;white-space:nowrap;z-index:5}
.note{color:var(--faint);font-size:11px;margin-top:12px;line-height:1.7}
a.maplink{color:var(--body);text-decoration:none}
a.maplink:hover{color:var(--primary-ink);text-decoration:underline}
a.maplink .pin{font-size:10.5px;opacity:0.4}
a.maplink:hover .pin{opacity:1}
</style></head><body>
<div class="app">

<nav class="sidebar">
 <div class="logo"><div class="mark">下</div><div class="name">하수관 보수<br>의사결정 대시보드</div></div>
 <div class="navlabel">추천</div>
 <button class="navitem on" id="navA" onclick="showPane('A')"><span class="ico">▤</span>조사 우선순위<span class="bdg real">실데이터</span></button>
 <button class="navitem" id="navB" onclick="showPane('B')"><span class="ico">◔</span>예산 시뮬레이션<span class="bdg sim">가상 시연</span></button>
 <div class="navlabel">바로가기</div>
 <a class="navitem" href="map_prototype.html" target="_blank"><span class="ico">◎</span>위험 지도 열기</a>
 <button class="navitem" onclick="downloadCsv()"><span class="ico">⬇</span>CSV 내보내기</button>
 <div class="sidefoot">데이터: 국토부 지반침하 사고정보 · 서울시 침수흔적도 · 서울시 포트홀 보수 이력 · AI-Hub 하수관로 CCTV</div>
</nav>

<main class="main">
 <h1 id="pageTitle">조사 우선순위 추천</h1>
 <div class="sub" id="pageSub">3회 이상 반복 보수된 지점 6,447곳을 주변 침하사고/침수 이력과 결합해, 조사가 시급한 순서로 정렬한 목록 (100% 실데이터)</div>

 <!-- ── Pane A ── -->
 <div id="paneA" class="pane on">
  <div class="filters">
   <label>자치구 <select id="gu"></select></label>
   <label>표시 <select id="topn"><option>50</option><option>100</option><option selected>200</option><option value="99999">전체</option></select></label>
   <button class="btn" id="csv">CSV 다운로드</button>
  </div>
  <div class="tiles">
   <div class="tile"><div class="l">조사 후보 지점 (반복 보수 3회+)</div><div class="v" id="n">-</div></div>
   <div class="tile acc"><div class="l">250m 내 실제 침하사고 있음</div><div class="v" id="na">-</div></div>
   <div class="tile fld"><div class="l">침수 이력 인접 (100m)</div><div class="v" id="nf">-</div></div>
  </div>
  <div class="card" style="max-height:520px;overflow-y:auto;padding:0 20px">
   <table><thead><tr><th style="width:36px">#</th><th>주소 <span style="font-weight:400">(클릭 시 지도)</span></th><th class="num" style="width:90px">반복 보수</th><th style="width:230px">위험 신호</th></tr></thead>
   <tbody id="tb"></tbody></table>
  </div>
  <div class="note">우선순위 규칙: ① 250m 내 침하사고 유무 → ② 반복 보수 횟수 → ③ 침수 이력 인접 ·
근거: 사고 지점 250m 내 반복 보수 밀도 1.47배 (순열검정 p=0.0001) ·
번지 단위 집계로 대형 필지 대표 주소 가능성 있음 · 본 목록은 스크리닝 후보이며 현장 확인을 대체하지 않음</div>
 </div>

 <!-- ── Pane B ── -->
 <div id="paneB" class="pane">
  <div class="sliderrow">
   <label style="font-size:12.5px;color:var(--muted)">보수 예산</label>
   <input type="range" id="budget" min="0" max="200000" step="1000" value="30000">
   <span class="bv" id="budgetLabel"></span>
  </div>
  <div class="tiles">
   <div class="tile"><div class="l">위험 커버리지 (점수 체계 내)</div><div class="v" id="cov">-</div></div>
   <div class="tile"><div class="l">보수 가능 구간 (가상 275개 중)</div><div class="v" id="nseg">-</div></div>
   <div class="tile"><div class="l">집행 금액</div><div class="v" id="spent">-</div></div>
  </div>
  <div class="card">
   <div class="cardtitle">예산 → 위험 커버리지</div>
   <div class="legend">
    <span><span class="dot" style="background:#5A67D8"></span>위험/비용 효율 전략</span>
    <span><span class="dot" style="background:#c9cdd6"></span>단순 위험순 (참조)</span>
   </div>
   <div class="chartwrap">
    <canvas id="curve" width="960" height="300"></canvas>
    <div class="tooltip" id="tip"></div>
   </div>
  </div>
  <div class="card" style="padding:0 20px">
   <table><thead><tr><th style="width:36px">#</th><th>구간</th><th class="num">위험 합계</th><th class="num">싱크홀</th><th class="num">침수</th><th>공법(가정)</th><th class="num">비용</th></tr></thead>
   <tbody id="toplist"></tbody></table>
  </div>
  <div class="note">가상 보수 시나리오 기반 의사결정 지원 — 커버리지는 본 시스템 위험 점수 체계 내 지표이며 실제 사고 감소율이 아님 ·
단가 가정: 부분 교체 5,000만 / 비굴착 라이닝 2,000만 / 준설 500만 (구간당) · 구간은 공개 데이터셋 이미지의 가상 묶음</div>
 </div>
</main>
</div>

<script>
const ROWS = __ROWS__;
const SEGS = __SEGS__;

const TITLES = {
  A: ["조사 우선순위 추천", "3회 이상 반복 보수된 지점 6,447곳을 주변 침하사고/침수 이력과 결합해, 조사가 시급한 순서로 정렬한 목록 (100% 실데이터)"],
  B: ["보수 예산 시뮬레이션", "결함이 확인된 구간을 위험 점수 순으로 정렬해, 예산 안에서 보수 가능한 구간과 위험 해소율을 계산 (가상 구간 시연)"],
};
function showPane(w){
  for (const k of ['A','B']){
    document.getElementById('pane'+k).classList.toggle('on', k===w);
    document.getElementById('nav'+k).classList.toggle('on', k===w);
  }
  document.getElementById('pageTitle').textContent = TITLES[w][0];
  document.getElementById('pageSub').textContent = TITLES[w][1];
  if (w==='B') draw();
}

/* ── Pane A ── */
const gusel = document.getElementById('gu');
gusel.innerHTML = '<option value="">서울 전체</option>' +
  [...new Set(ROWS.map(r=>r.gu))].sort().map(g=>`<option>${g}</option>`).join('');
function currentRows(){
  const g = gusel.value;
  return ROWS.filter(r=>!g || r.gu===g);
}
function renderA(){
  const rows = currentRows();
  const top = rows.slice(0, +document.getElementById('topn').value);
  document.getElementById('n').textContent = rows.length.toLocaleString();
  document.getElementById('na').textContent = rows.filter(r=>r.acc>0).length.toLocaleString();
  document.getElementById('nf').textContent = rows.filter(r=>r.flood).length.toLocaleString();
  const tb = document.getElementById('tb'); tb.innerHTML='';
  top.forEach((r,i)=>{
    const addr = r.addr.startsWith(r.gu) ? r.addr.slice(r.gu.length+1) : r.addr;
    const tags = (r.acc>0?`<span class="tag acc">사고 ${r.acc}건 인접</span>`:'') +
                 (r.flood?`<span class="tag fld">침수 인접</span>`:'');
    const link = (r.lat && r.lon)
      ? `<a class="maplink" href="map_prototype.html#loc=${r.lat},${r.lon},${encodeURIComponent(r.gu+' '+addr)}" target="_blank" title="지도에서 보기">${r.gu} ${addr} <span class="pin">📍</span></a>`
      : `${r.gu} ${addr}`;
    tb.insertAdjacentHTML('beforeend',
      `<tr><td>${i+1}</td><td>${link}</td><td class="num">${r.count}회</td><td>${tags}</td></tr>`);
  });
}
function downloadCsv(){
  const rows = currentRows();
  const head = "자치구,주소,반복보수횟수,250m내_침하사고건수,침수이력인접\n";
  const body = rows.map(r=>`${r.gu},"${r.addr}",${r.count},${r.acc},${r.flood?'Y':'N'}`).join("\n");
  const blob = new Blob(["\uFEFF"+head+body], {type:"text/csv;charset=utf-8"});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (gusel.value||"서울전체") + "_조사우선순위.csv";
  a.click();
}
document.getElementById('csv').onclick = downloadCsv;
gusel.onchange = renderA;
document.getElementById('topn').onchange = renderA;

/* ── Pane B ── */
const totalRisk = SEGS.reduce((s,x)=>s+x.total,0);
const byEff  = [...SEGS].sort((a,b)=>b.total/b.cost - a.total/a.cost);
const byRisk = [...SEGS].sort((a,b)=>b.total - a.total);
function curveOf(list){ let c=0,r=0; return list.map(s=>{c+=s.cost; r+=s.total; return [c, r/totalRisk*100];}); }
const effC = curveOf(byEff), riskC = curveOf(byRisk);
function pick(budget){
  let c=0,r=0,n=0,chosen=[];
  for(const s of byEff){ if(c+s.cost>budget) continue; c+=s.cost; r+=s.total; n++; chosen.push(s); }
  return {c,r,n,chosen};
}
const fmt = m => m>=10000 ? (m/10000).toFixed(1).replace(/\.0$/,'')+'억원' : m.toLocaleString()+'만원';
const MAXB = 200000;
const cv = document.getElementById('curve'), ctx = cv.getContext('2d');
const OX=52, OY=cv.height-32, PW=cv.width-72, PH=cv.height-52;
function covAt(cv2, b){
  let last=0;
  for(const [c,p] of cv2){ if(c>b) break; last=p; }
  return last;
}
function draw(){
  ctx.clearRect(0,0,cv.width,cv.height);
  ctx.font='11px Segoe UI'; ctx.fillStyle='#9aa3af';
  ctx.strokeStyle='#e8eaf0'; ctx.lineWidth=1;
  for(let p=0;p<=100;p+=25){
    const y=OY-PH*p/100;
    ctx.setLineDash([3,4]);
    ctx.beginPath(); ctx.moveTo(OX,y); ctx.lineTo(OX+PW,y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillText(p+'%', 16, y+4);
  }
  for(let b=0;b<=20;b+=5) ctx.fillText(b+'억', OX+PW*b/20-8, OY+18);
  function plot(cv2,color,width,dash){
    ctx.strokeStyle=color; ctx.lineWidth=width; ctx.setLineDash(dash);
    ctx.beginPath(); ctx.moveTo(OX,OY);
    for(const [c,p] of cv2){ if(c>MAXB)break; ctx.lineTo(OX+PW*c/MAXB, OY-PH*p/100); }
    ctx.stroke(); ctx.setLineDash([]);
  }
  plot(riskC,'#c9cdd6',2,[5,4]);
  plot(effC,'#5A67D8',2,[]);
  const b=+document.getElementById('budget').value;
  const y=OY-PH*covAt(effC,b)/100, x=OX+PW*b/MAXB;
  ctx.fillStyle='#fff'; ctx.beginPath(); ctx.arc(x,y,6.5,0,7); ctx.fill();
  ctx.strokeStyle='#5A67D8'; ctx.lineWidth=2.5; ctx.beginPath(); ctx.arc(x,y,5,0,7); ctx.stroke();
}
const tip = document.getElementById('tip');
cv.addEventListener('mousemove', e=>{
  const rect = cv.getBoundingClientRect();
  const px = (e.clientX-rect.left) * (cv.width/rect.width);
  if(px<OX||px>OX+PW){ tip.style.display='none'; return; }
  const b = (px-OX)/PW*MAXB;
  tip.innerHTML = `예산 ${fmt(Math.round(b/1000)*1000)}<br>` +
    `<span style="color:#aeb6f5">효율 전략</span> ${covAt(effC,b).toFixed(1)}% · ` +
    `<span style="color:#c9cdd6">위험순</span> ${covAt(riskC,b).toFixed(1)}%`;
  tip.style.display='block';
  tip.style.left = Math.min(e.clientX-rect.left+14, rect.width-175)+'px';
  tip.style.top = (e.clientY-rect.top-14)+'px';
});
cv.addEventListener('mouseleave', ()=> tip.style.display='none');
function renderB(){
  const b=+document.getElementById('budget').value, res=pick(b);
  document.getElementById('budgetLabel').textContent=fmt(b);
  document.getElementById('cov').textContent=(res.r/totalRisk*100).toFixed(1)+'%';
  document.getElementById('nseg').textContent=res.n+'개';
  document.getElementById('spent').textContent=fmt(res.c);
  const tb=document.querySelector('#toplist'); tb.innerHTML='';
  res.chosen.slice(0,15).forEach((s,i)=>{
    const method = s.classes.includes('BK')?'부분 교체':(s.classes.filter(c=>c!=='DS').length?'비굴착 라이닝':'준설');
    tb.insertAdjacentHTML('beforeend',
      `<tr><td>${i+1}</td><td>${s.id}</td><td class="num">${s.total.toFixed(2)}</td><td class="num">${s.sink.toFixed(2)}</td><td class="num">${s.flood.toFixed(2)}</td><td>${method}</td><td class="num">${fmt(s.cost)}</td></tr>`);
  });
  draw();
}
document.getElementById('budget').addEventListener('input', renderB);

renderA(); renderB();
</script>
</body></html>"""

html = html.replace("__ROWS__", ROWS).replace("__SEGS__", SEGS)
out = os.path.join(PROJ, "dashboard.html")
open(out, "w", encoding="utf-8").write(html)
print("saved:", out, f"{os.path.getsize(out)//1024} KB")
