"""Tests for StrategyService."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import Column, Integer, String, Table, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.database import Base
from backend.models.strategy import Code, Strategy, StrategyCode, StrategySchedule
from backend.services.strategy_service import StrategyService

if "workflows" not in Base.metadata.tables:
    Table(
        "workflows",
        Base.metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String(255)),
        extend_existing=True,
    )


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Provide SQLite session with required tables."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(
        bind=engine,
        tables=[
            Base.metadata.tables["workflows"],
            Code.__table__,
            StrategyCode,
            Strategy.__table__,
            StrategySchedule.__table__,
        ],
    )
    with engine.begin() as conn:
        conn.execute(Base.metadata.tables["workflows"].insert().values(name="Test Workflow"))
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def strategy_service(db_session: Session) -> StrategyService:
    return StrategyService(db_session)


@pytest.fixture
def sample_strategy(db_session: Session) -> Strategy:
    strategy = Strategy(
        name="Test Strategy",
        description="Test",
        workflow_id=1,
        param={},
        risk_params={},
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


def test_create_strategy(strategy_service: StrategyService):
    strategy = strategy_service.create_strategy(
        name="Cron Strategy",
        workflow_id=1,
        schedule="0 9 * * *",
    )
    assert strategy.id is not None
    assert strategy.schedule == "0 9 * * *"
    assert strategy.next_execution_at is not None


def test_create_strategy_with_invalid_cron(strategy_service: StrategyService):
    with pytest.raises(ValueError):
        strategy_service.create_strategy(
            name="Bad Cron",
            workflow_id=1,
            schedule="invalid",
        )


def test_get_and_list_strategies(strategy_service: StrategyService, sample_strategy: Strategy):
    result = strategy_service.get_strategy(sample_strategy.id)
    assert result is not None

    strategies = strategy_service.list_strategies(active_only=True)
    assert any(s.id == sample_strategy.id for s in strategies)


def test_activate_deactivate_strategy(strategy_service: StrategyService, sample_strategy: Strategy):
    sample_strategy.schedule = "0 9 * * *"
    strategy_service.deactivate_strategy(sample_strategy.id)
    refreshed = strategy_service.get_strategy(sample_strategy.id)
    assert refreshed.is_active is False
    assert refreshed.next_execution_at is None

    strategy_service.activate_strategy(sample_strategy.id)
    refreshed = strategy_service.get_strategy(sample_strategy.id)
    assert refreshed.is_active is True
    assert refreshed.next_execution_at is not None


def test_get_strategies_due_for_execution(strategy_service: StrategyService, sample_strategy: Strategy):
    sample_strategy.schedule = "*/5 * * * *"
    sample_strategy.next_execution_at = datetime.now(timezone.utc)
    strategy_service.db.commit()

    due = strategy_service.get_strategies_due_for_execution(tolerance_minutes=1)
    assert any(s.id == sample_strategy.id for s in due)


def test_schedule_crud(strategy_service: StrategyService, sample_strategy: Strategy):
    schedule = strategy_service.create_schedule(
        strategy_id=sample_strategy.id,
        cron_expression="0 10 * * 1-5",
        timezone_name="America/New_York",
        description="Weekday open",
    )
    assert schedule.id is not None
    assert schedule.enabled is True
    assert schedule.next_run_time is not None

    preview = strategy_service.preview_next_runs(schedule.cron_expression, timezone_name="America/New_York", count=3)
    assert len(preview) == 3

    updated = strategy_service.update_schedule(
        schedule.id,
        cron_expression="0 11 * * 1-5",
        enabled=False,
        description="Late open",
    )
    assert updated.cron_expression == "0 11 * * 1-5"
    assert updated.enabled is False
    assert updated.next_run_time is None

    strategy_service.delete_schedule(schedule.id)
    assert strategy_service.list_schedules(strategy_id=sample_strategy.id) == []


def test_mark_strategy_executed(strategy_service: StrategyService, sample_strategy: Strategy):
    sample_strategy.schedule = "0 9 * * *"
    schedule = StrategySchedule(
        strategy_id=sample_strategy.id,
        cron_expression="0 9 * * *",
        timezone="UTC",
        enabled=True,
    )
    strategy_service.db.add(schedule)
    strategy_service.db.commit()

    result = strategy_service.mark_strategy_executed(sample_strategy.id)
    assert result.last_executed_at is not None
    assert result.next_execution_at is not None


def test_validate_strategy_config(strategy_service: StrategyService, sample_strategy: Strategy):
    sample_strategy.codes = []
    sample_strategy.schedule = "bad cron"
    result = strategy_service.validate_strategy_config(sample_strategy)
    assert result["valid"] is False
    assert "Invalid cron expression" in result["issues"]
