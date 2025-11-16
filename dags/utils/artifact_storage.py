"""
Artifact Storage Utility - Store artifacts in database from Airflow DAGs
OpenSpec 2 Compliant - Enhanced with retry logic and better error handling
"""
import logging
import os
import requests
import time
import json
from typing import Dict, Any, Optional
from pathlib import Path
from decimal import Decimal

logger = logging.getLogger(__name__)

# Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
RETRY_BACKOFF = 2  # exponential backoff multiplier


def _convert_decimals(obj: Any) -> Any:
    """
    Recursively convert Decimal objects to float or string for JSON serialization.
    
    Args:
        obj: Object that may contain Decimal values
        
    Returns:
        Object with Decimal values converted to float/string
    """
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: _convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [_convert_decimals(item) for item in obj]
    else:
        return obj


def update_artifact(
    artifact_id: int,
    updates: Dict[str, Any],
    merge_metadata: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Update an existing artifact via API.
    
    Args:
        artifact_id: Artifact ID to update
        updates: Dict of fields to update
        merge_metadata: If True, merge new metadata with existing metadata instead of replacing
        
    Returns:
        Updated artifact dict or None if failed
    """
    try:
        backend_url = os.getenv('BACKEND_API_URL', 'http://backend:8000')
        
        # If merging metadata, fetch existing artifact first
        if merge_metadata and 'metadata' in updates:
            try:
                get_response = requests.get(f"{backend_url}/api/artifacts/{artifact_id}", timeout=5)
                if get_response.status_code == 200:
                    existing_artifact = get_response.json()
                    existing_metadata = existing_artifact.get('metadata', {})
                    
                    # Merge new metadata with existing
                    if existing_metadata:
                        merged_metadata = {**existing_metadata, **updates['metadata']}
                        updates['metadata'] = merged_metadata
                        logger.debug(f"Merged metadata for artifact {artifact_id}")
            except Exception as e:
                logger.warning(f"Failed to fetch existing metadata for merge: {e}")
                # Continue with update anyway
        
        api_url = f"{backend_url}/api/artifacts/{artifact_id}"
        
        # Convert Decimal values
        if 'metadata' in updates:
            updates['metadata'] = _convert_decimals(updates['metadata'])
        if 'chart_data' in updates:
            updates['chart_data'] = _convert_decimals(updates['chart_data'])
        if 'signal_data' in updates:
            updates['signal_data'] = _convert_decimals(updates['signal_data'])
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.patch(api_url, json=updates, timeout=10)
                response.raise_for_status()
                artifact = response.json()
                logger.info(f"✅ Updated artifact: {artifact_id}")
                return artifact
            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.warning(f"Retry {attempt + 1}/{MAX_RETRIES} updating artifact {artifact_id}: {e}")
                    time.sleep(delay)
                    continue
                raise
        
        return None
    except Exception as e:
        logger.error(f"❌ Failed to update artifact {artifact_id}: {e}", exc_info=True)
        return None


def attach_artifact_lineage(
    artifact_ids: list[int],
    run_id: Optional[str],
    experiment_id: Optional[str]
) -> None:
    """Attach MLflow lineage identifiers to stored artifacts."""
    if not run_id:
        return
    lineage_updates = {'run_id': run_id}
    if experiment_id:
        lineage_updates['experiment_id'] = experiment_id
    for artifact_id in [aid for aid in artifact_ids if aid]:
        try:
            update_artifact(artifact_id, lineage_updates, merge_metadata=False)
        except Exception as exc:
            logger.warning(f"Failed to tag artifact {artifact_id} with MLflow lineage: {exc}")


def store_artifact(
    name: str,
    artifact_type: str,
    symbol: Optional[str] = None,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    prompt: Optional[str] = None,
    response: Optional[str] = None,
    model_name: Optional[str] = None,
    image_path: Optional[str] = None,
    chart_type: Optional[str] = None,
    chart_data: Optional[Dict[str, Any]] = None,
    action: Optional[str] = None,
    confidence: Optional[float] = None,
    signal_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Store an artifact in the database via API.
    
    Args:
        name: Artifact name
        artifact_type: 'llm', 'chart', or 'signal'
        symbol: Trading symbol (optional)
        run_id: MLflow run ID (optional)
        experiment_id: MLflow experiment ID (optional)
        workflow_id: Workflow identifier (optional)
        execution_id: Workflow execution/run ID (optional)
        step_name: Workflow step name (optional)
        dag_id: Airflow DAG ID (optional)
        task_id: Airflow task ID (optional)
        prompt: LLM prompt (for 'llm' type)
        response: LLM response (for 'llm' type)
        model_name: LLM model name (for 'llm' type)
        image_path: Path to chart image (for 'chart' type)
        chart_type: Type of chart (for 'chart' type)
        chart_data: Chart data as dict (for 'chart' type)
        action: Trading action BUY/SELL/HOLD (for 'signal' type)
        confidence: Confidence score 0-1 (for 'signal' type)
        signal_data: Full signal details (for 'signal' type)
        metadata: Additional metadata
    
    Returns:
        Created artifact dict or None if failed
    """
    try:
        # Get backend API URL from environment or use default
        backend_url = os.getenv('BACKEND_API_URL', 'http://backend:8000')
        api_url = f"{backend_url}/api/artifacts/"
        
        # Build artifact payload
        artifact_data = {
            'name': name,
            'type': artifact_type,
        }
        
        if symbol:
            artifact_data['symbol'] = symbol
        if run_id:
            artifact_data['run_id'] = run_id
        if experiment_id:
            artifact_data['experiment_id'] = experiment_id
        if workflow_id:
            artifact_data['workflow_id'] = workflow_id
        if execution_id:
            artifact_data['execution_id'] = execution_id
        if step_name:
            artifact_data['step_name'] = step_name
        if dag_id:
            artifact_data['dag_id'] = dag_id
        if task_id:
            artifact_data['task_id'] = task_id
        
        # Type-specific fields
        if artifact_type == 'llm':
            if prompt:
                artifact_data['prompt'] = prompt
            if response:
                artifact_data['response'] = response
            if model_name:
                artifact_data['model_name'] = model_name
        
        elif artifact_type == 'chart':
            if image_path:
                # Convert to relative path or URL
                artifact_data['image_path'] = image_path
            if chart_type:
                artifact_data['chart_type'] = chart_type
            if chart_data:
                artifact_data['chart_data'] = chart_data
        
        elif artifact_type == 'signal':
            if action:
                artifact_data['action'] = action
            if confidence is not None:
                # Convert Decimal to float for JSON serialization
                if isinstance(confidence, Decimal):
                    artifact_data['confidence'] = float(confidence)
                else:
                    artifact_data['confidence'] = float(confidence)
            if signal_data:
                # Convert Decimal values in signal_data to float/string
                artifact_data['signal_data'] = _convert_decimals(signal_data)
        
        if metadata:
            # Convert Decimal values in metadata to float/string
            artifact_data['metadata'] = _convert_decimals(metadata)
        
        if chart_data:
            # Convert Decimal values in chart_data to float/string
            artifact_data['chart_data'] = _convert_decimals(chart_data)
        
        # Make API request with retry logic
        last_exception = None
        for attempt in range(MAX_RETRIES):
            try:
                logger.debug(f"Attempting to store artifact (attempt {attempt + 1}/{MAX_RETRIES})")
                response = requests.post(api_url, json=artifact_data, timeout=10)
                response.raise_for_status()
                
                artifact = response.json()
                logger.info(f"✅ Stored artifact: {artifact['id']} ({artifact_type}) - {name}")
                
                return artifact
            
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                continue
            
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Timeout on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                continue
            
            except requests.exceptions.HTTPError as e:
                # Don't retry on 4xx client errors (except 429 Too Many Requests)
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    logger.error(f"❌ Client error storing artifact (HTTP {response.status_code}): {e}")
                    logger.debug(f"Response: {response.text}")
                    return None
                
                last_exception = e
                logger.warning(f"HTTP error on attempt {attempt + 1}/{MAX_RETRIES} (HTTP {response.status_code}): {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                continue
            
            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAY * (RETRY_BACKOFF ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                continue
        
        # All retries exhausted
        logger.error(f"❌ Failed to store artifact after {MAX_RETRIES} attempts: {last_exception}")
        logger.debug(f"API URL: {api_url}, Payload: {artifact_data}")
        return None
    
    except Exception as e:
        logger.error(f"❌ Unexpected error storing artifact: {e}", exc_info=True)
        logger.debug(f"Artifact data: {artifact_data}")
        return None


def store_llm_artifact(
    name: str,
    symbol: str,
    prompt: str,
    response: str,
    model_name: str,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to store LLM artifact."""
    return store_artifact(
        name=name,
        artifact_type='llm',
        symbol=symbol,
        run_id=run_id,
        experiment_id=experiment_id,
        workflow_id=workflow_id,
        execution_id=execution_id,
        step_name=step_name,
        dag_id=dag_id,
        task_id=task_id,
        prompt=prompt,
        response=response,
        model_name=model_name,
        metadata=metadata
    )


def store_chart_artifact(
    name: str,
    symbol: str,
    image_path: str,
    chart_type: str,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    chart_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to store chart artifact."""
    return store_artifact(
        name=name,
        artifact_type='chart',
        symbol=symbol,
        run_id=run_id,
        experiment_id=experiment_id,
        workflow_id=workflow_id,
        execution_id=execution_id,
        step_name=step_name,
        dag_id=dag_id,
        task_id=task_id,
        image_path=image_path,
        chart_type=chart_type,
        chart_data=chart_data,
        metadata=metadata
    )


def store_signal_artifact(
    name: str,
    symbol: str,
    action: str,
    confidence: float,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    signal_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to store trading signal artifact."""
    return store_artifact(
        name=name,
        artifact_type='signal',
        symbol=symbol,
        run_id=run_id,
        experiment_id=experiment_id,
        workflow_id=workflow_id,
        execution_id=execution_id,
        step_name=step_name,
        dag_id=dag_id,
        task_id=task_id,
        action=action,
        confidence=confidence,
        signal_data=signal_data,
        metadata=metadata
    )


def store_order_artifact(
    name: str,
    symbol: str,
    order_id: str,
    order_type: str,
    side: str,
    quantity: int,
    price: Optional[float] = None,
    status: Optional[str] = None,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    order_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to store order artifact."""
    # Store order data in metadata since 'order' type is not in base model
    order_metadata = {
        'order_id': order_id,
        'order_type': order_type,
        'side': side,
        'quantity': quantity,
    }
    if price:
        order_metadata['price'] = price
    if status:
        order_metadata['status'] = status
    if order_data:
        order_metadata.update(order_data)
    if metadata:
        order_metadata.update(metadata)
    
    # Use 'signal' type as a workaround, or we can extend the model later
    # For now, store as signal type with order data in metadata
    return store_artifact(
        name=name,
        artifact_type='signal',  # Temporary: use signal type until model is extended
        symbol=symbol,
        run_id=run_id,
        experiment_id=experiment_id,
        workflow_id=workflow_id,
        execution_id=execution_id,
        step_name=step_name,
        dag_id=dag_id,
        task_id=task_id,
        action=side,  # Use action field for side
        confidence=1.0 if status == 'filled' else 0.5,  # Use confidence for status indicator
        signal_data={'artifact_type': 'order', **order_metadata},  # Mark as order in signal_data
        metadata=order_metadata
    )


def store_trade_artifact(
    name: str,
    symbol: str,
    trade_id: str,
    order_id: str,
    quantity: int,
    price: float,
    side: str,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    trade_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to store trade artifact."""
    # Store trade data in metadata
    trade_metadata = {
        'trade_id': trade_id,
        'order_id': order_id,
        'quantity': quantity,
        'price': price,
        'side': side,
    }
    if trade_data:
        trade_metadata.update(trade_data)
    if metadata:
        trade_metadata.update(metadata)
    
    # Use 'signal' type as a workaround
    return store_artifact(
        name=name,
        artifact_type='signal',  # Temporary: use signal type until model is extended
        symbol=symbol,
        run_id=run_id,
        experiment_id=experiment_id,
        workflow_id=workflow_id,
        execution_id=execution_id,
        step_name=step_name,
        dag_id=dag_id,
        task_id=task_id,
        action=side,  # Use action field for side
        confidence=1.0,  # Trades are executed, so confidence is 100%
        signal_data={'artifact_type': 'trade', **trade_metadata},  # Mark as trade in signal_data
        metadata=trade_metadata
    )


def store_portfolio_artifact(
    name: str,
    account_id: str,
    total_value: float,
    cash_balance: float,
    position_count: int,
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    execution_id: Optional[str] = None,
    step_name: Optional[str] = None,
    dag_id: Optional[str] = None,
    task_id: Optional[str] = None,
    portfolio_data: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Convenience function to store portfolio artifact."""
    # Store portfolio data in metadata
    portfolio_metadata = {
        'account_id': account_id,
        'total_value': total_value,
        'cash_balance': cash_balance,
        'position_count': position_count,
    }
    if portfolio_data:
        portfolio_metadata.update(portfolio_data)
    if metadata:
        portfolio_metadata.update(metadata)
    
    # Use 'signal' type as a workaround (portfolio is not symbol-specific)
    return store_artifact(
        name=name,
        artifact_type='signal',  # Temporary: use signal type until model is extended
        symbol=None,  # Portfolio is not symbol-specific
        run_id=run_id,
        experiment_id=experiment_id,
        workflow_id=workflow_id,
        execution_id=execution_id,
        step_name=step_name,
        dag_id=dag_id,
        task_id=task_id,
        action='HOLD',  # Portfolio snapshot, no action
        confidence=1.0,  # Portfolio data is factual
        signal_data={'artifact_type': 'portfolio', **portfolio_metadata},  # Mark as portfolio in signal_data
        metadata=portfolio_metadata
    )
