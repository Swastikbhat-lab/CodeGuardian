"""Coordinator Agent"""
from typing import Dict
from agents.static_analysis import analyze_code
from agents.semantic_analysis import analyze_semantics
from agents.test_generation import generate_tests
from core.observability import AgentTracer


def review_code(code_files: Dict[str, str], gen_tests: bool = False) -> Dict:
    """Run code review with observability"""
    
    # Initialize tracing
    tracer = AgentTracer(f"code_review_{len(code_files)}_files")
    
    print("\n" + "="*60)
    print(f"CodeGuardian Review - {len(code_files)} files")
    print("="*60)
    
    all_issues = []
    total_cost = 0.0
    total_tokens = 0
    
    # Static Analysis
    print("\n1. Running static analysis...")
    tracer.start_span("static_analysis", {"files": len(code_files)})
    static_issues = analyze_code(code_files)
    tracer.end_span("static_analysis", {"issues_found": len(static_issues)})
    all_issues.extend(static_issues)
    print(f"   Found {len(static_issues)} issues")
    
    # Semantic Analysis
    print("\n2. Running semantic analysis (Claude)...")
    tracer.start_span("semantic_analysis", {"files": len(code_files)})
    semantic_result = analyze_semantics(code_files, tracer)
    semantic_issues = semantic_result['issues']
    tracer.end_span(
        "semantic_analysis",
        {"issues_found": len(semantic_issues)},
        tokens=semantic_result['tokens'],
        cost=semantic_result['cost']
    )
    all_issues.extend(semantic_issues)
    total_cost += semantic_result['cost']
    total_tokens += semantic_result['tokens']
    print(f"   Found {len(semantic_issues)} issues (${semantic_result['cost']:.3f})")
    
    # Test Generation
    test_files = {}
    if gen_tests:
        print("\n3. Generating tests...")
        tracer.start_span("test_generation", {"files": len(code_files)})
        test_result = generate_tests(code_files, tracer)
        test_files = test_result['tests']
        tracer.end_span(
            "test_generation",
            {"tests_generated": len(test_files)},
            tokens=test_result['tokens'],
            cost=test_result['cost']
        )
        total_cost += test_result['cost']
        total_tokens += test_result['tokens']
        print(f"   Generated {len(test_files)} test files (${test_result['cost']:.3f})")
    
    print(f"\nTotal: {len(all_issues)} issues | Tokens: {total_tokens} | Cost: ${total_cost:.3f}")
    print("="*60)
    
    # Finish tracing
    tracer.finish()
    
    return {
        'status': 'complete',
        'files': len(code_files),
        'issues': all_issues,
        'total_issues': len(all_issues),
        'static': len(static_issues),
        'semantic': len(semantic_issues),
        'tests': test_files,
        'total_cost': total_cost,
        'total_tokens': total_tokens
    }
