"""
Strategy Executor Engine - Core workflow orchestrator.

This is the main execution engine that orchestrates the complete trading workflow:
1. Fetch market data
2. Calculate indicators
3. Generate charts
4. Run LLM analysis
5. Generate trading signals
6. Record lineage for transparency

Each step is tracked with input/output in the lineage system.
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from backend.models.strategy import Strategy
from backend.models.trading_signal import TradingSignal
from backend.services.lineage_tracker import LineageTracker
from backend.services.symbol_service import SymbolService
from backend.services.ibkr_service import IBKRService
from backend.services.chart_service import ChartService
from backend.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class StrategyExecutor:
    """
    Orchestrates the complete trading strategy execution workflow.
    
    Features:
    - Step-by-step execution with lineage tracking
    - Error handling and recovery
    - Performance monitoring
    - Modular design for easy testing
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.lineage = LineageTracker(db)
        self.symbol_service = SymbolService(db)
        self.ibkr = IBKRService()
        self.chart_service = ChartService(db)
        self.llm_service = LLMService()
    
    async def execute_strategy(
        self,
        strategy: Strategy,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Execute a complete trading strategy workflow.
        
        Args:
            strategy: Strategy object to execute
            execution_id: Unique execution ID for lineage tracking
            
        Returns:
            Dictionary with execution results
        """
        start_time = time.time()
        logger.info(f"Starting strategy execution: {strategy.name} (execution_id: {execution_id})")
        
        try:
            # Step 1: Validate and fetch symbol
            symbol_data = await self._fetch_symbol(strategy, execution_id)
            if not symbol_data:
                return {"error": "Symbol fetch failed", "execution_id": execution_id}
            
            # Step 2: Fetch market data
            market_data = await self._fetch_market_data(strategy, symbol_data, execution_id)
            if not market_data:
                return {"error": "Market data fetch failed", "execution_id": execution_id}
            
            # Step 3: Calculate indicators
            indicator_data = await self._calculate_indicators(strategy, market_data, execution_id)
            if not indicator_data:
                return {"error": "Indicator calculation failed", "execution_id": execution_id}
            
            # Step 4: Generate charts (if LLM enabled)
            chart_data = None
            if strategy.llm_enabled:
                chart_data = await self._generate_charts(strategy, market_data, indicator_data, execution_id)
                if not chart_data:
                    logger.warning("Chart generation failed, continuing without charts")
            
            # Step 5: Run LLM analysis (if enabled and charts available)
            llm_analysis = None
            if strategy.llm_enabled and chart_data:
                llm_analysis = await self._run_llm_analysis(strategy, chart_data, execution_id)
                if not llm_analysis:
                    logger.warning("LLM analysis failed, will use indicator-only signals")
            
            # Step 6: Generate trading signal
            signal = await self._generate_signal(
                strategy,
                market_data,
                indicator_data,
                llm_analysis,
                execution_id
            )
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"Strategy execution complete: {strategy.name} in {duration_ms}ms. "
                f"Signal: {signal.get('action') if signal else 'NONE'}"
            )
            
            return {
                "execution_id": execution_id,
                "strategy_id": strategy.id,
                "strategy_name": strategy.name,
                "status": "success",
                "duration_ms": duration_ms,
                "symbol": symbol_data,
                "signal": signal,
                "llm_enabled": strategy.llm_enabled,
                "executed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"Strategy execution failed: {strategy.name} after {duration_ms}ms. "
                f"Error: {str(e)}",
                exc_info=True
            )
            
            # Record error in lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name="execution_error",
                step_number=99,
                input_data={"strategy_id": strategy.id},
                output_data={},
                error=str(e),
                duration_ms=duration_ms,
                db=self.db
            )
            
            return {
                "execution_id": execution_id,
                "strategy_id": strategy.id,
                "status": "error",
                "error": str(e),
                "duration_ms": duration_ms
            }
    
    async def _fetch_symbol(
        self,
        strategy: Strategy,
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 1: Fetch and validate symbol data.
        """
        step_start = time.time()
        step_name = "fetch_symbol"
        
        try:
            input_data = {
                "strategy_id": strategy.id,
                "symbol_conid": strategy.symbol_conid
            }
            
            if not strategy.symbol_conid:
                raise ValueError("No symbol conid configured for strategy")
            
            # Fetch symbol from cache or IBKR
            symbol = await self.symbol_service.get_by_conid(strategy.symbol_conid)
            if not symbol:
                raise ValueError(f"Symbol {strategy.symbol_conid} not found")
            
            output_data = symbol.to_dict()
            
            # Record lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=1,
                input_data=input_data,
                output_data=output_data,
                metadata={"strategy_name": strategy.name},
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            
            logger.debug(f"Symbol fetched: {symbol.symbol} ({symbol.conid})")
            return output_data
            
        except Exception as e:
            logger.error(f"Symbol fetch failed: {str(e)}")
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=1,
                input_data={"strategy_id": strategy.id, "symbol_conid": strategy.symbol_conid},
                output_data={},
                error=str(e),
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            return None
    
    async def _fetch_market_data(
        self,
        strategy: Strategy,
        symbol_data: Dict[str, Any],
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 2: Fetch market data from IBKR.
        """
        step_start = time.time()
        step_name = "fetch_market_data"
        
        try:
            input_data = {
                "conid": symbol_data['conid'],
                "symbol": symbol_data['symbol'],
                "timeframes": strategy.llm_timeframes or ['1d']
            }
            
            # Fetch market data for each timeframe
            market_data = {}
            for timeframe in input_data['timeframes']:
                data = await self.ibkr.get_historical_data(
                    conid=symbol_data['conid'],
                    period=timeframe,
                    bar="1d" if timeframe == "1d" else "1w"
                )
                market_data[timeframe] = data
            
            output_data = {
                "conid": symbol_data['conid'],
                "timeframes": list(market_data.keys()),
                "data_points": {tf: len(data) for tf, data in market_data.items() if data},
                "latest_price": market_data.get('1d', [{}])[-1].get('close') if market_data.get('1d') else None
            }
            
            # Record lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=2,
                input_data=input_data,
                output_data=output_data,
                metadata={"strategy_id": strategy.id},
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            
            logger.debug(f"Market data fetched: {len(market_data)} timeframes")
            return market_data
            
        except Exception as e:
            logger.error(f"Market data fetch failed: {str(e)}")
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=2,
                input_data=input_data if 'input_data' in locals() else {},
                output_data={},
                error=str(e),
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            return None
    
    async def _calculate_indicators(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any],
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 3: Calculate technical indicators.
        """
        step_start = time.time()
        step_name = "calculate_indicators"
        
        try:
            input_data = {
                "strategy_id": strategy.id,
                "indicators": [ind.name for ind in strategy.indicators],
                "timeframes": list(market_data.keys())
            }
            
            # Calculate indicators for each timeframe
            # TODO: Implement actual indicator calculation
            # For now, return a placeholder
            indicator_results = {
                "timeframes": list(market_data.keys()),
                "indicators": [ind.name for ind in strategy.indicators],
                "calculated": True,
                "note": "Indicator calculation placeholder"
            }
            
            output_data = indicator_results
            
            # Record lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=3,
                input_data=input_data,
                output_data=output_data,
                metadata={"strategy_id": strategy.id},
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            
            logger.debug(f"Indicators calculated: {len(strategy.indicators)} indicators")
            return indicator_results
            
        except Exception as e:
            logger.error(f"Indicator calculation failed: {str(e)}")
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=3,
                input_data=input_data if 'input_data' in locals() else {},
                output_data={},
                error=str(e),
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            return None
    
    async def _generate_charts(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any],
        indicator_data: Dict[str, Any],
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 4: Generate chart images for LLM analysis.
        """
        step_start = time.time()
        step_name = "generate_charts"
        
        try:
            input_data = {
                "strategy_id": strategy.id,
                "timeframes": list(market_data.keys()),
                "indicators": indicator_data.get('indicators', [])
            }
            
            # Generate charts
            # TODO: Implement actual chart generation
            chart_urls = {
                "1d": f"https://charts.example.com/{execution_id}_1d.png",
                "1w": f"https://charts.example.com/{execution_id}_1w.png"
            }
            
            output_data = {
                "charts": chart_urls,
                "note": "Chart generation placeholder"
            }
            
            # Record lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=4,
                input_data=input_data,
                output_data=output_data,
                metadata={"strategy_id": strategy.id},
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            
            logger.debug(f"Charts generated: {len(chart_urls)} charts")
            return output_data
            
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=4,
                input_data=input_data if 'input_data' in locals() else {},
                output_data={},
                error=str(e),
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            return None
    
    async def _run_llm_analysis(
        self,
        strategy: Strategy,
        chart_data: Dict[str, Any],
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 5: Run LLM analysis on charts.
        """
        step_start = time.time()
        step_name = "llm_analysis"
        
        try:
            input_data = {
                "strategy_id": strategy.id,
                "model": strategy.llm_model,
                "language": strategy.llm_language,
                "prompt_template_id": strategy.prompt_template_id,
                "charts": list(chart_data.get('charts', {}).keys())
            }
            
            # Run LLM analysis
            # TODO: Implement actual LLM analysis with prompt rendering
            llm_result = {
                "recommendation": "HOLD",
                "confidence": 0.75,
                "reasoning": "Placeholder LLM analysis",
                "note": "LLM analysis placeholder"
            }
            
            output_data = llm_result
            
            # Record lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=5,
                input_data=input_data,
                output_data=output_data,
                metadata={
                    "strategy_id": strategy.id,
                    "model": strategy.llm_model
                },
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            
            logger.debug(f"LLM analysis complete: {llm_result['recommendation']}")
            return llm_result
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=5,
                input_data=input_data if 'input_data' in locals() else {},
                output_data={},
                error=str(e),
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            return None
    
    async def _generate_signal(
        self,
        strategy: Strategy,
        market_data: Dict[str, Any],
        indicator_data: Dict[str, Any],
        llm_analysis: Optional[Dict[str, Any]],
        execution_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Step 6: Generate final trading signal.
        """
        step_start = time.time()
        step_name = "generate_signal"
        
        try:
            input_data = {
                "strategy_id": strategy.id,
                "has_llm_analysis": llm_analysis is not None,
                "llm_recommendation": llm_analysis.get('recommendation') if llm_analysis else None
            }
            
            # Generate signal based on LLM analysis and indicators
            # TODO: Implement actual signal generation logic
            signal_action = llm_analysis.get('recommendation', 'HOLD') if llm_analysis else 'HOLD'
            
            signal_data = {
                "action": signal_action,
                "confidence": llm_analysis.get('confidence', 0.5) if llm_analysis else 0.5,
                "reasoning": llm_analysis.get('reasoning') if llm_analysis else "Indicator-based signal",
                "execution_id": execution_id,
                "generated_at": datetime.now().isoformat()
            }
            
            # Save signal to database
            signal = TradingSignal(
                strategy_id=strategy.id,
                signal_type=signal_action.lower(),
                confidence=signal_data['confidence'],
                reasoning=signal_data['reasoning'],
                metadata={"execution_id": execution_id},
                created_at=datetime.now()
            )
            self.db.add(signal)
            self.db.commit()
            self.db.refresh(signal)
            
            signal_data['signal_id'] = signal.id
            output_data = signal_data
            
            # Record lineage
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=6,
                input_data=input_data,
                output_data=output_data,
                metadata={"strategy_id": strategy.id, "signal_id": signal.id},
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            
            logger.info(f"Signal generated: {signal_action} (confidence: {signal_data['confidence']})")
            return signal_data
            
        except Exception as e:
            logger.error(f"Signal generation failed: {str(e)}")
            await self.lineage.record_step(
                execution_id=execution_id,
                step_name=step_name,
                step_number=6,
                input_data=input_data if 'input_data' in locals() else {},
                output_data={},
                error=str(e),
                duration_ms=int((time.time() - step_start) * 1000),
                db=self.db
            )
            return None

