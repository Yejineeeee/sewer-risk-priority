# -*- coding: utf-8 -*-
"""pothole_seasonality.png — 월별 포트홀 보수 분포 (해빙기 강조)
데이터: data/pothole_seasonality.txt (2023~2025, n=90,065)
스타일: monthly_accidents.png와 동일 (검정 축 · #0040cb 강조)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgunbd.ttf")
font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUE = "#0040cb"
LIGHTBLUE = "#8fa8e8"
GRAY = "#c3c9d2"
INK = "black"

counts = [9860, 10310, 10159, 8866, 8101, 5063, 10008, 6834, 6386, 5233, 3173, 6072]
total = sum(counts)
assert total == 90065, total
thaw = sum(counts[1:4])  # 2~4월

fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
xs = list(range(1, 13))
colors = [BLUE if m in (2, 3, 4) else (LIGHTBLUE if m == 7 else GRAY) for m in xs]
ax.bar(xs, counts, color=colors, width=0.66)
ax.set_xticks(xs)
ax.set_xticklabels([f"{m}월" for m in xs], fontsize=12, color=INK)
ax.tick_params(axis="y", labelsize=12, colors=INK)
ax.set_title("월별 포트홀 보수 (2023~2025, 90,065건)",
             fontsize=15, fontweight="bold", color=INK, pad=12)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK)

peak = max(counts)
ax.annotate(f"해빙기(2~4월) {thaw / total * 100:.1f}%",
            xy=(3, peak), xytext=(3, peak * 1.16),
            ha="center", fontsize=14, fontweight="bold", color=BLUE)
ax.annotate("7월 재상승 11.1%", xy=(7, counts[6]), xytext=(8.6, counts[6] * 1.22),
            ha="center", fontsize=11.5, fontweight="bold", color=LIGHTBLUE)
ax.set_ylim(0, peak * 1.35)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "pothole_seasonality.png"),
            bbox_inches="tight", facecolor="white")
print("saved pothole_seasonality.png | 해빙기:", f"{thaw / total * 100:.1f}%")
