"""FinAgent AutoGen Pipeline Workflow DAG.

New DAG that orchestrates a FinAgent-style multi-agent decision using Microsoft AutoGen and logs
an auditable trail to MLflow. It also supports an offline "train/backtest" mode that evaluates a
simple strategy over historical data and records results to MLflow.

Run modes (via `dag_run.conf.mode`):
  - inference (default)
  - train_backtest
  - both
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from airflow import DAG

try:
    # Airflow 3+
    from airflow.providers.standard.operators.python import PythonOperator
except Exception:  # pragma: no cover - Airflow 2 fallback
    from airflow.operators.python import PythonOperator

# Ensure Airflow can import local `models/` and `utils/` packages regardless of how the DAG is executed.
sys.path.append(os.path.dirname(__file__))

from models.market_data import MarketData
from models.chart import ChartConfig, Timeframe
from utils.autogen_finagent_orchestrator import AutoGenFinAgentOrchestrator
from utils.artifact_storage import attach_artifact_lineage, store_artifact
from utils.chart_generator import ChartGenerator
from utils.config import config
from utils.finagent_autogen_backtest import grid_search_sma_crossover
from utils.ibkr_client import IBKRClient
from utils.minio_upload import upload_chart_to_minio
from utils.mlflow_tracking import mlflow_run_context
from utils.news_api_client import NewsAPIClient

logger = logging.getLogger(__name__)

DEFAULT_ARGS = {
    "owner": "ibkr-trading",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

DAG_ID = "finagent_autogen_pipeline_workflow"
SYMBOL = config.stock_symbols[0] if config.stock_symbols else "TSLA"
IBKR_HOST = os.getenv("FINAGENT_IBKR_HOST", "gateway")
IBKR_PORT = int(os.getenv("FINAGENT_IBKR_PORT", "4002"))


def _resolve_mode(dag_run_conf: Optional[Dict[str, Any]]) -> str:
    mode = (dag_run_conf or {}).get("mode") or config.finagent_autogen_default_mode or "inference"
    return str(mode).strip().lower()


def _prepare_finagent_autogen_inputs(**context):
    """Fetch IBKR market data, optional NewsAPI items, and a chart path."""
    dag_run_conf = getattr(context.get("dag_run"), "conf", {}) if context.get("dag_run") else {}
    mode = _resolve_mode(dag_run_conf)
    lookback_days = int((dag_run_conf or {}).get("backtest_lookback_days") or config.finagent_autogen_backtest_lookback_days)

    duration_days = max(200, lookback_days if mode in {"train_backtest", "both"} else 200)
    duration = f"{duration_days} D"
    bar_size = os.getenv("FINAGENT_AUTOGEN_BAR_SIZE", "1 day")

    client = IBKRClient(host=IBKR_HOST, port=IBKR_PORT)
    market_data = client.fetch_market_data(symbol=SYMBOL, duration=duration, bar_size=bar_size)
    client.disconnect()

    news_items = []
    try:
        if config.news_api_key:
            max_news = int(os.getenv("FINAGENT_AUTOGEN_NEWS_MAX_ITEMS", "10"))
            news_items = NewsAPIClient().fetch_news(ticker=SYMBOL, max_items=max_news)
    except Exception as exc:
        logger.warning("News fetch failed; continuing with empty news list: %s", exc)
        news_items = []

    chart_path = None
    try:
        charts_dir = os.getenv("CHARTS_DIR") or os.getenv("FINAGENT_AUTOGEN_CHARTS_DIR")
        generator = ChartGenerator(output_dir=charts_dir)
        chart_result = generator.generate_chart(
            market_data,
            ChartConfig(symbol=SYMBOL, timeframe=Timeframe.DAILY, lookback_periods=120),
        )
        chart_path = chart_result.file_path
    except Exception as exc:
        logger.warning("Chart generation failed; continuing without chart: %s", exc)
        chart_path = None

    ti = context["ti"]
    ti.xcom_push(key="symbol", value=SYMBOL)
    ti.xcom_push(key="market_data", value=market_data.model_dump_json())
    ti.xcom_push(key="news_items", value=json.dumps(news_items))
    ti.xcom_push(key="chart_path", value=chart_path)

    return {
        "symbol": SYMBOL,
        "mode": mode,
        "bars": market_data.bar_count,
        "latest_price": float(market_data.latest_price),
        "news_items": len(news_items),
        "chart_generated": bool(chart_path),
    }


def _train_backtest_finagent_autogen(**context):
    """Offline evaluation path (grid-search SMA crossover) logged to MLflow."""
    dag_run_conf = getattr(context.get("dag_run"), "conf", {}) if context.get("dag_run") else {}
    mode = _resolve_mode(dag_run_conf)
    if mode not in {"train_backtest", "both"}:
        logger.info("Mode=%s; skipping train/backtest.", mode)
        return {"skipped": True, "mode": mode}

    ti = context["ti"]
    market_data_json = ti.xcom_pull(task_ids="prepare_finagent_autogen_inputs", key="market_data")
    if not market_data_json:
        raise ValueError("Market data missing from XCom")

    market_data = MarketData.model_validate_json(market_data_json)
    symbol = market_data.symbol

    best, all_results = grid_search_sma_crossover(market_data)

    run_name = f"finagent_autogen_train_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    tags = {
        "workflow_type": "finagent_signal",
        "analysis_method": "finagent_autogen",
        "mode": "train_backtest",
        "environment": config.environment,
    }

    with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
        tracker.log_params(
            {
                "symbol": symbol,
                "mode": "train_backtest",
                "backtest_fast_window": best.params["fast_window"],
                "backtest_slow_window": best.params["slow_window"],
            }
        )
        tracker.log_metrics(best.metrics)
        tracker.log_artifact_dict({"best_params": best.params}, "finagent_autogen_best_params.json")
        tracker.log_artifact_dict({"grid_results": all_results}, "finagent_autogen_grid_results.json")
        tracker.log_artifact_dict({"equity_curve": best.equity_curve}, "finagent_autogen_equity_curve.json")
        run_info = {"run_id": tracker.run_id, "experiment_id": tracker.experiment_id, "best_params": best.params}

    ti.xcom_push(key="train_mlflow_info", value=json.dumps(run_info))
    return run_info


def _run_finagent_autogen_inference(**context):
    """Run AutoGen group chat and log full trace to MLflow; return a compact payload via XCom."""
    dag_run_conf = getattr(context.get("dag_run"), "conf", {}) if context.get("dag_run") else {}
    mode = _resolve_mode(dag_run_conf)
    if mode not in {"inference", "both"}:
        logger.info("Mode=%s; skipping inference.", mode)
        return {"skipped": True, "mode": mode}

    ti = context["ti"]
    market_data_json = ti.xcom_pull(task_ids="prepare_finagent_autogen_inputs", key="market_data")
    news_json = ti.xcom_pull(task_ids="prepare_finagent_autogen_inputs", key="news_items")
    chart_path = ti.xcom_pull(task_ids="prepare_finagent_autogen_inputs", key="chart_path")
    train_mlflow_json = ti.xcom_pull(task_ids="train_backtest_finagent_autogen", key="train_mlflow_info")

    if not market_data_json:
        raise ValueError("Market data missing from XCom")

    market_data = MarketData.model_validate_json(market_data_json)
    news_items = json.loads(news_json) if news_json else []
    train_mlflow_info = json.loads(train_mlflow_json) if train_mlflow_json else {}
    best_params = train_mlflow_info.get("best_params") if isinstance(train_mlflow_info, dict) else None

    orchestrator = AutoGenFinAgentOrchestrator(max_turns=config.finagent_autogen_max_rounds)
    decision = orchestrator.run(market_data=market_data, news_items=news_items)

    run_name = f"finagent_autogen_infer_{market_data.symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    tags = {
        "workflow_type": "finagent_signal",
        "analysis_method": "finagent_autogen",
        "mode": "inference",
        "environment": config.environment,
    }

    with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
        tracker.log_params(
            {
                "symbol": market_data.symbol,
                "mode": "inference",
                "autogen_max_turns": config.finagent_autogen_max_rounds,
                "autogen_team": "TechnicalAnalyst,FundamentalAnalyst,RiskManager,Executor",
                "train_run_id": str(train_mlflow_info.get("run_id") or ""),
                "train_experiment_id": str(train_mlflow_info.get("experiment_id") or ""),
            }
        )
        if best_params:
            tracker.log_params({f"best_param_{k}": v for k, v in best_params.items()})

        tracker.log_metrics(
            {
                "confidence_score": float(decision.signal.confidence_score),
            }
        )
        tracker.log_artifact_dict(decision.agent_outputs, "finagent_autogen_agent_outputs.json")
        tracker.log_artifact_dict({"signal": json.loads(decision.signal.model_dump_json())}, "finagent_autogen_signal.json")
        tracker.log_artifact_dict({"conversation": decision.conversation}, "finagent_autogen_conversation.json")
        if chart_path:
            tracker.log_file_artifact(chart_path, artifact_path="charts")
        run_info = {"run_id": tracker.run_id, "experiment_id": tracker.experiment_id}

    payload = {
        "signal": json.loads(decision.signal.model_dump_json()),
        "chart_path": chart_path,
        "analysis_method": "finagent_autogen",
        "mlflow": run_info,
    }
    ti.xcom_push(key="inference_payload", value=json.dumps(payload))
    return {"run_id": run_info["run_id"], "experiment_id": run_info.get("experiment_id"), "symbol": market_data.symbol}


def _persist_finagent_autogen_signal(**context):
    """Persist WebUI artifacts (signal/llm/chart) and attach lineage to MLflow."""
    dag_run_conf = getattr(context.get("dag_run"), "conf", {}) if context.get("dag_run") else {}
    mode = _resolve_mode(dag_run_conf)
    if mode not in {"inference", "both"}:
        logger.info("Mode=%s; skipping persistence.", mode)
        return {"skipped": True, "mode": mode}

    ti = context["ti"]
    payload_json = ti.xcom_pull(task_ids="run_finagent_autogen_inference", key="inference_payload")
    if not payload_json:
        raise ValueError("Inference payload missing from XCom")

    payload: Dict[str, Any] = json.loads(payload_json)
    signal = payload["signal"]
    mlflow_info = payload.get("mlflow") or {}
    execution_id = str(context["run_id"])

    chart_path = payload.get("chart_path")
    minio_url = None
    if chart_path:
        try:
            minio_url = upload_chart_to_minio(chart_path, signal["symbol"], timeframe="daily", execution_id=execution_id)
        except Exception as exc:
            logger.warning("MinIO upload failed; continuing without minio_url: %s", exc)
            minio_url = None

    metadata = {
        "analysis_method": payload.get("analysis_method", "finagent_autogen"),
        "mlflow_run_id": mlflow_info.get("run_id"),
        "mlflow_experiment_id": mlflow_info.get("experiment_id"),
        "chart_minio_url": minio_url,
        "chart_path": chart_path,
    }

    signal_artifact = store_artifact(
        name=f"FinAgent AutoGen Signal {signal['symbol']}",
        artifact_type="signal",
        symbol=signal["symbol"],
        run_id=mlflow_info.get("run_id"),
        experiment_id=mlflow_info.get("experiment_id"),
        workflow_id=DAG_ID,
        execution_id=execution_id,
        step_name="finagent_autogen_decision",
        dag_id=context["dag"].dag_id,
        task_id=context["task"].task_id,
        action=signal["action"],
        confidence=float(signal["confidence_score"]) / 100,
        signal_data=signal,
        metadata=metadata,
    )

    llm_artifact = store_artifact(
        name=f"FinAgent AutoGen Reasoning {signal['symbol']}",
        artifact_type="llm",
        symbol=signal["symbol"],
        run_id=mlflow_info.get("run_id"),
        experiment_id=mlflow_info.get("experiment_id"),
        workflow_id=DAG_ID,
        execution_id=execution_id,
        step_name="finagent_autogen_llm",
        dag_id=context["dag"].dag_id,
        task_id=context["task"].task_id,
        prompt="AutoGen RoundRobinGroupChat: TechnicalAnalyst, FundamentalAnalyst, RiskManager, Executor",
        response=signal.get("reasoning", ""),
        model_name=signal.get("model_used"),
        metadata={"analysis_method": payload.get("analysis_method", "finagent_autogen")},
    )

    chart_artifact = None
    if chart_path:
        chart_artifact = store_artifact(
            name=f"FinAgent AutoGen Chart {signal['symbol']}",
            artifact_type="chart",
            symbol=signal["symbol"],
            run_id=mlflow_info.get("run_id"),
            experiment_id=mlflow_info.get("experiment_id"),
            workflow_id=DAG_ID,
            execution_id=execution_id,
            step_name="finagent_autogen_chart",
            dag_id=context["dag"].dag_id,
            task_id=context["task"].task_id,
            image_path=chart_path,
            chart_type="daily",
            metadata={"minio_url": minio_url} if minio_url else None,
        )

    artifact_ids = [
        artifact.get("id")
        for artifact in [signal_artifact, llm_artifact, chart_artifact]
        if artifact and artifact.get("id")
    ]
    attach_artifact_lineage(artifact_ids, mlflow_info.get("run_id"), mlflow_info.get("experiment_id"))
    return {"artifact_ids": artifact_ids, "run_id": mlflow_info.get("run_id")}


with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="FinAgent AutoGen pipeline (train/backtest + inference) with MLflow logging",
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["finagent", "autogen", "mlflow"],
) as dag:
    prepare_inputs = PythonOperator(
        task_id="prepare_finagent_autogen_inputs",
        python_callable=_prepare_finagent_autogen_inputs,
    )

    train_backtest = PythonOperator(
        task_id="train_backtest_finagent_autogen",
        python_callable=_train_backtest_finagent_autogen,
    )

    run_inference = PythonOperator(
        task_id="run_finagent_autogen_inference",
        python_callable=_run_finagent_autogen_inference,
    )

    persist_signal = PythonOperator(
        task_id="persist_finagent_autogen_signal",
        python_callable=_persist_finagent_autogen_signal,
    )

    prepare_inputs >> train_backtest >> run_inference >> persist_signal

