"""
Configuration management for IBKR workflows
Handles environment variables and workflow settings
"""
import os
from typing import List, Optional


class WorkflowConfig:
    """Centralized configuration for IBKR workflows"""
    
    def __init__(self):
        # Database configuration
        self.db_host = os.getenv('POSTGRES_HOST', 'postgres')
        self.db_port = os.getenv('POSTGRES_PORT', '5432')
        self.db_name = os.getenv('POSTGRES_DB', 'postgres')
        self.db_user = os.getenv('POSTGRES_USER', 'postgres')
        self.db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        
        # MLflow configuration
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow-server:5500')
        self.mlflow_experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'ibkr-stock-data')
        
        # Workflow configuration
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.stock_symbols = self._parse_stock_symbols(os.getenv('STOCK_SYMBOLS', 'TSLA,NVDA'))
        
        # Environment
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        # LLM configuration
        self.llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        self.llm_api_base_url = os.getenv('LLM_API_BASE_URL', os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'))
        self.llm_api_key = os.getenv('LLM_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        self.llm_model = os.getenv('LLM_MODEL', os.getenv('OPENAI_MODEL', 'gpt-4o'))
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.anthropic_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
    
    @staticmethod
    def _parse_stock_symbols(symbols_str: str) -> List[str]:
        """Parse comma-separated stock symbols"""
        if not symbols_str:
            return ['TSLA', 'NVDA']
        
        symbols = [s.strip().upper() for s in symbols_str.split(',')]
        # Validate format (basic validation)
        valid_symbols = [s for s in symbols if s.isalnum() and len(s) <= 5]
        
        if not valid_symbols:
            return ['TSLA', 'NVDA']
        
        return valid_symbols
    
    @property
    def database_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    def get_log_level(self) -> str:
        """Get appropriate log level based on debug mode"""
        return 'DEBUG' if self.debug_mode else 'INFO'
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (for MLflow logging)"""
        return {
            'debug_mode': self.debug_mode,
            'stock_symbols': ','.join(self.stock_symbols),
            'environment': self.environment,
            'mlflow_experiment': self.mlflow_experiment_name,
            'db_host': self.db_host,
            'db_name': self.db_name,
        }


# Global configuration instance
config = WorkflowConfig()

