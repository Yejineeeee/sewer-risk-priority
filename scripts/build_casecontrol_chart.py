# -*- coding: utf-8 -*-
"""p15용 사례-대조 검증 차트 — data/retrospective_validation.txt 실측값
250m: 사고 3.80 vs 대조 2.58 (1.47배, p=0.0001)
500m: 사고 11.14 vs 대조 10.39 (1.07배, p=0.2124)
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
GRAY = "#c3c9d2"
INK = "black"

acc = [3.80, 11.14]   # 사고 지점 평균 반복 보수 곳수
ctl = [2.58, 10.39]   # 무작위 대조점 평균

fig, ax = plt.subplots(figsize=(7.6, 4.4), dpi=200)
x = [0, 1]
w = 0.32
b1 = ax.bar([i - w / 2 for i in x], acc, width=w, color=BLUE, label="실제 사고 지점 주변")
b2 = ax.bar([i + w / 2 for i in x], ctl, width=w, color=GRAY, label="무작위 대조점 주변")

for b in list(b1) + list(b2):
    ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.15,
            f"{b.get_height():.2f}곳", ha="center", fontsize=13,
            fontweight="bold", color=INK)

ax.set_xticks(x)
ax.set_xticklabels(["반경 250m", "반경 500m"], fontsize=15, color=INK)
ax.set_ylabel("주변 반복 보수 지점 수 (평균)", fontsize=13, color=INK)
ax.set_ylim(0, 15.5)
ax.tick_params(axis="y", labelsize=12, colors=INK)
ax.legend(fontsize=12, frameon=False, loc="upper left")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK)
ax.set_title("실제 사고 지점 152곳 vs 무작위 대조점 1,520곳", fontsize=15,
             fontweight="bold", color=INK, pad=12)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "casecontrol_validation.png"),
            bbox_inches="tight", facecolor="white")
print("saved casecontrol_validation.png")
