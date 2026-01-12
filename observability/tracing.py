"""
Observability integration with Langfuse

This module provides tracing and monitoring for all agent executions.
Every LLM call, tool use, and decision is tracked for debugging and cost analysis.
"""
from functools import wraps
from typing import Any, Callable, Dict, Optional
from datetime import datetime
import asyncio

from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

from core.config import get_settings, calculate_cost


# Initialize Langfuse
settings = get_settings()
langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host
)


class AgentTracer:
    """
    Wrapper for tracing agent execution
    
    Tracks timing, token usage, cost, and quality for each agent.
    
    Example:
        tracer = AgentTracer("static_analysis")
        tracer.start()
        # ... do work ...
        tracer.add_tokens(1000, 500, "claude-sonnet-4")
        tracer.end(success=True)
    """
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.tokens_used = 0
        self.cost = 0.0
        self.metadata: Dict[str, Any] = {}
    
    def start(self, metadata: Dict[str, Any] = None):
        """
        Start tracing
        
        Args:
            metadata: Additional metadata to track
        """
        self.start_time = datetime.utcnow()
        if metadata:
            self.metadata.update(metadata)
    
    def end(self, success: bool = True, error: str = None):
        """
        End tracing and update Langfuse
        
        Args:
            success: Whether the agent succeeded
            error: Error message if failed
        """
        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()
        
        # Update current trace in Langfuse
        if langfuse_context.get_current_trace_id():
            langfuse_context.update_current_trace(
                name=f"agent-{self.agent_name}",
                metadata={
                    **self.metadata,
                    "duration_seconds": duration,
                    "success": success,
                    "error": error,
                    "tokens_used": self.tokens_used,
                    "cost_usd": self.cost
                }
            )
    
    def add_tokens(self, input_tokens: int, output_tokens: int, model: str):
        """
        Track token usage and cost
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            model: Model name used
        """
        self.tokens_used += input_tokens + output_tokens
        self.cost += calculate_cost(model, input_tokens, output_tokens)
        
        # Update current observation in Langfuse
        if langfuse_context.get_current_observation_id():
            langfuse_context.update_current_observation(
                usage={
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": input_tokens + output_tokens,
                    "unit": "TOKENS"
                },
                model=model,
                metadata={
                    "cost_usd": calculate_cost(model, input_tokens, output_tokens)
                }
            )
    
    def add_metadata(self, **kwargs):
        """Add additional metadata"""
        self.metadata.update(kwargs)


def trace_agent(agent_name: str):
    """
    Decorator to trace agent execution
    
    Automatically wraps agent functions with observability.
    
    Usage:
        @trace_agent("static_analysis")
        async def static_analysis_agent(code_files, _tracer=None):
            # _tracer is automatically injected
            result = await analyze_code(code_files)
            
            # Track LLM calls
            response = await llm.ainvoke(prompt)
            if _tracer:
                _tracer.add_tokens(
                    response.usage_metadata['input_tokens'],
                    response.usage_metadata['output_tokens'],
                    "claude-sonnet-4-20250514"
                )
            
            return result
    """
    def decorator(func: Callable):
        @observe(name=agent_name)
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = AgentTracer(agent_name)
            tracer.start()
            
            try:
                # Inject tracer into function
                result = await func(*args, **kwargs, _tracer=tracer)
                tracer.end(success=True)
                return result
            except Exception as e:
                tracer.end(success=False, error=str(e))
                raise
        
        @observe(name=agent_name)
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = AgentTracer(agent_name)
            tracer.start()
            
            try:
                result = func(*args, **kwargs, _tracer=tracer)
                tracer.end(success=True)
                return result
            except Exception as e:
                tracer.end(success=False, error=str(e))
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def create_review_trace(review_id: str, repository_url: str = None):
    """
    Create a top-level trace for a code review
    
    Args:
        review_id: Unique review identifier
        repository_url: Repository being reviewed (optional)
    
    Returns:
        Langfuse trace object
    """
    trace = langfuse.trace(
        name="code-review",
        user_id=review_id,
        metadata={
            "review_id": review_id,
            "repository_url": repository_url,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    return trace


def score_agent_output(agent_name: str, quality_score: float, comment: str = None):
    """
    Score an agent's output quality
    
    Args:
        agent_name: Name of the agent
        quality_score: Quality score from 0.0 to 1.0
        comment: Optional explanation
    """
    if not langfuse_context.get_current_trace_id():
        return
    
    langfuse.score(
        trace_id=langfuse_context.get_current_trace_id(),
        name=f"{agent_name}_quality",
        value=quality_score,
        comment=comment
    )


def log_issue_found(agent_name: str, issue_data: Dict[str, Any]):
    """
    Log when an agent finds an issue
    
    Args:
        agent_name: Name of the agent
        issue_data: Issue details
    """
    if not langfuse_context.get_current_observation_id():
        return
    
    langfuse_context.update_current_observation(
        metadata={
            "issue_found": True,
            "issue_severity": issue_data.get("severity"),
            "issue_category": issue_data.get("category"),
            "issue_file": issue_data.get("file_path"),
            "issue_line": issue_data.get("line_number")
        }
    )


def log_cost_warning(review_id: str, current_cost: float, limit: float):
    """
    Log when cost approaches limit
    
    Args:
        review_id: Review identifier
        current_cost: Current cost in USD
        limit: Cost limit in USD
    """
    langfuse.score(
        trace_id=review_id,
        name="cost_warning",
        value=current_cost / limit,
        comment=f"Cost ${current_cost:.2f} approaching limit ${limit:.2f}"
    )


class ObservabilityContext:
    """
    Context manager for observability
    
    Usage:
        with ObservabilityContext("database_query") as ctx:
            result = await db.query(...)
            ctx.add_metadata(rows=len(result))
    """
    
    def __init__(self, operation_name: str, metadata: Dict[str, Any] = None):
        self.operation_name = operation_name
        self.metadata = metadata or {}
        self.start_time: Optional[datetime] = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        # Log the operation
        if langfuse_context.get_current_trace_id():
            langfuse.score(
                trace_id=langfuse_context.get_current_trace_id(),
                name=f"{self.operation_name}_duration",
                value=duration,
                comment=f"Duration: {duration:.2f}s"
            )
    
    def add_metadata(self, **kwargs):
        """Add metadata during execution"""
        self.metadata.update(kwargs)
