"""Static Analysis Agent - Pylint + Flake8"""
import subprocess
import tempfile
import os
from typing import Dict, List


def analyze_code(code_files: Dict[str, str]) -> List[Dict]:
    """Run Pylint and Flake8 on code"""
    issues = []
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Run Pylint
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
                        'tool': 'pylint',
                        'message': line.split(':', 3)[-1].strip() if ':' in line else line.strip(),
                        'full_line': line.strip()
                    })
            
            # Run Flake8
            result = subprocess.run(
                ['flake8', temp_path, '--max-line-length=100'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            for line in result.stdout.split('\n'):
                if line.strip() and ':' in line:
                    parts = line.split(':')
                    if len(parts) >= 4:
                        line_num = parts[1].strip()
                        message = ':'.join(parts[3:]).strip()
                        issues.append({
                            'file': filepath,
                            'line': int(line_num) if line_num.isdigit() else None,
                            'type': 'static_analysis',
                            'tool': 'flake8',
                            'message': message,
                            'full_line': line.strip()
                        })
        
        except FileNotFoundError as e:
            if 'flake8' in str(e):
                print("   Flake8 not installed, skipping")
            pass
        except Exception as e:
            pass
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    return issues
