# Tier 1 위험 지도 (완성본)
# 레이어: ① 싱크홀 축 ② 침수 축 ③ 2축 사분면(기본) ④ 침수 실폴리곤 ⑤ E2E 시연(기본)
import json, os, io, zipfile
from collections import Counter

import folium
from folium.plugins import Fullscreen
import shapefile
from pyproj import Transformer

PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"
DATA = os.path.join(PROJ, "data")
OUT = os.path.join(PROJ, "map_prototype.html")

# ── 1. 구별 침하사고 ─────────────────────────────────────────────────
items = json.load(open(os.path.join(DATA, "accidents", "subsidence_all.json"), encoding="utf-8"))
seoul = [i for i in items if i.get("sido") == "서울특별시"]
acc = Counter(i["sigungu"] for i in seoul)

# ── 2. 침수 폴리곤 ───────────────────────────────────────────────────
tf = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)
flood_cnt = Counter()
flood_geo = {"type": "FeatureCollection", "features": []}
shapes_2022 = []  # 2022년 폭우: 개별 폴리곤 2만 개 → union 병합 후 침수 범위로 표시
for zp in sorted(os.listdir(os.path.join(DATA, "flood"))):
    if not zp.endswith(".zip"):
        continue
    light = zp in ("seq_31.zip", "seq_32.zip", "seq_103.zip")
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
        fields = [f[0] for f in r.fields[1:]]
        gi = fields.index("GU_NAM") if "GU_NAM" in fields else None
        yi = fields.index("F_YR") if "F_YR" in fields else None
        si = fields.index("F_SHIM") if "F_SHIM" in fields else None
        for sr in r.iterShapeRecords():
            gu = str(sr.record[gi]).strip().replace("?", "") if gi is not None else ""
            if gu.endswith("구"):
                flood_cnt[gu] += 1
            pts = sr.shape.points
            if not pts:
                continue
            if not light:  # 2022년: 원시 도형 수집 (아래에서 union 병합)
                if zp == "seq_30.zip":
                    try:
                        from shapely.geometry import shape as shp_shape
                        shapes_2022.append(shp_shape(sr.shape.__geo_interface__))
                    except Exception:
                        pass
                continue
            parts = list(sr.shape.parts) + [len(pts)]
            rings = []
            for a, b in zip(parts, parts[1:]):
                ring = [tf.transform(x, y) for x, y in pts[a:b]]
                rings.append([[round(lo, 6), round(la, 6)] for lo, la in ring])
            flood_geo["features"].append({
                "type": "Feature",
                "properties": {"gu": gu,
                               "year": str(sr.record[yi]).strip() if yi is not None else "?",
                               "depth": sr.record[si] if si is not None else None},
                "geometry": {"type": "Polygon", "coordinates": rings},
            })

# ── 3. 구별 2축 점수 + 사분면 ────────────────────────────────────────
gu_geo = json.load(open(os.path.join(DATA, "seoul_gu.geojson"), encoding="utf-8"))
gus = [f["properties"]["name"] for f in gu_geo["features"]]

def norm(cnt):
    mx = max(cnt.values()) if cnt else 1
    return {g: cnt.get(g, 0) / mx for g in gus}

pothole = Counter(json.load(open(os.path.join(DATA, "pothole_by_gu.json"), encoding="utf-8")))
s_sink, s_flood = norm(acc), norm(flood_cnt)
s_pot = norm(pothole)
med_s = sorted(s_sink.values())[len(gus) // 2]
med_f = sorted(s_flood.values())[len(gus) // 2]

def quadrant(g):
    hi_s, hi_f = s_sink[g] > med_s, s_flood[g] > med_f
    if hi_s and hi_f: return "복합 위험 (최우선)"
    if hi_s: return "싱크홀 우세"
    if hi_f: return "침수 우세"
    return "상대적 저위험"

QCOLOR = {"복합 위험 (최우선)": "#d73027", "싱크홀 우세": "#fc8d59",
          "침수 우세": "#4575b4", "상대적 저위험": "#d9d9d9"}

def lerp_hex(c1, c2, t):
    a = [int(c1[i:i+2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i+2], 16) for i in (1, 3, 5)]
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))

for f in gu_geo["features"]:
    g = f["properties"]["name"]
    f["properties"].update({
        "acc": acc.get(g, 0), "flood": flood_cnt.get(g, 0),
        "quad": quadrant(g), "qcolor": QCOLOR[quadrant(g)],
        "sink_color": lerp_hex("#fff5eb", "#d73027", s_sink[g]),
        "flood_color": lerp_hex("#f7fbff", "#2166ac", s_flood[g]),
        "pot": pothole.get(g, 0),
        "pot_color": lerp_hex("#f7fcf5", "#00441b", s_pot[g]),
    })

# ── 4. 지도 ──────────────────────────────────────────────────────────
# 배경지도: OpenStreetMap 표준(무료·무키·전 줌 커버) + CSS 회색 필터로 미니멀 톤 재현.
# CARTO 무료 타일은 2026.8부터 API 키 워터마크, Esri Light Gray는 한국 상세 줌 미지원이라 교체.
m = folium.Map(location=[37.5642, 126.99], zoom_start=11, tiles=None, prefer_canvas=True)
folium.TileLayer(
    tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    attr="&copy; OpenStreetMap contributors",
    name="배경지도", max_zoom=19, control=False,
).add_to(m)
Fullscreen(position="topleft", title="전체화면", title_cancel="닫기").add_to(m)

TIP = folium.GeoJsonTooltip(fields=["name", "acc", "flood", "quad"],
                            aliases=["자치구", "침하사고(건)", "침수이력(폴리곤)", "분류"])

def gu_layer(name, color_prop, show):
    layer = folium.FeatureGroup(name=name, show=show)
    folium.GeoJson(
        gu_geo,
        style_function=lambda f, cp=color_prop: {
            "fillColor": f["properties"][cp], "color": "#8a94a6",
            "weight": 0.8, "fillOpacity": 0.55},
        highlight_function=lambda f: {"weight": 3, "color": "#222"},
        tooltip=folium.GeoJsonTooltip(
            fields=["name", "acc", "flood", "pot", "quad"],
            aliases=["자치구", "침하사고(건)", "침수이력(폴리곤)", "포트홀 신고·보수(건)", "분류"]),
    ).add_to(layer)
    return layer

gu_layer("싱크홀 축", "sink_color", False).add_to(m)
gu_layer("침수 축", "flood_color", False).add_to(m)
gu_layer("사분면 종합", "qcolor", True).add_to(m)
# ⑥ 포트홀 구별 밀도 레이어는 제거 (⑦ 지점 단위가 대체 — 구별 수치는 툴팁에 유지)

flood_layer = folium.FeatureGroup(name="침수흔적 (2023~25)", show=False)
folium.GeoJson(
    flood_geo,
    style_function=lambda f: {"fillColor": "#1f78b4", "color": "#1f78b4",
                              "weight": 1, "fillOpacity": 0.5},
    tooltip=folium.GeoJsonTooltip(fields=["gu", "year", "depth"],
                                  aliases=["구", "연도", "침수심(m)"]),
).add_to(flood_layer)
flood_layer.add_to(m)

if shapes_2022:
    # union 병합 → 10m 단순화 → WGS84 변환 (원본 좌표계 단위 = 미터)
    from shapely.ops import unary_union
    from shapely.validation import make_valid
    valid = [g if g.is_valid else make_valid(g) for g in shapes_2022]
    merged = unary_union(valid).simplify(10)
    polys = list(merged.geoms) if merged.geom_type == "MultiPolygon" else [merged]
    geo_2022 = {"type": "FeatureCollection", "features": []}
    for p in polys:
        if p.geom_type != "Polygon" or p.area < 100:  # 100㎡ 미만 파편 제거
            continue
        rings = []
        for ring in [p.exterior] + list(p.interiors):
            rings.append([[round(lo, 6), round(la, 6)]
                          for lo, la in (tf.transform(x, y) for x, y in ring.coords)])
        geo_2022["features"].append({"type": "Feature", "properties": {},
                                     "geometry": {"type": "Polygon", "coordinates": rings}})
    layer_2022 = folium.FeatureGroup(name="2022 폭우 범위", show=False)
    folium.GeoJson(
        geo_2022,
        style_function=lambda f: {"fillColor": "#54278f", "color": "#54278f",
                                  "weight": 1, "fillOpacity": 0.45},
        tooltip="2022년 8월 집중호우 침수 구역 (병합)",
    ).add_to(layer_2022)
    layer_2022.add_to(m)
    print(f"2022 병합: {len(shapes_2022)}개 → {len(geo_2022['features'])}개 폴리곤")

# ── 4b. 지오코딩 점 레이어: 반복 보수 지점 + 침하사고 실지점 ─────────
rep_path = os.path.join(DATA, "geocoded_repairs.json")
if os.path.exists(rep_path):
    reps = json.load(open(rep_path, encoding="utf-8"))
    rep_layer = folium.FeatureGroup(name="반복 보수 지점", show=False)
    # 반복 횟수 구간별 GeoJSON (개별 마커 대비 용량·렌더링 효율)
    buckets = [("10회 이상", lambda c: c >= 10, "#67000d", 6),
               ("5~9회", lambda c: 5 <= c < 10, "#a50f15", 4),
               ("3~4회", lambda c: c < 5, "#fb6a4a", 2.5)]
    for label, cond, color, radius in buckets:
        feats = [{"type": "Feature",
                  "properties": {"addr": r["addr"], "count": r["count"]},
                  "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]}}
                 for r in reps if cond(r["count"])]
        if not feats:
            continue
        folium.GeoJson(
            {"type": "FeatureCollection", "features": feats},
            marker=folium.CircleMarker(radius=radius, color=color, fill=True,
                                       fill_opacity=0.7, weight=0),
            tooltip=folium.GeoJsonTooltip(fields=["addr", "count"],
                                          aliases=["지점", "보수 횟수"]),
        ).add_to(rep_layer)
    rep_layer.add_to(m)

acc_path = os.path.join(DATA, "geocoded_accidents.json")
if os.path.exists(acc_path):
    accs = json.load(open(acc_path, encoding="utf-8"))
    acc_layer = folium.FeatureGroup(name="실제 사고 지점", show=False)
    for a in accs:
        folium.CircleMarker(
            location=[a["lat"], a["lon"]], radius=6, color="#000",
            fill=True, fill_color="#ffd92f", fill_opacity=0.95, weight=1.5,
            popup=folium.Popup(
                f"<b>지반침하 사고</b> ({a['date'][:4]}.{a['date'][4:6]})<br>"
                f"{a['gu']} · 원인: {a['reason'] or '미상'}"
                + ("<br><span style='color:#888;font-size:11px'>동 단위 근사 위치</span>" if a.get("approx") else ""),
                max_width=220),
        ).add_to(acc_layer)
    acc_layer.add_to(m)

# ── 5. E2E 시연 레이어 + Top-3 순위 뱃지 ─────────────────────────────
demo_path = os.path.join(PROJ, "demo_segments.json")
top3_rows = ""
if os.path.exists(demo_path):
    rows = json.load(open(demo_path, encoding="utf-8"))
    route = [(37.5265, 126.8962), (37.5236, 126.9013), (37.5205, 126.9068),
             (37.5178, 126.9122), (37.5202, 126.9180), (37.5232, 126.9231),
             (37.5262, 126.9282), (37.5292, 126.9333)]
    max_total = max(r["total"] for r in rows) or 1
    ranked = {r["segment"]: i + 1 for i, r in enumerate(rows)}
    pos = {r["segment"]: route[i] for i, r in enumerate(sorted(rows, key=lambda x: x["segment"]))}
    demo_layer = folium.FeatureGroup(name="AI 탐지 구간 (시연)", show=True)
    folium.PolyLine(route, color="#888", weight=2, dash_array="6",
                    tooltip="가상 조사 노선 (시연)").add_to(demo_layer)
    for r in rows:
        la, lo = pos[r["segment"]]
        ratio = r["total"] / max_total
        color = "#d73027" if ratio > 0.75 else "#fc8d59" if ratio > 0.5 else "#4575b4"
        rank = ranked[r["segment"]]
        folium.CircleMarker(
            location=[la, lo], radius=8 + 9 * ratio, color=color, fill=True,
            fill_opacity=0.85,
            popup=folium.Popup(
                f"<b>{r['segment']}</b> — 우선순위 <b>{rank}위</b><br>"
                f"결함 {r['n_defects']}건: {', '.join(r['classes'])}<br>"
                f"싱크홀 <b>{r['sinkhole']}</b> / 침수 <b>{r['flood']}</b><br>"
                f"<span style='color:#777;font-size:11px'>※ 시연용 가상 배치 — 실운영 시 조사조서의 관로 ID·위치로 대체</span>",
                max_width=280),
        ).add_to(demo_layer)
        if rank <= 3:
            folium.Marker(
                location=[la, lo],
                icon=folium.DivIcon(html=(
                    f"<div style='font:700 11px sans-serif;color:#fff;background:#333;"
                    f"border-radius:50%;width:18px;height:18px;line-height:18px;"
                    f"text-align:center;transform:translate(-4px,-22px)'>{rank}</div>")),
            ).add_to(demo_layer)
    demo_layer.add_to(m)
    top3_rows = "".join(
        f"<tr><td style='font-weight:700'>{i+1}</td><td>{r['segment']}</td>"
        f"<td>{r['n_defects']}건</td><td>{r['sinkhole']}</td><td>{r['flood']}</td></tr>"
        for i, r in enumerate(rows[:3]))

# ── 6. 헤더 · 범례 · 우선순위 패널 (대시보드와 동일한 디자인 언어) ────
FONT = "'Pretendard Variable',Pretendard,'Segoe UI','Malgun Gothic',sans-serif"
BASE_CSS = f"font-family:{FONT};background:rgba(255,255,255,.97);" \
           "border:1px solid #e5e8ec;border-radius:12px;box-shadow:0 4px 18px rgba(27,37,89,.10);z-index:9999;"
INK, MUTED, FAINT = "#1B2559", "#6B7280", "#9aa3af"

header = f"""
<div style="position:fixed; top:12px; left:56px; {BASE_CSS} padding:11px 18px; max-width:460px">
 <div style="font-size:15px;font-weight:700;color:{INK}">하수관 위험 우선순위 지도</div>
 <div style="font-size:11px;color:{MUTED};margin-top:2px">
  지반침하 사고 1,584건 / 침수흔적도 2022~25 / 포트홀 9.4만 건</div>
 <div style="font-size:10px;color:{FAINT};margin-top:5px;padding-top:5px;border-top:1px solid #f4f6f9">
  자료: 국토교통부 지하안전정보시스템 / 서울 열린데이터광장 / 공공데이터포털 / VWorld</div>
</div>"""

gu_top5 = sorted(gus, key=lambda g: -(s_sink[g] + s_flood[g]))[:5]
chips = "".join(
    f"<div style='display:flex;align-items:center;gap:8px;padding:4.5px 0;"
    f"border-bottom:1px solid #f4f6f9;font-size:12px'>"
    f"<span style='width:9px;height:9px;border-radius:50%;background:{QCOLOR[quadrant(g)]};flex-shrink:0'></span>"
    f"<span style='color:{INK};font-weight:600'>{g}</span>"
    f"<span style='margin-left:auto;color:{MUTED}'>침하 {acc.get(g,0)} / 침수 {flood_cnt.get(g,0):,}</span></div>"
    for g in gu_top5)
top3_html = ""
if top3_rows:
    top3_html = ("<div style='font-size:10.5px;letter-spacing:1px;color:" + FAINT + ";margin:12px 0 4px'>시연 / 보수 권장 구간</div>"
                 + "<table style='width:100%;border-collapse:collapse;font-size:11.5px;color:" + MUTED + "'>"
                 + "<tr style='color:" + FAINT + ";font-size:10.5px'><th align=left>#</th><th align=left>구간</th><th>결함</th><th>싱크홀</th><th>침수</th></tr>"
                 + top3_rows + "</table>")
panel = f"""
<div style="position:fixed; top:12px; right:12px; {BASE_CSS} padding:14px 16px; width:280px">
 <div style="font-size:10.5px;letter-spacing:1px;color:{FAINT};margin-bottom:6px">자치구 종합 위험 TOP 5</div>
 {chips}
 {top3_html}
</div>"""

legend = f"""
<div style="position:fixed; bottom:26px; left:12px; {BASE_CSS} padding:11px 15px; font-size:11.5px; line-height:1.9; color:{MUTED}">
 <div style="font-size:10.5px;letter-spacing:1px;color:{FAINT};margin-bottom:3px">사분면 분류</div>
 {"".join(f"<span style='display:inline-block;width:9px;height:9px;border-radius:50%;background:{c};margin-right:6px'></span>{k}<br>" for k, c in QCOLOR.items())}
 <span style="color:{FAINT};font-size:10.5px">시연 원: 크기 = 위험 / 숫자 = 순위</span>
</div>"""

for html in (header, panel, legend):
    m.get_root().html.add_child(folium.Element(html))
m.get_root().header.add_child(folium.Element(
    "<title>하수관 위험 우선순위 지도</title>"
    '<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">'
    "<style>"
    f".leaflet-control-layers{{border-radius:12px !important;border:1px solid #e5e8ec !important;"
    f"box-shadow:0 4px 18px rgba(27,37,89,.10) !important;font-family:{FONT}}}"
    ".leaflet-control-layers-expanded{padding:10px 14px !important;min-width:170px}"
    ".leaflet-control-layers-overlays label,.leaflet-control-layers-base label"
    "{padding:3px 0;font-size:12.5px;color:#1B2559}"
    ".leaflet-control-layers-overlays label:hover{color:#0040cb}"
    ".leaflet-control-layers-separator{border-top:1px solid #f4f6f9 !important;margin:6px 0 !important}"
    # OSM 컬러 타일 → 회색 미니멀 톤 (배경 타일 이미지에만 적용, 데이터 레이어는 캔버스라 무관)
    ".leaflet-tile-pane img.leaflet-tile{filter:grayscale(1) brightness(1.08) contrast(0.9)}"
    f".leaflet-popup-content-wrapper{{border-radius:10px;font-family:{FONT}}}"
    f".leaflet-container{{font-family:{FONT}}}"
    "</style>"))
folium.LayerControl(collapsed=True, position="bottomright").add_to(m)

# 대시보드 → 지도 연결: #loc=lat,lon,라벨 해시를 받아 이동+하이라이트
hash_js = f"""
<script>
document.addEventListener("DOMContentLoaded", function() {{
  var mp = window["{m.get_name()}"];
  if (!mp || !location.hash.startsWith("#loc=")) return;
  try {{
    var parts = decodeURIComponent(location.hash.slice(5)).split(",");
    var lat = parseFloat(parts[0]), lon = parseFloat(parts[1]);
    var label = parts.slice(2).join(",") || "선택 지점";
    if (isNaN(lat) || isNaN(lon)) return;
    mp.setView([lat, lon], 17);
    var hl = L.circleMarker([lat, lon], {{radius: 14, color: "#D73027",
      weight: 3, fill: true, fillOpacity: 0.15}}).addTo(mp);
    hl.bindPopup("<b>" + label + "</b><br><span style='color:#777;font-size:11px'>대시보드에서 선택한 지점</span>").openPopup();
    var grow = true;
    setInterval(function() {{
      hl.setRadius(grow ? 20 : 14); grow = !grow;
    }}, 600);
  }} catch (e) {{}}
}});
</script>"""
m.get_root().html.add_child(folium.Element(hash_js))
m.save(OUT)
print("saved:", OUT, f"({os.path.getsize(OUT)//1024} KB)")
