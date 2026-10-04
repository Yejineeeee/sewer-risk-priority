# 예산 시뮬레이션 HTML 생성: full_segments.json → budget_sim.html (단일 파일, 서버 불필요)
# 출력 지표는 "위험 커버리지 %" — 사고 감소량 같은 인과 주장은 하지 않는다.
import json, os

PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"
rows = json.load(open(os.path.join(PROJ, "full_segments.json"), encoding="utf-8"))

# 보수 공법·단가 가정 (시연용 — 화면에 명시):
#   파손(BK) 포함     → 부분 교체     5,000만원/구간
#   구조 결함(그 외)  → 비굴착 라이닝 2,000만원/구간
#   토사퇴적(DS)만    → 준설           500만원/구간
def cost_of(r):
    cls = set(r["classes"])
    if "BK" in cls:
        return 5000
    if cls - {"DS"}:
        return 2000
    return 500

segs = [{"id": r["segment"], "total": r["total"], "sink": r["sinkhole"],
         "flood": r["flood"], "classes": r["classes"], "cost": cost_of(r)}
        for r in rows]

data_js = json.dumps(segs, ensure_ascii=False)

html = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>보수 예산 시뮬레이션 — 위험 커버리지</title>
<style>
 body{font-family:'Malgun Gothic',sans-serif;margin:24px;max-width:900px}
 h2{margin:0 0 4px} .sub{color:#666;font-size:13px;margin-bottom:18px}
 .big{font-size:34px;font-weight:700} .lbl{color:#666;font-size:12px}
 .cards{display:flex;gap:16px;margin:14px 0}
 .card{border:1px solid #ddd;border-radius:8px;padding:12px 18px;flex:1}
 input[type=range]{width:100%}
 table{border-collapse:collapse;font-size:12.5px;margin-top:10px;width:100%}
 th,td{border-bottom:1px solid #eee;padding:4px 8px;text-align:left}
 th{background:#f7f7f7}
 canvas{border:1px solid #eee;border-radius:6px;margin-top:8px;width:100%}
 .note{color:#888;font-size:11.5px;margin-top:14px;line-height:1.6}
</style></head><body>
<h2>우기 전 보수 예산 시뮬레이션 <span style="font-size:14px;color:#a55">— 가상 보수 시나리오 기반 의사결정 지원</span></h2>
<div class="sub">전략: 위험/비용 효율 순 greedy 선택 · 대상: 가상 275개 구간(시연) · 지표: 본 시스템 위험 점수 체계 내 해소 비율 (실제 사고 감소율 아님)</div>

<label>보수 예산: <b id="budgetLabel"></b></label>
<input type="range" id="budget" min="0" max="200000" step="1000" value="30000">

<div class="cards">
 <div class="card"><div class="big" id="cov">-</div><div class="lbl">위험 커버리지 (해소되는 위험 점수 비율)</div></div>
 <div class="card"><div class="big" id="nseg">-</div><div class="lbl">보수 가능 구간 수 (275개 중)</div></div>
 <div class="card"><div class="big" id="spent">-</div><div class="lbl">집행 금액</div></div>
</div>

<canvas id="curve" width="860" height="260"></canvas>
<div class="lbl" style="text-align:center">예산(억원) → 위험 커버리지(%) 곡선 — 파랑: 위험/비용 효율 순, 회색 점선: 단순 위험 순</div>

<table id="toplist"><thead><tr><th>#</th><th>구간</th><th>위험 합계</th><th>싱크홀</th><th>침수</th><th>공법(가정)</th><th>비용</th></tr></thead><tbody></tbody></table>

<div class="note">※ 시연용 가정: 부분 교체 5,000만원 / 비굴착 라이닝 2,000만원 / 준설 500만원 (구간당, 검출 결함 유형 기준).
실제 단가는 관경·심도·연장에 따라 달라지며, 커버리지는 본 시스템의 위험 점수 체계 내 지표로서
사고 감소량을 의미하지 않음. 구간은 공개 데이터셋 이미지의 가상 묶음임.</div>

<script>
const SEGS = __DATA__;
const totalRisk = SEGS.reduce((s,x)=>s+x.total,0);
const byEff  = [...SEGS].sort((a,b)=>b.total/b.cost - a.total/a.cost);
const byRisk = [...SEGS].sort((a,b)=>b.total - a.total);
function curve(list){ // 누적 (비용, 커버리지%)
  let c=0,r=0; return list.map(s=>{c+=s.cost; r+=s.total; return [c, r/totalRisk*100];});
}
const effC = curve(byEff), riskC = curve(byRisk);
function pick(budget){
  let c=0,r=0,n=0,chosen=[];
  for(const s of byEff){ if(c+s.cost>budget) continue; c+=s.cost; r+=s.total; n++; chosen.push(s); }
  return {c,r,n,chosen};
}
const fmt = m => m>=10000 ? (m/10000).toFixed(1).replace(/\\.0$/,'')+'억원' : m.toLocaleString()+'만원';
function draw(){
  const cv=document.getElementById('curve'), ctx=cv.getContext('2d');
  ctx.clearRect(0,0,cv.width,cv.height);
  const maxB=200000, W=cv.width-60, H=cv.height-40, ox=45, oy=cv.height-25;
  ctx.strokeStyle='#ccc'; ctx.beginPath(); ctx.moveTo(ox,oy); ctx.lineTo(ox+W,oy); ctx.moveTo(ox,oy); ctx.lineTo(ox,oy-H); ctx.stroke();
  ctx.fillStyle='#888'; ctx.font='11px sans-serif';
  for(let p=0;p<=100;p+=25){ ctx.fillText(p+'%',6,oy-H*p/100+4); }
  for(let b=0;b<=20;b+=5){ ctx.fillText(b+'억',ox+W*b/20-8,oy+16); }
  function plot(cv2,color,dash){
    ctx.strokeStyle=color; ctx.setLineDash(dash); ctx.beginPath(); ctx.moveTo(ox,oy);
    for(const [c,p] of cv2){ if(c>maxB)break; ctx.lineTo(ox+W*c/maxB, oy-H*p/100); }
    ctx.stroke(); ctx.setLineDash([]);
  }
  plot(riskC,'#aaa',[5,4]); plot(effC,'#2166ac',[]);
  const b=+document.getElementById('budget').value, {r}=pick(b);
  ctx.fillStyle='#d73027'; ctx.beginPath();
  ctx.arc(ox+W*b/maxB, oy-H*(r/totalRisk*100)/100, 5, 0, 7); ctx.fill();
}
function update(){
  const b=+document.getElementById('budget').value, res=pick(b);
  document.getElementById('budgetLabel').textContent=fmt(b);
  document.getElementById('cov').textContent=(res.r/totalRisk*100).toFixed(1)+'%';
  document.getElementById('nseg').textContent=res.n+'개';
  document.getElementById('spent').textContent=fmt(res.c);
  const tb=document.querySelector('#toplist tbody'); tb.innerHTML='';
  res.chosen.slice(0,15).forEach((s,i)=>{
    const method = s.classes.includes('BK')?'부분 교체':(s.classes.filter(c=>c!=='DS').length?'비굴착 라이닝':'준설');
    tb.insertAdjacentHTML('beforeend',
      `<tr><td>${i+1}</td><td>${s.id}</td><td>${s.total.toFixed(2)}</td><td>${s.sink.toFixed(2)}</td><td>${s.flood.toFixed(2)}</td><td>${method}</td><td>${fmt(s.cost)}</td></tr>`);
  });
  draw();
}
document.getElementById('budget').addEventListener('input',update);
update();
</script></body></html>"""

html = html.replace("__DATA__", data_js)
out = os.path.join(PROJ, "budget_sim.html")
open(out, "w", encoding="utf-8").write(html)
print("saved:", out, f"{os.path.getsize(out)//1024} KB")
