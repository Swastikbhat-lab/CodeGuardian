"""Risk-Based Scoring Model"""
from typing import Dict, List


class RiskScorer:
    def __init__(self, context: Dict):
        self.context = context
    
    def score_issue(self, issue: Dict) -> Dict:
        impact = self.calculate_impact(issue)
        likelihood = self.calculate_likelihood(issue)
        fix_cost = self.calculate_fix_cost(issue)
        scope = self.calculate_scope(issue)
        
        risk_score = (
            impact * 0.4 +
            likelihood * 0.3 +
            scope * 0.2 +
            (10 - fix_cost) * 0.1
        )
        
        issue['risk_score'] = round(risk_score, 2)
        issue['risk_impact'] = impact
        issue['risk_likelihood'] = likelihood
        issue['risk_fix_cost'] = fix_cost
        issue['risk_scope'] = scope
        issue['risk_level'] = self.get_risk_level(risk_score)
        
        return issue
    
    def calculate_impact(self, issue: Dict) -> int:
        issue_type = issue.get('type', '')
        severity = issue.get('severity', 'medium')
        message = issue.get('message', '').lower()
        
        if issue_type == 'security':
            if 'sql injection' in message or 'eval' in message:
                return 10
            elif 'xss' in message or 'hardcoded' in message:
                return 8
            return 7
        
        if issue_type == 'semantic':
            if 'crash' in message or 'error' in message:
                return 7
            return 5
        
        if issue_type == 'complexity':
            if self.context.get('stage') == 'Production':
                return 6
            return 3
        
        return 4
    
    def calculate_likelihood(self, issue: Dict) -> int:
        message = issue.get('message', '').lower()
        
        if 'hardcoded' in message or 'secret' in message:
            return 10
        if 'eval' in message or 'sql injection' in message:
            return 9
        if 'division by zero' in message:
            return 7
        if 'xss' in message:
            return 6
        if 'docstring' in message:
            return 1
        
        return 5
    
    def calculate_fix_cost(self, issue: Dict) -> int:
        message = issue.get('message', '').lower()
        issue_type = issue.get('type', '')
        
        if 'refactor' in message:
            return 9
        if issue_type == 'complexity':
            if 'long function' in message:
                return 7
            return 5
        if 'docstring' in message:
            return 1
        if 'naming' in message:
            return 2
        
        return 4
    
    def calculate_scope(self, issue: Dict) -> int:
        issue_type = issue.get('type', '')
        message = issue.get('message', '').lower()
        
        if issue_type == 'security':
            if 'sql' in message or 'eval' in message:
                return 9
            return 6
        
        if 'function' in message:
            return 3
        
        return 5
    
    def get_risk_level(self, score: float) -> str:
        if score >= 8:
            return 'CRITICAL'
        elif score >= 6:
            return 'HIGH'
        elif score >= 4:
            return 'MEDIUM'
        elif score >= 2:
            return 'LOW'
        else:
            return 'MINIMAL'


def score_all_issues(issues: List[Dict], context: Dict) -> List[Dict]:
    scorer = RiskScorer(context)
    
    scored = []
    for issue in issues:
        scored.append(scorer.score_issue(issue.copy()))
    
    scored.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
    return scored
