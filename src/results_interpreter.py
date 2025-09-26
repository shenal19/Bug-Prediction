import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import numpy as np


class BugPredictionInterpreter:
    """
    Interprets and explains bug prediction results for research and analysis.
    Provides actionable insights and recommendations.
    """
    
    def __init__(self):
        self.quality_bands = {
            "Excellent": {"min": 85, "max": 100, "color": "🟢", "action": "Maintain current practices"},
            "Good": {"min": 70, "max": 84, "color": "🟡", "action": "Minor improvements needed"},
            "Fair": {"min": 50, "max": 69, "color": "🟠", "action": "Moderate refactoring recommended"},
            "Poor": {"min": 30, "max": 49, "color": "🔴", "action": "Significant refactoring required"},
            "Critical": {"min": 0, "max": 29, "color": "🚨", "action": "Immediate attention needed"}
        }
        
        self.bug_type_explanations = {
            "null_pointer": {
                "description": "Null pointer dereference risks",
                "symptoms": ["Missing null checks", "Unsafe object access"],
                "fixes": ["Add null checks", "Use Optional types", "Defensive programming"],
                "severity": "High"
            },
            "off_by_one": {
                "description": "Array/loop boundary errors",
                "symptoms": ["Index out of bounds", "Incorrect loop conditions"],
                "fixes": ["Review loop conditions", "Use proper array bounds", "Add boundary checks"],
                "severity": "Medium"
            },
            "memory_leak": {
                "description": "Resource management issues",
                "symptoms": ["Unfreed memory", "Resource exhaustion"],
                "fixes": ["Use RAII", "Proper cleanup", "Smart pointers"],
                "severity": "High"
            },
            "race_condition": {
                "description": "Concurrency problems",
                "symptoms": ["Data races", "Inconsistent state"],
                "fixes": ["Synchronization", "Thread-safe data structures", "Locking mechanisms"],
                "severity": "Critical"
            },
            "api_misuse": {
                "description": "Incorrect API usage",
                "symptoms": ["Missing error handling", "Wrong parameters"],
                "fixes": ["Read documentation", "Add error handling", "Validate inputs"],
                "severity": "Medium"
            },
            "logic_error": {
                "description": "Complex logical mistakes",
                "symptoms": ["Incorrect conditions", "Flawed algorithms"],
                "fixes": ["Code review", "Unit testing", "Algorithm verification"],
                "severity": "High"
            },
            "resource_exhaustion": {
                "description": "Resource management problems",
                "symptoms": ["Memory/CPU exhaustion", "Infinite loops"],
                "fixes": ["Resource limits", "Timeout mechanisms", "Efficient algorithms"],
                "severity": "Critical"
            }
        }
    
    def interpret_single_file(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Interpret results for a single file."""
        interpretation = {
            "file": result.get("file", "unknown"),
            "overall_assessment": self._assess_overall_quality(result),
            "risk_analysis": self._analyze_risks(result),
            "bug_type_analysis": self._analyze_bug_type(result),
            "recommendations": self._generate_recommendations(result),
            "metrics_breakdown": self._breakdown_metrics(result),
            "research_insights": self._extract_research_insights(result)
        }
        return interpretation
    
    def interpret_folder_results(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Interpret results for a folder scan."""
        if df.empty:
            return {"error": "No files analyzed"}
        
        interpretation = {
            "summary_statistics": self._compute_summary_stats(df),
            "quality_distribution": self._analyze_quality_distribution(df),
            "bug_type_distribution": self._analyze_bug_type_distribution(df),
            "risk_patterns": self._identify_risk_patterns(df),
            "file_rankings": self._rank_files_by_risk(df),
            "correlation_analysis": self._analyze_correlations(df),
            "research_findings": self._extract_research_findings(df)
        }
        return interpretation
    
    def _assess_overall_quality(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall code quality."""
        quality_score = result.get("quality_score", 0)
        likelihood_band = result.get("likelihood_band", "Unknown")
        bug_prob = result.get("bug_probability", 0)
        
        band_info = self.quality_bands.get(likelihood_band, {"min": 0, "max": 100, "color": "⚪", "action": "Unknown"})
        
        return {
            "quality_score": quality_score,
            "band": likelihood_band,
            "band_info": band_info,
            "bug_probability": bug_prob,
            "risk_level": self._determine_risk_level(bug_prob),
            "confidence": self._assess_confidence(result)
        }
    
    def _analyze_risks(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze risk factors."""
        dominant_factor = result.get("dominant_factor", "unknown")
        total_risk = result.get("total_risk", 0)
        
        risk_factors = {
            "model_risk": result.get("total_risk", 0) * 0.7,  # Approximate
            "structural_risk": result.get("total_risk", 0) * 0.3,  # Approximate
            "dominant_factor": dominant_factor,
            "loc_risk": self._assess_loc_risk(result),
            "complexity_risk": self._assess_complexity_risk(result),
            "coupling_risk": self._assess_coupling_risk(result)
        }
        
        return risk_factors
    
    def _analyze_bug_type(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze bug type predictions."""
        heuristic_type = result.get("bug_type", "unknown")
        supervised_type = result.get("bug_type_supervised", None)
        confidence = result.get("bug_type_confidence", 0)
        
        analysis = {
            "heuristic_prediction": heuristic_type,
            "supervised_prediction": supervised_type,
            "confidence": confidence,
            "agreement": heuristic_type == supervised_type if supervised_type else "N/A",
            "explanation": self._explain_bug_type(supervised_type or heuristic_type),
            "severity": self._get_bug_type_severity(supervised_type or heuristic_type)
        }
        
        return analysis
    
    def _generate_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Quality-based recommendations
        quality_score = result.get("quality_score", 0)
        if quality_score < 50:
            recommendations.append("🔴 CRITICAL: Immediate refactoring required")
        elif quality_score < 70:
            recommendations.append("🟠 HIGH: Significant improvements needed")
        elif quality_score < 85:
            recommendations.append("🟡 MEDIUM: Minor improvements recommended")
        
        # Bug type specific recommendations
        bug_type = result.get("bug_type_supervised") or result.get("bug_type", "")
        if bug_type in self.bug_type_explanations:
            bug_info = self.bug_type_explanations[bug_type]
            recommendations.append(f"🐛 BUG TYPE: {bug_info['description']} - {bug_info['fixes'][0]}")
        
        # Feature-based recommendations
        if result.get("loc", 0) > 200:
            recommendations.append("📏 SIZE: File is too large - consider splitting")
        
        if result.get("v(g)", 0) > 10:
            recommendations.append("🧩 COMPLEXITY: High cyclomatic complexity - simplify logic")
        
        if result.get("brace_depth", 0) > 4:
            recommendations.append("🔗 NESTING: Deep nesting - extract methods")
        
        if result.get("comment_density", 0) < 0.1:
            recommendations.append("📝 DOCUMENTATION: Add more comments")
        
        if not result.get("error_handling", False):
            recommendations.append("⚠️ ERROR HANDLING: Add proper error handling")
        
        return recommendations
    
    def _breakdown_metrics(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Break down technical metrics."""
        return {
            "size_metrics": {
                "lines_of_code": result.get("loc", 0),
                "function_count": result.get("function_count", 0),
                "class_count": result.get("class_count", 0)
            },
            "complexity_metrics": {
                "cyclomatic_complexity": result.get("v(g)", 0),
                "branch_count": result.get("branchCount", 0),
                "nested_conditions": result.get("nested_conditions", 0),
                "loop_complexity": result.get("loop_complexity", 0)
            },
            "quality_metrics": {
                "comment_density": result.get("comment_density", 0),
                "error_handling": result.get("error_handling", 0),
                "brace_depth": result.get("brace_depth", 0),
                "py_max_indent": result.get("py_max_indent", 0)
            },
            "pattern_metrics": {
                "imports_count": result.get("imports_count", 0),
                "api_calls": result.get("api_calls", 0),
                "null_checks": result.get("null_checks", 0),
                "pointer_ops": result.get("pointer_ops", False)
            }
        }
    
    def _extract_research_insights(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights for research purposes."""
        return {
            "prediction_confidence": result.get("bug_type_confidence", 0),
            "feature_importance": self._estimate_feature_importance(result),
            "anomaly_detection": self._detect_anomalies(result),
            "pattern_analysis": self._analyze_patterns(result),
            "research_metrics": {
                "bug_probability": result.get("bug_probability", 0),
                "quality_score": result.get("quality_score", 0),
                "dominant_factor": result.get("dominant_factor", "unknown"),
                "total_risk": result.get("total_risk", 0)
            }
        }
    
    def _compute_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Compute summary statistics for folder results."""
        return {
            "total_files": len(df),
            "avg_quality_score": df['quality_score'].mean(),
            "avg_bug_probability": df['bug_probability'].mean(),
            "quality_distribution": df['likelihood_band'].value_counts().to_dict(),
            "high_risk_files": len(df[df['quality_score'] < 50]),
            "excellent_files": len(df[df['quality_score'] >= 85])
        }
    
    def _analyze_quality_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze quality score distribution."""
        return {
            "mean": df['quality_score'].mean(),
            "median": df['quality_score'].median(),
            "std": df['quality_score'].std(),
            "min": df['quality_score'].min(),
            "max": df['quality_score'].max(),
            "quartiles": df['quality_score'].quantile([0.25, 0.5, 0.75]).to_dict()
        }
    
    def _analyze_bug_type_distribution(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze bug type distribution."""
        if 'bug_type_supervised' in df.columns:
            return df['bug_type_supervised'].value_counts().to_dict()
        else:
            return df['bug_type'].value_counts().to_dict()
    
    def _identify_risk_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify patterns in high-risk files."""
        high_risk = df[df['quality_score'] < 50]
        
        if high_risk.empty:
            return {"message": "No high-risk files found"}
        
        return {
            "count": len(high_risk),
            "common_bug_types": high_risk['bug_type'].value_counts().head(3).to_dict(),
            "avg_complexity": high_risk['v(g)'].mean(),
            "avg_loc": high_risk['loc'].mean(),
            "common_patterns": self._find_common_patterns(high_risk)
        }
    
    def _rank_files_by_risk(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Rank files by risk level."""
        df_sorted = df.sort_values('quality_score').head(10)
        
        rankings = []
        for idx, row in df_sorted.iterrows():
            rankings.append({
                "file": row['file'],
                "quality_score": row['quality_score'],
                "bug_probability": row['bug_probability'],
                "bug_type": row.get('bug_type_supervised', row.get('bug_type', 'unknown')),
                "priority": "HIGH" if row['quality_score'] < 50 else "MEDIUM" if row['quality_score'] < 70 else "LOW"
            })
        
        return rankings
    
    def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze correlations between metrics and quality."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = df[numeric_cols].corr()['quality_score'].sort_values(ascending=False)
        
        return {
            "top_positive_correlations": correlations.head(5).to_dict(),
            "top_negative_correlations": correlations.tail(5).to_dict(),
            "insights": self._interpret_correlations(correlations)
        }
    
    def _extract_research_findings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Extract findings for research papers."""
        return {
            "dataset_size": len(df),
            "prediction_accuracy": self._estimate_accuracy(df),
            "feature_importance_ranking": self._rank_features(df),
            "quality_trends": self._analyze_quality_trends(df),
            "bug_type_effectiveness": self._assess_bug_type_effectiveness(df),
            "model_performance": self._assess_model_performance(df)
        }
    
    # Helper methods
    def _determine_risk_level(self, bug_prob: float) -> str:
        if bug_prob > 0.7:
            return "CRITICAL"
        elif bug_prob > 0.4:
            return "HIGH"
        elif bug_prob > 0.2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_confidence(self, result: Dict[str, Any]) -> str:
        confidence = result.get("bug_type_confidence", 0)
        if confidence > 0.8:
            return "HIGH"
        elif confidence > 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_loc_risk(self, result: Dict[str, Any]) -> str:
        loc = result.get("loc", 0)
        if loc > 300:
            return "HIGH"
        elif loc > 150:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_complexity_risk(self, result: Dict[str, Any]) -> str:
        complexity = result.get("v(g)", 0)
        if complexity > 15:
            return "HIGH"
        elif complexity > 8:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_coupling_risk(self, result: Dict[str, Any]) -> str:
        imports = result.get("imports_count", 0) + result.get("includes_count", 0)
        if imports > 10:
            return "HIGH"
        elif imports > 5:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _explain_bug_type(self, bug_type: str) -> str:
        if bug_type in self.bug_type_explanations:
            return self.bug_type_explanations[bug_type]["description"]
        return "Unknown bug type"
    
    def _get_bug_type_severity(self, bug_type: str) -> str:
        if bug_type in self.bug_type_explanations:
            return self.bug_type_explanations[bug_type]["severity"]
        return "Unknown"
    
    def _estimate_feature_importance(self, result: Dict[str, Any]) -> Dict[str, str]:
        """Estimate which features are most important for this prediction."""
        importance = {}
        
        if result.get("v(g)", 0) > 10:
            importance["complexity"] = "HIGH"
        if result.get("loc", 0) > 200:
            importance["size"] = "HIGH"
        if result.get("imports_count", 0) + result.get("includes_count", 0) > 8:
            importance["coupling"] = "HIGH"
        if result.get("brace_depth", 0) > 4:
            importance["nesting"] = "HIGH"
        
        return importance
    
    def _detect_anomalies(self, result: Dict[str, Any]) -> List[str]:
        """Detect anomalous patterns in the results."""
        anomalies = []
        
        if result.get("quality_score", 0) > 90 and result.get("bug_probability", 0) > 0.5:
            anomalies.append("High quality score but high bug probability")
        
        if result.get("loc", 0) > 500 and result.get("function_count", 0) < 5:
            anomalies.append("Very large file with few functions")
        
        if result.get("v(g)", 0) > 20 and result.get("comment_density", 0) < 0.05:
            anomalies.append("High complexity with low documentation")
        
        return anomalies
    
    def _analyze_patterns(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code patterns."""
        return {
            "has_error_handling": bool(result.get("error_handling", 0)),
            "has_comments": result.get("comment_density", 0) > 0.1,
            "is_well_structured": result.get("brace_depth", 0) < 4,
            "has_proper_documentation": result.get("comment_density", 0) > 0.2,
            "follows_best_practices": self._assess_best_practices(result)
        }
    
    def _assess_best_practices(self, result: Dict[str, Any]) -> bool:
        """Assess if code follows best practices."""
        checks = [
            result.get("error_handling", 0) > 0,
            result.get("comment_density", 0) > 0.1,
            result.get("brace_depth", 0) < 4,
            result.get("v(g)", 0) < 10,
            result.get("loc", 0) < 200
        ]
        return sum(checks) >= 3
    
    def _find_common_patterns(self, high_risk_df: pd.DataFrame) -> List[str]:
        """Find common patterns in high-risk files."""
        patterns = []
        
        if high_risk_df['v(g)'].mean() > 15:
            patterns.append("High cyclomatic complexity")
        if high_risk_df['loc'].mean() > 300:
            patterns.append("Large file sizes")
        if high_risk_df['comment_density'].mean() < 0.05:
            patterns.append("Low documentation")
        if high_risk_df['error_handling'].sum() == 0:
            patterns.append("No error handling")
        
        return patterns
    
    def _interpret_correlations(self, correlations: pd.Series) -> List[str]:
        """Interpret correlation findings."""
        insights = []
        
        if 'comment_density' in correlations and correlations['comment_density'] > 0.3:
            insights.append("Well-documented code tends to have higher quality scores")
        
        if 'v(g)' in correlations and correlations['v(g)'] < -0.3:
            insights.append("High complexity correlates with lower quality scores")
        
        if 'loc' in correlations and correlations['loc'] < -0.2:
            insights.append("Larger files tend to have lower quality scores")
        
        return insights
    
    def _estimate_accuracy(self, df: pd.DataFrame) -> float:
        """Estimate prediction accuracy based on consistency."""
        if 'bug_type_supervised' in df.columns and 'bug_type' in df.columns:
            agreement = (df['bug_type_supervised'] == df['bug_type']).mean()
            return agreement
        return 0.0
    
    def _rank_features(self, df: pd.DataFrame) -> Dict[str, float]:
        """Rank features by importance."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = df[numeric_cols].corr()['quality_score'].abs().sort_values(ascending=False)
        return correlations.head(10).to_dict()
    
    def _analyze_quality_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze quality trends across files."""
        return {
            "quality_variance": df['quality_score'].var(),
            "quality_range": df['quality_score'].max() - df['quality_score'].min(),
            "consistency": "HIGH" if df['quality_score'].std() < 20 else "LOW"
        }
    
    def _assess_bug_type_effectiveness(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess effectiveness of bug type classification."""
        if 'bug_type_supervised' not in df.columns:
            return {"message": "No supervised bug type data available"}
        
        return {
            "unique_types": df['bug_type_supervised'].nunique(),
            "most_common": df['bug_type_supervised'].mode().iloc[0] if not df['bug_type_supervised'].empty else "None",
            "distribution_balance": df['bug_type_supervised'].value_counts().std()
        }
    
    def _assess_model_performance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Assess overall model performance."""
        return {
            "avg_confidence": df.get('bug_type_confidence', pd.Series([0])).mean(),
            "prediction_consistency": df['quality_score'].std(),
            "coverage": len(df[df['quality_score'] > 0]) / len(df) if len(df) > 0 else 0
        }


def _read_file_with_encoding_fallback(file_path: str) -> str:
    """Read file with automatic encoding detection and BOM handling."""
    # Read as bytes first
    with open(file_path, 'rb') as f:
        raw_bytes = f.read()
    
    # Remove BOM if present
    if raw_bytes.startswith(b'\xef\xbb\xbf'):  # UTF-8 BOM
        raw_bytes = raw_bytes[3:]
    elif raw_bytes.startswith(b'\xff\xfe'):  # UTF-16 LE BOM
        raw_bytes = raw_bytes[2:]
    elif raw_bytes.startswith(b'\xfe\xff'):  # UTF-16 BE BOM
        raw_bytes = raw_bytes[2:]
    
    # Try different encodings
    encodings = ['utf-8', 'utf-16', 'latin-1', 'cp1252']
    
    for encoding in encodings:
        try:
            content = raw_bytes.decode(encoding)
            return content.strip()
        except UnicodeDecodeError:
            continue
    
    # If all fail, use utf-8 with errors='replace'
    return raw_bytes.decode('utf-8', errors='replace').strip()


def interpret_results(input_path: str, output_path: str = None):
    """
    Main function to interpret results from CSV or JSON file.
    
    Args:
        input_path: Path to CSV file with scan results or JSON file with single result
        output_path: Optional path to save interpretation results
    """
    interpreter = BugPredictionInterpreter()
    
    # Load data
    try:
        if input_path.endswith('.json'):
            content = _read_file_with_encoding_fallback(input_path)
            if not content:
                raise ValueError("JSON file is empty")
            data = json.loads(content)
            
            if isinstance(data, dict):
                # Single file result
                interpretation = interpreter.interpret_single_file(data)
            else:
                # Multiple results
                df = pd.DataFrame(data)
                interpretation = interpreter.interpret_folder_results(df)
        else:
            # CSV file
            df = pd.read_csv(input_path)
            interpretation = interpreter.interpret_folder_results(df)
    except Exception as e:
        print(f"❌ Error loading input file: {e}")
        return {"error": f"Failed to load input file: {e}"}
    
    # Save results
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(interpretation, f, indent=2)
            print(f"📊 Interpretation saved to {output_path}")
        except Exception as e:
            print(f"❌ Error saving output: {e}")
    
    return interpretation


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Interpret bug prediction results")
    parser.add_argument("--input", required=True, help="Input CSV or JSON file with results")
    parser.add_argument("--output", help="Output JSON file for interpretation")
    args = parser.parse_args()
    
    result = interpret_results(args.input, args.output)
    print(json.dumps(result, indent=2))
