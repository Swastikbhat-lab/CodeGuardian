"""Semantic Analysis Agent - Uses Claude to find logic bugs"""
from typing import Dict, List
import os
from anthropic import Anthropic
from core.config import get_settings
from core.observability import calculate_cost


def analyze_semantics(code_files: Dict[str, str], tracer=None) -> Dict:
    """Use Claude to find semantic bugs"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        print("   Skipping (no API key)")
        return {'issues': [], 'tokens': 0, 'cost': 0.0}
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    issues = []
    total_tokens = 0
    total_cost = 0.0
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        prompt = f"""Analyze this code for bugs and logic errors.

Language: {os.path.splitext(filepath)[1]}
Focus on:
- Potential runtime errors
- Logic bugs
- Edge cases not handled
- Security issues

Code:
```
{code}
```

List each issue as:
LINE X: [SEVERITY] Description

Keep it concise."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track tokens and cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = calculate_cost(input_tokens, output_tokens)
            total_tokens += (input_tokens + output_tokens)
            total_cost += cost
            
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
