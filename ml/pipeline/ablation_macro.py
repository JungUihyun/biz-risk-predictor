"""거시경제 피처 추가 효과 비교 실험 (ablation).

train.py가 찾은 랜덤 포레스트 최적 파라미터를 고정하고, 피처 묶음만 바꿔서
같은 시간 기준 분할(학습 2021Q1~2025Q1 → 테스트 2025Q2~2026Q1)로 성능을 비교한다.
결과: 거시지표를 넣을수록 테스트 성능이 조금씩 떨어져 최종 모델에서는 빼기로 했다 (config.MACRO_FEATURES).

사용법 (ml/ 디렉터리에서, train.py 실행 후):
    python -m pipeline.ablation_macro
"""
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, recall_score, roc_auc_score

from .config import ARTIFACT_DIR, FEATURE_COLS, MACRO_COLS, PROCESSED_DIR, TARGET_COL
from .train import SEED, split_and_label

BASE_COLS = FEATURE_COLS  # 최종 모델 피처 (상권 17개)
FEATURE_SETS = {
    "상권 피처만 (17개)": BASE_COLS,
    "+ GDP 성장률": BASE_COLS + ["gdp_growth"],
    "+ GDP, 민간소비": BASE_COLS + ["gdp_growth", "consumption_growth"],
    "+ 거시지표 5개 전체 (22개)": BASE_COLS + MACRO_COLS,
}


def main() -> None:
    meta = json.loads((ARTIFACT_DIR / "meta.json").read_text())
    params = meta["results"]["random_forest"]["best_params"]
    train, test, _ = split_and_label(pd.read_parquet(PROCESSED_DIR / "dataset.parquet"))
    y_tr, y_te = train[TARGET_COL].to_numpy(), test[TARGET_COL].to_numpy()

    # 학습 구간에서 거시지표가 가질 수 있는 서로 다른 값의 개수 = 학습 분기 수
    print(f"학습 분기 수: {train['quarter'].nunique()} → 거시지표는 피처마다 값이 {train['quarter'].nunique()}종류뿐")
    rows = []
    for name, cols in FEATURE_SETS.items():
        model = RandomForestClassifier(n_estimators=200, n_jobs=-1, random_state=SEED, **params)
        model.fit(train[cols].to_numpy(), y_tr)
        proba = model.predict_proba(test[cols].to_numpy())[:, 1]
        pred = (proba >= 0.5).astype(int)
        imp = dict(zip(cols, model.feature_importances_))
        rows.append({
            "피처 묶음": name, "피처 수": len(cols),
            "Test AUC": roc_auc_score(y_te, proba), "Recall": recall_score(y_te, pred), "F1": f1_score(y_te, pred),
            "거시지표 중요도 합": sum(imp.get(c, 0) for c in MACRO_COLS),
        })
        print(rows[-1])

    out = pd.DataFrame(rows).round(4)
    print("\n", out.to_string(index=False))
    (ARTIFACT_DIR / "ablation_macro.json").write_text(out.to_json(orient="records", force_ascii=False, indent=2))


if __name__ == "__main__":
    np.random.seed(SEED)
    main()
