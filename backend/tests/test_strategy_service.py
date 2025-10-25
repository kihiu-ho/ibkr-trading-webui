"""Tests for StrategyService."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from backend.services.strategy_service import StrategyService
from backend.models.strategy import Strategy


class TestStrategyService:
    """Test suite for StrategyService."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        return db
    
    @pytest.fixture
    def strategy_service(self, mock_db):
        """Create a StrategyService instance with mock db."""
        return StrategyService(mock_db)
    
    @pytest.fixture
    def sample_strategy(self):
        """Create a sample Strategy object."""
        return Strategy(
            id=1,
            name="Test Strategy",
            description="A test strategy",
            symbol_conid=265598,
            schedule="0 9 * * *",  # Daily at 9 AM
            is_active=1,
            llm_enabled=1
        )
    
    @pytest.mark.asyncio
    async def test_create_strategy(self, strategy_service, mock_db):
        """Test creating a new strategy."""
        # Execute
        strategy = await strategy_service.create_strategy(
            name="Test Strategy",
            description="A test strategy",
            symbol_conid=265598,
            schedule="0 9 * * *"
        )
        
        # Assert
        assert strategy is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_strategy_with_invalid_cron(self, strategy_service, mock_db):
        """Test creating strategy with invalid cron expression."""
        # Execute & Assert
        with pytest.raises(ValueError, match="Invalid cron expression"):
            await strategy_service.create_strategy(
                name="Test Strategy",
                schedule="invalid cron"
            )
    
    @pytest.mark.asyncio
    async def test_get_strategy(self, strategy_service, mock_db, sample_strategy):
        """Test getting a strategy by ID."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = sample_strategy
        
        # Execute
        result = await strategy_service.get_strategy(1)
        
        # Assert
        assert result is not None
        assert result.id == 1
        assert result.name == "Test Strategy"
    
    @pytest.mark.asyncio
    async def test_list_strategies(self, strategy_service, mock_db, sample_strategy):
        """Test listing strategies with filters."""
        # Setup
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = [sample_strategy]
        
        # Execute
        results = await strategy_service.list_strategies(active_only=True)
        
        # Assert
        assert len(results) == 1
        assert results[0].name == "Test Strategy"
    
    @pytest.mark.asyncio
    async def test_activate_strategy(self, strategy_service, mock_db, sample_strategy):
        """Test activating a strategy."""
        # Setup
        sample_strategy.is_active = 0
        with patch.object(strategy_service, 'get_strategy', return_value=sample_strategy):
            # Execute
            result = await strategy_service.activate_strategy(1)
            
            # Assert
            assert result.is_active == 1
            assert result.next_execution_at is not None
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_deactivate_strategy(self, strategy_service, mock_db, sample_strategy):
        """Test deactivating a strategy."""
        # Setup
        with patch.object(strategy_service, 'get_strategy', return_value=sample_strategy):
            # Execute
            result = await strategy_service.deactivate_strategy(1)
            
            # Assert
            assert result.is_active == 0
            assert result.next_execution_at is None
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_strategies_due_for_execution(self, strategy_service, mock_db, sample_strategy):
        """Test getting strategies due for execution."""
        # Setup
        sample_strategy.next_execution_at = datetime.now() - timedelta(minutes=1)
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_strategy]
        
        # Execute
        results = await strategy_service.get_strategies_due_for_execution(tolerance_minutes=5)
        
        # Assert
        assert len(results) == 1
        assert results[0].id == 1
    
    @pytest.mark.asyncio
    async def test_mark_strategy_executed(self, strategy_service, mock_db, sample_strategy):
        """Test marking a strategy as executed."""
        # Setup
        with patch.object(strategy_service, 'get_strategy', return_value=sample_strategy):
            # Execute
            result = await strategy_service.mark_strategy_executed(1)
            
            # Assert
            assert result.last_executed_at is not None
            assert result.next_execution_at is not None
            mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_strategy_config(self, strategy_service, mock_db, sample_strategy):
        """Test validating strategy configuration."""
        # Setup
        sample_strategy.indicators = []
        
        # Execute
        result = await strategy_service.validate_strategy_config(sample_strategy)
        
        # Assert
        assert 'valid' in result
        assert 'issues' in result
        assert 'warnings' in result
    
    def test_validate_cron(self, strategy_service):
        """Test cron expression validation."""
        # Valid cron expressions
        assert strategy_service._validate_cron("0 9 * * *") is True
        assert strategy_service._validate_cron("*/5 * * * *") is True
        assert strategy_service._validate_cron("0 0 1 * *") is True
        
        # Invalid cron expressions
        assert strategy_service._validate_cron("invalid") is False
        assert strategy_service._validate_cron("60 9 * * *") is False
        assert strategy_service._validate_cron("") is False
    
    def test_calculate_next_execution(self, strategy_service):
        """Test next execution time calculation."""
        # Test daily at 9 AM
        cron_expr = "0 9 * * *"
        next_exec = strategy_service._calculate_next_execution(cron_expr)
        
        # Assert
        assert next_exec > datetime.now()
        assert next_exec.hour == 9
        assert next_exec.minute == 0

