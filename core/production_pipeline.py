"""Production-Grade Pipeline - All Features Integrated"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, List, Annotated
import operator


class ReviewState(TypedDict):
    """Enhanced state with bash tools"""
    code_files: Dict[str, str]
    workspace_dir: str
    context: Dict
    raw_issues: Annotated[List[Dict], operator.add]
    deduplicated_issues: List[Dict]
    scored_issues: List[Dict]
    filtered_issues: List[Dict]
    enhanced_issues: List[Dict]
    generated_tests: Dict[str, str]
    test_coverage: Dict
    total_cost: float
    total_tokens: int
    status: str


def create_production_pipeline():
    """Production pipeline with bash tools"""
    
    workflow = StateGraph(ReviewState)
    
    # Nodes
    workflow.add_node("setup_workspace", setup_workspace_node)
    workflow.add_node("context_analysis", analyze_context_node)
    workflow.add_node("static_analysis_local", static_analysis_local_node)
    workflow.add_node("security_scan", security_scan_node)
    workflow.add_node("enhanced_semantic", enhanced_semantic_node)
    workflow.add_node("deduplication", deduplication_node)
    workflow.add_node("risk_scoring", risk_scoring_node)
    workflow.add_node("suppression", suppression_node)
    workflow.add_node("rag_enhancement", rag_enhancement_node)
    workflow.add_node("test_generation_local", test_generation_local_node)
    
    # Flow
    workflow.set_entry_point("setup_workspace")
    workflow.add_edge("setup_workspace", "context_analysis")
    
    # Analysis in parallel
    workflow.add_edge("context_analysis", "static_analysis_local")
    workflow.add_edge("context_analysis", "security_scan")
    workflow.add_edge("context_analysis", "enhanced_semantic")
    
    # Pipeline
    workflow.add_edge("static_analysis_local", "deduplication")
    workflow.add_edge("security_scan", "deduplication")
    workflow.add_edge("enhanced_semantic", "deduplication")
    workflow.add_edge("deduplication", "risk_scoring")
    workflow.add_edge("risk_scoring", "suppression")
    workflow.add_edge("suppression", "rag_enhancement")
    workflow.add_edge("rag_enhancement", "test_generation_local")
    workflow.add_edge("test_generation_local", END)
    
    return workflow.compile()


# Node implementations

def setup_workspace_node(state: ReviewState) -> ReviewState:
    from core.bash_toolkit import get_toolkit
    
    print("\n🔧 [1/10] Setting up workspace...")
    toolkit = get_toolkit()
    
    # Write code files to workspace
    toolkit.write_files(state['code_files'])
    
    return {'workspace_dir': toolkit.workspace_dir}


def analyze_context_node(state: ReviewState) -> ReviewState:
    from agents.context_analyzer import analyze_context
    
    print("\n🔍 [2/10] Context Analysis...")
    context = analyze_context(state['code_files'])
    return {'context': context}


def static_analysis_local_node(state: ReviewState) -> ReviewState:
    from core.bash_toolkit import get_toolkit
    
    print("\n📊 [3/10] Static Analysis (Local Execution)...")
    toolkit = get_toolkit()
    
    issues = []
    
    for filepath in state['code_files'].keys():
        if not filepath.endswith('.py'):
            continue
        
        # Run linters locally with bash
        linter_results = toolkit.run_linters_locally(filepath)
        
        # Parse results (simplified)
        if linter_results.get('pylint'):
            issues.append({
                'file': filepath,
                'type': 'static_analysis',
                'tool': 'pylint_local',
                'message': 'Static analysis issues found',
                'details': linter_results['pylint'][:200]
            })
    
    return {'raw_issues': issues}


def security_scan_node(state: ReviewState) -> ReviewState:
    from agents.security_scanner import analyze_security
    
    print("\n🔒 [4/10] Security Scan...")
    issues = analyze_security(state['code_files'])
    return {'raw_issues': issues}


def enhanced_semantic_node(state: ReviewState) -> ReviewState:
    from core.enhanced_ai import enhanced_semantic_analysis
    
    print("\n🤖 [5/10] Enhanced Semantic Analysis (Chain-of-Thought)...")
    result = enhanced_semantic_analysis(state['code_files'], state['context'])
    
    return {
        'raw_issues': result['issues'],
        'total_cost': state['total_cost'] + result['cost'],
        'total_tokens': state['total_tokens'] + result['tokens']
    }


def deduplication_node(state: ReviewState) -> ReviewState:
    from core.deduplication import process_issues_pipeline
    
    print(f"\n🎯 [6/10] Deduplication & Noise Filtering...")
    deduplicated = process_issues_pipeline(state['raw_issues'])
    
    return {'deduplicated_issues': deduplicated}


def risk_scoring_node(state: ReviewState) -> ReviewState:
    from core.risk_scorer import score_all_issues
    
    print(f"\n⚖️ [7/10] Risk Scoring...")
    scored = score_all_issues(state['deduplicated_issues'], state['context'])
    return {'scored_issues': scored}


def suppression_node(state: ReviewState) -> ReviewState:
    from core.suppression import apply_suppressions
    
    print("\n🔍 [8/10] Intelligent Suppression...")
    filtered = apply_suppressions(state['scored_issues'], state['context'])
    return {'filtered_issues': filtered}


def rag_enhancement_node(state: ReviewState) -> ReviewState:
    from core.code_rag import enhance_issues_with_rag
    
    print("\n💡 [9/10] RAG Enhancement...")
    enhanced = enhance_issues_with_rag(state['filtered_issues'], state['code_files'])
    return {'enhanced_issues': enhanced}


def test_generation_local_node(state: ReviewState) -> ReviewState:
    from core.bash_toolkit import get_toolkit
    from agents.test_generation import generate_tests
    
    print("\n🧪 [10/10] Test Generation + Coverage...")
    
    # Generate tests
    result = generate_tests(state['code_files'])
    
    # Write tests to workspace
    toolkit = get_toolkit()
    test_files = {}
    
    for test_name, test_code in result['tests'].items():
        test_path = toolkit.workspace_dir + '/' + test_name
        with open(test_path, 'w') as f:
            f.write(test_code)
        test_files[test_name] = test_code
    
    # Run pytest with coverage
    coverage_result = toolkit.run_pytest_with_coverage()
    
    return {
        'generated_tests': test_files,
        'test_coverage': coverage_result['coverage'],
        'total_cost': state['total_cost'] + result['cost'],
        'total_tokens': state['total_tokens'] + result['tokens'],
        'status': 'complete'
    }


def run_production_pipeline(code_files: Dict[str, str]) -> ReviewState:
    """Run production-grade pipeline"""
    
    initial_state = ReviewState(
        code_files=code_files,
        workspace_dir='',
        context={},
        raw_issues=[],
        deduplicated_issues=[],
        scored_issues=[],
        filtered_issues=[],
        enhanced_issues=[],
        generated_tests={},
        test_coverage={},
        total_cost=0.0,
        total_tokens=0,
        status='running'
    )
    
    pipeline = create_production_pipeline()
    
    print("\n" + "="*60)
    print("🚀 CodeGuardian - Production Pipeline")
    print("   - Bash Tool Integration")
    print("   - Deduplication & Noise Filtering")
    print("   - Enhanced AI Analysis")
    print("   - Local Test Execution")
    print("="*60)
    
    final_state = pipeline.invoke(initial_state)
    
    print("\n" + "="*60)
    print("✅ Production Analysis Complete")
    print(f"   Issues Found: {len(final_state['enhanced_issues'])}")
    print(f"   Coverage: {final_state['test_coverage'].get('percent', 0):.1f}%")
    print(f"   Cost: ${final_state['total_cost']:.3f}")
    print("="*60)
    
    # Cleanup
    from core.bash_toolkit import get_toolkit
    get_toolkit().cleanup()
    
    return final_state
