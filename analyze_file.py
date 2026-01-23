"""Analyze a single code file"""
from agents.coordinator import review_code
from pathlib import Path

print("="*60)
print("CodeGuardian - Single File Analyzer")
print("="*60)

# Get file path
file_path = input("\nEnter file path: ").strip()

if not file_path:
    print("No file provided")
    exit(1)

# Read file
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except Exception as e:
    print(f"Error reading file: {e}")
    exit(1)

# Get filename
filename = Path(file_path).name

# Review
code_files = {filename: content}

print(f"\nAnalyzing {filename}...")
print(f"File size: {len(content)} characters")

result = review_code(code_files, gen_tests=False)

print(f"\n{'='*60}")
print("RESULTS")
print(f"{'='*60}")
print(f"Total Issues: {result['total_issues']}")
print(f"  - Static: {result['static']}")
print(f"  - Semantic: {result['semantic']}")
print(f"Cost: ${result['total_cost']:.3f}")

if result['issues']:
    print(f"\n{'='*60}")
    print("Issues Found:")
    print(f"{'='*60}")
    for i, issue in enumerate(result['issues'], 1):
        print(f"\n{i}. [{issue['type']}] {issue.get('severity', 'N/A').upper()}")
        if 'line' in issue:
            print(f"   Line {issue['line']}: {issue['message']}")
            if 'code_snippet' in issue:
                print(f"   > {issue['code_snippet']}")
        else:
            print(f"   {issue['message']}")
            if 'full_line' in issue:
                print(f"   > {issue['full_line'][:80]}")
