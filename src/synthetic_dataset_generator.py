import random
import json
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd
import numpy as np


BUG_PATTERNS = {
    "null_pointer": {
        "description": "Null pointer dereference patterns",
        "languages": [".java", ".c", ".cpp"],
        "features": {"null_checks": 0, "pointer_ops": True, "complexity": "high"},
        "code_templates": [
            "if (obj == null) return; // Missing null check",
            "obj.method(); // Potential null dereference",
            "int* ptr = nullptr; *ptr = 5; // Null pointer dereference"
        ]
    },
    "off_by_one": {
        "description": "Off-by-one errors in loops and arrays",
        "languages": [".java", ".c", ".cpp", ".py"],
        "features": {"loop_complexity": "high", "array_access": True, "complexity": "medium"},
        "code_templates": [
            "for (int i = 0; i <= array.length; i++) { // Should be <",
            "for (int i = 1; i < array.length; i++) { // Should start at 0",
            "for i in range(len(arr) + 1): # Off by one"
        ]
    },
    "memory_leak": {
        "description": "Memory management issues",
        "languages": [".c", ".cpp"],
        "features": {"pointer_ops": True, "malloc_calls": True, "complexity": "medium"},
        "code_templates": [
            "char* str = malloc(100); // Missing free()",
            "int* arr = new int[100]; // Missing delete[]",
            "FILE* f = fopen(\"file.txt\", \"r\"); // Missing fclose()"
        ]
    },
    "race_condition": {
        "description": "Concurrency and threading issues",
        "languages": [".java", ".cpp"],
        "features": {"thread_ops": True, "sync_ops": False, "complexity": "high"},
        "code_templates": [
            "public int counter = 0; // Not synchronized",
            "counter++; // Race condition",
            "std::thread t1(func); // Missing join()"
        ]
    },
    "api_misuse": {
        "description": "Incorrect API usage patterns",
        "languages": [".java", ".py", ".c"],
        "features": {"api_calls": True, "error_handling": False, "complexity": "low"},
        "code_templates": [
            "FileInputStream fis = new FileInputStream(file); // Missing try-catch",
            "requests.get(url) # Missing error handling",
            "strcpy(dest, src); // Buffer overflow risk"
        ]
    },
    "logic_error": {
        "description": "Complex logical mistakes",
        "languages": [".java", ".py", ".c", ".cpp"],
        "features": {"complexity": "very_high", "nested_conditions": True, "complexity": "very_high"},
        "code_templates": [
            "if (a > b && a < b) { // Impossible condition",
            "if (x == 1 or x == 1) { // Redundant condition",
            "while (true) { if (condition) break; } // Infinite loop risk"
        ]
    },
    "resource_exhaustion": {
        "description": "Resource management problems",
        "languages": [".java", ".py", ".c"],
        "features": {"resource_ops": True, "loop_complexity": "high", "complexity": "medium"},
        "code_templates": [
            "while (true) { new Object(); } // Memory exhaustion",
            "for i in range(1000000): process() # Resource intensive",
            "while (1) { malloc(1024); } // Memory leak"
        ]
    }
}


def generate_synthetic_code(bug_type: str, language: str, complexity_level: str = "medium") -> Tuple[str, Dict]:
    """Generate synthetic code with specific bug patterns and extract features."""
    pattern = BUG_PATTERNS[bug_type]
    
    # Base metrics based on complexity level
    base_metrics = {
        "low": {"loc": (20, 50), "v(g)": (1, 3), "branchCount": (2, 5)},
        "medium": {"loc": (50, 150), "v(g)": (3, 8), "branchCount": (5, 15)},
        "high": {"loc": (150, 300), "v(g)": (8, 15), "branchCount": (15, 30)},
        "very_high": {"loc": (300, 500), "v(g)": (15, 25), "branchCount": (30, 50)}
    }
    
    ranges = base_metrics[complexity_level]
    loc = random.randint(*ranges["loc"])
    vg = random.uniform(*ranges["v(g)"])
    branch_count = random.randint(*ranges["branchCount"])
    
    # Generate code based on language and bug type
    if language == ".java":
        code = generate_java_code(bug_type, loc, vg)
    elif language == ".py":
        code = generate_python_code(bug_type, loc, vg)
    elif language in [".c", ".cpp"]:
        code = generate_c_cpp_code(bug_type, loc, vg)
    else:
        code = f"// Generated {bug_type} code\n" + "\n".join(["// Line " + str(i) for i in range(loc)])
    
    # Extract features from generated code
    features = extract_features_from_code(code, language)
    
    # Override with pattern-specific features
    pattern_features = pattern["features"]
    if "null_checks" in pattern_features:
        features["null_checks"] = pattern_features["null_checks"]
    if "pointer_ops" in pattern_features:
        features["pointer_ops"] = pattern_features["pointer_ops"]
    
    # Add base metrics
    features.update({
        "loc": loc,
        "v(g)": round(vg, 2),
        "branchCount": branch_count,
        "uniq_Op": max(1, branch_count // 2),
        "total_Op": loc,
        "total_Opnd": max(1, loc // 2)
    })
    
    return code, features


def generate_java_code(bug_type: str, loc: int, vg: float) -> str:
    """Generate Java code with specific bug patterns."""
    lines = ["public class SyntheticClass {", "    private int value;", "    private String name;"]
    
    if bug_type == "null_pointer":
        lines.extend([
            "    public void processData(Object obj) {",
            "        // Missing null check",
            "        obj.toString(); // Potential null pointer",
            "        if (obj != null) {",
            "            System.out.println(obj.hashCode());",
            "        }",
            "    }"
        ])
    elif bug_type == "off_by_one":
        lines.extend([
            "    public void processArray(int[] arr) {",
            "        for (int i = 0; i <= arr.length; i++) { // Off by one",
            "            if (i < arr.length) {",
            "                System.out.println(arr[i]);",
            "            }",
            "        }",
            "    }"
        ])
    elif bug_type == "race_condition":
        lines.extend([
            "    public int counter = 0; // Not synchronized",
            "    public void increment() {",
            "        counter++; // Race condition",
            "    }",
            "    public int getCounter() {",
            "        return counter;",
            "    }"
        ])
    elif bug_type == "api_misuse":
        lines.extend([
            "    public void readFile(String filename) {",
            "        FileInputStream fis = new FileInputStream(filename); // Missing try-catch",
            "        int data = fis.read();",
            "        fis.close();",
            "    }"
        ])
    elif bug_type == "logic_error":
        lines.extend([
            "    public boolean isValid(int a, int b) {",
            "        if (a > b && a < b) { // Impossible condition",
            "            return true;",
            "        }",
            "        return false;",
            "    }"
        ])
    elif bug_type == "resource_exhaustion":
        lines.extend([
            "    public void processData() {",
            "        while (true) { // Resource exhaustion risk",
            "            new Object(); // Memory leak",
            "            if (Math.random() < 0.001) break;",
            "        }",
            "    }"
        ])
    
    # Pad to target LOC
    while len(lines) < loc:
        lines.append(f"    // Line {len(lines)}")
    
    lines.append("}")
    return "\n".join(lines)


def generate_python_code(bug_type: str, loc: int, vg: float) -> str:
    """Generate Python code with specific bug patterns."""
    lines = ["class SyntheticClass:", "    def __init__(self):", "        self.value = 0", "        self.name = ''"]
    
    if bug_type == "off_by_one":
        lines.extend([
            "    def process_list(self, data):",
            "        for i in range(len(data) + 1):  # Off by one",
            "            if i < len(data):",
            "                print(data[i])",
            "    def safe_process(self, data):",
            "        for i in range(len(data)):",
            "            print(data[i])"
        ])
    elif bug_type == "api_misuse":
        lines.extend([
            "    def read_file(self, filename):",
            "        f = open(filename)  # Missing error handling",
            "        data = f.read()",
            "        f.close()",
            "        return data"
        ])
    elif bug_type == "logic_error":
        lines.extend([
            "    def validate(self, x, y):",
            "        if x > y and x < y:  # Impossible condition",
            "            return True",
            "        return False"
        ])
    elif bug_type == "resource_exhaustion":
        lines.extend([
            "    def process_data(self):",
            "        while True:  # Resource exhaustion",
            "            data = [0] * 1000  # Memory intensive",
            "            if random.random() < 0.001:",
            "                break"
        ])
    
    # Pad to target LOC
    while len(lines) < loc:
        lines.append(f"    # Line {len(lines)}")
    
    return "\n".join(lines)


def generate_c_cpp_code(bug_type: str, loc: int, vg: float) -> str:
    """Generate C/C++ code with specific bug patterns."""
    lines = ["#include <stdio.h>", "#include <stdlib.h>", ""]
    
    if bug_type == "null_pointer":
        lines.extend([
            "void process_data(int* ptr) {",
            "    // Missing null check",
            "    *ptr = 42;  // Potential null pointer dereference",
            "    if (ptr != NULL) {",
            "        printf(\"%d\\n\", *ptr);",
            "    }",
            "}"
        ])
    elif bug_type == "memory_leak":
        lines.extend([
            "void allocate_memory() {",
            "    char* str = malloc(100);  // Missing free()",
            "    strcpy(str, \"Hello\");",
            "    printf(\"%s\\n\", str);",
            "    // free(str);  // Memory leak",
            "}"
        ])
    elif bug_type == "off_by_one":
        lines.extend([
            "void process_array(int arr[], int size) {",
            "    for (int i = 0; i <= size; i++) {  // Off by one",
            "        if (i < size) {",
            "            printf(\"%d\\n\", arr[i]);",
            "        }",
            "    }",
            "}"
        ])
    elif bug_type == "api_misuse":
        lines.extend([
            "void read_file(const char* filename) {",
            "    FILE* f = fopen(filename, \"r\");  // Missing error check",
            "    char buffer[100];",
            "    fgets(buffer, 100, f);",
            "    fclose(f);",
            "}"
        ])
    
    # Pad to target LOC
    while len(lines) < loc:
        lines.append(f"    // Line {len(lines)}")
    
    return "\n".join(lines)


def extract_features_from_code(code: str, language: str) -> Dict:
    """Extract features from generated code."""
    features = {
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
        "nested_conditions": 0
    }
    
    lines = code.split('\n')
    
    # Language-specific feature extraction
    if language == ".py":
        features["imports_count"] = sum(1 for line in lines if line.strip().startswith(('import ', 'from ')))
        features["py_max_indent"] = max(len(line) - len(line.lstrip()) for line in lines if line.strip())
    elif language == ".java":
        features["imports_count"] = sum(1 for line in lines if 'import ' in line)
        features["null_checks"] = sum(1 for line in lines if '== null' in line or '!= null' in line)
        features["api_calls"] = sum(1 for line in lines if '.' in line and '(' in line)
        features["thread_ops"] = sum(1 for line in lines if 'Thread' in line or 'thread' in line)
        features["sync_ops"] = sum(1 for line in lines if 'synchronized' in line or 'lock' in line)
    elif language in [".c", ".cpp"]:
        features["includes_count"] = sum(1 for line in lines if '#include' in line)
        features["pointer_ops"] = '->' in code or '*' in code
        features["api_calls"] = sum(1 for line in lines if '(' in line and ')' in line)
        features["resource_ops"] = sum(1 for line in lines if 'malloc' in line or 'new ' in line)
    
    # Common features
    features["loop_complexity"] = sum(1 for line in lines if any(keyword in line for keyword in ['for ', 'while ', 'do ']))
    features["array_access"] = '[' in code and ']' in code
    features["error_handling"] = sum(1 for line in lines if any(keyword in line for keyword in ['try', 'catch', 'except', 'if (']))
    features["nested_conditions"] = sum(1 for line in lines if line.count('if') > 1 or line.count('&&') > 0 or line.count('||') > 0)
    
    # Calculate brace depth
    depth = 0
    max_depth = 0
    for char in code:
        if char == '{':
            depth += 1
            max_depth = max(max_depth, depth)
        elif char == '}':
            depth = max(0, depth - 1)
    features["brace_depth"] = max_depth
    
    return features


def generate_synthetic_dataset(num_samples: int = 1000, output_path: str = "data/synthetic_bugtype.csv") -> pd.DataFrame:
    """Generate a comprehensive synthetic dataset with various bug types and languages."""
    bug_types = list(BUG_PATTERNS.keys())
    languages = [".java", ".py", ".c", ".cpp"]
    complexity_levels = ["low", "medium", "high", "very_high"]
    
    rows = []
    
    for i in range(num_samples):
        # Randomly select bug type, language, and complexity
        bug_type = random.choice(bug_types)
        language = random.choice(languages)
        complexity = random.choice(complexity_levels)
        
        # Generate code and features
        code, features = generate_synthetic_code(bug_type, language, complexity)
        
        # Create row
        row = {
            "file": f"synthetic_{i:04d}{language}",
            "bug_type": bug_type,
            "language": language,
            "complexity_level": complexity,
            **features
        }
        rows.append(row)
    
    df = pd.DataFrame(rows)
    
    # Save to CSV
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    
    return df


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic bug-type dataset")
    parser.add_argument("--samples", type=int, default=1000, help="Number of samples to generate")
    parser.add_argument("--out", default="data/synthetic_bugtype.csv", help="Output CSV path")
    args = parser.parse_args()
    
    df = generate_synthetic_dataset(args.samples, args.out)
    print(f"Generated {len(df)} synthetic samples")
    print(f"Bug type distribution:")
    print(df['bug_type'].value_counts())
    print(f"Language distribution:")
    print(df['language'].value_counts())
    print(f"Saved to: {args.out}")
