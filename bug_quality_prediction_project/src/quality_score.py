
import numpy as np
import pandas as pd

def compute_quality_score(prob_bug: np.ndarray, X: pd.DataFrame, metric_weights=None) -> np.ndarray:
    """Compute a 0-100 Code Quality Score.
    Higher is better. Combines predicted bug probability with static metrics.
    Args:
        prob_bug: array of predicted probabilities for the positive (buggy) class.
        X: feature matrix (DataFrame) containing selected metrics if present.
        metric_weights: optional dict of weights for metrics (keys: 'loc', 'complexity', 'coupling')
    Returns:
        np.ndarray of scores in [0,100].
    """
    if metric_weights is None:
        metric_weights = {'loc': 0.25, 'complexity': 0.45, 'coupling': 0.30}
    # Identify columns
    col_loc_candidates = [c for c in X.columns if c.lower() in ['loc', 'loc_code_and_comment', 'loccodeandcomment'] or c.lower().endswith('loc')]
    col_complexity_candidates = [c for c in X.columns if c.lower() in ['v(g)', 'vg', 'cyclomatic_complexity', 'mccabe']]
    col_coupling_candidates = [c for c in X.columns if c.lower() in ['cbo','coupling','branchcount','rfc']]

    def safe_norm(series):
        s = series.astype(float).replace([np.inf, -np.inf], np.nan).fillna(series.astype(float).median())
        # robust scaling 0..1 using percentile clipping
        lo, hi = np.nanpercentile(s, [5, 95])
        s = np.clip((s - lo) / (hi - lo + 1e-9), 0, 1)
        return s

    loc_pen = safe_norm(X[col_loc_candidates[0]]) if col_loc_candidates else 0.5
    cmp_pen = safe_norm(X[col_complexity_candidates[0]]) if col_complexity_candidates else 0.5
    cpl_pen = safe_norm(X[col_coupling_candidates[0]]) if col_coupling_candidates else 0.5

    # Risk combines model probability and penalties
    model_risk = np.clip(prob_bug, 0, 1)
    structural_risk = (metric_weights['loc']*loc_pen 
                       + metric_weights['complexity']*cmp_pen
                       + metric_weights['coupling']*cpl_pen)
    # Blend risks (weight model higher)
    total_risk = np.clip(0.7*model_risk + 0.3*structural_risk, 0, 1)
    score = 100.0 * (1.0 - total_risk)
    return score
