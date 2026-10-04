# 위험 번역 엔진: 결함 탐지 결과 → 싱크홀×침수 2축 위험 점수
#
# 하이브리드 가중치 (초안 — 팀 검토 후 확정):
#   근거 유형 4종을 결합하고, 각 가중치의 출처를 WEIGHTS 표에 명시한다.
#   [A] 사고 통계  — 국토부 지반침하 표준데이터 1,584건 자체 분석(하수관 손상 41.0%)
#                   + 서울시 발표 세부 원인(접합부 결함 46.3%, 관로 노후 40.8%)
#   [B] 수리 계산  — Manning 공식: 퇴적에 의한 통수 단면 감소 → 통수능 저하
#   [C] 판독 기준  — 환경부 하수관로 상태등급(결함별 심각도 등급 체계)
#   [D] 공학적 판단 — 결함의 물리적 기전(토사 유입 경로, 침입수 등)
import math

CLASSES = ["CL", "CC", "SD", "BK", "LP", "JF", "JD", "DS", "ETC"]

# (싱크홀 가중치, 침수 가중치, 근거)
WEIGHTS = {
    #        sink  flood  근거
    "JF":  (1.00, 0.30, "[A] 접합부 결함=사고 원인 1위(46.3%) / [D] 이음부 틈 → 토사 유실 경로"),
    "JD":  (0.90, 0.30, "[A] 접합부 결함 46.3%에 포함 / [C] 단차는 손상보다 한 등급 아래"),
    "BK":  (0.80, 0.70, "[A] 관로 파손=구조 붕괴 직접 원인 / [B] 붕괴 단면의 통수 장애"),
    "DS":  (0.60, 1.00, "[D] 토사퇴적=주변 지반 토사 유실의 전조 / [B] 통수 단면 직접 감소(Manning)"),
    "LP":  (0.40, 0.60, "[D] 돌출 연결관 주변 공극 형성 / [B] 단면 내 장애물로 통수 저해"),
    "CL":  (0.50, 0.20, "[A] 관로 노후(균열) 40.8% / [D] 길이 균열은 붕괴 전조성 높음"),
    "CC":  (0.50, 0.20, "[A] 관로 노후(균열) 40.8% / [C] 원주 균열은 침하·단차와 연관"),
    "SD":  (0.30, 0.10, "[C] 표면손상은 최저 심각 등급 / 장기 노후 지표"),
    "ETC": (0.20, 0.20, "분류 불능 결함의 보수적 기본값"),
}

def manning_flow_ratio(sediment_ratio: float) -> float:
    """Manning 공식 기반: 원형관에서 퇴적 깊이비(0~1) → 만관 대비 통수능 비율.
    Q ∝ A * R^(2/3), R = A/P. 퇴적된 부분단면을 수치 적분으로 계산."""
    if sediment_ratio <= 0:
        return 1.0
    if sediment_ratio >= 1:
        return 0.0
    # 퇴적 깊이비 h/D에서 남은 유효 단면(위쪽 원호 부분)의 A, P 계산
    h = 1.0 - sediment_ratio          # 유효 수심비 (위쪽 남은 공간)
    theta = 2 * math.acos(1 - 2 * h)  # 중심각
    area = (theta - math.sin(theta)) / 8          # D=1 기준 단면적
    perim = theta / 2                              # 윤변
    r = area / perim
    q = area * r ** (2 / 3)
    # 만관 기준
    area_f, perim_f = math.pi / 4, math.pi
    q_full = area_f * (area_f / perim_f) ** (2 / 3)
    return q / q_full

def severity(bbox_area_ratio: float) -> float:
    """bbox 면적비(결함 크기 프록시) → 0.3~1.0 심각도 배율.
    환경부 판독 기준이 결함 크기로 등급을 나누는 것을 근사."""
    return 0.3 + 0.7 * min(1.0, bbox_area_ratio * 4)

def score_segment(detections):
    """관로 구간 하나의 탐지 리스트 → (싱크홀 점수, 침수 점수).
    detections: [{class, confidence, bbox_area_ratio}, ...]
    confidence를 곱해 AI 불확실성을 점수에 전파한다."""
    s_sink = s_flood = 0.0
    for d in detections:
        w_s, w_f, _ = WEIGHTS[d["class"]]
        sev = severity(d.get("bbox_area_ratio", 0.1))
        conf = d.get("confidence", 1.0)
        s_sink += w_s * sev * conf
        # 토사퇴적은 Manning 감소율로 침수 기여를 물리량 기반 보정
        if d["class"] == "DS":
            loss = 1 - manning_flow_ratio(min(0.9, d.get("bbox_area_ratio", 0.1) * 2))
            s_flood += w_f * (0.5 * sev + 0.5 * loss) * conf
        else:
            s_flood += w_f * sev * conf
    return round(s_sink, 3), round(s_flood, 3)

def sensitivity(detections_by_segment, perturb=0.3, trials=200, top_n=10, seed=42):
    """가중치를 ±perturb 균등 흔들어 Top-N 순위 안정성(평균 유지 비율)을 측정."""
    import random
    rng = random.Random(seed)
    base = {seg: sum(score_segment(d)) for seg, d in detections_by_segment.items()}
    base_top = set(sorted(base, key=base.get, reverse=True)[:top_n])
    keep = 0
    orig = {k: v[:2] for k, v in WEIGHTS.items()}
    for _ in range(trials):
        for k in WEIGHTS:
            w_s, w_f = orig[k]
            _, _, why = WEIGHTS[k]
            WEIGHTS[k] = (w_s * (1 + rng.uniform(-perturb, perturb)),
                          w_f * (1 + rng.uniform(-perturb, perturb)), why)
        sc = {seg: sum(score_segment(d)) for seg, d in detections_by_segment.items()}
        top = set(sorted(sc, key=sc.get, reverse=True)[:top_n])
        keep += len(top & base_top) / top_n
    for k in WEIGHTS:  # 원복
        w_s, w_f = orig[k]
        WEIGHTS[k] = (w_s, w_f, WEIGHTS[k][2])
    return keep / trials

if __name__ == "__main__":
    # 데모: 가상 구간 3개
    demo = {
        "구간A(이음부 다발)": [
            {"class": "JF", "confidence": 0.91, "bbox_area_ratio": 0.15},
            {"class": "JD", "confidence": 0.84, "bbox_area_ratio": 0.10},
        ],
        "구간B(퇴적 심함)": [
            {"class": "DS", "confidence": 0.88, "bbox_area_ratio": 0.35},
        ],
        "구간C(경미)": [
            {"class": "SD", "confidence": 0.77, "bbox_area_ratio": 0.05},
        ],
    }
    for seg, dets in demo.items():
        s, f = score_segment(dets)
        print(f"{seg}: 싱크홀 {s} / 침수 {f}")
    print("Manning 통수능(퇴적 30%):", round(manning_flow_ratio(0.3), 3))
    print("Top 순위 안정성(가중치 ±30%):", round(sensitivity(demo, top_n=2), 3))
