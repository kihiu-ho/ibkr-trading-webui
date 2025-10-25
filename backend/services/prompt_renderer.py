"""
Jinja2 Prompt Template Renderer Service

Provides full Jinja2 template rendering with custom filters, context builders,
and error handling for LLM prompt generation.
"""
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from jinja2 import Environment, TemplateSyntaxError, UndefinedError, meta
from jinja2.sandbox import SandboxedEnvironment

logger = logging.getLogger(__name__)


class PromptRenderer:
    """Renders Jinja2 prompt templates with context and custom filters."""
    
    def __init__(self, use_sandbox: bool = True):
        """
        Initialize the prompt renderer.
        
        Args:
            use_sandbox: If True, use SandboxedEnvironment for security (default: True)
        """
        self.use_sandbox = use_sandbox
        
        # Create Jinja2 environment with autoescape disabled (we're rendering prompts, not HTML)
        if use_sandbox:
            self.env = SandboxedEnvironment(
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self.env = Environment(
                autoescape=False,
                trim_blocks=True,
                lstrip_blocks=True,
            )
        
        # Register custom filters
        self._register_filters()
        
        logger.info(f"PromptRenderer initialized (sandbox={use_sandbox})")
    
    def _register_filters(self):
        """Register custom Jinja2 filters for prompt templates."""
        
        # Number formatting filters
        self.env.filters['round'] = lambda x, precision=2: round(float(x), precision) if x is not None else None
        self.env.filters['abs'] = lambda x: abs(float(x)) if x is not None else None
        self.env.filters['percent'] = lambda x, precision=2: f"{round(float(x) * 100, precision)}%" if x is not None else "N/A"
        self.env.filters['currency'] = lambda x, symbol='$', precision=2: f"{symbol}{round(float(x), precision):,.2f}" if x is not None else "N/A"
        
        # Date formatting filters
        self.env.filters['date'] = lambda x, fmt='%Y-%m-%d': x.strftime(fmt) if isinstance(x, (datetime, date)) else str(x)
        self.env.filters['datetime'] = lambda x, fmt='%Y-%m-%d %H:%M:%S': x.strftime(fmt) if isinstance(x, datetime) else str(x)
        
        # String filters
        self.env.filters['upper'] = lambda x: str(x).upper() if x is not None else ""
        self.env.filters['lower'] = lambda x: str(x).lower() if x is not None else ""
        self.env.filters['title'] = lambda x: str(x).title() if x is not None else ""
        self.env.filters['trim'] = lambda x: str(x).strip() if x is not None else ""
        
        # List filters
        self.env.filters['join'] = lambda x, sep=', ': sep.join([str(i) for i in x]) if isinstance(x, list) else str(x)
        self.env.filters['first'] = lambda x: x[0] if isinstance(x, list) and len(x) > 0 else None
        self.env.filters['last'] = lambda x: x[-1] if isinstance(x, list) and len(x) > 0 else None
        
        # Technical analysis filters
        self.env.filters['trend_label'] = self._trend_label_filter
        self.env.filters['signal_label'] = self._signal_label_filter
        
        logger.debug(f"Registered {len(self.env.filters)} custom Jinja2 filters")
    
    @staticmethod
    def _trend_label_filter(value: Optional[str]) -> str:
        """
        Convert trend value to human-readable label.
        
        Examples:
            'bullish' -> '看漲'
            'strong_bullish' -> '強烈看漲'
        """
        labels = {
            'strong_bullish': '強烈看漲',
            'bullish': '看漲',
            'neutral': '中性',
            'bearish': '看跌',
            'strong_bearish': '強烈看跌',
        }
        return labels.get(value, value if value else '未知')
    
    @staticmethod
    def _signal_label_filter(value: Optional[str]) -> str:
        """Convert signal type to human-readable label."""
        labels = {
            'BUY': '買入',
            'SELL': '賣出',
            'HOLD': '持有',
        }
        return labels.get(value, value if value else '未知')
    
    def render(
        self,
        template_text: str,
        context: Dict[str, Any],
        strict: bool = False
    ) -> str:
        """
        Render a Jinja2 template with provided context.
        
        Args:
            template_text: The Jinja2 template string
            context: Dictionary of variables to pass to template
            strict: If True, raise errors on undefined variables (default: False)
        
        Returns:
            Rendered template as string
        
        Raises:
            TemplateSyntaxError: If template has syntax errors
            UndefinedError: If strict=True and template uses undefined variables
        """
        try:
            template = self.env.from_string(template_text)
            
            # Add global variables
            context['now'] = datetime.now()
            context['today'] = date.today()
            
            # Render template
            rendered = template.render(context)
            
            logger.debug(f"Template rendered successfully ({len(rendered)} chars)")
            return rendered
            
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error at line {e.lineno}: {e.message}")
            raise ValueError(f"Template syntax error at line {e.lineno}: {e.message}") from e
        
        except UndefinedError as e:
            if strict:
                logger.error(f"Undefined variable in template: {e}")
                raise ValueError(f"Undefined variable in template: {e}") from e
            else:
                logger.warning(f"Undefined variable in template (continuing): {e}")
                # In non-strict mode, Jinja2 will render undefined as empty string
                # But we still log it for debugging
                return template.render(context)
        
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise ValueError(f"Error rendering template: {e}") from e
    
    def validate_template(self, template_text: str) -> tuple[bool, Optional[str]]:
        """
        Validate a Jinja2 template for syntax errors.
        
        Args:
            template_text: The template string to validate
        
        Returns:
            Tuple of (is_valid, error_message)
            - (True, None) if valid
            - (False, "error message") if invalid
        """
        try:
            self.env.from_string(template_text)
            return True, None
        
        except TemplateSyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}: {e.message}"
            logger.debug(f"Template validation failed: {error_msg}")
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Validation error: {str(e)}"
            logger.debug(f"Template validation failed: {error_msg}")
            return False, error_msg
    
    def get_undefined_variables(self, template_text: str, context: Dict[str, Any]) -> List[str]:
        """
        Get list of undefined variables in template given a context.
        
        Args:
            template_text: The template string
            context: The context to check against
        
        Returns:
            List of undefined variable names
        """
        try:
            # Get all undeclared variables from template
            ast = self.env.parse(template_text)
            undeclared = meta.find_undeclared_variables(ast)
            
            # Filter out variables that are in context or are globals
            globals_vars = {'now', 'today'}
            undefined = [var for var in undeclared if var not in context and var not in globals_vars]
            
            return undefined
        
        except Exception as e:
            logger.warning(f"Could not determine undefined variables: {e}")
            return []


class PromptContextBuilder:
    """Builds context dictionaries for prompt template rendering."""
    
    @staticmethod
    def build_analysis_context(
        symbol: str,
        exchange: Optional[str] = None,
        current_price: Optional[float] = None,
        timeframe: Optional[str] = None,
        market_data: Optional[Dict[str, Any]] = None,
        indicators: Optional[Dict[str, Any]] = None,
        strategy_params: Optional[Dict[str, Any]] = None,
        previous_analyses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build context for chart analysis prompts.
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            exchange: Exchange name (e.g., 'NASDAQ')
            current_price: Current/latest price
            timeframe: Chart timeframe (e.g., '1d', '1w')
            market_data: Market data dict with OHLCV
            indicators: Technical indicators dict
            strategy_params: Strategy-specific parameters
            previous_analyses: Previous analysis results for context
        
        Returns:
            Context dictionary for template rendering
        """
        context = {
            'symbol': symbol,
            'exchange': exchange,
            'current_price': current_price,
            'timeframe': timeframe or '1d',
        }
        
        # Add market data if available
        if market_data:
            context.update({
                'open': market_data.get('open'),
                'high': market_data.get('high'),
                'low': market_data.get('low'),
                'close': market_data.get('close'),
                'volume': market_data.get('volume'),
            })
        
        # Add indicators if available
        if indicators:
            context['indicators'] = indicators
            # Flatten common indicators to top level for easy access
            context.update({
                'atr': indicators.get('atr'),
                'rsi': indicators.get('rsi'),
                'macd': indicators.get('macd'),
                'supertrend': indicators.get('supertrend'),
                'ma20': indicators.get('ma20'),
                'ma50': indicators.get('ma50'),
                'ma200': indicators.get('ma200'),
                'bollinger': indicators.get('bollinger'),
            })
        
        # Add strategy parameters
        if strategy_params:
            context['strategy'] = strategy_params
        
        # Add previous analyses for multi-step workflows
        if previous_analyses:
            context['previous_analyses'] = previous_analyses
            # Make daily and weekly analyses easily accessible
            for analysis in previous_analyses:
                if analysis.get('timeframe') == '1d':
                    context['analysis_daily'] = analysis.get('result')
                elif analysis.get('timeframe') == '1w':
                    context['analysis_weekly'] = analysis.get('result')
        
        return context
    
    @staticmethod
    def build_consolidation_context(
        symbol: str,
        analyses: List[Dict[str, Any]],
        final_signal: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Build context for consolidation/final report prompts.
        
        Args:
            symbol: Stock symbol
            analyses: List of analysis results from different timeframes
            final_signal: Final trading signal/decision
            **kwargs: Additional context variables
        
        Returns:
            Context dictionary for template rendering
        """
        context = {
            'symbol': symbol,
            'analyses': analyses,
        }
        
        # Extract specific analyses by timeframe
        for analysis in analyses:
            tf = analysis.get('timeframe')
            if tf == '1d':
                context['analysis_daily'] = analysis.get('result')
            elif tf == '1w':
                context['analysis_weekly'] = analysis.get('result')
        
        # Add final signal if available
        if final_signal:
            context['signal'] = final_signal
        
        # Add any additional context
        context.update(kwargs)
        
        return context


# Singleton instance
_renderer_instance: Optional[PromptRenderer] = None


def get_prompt_renderer(use_sandbox: bool = True) -> PromptRenderer:
    """
    Get the singleton PromptRenderer instance.
    
    Args:
        use_sandbox: Whether to use sandboxed environment (default: True)
    
    Returns:
        PromptRenderer instance
    """
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = PromptRenderer(use_sandbox=use_sandbox)
    return _renderer_instance

