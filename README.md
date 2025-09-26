
# Bug Prediction & Code Quality Analysis

A complete pipeline to train ML models for software defect prediction on NASA datasets (kc1, jm1, pc1), 
handle class imbalance, evaluate models, and compute a Code Quality Score (0-100) per module.
Includes optional GitHub API integration for commit-based behavioral metrics.

## Quickstart
```bash
# Create venv (recommended)
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# IMPORTANT: Running from repo root vs. inner package
# - From REPO ROOT (this README's folder): use bug_quality_prediction_project.src.<module>
# - From INNER FOLDER bug_quality_prediction_project\: use src.<module>

# Option A) From REPO ROOT
python -m bug_quality_prediction_project.src.main --data bug_quality_prediction_project/data/kc1.csv --out bug_quality_prediction_project/reports/kc1

# Option B) From INNER FOLDER
cd bug_quality_prediction_project
python -m src.main --data data/kc1.csv --out reports/kc1

# Cross-project eval (REPO ROOT)
cd ..
python -m bug_quality_prediction_project.src.main --data bug_quality_prediction_project/data/kc1.csv --out bug_quality_prediction_project/reports --cross
```

## Predict for Files or Folders (Static Scanning)

```bash
# Single file (REPO ROOT)
python -m bug_quality_prediction_project.src.code_scanner --file bug_quality_prediction_project/sample_project/a.py --dataset bug_quality_prediction_project/data/kc1.csv

# Single file (INNER FOLDER)
cd bug_quality_prediction_project
python -m src.code_scanner --file sample_project/a.py --dataset data/kc1.csv

# Folder scan + CSV output (REPO ROOT)
cd ..
python -m bug_quality_prediction_project.src.code_scanner --folder bug_quality_prediction_project/sample_project --dataset bug_quality_prediction_project/data/kc1.csv --out bug_quality_prediction_project/report.csv

# Folder scan + CSV output (INNER FOLDER)
cd bug_quality_prediction_project
python -m src.code_scanner --folder sample_project --dataset data/kc1.csv --out ../report.csv
```

## Troubleshooting

- ModuleNotFoundError: No module named 'src'
  - Run from the REPO ROOT with full package path: `python -m bug_quality_prediction_project.src.code_scanner ...`
  - Or `cd bug_quality_prediction_project` first, then run: `python -m src.code_scanner ...`
- lizard not found
  - Install the static analysis tool used by the scanner: `pip install lizard`

## Outputs Explained

The scanner now returns, per file:
- `bug_probability` (0..1)
- `likelihood_band` (Excellent/Good/Fair/Poor/Critical)
- `bug_type` (heuristic category, e.g., logic/complexity-risk, coupling/dependency-risk)
- `quality_score` (0..100)
- `dominant_factor` (model/loc/complexity/coupling)
- raw static metrics (`loc`, `v(g)`, `branchCount`, ...)

Use these fields directly in CSV exports for your analysis and paper.

## Supervised Bug-Type Classification (Optional)

Train your own bug-type classifier on labeled data and use it during scanning.

Dataset CSV schema:
- numeric features per file (e.g., `loc`, `v(g)`, `branchCount`, `uniq_Op`, `total_Op`, `total_Opnd`, plus any others you compute)
- `bug_type` column with categorical labels (e.g., `null_deref`, `off_by_one`, `api_misuse`, ...)

Train and save a model:
```bash
# From inner package folder
cd bug_quality_prediction_project
python -m src.bug_type train --data data/your_bugtype_dataset.csv --out reports/bug_type_model.joblib
```

Use the model while scanning:
```bash
# Repo root
python -m bug_quality_prediction_project.src.code_scanner \
  --file bug_quality_prediction_project/sample_project/a.py \
  --dataset bug_quality_prediction_project/data/kc1.csv \
  --bugtype_model bug_quality_prediction_project/reports/bug_type_model.joblib
```

Outputs will include `bug_type_supervised` and `bug_type_confidence` when a model is provided. If the model is absent, the scanner falls back to a heuristic `bug_type` based on dominant risk factors and language.

## No public dataset? Build a realistic synthetic dataset

Generate a comprehensive synthetic dataset with realistic bug patterns for training:

```bash
# From inner package folder
cd bug_quality_prediction_project

# 1) Generate synthetic dataset (1000 samples by default)
python -m src.synthetic_dataset_generator --samples 2000 --out data/synthetic_bugtype.csv

# 2) Train supervised bug-type model
python -m src.bug_type train --data data/synthetic_bugtype.csv --out reports/bug_type_model.joblib

# 3) Use enhanced scanning with supervised bug types
python -m src.code_scanner --file sample_project/a.py --dataset data/kc1.csv --bugtype_model reports/bug_type_model.joblib
```

The synthetic generator creates realistic code with 7 bug types:
- `null_pointer`: Null dereference patterns (Java, C/C++)
- `off_by_one`: Loop/array boundary errors (all languages)
- `memory_leak`: Resource management issues (C/C++)
- `race_condition`: Concurrency problems (Java, C++)
- `api_misuse`: Incorrect API usage (all languages)
- `logic_error`: Complex logical mistakes (all languages)
- `resource_exhaustion`: Resource management problems (all languages)

Each sample includes realistic metrics (LOC, complexity, patterns) and language-specific features.

## Enhanced Feature Extraction

The scanner now extracts 20+ features including:
- **Static metrics**: LOC, cyclomatic complexity, branch count
- **Language patterns**: imports, includes, null checks, pointer ops
- **Code structure**: function/class counts, brace depth, indentation
- **Quality signals**: error handling, comment density, nested conditions
- **Resource patterns**: memory operations, threading, API calls

This provides much richer, more varied predictions suitable for research papers.

## Results Interpretation & Insights

Get detailed analysis and actionable insights from your scan results:

```bash
# Interpret single file result
python -m src.results_interpreter --input single_result.json --output interpretation.json

# Interpret folder scan results
python -m src.results_interpreter --input report.csv --output insights.json
```

The interpreter provides:
- **Quality Assessment**: Band analysis with color coding and action recommendations
- **Risk Analysis**: Breakdown of model vs structural risks, dominant factors
- **Bug Type Analysis**: Detailed explanations of predicted bug types with severity levels
- **Actionable Recommendations**: Specific fixes based on detected issues
- **Research Insights**: Feature importance, anomaly detection, pattern analysis
- **Summary Statistics**: Quality distribution, bug type patterns, correlation analysis

### Understanding Your Results:

**Quality Bands:**
- 🟢 **Excellent (85-100)**: Maintain current practices
- 🟡 **Good (70-84)**: Minor improvements needed  
- 🟠 **Fair (50-69)**: Moderate refactoring recommended
- 🔴 **Poor (30-49)**: Significant refactoring required
- 🚨 **Critical (0-29)**: Immediate attention needed

**Bug Types Explained:**
- `null_pointer`: Missing null checks, unsafe object access
- `off_by_one`: Array/loop boundary errors
- `memory_leak`: Resource management issues
- `race_condition`: Concurrency problems
- `api_misuse`: Incorrect API usage
- `logic_error`: Complex logical mistakes
- `resource_exhaustion`: Resource management problems

**Key Metrics:**
- `quality_score`: 0-100 overall code quality
- `bug_probability`: 0-1 likelihood of bugs
- `dominant_factor`: What drives the risk (model/loc/complexity/coupling)
- `confidence`: How certain the bug type prediction is

## Code Quality Score
Score = 100 * (1 - total_risk), where `total_risk` blends model bug probability (70%) and normalized 
static penalties for LOC, complexity, and coupling (30%).

## GitHub Commit Metrics (Optional)
Set `GITHUB_TOKEN` and use `src/github_features.py` to fetch commit churn and activity, 
then join with modules by filename/path and include as extra features in training.

Requirements
requirements.txt:
pandas
numpy
scikit-learn
matplotlib
requests
Optional:
lizard for static code metrics used by src/code_scanner.py
Troubleshooting
Missing target/label column:
Ensure your CSV contains one of: bug, bugs, defect, defects, is_buggy, label, target
Non-numeric features:
Non-numeric columns are dropped; numeric columns are cleaned, infinities replaced, and NaNs filled with median
Class imbalance:
Handled via class weights during training
lizard not found:
Install with pip install lizard in your active environment
GitHub rate limits:
Set GITHUB_TOKEN to increase limits; reduce max_pages in fetch_commit_metrics if needed
FAQ
Which model should I trust?
Compare ROC AUC and confusion matrices. Random Forest is generally robust; Logistic Regression is more interpretable.
Can I use my own dataset?
Yes. Provide a CSV with a recognized target column and numeric features. Run src.main with --data <your.csv>.
How is the quality score computed if I don’t have complexity/coupling?
Structural terms fallback to neutral penalties; the model probability still drives most of the score.
Roadmap
Add more models (e.g., XGBoost/LightGBM)
Persist trained models to disk and reuse for faster scanning
Richer static metrics (imports/coupling, function-level aggregation)
Improved visualizations and HTML reports