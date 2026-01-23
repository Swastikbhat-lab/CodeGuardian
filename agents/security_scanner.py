"""Security Scanner - Detects security vulnerabilities"""
import subprocess
import tempfile
import os
from typing import Dict, List
import re


def analyze_security(code_files: Dict[str, str]) -> List[Dict]:
    """Analyze code for security vulnerabilities"""
    issues = []
    
    for filepath, code in code_files.items():
        # Python security (Bandit)
        if filepath.endswith('.py'):
            python_issues = scan_python_security(filepath, code)
            issues.extend(python_issues)
        
        # JavaScript/Web security
        elif filepath.endswith(('.js', '.jsx', '.ts', '.tsx', '.html')):
            js_issues = scan_js_security(filepath, code)
            issues.extend(js_issues)
        
        # SQL injection (all languages)
        sql_issues = scan_sql_injection(filepath, code)
        issues.extend(sql_issues)
        
        # Hardcoded secrets
        secret_issues = scan_hardcoded_secrets(filepath, code)
        issues.extend(secret_issues)
    
    return issues


def scan_python_security(filepath: str, code: str) -> List[Dict]:
    """Scan Python code with Bandit"""
    issues = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ['bandit', '-r', temp_path, '-f', 'txt'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse Bandit output
        for line in result.stdout.split('\n'):
            if 'Issue:' in line or 'Severity:' in line:
                issues.append({
                    'file': filepath,
                    'type': 'security',
                    'severity': 'high' if 'High' in line else 'medium',
                    'message': line.strip()
                })
    
    except FileNotFoundError:
        # Bandit not installed, skip
        pass
    except Exception as e:
        pass
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return issues


def scan_js_security(filepath: str, code: str) -> List[Dict]:
    """Scan JavaScript/HTML for common vulnerabilities"""
    issues = []
    lines = code.split('\n')
    
    # XSS vulnerabilities
    xss_patterns = [
        (r'innerHTML\s*=', 'Potential XSS: Using innerHTML without sanitization'),
        (r'eval\s*\(', 'Critical: eval() usage - arbitrary code execution'),
        (r'document\.write\s*\(', 'Potential XSS: document.write() can inject scripts'),
        (r'dangerouslySetInnerHTML', 'Warning: dangerouslySetInnerHTML in React'),
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern, message in xss_patterns:
            if re.search(pattern, line):
                issues.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'security',
                    'severity': 'high' if 'Critical' in message else 'medium',
                    'message': message,
                    'code_snippet': line.strip()
                })
    
    # CORS issues
    for line_num, line in enumerate(lines, 1):
        if re.search(r'Access-Control-Allow-Origin:\s*\*', line):
            issues.append({
                'file': filepath,
                'line': line_num,
                'type': 'security',
                'severity': 'medium',
                'message': 'Insecure CORS: Wildcard (*) allows any origin',
                'code_snippet': line.strip()
            })
    
    # Unsafe HTTP
    for line_num, line in enumerate(lines, 1):
        if re.search(r'http://(?!localhost)', line, re.IGNORECASE):
            issues.append({
                'file': filepath,
                'line': line_num,
                'type': 'security',
                'severity': 'low',
                'message': 'Insecure HTTP connection (should use HTTPS)',
                'code_snippet': line.strip()[:80]
            })
    
    return issues


def scan_sql_injection(filepath: str, code: str) -> List[Dict]:
    """Detect potential SQL injection vulnerabilities"""
    issues = []
    
    # String concatenation in SQL queries
    sql_patterns = [
        (r'execute\s*\(\s*["\'].*\+.*["\']', 'SQL Injection: String concatenation in query'),
        (r'query\s*\(\s*["\'].*\+.*["\']', 'SQL Injection: String concatenation in query'),
        (r'SELECT.*\+.*FROM', 'SQL Injection: Dynamic SQL with concatenation'),
        (r'f["\']SELECT.*{.*}.*FROM', 'SQL Injection: f-string in SQL query'),
    ]
    
    for pattern, message in sql_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            issues.append({
                'file': filepath,
                'type': 'security',
                'severity': 'critical',
                'message': message
            })
    
    return issues


def scan_hardcoded_secrets(filepath: str, code: str) -> List[Dict]:
    """Detect hardcoded secrets and credentials"""
    issues = []
    lines = code.split('\n')
    
    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']{3,}["\']', 'Hardcoded password detected'),
        (r'api[_-]?key\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded API key detected'),
        (r'secret\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded secret detected'),
        (r'token\s*=\s*["\'][^"\']{10,}["\']', 'Hardcoded token detected'),
        (r'aws[_-]?secret', 'AWS secret key detected'),
        (r'sk-[a-zA-Z0-9]{20,}', 'Potential API secret key'),
        (r'pk-[a-zA-Z0-9]{20,}', 'Potential API public key'),
    ]
    
    for line_num, line in enumerate(lines, 1):
        for pattern, message in secret_patterns:
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Skip if it's a placeholder or example
                matched_text = match.group()
                if any(placeholder in matched_text.lower() for placeholder in 
                       ['example', 'your_', 'placeholder', 'xxx', '***', 'test']):
                    continue
                
                issues.append({
                    'file': filepath,
                    'line': line_num,
                    'type': 'security',
                    'severity': 'critical',
                    'message': f'{message}: {matched_text[:30]}...',
                    'code_snippet': line.strip()
                })
    
    return issues
