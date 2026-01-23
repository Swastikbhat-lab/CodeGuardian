"""Static Analysis Agent"""
import subprocess
import tempfile
import os
from typing import Dict, List


def analyze_code(code_files: Dict[str, str]) -> List[Dict]:
    """Run static analysis on code files"""
    issues = []
    
    for filepath, code in code_files.items():
        ext = os.path.splitext(filepath)[1]
        
        # Only run Pylint on Python files
        if ext == '.py':
            issues.extend(analyze_python(filepath, code))
        else:
            # For other languages, just note them
            issues.append({
                'file': filepath,
                'type': 'static_analysis',
                'message': f'Code file detected ({ext})',
                'full_line': f'{filepath}: Detected {ext} file'
            })
    
    return issues


def analyze_python(filepath: str, code: str) -> List[Dict]:
    """Analyze Python code with Pylint"""
    issues = []
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ['pylint', temp_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        for line in result.stdout.split('\n'):
            if ':' in line and any(c in line for c in ['C0', 'W0', 'E0', 'R0', 'F0']):
                issues.append({
                    'file': filepath,
                    'type': 'static_analysis',
                    'message': line.split(':', 3)[-1].strip() if ':' in line else line.strip(),
                    'full_line': line.strip()
                })
    except Exception as e:
        pass
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    return issues
