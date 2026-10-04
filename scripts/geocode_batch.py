# VWorld 지오코딩 배치: 반복 보수 지점(3회+) + 서울 침하사고 지점
# 사용: python geocode_batch.py <VWORLD_KEY> <JIS_KEY>
import sys, os, json, time, urllib.request, urllib.parse

VKEY = sys.argv[1]
JKEY = sys.argv[2]
PROJ = r"C:\Users\leeju\Desktop\창의적SW(2026)"

def geocode(addr, gtype="parcel"):
    url = ("https://api.vworld.kr/req/address?service=address&request=getcoord&version=2.0"
           f"&crs=epsg:4326&type={gtype}&format=json&key={VKEY}"
           f"&address={urllib.parse.quote(addr)}")
    try:
        d = json.load(urllib.request.urlopen(url, timeout=15))
        r = d["response"]
        if r["status"] == "OK":
            p = r["result"]["point"]
            return float(p["y"]), float(p["x"])  # lat, lon
    except Exception:
        pass
    return None

def in_seoul(lat, lon):
    return 37.4 < lat < 37.72 and 126.75 < lon < 127.2

# ── 1. 반복 보수 지점 (중간 저장 + 이어하기) ─────────────────────────
locs = json.load(open(os.path.join(PROJ, "data", "repeat_repair_locations.json"), encoding="utf-8"))
rep_out_path = os.path.join(PROJ, "data", "geocoded_repairs.json")
done_path = os.path.join(PROJ, "data", "geocoded_repairs_done.json")  # 실패 포함 처리 완료 주소
out_rep = json.load(open(rep_out_path, encoding="utf-8")) if os.path.exists(rep_out_path) else []
done = set(json.load(open(done_path, encoding="utf-8"))) if os.path.exists(done_path) else set()
fail = len(done) - len(out_rep)
items = [kv for kv in sorted(locs.items(), key=lambda kv: -kv[1]) if kv[0] not in done]
print(f"REPAIRS_RESUME 남은 {len(items)} (완료 {len(done)})", flush=True)

def save_rep():
    json.dump(out_rep, open(rep_out_path, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(sorted(done), open(done_path, "w", encoding="utf-8"), ensure_ascii=False)

consec_fail = 0
recent_fails = []
for i, (addr, cnt) in enumerate(items):
    full = "서울특별시 " + addr
    pt = geocode(full) or geocode(full, "road")
    if pt and in_seoul(*pt):
        done.add(addr)
        out_rep.append({"addr": addr, "count": cnt, "lat": round(pt[0], 6), "lon": round(pt[1], 6)})
        consec_fail = 0
        recent_fails = []
    else:
        consec_fail += 1
        recent_fails.append(addr)
        if consec_fail >= 20:  # 연속 실패 = 네트워크 단절로 판단
            for a in recent_fails:  # 단절 구간 실패는 미처리로 되돌림 (재실행 시 재시도)
                done.discard(a)
            fail -= len(recent_fails) - 1
            save_rep()
            print("NETWORK_ABORT 연속 실패 20회 — 저장 후 중단 (재실행 시 이어서)", flush=True)
            sys.exit(1)
        done.add(addr)
        fail += 1
    if (i + 1) % 200 == 0:
        save_rep()
        print(f"REPAIRS {i+1}/{len(items)} 성공 {len(out_rep)} 실패 {fail}", flush=True)
    time.sleep(0.04)
save_rep()
print(f"REPAIRS_DONE 성공 {len(out_rep)} / 실패 {fail}", flush=True)

# ── 2. 서울 침하사고: 상세 API에서 주소 확보 후 지오코딩 ─────────────
subs = json.load(open(os.path.join(PROJ, "data", "accidents", "subsidence_all.json"), encoding="utf-8"))
seoul = [s for s in subs if s.get("sido") == "서울특별시"]
base = "https://apis.data.go.kr/1613000/undergroundsafetyinfo01/getSubsidenceInfo01"
out_acc, fail2 = [], 0
for i, s in enumerate(seoul):
    try:
        d = json.load(urllib.request.urlopen(
            f"{base}?serviceKey={JKEY}&type=json&sagoNo={s['sagoNo']}", timeout=20))
        rec = d["response"]["body"]["items"][0]
        dong = (rec.get("dong") or "").strip()
        addr = (rec.get("addr") or "").strip().split("(")[0].strip()
        full = " ".join(x for x in ["서울특별시", s["sigungu"], dong, addr] if x)
        pt = geocode(full) or geocode(full, "road")
        if not pt and dong:  # 번지 실패 시 동 단위로 후퇴
            pt = geocode(f"서울특별시 {s['sigungu']} {dong}")
        if pt and in_seoul(*pt):
            out_acc.append({"sagoNo": s["sagoNo"], "gu": s["sigungu"], "date": s.get("sagoDate", ""),
                            "reason": s.get("sagoReason", ""), "lat": round(pt[0], 6),
                            "lon": round(pt[1], 6),
                            "approx": not addr})
        else:
            fail2 += 1
    except Exception:
        fail2 += 1
    time.sleep(0.04)
json.dump(out_acc, open(os.path.join(PROJ, "data", "geocoded_accidents.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
print(f"ACCIDENTS_DONE 성공 {len(out_acc)} / 실패 {fail2}", flush=True)
print("ALL_DONE", flush=True)
