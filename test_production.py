"""Test Production Pipeline"""
from core.production_pipeline import run_production_pipeline

# Test code
code = {
    "payment.py": """
import os

# Bad: Hardcoded secret
API_KEY = "sk-prod-12345"

def process_payment(amount, user_input):
    # Bad: SQL injection
    query = f"SELECT * FROM payments WHERE amount = {amount}"
    
    # Bad: eval
    result = eval(user_input)
    
    return result

def divide(a, b):
    # Missing error handling
    return a / b
"""
}

print("Testing Production-Grade CodeGuardian\n")

# Run pipeline
result = run_production_pipeline(code)

# Display results
print(f"\n{'='*60}")
print("PRODUCTION RESULTS")
print(f"{'='*60}")

print(f"\nContext:")
print(f"  Purpose: {result['context'].get('purpose')}")
print(f"  Stage: {result['context'].get('stage')}")

print(f"\nIssue Pipeline:")
print(f"  Raw Issues: {len(result['raw_issues'])}")
print(f"  After Dedup: {len(result['deduplicated_issues'])}")
print(f"  After Scoring: {len(result['scored_issues'])}")
print(f"  After Suppression: {len(result['filtered_issues'])}")
print(f"  Final (Enhanced): {len(result['enhanced_issues'])}")

print(f"\nTop Issues:")
for i, issue in enumerate(result['enhanced_issues'][:5], 1):
    print(f"\n{i}. [{issue.get('risk_level')}] Score: {issue.get('risk_score', 0):.1f}")
    print(f"   File: {issue.get('file')}")
    if 'line' in issue:
        print(f"   Line: {issue['line']}")
    print(f"   {issue['message'][:100]}")
    
    if 'detected_by' in issue:
        print(f"   Detected by: {', '.join(issue['detected_by'])}")
    
    if 'rag_analysis' in issue:
        print(f"   Analysis: {issue['rag_analysis'][:80]}...")

print(f"\nTest Coverage:")
print(f"  Coverage: {result['test_coverage'].get('percent', 0):.1f}%")
print(f"  Tests Generated: {len(result['generated_tests'])}")

print(f"\nCost: ${result['total_cost']:.3f}")
print(f"Tokens: {result['total_tokens']:,}")

print(f"\n{'='*60}")
print("✅ Production Pipeline Complete!")
print(f"{'='*60}")
