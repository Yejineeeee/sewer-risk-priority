# -*- coding: utf-8 -*-
"""데이터 수집 슬라이드용: 지하안전정보 API 응답 JSON 스니펫 이미지
실제 subsidence_all.json의 레코드 2건을 코드 카드 형태로 렌더링
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

font_manager.fontManager.addfont(r"C:\Windows\Fonts\malgun.ttf")
font_manager.fontManager.addfont(r"C:\Windows\Fonts\consola.ttf")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = json.load(open(os.path.join(BASE, "data/accidents/subsidence_all.json"), encoding="utf-8"))
# 서울 레코드 중 하수관 손상 사례 하나 + 그 다음 레코드
seoul = [i for i in items if i.get("sido") == "서울특별시" and i.get("sagoReason") == "하수관 손상"]
recs = [seoul[0], seoul[1]]

KEY = "#0040cb"      # 키 이름
STR = "#1a7f37"      # 문자열 값
PUNC = "#57606a"     # 구두점
BG = "#f6f8fa"
BORDER = "#d0d7de"

lines = []  # (들여쓰기, [(텍스트, 색)])
lines.append((0, [("[", PUNC)]))
for ri, r in enumerate(recs):
    lines.append((1, [("{", PUNC)]))
    keys = ["sagoNo", "sido", "sigungu", "sagoReason", "sagoDate"]
    for ki, k in enumerate(keys):
        seg = [(f'"{k}"', KEY), (": ", PUNC), (f'"{r[k]}"', STR)]
        if ki < len(keys) - 1:
            seg.append((",", PUNC))
        lines.append((2, seg))
    lines.append((1, [("}", PUNC), ("," if ri == 0 else "", PUNC)]))
lines.append((1, [("... 1,584건", PUNC)]))
lines.append((0, [("]", PUNC)]))

fig, ax = plt.subplots(figsize=(6.4, 4.6), dpi=200)
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

# 카드 배경
card = plt.Rectangle((0, 0), 100, 100, facecolor=BG, edgecolor=BORDER,
                     linewidth=2, zorder=0)
ax.add_patch(card)
# 상단 타이틀 바
ax.text(4, 94, "GET  지하안전정보시스템 사고정보 API", fontsize=11.5,
        family="Malgun Gothic", color="#57606a", va="top")
ax.plot([0, 100], [89, 89], color=BORDER, lw=1.5)

y = 84
for indent, segs in lines:
    x = 4 + indent * 5
    for text, color in segs:
        if not text:
            continue
        t = ax.text(x, y, text, fontsize=12, family=["Consolas", "Malgun Gothic"],
                    color=color, va="top")
        # 다음 세그먼트 x 위치: 대략 글자폭 추정 (Consolas 기준)
        w = sum(1.62 if ord(c) < 0x2e80 else 2.9 for c in text)
        x += w
    y -= 5.0

fig.tight_layout(pad=0.5)
out = os.path.join(BASE, "api_json_sample.png")
fig.savefig(out, bbox_inches="tight", facecolor="white")
print("saved:", out)
print("record used:", recs[0])
