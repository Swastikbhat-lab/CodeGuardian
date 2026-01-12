"""
Core configuration for CodeGuardian

This module manages all application settings using Pydantic for validation.
Settings are loaded from environment variables (.env file).
"""
from typing import List
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # ============================================
    # APPLICATION
    # ============================================
    app_name: str = "CodeGuardian"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # ============================================
    # API KEYS
    # ============================================
    anthropic_api_key: str
    
    # Observability
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "https://cloud.langfuse.com"
    
    # GitHub (optional)
    github_token: str | None = None
    
    # ============================================
    # DATABASE
    # ============================================
    database_url: str
    redis_url: str
    
    # ============================================
    # COST & RESOURCE LIMITS
    # ============================================
    max_cost_per_review: float = 5.0
    max_tokens_per_review: int = 100000
    max_file_size_mb: int = 10
    
    # ============================================
    # AGENT CONFIGURATION
    # ============================================
    enable_static_analysis: bool = True
    enable_security_scan: bool = True
    enable_logic_analysis: bool = True
    enable_test_generation: bool = True
    enable_auto_fix: bool = False
    
    parallel_agent_execution: bool = True
    max_parallel_agents: int = 4
    
    # Supported languages
    supported_languages: str = "python,javascript,typescript"
    
    # ============================================
    # CLAUDE MODELS
    # ============================================
    primary_model: str = "claude-sonnet-4-20250514"
    quick_model: str = "claude-haiku-4-20250514"
    analysis_temperature: float = 0.3
    
    # ============================================
    # SECURITY
    # ============================================
    secret_key: str
    access_token_expire_minutes: int = 30
    
    # ============================================
    # FRONTEND
    # ============================================
    cors_origins: str = "http://localhost:3000,http://localhost:5173"
    
    # ============================================
    # DERIVED PROPERTIES
    # ============================================
    @property
    def supported_languages_list(self) -> List[str]:
        """Get list of supported languages"""
        return [lang.strip() for lang in self.supported_languages.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get list of CORS origins"""
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    
    Using @lru_cache ensures we only load settings once
    """
    return Settings()


# ============================================
# COST TRACKING
# ============================================
# Claude API pricing (as of Jan 2025)
COST_PER_1K_TOKENS = {
    "claude-sonnet-4-20250514": {
        "input": 0.003,   # $3 per 1M input tokens
        "output": 0.015,  # $15 per 1M output tokens
    },
    "claude-haiku-4-20250514": {
        "input": 0.00025,  # $0.25 per 1M input tokens
        "output": 0.00125, # $1.25 per 1M output tokens
    }
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost for an LLM API call
    
    Args:
        model: Model name (e.g., "claude-sonnet-4-20250514")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Cost in USD
    
    Example:
        >>> calculate_cost("claude-sonnet-4-20250514", 1000, 500)
        0.0105  # $0.0105
    """
    if model not in COST_PER_1K_TOKENS:
        return 0.0
    
    rates = COST_PER_1K_TOKENS[model]
    input_cost = (input_tokens / 1000) * rates["input"]
    output_cost = (output_tokens / 1000) * rates["output"]
    
    return round(input_cost + output_cost, 6)


def estimate_tokens(text: str) -> int:
    """
    Rough estimation of token count
    
    Rule of thumb: ~4 characters per token for code
    
    Args:
        text: Text to estimate tokens for
    
    Returns:
        Estimated token count
    """
    return len(text) // 4


# ============================================
# MODEL SELECTION
# ============================================
def select_model(complexity: str, settings: Settings = None) -> str:
    """
    Select appropriate model based on task complexity
    
    Args:
        complexity: "high", "medium", or "low"
        settings: Application settings (optional)
    
    Returns:
        Model name to use
    
    Example:
        >>> select_model("high")
        "claude-sonnet-4-20250514"
        >>> select_model("low")
        "claude-haiku-4-20250514"
    """
    if settings is None:
        settings = get_settings()
    
    if complexity in ["high", "critical", "complex"]:
        return settings.primary_model
    else:
        return settings.quick_model
