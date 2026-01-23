"""Git Repository Analyzer"""
import os
import subprocess
from pathlib import Path
from typing import Dict, List
import tempfile
import shutil


def clone_repo(repo_url: str, branch: str = "main") -> str:
    """Clone git repo to temp directory"""
    temp_dir = tempfile.mkdtemp(prefix="codeguardian_")
    
    try:
        print(f"Cloning {repo_url}...")
        subprocess.run(
            ['git', 'clone', '--depth', '1', '--branch', branch, repo_url, temp_dir],
            capture_output=True,
            check=True
        )
        print(f"✓ Cloned to {temp_dir}")
        return temp_dir
    except subprocess.CalledProcessError as e:
        # Try without branch if it fails
        try:
            subprocess.run(
                ['git', 'clone', '--depth', '1', repo_url, temp_dir],
                capture_output=True,
                check=True
            )
            return temp_dir
        except:
            raise Exception(f"Failed to clone repo: {e}")


def extract_code_files(repo_path: str, max_files: int = 50) -> Dict[str, str]:
    """Extract code files from repo (Python, JS, Java, C++, etc)"""
    code_files = {}
    
    # Supported extensions
    code_extensions = {
        '.py', '.js', '.jsx', '.ts', '.tsx',  # Python, JavaScript
        '.java', '.cpp', '.c', '.h', '.hpp',  # Java, C/C++
        '.go', '.rs', '.rb', '.php',          # Go, Rust, Ruby, PHP
        '.cs', '.swift', '.kt'                # C#, Swift, Kotlin
    }
    
    # Patterns to ignore
    ignore_patterns = {
        '__pycache__', '.git', 'venv', 'env', '.venv',
        'node_modules', '.pytest_cache', '.tox', 'build', 
        'dist', 'target', 'bin', 'obj', '.next'
    }
    
    repo_path_obj = Path(repo_path)
    count = 0
    
    for file_path in repo_path_obj.rglob('*'):
        # Only process files with code extensions
        if file_path.suffix not in code_extensions:
            continue
            
        # Skip ignored directories
        if any(pattern in file_path.parts for pattern in ignore_patterns):
            continue
        
        # Skip test files
        if 'test' in file_path.name.lower():
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip empty or very small files
            if len(content.strip()) < 10:
                continue
            
            # Use relative path as key
            rel_path = file_path.relative_to(repo_path_obj)
            code_files[str(rel_path)] = content
            
            count += 1
            if count >= max_files:
                print(f"⚠️ Limiting to {max_files} files")
                break
                
        except Exception as e:
            continue
    
    return code_files


def analyze_git_repo(repo_url: str, branch: str = "main", max_files: int = 50) -> Dict:
    """Main function to analyze a Git repository"""
    temp_dir = None
    
    try:
        # Clone repo
        temp_dir = clone_repo(repo_url, branch)
        
        # Extract code files
        print(f"\nExtracting code files...")
        code_files = extract_code_files(temp_dir, max_files)
        
        if not code_files:
            raise Exception("No code files found in repository")
        
        print(f"✓ Found {len(code_files)} code files")
        
        return {
            'success': True,
            'code_files': code_files,
            'temp_dir': temp_dir
        }
        
    except Exception as e:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        return {
            'success': False,
            'error': str(e),
            'code_files': {}
        }


def cleanup_temp_dir(temp_dir: str):
    """Clean up temporary directory (Windows-safe)"""
    if temp_dir and os.path.exists(temp_dir):
        try:
            # On Windows, need to handle readonly files
            import stat
            def handle_remove_readonly(func, path, exc):
                os.chmod(path, stat.S_IWRITE)
                func(path)
            
            shutil.rmtree(temp_dir, onerror=handle_remove_readonly)
            print(f"✓ Cleaned up {temp_dir}")
        except Exception as e:
            print(f"Warning: Could not clean up {temp_dir}: {e}")
