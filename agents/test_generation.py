"""Test Generation Agent - Creates pytest tests"""
from typing import Dict, List
from anthropic import Anthropic
from core.config import get_settings
from core.observability import calculate_cost


def generate_tests(code_files: Dict[str, str], tracer=None) -> Dict:
    """Generate pytest tests for code"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        print("   Skipping (no API key)")
        return {'tests': {}, 'tokens': 0, 'cost': 0.0}
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    test_files = {}
    total_tokens = 0
    total_cost = 0.0
    
    for filepath, code in code_files.items():
        if not filepath.endswith('.py'):
            continue
        
        prompt = f"""Generate comprehensive pytest tests for this code.

Include:
- Unit tests for each function
- Edge cases
- Error handling tests
- Mock objects if needed

Code:
```python
{code}
```

Return ONLY the test code, no explanations."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Track tokens and cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = calculate_cost(input_tokens, output_tokens)
            total_tokens += (input_tokens + output_tokens)
            total_cost += cost
            
            test_code = response.content[0].text
            
            # Clean up markdown if present
            if '```python' in test_code:
                test_code = test_code.split('```python')[1].split('```')[0].strip()
            elif '```' in test_code:
                test_code = test_code.split('```')[1].split('```')[0].strip()
            
            test_filename = f"test_{filepath}"
            test_files[test_filename] = test_code
            
        except Exception as e:
            print(f"   Error generating tests for {filepath}: {e}")
    
    return {
        'tests': test_files,
        'tokens': total_tokens,
        'cost': total_cost
    }
