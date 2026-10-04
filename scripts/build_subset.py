# AI-Hub 하수관로 Validation 서브셋 구축
# zip 하나씩: 다운로드 → PNG→JPG 변환 추출 → 즉시 삭제 (디스크 8GB 이하 유지)
import os, sys, io, glob, json, random, shutil, subprocess, tarfile, zipfile

APIKEY = sys.argv[1]
PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"
WORK = os.path.join(PROJ, "_work")
DEST = os.path.join(PROJ, "dataset", "images")
URL = "https://api.aihub.or.kr/down/0.6/139.do"

# (filekey, 클래스코드, 예상GB, 샘플수 None=전부, 기대 이미지수)
JOBS = [
    (42918, "CL", 2, None, 2000), (42920, "SD", 2, None, 2000), (42842, "JF", 3, None, 4000),
    (42843, "JD", 4, None, 4000), (42844, "DS", 4, None, 3000), (42845, "ETC", 4, None, 4000),
    (42922, "LP", 5, None, 4000), (42919, "CC", 6, None, 2000), (42921, "BK", 7, None, 4000),
    (42846, "PJ", 6, 2000, 2000), (42848, "MH", 1, None, 1000), (42849, "IV", 1, None, 1000),
]

def free_gb():
    return shutil.disk_usage("C:\\").free / 1e9

def log(msg):
    print(msg, flush=True)

from PIL import Image

def process(filekey, code, est_gb, sample_n, expected):
    # 재개 지원: 이미 충분히 받아진 클래스는 건너뜀
    outdir_existing = os.path.join(DEST, code)
    n_have = len(glob.glob(os.path.join(outdir_existing, "*.jpg")))
    if n_have >= expected * 0.98:
        log(f"SKIP {code}: 이미 {n_have}장 존재 (완료로 간주)")
        return True
    if free_gb() < est_gb + 2.5:
        log(f"ABORT {code}: 여유 {free_gb():.1f}GB < 필요 {est_gb + 2.5}GB")
        return False
    os.makedirs(WORK, exist_ok=True)
    tar_path = os.path.join(WORK, "dl.tar")
    r = subprocess.run(["curl", "-sS", "-L", "-o", tar_path,
                        "-H", f"apikey:{APIKEY}", f"{URL}?fileSn={filekey}"],
                       capture_output=True, text=True, timeout=7200)
    if r.returncode != 0 or not os.path.exists(tar_path):
        log(f"FAIL {code}: curl rc={r.returncode} {r.stderr[:200]}")
        return False
    size = os.path.getsize(tar_path)
    if size < 10_000_000:  # 에러 응답(작은 tar/텍스트)
        log(f"FAIL {code}: 응답 {size}B — {open(tar_path,'rb').read(200)}")
        os.remove(tar_path)
        return False
    # tar 안의 .part* 를 순서대로 스트리밍 병합
    zip_path = os.path.join(WORK, "data.zip")
    with tarfile.open(tar_path) as t, open(zip_path, "wb") as out:
        members = sorted((m for m in t.getmembers() if m.isfile()),
                         key=lambda m: m.name)
        for m in members:
            f = t.extractfile(m)
            shutil.copyfileobj(f, out, 1024 * 1024)
    os.remove(tar_path)
    # 이미지 추출 + JPG 변환
    outdir = os.path.join(DEST, code)
    os.makedirs(outdir, exist_ok=True)
    n_done = n_err = 0
    with zipfile.ZipFile(zip_path) as z:
        names = [i for i in z.infolist()
                 if not i.is_dir() and i.filename.lower().endswith((".png", ".jpg"))]
        if sample_n and len(names) > sample_n:
            random.seed(42)
            names = random.sample(names, sample_n)
        for info in names:
            try:
                img = Image.open(io.BytesIO(z.read(info))).convert("RGB")
                base = os.path.splitext(os.path.basename(info.filename))[0]
                try:
                    base = base.encode("cp437").decode("cp949")
                except Exception:
                    pass
                img.save(os.path.join(outdir, base + ".jpg"), quality=88)
                n_done += 1
            except Exception:
                n_err += 1
    os.remove(zip_path)
    log(f"DONE {code}: {n_done}장 저장, 오류 {n_err}, 남은 여유 {free_gb():.1f}GB")
    return True

log(f"START 여유 {free_gb():.1f}GB, 대상 {len(JOBS)}개 zip")
ok = 0
for filekey, code, est_gb, sample_n, expected in JOBS:
    log(f"BEGIN {code} (filekey {filekey}, ~{est_gb}GB)")
    if process(filekey, code, est_gb, sample_n, expected):
        ok += 1
shutil.rmtree(WORK, ignore_errors=True)
total = sum(len(glob.glob(os.path.join(DEST, d, "*.jpg")))
            for d in os.listdir(DEST))
log(f"FINISHED {ok}/{len(JOBS)} zip 처리, 총 이미지 {total}장, 여유 {free_gb():.1f}GB")
