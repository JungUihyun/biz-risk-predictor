"""TreeSHAP으로 모델을 해석하고 보고서용 그림을 ml/artifacts/figures에 저장한다.

사용법 (ml/ 디렉터리에서):
    python -m pipeline.explain
"""
import json
import platform

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from .config import ARTIFACT_DIR, FEATURE_COLS, FEATURES, PROCESSED_DIR

FIG_DIR = ARTIFACT_DIR / "figures"
# 한글 폰트에 없는 유니코드 마이너스(−) 등은 DejaVu Sans로 대체 표시
plt.rcParams["font.family"] = ["AppleGothic" if platform.system() == "Darwin" else "NanumGothic", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False


def positive_class_shap(explainer: shap.TreeExplainer, X: np.ndarray) -> tuple[np.ndarray, float]:
    """shap 버전에 따라 (n, f, 2) 배열 또는 [neg, pos] 리스트로 반환되는 것을 양성 클래스 기준으로 통일."""
    sv = explainer.shap_values(X)
    if isinstance(sv, list):
        sv = sv[1]
    elif sv.ndim == 3:
        sv = sv[:, :, 1]
    base = explainer.expected_value
    base = float(base[1]) if np.ndim(base) else float(base)
    return sv, base


def main(sample_size: int = 2000) -> None:
    model = joblib.load(ARTIFACT_DIR / "model.joblib")
    df = pd.read_parquet(PROCESSED_DIR / "dataset.parquet")
    sample = df.sample(min(sample_size, len(df)), random_state=42)
    X = sample[FEATURE_COLS].to_numpy(dtype=np.float64)
    labels = [FEATURES[c] for c in FEATURE_COLS]

    explainer = shap.TreeExplainer(model)
    sv, base = positive_class_shap(explainer, X)

    # 예측값 = 기준값 + SHAP 합 검증
    proba = model.predict_proba(X)[:, 1]
    assert np.allclose(base + sv.sum(axis=1), proba, atol=1e-4), "SHAP 가법성 검증 실패"
    print(f"기준값(base value) = {base:.4f}, 가법성 검증 통과")

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    shap.summary_plot(sv, X, feature_names=labels, show=False)
    plt.tight_layout(); plt.savefig(FIG_DIR / "shap_beeswarm.png", dpi=150); plt.close()

    shap.summary_plot(sv, X, feature_names=labels, plot_type="bar", show=False)
    plt.tight_layout(); plt.savefig(FIG_DIR / "shap_bar.png", dpi=150); plt.close()

    # 불순도 기반 feature_importances_ vs 평균 |SHAP| 비교
    compare = pd.DataFrame({
        "impurity_importance": model.feature_importances_,
        "mean_abs_shap": np.abs(sv).mean(axis=0),
    }, index=labels).sort_values("mean_abs_shap")
    compare.plot.barh(figsize=(8, 7), title="불순도 중요도 vs 평균 |SHAP|")
    plt.tight_layout(); plt.savefig(FIG_DIR / "importance_vs_shap.png", dpi=150); plt.close()

    # 고위험 예측 1건에 대한 Waterfall
    i = int(np.argmax(proba))
    row = sample.iloc[i]
    exp = shap.Explanation(values=sv[i], base_values=base, data=X[i], feature_names=labels)
    shap.plots.waterfall(exp, show=False)
    plt.title(f"{row['dong_name']} · {row['industry_name']} ({row['quarter']})")
    plt.tight_layout(); plt.savefig(FIG_DIR / "waterfall_example.png", dpi=150); plt.close()

    (ARTIFACT_DIR / "shap_global.json").write_text(json.dumps(
        {"base_value": base, "mean_abs_shap": dict(zip(FEATURE_COLS, np.abs(sv).mean(axis=0).round(5).tolist()))},
        indent=2, ensure_ascii=False))
    print(f"그림 저장 완료: {FIG_DIR}")


if __name__ == "__main__":
    main()
