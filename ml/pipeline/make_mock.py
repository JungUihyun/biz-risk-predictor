"""실제 서울시 OpenAPI와 '같은 컬럼 구조'의 임시(가상) 데이터를 만들어 data/raw/에 저장한다.

인증키 발급·실데이터 수집 전에도 전처리 → 학습 → SHAP → API → 웹 전체 흐름을 개발/시연하기 위한 용도.
- 자치구(25개)와 코드는 실제, 행정동은 가상의 이름("○○1동(가상)")을 사용
- 폐업률은 "과밀·매출 감소·직전 폐업률" 등에 의존하도록 생성해 모델이 학습할 패턴을 심어 둠
- ※ 이 데이터로 얻은 성능·해석 결과는 실제 상권을 의미하지 않음

사용법 (ml/ 디렉터리에서):
    python -m pipeline.make_mock
"""
import numpy as np
import pandas as pd

from .config import RAW_DIR, SEOUL_GU

SEED = 2026
DONGS_PER_GU = 6
QUARTERS = [f"{y}{q}" for y in range(2021, 2026) for q in range(1, 5)][:18]  # 2021Q1 ~ 2025Q2
DAYS = ["MON", "TUES", "WED", "THUR", "FRI", "SAT", "SUN"]
MOCK_MARKER = RAW_DIR / "MOCK_DATA.txt"

# (코드, 업종명, 상대적 점포 규모, 업종 기본 폐업 성향)  ※ 코드는 예시
INDUSTRIES = [
    ("CS100001", "한식음식점", 3.0, 1.0), ("CS100002", "중식음식점", 0.8, 0.9),
    ("CS100003", "일식음식점", 0.6, 1.0), ("CS100004", "양식음식점", 0.6, 1.2),
    ("CS100005", "제과점", 0.4, 0.9), ("CS100006", "패스트푸드점", 0.4, 1.0),
    ("CS100007", "치킨전문점", 0.8, 1.3), ("CS100008", "분식전문점", 0.9, 1.2),
    ("CS100009", "호프-간이주점", 1.0, 1.3), ("CS100010", "커피-음료", 1.6, 1.4),
    ("CS200001", "일반교습학원", 1.0, 0.8), ("CS200002", "미용실", 1.4, 0.7),
    ("CS200003", "네일숍", 0.5, 1.1), ("CS200004", "피부관리실", 0.5, 1.0),
    ("CS200005", "세탁소", 0.5, 0.5), ("CS300001", "슈퍼마켓", 0.7, 0.7),
    ("CS300002", "편의점", 0.9, 0.8), ("CS300003", "일반의류", 0.9, 1.1),
    ("CS300004", "화장품", 0.4, 1.2), ("CS300005", "핸드폰", 0.4, 1.0),
]


def generate() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    stores, sales, flpop = [], [], []

    for gu_code, gu_name in SEOUL_GU.items():
        for n in range(1, DONGS_PER_GU + 1):
            dong_code = f"{gu_code}{500 + n * 10}"
            dong_name = f"{gu_name[:-1]}{n}동(가상)"
            pop_base = rng.lognormal(np.log(1.5e6), 0.5)       # 동별 유동인구 규모
            weekend_pref = rng.uniform(0.22, 0.40)              # 주말 유동인구 비중
            pop_trend = rng.normal(0, 0.01)

            pops = []
            for t, q in enumerate(QUARTERS):
                pop = pop_base * (1 + pop_trend) ** t * rng.normal(1, 0.03)
                pops.append(pop)
                share = np.r_[np.full(5, (1 - weekend_pref) / 5), np.full(2, weekend_pref / 2)]
                flpop.append({"STDR_YYQU_CD": q, "ADSTRD_CD": dong_code, "ADSTRD_CD_NM": dong_name,
                              "TOT_FLPOP_CO": round(pop),
                              **{f"{d}_FLPOP_CO": round(pop * s) for d, s in zip(DAYS, share)}})

            for ind_code, ind_name, scale, base_risk in INDUSTRIES:
                n_stores = max(1, rng.poisson(12 * scale * pop_base / 1.5e6))
                franchise = rng.beta(2, 6)
                sales_per_store = rng.lognormal(np.log(4e7), 0.4)
                close_rate = rng.uniform(2, 6)
                growth = rng.normal(0, 0.04)

                for t, q in enumerate(QUARTERS):
                    open_rate = max(0.0, rng.normal(4 + 3 * (growth > 0), 2))
                    amount = sales_per_store * n_stores
                    stores.append({
                        "STDR_YYQU_CD": q, "ADSTRD_CD": dong_code, "ADSTRD_CD_NM": dong_name,
                        "SVC_INDUTY_CD": ind_code, "SVC_INDUTY_CD_NM": ind_name,
                        "SIMILR_INDUTY_STOR_CO": n_stores + rng.integers(0, 3), "STOR_CO": n_stores,
                        "FRC_STOR_CO": round(n_stores * franchise),
                        "OPBIZ_RT": round(open_rate), "OPBIZ_STOR_CO": round(n_stores * open_rate / 100),
                        "CLSBIZ_RT": round(close_rate), "CLSBIZ_STOR_CO": round(n_stores * close_rate / 100),
                    })
                    if rng.random() > 0.05:  # 실제 데이터처럼 일부 매출 결측
                        wk = rng.uniform(0.15, 0.45)
                        sales.append({
                            "STDR_YYQU_CD": q, "ADSTRD_CD": dong_code, "ADSTRD_CD_NM": dong_name,
                            "SVC_INDUTY_CD": ind_code, "SVC_INDUTY_CD_NM": ind_name,
                            "THSMON_SELNG_AMT": round(amount), "THSMON_SELNG_CO": round(amount / 15000),
                            "MDWK_SELNG_AMT": round(amount * (1 - wk)), "WKEND_SELNG_AMT": round(amount * wk),
                        })

                    # --- 다음 분기 상태 갱신: 폐업률은 현재 분기 상태에 의존 ---
                    crowding = np.log(n_stores / (pops[t] / 1e5) + 0.1)     # 유동인구 대비 과밀도
                    risk = (0.9 * crowding - 6.0 * growth + 0.25 * (close_rate - 4)
                            + 0.8 * franchise * (scale < 1) + 0.5 * (open_rate > 6))
                    close_rate = float(np.clip(base_risk * (4 + 2.2 * risk) + rng.normal(0, 1.5), 0, 40))
                    growth = 0.6 * growth + rng.normal(0, 0.04) - 0.01 * crowding
                    sales_per_store *= (1 + growth)
                    n_stores = max(1, round(n_stores * (1 + (open_rate - close_rate) / 100)))

    return pd.DataFrame(stores), pd.DataFrame(sales), pd.DataFrame(flpop)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    stores, sales, flpop = generate()
    for name, df in [("stores", stores), ("sales", sales), ("flpop", flpop)]:
        df.to_csv(RAW_DIR / f"{name}.csv", index=False, encoding="utf-8-sig")
        print(f"{name}.csv {df.shape}")
    MOCK_MARKER.write_text("이 폴더의 CSV는 make_mock.py로 생성한 임시(가상) 데이터입니다.\n")
    print("※ 임시 데이터입니다. 실제 수집은 python -m pipeline.collect")


if __name__ == "__main__":
    main()
