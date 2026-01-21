# CodeGuardian

Autonomous Multi-Agent Code Review System with AI-Powered Analysis

## Features

- Static analysis with Pylint
- AI semantic analysis with Claude Sonnet 4
- Finds bugs, security issues, logic errors
- Multi-agent coordination



## What It Finds

- Runtime errors (division by zero, index errors)
- Security vulnerabilities (eval, SQL injection risks)
- Logic bugs (off-by-one errors)
- Code quality issues (style, complexity)

## Architecture

- Coordinator: Orchestrates review process
- Static Analysis Agent: Pylint-based linting
- Semantic Analysis Agent: Claude AI for deep analysis

## Results

Example output:
```
RESULTS: 11 total issues
  - Static: 5
  - Semantic (AI): 6
```

## Tech Stack

Python, Claude Sonnet 4, Pylint, LangChain, Anthropic API
