"""TradeMaster adapter helpers for Airflow DAGs.

This module provides a small wrapper around the vendored TradeMaster project so we can:
- Convert this project's `MarketData` model into TradeMaster-compatible CSVs.
- Train/backtest a lightweight TradeMaster algorithm (DQN / algorithmic_trading) on CPU.
- Produce a compact inference summary suitable for AutoGen review + MLflow logging.

The wrapper is defensive:
- If TradeMaster (or its heavy deps like torch/gym) is unavailable, it falls back to a simple,
  deterministic SMA-crossover backtest so the DAG remains operational.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from models.market_data import MarketData
from utils.finagent_autogen_backtest import grid_search_sma_crossover

logger = logging.getLogger(__name__)


def _vendored_trademaster_root() -> str:
    """Return absolute path to vendored TradeMaster root (contains `trademaster/` and `mmcv/`)."""

    dags_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # In Docker, `./shared` is mounted into `/opt/airflow/dags/shared`, so the vendored
    # TradeMaster root is reachable as `<dags_root>/shared/vendor/trademaster`.
    candidate = os.path.join(dags_root, "shared", "vendor", "trademaster")
    if os.path.isdir(candidate):
        return candidate

    # In local repo layout, `shared/` lives at the repository root.
    repo_root = os.path.abspath(os.path.join(dags_root, ".."))
    return os.path.join(repo_root, "shared", "vendor", "trademaster")


def ensure_trademaster_importable() -> None:
    """Ensure vendored TradeMaster is importable as `import trademaster`."""

    vendor_root = _vendored_trademaster_root()
    if vendor_root not in sys.path:
        sys.path.insert(0, vendor_root)


def market_data_to_dataframe(market_data: MarketData) -> pd.DataFrame:
    rows = [
        {
            "date": bar.timestamp,
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": float(bar.volume),
        }
        for bar in market_data.bars
    ]
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df


def _default_indicator_list() -> List[str]:
    # Keep this minimal and deterministic for the TradeMaster AlgorithmicTradingEnvironment:
    # it uses these columns as the state feature window.
    return ["close"]


def _split_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df, df, df
    n = len(df)
    train_end = max(1, int(n * 0.7))
    valid_end = max(train_end + 1, int(n * 0.85))
    valid_end = min(valid_end, n - 1) if n > 2 else valid_end
    train_df = df.iloc[:train_end].copy()
    valid_df = df.iloc[train_end:valid_end].copy()
    test_df = df.iloc[valid_end:].copy()
    return train_df, valid_df, test_df


@dataclass(frozen=True)
class TradeMasterRunConfig:
    epochs: int = 3
    backward_num_day: int = 30
    forward_num_day: int = 1
    max_volume: int = 1
    initial_amount: int = 100_000
    transaction_cost_pct: float = 0.001
    future_weights: float = 0.2
    explore_rate: float = 0.25
    learning_rate: float = 1e-3
    hidden_dims: Tuple[int, ...] = (64, 64)
    device: str = "cpu"

    @staticmethod
    def from_dict(value: Optional[Dict[str, Any]]) -> "TradeMasterRunConfig":
        if not value:
            return TradeMasterRunConfig()
        return TradeMasterRunConfig(
            epochs=int(value.get("epochs", 3)),
            backward_num_day=int(value.get("backward_num_day", 30)),
            forward_num_day=int(value.get("forward_num_day", 1)),
            max_volume=int(value.get("max_volume", 1)),
            initial_amount=int(value.get("initial_amount", 100_000)),
            transaction_cost_pct=float(value.get("transaction_cost_pct", 0.001)),
            future_weights=float(value.get("future_weights", 0.2)),
            explore_rate=float(value.get("explore_rate", 0.25)),
            learning_rate=float(value.get("learning_rate", 1e-3)),
            hidden_dims=tuple(value.get("hidden_dims", (64, 64))),
            device=str(value.get("device", "cpu")),
        )


@dataclass
class TradeMasterTrainResult:
    metrics: Dict[str, float]
    best_model_path: Optional[str]
    work_dir: str
    indicator_list: List[str]
    state_dim: Optional[int] = None
    action_dim: Optional[int] = None
    suggested_action: Optional[str] = None
    suggested_raw_action: Optional[int] = None


@dataclass
class TradeMasterInferenceResult:
    action: str
    raw_action: Optional[int]
    details: Dict[str, Any]


def _action_from_raw(raw_action: Optional[int], *, max_volume: int) -> str:
    if raw_action is None:
        return "HOLD"
    buy_volume = int(raw_action) - int(max_volume)
    if buy_volume > 0:
        return "BUY"
    if buy_volume < 0:
        return "SELL"
    return "HOLD"


def _fallback_train_backtest(market_data: MarketData, *, work_dir: str) -> TradeMasterTrainResult:
    best, all_results = grid_search_sma_crossover(market_data)
    metrics = dict(best.metrics)
    metrics["strategy"] = "sma_grid_search_fallback"
    try:
        os.makedirs(work_dir, exist_ok=True)
        with open(os.path.join(work_dir, "fallback_grid_results.json"), "w", encoding="utf-8") as handle:
            json.dump(all_results, handle, indent=2, default=str)
        with open(os.path.join(work_dir, "fallback_best_params.json"), "w", encoding="utf-8") as handle:
            json.dump(best.params, handle, indent=2, default=str)
        with open(os.path.join(work_dir, "fallback_equity_curve.json"), "w", encoding="utf-8") as handle:
            json.dump(best.equity_curve, handle, indent=2, default=str)
    except Exception as exc:
        logger.warning("Fallback artifact write failed: %s", exc)

    return TradeMasterTrainResult(
        metrics=metrics,
        best_model_path=None,
        work_dir=work_dir,
        indicator_list=["close"],
        suggested_action="HOLD",
        suggested_raw_action=None,
    )


def train_backtest_trademaster(
    market_data: MarketData,
    *,
    symbol: str,
    run_config: TradeMasterRunConfig,
    work_dir: Optional[str] = None,
) -> TradeMasterTrainResult:
    """Train/backtest a lightweight TradeMaster algorithmic trading agent.

    Returns metrics + best checkpoint path. Uses a safe SMA fallback if dependencies are missing.
    """

    ensure_trademaster_importable()

    resolved_work_dir = work_dir or tempfile.mkdtemp(prefix=f"trademaster_{symbol}_")
    df = market_data_to_dataframe(market_data)
    if df.empty or len(df) < (run_config.backward_num_day + run_config.forward_num_day + 10):
        logger.warning("Insufficient data for TradeMaster run (%s); using fallback.", symbol)
        return _fallback_train_backtest(market_data, work_dir=resolved_work_dir)

    indicator_list = _default_indicator_list()
    for indicator in indicator_list:
        if indicator not in df.columns:
            raise ValueError(f"Required indicator column missing: {indicator}")

    train_df, valid_df, test_df = _split_dataframe(df)

    try:
        import torch
        import torch.nn as nn

        from trademaster.agents.algorithmic_trading.dqn import AlgorithmicTradingDQN
        from trademaster.environments.algorithmic_trading.environment import AlgorithmicTradingEnvironment
        from trademaster.nets.dqn import QNet
        from trademaster.trainers.algorithmic_trading.trainer import AlgorithmicTradingTrainer
    except Exception as exc:
        logger.warning("TradeMaster dependencies unavailable (%s); using fallback.", exc)
        return _fallback_train_backtest(market_data, work_dir=resolved_work_dir)

    os.makedirs(resolved_work_dir, exist_ok=True)
    data_dir = os.path.join(resolved_work_dir, "data")
    os.makedirs(data_dir, exist_ok=True)

    train_path = os.path.join(data_dir, "train.csv")
    valid_path = os.path.join(data_dir, "valid.csv")
    test_path = os.path.join(data_dir, "test.csv")
    train_df.to_csv(train_path)
    valid_df.to_csv(valid_path)
    test_df.to_csv(test_path)

    class _DatasetConfig:
        def __init__(self):
            self.train_path = train_path
            self.valid_path = valid_path
            self.test_path = test_path
            self.initial_amount = run_config.initial_amount
            self.transaction_cost_pct = run_config.transaction_cost_pct
            self.tech_indicator_list = indicator_list
            self.forward_num_day = run_config.forward_num_day
            self.backward_num_day = run_config.backward_num_day
            self.max_volume = run_config.max_volume
            self.future_weights = run_config.future_weights

    dataset = _DatasetConfig()

    train_env = AlgorithmicTradingEnvironment(dataset=dataset, task="train", work_dir=resolved_work_dir)
    valid_env = AlgorithmicTradingEnvironment(dataset=dataset, task="valid", work_dir=resolved_work_dir)
    test_env = AlgorithmicTradingEnvironment(dataset=dataset, task="test", work_dir=resolved_work_dir)

    device = torch.device(run_config.device)
    act = QNet(
        dims=list(run_config.hidden_dims),
        state_dim=train_env.state_dim,
        action_dim=train_env.action_dim,
        explore_rate=run_config.explore_rate,
    ).to(device)

    optimizer = torch.optim.Adam(act.parameters(), lr=run_config.learning_rate)
    criterion = nn.MSELoss()

    agent = AlgorithmicTradingDQN(
        num_envs=1,
        device=device,
        state_dim=train_env.state_dim,
        action_dim=train_env.action_dim,
        act=act,
        act_optimizer=optimizer,
        criterion=criterion,
    )

    trainer = AlgorithmicTradingTrainer(
        num_envs=1,
        device=device,
        train_environment=train_env,
        valid_environment=valid_env,
        test_environment=test_env,
        agent=agent,
        work_dir=os.path.join(resolved_work_dir, "run"),
        if_remove=True,
        if_discrete=False,
        if_off_policy=True,
        epochs=run_config.epochs,
        horizon_len=256,
        batch_size=64,
        buffer_size=50_000,
        repeat_times=1.0,
        verbose=False,
    )

    trainer.train_and_valid()
    trainer.test()

    # Metrics come from TradeMaster environment analysis.
    tr, sharpe, vol, mdd, cr, sor = test_env.analysis_result()
    metrics = {
        "strategy": "trademaster_algorithmic_trading_dqn",
        "tr": float(tr),
        "sharpe_ratio": float(sharpe),
        "vol": float(vol),
        "mdd": float(mdd),
        "cr": float(cr),
        "sor": float(sor),
    }

    checkpoints_dir = os.path.join(resolved_work_dir, "run", "checkpoints")
    best_model_path = os.path.join(checkpoints_dir, "best.pth")
    if not os.path.exists(best_model_path):
        best_model_path = None

    # Infer a suggested action from the trained network using the most recent window.
    suggested_raw_action: Optional[int] = None
    suggested_action: Optional[str] = None
    try:
        recent = df.tail(run_config.backward_num_day)
        features: List[float] = []
        for tech in indicator_list:
            features.extend([float(v) for v in recent[tech].tolist()])
        features.extend([float(run_config.initial_amount), 0.0])
        state = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)
        q_values = act(state)
        suggested_raw_action = int(q_values.argmax(dim=1).item())
        suggested_action = _action_from_raw(suggested_raw_action, max_volume=run_config.max_volume)
    except Exception as exc:
        logger.debug("Failed to infer suggested action for %s: %s", symbol, exc)

    return TradeMasterTrainResult(
        metrics=metrics,
        best_model_path=best_model_path,
        work_dir=resolved_work_dir,
        indicator_list=indicator_list,
        state_dim=train_env.state_dim,
        action_dim=train_env.action_dim,
        suggested_action=suggested_action,
        suggested_raw_action=suggested_raw_action,
    )


def infer_trademaster(
    market_data: MarketData,
    *,
    symbol: str,
    run_config: TradeMasterRunConfig,
    best_model_path: Optional[str] = None,
    work_dir: Optional[str] = None,
) -> TradeMasterInferenceResult:
    """Run a lightweight TradeMaster inference.

    If a checkpoint is not provided (or deps are missing), falls back to a simple heuristic.
    """

    ensure_trademaster_importable()

    df = market_data_to_dataframe(market_data)
    if df.empty or len(df) < max(5, run_config.backward_num_day):
        return TradeMasterInferenceResult(action="HOLD", raw_action=None, details={"reason": "no_data"})

    resolved_work_dir = work_dir or tempfile.mkdtemp(prefix=f"trademaster_infer_{symbol}_")
    indicator_list = _default_indicator_list()

    try:
        import torch
        import torch.nn as nn  # noqa: F401

        from trademaster.agents.algorithmic_trading.dqn import AlgorithmicTradingDQN
        from trademaster.nets.dqn import QNet
        from trademaster.utils.misc import load_best_model
    except Exception as exc:
        logger.warning("TradeMaster inference deps unavailable (%s); using heuristic.", exc)
        last_close = float(df["close"].iloc[-1])
        prev_close = float(df["close"].iloc[-2])
        action = "BUY" if last_close > prev_close else "SELL" if last_close < prev_close else "HOLD"
        return TradeMasterInferenceResult(
            action=action,
            raw_action=None,
            details={"reason": "heuristic_close_vs_prev", "last_close": last_close, "prev_close": prev_close},
        )

    device = torch.device(run_config.device)
    # Construct a minimal state vector based on recent data.
    recent = df.tail(run_config.backward_num_day)
    features: List[float] = []
    for tech in indicator_list:
        features.extend([float(v) for v in recent[tech].tolist()])
    features.extend([float(run_config.initial_amount), 0.0])
    state = torch.tensor(features, dtype=torch.float32, device=device).unsqueeze(0)

    # Build a network matching training defaults.
    action_dim = 2 * run_config.max_volume + 1
    state_dim = len(indicator_list) * run_config.backward_num_day + 2
    act = QNet(
        dims=list(run_config.hidden_dims),
        state_dim=state_dim,
        action_dim=action_dim,
        explore_rate=0.0,
    ).to(device)
    optimizer = torch.optim.Adam(act.parameters(), lr=run_config.learning_rate)
    criterion = torch.nn.MSELoss()

    agent = AlgorithmicTradingDQN(
        num_envs=1,
        device=device,
        state_dim=state_dim,
        action_dim=action_dim,
        act=act,
        act_optimizer=optimizer,
        criterion=criterion,
    )

    if best_model_path:
        try:
            load_best_model(output_dir=os.path.dirname(best_model_path), resume=best_model_path, save=agent.get_save(), is_train=False)
        except Exception as exc:
            logger.warning("Failed to load TradeMaster checkpoint (%s); continuing with untrained policy.", exc)

    q_values = act(state).detach().cpu().numpy().tolist()
    raw_action = int(max(range(len(q_values[0])), key=lambda idx: q_values[0][idx]))
    action = _action_from_raw(raw_action, max_volume=run_config.max_volume)
    return TradeMasterInferenceResult(
        action=action,
        raw_action=raw_action,
        details={
            "q_values": q_values[0],
            "indicator_list": indicator_list,
            "state_dim": state_dim,
            "action_dim": action_dim,
            "work_dir": resolved_work_dir,
        },
    )
