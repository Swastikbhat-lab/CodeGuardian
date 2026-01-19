"""Test the test generation feature"""
from agents.coordinator import review_code

code = {
    "calculator.py": """
def add(a, b):
    return a + b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
"""
}

print("Generating tests...\n")
result = review_code(code, gen_tests=True)

print(f"\n{'='*60}")
print("GENERATED TESTS:")
print(f"{'='*60}\n")

for filename, test_code in result['tests'].items():
    print(f"File: {filename}")
    print("-" * 60)
    print(test_code)
    print("\n")
