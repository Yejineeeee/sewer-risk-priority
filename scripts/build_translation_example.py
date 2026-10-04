# -*- coding: utf-8 -*-
"""12p 위험 번역 슬라이드용: 실제 탐지 1건이 위험 점수로 환산되는 과정 그림
DS_000018.jpg → YOLO 탐지(실제) → risk_engine.score_segment(실제 계산)
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyArrow
from matplotlib import font_manager
from ultralytics import YOLO

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))
import risk_engine

import glob as _glob
_pret = []
for _d in (r"C:\Windows\Fonts", os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")):
    _pret += _glob.glob(os.path.join(_d, "Pretendard-*.otf"))
for _p in _pret:
    font_manager.fontManager.addfont(_p)
_names = sorted({font_manager.FontProperties(fname=p).get_name() for p in _pret})
print("등록된 Pretendard 패밀리:", _names)
font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
plt.rcParams["font.family"] = _names + ["Malgun Gothic"]
plt.rcParams["axes.unicode_minus"] = False

# 1) 실제 탐지
img_path = os.path.join(BASE, "dataset", "images", "DS", "DS_000018.jpg")
model = YOLO(os.path.join(BASE, "sewer_best.pt"))
r = model.predict([img_path], conf=0.30, verbose=False)[0]
best_i = int(r.boxes.conf.argmax())
conf = float(r.boxes.conf[best_i])
x1, y1, x2, y2 = [float(v) for v in r.boxes.xyxy[best_i]]
H, W = r.orig_shape
area_ratio = ((x2 - x1) * (y2 - y1)) / (W * H)
cls = model.names[int(r.boxes.cls[best_i])]

# 2) 실제 엔진 계산
det = {"class": cls, "confidence": conf, "bbox_area_ratio": area_ratio}
s_sink, s_flood = risk_engine.score_segment([det])
w_s, w_f, _ = risk_engine.WEIGHTS[cls]
sev = risk_engine.severity(area_ratio)
print(f"cls={cls} conf={conf:.2f} area={area_ratio:.2f} sev={sev:.2f} -> sink={s_sink} flood={s_flood}")

# 3) 그림
BLUE = "#0040cb"
RED = "#D7302F"
INK = "black"
GRAY = "#6b7280"

fig = plt.figure(figsize=(11, 4.4), dpi=200)

# 좌: 탐지 이미지
ax1 = fig.add_axes([0.02, 0.10, 0.34, 0.80])
det_img = mpimg.imread(os.path.join(BASE, "detection_samples", "det_1_DS_000018_conf0.96.png"))
ax1.imshow(det_img)
ax1.axis("off")
ax1.set_title(f"AI 탐지: 토사퇴적(DS) · 확신도 {conf:.2f}", fontsize=13, fontweight="bold", color=INK)

# 중: 환산 항목
ax2 = fig.add_axes([0.38, 0.05, 0.26, 0.90])
ax2.axis("off")
ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)
ax2.text(0.5, 0.97, "위험 점수 환산", fontsize=14, fontweight="bold", ha="center", color=INK)
rows = [
    ("가중치", f"싱크홀 {w_s:.1f} / 침수 {w_f:.1f}", "결함 종류(DS)에 따른 값"),
    ("심각도", f"{sev:.2f}", f"결함 크기(화면의 {area_ratio*100:.0f}%)로 계산"),
    ("신뢰도", f"{conf:.2f}", "AI의 확신도 그대로 반영"),
]
y = 0.80
for name, val, why in rows:
    ax2.text(0.02, y, name, fontsize=12.5, fontweight="bold", color=BLUE)
    ax2.text(0.35, y, val, fontsize=12.5, color=INK)
    ax2.text(0.02, y - 0.09, why, fontsize=10, color=GRAY)
    y -= 0.26
ax2.text(0.5, 0.02, "가중치 × 심각도 × 신뢰도", fontsize=12, ha="center",
         color=INK, style="italic")

# 화살표
for x0 in (0.365, 0.655):
    fig.patches.append(plt.Arrow(x0, 0.5, 0.018, 0, width=0.10,
                                 transform=fig.transFigure, color=BLUE))

# 우: 결과 점수 막대
ax3 = fig.add_axes([0.70, 0.15, 0.28, 0.66])
labels = ["싱크홀 위험", "침수 위험"]
vals = [s_sink, s_flood]
colors = [RED, BLUE]
bars = ax3.barh(labels, vals, color=colors, height=0.5)
for b, v in zip(bars, vals):
    ax3.text(v + 0.02, b.get_y() + b.get_height() / 2, f"{v:.2f}점",
             va="center", fontsize=13, fontweight="bold", color=INK)
ax3.set_xlim(0, max(vals) * 1.35)
ax3.invert_yaxis()
ax3.tick_params(axis="y", labelsize=13, colors=INK, length=0)
ax3.tick_params(axis="x", labelbottom=False, length=0)
for s in ("top", "right", "bottom"):
    ax3.spines[s].set_visible(False)
ax3.spines["left"].set_color(INK)
ax3.set_title("결함 1건의 2축 위험 점수", fontsize=13, fontweight="bold", color=INK)

out = os.path.join(BASE, "risk_translation_example.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("saved:", out)
