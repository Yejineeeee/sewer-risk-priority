# -*- coding: utf-8 -*-
"""슬라이드용 CCTV 결함 탐지 샘플 이미지 생성
dataset/images의 DS·JD 이미지에 sewer_best.pt 탐지를 돌려,
confidence가 높은 상위 결과에 바운딩 박스를 그려 저장.
"""
import os, glob
from ultralytics import YOLO
import cv2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = YOLO(os.path.join(BASE, "sewer_best.pt"))

cands = []
for code in ("DS", "JD"):
    imgs = sorted(glob.glob(os.path.join(BASE, "dataset", "images", code, "*.jpg")))[:30]
    cands.extend(imgs)

results = model.predict(cands, conf=0.30, verbose=False)

scored = []
for path, r in zip(cands, results):
    if len(r.boxes) == 0:
        continue
    best = float(r.boxes.conf.max())
    scored.append((best, path, r))
scored.sort(key=lambda x: -x[0])

os.makedirs(os.path.join(BASE, "detection_samples"), exist_ok=True)
for i, (conf, path, r) in enumerate(scored[:6]):
    img = r.plot(line_width=3, font_size=8)  # BGR, 박스+라벨 그려진 배열
    name = os.path.splitext(os.path.basename(path))[0]
    out = os.path.join(BASE, "detection_samples", f"det_{i+1}_{name}_conf{conf:.2f}.png")
    cv2.imwrite(out, img)
    cls_names = [model.names[int(c)] for c in r.boxes.cls]
    print(f"{i+1}. {name}  conf={conf:.2f}  탐지: {cls_names}")
print("저장 폴더:", os.path.join(BASE, "detection_samples"))
