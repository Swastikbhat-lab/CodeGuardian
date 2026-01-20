"""Coordinator Agent"""
from typing import Dict
from agents.static_analysis import analyze_code
from agents.semantic_analysis import analyze_semantics
from agents.test_generation import generate_tests


def review_code(code_files: Dict[str, str], gen_tests: bool = False) -> Dict:
    """Run code review"""
    print("\n" + "="*60)
    print(f"CodeGuardian Review - {len(code_files)} files")
    print("="*60)
    
    all_issues = []
    
    print("\n1. Running static analysis...")
    static_issues = analyze_code(code_files)
    all_issues.extend(static_issues)
    print(f"   Found {len(static_issues)} issues")
    
    print("\n2. Running semantic analysis (Claude)...")
    semantic_issues = analyze_semantics(code_files)
    all_issues.extend(semantic_issues)
    print(f"   Found {len(semantic_issues)} issues")
    
    test_files = {}
    if gen_tests:
        print("\n3. Generating tests...")
        test_files = generate_tests(code_files)
        print(f"   Generated {len(test_files)} test files")
    
    print(f"\nTotal: {len(all_issues)} issues")
    print("="*60)
    
    return {
        'status': 'complete',
        'files': len(code_files),
        'issues': all_issues,
        'total_issues': len(all_issues),
        'static': len(static_issues),
        'semantic': len(semantic_issues),
        'tests': test_files
    }
