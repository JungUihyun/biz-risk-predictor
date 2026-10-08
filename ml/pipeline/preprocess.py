"""원천 데이터(data/raw)를 정제·병합해 학습용 데이터셋(data/processed)을 만든다.

출력:
    data/processed/dataset.parquet   t분기 피처 + t+1분기 폐업률 (학습/평가용)
    data/processed/latest.parquet    가장 최근 분기 피처 (서비스 추론용, 레이블 없음)

사용법 (ml/ 디렉터리에서):
    python -m pipeline.preprocess
"""
import numpy as np
import pandas as pd

from .config import FEATURE_COLS, INDUSTRY_GROUPS, KEY_COLS, MIN_STORES, PROCESSED_DIR, RAW_DIR


def quarter_index(code: pd.Series) -> pd.Series:
    """'20241' → 연속 정수 인덱스 (분기 간 차이 계산용)."""
    code = code.astype(int)
    return (code // 10) * 4 + (code % 10) - 1


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if (RAW_DIR / "MOCK_DATA.txt").exists():
        print("⚠️  data/raw 는 make_mock.py로 만든 임시(가상) 데이터입니다. 결과를 실제 상권 해석에 쓰지 마세요.")
    dtype = {"STDR_YYQU_CD": str, "ADSTRD_CD": str, "SVC_INDUTY_CD": str}
    stores = pd.read_csv(RAW_DIR / "stores.csv", dtype=dtype)
    sales = pd.read_csv(RAW_DIR / "sales.csv", dtype=dtype)
    flpop = pd.read_csv(RAW_DIR / "flpop.csv", dtype=dtype)
    return stores, sales, flpop


def build_stores(stores: pd.DataFrame) -> pd.DataFrame:
    df = stores.rename(columns={
        "STDR_YYQU_CD": "quarter", "ADSTRD_CD": "dong_code", "ADSTRD_CD_NM": "dong_name",
        "SVC_INDUTY_CD": "industry_code", "SVC_INDUTY_CD_NM": "industry_name",
        "STOR_CO": "store_count", "SIMILR_INDUTY_STOR_CO": "similar_store_count",
        "FRC_STOR_CO": "franchise_count", "OPBIZ_RT": "open_rate", "CLSBIZ_RT": "close_rate",
    })
    df = df[KEY_COLS + ["dong_name", "industry_name", "store_count", "similar_store_count",
                        "franchise_count", "open_rate", "close_rate"]].copy()
    df["franchise_ratio"] = df["franchise_count"] / df["similar_store_count"].replace(0, np.nan)
    df["industry_group"] = df["industry_code"].str[:3]
    return df


def build_sales(sales: pd.DataFrame) -> pd.DataFrame:
    df = sales.rename(columns={
        "STDR_YYQU_CD": "quarter", "ADSTRD_CD": "dong_code", "SVC_INDUTY_CD": "industry_code",
        "THSMON_SELNG_AMT": "sales_amount",
    })
    df["weekend_sales_ratio"] = df["WKEND_SELNG_AMT"] / df["sales_amount"].replace(0, np.nan)
    return df[KEY_COLS + ["sales_amount", "weekend_sales_ratio"]]


def build_flpop(flpop: pd.DataFrame) -> pd.DataFrame:
    df = flpop.rename(columns={
        "STDR_YYQU_CD": "quarter", "ADSTRD_CD": "dong_code", "TOT_FLPOP_CO": "floating_pop",
    })
    day_cols = [f"{d}_FLPOP_CO" for d in ["MON", "TUES", "WED", "THUR", "FRI", "SAT", "SUN"]]
    df["weekend_pop_ratio"] = (df["SAT_FLPOP_CO"] + df["SUN_FLPOP_CO"]) / df[day_cols].sum(axis=1)
    return df[["quarter", "dong_code", "floating_pop", "weekend_pop_ratio"]]


def add_qoq(df: pd.DataFrame, col: str, out: str) -> pd.DataFrame:
    """전분기 대비 증감률. 직전 분기 데이터가 없으면 NaN."""
    df = df.sort_values(["dong_code", "industry_code", "qidx"])
    g = df.groupby(["dong_code", "industry_code"])
    prev_val, prev_q = g[col].shift(1), g["qidx"].shift(1)
    valid = (df["qidx"] - prev_q) == 1
    df[out] = np.where(valid, (df[col] - prev_val) / prev_val.replace(0, np.nan), np.nan)
    return df


def build_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    stores, sales, flpop = load_raw()
    df = build_stores(stores)
    df = df.merge(build_sales(sales), on=KEY_COLS, how="left")
    df = df.merge(build_flpop(flpop), on=["quarter", "dong_code"], how="left")
    df["qidx"] = quarter_index(df["quarter"])

    # 파생 피처
    df["sales_per_store"] = df["sales_amount"] / df["store_count"].replace(0, np.nan)
    df["pop_per_store"] = df["floating_pop"] / df["similar_store_count"].replace(0, np.nan)
    df = add_qoq(df, "store_count", "store_count_qoq")
    df = add_qoq(df, "sales_amount", "sales_qoq")
    for grp in INDUSTRY_GROUPS:
        df[f"grp_{grp}"] = (df["industry_group"] == grp).astype(int)

    # 추정매출은 37개 업종(전문서비스·오락 등)에 아예 제공되지 않으므로, 대체 전에 제공 여부를 피처로 남긴다
    df["has_sales"] = df["sales_amount"].notna().astype(int)

    # 결측치 현황 → 같은 분기·업종의 중앙값으로 대체, 그래도 남으면 전체 중앙값
    print("결측치 현황:\n", df[FEATURE_COLS].isna().sum()[lambda s: s > 0])
    for col in FEATURE_COLS:
        df[col] = df.groupby(["quarter", "industry_code"])[col].transform(lambda x: x.fillna(x.median()))
        df[col] = df[col].fillna(df[col].median())
    df[FEATURE_COLS] = df[FEATURE_COLS].replace([np.inf, -np.inf], 0).astype("float64")

    # 다음 분기 폐업률 붙이기 (레이블 원천)
    nxt = df[["dong_code", "industry_code", "qidx", "close_rate"]].copy()
    nxt["qidx"] -= 1
    nxt = nxt.rename(columns={"close_rate": "next_close_rate"})
    df = df.merge(nxt, on=["dong_code", "industry_code", "qidx"], how="left")

    df = df[df["store_count"] >= MIN_STORES]
    latest = df[df["qidx"] == df["qidx"].max()].drop(columns="next_close_rate")
    dataset = df.dropna(subset=["next_close_rate"])
    return dataset, latest


def main() -> None:
    dataset, latest = build_dataset()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    dataset.to_parquet(PROCESSED_DIR / "dataset.parquet", index=False)
    latest.to_parquet(PROCESSED_DIR / "latest.parquet", index=False)
    print(f"dataset: {dataset.shape}, 분기 {dataset['quarter'].min()}~{dataset['quarter'].max()}")
    print(f"latest:  {latest.shape}, 분기 {latest['quarter'].iloc[0]}")


if __name__ == "__main__":
    main()
