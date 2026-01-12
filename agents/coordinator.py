"""
Coordinator Agent - Main orchestrator for CodeGuardian

This agent is the "brain" that plans the review, delegates to specialists,
and synthesizes results. It decides which agents to use and in what order.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from pydantic import BaseModel

from core.config import get_settings
from observability.tracing import trace_agent, AgentTracer


settings = get_settings()


# ============================================
# DATA MODELS
# ============================================
class CodebaseAnalysis(BaseModel):
    """Analysis of codebase structure"""
    total_files: int
    total_lines: int
    file_types: Dict[str, int]  # {".py": 10, ".js": 5}
    has_tests: bool
    test_coverage: float = 0.0
    complexity_score: float = 0.0
    frameworks_detected: List[str] = []
    has_web_framework: bool = False
    has_database: bool = False


class ExecutionPlan(BaseModel):
    """Plan for review execution"""
    agents_to_use: List[str]
    parallel_execution: bool
    estimated_time_minutes: float
    estimated_cost: float
    priority_order: List[str]


class ReviewState(BaseModel):
    """Shared state across all agents"""
    review_id: str
    code_files: Dict[str, str]
    
    # Phase 1: Analysis
    static_analysis_complete: bool = False
    security_complete: bool = False
    logic_complete: bool = False
    issues: List[Dict[str, Any]] = []
    
    # Phase 2: Testing
    tests_generated: List[Dict[str, Any]] = []
    test_results: Optional[Dict[str, Any]] = None
    bugs_from_tests: List[Dict[str, Any]] = []
    
    # Phase 3: Fixing
    fixes_generated: List[Dict[str, Any]] = []
    
    # Metadata
    current_phase: str = "initialization"
    total_cost: float = 0.0
    total_tokens: int = 0
    start_time: datetime = datetime.utcnow()


# ============================================
# COORDINATOR AGENT
# ============================================
class CoordinatorAgent:
    """
    Main orchestrator for code reviews
    
    Responsibilities:
    1. Analyze codebase structure
    2. Create execution plan
    3. Delegate to specialist agents
    4. Monitor progress and costs
    5. Synthesize final results
    
    Example:
        coordinator = CoordinatorAgent()
        result = await coordinator.execute_review(review_id, code_files)
    """
    
    def __init__(self):
        self.llm = ChatAnthropic(
            model=settings.primary_model,
            temperature=settings.analysis_temperature
        )
    
    @trace_agent("coordinator")
    async def execute_review(
        self,
        review_id: str,
        code_files: Dict[str, str],
        _tracer: Optional[AgentTracer] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for code review
        
        Args:
            review_id: Unique identifier for this review
            code_files: Dictionary of {filepath: content}
            _tracer: Observability tracer (auto-injected)
        
        Returns:
            Complete review results with issues, tests, fixes
        """
        print(f"\n{'='*60}")
        print(f"🤖 CodeGuardian Starting Review: {review_id}")
        print(f"{'='*60}\n")
        
        # Step 1: Analyze codebase
        print("📊 Step 1: Analyzing codebase structure...")
        analysis = await self.analyze_codebase(code_files, _tracer)
        print(f"   ✓ Found {analysis.total_files} files, {analysis.total_lines} LOC")
        
        # Step 2: Create execution plan
        print("\n📋 Step 2: Creating execution plan...")
        plan = await self.create_execution_plan(analysis, _tracer)
        print(f"   ✓ Will use {len(plan.agents_to_use)} agents")
        print(f"   ✓ Estimated time: {plan.estimated_time_minutes:.1f} minutes")
        print(f"   ✓ Estimated cost: ${plan.estimated_cost:.2f}")
        
        # Step 3: Execute Phase 1 - Analysis
        print("\n🔍 Step 3: Phase 1 - Code Analysis...")
        issues = await self.execute_phase1_analysis(
            code_files, 
            plan,
            _tracer
        )
        print(f"   ✓ Found {len(issues)} issues")
        
        # Step 4: Execute Phase 2 - Testing (if enabled)
        tests = []
        bugs = []
        if "test_generator" in plan.agents_to_use:
            print("\n🧪 Step 4: Phase 2 - Test Generation...")
            tests, bugs = await self.execute_phase2_testing(
                code_files,
                issues,
                _tracer
            )
            print(f"   ✓ Generated {len(tests)} test files")
            print(f"   ✓ Found {len(bugs)} additional bugs from tests")
            issues.extend(bugs)
        
        # Step 5: Execute Phase 3 - Fixing (if enabled)
        fixes = []
        if settings.enable_auto_fix:
            print("\n🔧 Step 5: Phase 3 - Fix Generation...")
            fixes = await self.execute_phase3_fixing(
                code_files,
                issues,
                _tracer
            )
            print(f"   ✓ Generated {len(fixes)} fixes")
        
        # Step 6: Generate summary
        print("\n📊 Step 6: Generating summary...")
        summary = self.generate_summary(issues, tests, fixes)
        
        # Final results
        result = {
            "review_id": review_id,
            "status": "complete",
            "analysis": analysis.dict(),
            "plan": plan.dict(),
            "issues": issues,
            "tests": tests,
            "fixes": fixes,
            "summary": summary,
            "metadata": {
                "total_cost": _tracer.cost if _tracer else 0.0,
                "total_tokens": _tracer.tokens_used if _tracer else 0,
                "duration_seconds": (datetime.utcnow() - datetime.utcnow()).total_seconds()
            }
        }
        
        print(f"\n{'='*60}")
        print(f"✅ Review Complete!")
        print(f"   Issues: {len(issues)}")
        print(f"   Tests: {len(tests)}")
        print(f"   Fixes: {len(fixes)}")
        print(f"   Cost: ${_tracer.cost:.2f}" if _tracer else "")
        print(f"{'='*60}\n")
        
        return result
    
    async def analyze_codebase(
        self,
        code_files: Dict[str, str],
        _tracer: Optional[AgentTracer] = None
    ) -> CodebaseAnalysis:
        """
        Analyze codebase structure to understand what we're dealing with
        
        This helps us decide which agents to use and how to configure them.
        """
        total_lines = sum(len(code.split('\n')) for code in code_files.values())
        
        # Count file types
        file_types = {}
        for filepath in code_files.keys():
            ext = filepath.split('.')[-1] if '.' in filepath else 'unknown'
            file_types[f".{ext}"] = file_types.get(f".{ext}", 0) + 1
        
        # Check for test files
        has_tests = any('test' in f.lower() for f in code_files.keys())
        
        # Estimate complexity (simple heuristic)
        avg_lines_per_file = total_lines / len(code_files) if code_files else 0
        complexity_score = min(10.0, avg_lines_per_file / 50)  # 0-10 scale
        
        # Detect frameworks (simple pattern matching)
        frameworks = []
        all_code = '\n'.join(code_files.values())
        
        if 'flask' in all_code.lower() or 'fastapi' in all_code.lower():
            frameworks.append('web_framework')
        if 'sqlalchemy' in all_code.lower() or 'django.db' in all_code.lower():
            frameworks.append('database')
        
        return CodebaseAnalysis(
            total_files=len(code_files),
            total_lines=total_lines,
            file_types=file_types,
            has_tests=has_tests,
            test_coverage=0.3 if has_tests else 0.0,  # Assume 30% if tests exist
            complexity_score=complexity_score,
            frameworks_detected=frameworks,
            has_web_framework='web_framework' in frameworks,
            has_database='database' in frameworks
        )
    
    async def create_execution_plan(
        self,
        analysis: CodebaseAnalysis,
        _tracer: Optional[AgentTracer] = None
    ) -> ExecutionPlan:
        """
        Create intelligent execution plan based on codebase characteristics
        
        Decides:
        - Which agents to use
        - Whether to run in parallel
        - Priority order
        - Resource estimates
        """
        agents = []
        estimated_cost = 0.0
        estimated_time = 0.0
        
        # Static analysis is always fast and free
        if settings.enable_static_analysis:
            agents.append("static_analysis")
            estimated_time += 0.2  # 12 seconds
        
        # Security scan if web or database detected
        if settings.enable_security_scan:
            if analysis.has_web_framework or analysis.has_database:
                agents.append("security")
                estimated_cost += 0.10
                estimated_time += 0.5  # 30 seconds
        
        # Logic analysis if complex or low coverage
        if settings.enable_logic_analysis:
            if analysis.complexity_score > 5 or analysis.test_coverage < 0.5:
                agents.append("logic")
                estimated_cost += 0.25
                estimated_time += 2.0  # 2 minutes
        
        # Test generation if low coverage
        if settings.enable_test_generation:
            if analysis.test_coverage < 0.7:
                agents.append("test_generator")
                agents.append("test_runner")
                agents.append("bug_hunter")
                estimated_cost += 0.15
                estimated_time += 2.0  # 2 minutes
        
        # Parallel execution for small codebases
        parallel = (
            settings.parallel_agent_execution and
            len(agents) > 1 and
            analysis.total_lines < 10000
        )
        
        if parallel:
            estimated_time = estimated_time / 2  # Rough parallel speedup
        
        return ExecutionPlan(
            agents_to_use=agents,
            parallel_execution=parallel,
            estimated_time_minutes=estimated_time,
            estimated_cost=estimated_cost,
            priority_order=agents  # For now, use same order
        )
    
    async def execute_phase1_analysis(
        self,
        code_files: Dict[str, str],
        plan: ExecutionPlan,
        _tracer: Optional[AgentTracer] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Phase 1: Code Analysis
        
        Runs static analysis, security, and logic agents in parallel (if enabled)
        """
        issues = []
        
        # Import agents (lazy import to avoid circular dependencies)
        from agents.static_analysis import static_analysis_agent
        from agents.security import security_agent
        from agents.logic import logic_agent
        
        tasks = []
        
        # Build task list
        if "static_analysis" in plan.agents_to_use:
            print("   → Running static analysis...")
            tasks.append(static_analysis_agent(code_files))
        
        if "security" in plan.agents_to_use:
            print("   → Running security scan...")
            tasks.append(security_agent(code_files))
        
        if "logic" in plan.agents_to_use:
            print("   → Running logic analysis...")
            tasks.append(logic_agent(code_files))
        
        # Execute (parallel or sequential)
        if plan.parallel_execution and len(tasks) > 1:
            results = await asyncio.gather(*tasks)
        else:
            results = []
            for task in tasks:
                result = await task
                results.append(result)
        
        # Merge and deduplicate issues
        for result in results:
            if result:
                issues.extend(result)
        
        # Deduplicate
        issues = self.deduplicate_issues(issues)
        
        return issues
    
    async def execute_phase2_testing(
        self,
        code_files: Dict[str, str],
        issues: List[Dict[str, Any]],
        _tracer: Optional[AgentTracer] = None
    ) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Execute Phase 2: Test Generation and Execution
        
        Sequential execution (test gen → run → analyze)
        """
        # Import agents
        from agents.test_generator import test_generator_agent
        from agents.test_runner import test_runner_agent
        from agents.bug_hunter import bug_hunter_agent
        
        # Generate tests
        print("   → Generating tests...")
        tests = await test_generator_agent(code_files, issues)
        
        # Run tests
        print("   → Running tests...")
        test_results = await test_runner_agent(tests, code_files)
        
        # Analyze failures
        bugs = []
        if test_results and test_results.get('failures'):
            print("   → Analyzing test failures...")
            bugs = await bug_hunter_agent(
                test_results['failures'],
                code_files
            )
        
        return tests, bugs
    
    async def execute_phase3_fixing(
        self,
        code_files: Dict[str, str],
        issues: List[Dict[str, Any]],
        _tracer: Optional[AgentTracer] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute Phase 3: Fix Generation
        
        Generates patches for auto-fixable issues
        """
        from agents.fix_implementer import fix_implementer_agent
        
        print("   → Generating fixes...")
        fixes = await fix_implementer_agent(code_files, issues)
        
        return fixes
    
    def deduplicate_issues(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate issues
        
        Two issues are duplicates if they:
        - Are in the same file
        - On the same line
        - Have similar descriptions
        """
        seen = set()
        unique = []
        
        for issue in issues:
            key = (
                issue.get('file_path'),
                issue.get('line_number'),
                issue.get('category')
            )
            
            if key not in seen:
                seen.add(key)
                unique.append(issue)
        
        return unique
    
    def generate_summary(
        self,
        issues: List[Dict[str, Any]],
        tests: List[Dict[str, Any]],
        fixes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate summary statistics"""
        
        # Count issues by severity
        severity_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for issue in issues:
            severity = issue.get('severity', 'info')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Count issues by category
        category_counts = {}
        for issue in issues:
            cat = issue.get('category', 'unknown')
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        return {
            'total_issues': len(issues),
            'severity_breakdown': severity_counts,
            'category_breakdown': category_counts,
            'total_tests': len(tests),
            'total_fixes': len(fixes),
            'auto_fixable': sum(1 for i in issues if i.get('auto_fixable')),
        }


# ============================================
# CONVENIENCE FUNCTION
# ============================================
async def review_code(
    code_files: Dict[str, str],
    review_id: str = None
) -> Dict[str, Any]:
    """
    Convenience function to review code
    
    Args:
        code_files: Dictionary of {filepath: content}
        review_id: Optional review ID (will generate if not provided)
    
    Returns:
        Complete review results
    
    Example:
        >>> result = await review_code({
        ...     "main.py": "def divide(a, b):\n    return a / b"
        ... })
        >>> print(f"Found {result['summary']['total_issues']} issues")
    """
    import uuid
    
    if not review_id:
        review_id = str(uuid.uuid4())
    
    coordinator = CoordinatorAgent()
    return await coordinator.execute_review(review_id, code_files)
