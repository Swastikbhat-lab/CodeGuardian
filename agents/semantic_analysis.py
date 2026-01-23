"""Semantic Analysis - Enhanced with Chain-of-Thought"""
from anthropic import Anthropic
from core.config import get_settings
from typing import Dict, List


def analyze_semantics(code_files: Dict[str, str], tracer=None) -> Dict:
    """Standard semantic analysis (for backward compatibility)"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        return {'issues': [], 'tokens': 0, 'cost': 0.0}
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    issues = []
    total_tokens = 0
    total_cost = 0.0
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        prompt = f"""Analyze this code for bugs:

{code}

List issues as:
LINE X: [SEVERITY] Description"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens += (input_tokens + output_tokens)
            total_cost += (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            
            analysis = response.content[0].text
            
            for line in analysis.split('\n'):
                if 'LINE' in line.upper() and ':' in line:
                    issues.append({
                        'file': filepath,
                        'type': 'semantic',
                        'message': line.strip(),
                        'agent': 'claude'
                    })
        except Exception as e:
            print(f"   Error: {e}")
    
    return {
        'issues': issues,
        'tokens': total_tokens,
        'cost': total_cost
    }


def enhanced_semantic_analysis(code_files: Dict[str, str], context: Dict) -> Dict:
    """Enhanced analysis with context awareness"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        return {'issues': [], 'tokens': 0, 'cost': 0.0}
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    issues = []
    total_tokens = 0
    total_cost = 0.0
    
    purpose = context.get('purpose', 'Code review')
    stage = context.get('stage', 'Development')
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        # Enhanced prompt with context
        prompt = f"""You are a senior code reviewer.

CONTEXT:
- File: {filepath}
- Purpose: {purpose}
- Stage: {stage}

CODE:
```python
{code}
```

Find REAL issues only:
1. Security risks (injection, exposed credentials)
2. Logic errors (edge cases, off-by-one)
3. Runtime risks (division by zero, null errors)

OUTPUT:
LINE <num>: [CRITICAL/HIGH/MEDIUM] Description
Impact: What breaks
Fix: How to fix

Only report actionable bugs, not style issues."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens += (input_tokens + output_tokens)
            total_cost += (input_tokens / 1_000_000 * 3.0) + (output_tokens / 1_000_000 * 15.0)
            
            analysis = response.content[0].text
            
            # Parse enhanced response
            current_issue = None
            for line in analysis.split('\n'):
                line = line.strip()
                
                if line.startswith('LINE') and ':' in line:
                    if current_issue:
                        issues.append(current_issue)
                    
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        line_num = parts[0].replace('LINE', '').strip()
                        rest = parts[1] + ':' + parts[2]
                        
                        severity = 'medium'
                        if '[CRITICAL]' in rest:
                            severity = 'critical'
                        elif '[HIGH]' in rest:
                            severity = 'high'
                        
                        message = rest.split(']')[-1].strip()
                        
                        current_issue = {
                            'file': filepath,
                            'line': int(line_num) if line_num.isdigit() else None,
                            'type': 'semantic',
                            'severity': severity,
                            'message': message,
                            'tool': 'claude_enhanced'
                        }
                
                elif current_issue:
                    if line.startswith('Impact:'):
                        current_issue['impact'] = line.replace('Impact:', '').strip()
                    elif line.startswith('Fix:'):
                        current_issue['suggested_fix'] = line.replace('Fix:', '').strip()
            
            if current_issue:
                issues.append(current_issue)
                
        except Exception as e:
            print(f"   Error: {e}")
    
    return {
        'issues': issues,
        'tokens': total_tokens,
        'cost': total_cost
    }
