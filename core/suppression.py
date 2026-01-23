"""Intelligent Suppression System"""
from typing import Dict, List


class SuppressionEngine:
    def __init__(self, context: Dict):
        self.context = context
    
    def should_suppress(self, issue: Dict) -> tuple[bool, str]:
        for rule_func in [
            self.suppress_performance_complexity,
            self.suppress_domain_complexity,
            self.suppress_generated_code,
            self.suppress_prototype_style,
            self.suppress_test_code_issues,
        ]:
            should_suppress, reason = rule_func(issue)
            if should_suppress:
                return True, reason
        
        return False, ""
    
    def suppress_performance_complexity(self, issue: Dict) -> tuple[bool, str]:
        if issue.get('type') != 'complexity':
            return False, ""
        
        if not self.context.get('is_performance_critical'):
            return False, ""
        
        message = issue.get('message', '').lower()
        if 'complexity' in message or 'nesting' in message:
            return True, "Performance-critical code - complexity acceptable"
        
        return False, ""
    
    def suppress_domain_complexity(self, issue: Dict) -> tuple[bool, str]:
        if issue.get('type') != 'complexity':
            return False, ""
        
        if not self.context.get('has_domain_complexity'):
            return False, ""
        
        filename = issue.get('file', '').lower()
        if any(kw in filename for kw in ['parser', 'model', 'crypto', 'transform']):
            if 'complexity' in issue.get('message', '').lower():
                return True, "Domain-heavy code - complexity expected"
        
        return False, ""
    
    def suppress_generated_code(self, issue: Dict) -> tuple[bool, str]:
        filename = issue.get('file', '').lower()
        
        if any(p in filename for p in ['generated', '_gen.', 'migrations/', 'vendor/']):
            return True, "Generated code"
        
        return False, ""
    
    def suppress_prototype_style(self, issue: Dict) -> tuple[bool, str]:
        if self.context.get('stage') != 'Prototype':
            return False, ""
        
        message = issue.get('message', '').lower()
        if any(kw in message for kw in ['docstring', 'naming', 'comment']):
            return True, "Prototype - style not critical"
        
        return False, ""
    
    def suppress_test_code_issues(self, issue: Dict) -> tuple[bool, str]:
        filename = issue.get('file', '').lower()
        
        if not any(m in filename for m in ['test_', '_test.', 'tests/']):
            return False, ""
        
        message = issue.get('message', '').lower()
        if 'complexity' in message or 'docstring' in message:
            return True, "Test code - relaxed rules"
        
        return False, ""


def apply_suppressions(issues: List[Dict], context: Dict) -> List[Dict]:
    engine = SuppressionEngine(context)
    
    unsuppressed = []
    suppressed_count = 0
    
    for issue in issues:
        should_suppress, reason = engine.should_suppress(issue)
        
        if should_suppress:
            suppressed_count += 1
        else:
            unsuppressed.append(issue)
    
    print(f"   Filtered {suppressed_count} false positives")
    return unsuppressed
