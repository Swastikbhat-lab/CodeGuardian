"""Code Complexity Analyzer - Measures complexity metrics"""
import subprocess
import tempfile
import os
from typing import Dict, List
import re


def analyze_complexity(code_files: Dict[str, str]) -> List[Dict]:
    """Analyze code complexity using radon and custom metrics"""
    issues = []
    
    for filepath, code in code_files.items():
        # Python complexity
        if filepath.endswith('.py'):
            python_issues = analyze_python_complexity(filepath, code)
            issues.extend(python_issues)
        
        # JavaScript complexity
        elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx')):
            js_issues = analyze_js_complexity(filepath, code)
            issues.extend(js_issues)
        
        # General complexity (all languages)
        general_issues = analyze_general_complexity(filepath, code)
        issues.extend(general_issues)
    
    return issues


def analyze_python_complexity(filepath: str, code: str) -> List[Dict]:
    """Analyze Python code complexity with radon"""
    issues = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # Cyclomatic complexity
        result = subprocess.run(
            ['radon', 'cc', temp_path, '-s'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        for line in result.stdout.split('\n'):
            if any(grade in line for grade in ['C', 'D', 'E', 'F']):
                issues.append({
                    'file': filepath,
                    'type': 'complexity',
                    'severity': 'medium' if 'C' in line or 'D' in line else 'high',
                    'message': f"High cyclomatic complexity: {line.strip()}"
                })
        
        # Maintainability index
        result = subprocess.run(
            ['radon', 'mi', temp_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        for line in result.stdout.split('\n'):
            if any(grade in line for grade in ['B', 'C']):
                issues.append({
                    'file': filepath,
                    'type': 'complexity',
                    'severity': 'medium',
                    'message': f"Low maintainability: {line.strip()}"
                })
    
    except Exception as e:
        pass
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return issues


def analyze_js_complexity(filepath: str, code: str) -> List[Dict]:
    """Analyze JavaScript complexity"""
    issues = []
    
    # Count nested blocks
    nesting_level = 0
    max_nesting = 0
    
    for line in code.split('\n'):
        nesting_level += line.count('{') - line.count('}')
        max_nesting = max(max_nesting, nesting_level)
    
    if max_nesting > 5:
        issues.append({
            'file': filepath,
            'type': 'complexity',
            'severity': 'high',
            'message': f"Deep nesting detected: {max_nesting} levels (recommended: ≤5)"
        })
    
    # Count callback nesting (callback hell)
    callback_pattern = r'function\s*\([^)]*\)\s*{'
    callbacks = re.findall(callback_pattern, code)
    
    if len(callbacks) > 3:
        issues.append({
            'file': filepath,
            'type': 'complexity',
            'severity': 'medium',
            'message': f"Callback hell detected: {len(callbacks)} nested callbacks"
        })
    
    return issues


def analyze_general_complexity(filepath: str, code: str) -> List[Dict]:
    """General complexity metrics for any language"""
    issues = []
    lines = code.split('\n')
    
    # Lines of code
    loc = len([l for l in lines if l.strip() and not l.strip().startswith(('#', '//', '/*'))])
    
    if loc > 500:
        issues.append({
            'file': filepath,
            'type': 'complexity',
            'severity': 'medium',
            'message': f"Large file: {loc} lines of code (recommended: <500)"
        })
    
    # Function length detection
    function_patterns = [
        r'def\s+\w+\(',        # Python
        r'function\s+\w+\(',   # JavaScript
        r'public\s+\w+\s+\w+\(' # Java/C#
    ]
    
    for pattern in function_patterns:
        matches = list(re.finditer(pattern, code))
        
        for match in matches:
            # Count lines in function (rough estimate)
            start_pos = match.start()
            remaining_code = code[start_pos:]
            
            # Find function end (closing brace or dedent)
            brace_count = 0
            function_lines = 0
            
            for line in remaining_code.split('\n')[:200]:  # Max 200 lines check
                function_lines += 1
                if '{' in line:
                    brace_count += line.count('{')
                if '}' in line:
                    brace_count -= line.count('}')
                    if brace_count <= 0 and function_lines > 1:
                        break
            
            if function_lines > 50:
                issues.append({
                    'file': filepath,
                    'type': 'complexity',
                    'severity': 'high',
                    'message': f"Long function detected: ~{function_lines} lines (recommended: <50)"
                })
                break  # Only report once per file
    
    # Deeply nested structures
    max_indent = 0
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent)
    
    if max_indent > 20:  # 5 levels of 4-space indents
        issues.append({
            'file': filepath,
            'type': 'complexity',
            'severity': 'high',
            'message': f"Deep nesting: {max_indent // 4} levels (recommended: ≤5)"
        })
    
    # Comment ratio
    comment_lines = len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
    
    if loc > 100 and comment_lines / max(loc, 1) < 0.1:
        issues.append({
            'file': filepath,
            'type': 'complexity',
            'severity': 'low',
            'message': f"Low comment ratio: {comment_lines}/{loc} = {comment_lines/loc*100:.1f}% (recommended: >10%)"
        })
    
    return issues
