# -*- coding: utf-8 -*-
"""p12용 미니 차트 2종 — risk_matrix와 같은 미니멀 스타일
1) cause_distribution.png : 사고 원인 가로 막대 (하수관 손상 강조)
2) monthly_accidents.png  : 월별 사고 분포 (우기 6~8월 강조)
데이터: data/accidents/subsidence_all.json (1,584건)
"""
import json, os, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgunbd.ttf")
font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = json.load(open(os.path.join(BASE, "data/accidents/subsidence_all.json"), encoding="utf-8"))
total = len(items)
assert total == 1584, total

BLUE = "#0040cb"
GRAY = "#c3c9d2"
INK = "black"

# ── 1) 원인 분포 (상위 5개 명시 원인) ──────────────────────
reasons = collections.Counter(i["sagoReason"].strip() for i in items)
named = [(k, v) for k, v in reasons.most_common() if k and k not in ("기타",)]
top5 = named[:5]
labels = [k for k, v in top5][::-1]
vals = [v / total * 100 for k, v in top5][::-1]

fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
colors = [BLUE if l == "하수관 손상" else GRAY for l in labels]
bars = ax.barh(labels, vals, color=colors, height=0.62)
for b, v, l in zip(bars, vals, labels):
    ax.text(v + 0.8, b.get_y() + b.get_height() / 2, f"{v:.1f}%",
            va="center", fontsize=13,
            fontweight="bold" if l == "하수관 손상" else "normal",
            color=BLUE if l == "하수관 손상" else "#6b7280")
ax.set_title("지반침하 사고 원인 분포 (2018~2025, 1,584건)",
             fontsize=15, fontweight="bold", color=INK, pad=12)
ax.set_xlim(0, 48)
ax.tick_params(axis="y", labelsize=13, colors=INK, length=0)
ax.tick_params(axis="x", labelbottom=False, length=0)
for s in ("top", "right", "bottom"):
    ax.spines[s].set_visible(False)
ax.spines["left"].set_color(INK)
ax.text(0, -0.14, "※ 원인 미기재 10.5% · 기타 10.3% 제외한 상위 5개 원인",
        transform=ax.transAxes, fontsize=10, color="#8b93a1")
fig.tight_layout()
fig.savefig(os.path.join(BASE, "cause_distribution.png"),
            bbox_inches="tight", facecolor="white")
print("saved cause_distribution.png")

# ── 2) 월별 분포 (우기 강조) ──────────────────────────────
months = collections.Counter(int(i["sagoDate"][4:6]) for i in items
                             if i.get("sagoDate") and len(i["sagoDate"]) >= 6)
rainy = sum(months[m] for m in (6, 7, 8))
print("월별 합:", sum(months.values()), "| 우기(6-8월):", rainy,
      f"= {rainy / total * 100:.1f}%")

fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
xs = list(range(1, 13))
ys = [months.get(m, 0) for m in xs]
colors = [BLUE if m in (6, 7, 8) else GRAY for m in xs]
ax.bar(xs, ys, color=colors, width=0.66)
ax.set_xticks(xs)
ax.set_xticklabels([f"{m}월" for m in xs], fontsize=12, color=INK)
ax.tick_params(axis="y", labelsize=12, colors=INK)
ax.set_title("월별 지반침하 사고 (2018~2025, 1,584건)",
             fontsize=15, fontweight="bold", color=INK, pad=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK)
# 우기 브레이스 주석
peak = max(ys[5:8])
ax.annotate(f"우기(6~8월) {rainy / total * 100:.1f}%",
            xy=(7, peak), xytext=(7, peak * 1.18),
            ha="center", fontsize=14, fontweight="bold", color=BLUE)
ax.set_ylim(0, peak * 1.35)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "monthly_accidents.png"),
            bbox_inches="tight", facecolor="white")
print("saved monthly_accidents.png")
