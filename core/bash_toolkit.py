"""Bash Tool Integration - Give agents computer access"""
import subprocess
import os
from typing import Dict, List
import tempfile
import shutil


class BashToolkit:
    """Provides bash command execution for agents"""
    
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or tempfile.mkdtemp(prefix="codeguardian_workspace_")
        os.makedirs(self.workspace_dir, exist_ok=True)
    
    def execute_bash(self, command: str, timeout: int = 30) -> Dict:
        """Execute bash command safely"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace_dir
            )
            
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': f'Command timeout after {timeout}s',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def write_files(self, code_files: Dict[str, str]) -> Dict[str, str]:
        """Write code files to workspace"""
        file_paths = {}
        
        for filepath, content in code_files.items():
            full_path = os.path.join(self.workspace_dir, filepath)
            
            # Create directories
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_paths[filepath] = full_path
        
        return file_paths
    
    def glob_files(self, pattern: str) -> List[str]:
        """Find files matching pattern"""
        import glob
        
        full_pattern = os.path.join(self.workspace_dir, pattern)
        matches = glob.glob(full_pattern, recursive=True)
        
        # Return relative paths
        return [os.path.relpath(m, self.workspace_dir) for m in matches]
    
    def run_pytest_with_coverage(self, test_pattern: str = "test_*.py") -> Dict:
        """Run pytest with coverage"""
        
        # Install pytest and coverage if needed
        self.execute_bash("pip install pytest pytest-cov --quiet")
        
        # Run pytest
        result = self.execute_bash(
            f"pytest {test_pattern} --cov=. --cov-report=term --cov-report=json -v"
        )
        
        # Parse coverage
        coverage_data = self._parse_coverage()
        
        return {
            'test_output': result['stdout'],
            'tests_passed': 'passed' in result['stdout'].lower(),
            'coverage': coverage_data
        }
    
    def run_linters_locally(self, filepath: str) -> Dict:
        """Run all linters on file"""
        results = {}
        
        full_path = os.path.join(self.workspace_dir, filepath)
        
        # Pylint
        pylint_result = self.execute_bash(f"pylint {full_path}")
        results['pylint'] = pylint_result['stdout']
        
        # Flake8
        flake8_result = self.execute_bash(f"flake8 {full_path}")
        results['flake8'] = flake8_result['stdout']
        
        # Bandit
        bandit_result = self.execute_bash(f"bandit -r {full_path}")
        results['bandit'] = bandit_result['stdout']
        
        # Radon (complexity)
        radon_result = self.execute_bash(f"radon cc {full_path} -s")
        results['radon'] = radon_result['stdout']
        
        return results
    
    def _parse_coverage(self) -> Dict:
        """Parse coverage.json if exists"""
        coverage_file = os.path.join(self.workspace_dir, 'coverage.json')
        
        if not os.path.exists(coverage_file):
            return {'percent': 0.0}
        
        import json
        try:
            with open(coverage_file, 'r') as f:
                data = json.load(f)
            
            total = data.get('totals', {})
            percent = total.get('percent_covered', 0.0)
            
            return {
                'percent': percent,
                'lines_covered': total.get('covered_lines', 0),
                'lines_total': total.get('num_statements', 0)
            }
        except:
            return {'percent': 0.0}
    
    def cleanup(self):
        """Clean up workspace"""
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir, ignore_errors=True)


# Global toolkit instance
_toolkit = None

def get_toolkit(workspace_dir: str = None) -> BashToolkit:
    """Get or create toolkit"""
    global _toolkit
    if _toolkit is None:
        _toolkit = BashToolkit(workspace_dir)
    return _toolkit
