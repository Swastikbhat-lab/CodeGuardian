"""Analyze large Git repositories in batches"""
from utils.git_analyzer import analyze_git_repo, cleanup_temp_dir
from agents.coordinator import review_code
from agents.ai_explainer import generate_explanations_and_fixes
from utils.report_generator import generate_html_report
import time
import os

print("="*60)
print("CodeGuardian - Large Repository Batch Analyzer")
print("="*60)

repo_url = input("\nEnter Git repository URL: ").strip()
if not repo_url:
    print("No repo provided")
    exit(1)

branch = input("Branch (default: main): ").strip() or "main"
max_files = int(input("Max files to analyze (default: 50): ").strip() or "50")
batch_size = 10  # Process 10 files at a time

print(f"\nWill process repo in batches of {batch_size} files")

# Analyze repo
result = analyze_git_repo(repo_url, branch, max_files)

if not result['success']:
    print(f"\n❌ Error: {result['error']}")
    exit(1)

# Get code files and split into batches
code_files = result.get('code_files', {})
if not code_files:
    print("No code files found")
    exit(1)

# Split into batches
file_items = list(code_files.items())
batches = [dict(file_items[i:i + batch_size]) for i in range(0, len(file_items), batch_size)]

temp_dir = result['temp_dir']
total_files = len(code_files)

print(f"\n{'='*60}")
print(f"Processing {total_files} files in {len(batches)} batches")
print(f"{'='*60}")

# Process each batch
all_issues = []
total_cost = 0.0
total_tokens = 0

try:
    for batch_num, code_files in enumerate(batches, 1):
        print(f"\n{'='*60}")
        print(f"BATCH {batch_num}/{len(batches)} - {len(code_files)} files")
        print(f"{'='*60}")
        
        # List files in this batch
        for filename in code_files.keys():
            print(f"  - {filename}")
        
        # Review this batch
        batch_result = review_code(code_files, gen_tests=False)
        
        # Collect results
        all_issues.extend(batch_result['issues'])
        total_cost += batch_result['total_cost']
        total_tokens += batch_result['total_tokens']
        
        print(f"\nBatch {batch_num} complete:")
        print(f"  Issues: {batch_result['total_issues']}")
        print(f"  Cost: ${batch_result['total_cost']:.3f}")
        
        # Small delay between batches
        if batch_num < len(batches):
            time.sleep(2)
    
    # Final summary
    print(f"\n{'='*60}")
    print("COMPLETE REPOSITORY ANALYSIS")
    print(f"{'='*60}")
    print(f"Total Files: {total_files}")
    print(f"Total Issues: {len(all_issues)}")
    print(f"Total Cost: ${total_cost:.3f}")
    print(f"Total Tokens: {total_tokens}")
    
    # Group by type
    by_type = {}
    for issue in all_issues:
        issue_type = issue['type']
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
    
    print(f"\nIssues by type:")
    for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {issue_type}: {count}")
    
    # Show critical/high severity issues
    critical = [i for i in all_issues if i.get('severity') in ['critical', 'high']]
    if critical:
        print(f"\n{'='*60}")
        print(f"CRITICAL/HIGH SEVERITY ISSUES ({len(critical)})")
        print(f"{'='*60}")
        for i, issue in enumerate(critical[:20], 1):  # Show first 20
            print(f"\n{i}. [{issue['type']}] {issue.get('severity', '').upper()}")
            print(f"   File: {issue['file']}")
            if 'line' in issue:
                print(f"   Line {issue['line']}: {issue['message']}")
            else:
                print(f"   {issue['message']}")
    
    # Generate AI explanations
    print(f"\n{'='*60}")
    print("Generating AI explanations and fixes...")
    print(f"{'='*60}")
    
    all_issues = generate_explanations_and_fixes(all_issues)
    
    # Generate HTML report
    print(f"\n{'='*60}")
    print("Generating detailed report...")
    print(f"{'='*60}")
    
    report_metadata = {
        'files': total_files,
        'cost': total_cost,
        'tokens': total_tokens,
        'trace_id': result.get('trace_id', 'N/A') if batches else 'N/A'
    }
    
    report_path = generate_html_report(all_issues, report_metadata, "codeguardian_report.html")
    abs_path = os.path.abspath(report_path)
    
    print(f"\n✅ HTML Report saved: {abs_path}")
    print(f"   Open in browser to view detailed analysis")

finally:
    cleanup_temp_dir(temp_dir)

print(f"\n{'='*60}")
print("Analysis complete!")
print(f"{'='*60}")
