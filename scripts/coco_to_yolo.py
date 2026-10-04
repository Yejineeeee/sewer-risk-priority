# COCO(AI-Hub Validation 라벨) → YOLO 포맷 변환 + train/val/test 분할
# 사용: python coco_to_yolo.py
# 입력: data/aihub_labels/labels_val/**/*.json + dataset/images/<CODE>/*.jpg
# 출력: dataset/yolo/{images,labels}/{train,val,test}/ + dataset.yaml
import os, glob, json, random, shutil

PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"
LABELS = os.path.join(PROJ, "data", "aihub_labels", "labels_val")
IMAGES = os.path.join(PROJ, "dataset", "images")
OUT = os.path.join(PROJ, "dataset", "yolo")
SPLIT = (0.8, 0.1, 0.1)  # train/val/test
SEED = 42

# 손상 8클래스 + 기타결함 = 검출 대상. EX(예외) 박스는 제외.
# 비손상(PJ/MH/IV)은 박스 없는 네거티브 샘플로 포함.
CLASSES = ["CL", "CC", "SD", "BK", "LP", "JF", "JD", "DS", "ETC"]
NEGATIVE_DIRS = ["PJ", "MH", "IV"]
cls_id = {c: i for i, c in enumerate(CLASSES)}

def collect():
    """이미지 base명 -> (jpg 경로, [yolo 라벨 라인])"""
    entries = {}
    # 서브셋에 실제로 존재하는 이미지 인덱스
    on_disk = {}
    for d in CLASSES + NEGATIVE_DIRS:
        for p in glob.glob(os.path.join(IMAGES, d, "*.jpg")):
            on_disk[os.path.splitext(os.path.basename(p))[0]] = p

    for jf in glob.glob(os.path.join(LABELS, "**", "*.json"), recursive=True):
        d = json.load(open(jf, encoding="utf-8"))
        cats = {c["id"]: c["name"] for c in d.get("categories", [])}
        imgs = {i["id"]: i for i in d.get("images", [])}
        anns_by_img = {}
        for a in d.get("annotations", []):
            anns_by_img.setdefault(a["image_id"], []).append(a)
        for iid, im in imgs.items():
            base = os.path.splitext(im["file_name"])[0]
            if base not in on_disk or base in entries:
                continue
            w, h = im["width"], im["height"]
            lines = []
            for a in anns_by_img.get(iid, []):
                name = cats.get(a["category_id"])
                if name not in cls_id:  # EX, PJ, IN, OUT 박스 제외
                    continue
                x, y, bw, bh = a["bbox"]
                cx, cy = (x + bw / 2) / w, (y + bh / 2) / h
                lines.append(f"{cls_id[name]} {cx:.6f} {cy:.6f} {bw/w:.6f} {bh/h:.6f}")
            entries[base] = (on_disk[base], lines)
    # 라벨 JSON에 없는 네거티브 이미지도 빈 라벨로 포함
    for base, p in on_disk.items():
        if base not in entries and any(os.sep + nd + os.sep in p for nd in NEGATIVE_DIRS):
            entries[base] = (p, [])
    return entries

def main():
    entries = collect()
    print(f"총 {len(entries)}장 (라벨 있는 이미지 + 네거티브)")
    keys = sorted(entries)
    random.seed(SEED)
    random.shuffle(keys)
    n = len(keys)
    cuts = [int(n * SPLIT[0]), int(n * (SPLIT[0] + SPLIT[1]))]
    splits = {"train": keys[:cuts[0]], "val": keys[cuts[0]:cuts[1]], "test": keys[cuts[1]:]}

    for split, ks in splits.items():
        img_d = os.path.join(OUT, "images", split)
        lbl_d = os.path.join(OUT, "labels", split)
        os.makedirs(img_d, exist_ok=True)
        os.makedirs(lbl_d, exist_ok=True)
        for k in ks:
            src, lines = entries[k]
            # 디스크 절약: 복사 대신 하드링크 시도, 실패 시 복사
            dst = os.path.join(img_d, k + ".jpg")
            if not os.path.exists(dst):
                try:
                    os.link(src, dst)
                except OSError:
                    shutil.copy2(src, dst)
            open(os.path.join(lbl_d, k + ".txt"), "w").write("\n".join(lines))
        print(f"{split}: {len(ks)}장")

    yaml = [f"path: {OUT}", "train: images/train", "val: images/val", "test: images/test",
            "names:"] + [f"  {i}: {c}" for i, c in enumerate(CLASSES)]
    open(os.path.join(OUT, "dataset.yaml"), "w", encoding="utf-8").write("\n".join(yaml))
    print("dataset.yaml 작성 완료 →", os.path.join(OUT, "dataset.yaml"))

if __name__ == "__main__":
    main()
