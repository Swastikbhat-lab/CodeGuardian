"""Generate detailed HTML/Markdown reports"""
from datetime import datetime
from typing import Dict, List


def generate_html_report(issues: List[Dict], metadata: Dict, output_path: str = "report.html"):
    """Generate detailed HTML report"""
    
    # Group by type and file
    by_type = {}
    by_file = {}
    
    for issue in issues:
        issue_type = issue['type']
        by_type[issue_type] = by_type.get(issue_type, 0) + 1
        
        filename = issue.get('file', 'Unknown')
        if filename not in by_file:
            by_file[filename] = []
        by_file[filename].append(issue)
    
    # Critical issues
    critical_issues = [i for i in issues if i.get('severity') in ['critical', 'high']]
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CodeGuardian Report</title>
    <style>
        body {{ font-family: Arial; margin: 40px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 30px; border-radius: 8px; }}
        .summary {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 20px; }}
        .metric-value {{ font-size: 36px; font-weight: bold; color: #3498db; }}
        .section {{ background: white; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .issue {{ border-left: 4px solid #e74c3c; padding: 15px; margin: 15px 0; background: #fef5f5; }}
        .issue.medium {{ border-left-color: #f39c12; background: #fef9f5; }}
        .issue-header {{ font-weight: bold; margin-bottom: 10px; }}
        .code {{ background: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 4px; font-family: monospace; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }}
        th {{ background: #34495e; color: white; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ CodeGuardian Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <div class="metric-value">{len(issues)}</div>
            <div>Total Issues</div>
        </div>
        <div class="metric">
            <div class="metric-value">{metadata.get('files', 0)}</div>
            <div>Files</div>
        </div>
        <div class="metric">
            <div class="metric-value">{len(critical_issues)}</div>
            <div>Critical/High</div>
        </div>
        <div class="metric">
            <div class="metric-value">${metadata.get('cost', 0):.3f}</div>
            <div>Cost</div>
        </div>
    </div>
    
    <div class="section">
        <h2>Issues by Type</h2>
        <table>
            <tr><th>Type</th><th>Count</th><th>%</th></tr>
"""
    
    for issue_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        pct = (count / len(issues) * 100) if issues else 0
        html += f"<tr><td>{issue_type.title()}</td><td>{count}</td><td>{pct:.1f}%</td></tr>"
    
    html += """
        </table>
    </div>
    
    <div class="section">
        <h2>Critical & High Severity Issues</h2>
"""
    
    for issue in critical_issues[:50]:
        severity = issue.get('severity', 'high')
        html += f"""
        <div class="issue">
            <div class="issue-header">[{severity.upper()}] {issue['type'].title()}</div>
            <div>📁 {issue.get('file', 'Unknown')}"""
        
        if 'line' in issue:
            html += f""" - Line {issue['line']}"""
        
        html += f"""</div>
            <p><strong>Issue:</strong> {issue['message']}</p>"""
        
        # AI Explanation
        if 'ai_risk_explanation' in issue:
            html += f"""
            <div style="background: #fff3cd; padding: 10px; border-radius: 4px; margin: 10px 0;">
                <strong>⚠️ Why it's a risk:</strong><br>
                {issue['ai_risk_explanation']}
            </div>"""
        
        # AI Fix
        if 'ai_fix_suggestion' in issue:
            html += f"""
            <div style="background: #d4edda; padding: 10px; border-radius: 4px; margin: 10px 0;">
                <strong>✅ How to fix:</strong><br>
                {issue['ai_fix_suggestion']}
            </div>"""
        
        if 'code_snippet' in issue:
            html += f"""<div class="code">{issue['code_snippet']}</div>"""
        
        html += """</div>"""
    
    html += """
    </div>
    
    <div class="section">
        <h2>All Issues by File</h2>
"""
    
    for filename, file_issues in sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True):
        html += f"<h3>📄 {filename} ({len(file_issues)})</h3>"
        
        for issue in file_issues[:30]:
            html += f"""<div class="issue medium">
                <div class="issue-header">[{issue['type'].title()}]</div>
                <p>{issue['message']}</p>"""
            
            if 'line' in issue:
                html += f"""<div>Line {issue['line']}</div>"""
            if 'code_snippet' in issue:
                html += f"""<div class="code">{issue['code_snippet']}</div>"""
            
            html += """</div>"""
    
    html += """
    </div>
</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_path
