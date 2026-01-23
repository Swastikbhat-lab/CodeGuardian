"""Context & Intent Analyzer"""
from anthropic import Anthropic
from core.config import get_settings
from typing import Dict


def analyze_context(code_files: Dict[str, str], repo_path: str = None) -> Dict:
    """Analyze codebase context"""
    settings = get_settings()
    
    if not settings.anthropic_api_key:
        return get_default_context()
    
    client = Anthropic(api_key=settings.anthropic_api_key)
    
    # Build prompt
    file_list = "\n".join([f"- {f}" for f in code_files.keys()])
    sample = ""
    for filepath, code in list(code_files.items())[:2]:
        sample += f"\n{filepath}:\n{code[:300]}\n"
    
    prompt = f"""Analyze this codebase:

FILES: {file_list}

SAMPLE: {sample}

Answer:
Purpose: [what?]
Type: [Library/App/CLI/Service]
Stage: [Prototype/Development/Production]
Performance Critical: [Yes/No]
Domain Complexity: [Yes/No]
Risk Tolerance: [Low/Medium/High]"""
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = response.content[0].text
        context = parse_context_analysis(analysis)
        return context
        
    except:
        return get_default_context()


def parse_context_analysis(analysis: str) -> Dict:
    context = get_default_context()
    
    for line in analysis.split('\n'):
        line = line.strip()
        if 'Purpose:' in line:
            context['purpose'] = line.split('Purpose:')[1].strip()
        elif 'Type:' in line:
            context['project_type'] = line.split('Type:')[1].strip()
        elif 'Stage:' in line:
            context['stage'] = line.split('Stage:')[1].strip()
        elif 'Performance Critical:' in line:
            context['is_performance_critical'] = 'yes' in line.lower()
        elif 'Domain Complexity:' in line:
            context['has_domain_complexity'] = 'yes' in line.lower()
        elif 'Risk Tolerance:' in line:
            tol = line.split('Risk Tolerance:')[1].strip().lower()
            context['risk_tolerance'] = tol if tol in ['low', 'medium', 'high'] else 'medium'
    
    return context


def get_default_context() -> Dict:
    return {
        'purpose': 'Code review',
        'project_type': 'Application',
        'stage': 'Development',
        'is_performance_critical': False,
        'has_domain_complexity': False,
        'risk_tolerance': 'medium',
        'maintainers': 'Team'
    }
