# -*- coding: utf-8 -*-
"""risk_matrix.png 생성 — 구별 싱크홀×침수 사분면 산점도
데이터: data/gu_matrix_data.json (gu_aggregate 재집계 결과, 총 침수폴리곤 18,007 검증됨)
스타일: 미니멀(스파인 최소·그리드 없음·큰 점·점 옆 라벨) — 결과보고서 p12용
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgunbd.ttf")
font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data = json.load(open(os.path.join(BASE, "data/gu_matrix_data.json"), encoding="utf-8"))

gus = list(data)
xs = {g: data[g]["flood"] for g in gus}
ys = {g: data[g]["acc"] for g in gus}
mx = sorted(xs.values())[len(gus) // 2]   # 침수 중앙값 153
my = sorted(ys.values())[len(gus) // 2]   # 침하 중앙값 5

RED, ORANGE, BLUE, GRAY = "#D7302F", "#F1892D", "#1F63AC", "#b3bac4"
INK = "#2d3748"

def color(g):
    hi_s, hi_f = ys[g] > my, xs[g] > mx
    return RED if (hi_s and hi_f) else ORANGE if hi_s else BLUE if hi_f else GRAY

# 라벨 배치: (dx pt, dy pt, ha)  — 겹침 수동 해소
POS = {
    "강남구":  (10, 2, "left"),   "송파구":  (10, 2, "left"),
    "성북구":  (10, 2, "left"),   "영등포구": (-10, 6, "right"),
    "강서구":  (10, 2, "left"),   "동대문구": (0, 11, "center"),
    "마포구":  (10, -4, "left"),   "성동구": (-10, 0, "right"),
    "종로구":  (4, 11, "center"),  "강동구":  (0, 11, "center"),
    "서초구":  (-6, 12, "center"), "구로구":  (2, -18, "center"),
    "강북구":  (2, -18, "center"), "동작구":  (0, 12, "right"),
    "관악구":  (-2, -20, "right"), "금천구":  (10, -2, "left"),
}

fig, ax = plt.subplots(figsize=(10.5, 7.5), dpi=200)

# 사분면 배경 (아주 옅은 톤 — 코너 라벨 색과 대응)
X0, X1 = -1, 9000
Y0, Y1 = -2.4, 22
fy = (my - Y0) / (Y1 - Y0)   # 중앙값의 세로 위치(축 비율)
ax.axvspan(X0, mx, ymin=fy, ymax=1, color=ORANGE, alpha=0.05, zorder=0)   # 싱크홀 우세
ax.axvspan(mx, X1, ymin=fy, ymax=1, color=RED, alpha=0.05, zorder=0)      # 복합 위험
ax.axvspan(X0, mx, ymin=0, ymax=fy, color="#9aa3af", alpha=0.05, zorder=0)  # 저위험
ax.axvspan(mx, X1, ymin=0, ymax=fy, color=BLUE, alpha=0.05, zorder=0)     # 침수 우세

# 중앙값 기준선 (아주 옅게)
ax.axvline(mx, color="#c9cdd6", lw=1.4, ls=(0, (5, 4)), zorder=1)
ax.axhline(my, color="#c9cdd6", lw=1.4, ls=(0, (5, 4)), zorder=1)

# 점
for g in gus:
    ax.scatter(xs[g], ys[g], s=210, color=color(g), zorder=3,
               edgecolor="white", linewidth=1.8)

# 라벨 (색 있는 구만)
for g, (dx, dy, ha) in POS.items():
    ax.annotate(g, (xs[g], ys[g]), textcoords="offset points",
                xytext=(dx, dy), fontsize=13, fontweight="bold",
                color=INK, ha=ha, zorder=4)

# 사분면 코너 라벨
ax.text(0.02, 0.97, "싱크홀 우세", transform=ax.transAxes, fontsize=15,
        fontweight="bold", color=ORANGE, va="top")
ax.text(0.98, 0.97, "복합 위험", transform=ax.transAxes, fontsize=15,
        fontweight="bold", color=RED, va="top", ha="right")
ax.text(0.02, 0.03, "상대적 저위험", transform=ax.transAxes, fontsize=15,
        fontweight="bold", color="#9aa3af", va="bottom")
ax.text(0.98, 0.03, "침수 우세", transform=ax.transAxes, fontsize=15,
        fontweight="bold", color=BLUE, va="bottom", ha="right")

ax.set_xscale("symlog", linthresh=10)
ax.set_xlim(X0, X1)
ax.set_ylim(Y0, Y1)
ax.set_xlabel("침수 이력 (침수흔적 폴리곤 수, 로그 스케일)", fontsize=17, color="black", labelpad=8)
ax.set_ylabel("지반침하 사고 (건, 2018~2025)", fontsize=17, color="black", labelpad=8)

# 미니멀 축: 위·오른쪽 제거
for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color("black")
    ax.spines[side].set_linewidth(1.3)
ax.tick_params(colors="black", labelsize=14)
ax.grid(False)

ax.set_title("서울 25개 자치구 싱크홀 × 침수 위험 매트릭스",
             fontsize=20, fontweight="bold", color="black", pad=18)

fig.tight_layout()
out = os.path.join(BASE, "risk_matrix.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("saved:", out)
