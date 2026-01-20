"""Semantic Analysis Agent - Uses Claude to find logic bugs"""
from typing import Dict, List
from anthropic import Anthropic
from core.config import get_settings


def analyze_semantics(code_files: Dict[str, str]) -> List[Dict]:
    """Use Claude to find semantic bugs"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        print("   Skipping (no API key)")
        return []
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    issues = []
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        prompt = f"""Analyze this Python code for bugs and logic errors.
Focus on:
- Potential runtime errors
- Logic bugs
- Edge cases not handled
- Security issues

Code:
```python
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
    
    return issues
