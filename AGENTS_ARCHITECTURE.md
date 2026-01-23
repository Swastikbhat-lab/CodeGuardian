# CodeGuardian - 8 Specialized Agents

## Agent Architecture

### 1. **Static Analysis Agent** (Pylint + Flake8)
- **Tools:** Pylint, Flake8
- **Purpose:** Code style, PEP8 compliance, basic errors
- **Output:** Convention violations, warnings, errors

### 2. **Security Scanner Agent** (Bandit + Custom)
- **Tools:** Bandit, custom regex patterns
- **Purpose:** Security vulnerabilities
- **Detects:** 
  - SQL injection
  - XSS vulnerabilities
  - Hardcoded secrets
  - Insecure protocols
  - CORS misconfigurations

### 3. **Complexity Analyzer Agent** (Radon + Custom)
- **Tools:** Radon, custom metrics
- **Purpose:** Code maintainability
- **Detects:**
  - Cyclomatic complexity
  - Deep nesting
  - Long functions
  - Low comment ratio

### 4. **Semantic Analysis Agent** (Claude AI)
- **Tools:** Claude Sonnet 4
- **Purpose:** Logic bugs, edge cases
- **Detects:**
  - Runtime errors
  - Logic bugs
  - Edge cases
  - Type mismatches

### 5. **Test Generation Agent** (Claude AI)
- **Tools:** Claude Sonnet 4, pytest
- **Purpose:** Automated test creation
- **Generates:**
  - Unit tests
  - Edge case tests
  - Mock objects
  - Coverage analysis

### 6. **Bug Pattern Detector Agent** (Pattern Matching)
- **Tools:** Regex patterns, AST analysis
- **Purpose:** Common bug patterns
- **Detects:**
  - Assignment in conditions
  - Bare except clauses
  - File handle leaks
  - Inefficient patterns

### 7. **Performance Analyzer Agent** (Custom)
- **Tools:** Pattern analysis
- **Purpose:** Performance anti-patterns
- **Detects:**
  - Loop inefficiencies
  - String concatenation issues
  - Global variable usage
  - Regex compilation in loops

### 8. **Best Practices Enforcer Agent** (Custom)
- **Tools:** Python idiom checks
- **Purpose:** Pythonic code standards
- **Detects:**
  - Print vs logging
  - Type() vs isinstance()
  - TODO/FIXME comments
  - Redundant operations

## Multi-Agent Coordination (LangGraph)

```
Context Analysis
      ↓
┌─────┴─────┬─────────┬──────────┬──────────┬──────────┬──────────┬──────────┐
│           │         │          │          │          │          │          │
Static    Security  Complex  Semantic   Test Gen  Bug Pat  Perf   Best Prac
│           │         │          │          │          │          │          │
└─────┬─────┴─────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
      ↓
Risk-Based Scoring
      ↓
Intelligent Suppression
      ↓
RAG Context Enhancement
      ↓
Final Report
```

## RAG Integration

**Retrieval-Augmented Generation** provides contextual understanding:
- Indexes codebase structure
- Retrieves relevant context for each issue
- Uses Claude to analyze issues with surrounding code
- Provides root cause analysis
- Suggests fixes with full context

## Issue Processing Pipeline

1. **Detection** - 8 agents find issues in parallel
2. **Scoring** - Risk model scores on 4 dimensions
3. **Suppression** - Filters false positives based on context
4. **Enhancement** - RAG adds contextual analysis
5. **Reporting** - HTML/Markdown with explanations
