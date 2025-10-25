"""
Signal Generator Service - Combines indicators and LLM analysis.

Generates trading signals by:
1. Analyzing technical indicators
2. Getting LLM vision analysis of charts
3. Calculating confidence scores
4. Determining entry/exit levels
5. Applying 3/4 confirmation rule
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.services.indicator_calculator import IndicatorCalculator
from backend.services.llm_service import LLMService
from backend.models.trading_signal import TradingSignal

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Generate trading signals from technical indicators and LLM analysis.
    """
    
    def __init__(self, db: Session):
        """Initialize the signal generator."""
        self.db = db
        self.indicator_calc = IndicatorCalculator()
        self.llm_service = LLMService(db=db)
    
    async def generate_signal(
        self,
        strategy_id: int,
        symbol: str,
        conid: int,
        market_data: Dict[str, Any],
        indicator_data: Dict[str, Any],
        chart_urls: Dict[str, str],
        llm_enabled: bool = True,
        llm_language: str = "en",
        prompt_template_id: Optional[int] = None
    ) -> TradingSignal:
        """
        Generate a complete trading signal.
        
        Args:
            strategy_id: Strategy ID
            symbol: Stock symbol
            conid: IBKR contract ID
            market_data: Market data by timeframe
            indicator_data: Pre-calculated indicators
            chart_urls: Chart URLs by timeframe
            llm_enabled: Whether to use LLM analysis
            llm_language: Language for LLM prompts
            prompt_template_id: Specific prompt template ID
            
        Returns:
            TradingSignal object
        """
        try:
            logger.info(f"Generating signal for {symbol} (strategy {strategy_id})")
            
            # Get current price
            current_price = self._get_current_price(market_data)
            if not current_price:
                raise ValueError("Cannot determine current price from market data")
            
            # 1. Analyze technical indicators
            technical_analysis = await self._analyze_indicators(
                indicator_data, current_price
            )
            
            # 2. Get LLM analysis if enabled
            llm_analysis = {}
            if llm_enabled and chart_urls:
                llm_analysis = await self._get_llm_analysis(
                    strategy_id=strategy_id,
                    symbol=symbol,
                    chart_urls=chart_urls,
                    language=llm_language,
                    current_price=current_price,
                    indicators=indicator_data
                )
            
            # 3. Combine analyses
            combined = await self._combine_analyses(
                technical_analysis, llm_analysis, current_price
            )
            
            # 4. Calculate confidence
            confidence = self._calculate_confidence(technical_analysis, llm_analysis)
            
            # 5. Determine entry/exit levels
            levels = self._calculate_trading_levels(
                signal_type=combined['signal_type'],
                current_price=current_price,
                indicator_data=indicator_data,
                llm_recommendation=llm_analysis.get('parsed_signal', {})
            )
            
            # 6. Check 3/4 confirmation rule
            confirmation = self.indicator_calc.calculate_signal_confirmation(
                indicator_data.get('1d', {}), current_price
            )
            
            # 7. Create signal object
            signal = TradingSignal(
                symbol=symbol,
                strategy_id=strategy_id,
                signal_type=combined['signal_type'],
                trend=combined['trend'],
                confidence=confidence,
                
                # Timeframes
                timeframe_primary="1d",
                timeframe_confirmation="1w",
                
                # Trading levels
                entry_price_low=levels['entry_low'],
                entry_price_high=levels['entry_high'],
                stop_loss=levels['stop_loss'],
                target_conservative=levels['target_conservative'],
                target_aggressive=levels['target_aggressive'],
                r_multiple_conservative=levels['r_conservative'],
                r_multiple_aggressive=levels['r_aggressive'],
                position_size_percent=levels['position_size'],
                
                # Confirmation
                confirmation_signals=confirmation,
                
                # Analysis text
                analysis_daily=llm_analysis.get('daily_analysis', technical_analysis.get('summary', '')),
                analysis_weekly=llm_analysis.get('weekly_analysis', ''),
                analysis_consolidated=combined.get('reasoning', ''),
                
                # Chart URLs
                chart_url_daily=chart_urls.get('1d'),
                chart_url_weekly=chart_urls.get('1w'),
                chart_html_daily=chart_urls.get('1d_html'),
                chart_html_weekly=chart_urls.get('1w_html'),
                
                # Metadata
                language=llm_language,
                model_used=llm_analysis.get('model_used'),
                provider=llm_analysis.get('provider'),
                
                # Prompt tracking
                prompt_template_id=llm_analysis.get('prompt_template_id', prompt_template_id),
                prompt_version=llm_analysis.get('prompt_version'),
                prompt_type='consolidated',
                
                # Timestamps
                generated_at=datetime.now(),
                expires_at=datetime.now() + timedelta(days=1),
                status='active'
            )
            
            logger.info(
                f"Signal generated: {signal.signal_type} with {confidence:.2f} confidence "
                f"(confirmation: {confirmation['confirmed_count']}/4)"
            )
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {str(e)}", exc_info=True)
            raise
    
    def _get_current_price(self, market_data: Dict[str, Any]) -> Optional[float]:
        """Extract current price from market data."""
        try:
            # Try daily data first
            if '1d' in market_data and market_data['1d']:
                daily = market_data['1d']
                if isinstance(daily, list) and len(daily) > 0:
                    return float(daily[-1].get('close', 0))
            
            # Try any available timeframe
            for timeframe, data in market_data.items():
                if data and isinstance(data, list) and len(data) > 0:
                    return float(data[-1].get('close', 0))
            
            return None
        except Exception as e:
            logger.error(f"Error getting current price: {e}")
            return None
    
    async def _analyze_indicators(
        self,
        indicator_data: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """
        Analyze technical indicators to determine signal.
        
        Returns:
            Dictionary with technical analysis results
        """
        try:
            # Focus on daily timeframe indicators
            daily_indicators = indicator_data.get('1d', {})
            
            analysis = {
                'signal_type': 'HOLD',
                'trend': 'neutral',
                'reasoning': [],
                'summary': ''
            }
            
            bullish_signals = 0
            bearish_signals = 0
            
            # Check each indicator
            for name, data in daily_indicators.items():
                if not data:
                    continue
                
                indicator_type = data.get('type', '')
                
                # SuperTrend
                if indicator_type == 'SUPERTREND':
                    if data.get('is_bullish'):
                        bullish_signals += 1
                        analysis['reasoning'].append(f"SuperTrend bullish")
                    else:
                        bearish_signals += 1
                        analysis['reasoning'].append(f"SuperTrend bearish")
                
                # MACD
                elif indicator_type == 'MACD':
                    if data.get('is_bullish'):
                        bullish_signals += 1
                        analysis['reasoning'].append(f"MACD bullish")
                    else:
                        bearish_signals += 1
                        analysis['reasoning'].append(f"MACD bearish")
                
                # RSI
                elif indicator_type == 'RSI':
                    rsi = data.get('current')
                    if rsi:
                        if rsi > 70:
                            bearish_signals += 1
                            analysis['reasoning'].append(f"RSI overbought ({rsi:.1f})")
                        elif rsi < 30:
                            bullish_signals += 1
                            analysis['reasoning'].append(f"RSI oversold ({rsi:.1f})")
                        elif rsi > 50:
                            bullish_signals += 0.5
                            analysis['reasoning'].append(f"RSI bullish ({rsi:.1f})")
                        else:
                            bearish_signals += 0.5
                            analysis['reasoning'].append(f"RSI bearish ({rsi:.1f})")
                
                # Moving Average
                elif indicator_type in ['SMA', 'EMA', 'MA']:
                    ma_value = data.get('current')
                    if ma_value:
                        if current_price > ma_value:
                            bullish_signals += 0.5
                            analysis['reasoning'].append(f"Price above {indicator_type}")
                        else:
                            bearish_signals += 0.5
                            analysis['reasoning'].append(f"Price below {indicator_type}")
            
            # Determine signal based on balance
            if bullish_signals >= 2.5 and bullish_signals > bearish_signals:
                analysis['signal_type'] = 'BUY'
                if bullish_signals >= 4:
                    analysis['trend'] = 'strong_bullish'
                else:
                    analysis['trend'] = 'bullish'
            elif bearish_signals >= 2.5 and bearish_signals > bullish_signals:
                analysis['signal_type'] = 'SELL'
                if bearish_signals >= 4:
                    analysis['trend'] = 'strong_bearish'
                else:
                    analysis['trend'] = 'bearish'
            else:
                analysis['signal_type'] = 'HOLD'
                analysis['trend'] = 'neutral'
            
            analysis['summary'] = f"Technical analysis: {analysis['signal_type']} ({bullish_signals:.1f} bullish, {bearish_signals:.1f} bearish)"
            
            logger.info(f"Technical analysis: {analysis['signal_type']} - {', '.join(analysis['reasoning'])}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing indicators: {e}")
            return {
                'signal_type': 'HOLD',
                'trend': 'neutral',
                'reasoning': ['Error in technical analysis'],
                'summary': 'Technical analysis failed'
            }
    
    async def _get_llm_analysis(
        self,
        strategy_id: int,
        symbol: str,
        chart_urls: Dict[str, str],
        language: str,
        current_price: float,
        indicators: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get LLM analysis of charts."""
        try:
            analyses = {}
            
            # Analyze daily chart
            if '1d' in chart_urls:
                daily = await self.llm_service.analyze_chart(
                    chart_url=chart_urls['1d'],
                    prompt_template="analysis",
                    symbol=symbol,
                    strategy_id=strategy_id,
                    language=language,
                    current_price=current_price,
                    indicators=indicators.get('1d', {}),
                    timeframe="daily"
                )
                analyses['daily_analysis'] = daily.get('raw_text', '')
                analyses['daily_parsed'] = daily.get('parsed_signal', {})
                analyses['model_used'] = daily.get('model_used')
                analyses['provider'] = daily.get('provider')
                analyses['prompt_template_id'] = daily.get('prompt_template_id')
                analyses['prompt_version'] = daily.get('prompt_version')
            
            # Analyze weekly chart
            if '1w' in chart_urls:
                weekly = await self.llm_service.analyze_chart(
                    chart_url=chart_urls['1w'],
                    prompt_template="analysis",
                    symbol=symbol,
                    strategy_id=strategy_id,
                    language=language,
                    current_price=current_price,
                    indicators=indicators.get('1w', {}),
                    timeframe="weekly"
                )
                analyses['weekly_analysis'] = weekly.get('raw_text', '')
                analyses['weekly_parsed'] = weekly.get('parsed_signal', {})
            
            # Consolidate if we have both
            if 'daily_analysis' in analyses and 'weekly_analysis' in analyses:
                consolidated = await self._consolidate_analyses(
                    daily=analyses['daily_analysis'],
                    weekly=analyses['weekly_analysis'],
                    strategy_id=strategy_id,
                    language=language
                )
                analyses['consolidated'] = consolidated
            
            # Extract parsed signal
            if 'daily_parsed' in analyses:
                analyses['parsed_signal'] = analyses['daily_parsed']
            
            return analyses
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            return {}
    
    async def _consolidate_analyses(
        self,
        daily: str,
        weekly: str,
        strategy_id: int,
        language: str
    ) -> str:
        """Consolidate daily and weekly analyses."""
        # This would normally call LLM with a consolidation prompt
        # For now, just combine them
        return f"Daily: {daily}\n\nWeekly: {weekly}"
    
    async def _combine_analyses(
        self,
        technical: Dict[str, Any],
        llm: Dict[str, Any],
        current_price: float
    ) -> Dict[str, Any]:
        """Combine technical and LLM analyses."""
        # If LLM is available, use it as primary
        if llm and 'parsed_signal' in llm:
            llm_signal = llm['parsed_signal'].get('signal', 'HOLD').upper()
            return {
                'signal_type': llm_signal,
                'trend': llm['parsed_signal'].get('trend', technical['trend']),
                'reasoning': f"LLM: {llm_signal}, Technical: {technical['signal_type']}"
            }
        
        # Otherwise use technical
        return {
            'signal_type': technical['signal_type'],
            'trend': technical['trend'],
            'reasoning': technical['summary']
        }
    
    def _calculate_confidence(
        self,
        technical: Dict[str, Any],
        llm: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence score (0-1)."""
        base_confidence = 0.5
        
        # Boost if LLM and technical agree
        if llm and 'parsed_signal' in llm:
            llm_signal = llm['parsed_signal'].get('signal', 'HOLD').upper()
            if llm_signal == technical['signal_type']:
                base_confidence += 0.3
            
            # Add LLM confidence if available
            llm_confidence = llm['parsed_signal'].get('confidence')
            if llm_confidence:
                base_confidence = (base_confidence + float(llm_confidence)) / 2
        
        return min(1.0, max(0.0, base_confidence))
    
    def _calculate_trading_levels(
        self,
        signal_type: str,
        current_price: float,
        indicator_data: Dict[str, Any],
        llm_recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate entry, stop loss, and target levels."""
        daily_indicators = indicator_data.get('1d', {})
        
        # Get ATR for stop loss calculation
        atr = None
        for name, data in daily_indicators.items():
            if data.get('type') == 'ATR':
                atr = data.get('current')
                break
        
        if not atr:
            atr = current_price * 0.02  # 2% default
        
        levels = {
            'entry_low': current_price * 0.98,
            'entry_high': current_price * 1.02,
            'stop_loss': None,
            'target_conservative': None,
            'target_aggressive': None,
            'r_conservative': None,
            'r_aggressive': None,
            'position_size': 2.0  # 2% default
        }
        
        if signal_type == 'BUY':
            # Stop loss below entry
            levels['stop_loss'] = current_price - (2 * atr)
            
            # Targets above entry
            levels['target_conservative'] = current_price + (2 * atr)
            levels['target_aggressive'] = current_price + (4 * atr)
            
            # Calculate R-multiples
            risk = current_price - levels['stop_loss']
            if risk > 0:
                levels['r_conservative'] = (levels['target_conservative'] - current_price) / risk
                levels['r_aggressive'] = (levels['target_aggressive'] - current_price) / risk
        
        elif signal_type == 'SELL':
            # Stop loss above entry
            levels['stop_loss'] = current_price + (2 * atr)
            
            # Targets below entry
            levels['target_conservative'] = current_price - (2 * atr)
            levels['target_aggressive'] = current_price - (4 * atr)
            
            # Calculate R-multiples
            risk = levels['stop_loss'] - current_price
            if risk > 0:
                levels['r_conservative'] = (current_price - levels['target_conservative']) / risk
                levels['r_aggressive'] = (current_price - levels['target_aggressive']) / risk
        
        # Use LLM recommendations if available
        if llm_recommendation:
            if 'entry_low' in llm_recommendation:
                levels['entry_low'] = llm_recommendation['entry_low']
            if 'entry_high' in llm_recommendation:
                levels['entry_high'] = llm_recommendation['entry_high']
            if 'stop_loss' in llm_recommendation:
                levels['stop_loss'] = llm_recommendation['stop_loss']
            if 'target_conservative' in llm_recommendation:
                levels['target_conservative'] = llm_recommendation['target_conservative']
            if 'target_aggressive' in llm_recommendation:
                levels['target_aggressive'] = llm_recommendation['target_aggressive']
        
        return levels


def get_signal_generator(db: Session) -> SignalGenerator:
    """Factory function for SignalGenerator."""
    return SignalGenerator(db)
