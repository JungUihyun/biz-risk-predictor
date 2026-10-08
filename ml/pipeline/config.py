"""프로젝트 전역 설정: 경로, API 서비스명, 피처/레이블 정의."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
ARTIFACT_DIR = ROOT / "ml" / "artifacts"

# 서울 열린데이터광장 OpenAPI (행정동 단위 상권분석서비스)
SEOUL_API_BASE = "http://openapi.seoul.go.kr:8088"
SEOUL_SERVICES = {
    "stores": "VwsmAdstrdStorW",   # 점포-행정동 (점포수, 개업률, 폐업률)
    "sales": "VwsmAdstrdSelngW",   # 추정매출-행정동
    "flpop": "VwsmAdstrdFlpopW",   # 길단위인구-행정동 (업종 구분 없음)
}
PAGE_SIZE = 1000  # 서울 OpenAPI 1회 최대 호출 건수

# 공통 키
KEY_COLS = ["quarter", "dong_code", "industry_code"]

# 노이즈 제거: 점포 수가 너무 적으면 폐업률이 0% / 50% / 100%처럼 튀므로 제외
MIN_STORES = 5

# 레이블: "다음 분기" 폐업률이 같은 업종 대분류 내 상위 30%이면 고위험(1)
# ※ 같은 분기 폐업률을 피처와 레이블에 동시에 쓰면 데이터 누수(leakage)가 발생하므로
#    t분기 피처 → t+1분기 폐업 위험을 예측하는 구조로 설계한다.
RISK_QUANTILE = 0.7

# 시간 기반 분할: 마지막 N개 분기를 테스트셋으로 사용 (미래 데이터로 학습하는 것을 방지)
TEST_QUARTERS = 4

# 위험도 3단계 표시용 확률 구간 (UI: 안정/보통/위험)
RISK_BANDS = [(0.0, 0.35, "안정"), (0.35, 0.6, "보통"), (0.6, 1.01, "위험")]

# 업종 대분류 (서비스업종코드 앞 3자리)
INDUSTRY_GROUPS = {"CS1": "외식업", "CS2": "서비스업", "CS3": "소매업"}

# 모델 입력 피처와 한국어 라벨 (SHAP 시각화/리포트에 사용)
FEATURES = {
    "store_count": "점포 수",
    "similar_store_count": "유사업종 점포 수",
    "franchise_ratio": "프랜차이즈 비율",
    "open_rate": "개업률",
    "close_rate": "현재 분기 폐업률",
    "store_count_qoq": "점포 수 증감률(전분기 대비)",
    "sales_amount": "분기 매출액",
    "sales_per_store": "점포당 매출액",
    "sales_qoq": "매출 증감률(전분기 대비)",
    "weekend_sales_ratio": "주말 매출 비중",
    "has_sales": "매출 데이터 제공 여부",
    "floating_pop": "유동인구",
    "pop_per_store": "점포당 유동인구",
    "weekend_pop_ratio": "주말 유동인구 비중",
    "grp_CS1": "업종: 외식업",
    "grp_CS2": "업종: 서비스업",
    "grp_CS3": "업종: 소매업",
}
FEATURE_COLS = list(FEATURES.keys())
TARGET_COL = "risk_label"

# 서울시 25개 자치구 (행정동코드 앞 5자리)
SEOUL_GU = {
    "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구",
    "11215": "광진구", "11230": "동대문구", "11260": "중랑구", "11290": "성북구",
    "11305": "강북구", "11320": "도봉구", "11350": "노원구", "11380": "은평구",
    "11410": "서대문구", "11440": "마포구", "11470": "양천구", "11500": "강서구",
    "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
    "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구",
    "11740": "강동구",
}
