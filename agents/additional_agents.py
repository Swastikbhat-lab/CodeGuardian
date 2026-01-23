"""Additional Specialized Agents"""
from typing import Dict, List
import re


# AGENT 6: Bug Pattern Detector
def detect_bug_patterns(code_files: Dict[str, str]) -> List[Dict]:
    """Detect common bug patterns"""
    issues = []
    
    patterns = [
        (r'if\s+.*=\s+.*:', 'Assignment in condition (should be ==)'),
        (r'except\s*:', 'Bare except clause catches all exceptions'),
        (r'time\.sleep\(', 'Blocking sleep in async code'),
        (r'open\([^)]*\)(?!\s*with)', 'File not closed (use with statement)'),
        (r'==\s*True|==\s*False', 'Explicit boolean comparison (use "if x:" instead)'),
        (r'\[\]\s*\+\s*\[', 'Inefficient list concatenation (use extend)'),
        (r'range\(len\(', 'Range over length (use enumerate)'),
    ]
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, message in patterns:
                if re.search(pattern, line):
                    issues.append({
                        'file': filepath,
                        'line': line_num,
                        'type': 'bug_pattern',
                        'severity': 'medium',
                        'message': message,
                        'code_snippet': line.strip()
                    })
    
    return issues


# AGENT 7: Performance Analyzer
def analyze_performance(code_files: Dict[str, str]) -> List[Dict]:
    """Detect performance anti-patterns"""
    issues = []
    
    anti_patterns = [
        (r'for.*in.*:\s*.*\.append\(', 'List comprehension would be faster'),
        (r'\+\s*str\(', 'String concatenation in loop (use join)'),
        (r'global\s+\w+', 'Global variable (impacts performance)'),
        (r're\.compile.*for.*in', 'Regex compiled in loop (move outside)'),
        (r'json\.loads.*for.*in', 'JSON parsing in loop (batch if possible)'),
    ]
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, message in anti_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append({
                        'file': filepath,
                        'line': line_num,
                        'type': 'performance',
                        'severity': 'low',
                        'message': f'Performance: {message}',
                        'code_snippet': line.strip()
                    })
    
    return issues


# AGENT 8: Best Practices Enforcer  
def check_best_practices(code_files: Dict[str, str]) -> List[Dict]:
    """Check Python best practices"""
    issues = []
    
    checks = [
        (r'print\(', 'Use logging instead of print'),
        (r'TODO|FIXME|XXX', 'TODO/FIXME comment found'),
        (r'type\(.*\)\s*==', 'Use isinstance() instead of type()'),
        (r'len\(.*\)\s*==\s*0', 'Use "if not x:" instead of len() == 0'),
        (r'dict\.keys\(\).*in', 'Redundant .keys() call'),
    ]
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, message in checks:
                if re.search(pattern, line):
                    issues.append({
                        'file': filepath,
                        'line': line_num,
                        'type': 'best_practices',
                        'severity': 'low',
                        'message': message,
                        'code_snippet': line.strip()
                    })
    
    return issues
