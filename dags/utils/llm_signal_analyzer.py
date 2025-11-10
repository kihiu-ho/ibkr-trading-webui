"""
LLM-based trading signal generation from chart analysis
"""
import logging
import base64
from typing import Optional
from decimal import Decimal
import json
import os

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("openai not installed. OpenAI integration will be mocked.")

try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logging.warning("anthropic not installed. Anthropic integration will be mocked.")

from models.chart import ChartResult
from models.signal import TradingSignal, SignalAction, SignalConfidence
from models.market_data import MarketData

logger = logging.getLogger(__name__)


ANALYSIS_PROMPT = """You are a professional technical analyst specializing in medium-term trading (30-180 days holding period) based on daily and weekly candle charts. Please analyze using the following framework.

You are provided with:
1. A DAILY chart showing recent price action and technical indicators (primary analysis)
2. A WEEKLY chart for longer-term trend confirmation

Please provide a comprehensive analysis following this structured framework:

## 1. Core Price Analysis
- Current price and trend overview
- Key support/resistance levels
- Important candlestick patterns and price structure
- Chart time range: Daily chart (primary) and Weekly chart (confirmation)

## 2. Trend Indicator Analysis

A. SuperTrend (10,3):
   - Current state: [uptrend/downtrend]
   - Signal color: [green/red]
   - Relative position to price and recent changes

B. Moving Average System:
   - 20-day SMA: Short-term trend direction
   - 50-day SMA: Medium-term trend direction
   - 200-day SMA: Long-term trend direction
   - Golden/Death cross situations
   - Price relationship to moving averages (support/resistance)

## 3. Confirmation Indicator Analysis

A. Momentum Confirmation:
   - MACD (12,26,9): Status and signals
   - RSI (14): Levels and direction [overbought/oversold/neutral]

B. Volatility Analysis:
   - ATR (14): Values and trends
   - Bollinger Bands (20,2): Width and price position

C. Volume Analysis:
   - Current volume vs 20-day average
   - Volume trend characteristics
   - OBV trends and price confirmation

## 4. Signal Confirmation System (3/4 Rule)
At least 3 of 4 signals must confirm the trading direction:
- SuperTrend signal direction [bullish/bearish]
- Price relationship to 20-day SMA [above/below]
- MACD signal line crossover [buy/sell]
- RSI relative position [>50 bullish/<50 bearish]

## 5. Trading Recommendations
- Overall trend judgment: [strongly bullish/bullish/neutral/bearish/strongly bearish]
- Trading signal: [entry/hold/exit]

A. If bullish (long):
   - Entry price range: [price range]
   - Stop loss: Entry price - (2 × ATR), approximately [specific value]
   - Profit targets:
     * First target (conservative): [value] - Based on [support/resistance/chart pattern/indicator level]
     * Second target (aggressive): [value] - Based on [support/resistance/chart pattern/indicator level]
   - R-multiple calculation: (Target - Entry) ÷ (Entry - Stop Loss) = ?R

B. If bearish (short):
   - Entry price range: [price range]
   - Stop loss: Entry price + (2 × ATR), approximately [specific value]
   - Profit targets:
     * First target (conservative): [value] - Based on [support/resistance/chart pattern/indicator level]
     * Second target (aggressive): [value] - Based on [support/resistance/chart pattern/indicator level]
   - R-multiple calculation: (Entry - Target) ÷ (Stop Loss - Entry) = ?R

- Suggested position size: [% based on fixed risk management]

## Target Price Setting Reference Framework
When setting target prices, consider these technical factors:
1. Previous support/resistance levels: Historical highs/lows, trading dense areas
2. Chart pattern projections: Head and shoulders, triangles, flags, wedges, etc.
3. Fibonacci levels: Extensions (127.2%, 161.8%) or retracements (38.2%, 50%, 61.8%)
4. Bollinger Band targets: Upper/lower bands or width projections
5. Moving average targets: Important EMA/SMA positions or crossover points
6. Volume targets: Volume distribution peaks, volume force field highs/lows
7. Volatility projections: Based on ATR (e.g., 3×ATR volatility range)

Each target price must include at least one technical basis and explain why it is a reasonable price target.

## 6. Risk Assessment
- Main technical risk factors
- Key reversal prices and alert points
- Potential signal failure scenarios
- Weekly chart confirmation status
- How to manage and mitigate identified risks

## Response Format
Respond ONLY with valid JSON in this exact format:
{
  "action": "BUY|SELL|HOLD",
  "confidence": "HIGH|MEDIUM|LOW",
  "confidence_score": 85.5,
  "reasoning": "Detailed explanation covering all 6 sections above (minimum 200 words)...",
  "key_factors": ["Factor 1", "Factor 2", "Factor 3", "Factor 4", "Factor 5"],
  "trend": "strongly bullish|bullish|neutral|bearish|strongly bearish",
  "support_level": 245.00,
  "resistance_level": 265.00,
  "suggested_entry_price": 250.00,
  "suggested_stop_loss": 245.00,
  "suggested_take_profit": 265.00,
  "r_multiple": 2.5,
  "position_size_percent": 5.0
}

Important: Only recommend BUY/SELL when at least 3 of 4 signals confirm. Be conservative and focus on risk management. Weekly chart analysis serves as trend confirmation only - do not provide separate weekly trend confirmation analysis in the response.
"""


class LLMSignalAnalyzer:
    """LLM-based trading signal analyzer"""
    
    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize LLM analyzer
        
        Args:
            provider: LLM provider ("openai" or "anthropic"), defaults to LLM_PROVIDER env var
            model: Model name (uses env var LLM_MODEL/OPENAI_MODEL/ANTHROPIC_MODEL if None)
            api_key: API key (uses env var LLM_API_KEY/OPENAI_API_KEY/ANTHROPIC_API_KEY if None)
            base_url: Base URL for API (uses env var LLM_API_BASE_URL/OPENAI_API_BASE if None)
        """
        # Get provider from parameter or environment
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
        
        if self.provider == "openai":
            self.model = model or os.getenv("LLM_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o"))
            if OPENAI_AVAILABLE:
                try:
                    api_key = api_key or os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY")
                    base_url = base_url or os.getenv("LLM_API_BASE_URL") or os.getenv("OPENAI_API_BASE")
                    
                    if api_key:
                        client_kwargs = {"api_key": api_key}
                        if base_url:
                            client_kwargs["base_url"] = base_url
                            logger.info(f"Using OpenAI API base URL: {base_url}")
                        self.client = OpenAI(**client_kwargs)
                    else:
                        self.client = None
                        logger.warning("Running in MOCK mode - OPENAI_API_KEY/LLM_API_KEY not set")
                except Exception as e:
                    self.client = None
                    logger.warning(f"Running in MOCK mode - OpenAI initialization failed: {e}")
            else:
                self.client = None
                logger.warning("Running in MOCK mode - openai not available")
        
        elif self.provider == "anthropic":
            self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
            if ANTHROPIC_AVAILABLE:
                try:
                    api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
                    if api_key:
                        self.client = Anthropic(api_key=api_key)
                    else:
                        self.client = None
                        logger.warning("Running in MOCK mode - ANTHROPIC_API_KEY not set")
                except Exception as e:
                    self.client = None
                    logger.warning(f"Running in MOCK mode - Anthropic initialization failed: {e}")
            else:
                self.client = None
                logger.warning("Running in MOCK mode - anthropic not available")
        
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Chart file not found: {image_path}")
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def analyze_charts(
        self,
        symbol: str,
        daily_chart: ChartResult,
        weekly_chart: ChartResult,
        market_data: Optional[MarketData] = None
    ) -> TradingSignal:
        """
        Analyze charts and generate trading signal
        
        Args:
            symbol: Stock symbol
            daily_chart: Daily timeframe chart
            weekly_chart: Weekly timeframe chart
            market_data: Optional market data for context
            
        Returns:
            TradingSignal with LLM recommendation
        """
        if self.client is None:
            return self._mock_signal(symbol)
        
        try:
            # Encode charts
            daily_image = self.encode_image(daily_chart.file_path)
            weekly_image = self.encode_image(weekly_chart.file_path)
            
            # Add market context if available
            context_info = ""
            if market_data:
                latest_price = market_data.latest_price
                context_info = f"\n\nCurrent price: ${latest_price}"
            
            if self.provider == "openai":
                signal = self._analyze_with_openai(
                    symbol, daily_image, weekly_image, context_info
                )
            else:
                signal = self._analyze_with_anthropic(
                    symbol, daily_image, weekly_image, context_info
                )
            
            logger.info(f"Generated {signal.action} signal with {signal.confidence} confidence for {symbol}")
            return signal
        
        except (FileNotFoundError, Exception) as e:
            logger.warning(f"Failed to analyze charts with LLM ({e}), falling back to mock signal")
            return self._mock_signal(symbol)
    
    def _analyze_with_openai(
        self,
        symbol: str,
        daily_image: str,
        weekly_image: str,
        context_info: str
    ) -> TradingSignal:
        """Analyze with OpenAI GPT-4 Vision"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ANALYSIS_PROMPT + context_info
                        },
                        {
                            "type": "text",
                            "text": "Daily Chart:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{daily_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Weekly Chart:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{weekly_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=2000,
            temperature=0.3
        )
        
        # Parse response
        content = response.choices[0].message.content
        signal_data = json.loads(content)
        
        return self._create_signal(symbol, signal_data, "openai")
    
    def _analyze_with_anthropic(
        self,
        symbol: str,
        daily_image: str,
        weekly_image: str,
        context_info: str
    ) -> TradingSignal:
        """Analyze with Anthropic Claude"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": ANALYSIS_PROMPT + context_info
                        },
                        {
                            "type": "text",
                            "text": "Daily Chart:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": daily_image
                            }
                        },
                        {
                            "type": "text",
                            "text": "Weekly Chart:"
                        },
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": weekly_image
                            }
                        }
                    ]
                }
            ]
        )
        
        # Parse response
        content = response.content[0].text
        signal_data = json.loads(content)
        
        return self._create_signal(symbol, signal_data, "anthropic")
    
    def _create_signal(self, symbol: str, signal_data: dict, provider: str) -> TradingSignal:
        """Create TradingSignal from parsed JSON"""
        return TradingSignal(
            symbol=symbol,
            action=SignalAction(signal_data["action"]),
            confidence=SignalConfidence(signal_data["confidence"]),
            confidence_score=Decimal(str(signal_data["confidence_score"])),
            reasoning=signal_data["reasoning"],
            key_factors=signal_data["key_factors"],
            trend=signal_data.get("trend"),
            support_level=Decimal(str(signal_data["support_level"])) if signal_data.get("support_level") else None,
            resistance_level=Decimal(str(signal_data["resistance_level"])) if signal_data.get("resistance_level") else None,
            suggested_entry_price=Decimal(str(signal_data["suggested_entry_price"])) if signal_data.get("suggested_entry_price") else None,
            suggested_stop_loss=Decimal(str(signal_data["suggested_stop_loss"])) if signal_data.get("suggested_stop_loss") else None,
            suggested_take_profit=Decimal(str(signal_data["suggested_take_profit"])) if signal_data.get("suggested_take_profit") else None,
            r_multiple=Decimal(str(signal_data["r_multiple"])) if signal_data.get("r_multiple") else None,
            position_size_percent=Decimal(str(signal_data["position_size_percent"])) if signal_data.get("position_size_percent") else None,
            timeframe_analyzed="daily+weekly",
            model_used=f"{provider}/{self.model}"
        )
    
    def _mock_signal(self, symbol: str) -> TradingSignal:
        """Generate mock signal for testing"""
        logger.info(f"MOCK: Generating trading signal for {symbol}")
        
        return TradingSignal(
            symbol=symbol,
            action=SignalAction.BUY,
            confidence=SignalConfidence.MEDIUM,
            confidence_score=Decimal("72.5"),
            reasoning="MOCK: Strong bullish momentum observed on daily chart with price breaking above 50-day SMA. "
                     "Weekly chart confirms uptrend with higher highs and higher lows. RSI at 58 indicates room for upside. "
                     "MACD showing positive divergence. Volume increasing on up days. Conservative entry recommended with "
                     "stop loss below recent support at $245.",
            key_factors=[
                "Breakout above 50-day SMA",
                "Weekly uptrend intact",
                "RSI at healthy 58 level",
                "MACD positive divergence",
                "Increasing volume on rallies"
            ],
            trend="bullish",
            support_level=Decimal("245.00"),
            resistance_level=Decimal("265.00"),
            suggested_entry_price=Decimal("250.00"),
            suggested_stop_loss=Decimal("245.00"),
            suggested_take_profit=Decimal("265.00"),
            timeframe_analyzed="daily+weekly",
            model_used="mock/test"
        )

