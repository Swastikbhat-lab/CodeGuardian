"""
Static Analysis Agent

Runs Python code quality tools (Pylint, Flake8, Black) to find style violations,
code smells, and potential bugs.

This agent is fast (no LLM calls) and catches common issues.
"""
import subprocess
import tempfile
import os
import json
from typing import Dict, List, Any, Optional

from observability.tracing import trace_agent, AgentTracer


@trace_agent("static_analysis")
async def static_analysis_agent(
    code_files: Dict[str, str],
    _tracer: Optional[AgentTracer] = None
) -> List[Dict[str, Any]]:
    """
    Run static analysis tools on Python code
    
    Args:
        code_files: Dictionary of {filepath: content}
        _tracer: Observability tracer (auto-injected)
    
    Returns:
        List of issues found
    
    Example:
        >>> issues = await static_analysis_agent({
        ...     "main.py": "def hello( ):\\n  print('hello')"
        ... })
        >>> len(issues) > 0  # Will find style issues
        True
    """
    issues = []
    
    if _tracer:
        _tracer.add_metadata(files_analyzed=len(code_files))
    
    for file_path, code in code_files.items():
        # Only analyze Python files
        if not file_path.endswith('.py'):
            continue
        
        # Run Pylint
        pylint_issues = run_pylint(code, file_path)
        issues.extend(pylint_issues)
        
        # Run Flake8
        flake8_issues = run_flake8(code, file_path)
        issues.extend(flake8_issues)
        
        # Check Black formatting
        if not is_black_compliant(code):
            issues.append({
                'agent_name': 'static_analysis',
                'severity': 'low',
                'category': 'style',
                'file_path': file_path,
                'line_number': 1,
                'title': 'Code not formatted with Black',
                'description': 'Code does not conform to Black code style',
                'suggestion': 'Run: black ' + file_path,
                'auto_fixable': True,
                'tool': 'black',
                'confidence_score': 1.0
            })
        
        # Calculate complexity
        complexity_issues = check_complexity(code, file_path)
        issues.extend(complexity_issues)
    
    if _tracer:
        _tracer.add_metadata(issues_found=len(issues))
    
    return issues


def run_pylint(code: str, filename: str) -> List[Dict[str, Any]]:
    """
    Run Pylint and parse results
    
    Pylint checks for:
    - Code style (PEP 8)
    - Potential bugs (unused variables, etc.)
    - Code smells
    """
    # Write code to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False
    ) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        # Run Pylint with JSON output
        result = subprocess.run(
            [
                'pylint',
                temp_path,
                '--output-format=json',
                '--disable=C0114,C0115,C0116',  # Disable docstring warnings for now
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse JSON output
        try:
            pylint_output = json.loads(result.stdout)
        except json.JSONDecodeError:
            # Pylint might not return valid JSON if no issues
            return []
        
        issues = []
        for item in pylint_output:
            severity = map_pylint_severity(item.get('type', 'info'))
            
            issues.append({
                'agent_name': 'static_analysis',
                'severity': severity,
                'category': map_pylint_category(item.get('type')),
                'file_path': filename,
                'line_number': item.get('line', 0),
                'title': item.get('symbol', 'Pylint issue'),
                'description': item.get('message', 'Unknown issue'),
                'suggestion': None,
                'auto_fixable': False,
                'tool': 'pylint',
                'confidence_score': 0.9
            })
        
        return issues
    
    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        print(f"Pylint error: {e}")
        return []
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass


def run_flake8(code: str, filename: str) -> List[Dict[str, Any]]:
    """
    Run Flake8 for PEP 8 style checking
    
    Flake8 is stricter than Pylint for style
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        delete=False
    ) as f:
        f.write(code)
        temp_path = f.name
    
    try:
        result = subprocess.run(
            ['flake8', temp_path, '--format=json'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Flake8 doesn't have built-in JSON format, parse line by line
        issues = []
        for line in result.stdout.split('\n'):
            if not line.strip():
                continue
            
            # Format: filename:line:col: code message
            parts = line.split(':', 3)
            if len(parts) >= 4:
                try:
                    line_num = int(parts[1])
                    message = parts[3].strip()
                    
                    issues.append({
                        'agent_name': 'static_analysis',
                        'severity': 'low',  # Flake8 is mostly style
                        'category': 'style',
                        'file_path': filename,
                        'line_number': line_num,
                        'title': 'Style violation',
                        'description': message,
                        'suggestion': None,
                        'auto_fixable': True,
                        'tool': 'flake8',
                        'confidence_score': 1.0
                    })
                except:
                    continue
        
        return issues
    
    except subprocess.TimeoutExpired:
        return []
    except Exception as e:
        print(f"Flake8 error: {e}")
        return []
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass


def is_black_compliant(code: str) -> bool:
    """
    Check if code is formatted with Black
    
    Returns True if code is already Black-formatted
    """
    try:
        import black
        
        # Try to format with Black
        mode = black.Mode()
        formatted = black.format_str(code, mode=mode)
        
        # If formatting changes the code, it's not compliant
        return formatted == code
    
    except Exception:
        # If Black isn't installed or errors, assume compliant
        return True


def check_complexity(code: str, filename: str) -> List[Dict[str, Any]]:
    """
    Check code complexity using Radon
    
    Warns about overly complex functions
    """
    try:
        from radon.complexity import cc_visit
        from radon.visitors import ComplexityVisitor
        
        # Calculate cyclomatic complexity
        results = cc_visit(code)
        
        issues = []
        for item in results:
            if item.complexity > 10:  # Threshold for "too complex"
                issues.append({
                    'agent_name': 'static_analysis',
                    'severity': 'medium' if item.complexity < 15 else 'high',
                    'category': 'complexity',
                    'file_path': filename,
                    'line_number': item.lineno,
                    'title': f'High complexity: {item.complexity}',
                    'description': (
                        f"Function '{item.name}' has cyclomatic complexity of "
                        f"{item.complexity} (threshold: 10). Consider refactoring."
                    ),
                    'suggestion': 'Break function into smaller functions',
                    'auto_fixable': False,
                    'tool': 'radon',
                    'confidence_score': 1.0
                })
        
        return issues
    
    except ImportError:
        # Radon not installed
        return []
    except Exception as e:
        print(f"Radon error: {e}")
        return []


def map_pylint_severity(pylint_type: str) -> str:
    """Map Pylint message type to our severity levels"""
    mapping = {
        'error': 'high',
        'warning': 'medium',
        'refactor': 'low',
        'convention': 'low',
        'info': 'info'
    }
    return mapping.get(pylint_type.lower(), 'info')


def map_pylint_category(pylint_type: str) -> str:
    """Map Pylint message type to our categories"""
    mapping = {
        'error': 'logic',
        'warning': 'logic',
        'refactor': 'style',
        'convention': 'style',
        'info': 'documentation'
    }
    return mapping.get(pylint_type.lower(), 'style')
