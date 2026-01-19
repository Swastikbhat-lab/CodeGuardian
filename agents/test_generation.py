"""Test Generation Agent - Creates pytest tests"""
from typing import Dict, List
from anthropic import Anthropic
from core.config import get_settings


def generate_tests(code_files: Dict[str, str]) -> Dict[str, str]:
    """Generate pytest tests for code"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        print("   Skipping (no API key)")
        return {}
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    test_files = {}
    
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
    
    return test_files
