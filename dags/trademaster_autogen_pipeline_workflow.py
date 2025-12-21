"""TradeMaster AutoGen Pipeline Workflow DAG.

Runs a TradeMaster train/backtest + inference pipeline per symbol and uses AutoGen to generate
an auditable TradingSignal payload (BUY/SELL/HOLD + confidence + rationale).

Symbol targeting:
  - If `dag_run.conf.symbol` is provided: run only that symbol (backend auto-trigger compatible).
  - Else: run enabled symbols assigned to this DAG via Workflow Symbols (`/api/workflow-symbols` links).

Run modes (via `dag_run.conf.mode`):
  - both (default): train_backtest + inference
  - train_backtest
  - inference
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from airflow import DAG

try:
    # Airflow 3+
    from airflow.providers.standard.operators.python import PythonOperator
except Exception:  # pragma: no cover - Airflow 2 fallback
    from airflow.operators.python import PythonOperator

# Ensure Airflow can import local `models/` and `utils/` packages regardless of how the DAG is executed.
sys.path.append(os.path.dirname(__file__))

from models.chart import ChartConfig, Timeframe
from models.market_data import MarketData
from utils.autogen_trademaster_orchestrator import AutoGenTradeMasterOrchestrator
from utils.chart_generator import ChartGenerator
from utils.config import config
from utils.ibkr_client import IBKRClient
from utils.minio_upload import upload_chart_to_minio
from utils.mlflow_tracking import mlflow_run_context
from utils.trademaster_runner import TradeMasterRunConfig, infer_trademaster, train_backtest_trademaster
from utils.artifact_storage import attach_artifact_lineage, store_artifact

logger = logging.getLogger(__name__)


DEFAULT_ARGS = {
    "owner": "ibkr-trading",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

DAG_ID = "trademaster_autogen_pipeline_workflow"
IBKR_HOST = getattr(config, "ibkr_host", "ibkr-gateway")
IBKR_PORT = int(getattr(config, "ibkr_port", 4002))


def _resolve_mode(dag_run_conf: Optional[Dict[str, Any]]) -> str:
    mode = (dag_run_conf or {}).get("mode") or getattr(config, "trademaster_autogen_default_mode", None) or "both"
    normalized = str(mode).strip().lower()
    if normalized not in {"both", "train_backtest", "inference"}:
        return "both"
    return normalized


def _backend_url() -> str:
    return os.getenv("BACKEND_API_URL", "http://backend:8000").rstrip("/")


def _fetch_symbol_detail(symbol: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"{_backend_url()}/api/workflow-symbols/{symbol}"
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None
        return resp.json()
    except Exception as exc:
        logger.warning("Failed fetching symbol detail from backend (%s): %s", symbol, exc)
        return None


def _fetch_enabled_symbols() -> List[Dict[str, Any]]:
    try:
        url = f"{_backend_url()}/api/workflow-symbols/?enabled_only=true"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list):
            return data
        return []
    except Exception as exc:
        logger.warning("Failed fetching workflow symbols from backend: %s", exc)
        return []


def _select_dag_link(symbol_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for link in symbol_record.get("workflows") or []:
        if link.get("dag_id") == DAG_ID and bool(link.get("is_active", True)):
            return link
    return None


def _resolve_targets(**context):
    dag_run_conf = getattr(context.get("dag_run"), "conf", {}) if context.get("dag_run") else {}
    symbol_override = (dag_run_conf or {}).get("symbol")
    targets: List[Dict[str, Any]] = []

    if symbol_override:
        symbol = str(symbol_override).strip().upper()
        record = _fetch_symbol_detail(symbol) or {"symbol": symbol}
        link = _select_dag_link(record) or {"dag_id": DAG_ID, "is_active": True, "config": None}
        targets.append(
            {
                "symbol": symbol,
                "conid": record.get("conid") or dag_run_conf.get("conid"),
                "workflow_symbol_id": record.get("id") or dag_run_conf.get("workflow_symbol_id"),
                "link": link,
                "priority": record.get("priority", 0),
            }
        )
        context["ti"].xcom_push(key="targets", value=json.dumps(targets))
        return {"count": len(targets), "mode": _resolve_mode(dag_run_conf), "single_symbol": True}

    symbols = _fetch_enabled_symbols()
    for record in symbols:
        link = _select_dag_link(record)
        if not link:
            continue
        targets.append(
            {
                "symbol": str(record.get("symbol") or "").strip().upper(),
                "conid": record.get("conid"),
                "workflow_symbol_id": record.get("id"),
                "link": link,
                "priority": record.get("priority", 0),
            }
        )

    # Sort by priority desc, then symbol for stability.
    targets = sorted(targets, key=lambda t: (-int(t.get("priority") or 0), str(t.get("symbol") or "")))

    # Guardrail: cap batch size (defaults to 10 if not configured).
    max_symbols = int(getattr(config, "trademaster_autogen_max_symbols", 10) or 10)
    if max_symbols > 0:
        targets = targets[:max_symbols]

    context["ti"].xcom_push(key="targets", value=json.dumps(targets))
    return {"count": len(targets), "mode": _resolve_mode(dag_run_conf), "single_symbol": False}


def _run_pipeline(**context):
    dag_run_conf = getattr(context.get("dag_run"), "conf", {}) if context.get("dag_run") else {}
    mode = _resolve_mode(dag_run_conf)

    ti = context["ti"]
    targets_json = ti.xcom_pull(task_ids="resolve_trademaster_targets", key="targets")
    targets: List[Dict[str, Any]] = json.loads(targets_json) if targets_json else []

    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []

    for target in targets:
        symbol = str(target.get("symbol") or "").strip().upper()
        if not symbol:
            continue

        try:
            link = target.get("link") or {}
            link_config = link.get("config") or {}
            run_overrides = (dag_run_conf or {}).get("config") or {}
            merged_cfg = {**(link_config or {}), **(run_overrides or {})}

            run_config = TradeMasterRunConfig.from_dict(merged_cfg.get("trademaster") or merged_cfg)

            lookback_days = int(
                merged_cfg.get("backtest_lookback_days")
                or getattr(config, "trademaster_autogen_backtest_lookback_days", 365)
                or 365
            )
            duration_days = max(200, lookback_days) if mode in {"train_backtest", "both"} else 200
            duration = f"{duration_days} D"
            bar_size = str(merged_cfg.get("bar_size") or os.getenv("TRADEMASTER_AUTOGEN_BAR_SIZE", "1 day"))

            client = IBKRClient(host=IBKR_HOST, port=IBKR_PORT)
            market_data = client.fetch_market_data(symbol=symbol, duration=duration, bar_size=bar_size)
            client.disconnect()

            execution_id = str(context.get("run_id") or "")

            train_result = None
            if mode in {"train_backtest", "both"}:
                train_run_name = f"trademaster_train_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                with mlflow_run_context(
                    run_name=train_run_name,
                    tags={
                        "workflow_type": "trademaster_autogen",
                        "analysis_method": "trademaster",
                        "mode": "train_backtest",
                        "environment": config.environment,
                        "symbol": symbol,
                    },
                ) as tracker:
                    train_result = train_backtest_trademaster(
                        market_data,
                        symbol=symbol,
                        run_config=run_config,
                        work_dir=os.path.join("/tmp", "trademaster", execution_id, symbol, "train"),
                    )
                    tracker.log_params({"symbol": symbol, "mode": "train_backtest", "bar_size": bar_size, "duration": duration})
                    tracker.log_metrics({k: float(v) for k, v in train_result.metrics.items() if isinstance(v, (int, float))})
                    tracker.log_artifact_dict(
                        {
                            "metrics": train_result.metrics,
                            "best_model_path": train_result.best_model_path,
                            "work_dir": train_result.work_dir,
                        },
                        "trademaster_train_summary.json",
                    )
                    # Optional artifacts created by TradeMaster runner (if present).
                    # - DQN path writes under `<work_dir>/run/*`
                    # - fallback writes under `<work_dir>/*`
                    for filename in (
                        "test_result.csv",
                        "fallback_grid_results.json",
                        "fallback_best_params.json",
                        "fallback_equity_curve.json",
                    ):
                        candidates = [
                            os.path.join(train_result.work_dir, "run", filename),
                            os.path.join(train_result.work_dir, filename),
                        ]
                        for candidate in candidates:
                            if os.path.exists(candidate):
                                tracker.log_file_artifact(candidate, artifact_path="trademaster")
                                break

                train_mlflow = {"run_id": tracker.run_id, "experiment_id": tracker.experiment_id}
            else:
                train_mlflow = {}

            infer_result = None
            if mode in {"inference", "both"}:
                best_model_path = None
                if train_result and train_result.best_model_path:
                    best_model_path = train_result.best_model_path
                best_model_path = str(dag_run_conf.get("best_model_path") or best_model_path or "") or None

                infer_run_name = f"trademaster_infer_{symbol}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                with mlflow_run_context(
                    run_name=infer_run_name,
                    tags={
                        "workflow_type": "trademaster_autogen",
                        "analysis_method": "trademaster_autogen",
                        "mode": "inference",
                        "environment": config.environment,
                        "symbol": symbol,
                    },
                ) as tracker:
                    infer_result = infer_trademaster(
                        market_data,
                        symbol=symbol,
                        run_config=run_config,
                        best_model_path=best_model_path,
                        work_dir=os.path.join("/tmp", "trademaster", execution_id, symbol, "infer"),
                    )

                    trademaster_summary = {
                        "symbol": symbol,
                        "mode": mode,
                        "train_metrics": (train_result.metrics if train_result else None),
                        "train_suggested_action": (train_result.suggested_action if train_result else None),
                        "train_suggested_raw_action": (train_result.suggested_raw_action if train_result else None),
                        "inference_action": infer_result.action if infer_result else None,
                        "inference_raw_action": infer_result.raw_action if infer_result else None,
                        "inference_details": infer_result.details if infer_result else None,
                        "train_mlflow": train_mlflow,
                    }

                    orchestrator = AutoGenTradeMasterOrchestrator(max_turns=getattr(config, "trademaster_autogen_max_rounds", 8))
                    decision = orchestrator.run(market_data=market_data, trademaster_summary=trademaster_summary)

                    tracker.log_params(
                        {
                            "symbol": symbol,
                            "mode": "inference",
                            "bar_size": bar_size,
                            "duration": duration,
                            "trademaster_inference_action": str(infer_result.action if infer_result else ""),
                            "trademaster_best_model_path": str(best_model_path or ""),
                        }
                    )
                    tracker.log_metrics({"confidence_score": float(decision.signal.confidence_score)})
                    tracker.log_artifact_dict({"conversation": decision.conversation}, "trademaster_autogen_conversation.json")
                    tracker.log_artifact_dict(decision.agent_outputs, "trademaster_autogen_agent_outputs.json")
                    tracker.log_artifact_dict({"signal": json.loads(decision.signal.model_dump_json())}, "trademaster_autogen_signal.json")

                    # Optional chart for WebUI convenience (best-effort)
                    chart_path = None
                    minio_url = None
                    try:
                        charts_dir = os.getenv("CHARTS_DIR", "/app/charts")
                        generator = ChartGenerator(output_dir=charts_dir)
                        chart_result = generator.generate_chart(
                            market_data,
                            ChartConfig(symbol=symbol, timeframe=Timeframe.DAILY, lookback_periods=120),
                        )
                        chart_path = chart_result.file_path
                        try:
                            minio_url = upload_chart_to_minio(chart_path, symbol, timeframe="daily", execution_id=execution_id)
                        except Exception as exc:
                            logger.warning("MinIO upload failed; continuing without minio_url: %s", exc)
                            minio_url = None
                        tracker.log_file_artifact(chart_path, artifact_path="charts")
                    except Exception as exc:
                        logger.warning("Chart generation failed; continuing without chart: %s", exc)

                    infer_mlflow = {"run_id": tracker.run_id, "experiment_id": tracker.experiment_id}

                    # Persist WebUI artifacts (signal + llm + optional chart)
                    signal_payload = json.loads(decision.signal.model_dump_json())
                    metadata = {
                        "analysis_method": "trademaster_autogen",
                        "trademaster_summary": trademaster_summary,
                        "chart_path": chart_path,
                        "chart_minio_url": minio_url,
                    }

                    signal_artifact = store_artifact(
                        name=f"TradeMaster AutoGen Signal {symbol}",
                        artifact_type="signal",
                        symbol=symbol,
                        run_id=infer_mlflow.get("run_id"),
                        experiment_id=infer_mlflow.get("experiment_id"),
                        workflow_id=DAG_ID,
                        execution_id=execution_id,
                        step_name="trademaster_autogen_decision",
                        dag_id=context["dag"].dag_id,
                        task_id=context["task"].task_id,
                        action=signal_payload.get("action"),
                        confidence=float(signal_payload.get("confidence_score", 50)) / 100.0,
                        signal_data=signal_payload,
                        metadata=metadata,
                    )

                    llm_artifact = store_artifact(
                        name=f"TradeMaster AutoGen Reasoning {symbol}",
                        artifact_type="llm",
                        symbol=symbol,
                        run_id=infer_mlflow.get("run_id"),
                        experiment_id=infer_mlflow.get("experiment_id"),
                        workflow_id=DAG_ID,
                        execution_id=execution_id,
                        step_name="trademaster_autogen_llm",
                        dag_id=context["dag"].dag_id,
                        task_id=context["task"].task_id,
                        prompt="AutoGen RoundRobinGroupChat: TechnicalAnalyst, StrategyAnalyst, RiskManager, Executor",
                        response=signal_payload.get("reasoning", ""),
                        model_name=signal_payload.get("model_used"),
                        metadata={"analysis_method": "trademaster_autogen"},
                    )

                    chart_artifact = None
                    if chart_path:
                        chart_artifact = store_artifact(
                            name=f"TradeMaster AutoGen Chart {symbol}",
                            artifact_type="chart",
                            symbol=symbol,
                            run_id=infer_mlflow.get("run_id"),
                            experiment_id=infer_mlflow.get("experiment_id"),
                            workflow_id=DAG_ID,
                            execution_id=execution_id,
                            step_name="trademaster_autogen_chart",
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
                    attach_artifact_lineage(artifact_ids, infer_mlflow.get("run_id"), infer_mlflow.get("experiment_id"))

                    results.append(
                        {
                            "symbol": symbol,
                            "mode": mode,
                            "train_mlflow": train_mlflow,
                            "infer_mlflow": infer_mlflow,
                            "artifact_ids": artifact_ids,
                            "inference_action": infer_result.action if infer_result else None,
                        }
                    )
            else:
                # train_backtest-only mode result summary
                results.append({"symbol": symbol, "mode": mode, "train_mlflow": train_mlflow})

        except Exception as exc:
            logger.exception("TradeMaster pipeline failed for %s: %s", symbol, exc)
            failures.append({"symbol": symbol, "error": str(exc)})

    if failures and not results:
        raise RuntimeError(f"TradeMaster pipeline failed for all symbols: {failures}")

    return {"results": results, "failures": failures, "mode": mode, "count": len(results), "failed": len(failures)}


with DAG(
    dag_id=DAG_ID,
    default_args=DEFAULT_ARGS,
    description="TradeMaster pipeline (train/backtest + inference) with AutoGen review and MLflow logging",
    schedule_interval=None,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["trademaster", "autogen", "mlflow"],
) as dag:
    resolve_targets = PythonOperator(
        task_id="resolve_trademaster_targets",
        python_callable=_resolve_targets,
    )

    run_pipeline = PythonOperator(
        task_id="run_trademaster_autogen_pipeline",
        python_callable=_run_pipeline,
    )

    resolve_targets >> run_pipeline
