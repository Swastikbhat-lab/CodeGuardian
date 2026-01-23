"""Coordinator Agent"""
from typing import Dict
from agents.static_analysis import analyze_code
from agents.semantic_analysis import analyze_semantics
from agents.test_generation import generate_tests
from agents.complexity_analysis import analyze_complexity
from agents.security_scanner import analyze_security
from core.observability import AgentTracer


def review_code(code_files: Dict[str, str], gen_tests: bool = False) -> Dict:
    """Run code review with observability"""
    
    # Initialize tracing
    tracer = AgentTracer(f"code_review_{len(code_files)}_files")
    
    print("\n" + "="*60)
    print(f"CodeGuardian Review - {len(code_files)} files")
    print(f"Trace ID: {tracer.trace_id}")
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
    
    # Security Scanning
    print("\n2. Running security scan...")
    tracer.start_span("security_scan", {"files": len(code_files)})
    security_issues = analyze_security(code_files)
    tracer.end_span("security_scan", {"issues_found": len(security_issues)})
    all_issues.extend(security_issues)
    print(f"   Found {len(security_issues)} issues")
    
    # Complexity Analysis
    print("\n3. Running complexity analysis...")
    tracer.start_span("complexity_analysis", {"files": len(code_files)})
    complexity_issues = analyze_complexity(code_files)
    tracer.end_span("complexity_analysis", {"issues_found": len(complexity_issues)})
    all_issues.extend(complexity_issues)
    print(f"   Found {len(complexity_issues)} issues")
    
    # Semantic Analysis
    print("\n4. Running semantic analysis (Claude)...")
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
        print("\n5. Generating tests...")
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
    print(f"View trace: https://cloud.langfuse.com (Trace ID: {tracer.trace_id})")
    print("="*60)
    
    # Finish tracing
    tracer.finish()
    
    return {
        'status': 'complete',
        'files': len(code_files),
        'issues': all_issues,
        'total_issues': len(all_issues),
        'static': len(static_issues),
        'security': len(security_issues),
        'complexity': len(complexity_issues),
        'semantic': len(semantic_issues),
        'tests': test_files,
        'total_cost': total_cost,
        'total_tokens': total_tokens,
        'trace_id': tracer.trace_id
    }
