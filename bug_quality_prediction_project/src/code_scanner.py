import subprocess
import json
import pandas as pd
import numpy as np
from pathlib import Path
from .quality_score import compute_quality_score
from .pipeline import load_dataset, split_features_target, train_models

def extract_metrics_lizard(file_path: str):
    """
    Extract metrics from Lizard plain text output.
    Returns: dict with LOC, complexity, etc.
    """
    try:
        result = subprocess.run(["lizard", file_path],
                                capture_output=True, text=True)
        lines = result.stdout.splitlines()

        metrics_rows = []
        for line in lines:
            parts = line.strip().split()
            # Ensure first two columns are integers (function rows only)
            if len(parts) >= 6 and parts[0].isdigit() and parts[1].isdigit():
                metrics_rows.append(parts)

        total_loc = sum(int(r[0]) for r in metrics_rows)
        total_complexity = sum(int(r[1]) for r in metrics_rows)
        func_count = len(metrics_rows)
        avg_complexity = (total_complexity / func_count) if func_count else 0

        return {
            "loc": total_loc or 1,
            "v(g)": avg_complexity,
            "branchCount": total_complexity,
            "uniq_Op": func_count,
            "total_Op": total_loc,
            "total_Opnd": max(1, total_loc // 2)
        }
    except Exception as e:
        print("Error parsing lizard output:", e)
        return {
            "loc": 1, "v(g)": 0, "branchCount": 0,
            "uniq_Op": 1, "total_Op": 1, "total_Opnd": 1
        }

def predict_file_bug(file_path: str, dataset_path: str = "data/kc1.csv"):
    """
    Predict bug probability and quality score for a given file.
    Uses RandomForest trained on the chosen dataset (default: kc1).
    """
    # Load dataset & train model
    df, target = load_dataset(Path(dataset_path))
    X, y = split_features_target(df, target)
    models = train_models(X, y)
    rf = models["rf"]["pipe"]   # full pipeline

    # Extract metrics from file
    metrics = extract_metrics_lizard(file_path)
    df_new = pd.DataFrame([metrics])

    # Align with training columns (fill missing with 0)
    df_new = df_new.reindex(columns=X.columns, fill_value=0)

    # Predict
    proba = rf.predict_proba(df_new)[:, 1][0]
    qscore = compute_quality_score([proba], df_new)[0]

    # Return result with metrics
    return {
        "file": file_path,
        "bug_probability": float(proba),
        "quality_score": float(qscore),
        **metrics  # include raw metrics
    }


def predict_folder(folder_path: str, dataset_path: str = "data/kc1.csv", exts=(".py", ".java", ".c", ".cpp")):
    """
    Scan a folder of source code files, predict bug probability + quality score for each,
    and return a DataFrame with metrics.
    """
    folder = Path(folder_path)
    results = []

    for file in folder.rglob("*"):
        if file.suffix.lower() in exts:
            try:
                res = predict_file_bug(str(file), dataset_path)
                results.append(res)
            except Exception as e:
                print(f"⚠️ Skipping {file}: {e}")

    return pd.DataFrame(results)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Predict bug probability for code files")
    parser.add_argument("--file", type=str, help="Path to a single code file")
    parser.add_argument("--folder", type=str, help="Path to a folder of code files")
    parser.add_argument("--dataset", type=str, default="data/kc1.csv", help="Training dataset (kc1/jm1/pc1)")
    parser.add_argument("--out", type=str, help="Optional output CSV for folder mode")
    args = parser.parse_args()

    if args.file:
        result = predict_file_bug(args.file, args.dataset)
        print(json.dumps(result, indent=2))

    elif args.folder:
        df = predict_folder(args.folder, args.dataset)
        print(df.head())
        if args.out:
            df.to_csv(args.out, index=False)
            print(f"\n📄 Saved report to {args.out}")
    else:
        print("Please specify either --file or --folder")

