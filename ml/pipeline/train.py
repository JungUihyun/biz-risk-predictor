"""결정 트리 / 랜덤 포레스트 분류 모델 학습 + GridSearchCV 튜닝 + 평가.

사용법 (ml/ 디렉터리에서):
    python -m pipeline.train                    # 튜닝은 5만 건 샘플, 최종 학습은 전체
    python -m pipeline.train --tune-sample 0    # 전체 데이터로 튜닝 (오래 걸림)
"""
import argparse
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from .config import (ARTIFACT_DIR, FEATURE_COLS, FEATURES, PROCESSED_DIR, RISK_BANDS,
                     RISK_QUANTILE, TARGET_COL, TEST_QUARTERS)

SEED = 42

PARAM_GRIDS = {
    "decision_tree": (
        DecisionTreeClassifier(criterion="gini", random_state=SEED),
        {
            "max_depth": [4, 6, 8, 12],
            "min_samples_split": [20, 50, 100],
            "min_samples_leaf": [10, 30, 50],
            "class_weight": [None, "balanced"],
        },
    ),
    "random_forest": (
        RandomForestClassifier(n_estimators=200, criterion="gini", n_jobs=-1, random_state=SEED),
        {
            "max_depth": [8, 12, 16],
            "min_samples_split": [20, 50],
            "min_samples_leaf": [10, 30],
            "class_weight": [None, "balanced"],
        },
    ),
}


def split_and_label(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """시간 기준 분할 후, 학습 구간에서만 업종 대분류별 임곗값을 계산해 레이블을 만든다."""
    cutoff = df["qidx"].max() - TEST_QUARTERS + 1
    train, test = df[df["qidx"] < cutoff].copy(), df[df["qidx"] >= cutoff].copy()

    thresholds = train.groupby("industry_group")["next_close_rate"].quantile(RISK_QUANTILE).to_dict()
    for part in (train, test):
        th = part["industry_group"].map(thresholds)
        part[TARGET_COL] = (part["next_close_rate"] > th).astype(int)
    return train, test, thresholds


def to_xy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    X = df[FEATURE_COLS].to_numpy(dtype=np.float64)
    y = df[TARGET_COL].to_numpy(dtype=np.int64)
    assert X.ndim == 2 and X.shape[1] == len(FEATURE_COLS), f"X shape 오류: {X.shape}"
    assert y.ndim == 1, f"y shape 오류: {y.shape}"
    assert X.shape[0] == y.shape[0], "X와 y의 행 개수가 일치하지 않습니다."
    return X, y


def evaluate(model, X: np.ndarray, y: np.ndarray) -> dict:
    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {
        "accuracy": accuracy_score(y, pred),
        "precision": precision_score(y, pred, zero_division=0),
        "recall": recall_score(y, pred, zero_division=0),
        "f1": f1_score(y, pred, zero_division=0),
        "roc_auc": roc_auc_score(y, proba),
        "confusion_matrix": confusion_matrix(y, pred).tolist(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tune-sample", type=int, default=50_000,
                        help="GridSearchCV에 사용할 샘플 수 (0이면 전체)")
    args = parser.parse_args()

    df = pd.read_parquet(PROCESSED_DIR / "dataset.parquet")
    train, test, thresholds = split_and_label(df)
    X_train, y_train = to_xy(train)
    X_test, y_test = to_xy(test)
    print(f"X_train {X_train.shape} {X_train.dtype} | y_train {y_train.shape} 양성비율 {y_train.mean():.3f}")
    print(f"X_test  {X_test.shape} | y_test 양성비율 {y_test.mean():.3f}")

    tune_idx = np.arange(len(y_train))
    if 0 < args.tune_sample < len(y_train):
        rng = np.random.default_rng(SEED)
        tune_idx = rng.choice(len(y_train), args.tune_sample, replace=False)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    results, best_models = {}, {}

    # 베이스라인: "이번 분기 폐업률이 높으면 다음 분기도 위험" — 모델이 이보다 나아야 의미가 있다
    close_now = test["close_rate"].to_numpy()
    results["baseline_close_rate"] = {"test": {"roc_auc": roc_auc_score(y_test, close_now)}}
    print(f"베이스라인(현재 폐업률만 사용) Test AUC: {results['baseline_close_rate']['test']['roc_auc']:.3f}")
    for name, (estimator, grid) in PARAM_GRIDS.items():
        print(f"\n=== {name} GridSearchCV ===")
        search = GridSearchCV(estimator, grid, scoring="roc_auc", cv=cv, n_jobs=-1, verbose=1)
        search.fit(X_train[tune_idx], y_train[tune_idx])
        model = search.best_estimator_.fit(X_train, y_train)  # 최적 파라미터로 전체 재학습
        metrics = evaluate(model, X_test, y_test)
        results[name] = {"best_params": search.best_params_, "cv_auc": search.best_score_, "test": metrics}
        best_models[name] = model
        print(json.dumps(results[name], indent=2, ensure_ascii=False))

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    model = best_models["random_forest"]
    joblib.dump(model, ARTIFACT_DIR / "model.joblib", compress=3)
    joblib.dump(best_models["decision_tree"], ARTIFACT_DIR / "decision_tree.joblib", compress=3)
    # API 서버는 artifacts 폴더만 있으면 동작하도록 최신 분기 피처도 함께 저장
    latest = pd.read_parquet(PROCESSED_DIR / "latest.parquet")
    latest[["quarter", "dong_code", "dong_name", "industry_code", "industry_name",
            "industry_group", *FEATURE_COLS]].to_parquet(ARTIFACT_DIR / "latest.parquet", index=False)

    meta = {
        "features": FEATURES,
        "thresholds": thresholds,
        "risk_quantile": RISK_QUANTILE,
        "risk_bands": RISK_BANDS,
        "train_quarters": [train["quarter"].min(), train["quarter"].max()],
        "test_quarters": [test["quarter"].min(), test["quarter"].max()],
        "results": results,
        "feature_importances": dict(zip(FEATURE_COLS, model.feature_importances_.round(4).tolist())),
    }
    (ARTIFACT_DIR / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False, default=float))
    print(f"\n모델 저장 완료: {ARTIFACT_DIR}")


if __name__ == "__main__":
    main()
