
# Bug Prediction & Code Quality Analysis

A complete pipeline to train ML models for software defect prediction on NASA datasets (kc1, jm1, pc1), 
handle class imbalance, evaluate models, and compute a Code Quality Score (0-100) per module.
Includes optional GitHub API integration for commit-based behavioral metrics.

## Quickstart
```bash
# Create venv (recommended)
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Train on kc1
python -m src.main --data data/kc1.csv --out reports/kc1

# Cross-project eval
python -m src.main --data data/kc1.csv --out reports --cross
```

## Code Quality Score
Score = 100 * (1 - total_risk), where `total_risk` blends model bug probability (70%) and normalized 
static penalties for LOC, complexity, and coupling (30%).

## GitHub Commit Metrics (Optional)
Set `GITHUB_TOKEN` and use `src/github_features.py` to fetch commit churn and activity, 
then join with modules by filename/path and include as extra features in training.
