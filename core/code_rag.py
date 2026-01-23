"""RAG System - Retrieve relevant context from codebase"""
from typing import Dict, List
import os
from anthropic import Anthropic
from core.config import get_settings


class CodeRAG:
    """Retrieval-Augmented Generation for code context"""
    
    def __init__(self, code_files: Dict[str, str]):
        self.code_files = code_files
        self.index = self._build_index()
    
    def _build_index(self) -> Dict[str, Dict]:
        """Build searchable index of code"""
        index = {}
        
        for filepath, code in self.code_files.items():
            # Extract functions, classes, imports
            lines = code.split('\n')
            
            functions = []
            classes = []
            imports = []
            
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                
                if stripped.startswith('def '):
                    func_name = stripped.split('(')[0].replace('def ', '')
                    functions.append({'name': func_name, 'line': i})
                
                elif stripped.startswith('class '):
                    class_name = stripped.split('(')[0].split(':')[0].replace('class ', '')
                    classes.append({'name': class_name, 'line': i})
                
                elif stripped.startswith('import ') or stripped.startswith('from '):
                    imports.append(stripped)
            
            index[filepath] = {
                'functions': functions,
                'classes': classes,
                'imports': imports,
                'loc': len([l for l in lines if l.strip()])
            }
        
        return index
    
    def get_context_for_issue(self, issue: Dict) -> str:
        """Get relevant context for an issue using RAG"""
        filepath = issue.get('file', '')
        line = issue.get('line', 0)
        
        if filepath not in self.code_files:
            return ""
        
        code = self.code_files[filepath]
        lines = code.split('\n')
        
        # Get surrounding context (10 lines before/after)
        start = max(0, line - 10)
        end = min(len(lines), line + 10)
        
        context_lines = lines[start:end]
        
        # Get related functions/classes
        file_index = self.index.get(filepath, {})
        
        related_info = f"File: {filepath}\n"
        related_info += f"Functions: {', '.join([f['name'] for f in file_index.get('functions', [])])}\n"
        related_info += f"Classes: {', '.join([c['name'] for c in file_index.get('classes', [])])}\n"
        related_info += f"\nContext around line {line}:\n"
        related_info += '\n'.join(f"{start+i+1}: {l}" for i, l in enumerate(context_lines))
        
        return related_info
    
    def enhance_issue_with_context(self, issue: Dict) -> Dict:
        """Enhance issue with RAG context"""
        settings = get_settings()
        
        if not settings.anthropic_api_key:
            return issue
        
        context = self.get_context_for_issue(issue)
        
        if not context:
            return issue
        
        # Use RAG to understand issue in context
        client = Anthropic(api_key=settings.anthropic_api_key)
        
        prompt = f"""Given this code context:

{context}

And this issue:
{issue.get('message', '')}

Provide:
1. Root cause analysis (why is this happening?)
2. Impact on the broader codebase
3. Specific fix with code example

Keep it concise (3-4 sentences total)."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=400,
                messages=[{"role": "user", "content": prompt}]
            )
            
            analysis = response.content[0].text.strip()
            
            issue['rag_context'] = context
            issue['rag_analysis'] = analysis
            
        except:
            pass
        
        return issue


def enhance_issues_with_rag(issues: List[Dict], code_files: Dict[str, str]) -> List[Dict]:
    """Enhance critical issues with RAG"""
    rag = CodeRAG(code_files)
    
    # Only enhance top 10 critical issues (cost control)
    critical = [i for i in issues if i.get('risk_level') in ['CRITICAL', 'HIGH']][:10]
    
    print(f"\n🔍 RAG: Analyzing {len(critical)} critical issues with context...")
    
    enhanced = []
    for issue in issues:
        if issue in critical:
            enhanced.append(rag.enhance_issue_with_context(issue))
        else:
            enhanced.append(issue)
    
    return enhanced
