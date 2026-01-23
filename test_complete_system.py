"""Test Complete CodeGuardian System - All 8 Agents + RAG"""
from core.complete_pipeline import run_complete_pipeline

# Realistic buggy code
code_files = {
    "payment_processor.py": """
# Payment processing - production code
import time

api_key = "sk-prod-abc123def456"  # Hardcoded secret

def process_payment(amount, user_id):
    # No input validation
    result = eval(f"amount * 1.05")  # Security issue
    
    # Performance issue
    for i in range(len(transactions)):
        if transactions[i] == user_id:
            total = total + transactions[i]
    
    return result

def refund(payment_id):
    # Missing error handling
    payment = db.query(f"SELECT * FROM payments WHERE id = {payment_id}")
    return payment
""",
    
    "data_analyzer.py": """
# Complex analytics - domain heavy
def analyze_dataset(data):
    results = []
    for item in data:
        if item['type'] == 'A':
            if item['status'] == 'active':
                if item['priority'] > 5:
                    if item['region'] == 'US':
                        if item['verified']:
                            results.append(transform(item))
    return results

def transform(item):
    # Long function
    step1 = item['value'] * 2
    step2 = step1 + 10
    step3 = step2 / 3
    # ... 50 more lines ...
    return step3
"""
}

print("Testing CodeGuardian - Production-Grade Review\n")

# Run complete pipeline
result = run_complete_pipeline(code_files)

# Display results
print(f"\n{'='*60}")
print("FINAL RESULTS")
print(f"{'='*60}")

print(f"\nContext Understanding:")
print(f"  Purpose: {result['context'].get('purpose', 'Unknown')}")
print(f"  Stage: {result['context'].get('stage', 'Unknown')}")
print(f"  Performance Critical: {result['context'].get('is_performance_critical')}")

print(f"\nIssue Pipeline:")
print(f"  Raw Detections: {len(result['raw_issues'])}")
print(f"  After Risk Scoring: {len(result['scored_issues'])}")
print(f"  After Suppression: {len(result['filtered_issues'])}")
print(f"  Enhanced with RAG: {len(result['enhanced_issues'])}")

print(f"\nTop 5 Critical Issues:")
for i, issue in enumerate(result['enhanced_issues'][:5], 1):
    print(f"\n{i}. [{issue.get('risk_level', 'N/A')}] Score: {issue.get('risk_score', 0):.1f}")
    print(f"   Type: {issue['type']}")
    print(f"   File: {issue.get('file', 'Unknown')}")
    if 'line' in issue:
        print(f"   Line: {issue['line']}")
    print(f"   Issue: {issue['message'][:80]}...")
    
    if 'rag_analysis' in issue:
        print(f"   RAG Analysis: {issue['rag_analysis'][:100]}...")

print(f"\nAgent Breakdown:")
by_agent = {}
for issue in result['raw_issues']:
    agent_type = issue.get('type', 'unknown')
    by_agent[agent_type] = by_agent.get(agent_type, 0) + 1

for agent, count in sorted(by_agent.items(), key=lambda x: x[1], reverse=True):
    print(f"  {agent}: {count} issues")

print(f"\nCost Analysis:")
print(f"  Total Cost: ${result['total_cost']:.3f}")
print(f"  Total Tokens: {result['total_tokens']:,}")

print(f"\n{'='*60}")
print(" CodeGuardian Complete!")
print(f"{'='*60}")
