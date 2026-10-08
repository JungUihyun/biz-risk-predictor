"""학습된 모델·메타데이터·최신 분기 피처를 로드하고 예측 + SHAP 분해를 수행한다."""
import json
import os
from functools import cached_property
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap

DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "ml" / "artifacts"
SEOUL_GU = {
    "11110": "종로구", "11140": "중구", "11170": "용산구", "11200": "성동구",
    "11215": "광진구", "11230": "동대문구", "11260": "중랑구", "11290": "성북구",
    "11305": "강북구", "11320": "도봉구", "11350": "노원구", "11380": "은평구",
    "11410": "서대문구", "11440": "마포구", "11470": "양천구", "11500": "강서구",
    "11530": "구로구", "11545": "금천구", "11560": "영등포구", "11590": "동작구",
    "11620": "관악구", "11650": "서초구", "11680": "강남구", "11710": "송파구",
    "11740": "강동구",
}


class RiskModel:
    def __init__(self, artifact_dir: Path | None = None):
        self.dir = Path(artifact_dir or os.getenv("ARTIFACT_DIR", DEFAULT_ARTIFACT_DIR))
        self.model = joblib.load(self.dir / "model.joblib")
        self.meta = json.loads((self.dir / "meta.json").read_text())
        self.features: dict[str, str] = self.meta["features"]
        self.feature_cols = list(self.features)
        self.latest = pd.read_parquet(self.dir / "latest.parquet")
        self.latest["probability"] = self.model.predict_proba(self._X(self.latest))[:, 1]
        self.latest["level"] = self.latest["probability"].map(self.level)
        self.explainer = shap.TreeExplainer(self.model)

    def _X(self, df: pd.DataFrame) -> np.ndarray:
        return df[self.feature_cols].to_numpy(dtype=np.float64)

    def level(self, p: float) -> str:
        for lo, hi, name in self.meta["risk_bands"]:
            if lo <= p < hi:
                return name
        return self.meta["risk_bands"][-1][2]

    @cached_property
    def options(self) -> dict:
        df = self.latest
        dongs = df[["dong_code", "dong_name"]].drop_duplicates().sort_values("dong_name")
        gu = []
        for gu_code, gu_name in sorted(SEOUL_GU.items(), key=lambda kv: kv[1]):
            items = dongs[dongs["dong_code"].str.startswith(gu_code)]
            gu.append({"code": gu_code, "name": gu_name,
                       "dongs": [{"code": c, "name": n} for c, n in items.itertuples(index=False)]})
        industries = (df[["industry_code", "industry_name", "industry_group"]]
                      .drop_duplicates().sort_values(["industry_group", "industry_name"]))
        return {
            "quarter": str(df["quarter"].iloc[0]),
            "gu": gu,
            "industries": [{"code": c, "name": n, "group": g} for c, n, g in industries.itertuples(index=False)],
        }

    def map_scores(self, industry_code: str) -> list[dict]:
        rows = self.latest[self.latest["industry_code"] == industry_code]
        return [{"dong_code": r.dong_code, "dong_name": r.dong_name,
                 "probability": round(float(r.probability), 4), "level": r.level}
                for r in rows.itertuples()]

    def diagnose(self, dong_code: str, industry_code: str) -> dict | None:
        match = self.latest[(self.latest["dong_code"] == dong_code)
                            & (self.latest["industry_code"] == industry_code)]
        if match.empty:
            return None
        row = match.iloc[0]
        X = self._X(match)

        sv = self.explainer.shap_values(X)
        if isinstance(sv, list):
            sv = sv[1]
        elif sv.ndim == 3:
            sv = sv[:, :, 1]
        base = self.explainer.expected_value
        base = float(base[1]) if np.ndim(base) else float(base)

        contributions = [
            {"feature": f, "label": self.features[f], "value": float(X[0, i]), "shap": float(sv[0, i])}
            for i, f in enumerate(self.feature_cols) if not f.startswith("grp_")
        ]
        # 업종 원-핫 피처의 기여도는 하나로 묶어서 표시
        grp_shap = float(sum(sv[0, i] for i, f in enumerate(self.feature_cols) if f.startswith("grp_")))
        contributions.append({"feature": "industry_group", "label": "업종 대분류", "value": None, "shap": grp_shap})
        contributions.sort(key=lambda c: abs(c["shap"]), reverse=True)

        return {
            "quarter": str(row["quarter"]),
            "dong_code": dong_code,
            "dong_name": row["dong_name"],
            "gu_name": SEOUL_GU.get(dong_code[:5], ""),
            "industry_code": industry_code,
            "industry_name": row["industry_name"],
            "probability": float(row["probability"]),
            "level": row["level"],
            "base_value": base,
            "contributions": contributions,
        }
