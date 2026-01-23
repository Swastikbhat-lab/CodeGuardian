"""Analyze a Git repository"""
from utils.git_analyzer import analyze_git_repo, cleanup_temp_dir
from agents.coordinator import review_code

print("="*60)
print("CodeGuardian - Git Repository Analyzer")
print("="*60)

# Example: Analyze a public repo
repo_url = input("\nEnter Git repository URL: ").strip()
if not repo_url:
    repo_url = "https://github.com/Swastikbhat-lab/CodeGuardian.git"
    print(f"Using default: {repo_url}")

branch = input("Branch (default: main): ").strip() or "main"

# Analyze repo
result = analyze_git_repo(repo_url, branch, max_files=10)

if not result['success']:
    print(f"\n❌ Error: {result['error']}")
    exit(1)

code_files = result['code_files']
temp_dir = result['temp_dir']

print(f"\n{'='*60}")
print("Files to analyze:")
for i, filename in enumerate(code_files.keys(), 1):
    print(f"  {i}. {filename}")
print(f"{'='*60}")

# Run review
try:
    review_result = review_code(code_files, gen_tests=False)
    
    print(f"\n{'='*60}")
    print("REVIEW RESULTS")
    print(f"{'='*60}")
    print(f"Total Issues: {review_result['total_issues']}")
    print(f"  - Static: {review_result['static']}")
    print(f"  - Semantic: {review_result['semantic']}")
    print(f"Cost: ${review_result['total_cost']:.3f}")
    print(f"Tokens: {review_result['total_tokens']}")
    
    if review_result['issues']:
        print(f"\n{'='*60}")
        print("Sample Issues (first 10):")
        print(f"{'='*60}")
        for i, issue in enumerate(review_result['issues'][:10], 1):
            print(f"\n{i}. [{issue['type']}] {issue.get('file', 'N/A')}")
            print(f"   {issue['message'][:100]}...")
    
finally:
    # Cleanup
    cleanup_temp_dir(temp_dir)

print(f"\n{'='*60}")
print("Analysis complete!")
print(f"{'='*60}")
