# E2E 시연: 학습된 YOLO 가중치로 테스트 이미지를 탐지 → risk_engine으로 2축 점수 → 구간 순위
#
# 사용: python demo_e2e.py [가중치경로]  (기본: ../sewer_best.pt)
# 시나리오: test 분할 이미지를 "가상 관로 구간" 여러 개로 묶어 CCTV 조사 1회분을 시뮬레이션.
#   실운영에서는 조사조서의 관로 ID가 이 묶음을 대체한다 (보고서에 명시할 것).
import os, sys, glob, json, random

PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"
sys.path.insert(0, os.path.join(PROJ, "scripts"))
from risk_engine import score_segment, CLASSES

WEIGHTS = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJ, "sewer_best.pt")
TEST_DIR = os.path.join(PROJ, "dataset", "yolo", "images", "test")
N_SEGMENTS = int(os.environ.get("N_SEGMENTS", 8))   # 가상 구간 수
IMGS_PER_SEG = 12       # 구간당 조사 이미지 수
CONF_THRES = 0.4
SAVE_DETS = os.environ.get("SAVE_DETS") == "1"      # 민감도 분석용 원시 탐지 저장

def main():
    from ultralytics import YOLO
    model = YOLO(WEIGHTS)

    imgs = sorted(glob.glob(os.path.join(TEST_DIR, "*.jpg")))
    random.seed(7)
    random.shuffle(imgs)
    segments = {f"관로구간-{i+1:02d}": imgs[i*IMGS_PER_SEG:(i+1)*IMGS_PER_SEG]
                for i in range(N_SEGMENTS)}

    rows = []
    raw = {}
    for seg, files in segments.items():
        dets = []
        results = model.predict(files, conf=CONF_THRES, verbose=False)
        for r in results:
            iw, ih = r.orig_shape[1], r.orig_shape[0]
            for b in r.boxes:
                cls = CLASSES[int(b.cls)]
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                dets.append({"class": cls,
                             "confidence": float(b.conf),
                             "bbox_area_ratio": (x2-x1)*(y2-y1)/(iw*ih)})
        raw[seg] = dets
        s_sink, s_flood = score_segment(dets)
        rows.append({"segment": seg, "n_images": len(files), "n_defects": len(dets),
                     "sinkhole": s_sink, "flood": s_flood,
                     "total": round(s_sink + s_flood, 3),
                     "classes": sorted({d["class"] for d in dets})})

    rows.sort(key=lambda r: -r["total"])
    if SAVE_DETS:
        json.dump(raw, open(os.path.join(PROJ, "segments_raw_detections.json"),
                            "w", encoding="utf-8"), ensure_ascii=False)
    out = os.path.join(PROJ, os.environ.get("OUT_JSON", "demo_segments.json"))
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"{'순위':4s} {'구간':14s} {'결함수':>4s} {'싱크홀':>7s} {'침수':>7s} {'합계':>7s}  검출 클래스")
    for i, r in enumerate(rows, 1):
        print(f"{i:4d} {r['segment']:14s} {r['n_defects']:4d} {r['sinkhole']:7.3f} "
              f"{r['flood']:7.3f} {r['total']:7.3f}  {','.join(r['classes'])}")
    print(f"\n→ 우기 전 보수 권장: 상위 {min(3,len(rows))}개 구간")
    print(f"저장: {out} (지도 시연 레이어 입력용)")

if __name__ == "__main__":
    main()
