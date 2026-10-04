# 조사 우선순위 리스트 페이지 생성: 반복 보수 핫스팟 → 구별 CCTV 조사 후보 목록 (CSV 내보내기)
# 우선순위 규칙(투명성): ① 250m 내 실제 침하사고 유무 → ② 반복 보수 횟수 → ③ 침수 이력 인접(100m)
import json, math, os

import shapefile, io, zipfile
from shapely.geometry import shape, Point, Polygon
from shapely.strtree import STRtree
from shapely.ops import transform as shp_transform

PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"
DATA = os.path.join(PROJ, "data")

LAT_M = 111320.0
LON_M = 111320.0 * math.cos(math.radians(37.55))
def to_m(lon, lat):
    return lon * LON_M, lat * LAT_M

reps = json.load(open(os.path.join(DATA, "geocoded_repairs.json"), encoding="utf-8"))
accs = json.load(open(os.path.join(DATA, "geocoded_accidents.json"), encoding="utf-8"))
gu_geo = json.load(open(os.path.join(DATA, "seoul_gu.geojson"), encoding="utf-8"))

# 구 폴리곤 (주소에서 구를 못 뽑는 경우 대비)
gu_polys = [(f["properties"]["name"], shape(f["geometry"])) for f in gu_geo["features"]]
GUS = [n for n, _ in gu_polys]

def gu_of(item):
    tok = item["addr"].split()[0]
    if tok in GUS:
        return tok
    p = Point(item["lon"], item["lat"])
    for n, poly in gu_polys:
        if poly.contains(p):
            return n
    return None

# 사고 인접(250m) 건수
acc_pts = [(a["lat"], a["lon"]) for a in accs]
def acc_near(lat, lon, radius=250):
    n = 0
    for al, ao in acc_pts:
        dy = (al - lat) * LAT_M
        dx = (ao - lon) * LON_M
        if dy*dy + dx*dx <= radius*radius:
            n += 1
    return n

# 침수 폴리곤 (2023~25 상세 + 2022 병합과 동일 소스에서 도형 로드) → 미터 좌표 STRtree
tfm = None
try:
    from pyproj import Transformer
    tfm = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)
except Exception:
    pass

flood_geoms = []
for zp in sorted(os.listdir(os.path.join(DATA, "flood"))):
    if not zp.endswith(".zip"):
        continue
    z = zipfile.ZipFile(os.path.join(DATA, "flood", zp))
    names = z.namelist()
    for base in sorted(set(n[:-4] for n in names if n.lower().endswith(".shp"))):
        try:
            r = shapefile.Reader(shp=io.BytesIO(z.read(base + ".shp")),
                                 dbf=io.BytesIO(z.read(base + ".dbf")),
                                 shx=io.BytesIO(z.read(base + ".shx")),
                                 encoding="cp949", encodingErrors="replace")
        except Exception:
            continue
        for sr in r.iterShapes():
            pts = sr.points
            if not pts:
                continue
            parts = list(sr.parts) + [len(pts)]
            ring = [tfm.transform(x, y) for x, y in pts[parts[0]:parts[1]]]
            if len(ring) >= 4:
                try:
                    poly = Polygon(ring)
                    if poly.is_valid and 126.5 < poly.centroid.x < 127.5:
                        flood_geoms.append(shp_transform(lambda x, y: to_m(x, y), poly))
                except Exception:
                    pass

tree = STRtree(flood_geoms)
def flood_near(lat, lon, radius=100):
    x, y = to_m(lon, lat)
    p = Point(x, y)
    idx = tree.query(p.buffer(radius))
    return len(idx) > 0

rows = []
for r in reps:
    g = gu_of(r)
    if not g:
        continue
    an = acc_near(r["lat"], r["lon"])
    fn = flood_near(r["lat"], r["lon"])
    rows.append({"gu": g, "addr": r["addr"], "count": r["count"],
                 "acc": an, "flood": 1 if fn else 0,
                 "lat": round(r["lat"], 6), "lon": round(r["lon"], 6)})

rows.sort(key=lambda r: (-(r["acc"] > 0), -r["count"], -r["flood"]))
stats = {
    "total": len(rows),
    "with_acc": sum(1 for r in rows if r["acc"] > 0),
    "with_flood": sum(1 for r in rows if r["flood"]),
    "flood_polys": len(flood_geoms),
}
print(f"핫스팟 {stats['total']}곳 | 사고 250m 인접 {stats['with_acc']} | 침수 100m 인접 {stats['with_flood']} | 침수도형 {stats['flood_polys']}")

data_js = json.dumps(rows, ensure_ascii=False)
html = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>CCTV 조사 우선순위 리스트 — 반복 보수 핫스팟</title>
<style>
 body{font-family:'Malgun Gothic',sans-serif;margin:24px;max-width:980px}
 h2{margin:0 0 4px} .sub{color:#666;font-size:13px;margin-bottom:16px;line-height:1.6}
 .bar{display:flex;gap:12px;align-items:center;margin:14px 0}
 select,button{font:14px 'Malgun Gothic';padding:6px 10px}
 button{cursor:pointer;background:#1F3557;color:#fff;border:none;border-radius:5px}
 .cards{display:flex;gap:14px;margin:12px 0}
 .card{border:1px solid #ddd;border-radius:8px;padding:10px 16px;flex:1}
 .big{font-size:26px;font-weight:700} .lbl{color:#666;font-size:12px}
 table{border-collapse:collapse;font-size:13px;width:100%;margin-top:8px}
 th,td{border-bottom:1px solid #eee;padding:5px 8px;text-align:left}
 th{background:#f7f7f7;position:sticky;top:0}
 .tag{display:inline-block;padding:1px 7px;border-radius:9px;font-size:11.5px;color:#fff}
 .acc{background:#C0392B} .fld{background:#2166AC}
 .note{color:#888;font-size:11.5px;margin-top:14px;line-height:1.6}
</style></head><body>
<h2>CCTV 조사 우선순위 리스트</h2>
<div class="sub">반복 보수 핫스팟(3회 이상, 지오코딩 성공분) 기반 정밀조사 후보 —
우선순위 규칙: ① 250m 내 침하사고 유무 → ② 반복 보수 횟수 → ③ 침수 이력 인접(100m).<br>
근거: 실제 침하사고 지점 주변 250m의 반복 보수 밀도는 무작위 대비 1.47배 (순열검정 p=0.0001).</div>

<div class="bar">
 <label>자치구: <select id="gu"></select></label>
 <label>표시: <select id="topn"><option>50</option><option>100</option><option selected>200</option><option value="99999">전체</option></select></label>
 <button id="csv">CSV 다운로드</button>
</div>

<div class="cards">
 <div class="card"><div class="big" id="n">-</div><div class="lbl">조사 후보 지점</div></div>
 <div class="card"><div class="big" id="na">-</div><div class="lbl">250m 내 실제 침하사고 있음</div></div>
 <div class="card"><div class="big" id="nf">-</div><div class="lbl">침수 이력 인접(100m)</div></div>
</div>

<table><thead><tr><th>#</th><th>주소</th><th>반복 보수</th><th>신호</th></tr></thead><tbody id="tb"></tbody></table>

<div class="note">※ 데이터: 서울시 포트홀 보수 위치(2023.1~2025.5) · 국토부 지반침하 사고정보 · 서울시 침수흔적도.
반복 보수 횟수는 번지 단위 집계로, 대형 필지·긴 도로 구간의 대표 주소 집계 가능성 있음.
본 목록은 조사 대상 스크리닝 후보이며 현장 여건 확인을 대체하지 않음.</div>

<script>
const ROWS = __DATA__;
const gus = [...new Set(ROWS.map(r=>r.gu))].sort();
const sel = document.getElementById('gu');
sel.innerHTML = '<option value="">서울 전체</option>' + gus.map(g=>`<option>${g}</option>`).join('');
function current(){
  const g = sel.value, n = +document.getElementById('topn').value;
  const rows = ROWS.filter(r=>!g || r.gu===g);
  return {rows, top: rows.slice(0, n)};
}
function render(){
  const {rows, top} = current();
  document.getElementById('n').textContent = rows.length.toLocaleString();
  document.getElementById('na').textContent = rows.filter(r=>r.acc>0).length.toLocaleString();
  document.getElementById('nf').textContent = rows.filter(r=>r.flood).length.toLocaleString();
  const tb = document.getElementById('tb'); tb.innerHTML='';
  top.forEach((r,i)=>{
    const tags = (r.acc>0?`<span class="tag acc">사고 ${r.acc}건 인접</span> `:'') + (r.flood?`<span class="tag fld">침수 인접</span>`:'');
    tb.insertAdjacentHTML('beforeend', `<tr><td>${i+1}</td><td>${r.gu} ${r.addr.startsWith(r.gu)?r.addr.slice(r.gu.length+1):r.addr}</td><td>${r.count}회</td><td>${tags}</td></tr>`);
  });
}
document.getElementById('csv').onclick = ()=>{
  const {rows} = current();
  const head = "자치구,주소,반복보수횟수,250m내_침하사고건수,침수이력인접\\n";
  const body = rows.map(r=>`${r.gu},"${r.addr}",${r.count},${r.acc},${r.flood?'Y':'N'}`).join("\\n");
  const blob = new Blob(["\\uFEFF"+head+body], {type:"text/csv;charset=utf-8"});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = (sel.value||"서울전체") + "_조사우선순위.csv";
  a.click();
};
sel.onchange = render; document.getElementById('topn').onchange = render;
render();
</script></body></html>"""
html = html.replace("__DATA__", data_js)
out = os.path.join(PROJ, "survey_priority.html")
open(out, "w", encoding="utf-8").write(html)
print("saved:", out, f"{os.path.getsize(out)//1024} KB")
