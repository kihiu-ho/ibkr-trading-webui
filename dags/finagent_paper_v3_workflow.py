"""FinAgent Paper-v3 Trading Signal Workflow DAG.

Implements the arXiv:2402.18485v3 prompt pipeline (Appendix F) and fetches market intelligence via NewsAPI.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict

from airflow import DAG
try:
    # Airflow 3+
    from airflow.providers.standard.operators.python import PythonOperator
except Exception:  # pragma: no cover - Airflow 2 fallback
    from airflow.operators.python import PythonOperator

# Ensure Airflow can import local `models/` and `utils/` packages regardless of how the DAG is executed.
sys.path.append(os.path.dirname(__file__))

from models.market_data import MarketData
from utils.artifact_storage import attach_artifact_lineage, store_artifact
from utils.config import config
from utils.finagent_runner import FinAgentRunner
from utils.ibkr_client import IBKRClient
from utils.mlflow_tracking import mlflow_run_context
from utils.minio_upload import upload_chart_to_minio
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

DAG_ID = "finagent_paper_v3_workflow"
SYMBOL = config.stock_symbols[0] if config.stock_symbols else "TSLA"
IBKR_HOST = os.getenv("FINAGENT_IBKR_HOST", "gateway")
IBKR_PORT = int(os.getenv("FINAGENT_IBKR_PORT", "4002"))

# Workflow schedule configuration
# Default: every 10 minutes ('*/10 * * * *').
# Override by setting WORKFLOW_SCHEDULE (cron or preset like '@hourly').
WORKFLOW_SCHEDULE = os.getenv("WORKFLOW_SCHEDULE") or "*/10 * * * *"


def _prepare_finagent_v3_inputs(**context):
    """Fetch IBKR market data + NewsAPI market intelligence and cache in XCom."""
    logger.info("Preparing FinAgent v3 inputs for symbol: %s", SYMBOL)

    client = IBKRClient(host=IBKR_HOST, port=IBKR_PORT)
    market_data = client.fetch_market_data(symbol=SYMBOL, duration="200 D", bar_size="1 day")
    client.disconnect()

    max_news = int(os.getenv("FINAGENT_NEWS_MAX_ITEMS", "10"))
    news_client = NewsAPIClient()
    news_items = news_client.fetch_news(ticker=SYMBOL, max_items=max_news)

    ti = context["ti"]
    ti.xcom_push(key="market_data", value=market_data.model_dump_json())
    ti.xcom_push(key="symbol", value=SYMBOL)
    ti.xcom_push(key="news_items", value=json.dumps(news_items))
    return {
        "symbol": SYMBOL,
        "bars": market_data.bar_count,
        "latest_price": float(market_data.latest_price),
        "news_items": len(news_items),
    }


def _run_finagent_v3_agent(**context):
    ti = context["ti"]
    market_data_json = ti.xcom_pull(task_ids="prepare_finagent_v3_inputs", key="market_data")
    news_json = ti.xcom_pull(task_ids="prepare_finagent_v3_inputs", key="news_items")
    if not market_data_json:
        raise ValueError("Market data missing from XCom")

    market_data = MarketData.model_validate_json(market_data_json)
    news_items = json.loads(news_json) if news_json else []

    runner = FinAgentRunner(prompts_version="v3")
    result = runner.run(
        market_data=market_data,
        execution_id=str(context["run_id"]),
        dag_id=context["dag"].dag_id,
        task_id=context["task"].task_id,
        workflow_id=context["dag"].dag_id,
        news_items=news_items,
    )

    signal_dict = json.loads(result["signal"].model_dump_json())
    payload = {
        "signal": signal_dict,
        "chart_path": result["chart_path"],
        "metrics": result["metrics"],
        "llm_artifact": result["llm_artifact"],
        "market_snapshot": result["market_snapshot"],
        "news": result["news"],
        "baseline": result["baseline"],
        "analysis_method": "finagent_v3",
        "prompt_version": "v3",
    }
    ti.xcom_push(key="finagent_result", value=json.dumps(payload))
    return payload


def _log_finagent_v3_results(**context):
    ti = context["ti"]
    payload_json = ti.xcom_pull(task_ids="run_finagent_v3_agent", key="finagent_result")
    if not payload_json:
        raise ValueError("FinAgent result missing")

    payload: Dict[str, Any] = json.loads(payload_json)
    symbol = payload["signal"]["symbol"]
    run_name = f"finagent_v3_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    tags = {
        "workflow_type": "finagent_signal",
        "analysis_method": payload.get("analysis_method", "finagent_v3"),
        "prompt_version": payload.get("prompt_version", "v3"),
        "environment": config.environment,
        "news_source": "newsapi" if bool(config.news_api_key) else "none",
    }

    with mlflow_run_context(run_name=run_name, tags=tags) as tracker:
        tracker.log_params(
            {
                "symbol": symbol,
                "finagent_reflection_rounds": config.finagent_reflection_rounds,
                "finagent_toolkit": ",".join(config.finagent_toolkit),
                "llm_provider": config.llm_provider,
                "model_used": config.llm_model,
                "vision_model_used": config.llm_vision_model,
                "finagent_prompts_source": "arxiv:2402.18485v3",
                "finagent_prompts_version": payload.get("prompt_version", "v3"),
                "news_api_enabled": str(bool(config.news_api_key)),
                "news_api_base_url": config.news_api_base_url,
            }
        )
        tracker.log_metrics(payload["metrics"])
        tracker.log_artifact_dict(payload["llm_artifact"], "finagent_v3_llm_artifact.json")
        tracker.log_artifact_dict(payload["market_snapshot"], "finagent_v3_market_snapshot.json")
        tracker.log_debug_info({"news": payload.get("news")})
        chart_path = payload.get("chart_path")
        if chart_path:
            tracker.log_file_artifact(chart_path, artifact_path="charts")
        run_info = {"run_id": tracker.run_id, "experiment_id": tracker.experiment_id}

    ti.xcom_push(key="mlflow_info", value=json.dumps(run_info))
    ti.xcom_push(key="logged_result", value=payload_json)
    return run_info


def _persist_finagent_v3_signal(**context):
    ti = context["ti"]
    payload_json = ti.xcom_pull(task_ids="run_finagent_v3_agent", key="finagent_result")
    mlflow_json = ti.xcom_pull(task_ids="log_finagent_v3_results", key="mlflow_info")
    if not payload_json or not mlflow_json:
        raise ValueError("Missing FinAgent payload/mlflow info")

    payload: Dict[str, Any] = json.loads(payload_json)
    mlflow_info: Dict[str, Any] = json.loads(mlflow_json)
    execution_id = str(context["run_id"])
    signal = payload["signal"]

    chart_path = payload.get("chart_path")
    minio_url = None
    if chart_path:
        minio_url = upload_chart_to_minio(chart_path, signal["symbol"], timeframe="daily", execution_id=execution_id)

    metadata = {
        "analysis_method": payload.get("analysis_method", "finagent_v3"),
        "prompt_version": payload.get("prompt_version", "v3"),
        "baseline": payload.get("baseline"),
        "finagent_metrics": payload.get("metrics"),
        "news_items": len(payload.get("news") or []),
    }

    signal_artifact = store_artifact(
        name=f"FinAgent v3 Signal {signal['symbol']}",
        artifact_type="signal",
        symbol=signal["symbol"],
        run_id=mlflow_info.get("run_id"),
        experiment_id=mlflow_info.get("experiment_id"),
        workflow_id=DAG_ID,
        execution_id=execution_id,
        step_name="finagent_v3_decision",
        dag_id=context["dag"].dag_id,
        task_id=context["task"].task_id,
        action=signal["action"],
        confidence=float(signal["confidence_score"]) / 100,
        signal_data=signal,
        metadata=metadata,
    )

    llm_artifact = store_artifact(
        name=f"FinAgent v3 Reasoning {signal['symbol']}",
        artifact_type="llm",
        symbol=signal["symbol"],
        run_id=mlflow_info.get("run_id"),
        experiment_id=mlflow_info.get("experiment_id"),
        workflow_id=DAG_ID,
        execution_id=execution_id,
        step_name="finagent_v3_llm",
        dag_id=context["dag"].dag_id,
        task_id=context["task"].task_id,
        prompt=payload["llm_artifact"]["prompt"],
        response=payload["llm_artifact"]["response"],
        model_name=config.llm_model,
        metadata={"reflections": payload["llm_artifact"]["reflections"], "prompt_version": payload.get("prompt_version", "v3")},
    )

    chart_artifact = None
    if chart_path:
        chart_metadata = {"minio_url": minio_url} if minio_url else None
        chart_artifact = store_artifact(
            name=f"FinAgent v3 Chart {signal['symbol']}",
            artifact_type="chart",
            symbol=signal["symbol"],
            run_id=mlflow_info.get("run_id"),
            experiment_id=mlflow_info.get("experiment_id"),
            workflow_id=DAG_ID,
            execution_id=execution_id,
            step_name="finagent_v3_chart",
            dag_id=context["dag"].dag_id,
            task_id=context["task"].task_id,
            image_path=chart_path,
            chart_type="daily",
            metadata=chart_metadata,
        )

    artifact_ids = [
        artifact.get("id")
        for artifact in [signal_artifact, llm_artifact, chart_artifact]
        if artifact and artifact.get("id")
    ]
    attach_artifact_lineage(artifact_ids, mlflow_info.get("run_id"), mlflow_info.get("experiment_id"))

    return {"signal_artifact_id": signal_artifact.get("id") if signal_artifact else None, "chart_url": minio_url}


_dag_kwargs = dict(
    dag_id=DAG_ID,
    description="FinAgent paper-v3 (arXiv:2402.18485v3) trading signal workflow with NewsAPI + MLflow tracking",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    is_paused_upon_creation=False,
    max_active_runs=1,
    tags=["finagent", "paper-v3", "newsapi", "mlflow", "automated"],
)

# Airflow 3: uses `schedule`; Airflow 2: still supports `schedule_interval`.
try:
    dag = DAG(**_dag_kwargs, schedule=WORKFLOW_SCHEDULE)
except TypeError:  # pragma: no cover
    dag = DAG(**_dag_kwargs, schedule_interval=WORKFLOW_SCHEDULE)

with dag:
    prepare_task = PythonOperator(task_id="prepare_finagent_v3_inputs", python_callable=_prepare_finagent_v3_inputs)
    run_task = PythonOperator(task_id="run_finagent_v3_agent", python_callable=_run_finagent_v3_agent)
    log_task = PythonOperator(task_id="log_finagent_v3_results", python_callable=_log_finagent_v3_results)
    persist_task = PythonOperator(task_id="persist_finagent_v3_signal", python_callable=_persist_finagent_v3_signal)

    prepare_task >> run_task >> log_task >> persist_task
