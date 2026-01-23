"""Generate AI explanations and fixes for issues"""
from anthropic import Anthropic
from core.config import get_settings
from typing import Dict, List


def generate_explanations_and_fixes(issues: List[Dict]) -> List[Dict]:
    """Add AI-generated explanations and fixes to issues"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        return issues
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    
    # Only explain critical/high severity issues (to save cost)
    issues_to_explain = [i for i in issues if i.get('severity') in ['critical', 'high']][:20]
    
    print(f"\n💡 Generating AI explanations for {len(issues_to_explain)} critical issues...")
    
    for issue in issues_to_explain:
        prompt = f"""You are a security and code quality expert. Explain this code issue:

**Type:** {issue['type']}
**Severity:** {issue.get('severity', 'unknown')}
**Message:** {issue['message']}
**File:** {issue.get('file', 'unknown')}
{f"**Line:** {issue['line']}" if 'line' in issue else ''}
{f"**Code:** `{issue['code_snippet']}`" if 'code_snippet' in issue else ''}

Provide:
1. **Why it's a risk:** Explain the security/quality impact (2-3 sentences)
2. **How to fix:** Specific actionable fix (code example if applicable)

Keep it concise and practical."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            explanation = response.content[0].text.strip()
            
            # Parse into risk and fix
            parts = explanation.split('\n\n')
            risk = ""
            fix = ""
            
            for part in parts:
                if 'risk' in part.lower() or 'why' in part.lower():
                    risk = part.replace('**Why it\'s a risk:**', '').replace('1.', '').strip()
                elif 'fix' in part.lower() or 'how' in part.lower():
                    fix = part.replace('**How to fix:**', '').replace('2.', '').strip()
            
            if not risk:
                risk = explanation.split('\n')[0]
            if not fix:
                fix = explanation.split('\n')[-1] if len(explanation.split('\n')) > 1 else "Review code manually"
            
            issue['ai_risk_explanation'] = risk
            issue['ai_fix_suggestion'] = fix
            
        except Exception as e:
            print(f"   Error generating explanation: {e}")
            issue['ai_risk_explanation'] = "Unable to generate explanation"
            issue['ai_fix_suggestion'] = "Review manually"
    
    # Copy explanations to all issues in the list
    enhanced_issues = []
    for issue in issues:
        enhanced = issue.copy()
        
        # Find if we have explanation for this type of issue
        for explained in issues_to_explain:
            if (explained.get('type') == issue.get('type') and 
                explained.get('message') == issue.get('message')):
                enhanced['ai_risk_explanation'] = explained.get('ai_risk_explanation', '')
                enhanced['ai_fix_suggestion'] = explained.get('ai_fix_suggestion', '')
                break
        
        enhanced_issues.append(enhanced)
    
    return enhanced_issues
