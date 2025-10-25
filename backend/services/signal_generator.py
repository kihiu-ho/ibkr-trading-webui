"""
Signal Generator Service - Orchestrates multi-timeframe chart analysis.

Coordinates chart generation, LLM analysis, and signal extraction.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from backend.services.chart_generator import ChartGenerator
from backend.services.llm_service import LLMService
from backend.config.settings import settings

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Service for generating trading signals using LLM chart analysis."""
    
    def __init__(self, db_session=None):
        self.chart_generator = ChartGenerator()
        self.llm_service = LLMService(db_session=db_session)
        
    async def generate_signal(
        self,
        symbol: str,
        timeframes: list[str] = None,
        consolidate: bool = None,
        strategy_id: Optional[int] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate a complete trading signal for a symbol.
        
        Args:
            symbol: Stock symbol (e.g., "TSLA")
            timeframes: List of timeframes to analyze (default: ["1d", "1w"])
            consolidate: Whether to consolidate analyses (default: from settings)
            strategy_id: Strategy ID for strategy-specific prompts
            language: Language for prompts (en, zh)
            
        Returns:
            Complete signal with charts, analyses, and trading parameters including prompt metadata
        """
        timeframes = timeframes or ["1d", "1w"]
        consolidate = consolidate if consolidate is not None else settings.LLM_CONSOLIDATE_TIMEFRAMES
        
        logger.info(f"Generating signal for {symbol} (timeframes: {timeframes}, strategy_id: {strategy_id}, lang: {language})")
        
        try:
            # 1. Generate charts for all timeframes
            charts = await self._generate_charts(symbol, timeframes)
            
            # 2. Analyze each chart with LLM
            analyses = await self._analyze_charts(charts, symbol, strategy_id, language)
            
            # 3. Consolidate if multiple timeframes
            final_analysis = await self._consolidate_analyses(
                analyses, symbol, consolidate, strategy_id, language
            )
            
            # 4. Extract trading parameters
            signal = self._extract_signal(final_analysis, analyses, charts)
            
            # 5. Calculate R-multiples and position sizing
            signal = self._calculate_trading_params(signal)
            
            # 6. Add metadata
            signal.update({
                "symbol": symbol,
                "timeframes": timeframes,
                "generated_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=24),
                "model_used": settings.LLM_VISION_MODEL,
                "provider": settings.LLM_VISION_PROVIDER
            })
            
            logger.info(f"Signal generated for {symbol}: {signal.get('signal_type', 'UNKNOWN')}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {str(e)}")
            raise
    
    async def _generate_charts(
        self,
        symbol: str,
        timeframes: list[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Generate charts for all requested timeframes."""
        charts = {}
        
        for timeframe in timeframes:
            try:
                period = 200 if timeframe == "1d" else 52 if timeframe == "1w" else 24
                chart = await self.chart_generator.generate_chart(
                    symbol=symbol,
                    timeframe=timeframe,
                    period=period
                )
                charts[timeframe] = chart
                logger.info(f"Chart generated for {symbol} ({timeframe})")
            except Exception as e:
                logger.error(f"Failed to generate {timeframe} chart for {symbol}: {str(e)}")
                # Continue with other timeframes
        
        if not charts:
            raise ValueError(f"Failed to generate any charts for {symbol}")
        
        return charts
    
    async def _analyze_charts(
        self,
        charts: Dict[str, Dict[str, Any]],
        symbol: str,
        strategy_id: Optional[int] = None,
        language: str = "en"
    ) -> Dict[str, Dict[str, Any]]:
        """Analyze each chart with LLM."""
        analyses = {}
        
        for timeframe, chart in charts.items():
            try:
                # Use 'analysis' template type for all timeframes
                # (database templates are categorized by type, not timeframe)
                prompt_template = "analysis"
                
                analysis = await self.llm_service.analyze_chart(
                    chart_url=chart["chart_url_jpeg"],
                    prompt_template=prompt_template,
                    symbol=symbol,
                    strategy_id=strategy_id,
                    language=language,
                    timeframe=timeframe  # Pass as context
                )
                
                analyses[timeframe] = analysis
                logger.info(f"Analysis complete for {symbol} ({timeframe}) with prompt_id={analysis.get('prompt_template_id')}")
            except Exception as e:
                logger.error(f"Failed to analyze {timeframe} chart for {symbol}: {str(e)}")
                # Continue with other analyses
        
        if not analyses:
            raise ValueError(f"Failed to analyze any charts for {symbol}")
        
        return analyses
    
    async def _consolidate_analyses(
        self,
        analyses: Dict[str, Dict[str, Any]],
        symbol: str,
        consolidate: bool,
        strategy_id: Optional[int] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Consolidate multiple timeframe analyses."""
        if not consolidate or len(analyses) == 1:
            # Return primary timeframe analysis (daily if available)
            primary = analyses.get("1d", list(analyses.values())[0])
            return primary
        
        # Get daily and weekly analyses
        daily = analyses.get("1d")
        weekly = analyses.get("1w")
        
        if not daily or not weekly:
            # If we don't have both, return what we have
            return daily or weekly or list(analyses.values())[0]
        
        try:
            # Call LLM to consolidate
            consolidated = await self.llm_service.consolidate_analyses(
                daily_analysis=daily["raw_text"],
                weekly_analysis=weekly["raw_text"],
                symbol=symbol,
                strategy_id=strategy_id,
                language=language
            )
            
            logger.info(f"Analyses consolidated for {symbol} with prompt_id={consolidated.get('prompt_template_id')}")
            return consolidated
            
        except Exception as e:
            logger.error(f"Failed to consolidate analyses for {symbol}: {str(e)}")
            # Fall back to daily analysis
            return daily
    
    def _extract_signal(
        self,
        final_analysis: Dict[str, Any],
        all_analyses: Dict[str, Dict[str, Any]],
        charts: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract trading signal from analysis including prompt metadata."""
        parsed = final_analysis.get("parsed_signal", {})
        
        signal = {
            "signal_type": parsed.get("signal", "HOLD"),
            "trend": parsed.get("trend", "neutral"),
            "confidence": self._calculate_confidence(parsed),
            "entry_price_low": parsed.get("entry_low"),
            "entry_price_high": parsed.get("entry_high"),
            "stop_loss": parsed.get("stop_loss"),
            "target_conservative": parsed.get("target_conservative"),
            "target_aggressive": parsed.get("target_aggressive"),
            "r_multiple_conservative": parsed.get("r_multiple_conservative"),
            "r_multiple_aggressive": parsed.get("r_multiple_aggressive"),
            "position_size_percent": parsed.get("position_size_percent"),
            "confirmation": parsed.get("confirmation", {}),
            "analysis_daily": all_analyses.get("1d", {}).get("raw_text", ""),
            "analysis_weekly": all_analyses.get("1w", {}).get("raw_text", ""),
            "analysis_consolidated": final_analysis.get("raw_text", ""),
            "chart_url_daily": charts.get("1d", {}).get("chart_url_jpeg"),
            "chart_url_weekly": charts.get("1w", {}).get("chart_url_jpeg"),
            "chart_html_daily": charts.get("1d", {}).get("chart_url_html"),
            "chart_html_weekly": charts.get("1w", {}).get("chart_url_html"),
            # Prompt metadata for traceability (from final/consolidated analysis)
            "prompt_template_id": final_analysis.get("prompt_template_id"),
            "prompt_version": final_analysis.get("prompt_version"),
            "prompt_type": final_analysis.get("prompt_type"),
        }
        
        return signal
    
    def _calculate_confidence(self, parsed_signal: Dict[str, Any]) -> float:
        """Calculate signal confidence based on confirmation count."""
        confirmation = parsed_signal.get("confirmation", {})
        confirmed_count = confirmation.get("confirmed_count", 0)
        
        # Confidence based on 3/4 rule
        if confirmed_count >= 3:
            return 0.75 + (confirmed_count - 3) * 0.125  # 75% for 3, 87.5% for 4
        elif confirmed_count == 2:
            return 0.50
        elif confirmed_count == 1:
            return 0.25
        else:
            return 0.0
    
    def _calculate_trading_params(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate R-multiples and validate trading parameters."""
        entry_low = signal.get("entry_price_low")
        entry_high = signal.get("entry_price_high")
        stop_loss = signal.get("stop_loss")
        target_conservative = signal.get("target_conservative")
        target_aggressive = signal.get("target_aggressive")
        
        # Calculate average entry price
        if entry_low and entry_high:
            entry_avg = (entry_low + entry_high) / 2
        else:
            entry_avg = entry_low or entry_high
        
        # Calculate R-multiples if not already set
        if entry_avg and stop_loss:
            risk = abs(entry_avg - stop_loss)
            
            if target_conservative and not signal.get("r_multiple_conservative"):
                reward_conservative = abs(target_conservative - entry_avg)
                signal["r_multiple_conservative"] = reward_conservative / risk if risk > 0 else 0
            
            if target_aggressive and not signal.get("r_multiple_aggressive"):
                reward_aggressive = abs(target_aggressive - entry_avg)
                signal["r_multiple_aggressive"] = reward_aggressive / risk if risk > 0 else 0
        
        # Calculate position size if not set
        if not signal.get("position_size_percent"):
            # Default to risk-based sizing (1% risk per trade)
            signal["position_size_percent"] = self._calculate_position_size(
                signal.get("confidence", 0.5)
            )
        
        return signal
    
    def _calculate_position_size(self, confidence: float) -> float:
        """Calculate recommended position size based on confidence."""
        # Base position size: 1-5% based on confidence
        # Higher confidence = larger position (up to max)
        base_size = settings.RISK_PER_TRADE * 100  # Convert to percentage
        confidence_multiplier = 1 + (confidence * 4)  # 1x to 5x
        
        position_size = min(
            base_size * confidence_multiplier,
            settings.MAX_POSITION_SIZE * 100
        )
        
        return round(position_size, 1)
    
    async def batch_generate(
        self,
        symbols: list[str],
        timeframes: list[str] = None,
        max_concurrent: int = 5
    ) -> Dict[str, Any]:
        """
        Generate signals for multiple symbols in batch.
        
        Args:
            symbols: List of symbols to analyze
            timeframes: Timeframes for each (default: ["1d", "1w"])
            max_concurrent: Maximum concurrent generations
            
        Returns:
            Dict with results and errors
        """
        import asyncio
        
        logger.info(f"Batch generating signals for {len(symbols)} symbols")
        
        results = []
        errors = []
        
        # Process in batches to avoid overwhelming APIs
        for i in range(0, len(symbols), max_concurrent):
            batch = symbols[i:i + max_concurrent]
            tasks = [
                self.generate_signal(symbol, timeframes)
                for symbol in batch
            ]
            
            # Run batch concurrently
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Separate successful results from errors
            for symbol, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    errors.append({
                        "symbol": symbol,
                        "error": str(result)
                    })
                    logger.error(f"Failed to generate signal for {symbol}: {result}")
                else:
                    results.append(result)
                    logger.info(f"Signal generated for {symbol}")
        
        return {
            "total": len(symbols),
            "successful": len(results),
            "failed": len(errors),
            "signals": results,
            "errors": errors
        }

