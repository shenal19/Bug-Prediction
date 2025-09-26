import json
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier
import joblib


BUG_TYPE_LABEL_COL = "bug_type"


def _default_feature_columns(df: pd.DataFrame) -> List[str]:
    """Select numeric columns usable for bug-type classification, excluding the label."""
    exclude = {BUG_TYPE_LABEL_COL}
    numeric_cols = [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
    return numeric_cols


def load_bug_type_dataset(path: Path, feature_cols: List[str] = None) -> Tuple[pd.DataFrame, np.ndarray, List[str]]:
    df = pd.read_csv(path)
    if BUG_TYPE_LABEL_COL not in df.columns:
        raise ValueError(f"Dataset must contain '{BUG_TYPE_LABEL_COL}' column with categorical labels.")
    if feature_cols is None:
        feature_cols = _default_feature_columns(df)
    X = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(df[feature_cols].median())
    y = df[BUG_TYPE_LABEL_COL].astype(str).values
    return X, y, feature_cols


def train_bug_type_model(dataset_csv: str, model_out: str) -> dict:
    """Train a supervised bug-type classifier and persist it as a joblib file.
    Dataset schema:
      - numeric features (e.g., loc, v(g), branchCount, uniq_Op, total_Op, total_Opnd, etc.)
      - bug_type (categorical string label)
    """
    X, y, feature_cols = load_bug_type_dataset(Path(dataset_csv))

    # Handle tiny or imbalanced datasets robustly
    unique, counts = np.unique(y, return_counts=True)
    min_count = int(counts.min()) if len(counts) else 0
    do_split = (len(y) >= 8) and (min_count >= 2)

    if do_split:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    else:
        Xtr, ytr = X, y
        Xte, yte = None, None

    pipe = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", RandomForestClassifier(n_estimators=400, random_state=42, n_jobs=-1))
    ])
    pipe.fit(Xtr, ytr)
    if do_split:
        ypred = pipe.predict(Xte)
        report = classification_report(yte, ypred, output_dict=True, zero_division=0)
    else:
        report = {"note": "trained_on_all_data_due_to_small_or_imbalanced_dataset"}

    artifact = {
        "model": pipe,
        "feature_cols": feature_cols,
        "labels": sorted(np.unique(y).tolist()),
        "metrics": report,
    }
    joblib.dump(artifact, model_out)
    return {"model_path": model_out, "feature_cols": feature_cols, "metrics": report}


def predict_bug_type(model_path: str, df_features: pd.DataFrame) -> Tuple[str, float]:
    """Predict bug type and confidence given a trained model artifact and a one-row features DataFrame."""
    artifact = joblib.load(model_path)
    pipe = artifact["model"]
    feature_cols = artifact["feature_cols"]
    df = df_features.reindex(columns=feature_cols, fill_value=0)
    proba = None
    if hasattr(pipe.named_steps.get("clf"), "predict_proba"):
        probas = pipe.predict_proba(df)
        conf = float(np.max(probas[0]))
        label = pipe.classes_[int(np.argmax(probas[0]))]
        return str(label), conf
    # Fallback to decision
    label = pipe.predict(df)[0]
    return str(label), 1.0


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train a supervised bug-type classifier or predict using an existing model.")
    sub = parser.add_subparsers(dest="cmd")

    p_train = sub.add_parser("train", help="Train bug-type model")
    p_train.add_argument("--data", required=True, help="CSV with numeric features + bug_type column")
    p_train.add_argument("--out", required=True, help="Path to save model .joblib")

    p_pred = sub.add_parser("predict", help="Predict bug type for a JSON of features")
    p_pred.add_argument("--model", required=True, help="Path to model .joblib")
    p_pred.add_argument("--features_json", required=True, help="JSON string or path to JSON file with one-row features")

    args = parser.parse_args()
    if args.cmd == "train":
        info = train_bug_type_model(args.data, args.out)
        print(json.dumps({"status": "ok", **info}, indent=2))
    elif args.cmd == "predict":
        payload = args.features_json
        try:
            if Path(payload).exists():
                data = json.loads(Path(payload).read_text())
            else:
                data = json.loads(payload)
        except Exception as e:
            raise SystemExit(f"Failed to parse features_json: {e}")
        df = pd.DataFrame([data])
        label, conf = predict_bug_type(args.model, df)
        print(json.dumps({"bug_type": label, "confidence": conf}, indent=2))
    else:
        parser.print_help()


