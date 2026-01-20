"""Test CodeGuardian"""
from agents.coordinator import review_code

print("Testing CodeGuardian\n")

buggy_code = {
    "calculator.py": """
def divide(a, b):
    return a / b  # BUG: No zero check

def process_list(items):
    total = 0
    for i in range(len(items) + 1):  # BUG: Off-by-one
        total += items[i]
    return total

def unsafe_eval(user_input):
    return eval(user_input)  # BUG: Security
"""
}

result = review_code(buggy_code)

print(f"\n{'='*60}")
print(f"RESULTS: {result['total_issues']} total issues")
print(f"  - Static: {result['static']}")
print(f"  - Semantic (AI): {result['semantic']}")
print(f"{'='*60}\n")

if result['issues']:
    print("Issues Found:\n")
    for i, issue in enumerate(result['issues'][:10], 1):
        print(f"{i}. [{issue['type']}] {issue['message']}")
