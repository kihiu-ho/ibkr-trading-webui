"""Strategy management service with scheduling."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from croniter import croniter
from backend.models.strategy import Strategy
from backend.models.symbol import Symbol

logger = logging.getLogger(__name__)


class StrategyService:
    """
    Service for managing trading strategies with scheduling.
    
    Features:
    - Strategy CRUD operations
    - Cron schedule parsing and validation
    - Next execution time calculation
    - Active strategy queries
    - Celery Beat integration
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_strategy(
        self,
        name: str,
        description: Optional[str] = None,
        symbol_conid: Optional[int] = None,
        strategy_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        risk_params: Optional[Dict[str, Any]] = None,
        llm_config: Optional[Dict[str, Any]] = None,
        schedule: Optional[str] = None,
        prompt_template_id: Optional[int] = None
    ) -> Strategy:
        """
        Create a new trading strategy.
        
        Args:
            name: Strategy name (unique)
            description: Strategy description
            symbol_conid: IBKR contract ID
            strategy_type: Type of strategy (e.g., "trend_following")
            parameters: Strategy-specific parameters
            risk_params: Risk management params (position_size, stop_loss, etc.)
            llm_config: LLM configuration (model, language, timeframes)
            schedule: Cron expression for execution schedule
            prompt_template_id: ID of prompt template to use
            
        Returns:
            Created Strategy object
        """
        # Validate schedule if provided
        if schedule:
            if not self._validate_cron(schedule):
                raise ValueError(f"Invalid cron expression: {schedule}")
        
        # Create strategy
        strategy = Strategy(
            name=name,
            description=description,
            symbol_conid=symbol_conid,
            type=strategy_type,
            param=parameters or {},
            risk_params=risk_params or {},
            prompt_template_id=prompt_template_id,
            schedule=schedule,
            is_active=1
        )
        
        # Set LLM config
        if llm_config:
            strategy.llm_enabled = llm_config.get('enabled', 1)
            strategy.llm_model = llm_config.get('model', 'gpt-4-vision-preview')
            strategy.llm_language = llm_config.get('language', 'en')
            strategy.llm_timeframes = llm_config.get('timeframes', ['1d', '1w'])
        
        # Calculate next execution time
        if schedule:
            strategy.next_execution_at = self._calculate_next_execution(schedule)
        
        self.db.add(strategy)
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Created strategy: {name} (ID: {strategy.id})")
        return strategy
    
    async def update_strategy(
        self,
        strategy_id: int,
        **updates
    ) -> Strategy:
        """
        Update an existing strategy.
        
        Args:
            strategy_id: Strategy ID
            **updates: Fields to update
            
        Returns:
            Updated Strategy object
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        # Update fields
        for key, value in updates.items():
            if hasattr(strategy, key):
                setattr(strategy, key, value)
        
        # If schedule changed, recalculate next execution
        if 'schedule' in updates and updates['schedule']:
            if not self._validate_cron(updates['schedule']):
                raise ValueError(f"Invalid cron expression: {updates['schedule']}")
            strategy.next_execution_at = self._calculate_next_execution(updates['schedule'])
        
        strategy.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Updated strategy: {strategy.name} (ID: {strategy_id})")
        return strategy
    
    def get_strategy(self, strategy_id: int) -> Optional[Strategy]:
        """Get strategy by ID."""
        return self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
    
    def get_strategy_by_name(self, name: str) -> Optional[Strategy]:
        """Get strategy by name."""
        return self.db.query(Strategy).filter(Strategy.name == name).first()
    
    def list_strategies(
        self,
        active_only: bool = False,
        symbol_conid: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Strategy]:
        """
        List strategies with filters.
        
        Args:
            active_only: Only return active strategies
            symbol_conid: Filter by symbol
            skip: Pagination offset
            limit: Maximum results
            
        Returns:
            List of Strategy objects
        """
        query = self.db.query(Strategy)
        
        if active_only:
            query = query.filter(Strategy.is_active == 1)
        
        if symbol_conid:
            query = query.filter(Strategy.symbol_conid == symbol_conid)
        
        strategies = query.offset(skip).limit(limit).all()
        return strategies
    
    async def delete_strategy(self, strategy_id: int) -> bool:
        """
        Delete a strategy.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            True if deleted, False if not found
        """
        strategy = self.db.query(Strategy).filter(Strategy.id == strategy_id).first()
        if not strategy:
            return False
        
        self.db.delete(strategy)
        self.db.commit()
        
        logger.info(f"Deleted strategy: {strategy.name} (ID: {strategy_id})")
        return True
    
    async def activate_strategy(self, strategy_id: int) -> Strategy:
        """Activate a strategy."""
        strategy = await self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        strategy.is_active = 1
        
        # Recalculate next execution if schedule exists
        if strategy.schedule:
            strategy.next_execution_at = self._calculate_next_execution(strategy.schedule)
        
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Activated strategy: {strategy.name}")
        return strategy
    
    async def deactivate_strategy(self, strategy_id: int) -> Strategy:
        """Deactivate a strategy."""
        strategy = await self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        strategy.is_active = 0
        strategy.next_execution_at = None
        
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(f"Deactivated strategy: {strategy.name}")
        return strategy
    
    def get_strategies_due_for_execution(
        self,
        tolerance_minutes: int = 5
    ) -> List[Strategy]:
        """
        Get strategies that are due for execution.
        
        Args:
            tolerance_minutes: Minutes of tolerance for execution time
            
        Returns:
            List of strategies due for execution
        """
        now = datetime.now()
        cutoff = now + timedelta(minutes=tolerance_minutes)
        
        strategies = self.db.query(Strategy).filter(
            and_(
                Strategy.is_active == 1,
                Strategy.schedule.isnot(None),
                Strategy.next_execution_at <= cutoff
            )
        ).all()
        
        logger.debug(f"Found {len(strategies)} strategies due for execution")
        return strategies
    
    def mark_strategy_executed(
        self,
        strategy_id: int,
        execution_time: Optional[datetime] = None
    ) -> Strategy:
        """
        Mark strategy as executed and calculate next execution time.
        
        Args:
            strategy_id: Strategy ID
            execution_time: Execution timestamp (defaults to now)
            
        Returns:
            Updated Strategy object
        """
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            raise ValueError(f"Strategy {strategy_id} not found")
        
        execution_time = execution_time or datetime.now()
        strategy.last_executed_at = execution_time
        
        # Calculate next execution
        if strategy.schedule:
            strategy.next_execution_at = self._calculate_next_execution(
                strategy.schedule,
                from_time=execution_time
            )
        
        self.db.commit()
        self.db.refresh(strategy)
        
        logger.info(
            f"Marked strategy {strategy.name} as executed. "
            f"Next execution: {strategy.next_execution_at}"
        )
        return strategy
    
    def validate_strategy_config(
        self,
        strategy: Strategy
    ) -> Dict[str, Any]:
        """
        Validate strategy configuration.
        
        Returns:
            Dictionary with validation results
        """
        issues = []
        warnings = []
        
        # Check symbol
        if not strategy.symbol_conid:
            issues.append("No symbol (conid) configured")
        else:
            symbol = self.db.query(Symbol).filter(Symbol.conid == strategy.symbol_conid).first()
            if not symbol:
                warnings.append(f"Symbol conid {strategy.symbol_conid} not found in cache")
        
        # Check schedule
        if strategy.schedule:
            if not self._validate_cron(strategy.schedule):
                issues.append(f"Invalid cron expression: {strategy.schedule}")
        else:
            warnings.append("No schedule configured - strategy will not auto-execute")
        
        # Check prompt template
        if strategy.llm_enabled and not strategy.prompt_template_id:
            warnings.append("LLM enabled but no prompt template configured")
        
        # Check indicators
        if len(strategy.indicators) == 0:
            warnings.append("No indicators configured for this strategy")
        
        # Check risk params
        if not strategy.risk_params:
            warnings.append("No risk parameters configured")
        else:
            if 'position_size' not in strategy.risk_params:
                warnings.append("No position_size in risk_params")
            if 'stop_loss_pct' not in strategy.risk_params:
                warnings.append("No stop_loss_pct in risk_params")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings
        }
    
    def _validate_cron(self, cron_expr: str) -> bool:
        """
        Validate a cron expression.
        
        Args:
            cron_expr: Cron expression string
            
        Returns:
            True if valid
        """
        try:
            croniter(cron_expr)
            return True
        except Exception as e:
            logger.warning(f"Invalid cron expression '{cron_expr}': {str(e)}")
            return False
    
    def _calculate_next_execution(
        self,
        cron_expr: str,
        from_time: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate next execution time from cron expression.
        
        Args:
            cron_expr: Cron expression
            from_time: Starting time (defaults to now)
            
        Returns:
            Next execution datetime
        """
        from_time = from_time or datetime.now()
        cron = croniter(cron_expr, from_time)
        next_time = cron.get_next(datetime)
        return next_time


def get_strategy_service(db: Session) -> StrategyService:
    """Factory function for StrategyService."""
    return StrategyService(db)

