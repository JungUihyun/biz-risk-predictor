"""서울 열린데이터광장 OpenAPI에서 상권분석 원천 데이터를 수집해 data/raw/*.csv로 저장한다.

사용법 (ml/ 디렉터리에서):
    python -m pipeline.collect                 # 전체 수집 (SEOUL_API_KEY 필요)
    python -m pipeline.collect --only flpop    # 일부만 수집
    python -m pipeline.collect --sample        # 'sample' 키로 5건만 받아 구조 확인
"""
import argparse
import os
import time

import pandas as pd
import requests
from dotenv import load_dotenv

from .config import PAGE_SIZE, RAW_DIR, SEOUL_API_BASE, SEOUL_SERVICES


def fetch_page(api_key: str, service: str, start: int, end: int, retries: int = 3) -> dict:
    url = f"{SEOUL_API_BASE}/{api_key}/json/{service}/{start}/{end}/"
    for attempt in range(retries):
        try:
            res = requests.get(url, timeout=30)
            res.raise_for_status()
            if res.text.lstrip().startswith("<"):  # 인증키 오류(INFO-100) 등은 json 요청에도 XML로 응답한다
                raise RuntimeError(f"API 오류: {res.text.strip()[:200]}")
            body = res.json()
            if service not in body:  # 인증 오류 등은 최상위 RESULT로 내려온다
                raise RuntimeError(f"API 오류: {body.get('RESULT', body)}")
            return body[service]
        except (requests.RequestException, ValueError) as e:
            if attempt == retries - 1:
                raise
            print(f"  재시도 {attempt + 1}/{retries}: {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError("unreachable")


def fetch_all(api_key: str, service: str, page_size: int = PAGE_SIZE) -> pd.DataFrame:
    first = fetch_page(api_key, service, 1, page_size)
    total = first["list_total_count"]
    rows = list(first["row"])
    print(f"[{service}] 전체 {total:,}건")

    for start in range(page_size + 1, total + 1, page_size):
        end = min(start + page_size - 1, total)
        rows.extend(fetch_page(api_key, service, start, end)["row"])
        if (start // page_size) % 50 == 0:
            print(f"  {end:,}/{total:,}")
        time.sleep(0.05)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=list(SEOUL_SERVICES), nargs="*")
    parser.add_argument("--sample", action="store_true", help="sample 키로 5건만 조회")
    args = parser.parse_args()

    load_dotenv()
    api_key = "sample" if args.sample else os.getenv("SEOUL_API_KEY")
    if not api_key:
        raise SystemExit("SEOUL_API_KEY 환경변수가 없습니다. ml/.env 파일을 확인하세요.")

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in args.only or SEOUL_SERVICES:
        service = SEOUL_SERVICES[name]
        if args.sample:
            df = pd.DataFrame(fetch_page(api_key, service, 1, 5)["row"])
            print(df.head())
            continue
        df = fetch_all(api_key, service)
        path = RAW_DIR / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"저장 완료: {path} {df.shape}")

    if not args.sample:
        (RAW_DIR / "MOCK_DATA.txt").unlink(missing_ok=True)  # 실데이터로 교체되었음을 표시


if __name__ == "__main__":
    main()
