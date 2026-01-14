# CodeGuardian

Autonomous Code Review System 

## What It Does

- Analyzes code for bugs, security vulnerabilities, and style issues
- Generates comprehensive test suites automatically
- Identifies logical errors using semantic analysis
- Implements fixes with validation
- Tracks all operations with complete observability

## Architecture

8 specialized AI agents coordinate to perform code reviews:

1. Coordinator - Plans and orchestrates the review process
2. Static Analysis - Runs linters (Pylint, Flake8, Radon)
3. Security - Scans for vulnerabilities (Bandit + Claude)
4. Logic - Finds semantic bugs using Claude
5. Test Generator - Creates pytest test suites
6. Test Runner - Executes tests and measures coverage
7. Bug Hunter - Analyzes test failures for root causes
8. Fix Implementer - Generates and validates code patches

## Tech Stack

- Python 3.11+
- LangGraph (multi-agent orchestration)
- Claude Sonnet 4 & Haiku (LLM reasoning)
- Langfuse (observability platform)
- FastAPI (REST API)
- PostgreSQL (data storage)
- Redis (task queue)
- React (dashboard UI)

## Project Status

Week 1 - Foundation

Currently implemented:
- Coordinator agent (fully functional)
- Static Analysis agent (fully functional)
- Core configuration system
- Database models
- Observability integration
- Test suite

In progress:
- Security agent
- Logic agent
- Test generation pipeline
- Dashboard UI

## Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 14+
- Redis 7+

### Installation
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Required API keys:
- Anthropic Claude API (https://console.anthropic.com)
- Langfuse (https://cloud.langfuse.com - free tier available)

### Run Test
```bash
python test_codeguardian.py
```

This will test your setup and run a sample code review using the Static Analysis agent.

## Current Capabilities

The system can currently:
- Analyze Python code structure
- Run static analysis (linting, complexity metrics)
- Track execution in Langfuse
- Calculate costs and token usage
- Generate execution reports


## Development Roadmap

Week 2-3: Security and Logic agents
Week 4-5: Test generation and execution
Week 6-7: Fix implementation and API
Week 8: Dashboard UI and deployment

## Observability

All agent operations are tracked via Langfuse:
- Execution timeline
- Token usage and costs
- Agent performance metrics
- Failure analysis
- Decision logging


## Contributing

This is currently a portfolio/learning project. Week 1 focus is on building the foundation.
