"""Complete LangGraph Pipeline - All 8 Agents + RAG"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Dict, List, Annotated
import operator


class ReviewState(TypedDict):
    """State passed between agents"""
    code_files: Dict[str, str]
    context: Dict
    raw_issues: Annotated[List[Dict], operator.add]
    scored_issues: List[Dict]
    filtered_issues: List[Dict]
    enhanced_issues: List[Dict]
    generated_tests: Dict[str, str]
    test_coverage: Dict
    total_cost: float
    total_tokens: int
    status: str


def create_complete_pipeline():
    """Create complete pipeline with all 8 agents"""
    
    workflow = StateGraph(ReviewState)
    
    # All 8 agents
    workflow.add_node("context_analysis", analyze_context_node)
    workflow.add_node("static_analysis", static_analysis_node)
    workflow.add_node("security_scan", security_scan_node)
    workflow.add_node("complexity_analysis", complexity_analysis_node)
    workflow.add_node("semantic_analysis", semantic_analysis_node)
    workflow.add_node("bug_patterns", bug_pattern_node)
    workflow.add_node("performance", performance_node)
    workflow.add_node("best_practices", best_practices_node)
    workflow.add_node("risk_scoring", risk_scoring_node)
    workflow.add_node("suppression", suppression_node)
    workflow.add_node("rag_enhancement", rag_enhancement_node)
    workflow.add_node("test_generation", test_generation_node)
    
    # Flow
    workflow.set_entry_point("context_analysis")
    
    # Context → All 8 analysis agents
    workflow.add_edge("context_analysis", "static_analysis")
    workflow.add_edge("context_analysis", "security_scan")
    workflow.add_edge("context_analysis", "complexity_analysis")
    workflow.add_edge("context_analysis", "semantic_analysis")
    workflow.add_edge("context_analysis", "bug_patterns")
    workflow.add_edge("context_analysis", "performance")
    workflow.add_edge("context_analysis", "best_practices")
    
    # All → Risk scoring
    workflow.add_edge("static_analysis", "risk_scoring")
    workflow.add_edge("security_scan", "risk_scoring")
    workflow.add_edge("complexity_analysis", "risk_scoring")
    workflow.add_edge("semantic_analysis", "risk_scoring")
    workflow.add_edge("bug_patterns", "risk_scoring")
    workflow.add_edge("performance", "risk_scoring")
    workflow.add_edge("best_practices", "risk_scoring")
    
    # Risk → Suppression → RAG → Tests
    workflow.add_edge("risk_scoring", "suppression")
    workflow.add_edge("suppression", "rag_enhancement")
    workflow.add_edge("rag_enhancement", "test_generation")
    workflow.add_edge("test_generation", END)
    
    return workflow.compile()


# Node implementations

def analyze_context_node(state: ReviewState) -> ReviewState:
    from agents.context_analyzer import analyze_context
    print("\n [1/11] Context Analysis...")
    state['context'] = analyze_context(state['code_files'])
    return state


def static_analysis_node(state: ReviewState) -> ReviewState:
    from agents.static_analysis import analyze_code
    print("\n [2/11] Static Analysis (Pylint + Flake8)...")
    issues = analyze_code(state['code_files'])
    return {'raw_issues': issues}


def security_scan_node(state: ReviewState) -> ReviewState:
    from agents.security_scanner import analyze_security
    print("\n [3/11] Security Scan (Bandit)...")
    issues = analyze_security(state['code_files'])
    return {'raw_issues': issues}


def complexity_analysis_node(state: ReviewState) -> ReviewState:
    from agents.complexity_analysis import analyze_complexity
    print("\n [4/11] Complexity Analysis (Radon)...")
    issues = analyze_complexity(state['code_files'])
    return {'raw_issues': issues}


def semantic_analysis_node(state: ReviewState) -> ReviewState:
    from agents.semantic_analysis import analyze_semantics
    print("\n [5/11] Semantic Analysis (Claude AI)...")
    result = analyze_semantics(state['code_files'])
    return {
        'raw_issues': result['issues'],
        'total_cost': state['total_cost'] + result['cost'],
        'total_tokens': state['total_tokens'] + result['tokens']
    }


def bug_pattern_node(state: ReviewState) -> ReviewState:
    from agents.additional_agents import detect_bug_patterns
    print("\n [6/11] Bug Pattern Detection...")
    issues = detect_bug_patterns(state['code_files'])
    return {'raw_issues': issues}


def performance_node(state: ReviewState) -> ReviewState:
    from agents.additional_agents import analyze_performance
    print("\n [7/11] Performance Analysis...")
    issues = analyze_performance(state['code_files'])
    return {'raw_issues': issues}


def best_practices_node(state: ReviewState) -> ReviewState:
    from agents.additional_agents import check_best_practices
    print("\n [8/11] Best Practices Check...")
    issues = check_best_practices(state['code_files'])
    return {'raw_issues': issues}


def risk_scoring_node(state: ReviewState) -> ReviewState:
    from core.risk_scorer import score_all_issues
    print(f"\n [9/11] Risk Scoring ({len(state['raw_issues'])} issues)...")
    state['scored_issues'] = score_all_issues(state['raw_issues'], state['context'])
    return state


def suppression_node(state: ReviewState) -> ReviewState:
    from core.suppression import apply_suppressions
    print("\n [10/11] Intelligent Suppression...")
    state['filtered_issues'] = apply_suppressions(state['scored_issues'], state['context'])
    return state


def rag_enhancement_node(state: ReviewState) -> ReviewState:
    from core.code_rag import enhance_issues_with_rag
    print("\n [11/11] RAG Context Enhancement...")
    state['enhanced_issues'] = enhance_issues_with_rag(state['filtered_issues'], state['code_files'])
    return state


def test_generation_node(state: ReviewState) -> ReviewState:
    from agents.test_generation import generate_tests
    print("\n [12/11] Test Generation...")
    result = generate_tests(state['code_files'])
    state['generated_tests'] = result['tests']
    state['total_cost'] += result['cost']
    state['total_tokens'] += result['tokens']
    state['status'] = 'complete'
    return state


def run_complete_pipeline(code_files: Dict[str, str]) -> ReviewState:
    """Run complete 8-agent pipeline with RAG"""
    
    initial_state = ReviewState(
        code_files=code_files,
        context={},
        raw_issues=[],
        scored_issues=[],
        filtered_issues=[],
        enhanced_issues=[],
        generated_tests={},
        test_coverage={},
        total_cost=0.0,
        total_tokens=0,
        status='running'
    )
    
    pipeline = create_complete_pipeline()
    
    print("\n" + "="*60)
    print(" CodeGuardian - Complete 8-Agent Pipeline")
    print("="*60)
    
    final_state = pipeline.invoke(initial_state)
    
    print("\n" + "="*60)
    print(" Analysis Complete")
    print(f"   8 Agents Executed")
    print(f"   Raw Issues: {len(final_state['raw_issues'])}")
    print(f"   After Suppression: {len(final_state['filtered_issues'])}")
    print(f"   Cost: ${final_state['total_cost']:.3f}")
    print("="*60)
    
    return final_state
