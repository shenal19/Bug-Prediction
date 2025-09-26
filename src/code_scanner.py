import subprocess
import json
import pandas as pd
import numpy as np
from pathlib import Path
from .quality_score import compute_quality_score, compute_quality_details
from .pipeline import load_dataset, split_features_target, train_models
from .bug_type import predict_bug_type

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


def extract_enhanced_metrics(file_path: str):
    """
    Extract enhanced metrics including code patterns and complexity measures.
    Falls back to lizard if available, otherwise uses file analysis.
    """
    from pathlib import Path
    import re
    
    try:
        # Try lizard first
        lizard_metrics = extract_metrics_lizard(file_path)
        if lizard_metrics["loc"] > 1:  # Valid lizard output
            base_metrics = lizard_metrics
        else:
            # Fallback: analyze file directly
            base_metrics = analyze_file_directly(file_path)
    except:
        base_metrics = analyze_file_directly(file_path)
    
    # Read file for enhanced analysis
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except:
        content = ""
    
    lines = content.split('\n')
    ext = Path(file_path).suffix.lower()
    
    # Enhanced features
    enhanced = {
        **base_metrics,
        "imports_count": 0,
        "includes_count": 0,
        "null_checks": 0,
        "pointer_ops": False,
        "brace_depth": 0,
        "py_max_indent": 0,
        "api_calls": 0,
        "loop_complexity": 0,
        "array_access": False,
        "thread_ops": False,
        "sync_ops": False,
        "error_handling": False,
        "resource_ops": False,
        "nested_conditions": 0,
        "comment_density": 0,
        "function_count": 0,
        "class_count": 0,
        "cyclomatic_complexity": base_metrics.get("v(g)", 0)
    }
    
    # Language-specific analysis
    if ext == ".py":
        enhanced.update(analyze_python_patterns(content, lines))
    elif ext == ".java":
        enhanced.update(analyze_java_patterns(content, lines))
    elif ext in [".c", ".cpp"]:
        enhanced.update(analyze_c_cpp_patterns(content, lines))
    
    # Common patterns
    enhanced.update(analyze_common_patterns(content, lines))
    
    return enhanced


def analyze_file_directly(file_path: str):
    """Fallback file analysis when lizard is not available."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        # Basic metrics
        loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        comments = len([l for l in lines if l.strip().startswith('#')])
        
        # Simple complexity estimation
        complexity = 0
        for line in lines:
            complexity += line.count('if') + line.count('for') + line.count('while') + line.count('switch')
            complexity += line.count('&&') + line.count('||')
        
        return {
            "loc": max(1, loc),
            "v(g)": max(1, complexity / max(1, loc) * 2),
            "branchCount": complexity,
            "uniq_Op": max(1, complexity // 2),
            "total_Op": loc,
            "total_Opnd": max(1, loc // 2)
        }
    except:
        return {"loc": 1, "v(g)": 1, "branchCount": 1, "uniq_Op": 1, "total_Op": 1, "total_Opnd": 1}


def analyze_python_patterns(content: str, lines: list):
    """Analyze Python-specific patterns."""
    features = {}
    
    # Imports
    features["imports_count"] = sum(1 for line in lines if line.strip().startswith(('import ', 'from ')))
    
    # Indentation analysis
    max_indent = 0
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
    features["py_max_indent"] = max_indent
    
    # Functions and classes
    features["function_count"] = sum(1 for line in lines if line.strip().startswith('def '))
    features["class_count"] = sum(1 for line in lines if line.strip().startswith('class '))
    
    # Error handling
    features["error_handling"] = sum(1 for line in lines if any(keyword in line for keyword in ['try:', 'except:', 'finally:']))
    
    return features


def analyze_java_patterns(content: str, lines: list):
    """Analyze Java-specific patterns."""
    features = {}
    
    # Imports
    features["imports_count"] = sum(1 for line in lines if 'import ' in line)
    
    # Null checks
    features["null_checks"] = sum(1 for line in lines if '== null' in line or '!= null' in line)
    
    # API calls
    features["api_calls"] = sum(1 for line in lines if '.' in line and '(' in line)
    
    # Threading
    features["thread_ops"] = sum(1 for line in lines if 'Thread' in line or 'thread' in line)
    features["sync_ops"] = sum(1 for line in lines if 'synchronized' in line or 'lock' in line)
    
    # Functions and classes
    features["function_count"] = sum(1 for line in lines if '(' in line and ')' in line and '{' in line)
    features["class_count"] = sum(1 for line in lines if 'class ' in line)
    
    # Error handling
    features["error_handling"] = sum(1 for line in lines if any(keyword in line for keyword in ['try', 'catch', 'finally']))
    
    return features


def analyze_c_cpp_patterns(content: str, lines: list):
    """Analyze C/C++-specific patterns."""
    features = {}
    
    # Includes
    features["includes_count"] = sum(1 for line in lines if '#include' in line)
    
    # Pointer operations
    features["pointer_ops"] = '->' in content or '*' in content
    
    # API calls
    features["api_calls"] = sum(1 for line in lines if '(' in line and ')' in line)
    
    # Resource operations
    features["resource_ops"] = sum(1 for line in lines if 'malloc' in line or 'new ' in line or 'free(' in line or 'delete' in line)
    
    # Functions
    features["function_count"] = sum(1 for line in lines if '(' in line and ')' in line and '{' in line)
    
    return features


def analyze_common_patterns(content: str, lines: list):
    """Analyze common patterns across languages."""
    features = {}
    
    # Loop complexity
    features["loop_complexity"] = sum(1 for line in lines if any(keyword in line for keyword in ['for ', 'while ', 'do ']))
    
    # Array access
    features["array_access"] = '[' in content and ']' in content
    
    # Nested conditions
    features["nested_conditions"] = sum(1 for line in lines if line.count('if') > 1 or line.count('&&') > 0 or line.count('||') > 0)
    
    # Comment density
    comment_lines = sum(1 for line in lines if line.strip().startswith(('#', '//', '/*')))
    total_lines = len([l for l in lines if l.strip()])
    features["comment_density"] = comment_lines / max(1, total_lines)
    
    # Brace depth analysis
    depth = 0
    max_depth = 0
    for char in content:
        if char == '{':
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == '}':
            depth = max(0, depth - 1)
    features["brace_depth"] = max_depth
    
    return features

def predict_file_bug(file_path: str, dataset_path: str = "data/kc1.csv", bug_type_model: str = None):
    """
    Predict bug probability and quality score for a given file.
    Uses RandomForest trained on the chosen dataset (default: kc1).
    """
    # Load dataset & train model
    df, target = load_dataset(Path(dataset_path))
    X, y = split_features_target(df, target)
    models = train_models(X, y)
    rf = models["rf"]["pipe"]   # full pipeline

    # Extract enhanced metrics from file
    metrics = extract_enhanced_metrics(file_path)
    df_new = pd.DataFrame([metrics])

    # Align with training columns (fill missing with 0)
    df_new = df_new.reindex(columns=X.columns, fill_value=0)

    # Predict
    proba = rf.predict_proba(df_new)[:, 1][0]
    qscore = compute_quality_score([proba], df_new)[0]
    details = compute_quality_details([proba], df_new)[0]

    # Likelihood band
    likelihood_band = details.get("band", "Unknown")

    # Naive bug type heuristic based on dominant factor and language
    dominant = details.get("dominant_factor", "model")
    ext = Path(file_path).suffix.lower()
    if dominant == "complexity":
        bug_type = "logic/complexity-risk"
    elif dominant == "loc":
        bug_type = "size/maintainability-risk"
    elif dominant == "coupling":
        bug_type = "coupling/dependency-risk"
    else:
        bug_type = "historical/model-risk"
    if ext in (".c", ".cpp") and dominant == "complexity":
        bug_type = "pointer/control-flow-risk"
    elif ext == ".py" and dominant == "coupling":
        bug_type = "dynamic-coupling-risk"
    elif ext == ".java" and dominant == "loc":
        bug_type = "bloat/long-class-risk"

    result = {
        "file": file_path,
        "bug_probability": float(proba),
        "likelihood_band": likelihood_band,
        "bug_type": bug_type,
        "quality_score": float(qscore),
        "dominant_factor": dominant,
        "total_risk": details.get("total_risk"),
        **metrics  # include raw metrics
    }

    # If a supervised bug-type model is provided, override heuristic bug_type
    if bug_type_model:
        try:
            label, conf = predict_bug_type(bug_type_model, df_new)
            result["bug_type_supervised"] = label
            result["bug_type_confidence"] = conf
        except Exception as e:
            result["bug_type_supervised_error"] = str(e)
    return result


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
    parser.add_argument("--bugtype_model", type=str, help="Optional path to bug-type .joblib model")
    parser.add_argument("--out", type=str, help="Optional output CSV for folder mode")
    args = parser.parse_args()

    if args.file:
        result = predict_file_bug(args.file, args.dataset, args.bugtype_model)
        print(json.dumps(result, indent=2))

    elif args.folder:
        df = predict_folder(args.folder, args.dataset)
        print(df.head())
        if args.out:
            df.to_csv(args.out, index=False)
            print(f"\n📄 Saved report to {args.out}")
    else:
        print("Please specify either --file or --folder")

