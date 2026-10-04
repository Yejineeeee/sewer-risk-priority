# 분석 로드맵 다이어그램 (계획서 삽입용 PNG) — U자 흐름 6단계
from PIL import Image, ImageDraw, ImageFont

W, H = 1500, 860
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)

bold = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 30)
small = ImageFont.truetype(r"C:\Windows\Fonts\malgun.ttf", 19)

GRAY = (205, 208, 212)
BW, BH = 280, 96          # 박스 크기
TOP_Y, BOT_Y = 200, 540   # 박스 상단 y
XS = [80, 560, 1040]      # 좌측 x (상단 좌→우, 하단도 동일 열)

# ── U자 화살표 밴드 (박스 뒤) ──
band = 56
tc, bc = TOP_Y + BH // 2, BOT_Y + BH // 2      # 행 중심 y
cx = XS[2] + BW - 40                            # 커브 중심 x
d.rectangle([XS[0] + BW // 2, tc - band // 2, cx, tc + band // 2], fill=GRAY)
mid = (tc + bc) // 2
r_out = (bc - tc) // 2 + band // 2
r_in = (bc - tc) // 2 - band // 2
d.pieslice([cx - r_out, mid - r_out, cx + r_out, mid + r_out], -90, 90, fill=GRAY)
d.pieslice([cx - r_in, mid - r_in, cx + r_in, mid + r_in], -90, 90, fill="white")
d.rectangle([cx - r_in - 5, tc - band // 2, cx, bc + band // 2], fill="white")
d.rectangle([XS[0] + BW // 2, tc - band // 2, cx, tc + band // 2], fill=GRAY)  # 상단 밴드 재도포
d.rectangle([XS[0] + BW + 40, bc - band // 2, cx, bc + band // 2], fill=GRAY)  # 하단 밴드
tip_x = XS[0] + BW + 40
d.polygon([(tip_x, bc - band), (tip_x, bc + band), (tip_x - 70, bc)], fill=GRAY)  # 좌향 화살촉

def box(x, y, title):
    d.rectangle([x, y, x + BW, y + BH], fill="white", outline=(30, 30, 30), width=3)
    tw = d.textlength(title, font=bold)
    d.text((x + (BW - tw) / 2, y + BH / 2 - 20), title, font=bold, fill=(15, 15, 15))

def bullets(x, y, lines, align="left"):
    for i, ln in enumerate(lines):
        d.text((x, y + i * 30), "•  " + ln, font=small, fill=(40, 40, 40))

# ── 상단 행 ──
box(XS[0], TOP_Y, "문제 정의")
bullets(XS[0] - 10, TOP_Y - 105, ["노후 하수관발 싱크홀·침수", "보수 우선순위 체계 부재", "명일동 사고(2025) 등"])
box(XS[1], TOP_Y, "데이터 수집")
bullets(XS[1] - 10, TOP_Y - 135, ["지반침하 사고 정보 (국토부 API)", "침수흔적도 공간정보 (서울시)", "포트홀 보수 이력 (서울시)", "하수관 CCTV 이미지 (AI-Hub)"])
box(XS[2], TOP_Y, "데이터 정제")
bullets(XS[2] - 10, TOP_Y - 105, ["좌표계 통일 (WGS84)", "주소 → 좌표 지오코딩", "이종 데이터 공간 결합"])

# ── 하단 행 (흐름은 우→좌) ──
box(XS[2], BOT_Y, "데이터 분석")
bullets(XS[2] - 10, BOT_Y + BH + 18, ["AI 결함 탐지 (YOLO)", "상관·공간 근접성 분석", "2축 위험 점수 산출"])
box(XS[1], BOT_Y, "검증")
bullets(XS[1] - 10, BOT_Y + BH + 18, ["가중치 민감도 분석", "독립 신호 교차 검증", "탐지 오류 교란 실험"])
box(XS[0], BOT_Y, "시각화·제안")
bullets(XS[0] - 10, BOT_Y + BH + 18, ["위험 지도·대시보드 구현", "조사·보수 우선순위 추천", "정책 제언 도출"])

img.save(r"C:\Users\leeju\Desktop\창의적SW(2026)\roadmap.png")
print("saved roadmap.png")
