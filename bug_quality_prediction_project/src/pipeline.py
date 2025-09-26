
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Tuple, Dict, Any
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_class_weight
import matplotlib.pyplot as plt

from .quality_score import compute_quality_score

# graceful imbalance handling
def _rebalance_fit(X, y, clf):
    # Try class weights (works for LR, RF ignores or supports 'balanced')
    classes = np.unique(y)
    weights = compute_class_weight(class_weight='balanced', classes=classes, y=y)
    class_weight = {c:w for c,w in zip(classes, weights)}
    if hasattr(clf, 'class_weight'):
        clf.set_params(class_weight=class_weight)
    clf.fit(X, y)
    return clf

def load_dataset(path: Path) -> Tuple[pd.DataFrame, str]:
    df = pd.read_csv(path) if path.suffix.lower() == '.csv' else pd.read_csv(path, sep=';')
    # Identify target column
    target_candidates = [c for c in df.columns if c.lower() in ['bug', 'bugs', 'defect', 'defects', 'is_buggy', 'label', 'target']]
    if not target_candidates:
        raise ValueError(f"No target column found in {path.name}. Expected one of: bug/bugs/defect/defects/is_buggy/label/target")
    target = target_candidates[0]
    # Normalize boolean/yes-no targets to {0,1}
    if df[target].dtype == bool:
        df[target] = df[target].astype(int)
    elif df[target].dtype == object:
        df[target] = df[target].astype(str).str.strip().str.lower().map({'yes':1, 'true':1, '1':1, 'y':1, 'buggy':1}).fillna(0).astype(int)
    else:
        # if numeric counts, make binary defective if >0
        df[target] = (df[target].astype(float) > 0).astype(int)
    return df, target

def split_features_target(df: pd.DataFrame, target: str):
    X = df.drop(columns=[target])
    y = df[target].values
    # remove non-numeric columns except known identifiers
    keep_cols = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    X = X[keep_cols].copy()
    X = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())
    return X, y

def train_models(X: pd.DataFrame, y: np.ndarray) -> Dict[str, Any]:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=42
    )
    scaler = StandardScaler()
    models = {
        'logreg': LogisticRegression(max_iter=200, solver='lbfgs'),
        'rf': RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
    }
    results = {}
    for name, base_clf in models.items():
        # Build pipeline
        pipe = Pipeline(steps=[('scaler', scaler), ('clf', base_clf)])

        # Train with class balancing
        Xtr_scaled = pipe.named_steps['scaler'].fit_transform(X_train)
        clf = _rebalance_fit(Xtr_scaled, y_train, pipe.named_steps['clf'])

        # Replace in pipeline
        pipe = Pipeline(steps=[('scaler', pipe.named_steps['scaler']), ('clf', clf)])

        # Evaluate
        Xte_scaled = pipe.named_steps['scaler'].transform(X_test)
        y_pred = pipe.named_steps['clf'].predict(Xte_scaled)
        y_proba = pipe.named_steps['clf'].predict_proba(Xte_scaled)[:, 1]

        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(y_test, y_pred)
        try:
            auc = roc_auc_score(y_test, y_proba)
        except Exception:
            auc = float('nan')

        qscore = compute_quality_score(y_proba, pd.DataFrame(X_test, columns=X.columns))

        results[name] = {
            'pipe': pipe,   # ✅ keep real pipeline here
            'metrics': {'classification_report': report,
                        'confusion_matrix': cm.tolist(),
                        'roc_auc': auc},
            'preds': {'y_test': y_test.tolist(),
                      'y_pred': y_pred.tolist(),
                      'y_proba': y_proba.tolist(),
                      'qscore': qscore.tolist()},
            'X_test_columns': X.columns.tolist()
        }
    return results

def plot_and_save(figpath: Path):
    import matplotlib.pyplot as plt
    plt.savefig(figpath, bbox_inches='tight', dpi=160)
    plt.close()

def feature_importance(pipe, X: pd.DataFrame) -> pd.Series:
    clf = pipe.named_steps['clf']
    if hasattr(clf, 'feature_importances_'):
        return pd.Series(clf.feature_importances_, index=X.columns).sort_values(ascending=False)
    elif hasattr(clf, 'coef_'):
        coefs = np.abs(clf.coef_[0])
        return pd.Series(coefs, index=X.columns).sort_values(ascending=False)
    else:
        return pd.Series(np.zeros(len(X.columns)), index=X.columns)

def run_dataset(path: Path, out_dir: Path):
    df, target = load_dataset(path)
    X, y = split_features_target(df, target)
    results = train_models(X, y)

    out_dir.mkdir(parents=True, exist_ok=True)
    # Save metrics and predictions
    serializable = {}
    for k,v in results.items():
        vv = dict(v)
        vv['pipe'] = None
        serializable[k] = vv
    with open(out_dir/'results.json', 'w') as f:
        json.dump(serializable, f, indent=2)
    # Plots (matplotlib only, no seaborn)
    # Confusion matrix and ROC for each model
    import matplotlib.pyplot as plt
    for name, res in results.items():
        y_test = np.array(res['preds']['y_test'])
        y_pred = np.array(res['preds']['y_pred'])
        y_proba = np.array(res['preds']['y_proba'])
        cm = np.array(res['metrics']['confusion_matrix'])
        # Confusion Matrix plot
        plt.figure()
        plt.imshow(cm, interpolation='nearest')
        plt.title(f'Confusion Matrix - {name}')
        plt.xlabel('Predicted'); plt.ylabel('True')
        for (i, j), val in np.ndenumerate(cm):
            plt.text(j, i, int(val), ha='center', va='center')
        plot_and_save(out_dir/f'cm_{name}.png')
        # ROC
        try:
            from sklearn.metrics import RocCurveDisplay
            RocCurveDisplay.from_predictions(y_test, y_proba)
            plt.title(f'ROC - {name}')
            plot_and_save(out_dir/f'roc_{name}.png')
        except Exception:
            pass
        # Feature importance (on train columns)
        import pandas as pd
        if 'feature_importance' in res:
            cols = res['feature_importance']['columns']
            vals = res['feature_importance']['values']
            imp_df = pd.DataFrame({'feature': cols, 'importance': vals}).sort_values('importance', ascending=False)
            imp_df.head(20).to_csv(out_dir/f'feature_importance_top20_{name}.csv', index=False)
        else:
            pass
    return results

def cross_project_eval(paths: Dict[str, Path], out_dir: Path):
    from sklearn.preprocessing import StandardScaler
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    out_dir.mkdir(parents=True, exist_ok=True)
    cp_results = {}
    datasets = {}
    for name, p in paths.items():
        df, target = load_dataset(p)
        X, y = split_features_target(df, target)
        datasets[name] = (X, y)
    for train_name in datasets:
        Xtr, ytr = datasets[train_name]
        for test_name in datasets:
            if test_name == train_name: 
                continue
            Xte, yte = datasets[test_name]
            common = Xtr.columns.intersection(Xte.columns)
            # Fit scaler and classifier on aligned train columns
            scaler = StandardScaler().fit(Xtr[common])
            Xtr_aligned = scaler.transform(Xtr[common])
            clf = RandomForestClassifier(n_estimators=300, random_state=42, n_jobs=-1)
            clf = _rebalance_fit(Xtr_aligned, ytr, clf)
            # Evaluate on test (aligned)
            Xte_aligned = scaler.transform(Xte[common])
            y_proba = clf.predict_proba(Xte_aligned)[:,1]
            y_pred = (y_proba >= 0.5).astype(int)
            rep = classification_report(yte, y_pred, output_dict=True, zero_division=0)
            cm = confusion_matrix(yte, y_pred).tolist()
            try:
                auc = roc_auc_score(yte, y_proba)
            except Exception:
                auc = float('nan')
            cp_results[f'{train_name} -> {test_name}'] = {'report': rep, 'cm': cm, 'roc_auc': auc, 'common_features': common.tolist()}
    with open(out_dir/'cross_project_results.json', 'w') as f:
        json.dump(cp_results, f, indent=2)
    return cp_results
