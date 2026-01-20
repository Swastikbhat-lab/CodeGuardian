"""Langfuse Observability"""
from langfuse import Langfuse
from core.config import get_settings
import time

settings = get_settings()

# Initialize Langfuse client
langfuse_client = None
if settings.langfuse_public_key and settings.langfuse_secret_key:
    try:
        langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host
        )
    except:
        langfuse_client = None


class AgentTracer:
    """Track agent execution"""
    
    def __init__(self, trace_name: str):
        self.trace_name = trace_name
        self.generations = {}
    
    def start_span(self, agent_name: str, input_data: dict = None):
        """Start tracking an agent"""
        self.generations[agent_name] = {
            'start_time': time.time(),
            'input': input_data
        }
    
    def end_span(self, agent_name: str, output_data: dict = None, tokens: int = 0, cost: float = 0.0):
        """End tracking an agent"""
        if agent_name not in self.generations or not langfuse_client:
            return
        
        gen_data = self.generations[agent_name]
        duration = time.time() - gen_data['start_time']
        
        # Log to Langfuse
        try:
            langfuse_client.generation(
                name=f"{self.trace_name}_{agent_name}",
                input=gen_data['input'],
                output=output_data,
                usage={
                    'total': tokens,
                    'input': int(tokens * 0.4),
                    'output': int(tokens * 0.6)
                },
                metadata={
                    'duration_seconds': duration,
                    'cost_usd': cost
                }
            )
        except Exception as e:
            print(f"   Langfuse logging error: {e}")
    
    def finish(self):
        """Finish the trace"""
        if langfuse_client:
            try:
                langfuse_client.flush()
            except:
                pass


def calculate_cost(input_tokens: int, output_tokens: int, model: str = "claude-sonnet-4") -> float:
    """Calculate cost based on tokens"""
    input_cost_per_1m = 3.00
    output_cost_per_1m = 15.00
    
    input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
    output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
    
    return input_cost + output_cost
