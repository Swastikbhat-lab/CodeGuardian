"""Issue Deduplication and Smart Aggregation"""
from typing import List, Dict
import re
from collections import defaultdict


def deduplicate_issues(issues: List[Dict]) -> List[Dict]:
    """Remove duplicate issues"""
    
    seen = set()
    deduplicated = []
    
    for issue in issues:
        # Create fingerprint
        fingerprint = create_fingerprint(issue)
        
        if fingerprint not in seen:
            seen.add(fingerprint)
            deduplicated.append(issue)
        else:
            # Merge metadata from duplicate
            for existing in deduplicated:
                if create_fingerprint(existing) == fingerprint:
                    merge_duplicate_metadata(existing, issue)
                    break
    
    print(f"   Deduplication: {len(issues)} → {len(deduplicated)} issues")
    return deduplicated


def create_fingerprint(issue: Dict) -> str:
    """Create unique fingerprint for issue"""
    
    # Normalize message
    message = issue.get('message', '').lower()
    
    # Remove tool-specific prefixes
    message = re.sub(r'\[b\d+:.*?\]', '', message)  # Bandit codes
    message = re.sub(r'line \d+:', '', message)  # Line numbers
    message = re.sub(r'\d+:', '', message)  # Numbers
    
    # Extract core issue
    message = message.strip()
    
    # Fingerprint: file + line + normalized message
    file_key = issue.get('file', 'unknown')
    line_key = issue.get('line', 0)
    
    return f"{file_key}:{line_key}:{message[:50]}"


def merge_duplicate_metadata(existing: Dict, duplicate: Dict):
    """Merge metadata from duplicate into existing"""
    
    # Track which tools found this
    if 'detected_by' not in existing:
        existing['detected_by'] = [existing.get('tool', existing.get('type', 'unknown'))]
    
    duplicate_tool = duplicate.get('tool', duplicate.get('type', 'unknown'))
    if duplicate_tool not in existing['detected_by']:
        existing['detected_by'].append(duplicate_tool)
    
    # Update confidence score
    existing['confidence'] = len(existing['detected_by'])


def aggregate_issues(issues: List[Dict]) -> List[Dict]:
    """Group related issues"""
    
    # Group by file
    by_file = defaultdict(list)
    for issue in issues:
        by_file[issue.get('file', 'unknown')].append(issue)
    
    aggregated = []
    
    for filepath, file_issues in by_file.items():
        # Check if we should aggregate
        if len(file_issues) > 10:
            # Create summary issue
            summary = create_file_summary(filepath, file_issues)
            aggregated.append(summary)
        else:
            # Keep individual issues
            aggregated.extend(file_issues)
    
    return aggregated


def create_file_summary(filepath: str, issues: List[Dict]) -> Dict:
    """Create summary issue for file with many problems"""
    
    by_type = defaultdict(int)
    highest_risk = 0
    
    for issue in issues:
        by_type[issue.get('type', 'unknown')] += 1
        highest_risk = max(highest_risk, issue.get('risk_score', 0))
    
    summary_parts = []
    for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        summary_parts.append(f"{count} {issue_type}")
    
    return {
        'file': filepath,
        'type': 'file_summary',
        'severity': 'high',
        'message': f"Multiple issues in file: {', '.join(summary_parts[:3])}",
        'risk_score': highest_risk,
        'risk_level': 'HIGH',
        'aggregated_count': len(issues),
        'detailed_issues': issues[:20]  # Keep top 20
    }


def smart_filter_noise(issues: List[Dict]) -> List[Dict]:
    """Additional noise filtering"""
    
    filtered = []
    
    for issue in issues:
        if should_keep_issue(issue):
            filtered.append(issue)
    
    print(f"   Noise filtering: {len(issues)} → {len(filtered)} issues")
    return filtered


def should_keep_issue(issue: Dict) -> bool:
    """Decide if issue is worth keeping"""
    
    message = issue.get('message', '').lower()
    
    # Filter ultra-low value issues
    noise_patterns = [
        'line too long',  # Formatting
        'trailing whitespace',
        'missing final newline',
        'wrong import order',
        'unused import',  # Unless it's a real problem
        'module level import',
        'lowercase variable',  # Unless critical
        'invalid name "i"',  # Loop variables
        'invalid name "x"',
        'invalid name "f"',
    ]
    
    for pattern in noise_patterns:
        if pattern in message and issue.get('risk_score', 0) < 3:
            return False
    
    # Keep high risk issues
    if issue.get('risk_score', 0) >= 4:
        return True
    
    # Keep security issues
    if issue.get('type') == 'security':
        return True
    
    # Keep critical semantic issues
    if issue.get('type') == 'semantic' and 'critical' in message:
        return True
    
    # Filter low-value complexity warnings
    if issue.get('type') == 'complexity' and issue.get('risk_score', 0) < 4:
        return False
    
    return True


def process_issues_pipeline(issues: List[Dict]) -> List[Dict]:
    """Complete processing pipeline"""
    
    print("\n📊 Issue Processing Pipeline:")
    print(f"   Input: {len(issues)} raw issues")
    
    # Step 1: Deduplicate
    issues = deduplicate_issues(issues)
    
    # Step 2: Filter noise
    issues = smart_filter_noise(issues)
    
    # Step 3: Aggregate if needed
    # issues = aggregate_issues(issues)  # Optional
    
    print(f"   Final: {len(issues)} actionable issues")
    
    return issues
