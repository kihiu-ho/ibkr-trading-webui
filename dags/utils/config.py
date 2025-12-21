"""Configuration management for IBKR workflows."""
import os
from typing import List, Optional
from urllib.parse import urlparse


class WorkflowConfig:
    """Centralized configuration for IBKR workflows"""
    
    def __init__(self):
        # Database configuration
        self.db_host = os.getenv('POSTGRES_HOST', 'postgres')
        self.db_port = os.getenv('POSTGRES_PORT', '5432')
        self.db_name = os.getenv('POSTGRES_DB', 'postgres')
        self.db_user = os.getenv('POSTGRES_USER', 'postgres')
        self.db_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
        self._database_url_env = os.getenv('DATABASE_URL')
        self.neon_database_url = os.getenv('NEON_DATABASE', self._database_url_env)
        if self._database_url_env:
            self._apply_database_url(self._database_url_env)
        
        # MLflow configuration
        self.mlflow_tracking_uri = os.getenv('MLFLOW_TRACKING_URI', 'http://mlflow-server:5500')
        self.mlflow_experiment_name = os.getenv('MLFLOW_EXPERIMENT_NAME', 'ibkr-stock-data')
        
        # Workflow configuration
        self.debug_mode = os.getenv('DEBUG_MODE', 'false').lower() == 'true'
        self.stock_symbols = self._parse_stock_symbols(os.getenv('STOCK_SYMBOLS', 'TSLA,NVDA'))
        self.market_data_duration = self._parse_duration(os.getenv('MARKET_DATA_DURATION', '1 Y'))
        self.market_data_bar_size = self._parse_bar_size(os.getenv('MARKET_DATA_BAR_SIZE', '1 day'))

        # Environment
        self.environment = (os.getenv('ENVIRONMENT', 'development') or 'development').strip()
        env_lower = self.environment.lower()
        strict_default = env_lower not in {'development', 'dev', 'test', 'testing'}
        self.ibkr_strict_mode = self._parse_bool_env(
            os.getenv('IBKR_STRICT_MODE'),
            default=strict_default
        )
        self.ibkr_host = self._parse_host(os.getenv('IBKR_HOST'), default='ibkr-gateway')
        self.ibkr_port = self._parse_int(os.getenv('IBKR_PORT', '4002'), default=4002)

        # LLM configuration
        self.llm_provider = os.getenv('LLM_PROVIDER', 'openai').lower()
        self.llm_api_base_url = os.getenv('LLM_API_BASE_URL', os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1'))
        self.llm_api_key = os.getenv('LLM_API_KEY', os.getenv('OPENAI_API_KEY', ''))
        self.llm_model = os.getenv('LLM_MODEL', os.getenv('OPENAI_MODEL', 'gpt-4o'))
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.anthropic_model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        self.llm_vision_model = os.getenv('LLM_VISION_MODEL', 'gpt-4o-mini-vision')

        # FinAgent-specific configuration
        self.finagent_enabled = os.getenv('FINAGENT_ENABLED', 'false').lower() == 'true'
        self.finagent_model_path = os.getenv('FINAGENT_MODEL_PATH', 'reference/finagent_runtime')
        self.finagent_prompts_version = (os.getenv('FINAGENT_PROMPTS_VERSION', 'v1') or 'v1').strip().lower()
        try:
            self.finagent_reflection_rounds = max(1, int(os.getenv('FINAGENT_REFLECTION_ROUNDS', '2') or 2))
        except ValueError:
            self.finagent_reflection_rounds = 2
        self.finagent_toolkit = self._parse_tool_list(os.getenv('FINAGENT_TOOLKIT', 'technical_indicators,news_memory'))

        # FinAgent AutoGen pipeline (new DAG)
        self.finagent_autogen_enabled = os.getenv('FINAGENT_AUTOGEN_ENABLED', 'false').lower() == 'true'
        self.finagent_autogen_default_mode = (os.getenv('FINAGENT_AUTOGEN_DEFAULT_MODE', 'inference') or 'inference').strip().lower()
        self.finagent_autogen_max_rounds = self._parse_int(os.getenv('FINAGENT_AUTOGEN_MAX_ROUNDS', '8'), default=8)
        self.finagent_autogen_backtest_lookback_days = self._parse_int(
            os.getenv('FINAGENT_AUTOGEN_BACKTEST_LOOKBACK_DAYS', '365'),
            default=365,
        )

        # TradeMaster AutoGen pipeline (new DAG)
        self.trademaster_autogen_enabled = os.getenv('TRADEMASTER_AUTOGEN_ENABLED', 'false').lower() == 'true'
        self.trademaster_autogen_default_mode = (os.getenv('TRADEMASTER_AUTOGEN_DEFAULT_MODE', 'both') or 'both').strip().lower()
        self.trademaster_autogen_max_rounds = self._parse_int(os.getenv('TRADEMASTER_AUTOGEN_MAX_ROUNDS', '8'), default=8)
        self.trademaster_autogen_backtest_lookback_days = self._parse_int(
            os.getenv('TRADEMASTER_AUTOGEN_BACKTEST_LOOKBACK_DAYS', '365'),
            default=365,
        )
        self.trademaster_autogen_max_symbols = self._parse_int(
            os.getenv('TRADEMASTER_AUTOGEN_MAX_SYMBOLS', '10'),
            default=10,
        )

        # News API (market intelligence source)
        self.news_api_key = os.getenv('NEWS_API_KEY', '').strip()
        self.news_api_base_url = os.getenv('NEWS_API_BASE_URL', 'https://newsapi.org/v2/everything').strip()
        self.news_api_language = os.getenv('NEWS_API_LANGUAGE', 'en').strip() or 'en'
        self.news_api_sort_by = os.getenv('NEWS_API_SORT_BY', 'publishedAt').strip() or 'publishedAt'
        self.news_api_page_size = self._parse_int(os.getenv('NEWS_API_PAGE_SIZE', '10'), default=10)
        self.news_api_timeout = self._parse_int(os.getenv('NEWS_API_TIMEOUT', '10'), default=10)

        # Vector memory (Weaviate)
        self.weaviate_url = os.getenv('WEAVIATE_URL', '').strip()
        self.weaviate_api_key = os.getenv('WEAVIATE_API_KEY', '').strip()

        # IBKR Client Portal REST API configuration (live market data snapshots)
        api_internal = os.getenv('IBKR_API_BASE_URL_INTERNAL', '')
        self.ibkr_api_base_url = (api_internal or os.getenv('IBKR_API_BASE_URL', '') or '').strip().rstrip('/')
        self.ibkr_api_verify_ssl = self._parse_bool_env(os.getenv('IBKR_API_VERIFY_SSL'), default=False)
        self.ibkr_api_timeout = self._parse_int(os.getenv('IBKR_API_TIMEOUT', '15'), default=15)
        self.ibkr_primary_conid = self._parse_optional_int(os.getenv('IBKR_PRIMARY_CONID'))
    
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
        if self._database_url_env:
            return self._database_url_env
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    @property
    def neon_database_dsn(self) -> Optional[str]:
        """Return psycopg2-friendly DSN for Neon metadata storage."""
        target_url = self.neon_database_url or self.database_url
        if not target_url:
            return None
        return self._normalize_pg_dsn(target_url)
    
    def get_log_level(self) -> str:
        """Get appropriate log level based on debug mode"""
        return 'DEBUG' if self.debug_mode else 'INFO'
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (for MLflow logging)"""
        return {
            'debug_mode': self.debug_mode,
            'stock_symbols': ','.join(self.stock_symbols),
            'market_data_duration': self.market_data_duration,
            'market_data_bar_size': self.market_data_bar_size,
            'environment': self.environment,
            'mlflow_experiment': self.mlflow_experiment_name,
            'db_host': self.db_host,
            'db_name': self.db_name,
            'ibkr_strict_mode': str(self.ibkr_strict_mode),
            'ibkr_host': self.ibkr_host,
            'ibkr_port': str(self.ibkr_port),
            'ibkr_api_base_url': self.ibkr_api_base_url,
            'ibkr_api_verify_ssl': str(self.ibkr_api_verify_ssl),
            'ibkr_api_timeout': str(self.ibkr_api_timeout),
            'ibkr_primary_conid': str(self.ibkr_primary_conid or ''),
            'finagent_enabled': str(self.finagent_enabled),
            'finagent_reflection_rounds': self.finagent_reflection_rounds,
            'has_weaviate': str(bool(self.weaviate_url)),
            'has_neon_database': str(bool(self.neon_database_url)),
            'finagent_prompts_version': self.finagent_prompts_version,
            'has_news_api_key': str(bool(self.news_api_key)),
            'finagent_autogen_enabled': str(self.finagent_autogen_enabled),
            'finagent_autogen_default_mode': self.finagent_autogen_default_mode,
            'finagent_autogen_max_rounds': str(self.finagent_autogen_max_rounds),
            'trademaster_autogen_enabled': str(self.trademaster_autogen_enabled),
            'trademaster_autogen_default_mode': self.trademaster_autogen_default_mode,
            'trademaster_autogen_max_rounds': str(self.trademaster_autogen_max_rounds),
            'trademaster_autogen_max_symbols': str(self.trademaster_autogen_max_symbols),
        }

    def _apply_database_url(self, url: str) -> None:
        """Parse DATABASE_URL and override host/user/port/name values."""
        parsed = urlparse(self._normalize_pg_dsn(url))
        if parsed.hostname:
            self.db_host = parsed.hostname
        if parsed.port:
            self.db_port = str(parsed.port)
        if parsed.path and len(parsed.path) > 1:
            self.db_name = parsed.path.lstrip('/')
        if parsed.username:
            self.db_user = parsed.username
        if parsed.password:
            self.db_password = parsed.password

    @staticmethod
    def _normalize_pg_dsn(url: str) -> str:
        """Convert SQLAlchemy-style URLs into psycopg2 compatible DSNs."""
        if not url:
            return url
        if '+psycopg2' in url:
            return url.replace('+psycopg2', '')
        return url

    @staticmethod
    def _parse_tool_list(value: str) -> List[str]:
        if not value:
            return []
        return [chunk.strip() for chunk in value.split(',') if chunk.strip()]

    @staticmethod
    def _parse_duration(value: str) -> str:
        """Normalize IBKR duration strings, defaulting to one year of data."""
        normalized = (value or '').strip()
        return normalized or '1 Y'

    @staticmethod
    def _parse_bar_size(value: str) -> str:
        """Normalize IBKR bar size strings."""
        normalized = (value or '').strip()
        return normalized or '1 day'

    @staticmethod
    def _parse_int(value: Optional[str], default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _parse_optional_int(value: Optional[str]) -> Optional[int]:
        if value is None:
            return None
        value_str = value.strip()
        if not value_str:
            return None
        try:
            return int(value_str)
        except ValueError:
            return None

    @staticmethod
    def _parse_bool_env(value: Optional[str], default: bool = False) -> bool:
        """Convert env strings such as 'true'/'false' into booleans with default fallback."""
        if value is None:
            return default
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}

    @staticmethod
    def _parse_host(value: Optional[str], default: str) -> str:
        host = (value or '').strip()
        return host or default


# Global configuration instance
config = WorkflowConfig()
