"""한국은행 경제통계시스템(ECOS) Open API에서 분기 거시경제 지표를 수집해 data/raw/macro.csv로 저장한다.

상권 데이터는 행정동 × 업종 단위지만, 거시경제 지표는 "분기"마다 하나의 값(전국)이다.
preprocess.py에서 quarter 기준으로 모든 행에 붙인다.

사용법 (ml/ 디렉터리에서):
    python -m pipeline.collect_macro

인증키: ml/.env의 ECOS_API_KEY (ecos.bok.or.kr > 인증키 신청).
없으면 ECOS 공개 테스트 키 'sample'을 쓴다. sample 키는 1회 10건까지만 주므로 기간을 10개씩 나눠 요청한다.
"""
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

from .config import MACRO_START_QUARTER, RAW_DIR

ECOS_BASE = "https://ecos.bok.or.kr/api/StatisticSearch"
CHUNK = 10  # sample 키 1회 최대 건수 (개인 키여도 그대로 동작)

# 이름: (통계표 코드, 주기, 항목 코드, 설명)
SERIES = {
    "gdp_growth": ("200Y102", "Q", "10111", "실질 GDP 성장률 (계절조정, 전기비, %)"),
    "consumption_growth": ("200Y102", "Q", "10122", "실질 민간소비 증감률 (계절조정, 전기비, %)"),
    "cpi_index": ("901Y009", "Q", "0", "소비자물가지수 총지수 (2020=100)"),
    "base_rate": ("722Y001", "Q", "0101000", "한국은행 기준금리 (%)"),
    "consumer_sentiment": ("511Y002", "M", "FME/99988", "소비자심리지수 (월)"),
}


def periods(cycle: str, start_q: str, end_q: str) -> list[str]:
    """ECOS 기간 코드 목록. Q → '2021Q1', M → '202101'."""
    qs = pd.period_range(pd.Period(start_q, "Q"), pd.Period(end_q, "Q"), freq="Q")
    if cycle == "Q":
        return [f"{p.year}Q{p.quarter}" for p in qs]
    ms = pd.period_range(qs[0].asfreq("M", "start"), qs[-1].asfreq("M", "end"), freq="M")
    return [f"{p.year}{p.month:02d}" for p in ms]


def fetch_series(key: str, stat: str, cycle: str, item: str, start_q: str, end_q: str) -> pd.DataFrame:
    ps = periods(cycle, start_q, end_q)
    rows = []
    for i in range(0, len(ps), CHUNK):
        lo, hi = ps[i], ps[min(i + CHUNK, len(ps)) - 1]
        url = f"{ECOS_BASE}/{key}/json/kr/1/{CHUNK}/{stat}/{cycle}/{lo}/{hi}/{item}"
        body = requests.get(url, timeout=30).json()
        if "StatisticSearch" not in body:
            msg = body.get("RESULT", body)
            if isinstance(msg, dict) and msg.get("CODE") == "INFO-200":  # 해당 기간 데이터 없음 (미발표)
                continue
            raise RuntimeError(f"ECOS 오류 ({stat}/{item} {lo}~{hi}): {msg}")
        rows += body["StatisticSearch"]["row"]
        time.sleep(0.2)
    return pd.DataFrame([{"period": r["TIME"], "value": float(r["DATA_VALUE"])} for r in rows])


def to_quarter(df: pd.DataFrame, cycle: str) -> pd.Series:
    """기간 코드 → '20211' 형식(상권 데이터의 STDR_YYQU_CD와 같음). 월 자료는 분기 평균."""
    if cycle == "Q":
        q = df["period"].str.replace("Q", "", regex=False)
        return pd.Series(df["value"].to_numpy(), index=q)
    p = pd.PeriodIndex(df["period"], freq="M").asfreq("Q")
    q = [f"{x.year}{x.quarter}" for x in p]
    return df.assign(q=q).groupby("q")["value"].mean()


def main() -> None:
    load_dotenv()
    key = os.getenv("ECOS_API_KEY") or "sample"
    end_q = str(pd.Timestamp.today().to_period("Q") - 1)  # 진행 중인 분기는 월 자료가 일부만 있으므로 제외
    print(f"ECOS 수집: {MACRO_START_QUARTER} ~ {end_q} (키: {'개인 키' if key != 'sample' else 'sample'})")

    cols = {}
    for name, (stat, cycle, item, desc) in SERIES.items():
        df = fetch_series(key, stat, cycle, item, MACRO_START_QUARTER, end_q)
        cols[name] = to_quarter(df, cycle)
        print(f"  {name:<20} {len(cols[name]):>3}개 분기  {desc}")

    macro = pd.DataFrame(cols).sort_index()
    macro.index.name = "quarter"
    # 물가는 지수 수준보다 "1년 전 대비 상승률"이 의미 있으므로 4분기 전과 비교
    macro["cpi_yoy"] = (macro["cpi_index"] / macro["cpi_index"].shift(4) - 1) * 100
    macro = macro.drop(columns="cpi_index").round(3)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "macro.csv"
    macro.to_csv(path, encoding="utf-8-sig")
    print(f"저장 완료: {path} {macro.shape}\n{macro.tail(8)}")


if __name__ == "__main__":
    main()
