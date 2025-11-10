"""
Airflow API Proxy Routes (FastAPI)
Proxy requests to Airflow REST API
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response
import requests
from requests.auth import HTTPBasicAuth
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

AIRFLOW_API_URL = "http://airflow-webserver:8080/api/v1"
AIRFLOW_USER = "airflow"
AIRFLOW_PASSWORD = "airflow"

def get_airflow_session():
    """Get configured Airflow API session"""
    session = requests.Session()
    session.auth = HTTPBasicAuth(AIRFLOW_USER, AIRFLOW_PASSWORD)
    return session

@router.get('/dags')
async def list_dags(request: Request):
    """List all DAGs"""
    try:
        session = get_airflow_session()
        url = f"{AIRFLOW_API_URL}/dags"
        response = session.get(url, params=dict(request.query_params))
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to list DAGs: {e}")
        return JSONResponse(content={'error': str(e)}, status_code=500)

@router.get('/dags/{dag_id}')
async def get_dag(dag_id: str):
    """Get specific DAG details"""
    try:
        session = get_airflow_session()
        url = f"{AIRFLOW_API_URL}/dags/{dag_id}"
        response = session.get(url)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to get DAG {dag_id}: {e}")
        return JSONResponse(content={'error': str(e)}, status_code=500)

@router.get('/dags/{dag_id}/dagRuns')
@router.post('/dags/{dag_id}/dagRuns')
async def dag_runs(dag_id: str, request: Request):
    """Get DAG runs or trigger new run"""
    try:
        session = get_airflow_session()
        url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns"
        
        if request.method == 'POST':
            # Validate trigger conditions before forwarding to Airflow
            validation_error = await validate_trigger_conditions(session, dag_id)
            if validation_error:
                return JSONResponse(
                    content={
                        'error': validation_error['error'],
                        'message': validation_error['message'],
                        'suggestion': validation_error.get('suggestion', '')
                    },
                    status_code=validation_error['status_code']
                )
            
            body = await request.json()
            response = session.post(url, json=body)
            response_data = response.json()
            
            # Check if run was queued due to max_active_runs
            if response.status_code == 200 and response_data.get('state') == 'queued':
                # Check for active runs
                active_runs_url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns?state=running"
                active_response = session.get(active_runs_url)
                if active_response.status_code == 200:
                    active_data = active_response.json()
                    active_count = active_data.get('total_entries', 0)
                    if active_count > 0:
                        # Get DAG info to check max_active_runs
                        dag_url = f"{AIRFLOW_API_URL}/dags/{dag_id}"
                        dag_response = session.get(dag_url)
                        if dag_response.status_code == 200:
                            dag_data = dag_response.json()
                            max_active_runs = dag_data.get('max_active_runs', 1)
                            if active_count >= max_active_runs:
                                response_data['queued_reason'] = 'max_active_runs'
                                response_data['active_runs_count'] = active_count
                                response_data['max_active_runs'] = max_active_runs
                                response_data['message'] = f'Workflow triggered successfully but queued due to max_active_runs limit ({max_active_runs}). {active_count} active run(s) blocking execution.'
            
            return JSONResponse(content=response_data, status_code=response.status_code)
        else:
            response = session.get(url, params=dict(request.query_params))
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to handle DAG runs for {dag_id}: {e}", exc_info=True)
        return JSONResponse(content={'error': str(e)}, status_code=500)


async def validate_trigger_conditions(session, dag_id: str):
    """Validate conditions before triggering a DAG"""
    try:
        # Check if DAG exists and get its status
        dag_url = f"{AIRFLOW_API_URL}/dags/{dag_id}"
        dag_response = session.get(dag_url)
        
        if dag_response.status_code == 404:
            return {
                'error': 'DAG not found',
                'message': f'DAG "{dag_id}" does not exist or is not accessible',
                'status_code': 404,
                'suggestion': 'Check that the DAG ID is correct and the DAG is properly configured'
            }
        
        if dag_response.status_code != 200:
            return {
                'error': 'Failed to validate DAG',
                'message': f'Unable to retrieve DAG information: {dag_response.status_code}',
                'status_code': 503,
                'suggestion': 'Check Airflow connection and try again'
            }
        
        dag_data = dag_response.json()
        
        # Check if DAG is paused
        if dag_data.get('is_paused', False):
            return {
                'error': 'DAG is paused',
                'message': f'DAG "{dag_id}" is paused and cannot be triggered',
                'status_code': 400,
                'suggestion': 'Unpause the DAG in Airflow UI before triggering'
            }
        
        # Check for import errors
        if dag_data.get('has_import_errors', False):
            return {
                'error': 'DAG has import errors',
                'message': f'DAG "{dag_id}" has import errors and cannot be triggered',
                'status_code': 400,
                'suggestion': 'Fix import errors in the DAG file before triggering'
            }
        
        # Check active runs vs max_active_runs
        max_active_runs = dag_data.get('max_active_runs', 1)
        if max_active_runs > 0:
            active_runs_url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns?state=running"
            active_response = session.get(active_runs_url)
            if active_response.status_code == 200:
                active_data = active_response.json()
                active_count = active_data.get('total_entries', 0)
                if active_count >= max_active_runs:
                    # Allow trigger but it will be queued - this is not an error
                    # Return None to allow trigger, but include warning in response
                    pass
        
        return None  # Validation passed
        
    except Exception as e:
        logger.error(f"Error validating trigger conditions for {dag_id}: {e}", exc_info=True)
        return {
            'error': 'Validation error',
            'message': f'Failed to validate trigger conditions: {str(e)}',
            'status_code': 500,
            'suggestion': 'Check Airflow connection and try again'
        }

# IMPORTANT: More specific routes must be defined before less specific ones
# This route handles task instance logs - must come before the general taskInstances route
@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances/{task_id}/logs/{try_number}')
async def task_instance_logs(
    dag_id: str, 
    dag_run_id: str, 
    task_id: str, 
    try_number: int,
    request: Request
):
    """Get logs for a specific task instance"""
    logger.info(f"Task instance logs endpoint called: dag_id={dag_id}, dag_run_id={dag_run_id}, task_id={task_id}, try_number={try_number}")
    try:
        session = get_airflow_session()
        # Airflow API endpoint for task instance logs
        # Note: Airflow API uses URL-encoded dag_run_id
        from urllib.parse import quote
        encoded_dag_run_id = quote(dag_run_id, safe='')
        url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{encoded_dag_run_id}/taskInstances/{task_id}/logs/{try_number}"
        
        # Get query parameters
        params = dict(request.query_params)
        # Add full_content parameter if not present (to get full logs)
        if 'full_content' not in params:
            params['full_content'] = 'true'
        
        logger.info(f"Fetching logs from Airflow: {url} with params {params}")
        
        # Make request to Airflow API
        response = session.get(url, params=params, stream=False, timeout=30)
        
        logger.info(f"Airflow API response status: {response.status_code}")
        
        # Check if response is successful
        if response.status_code == 200:
            try:
                # Try to parse as JSON first (Airflow v2+ returns JSON)
                content = response.json()
                logger.debug(f"Received JSON response with keys: {list(content.keys()) if isinstance(content, dict) else 'not a dict'}")
                
                # Check if content is empty
                if isinstance(content, dict):
                    # Airflow v2+ format: {"content": "...", "continuation_token": "..."}
                    log_content = content.get('content', '')
                    if not log_content or log_content.strip() == '':
                        logger.warning(f"Log content is empty for {dag_id}/{dag_run_id}/{task_id}")
                        return JSONResponse(
                            content={
                                'content': '',
                                'message': 'No logs available for this task instance',
                                'empty': True
                            },
                            status_code=200
                        )
                    # Return consistent format with extracted content
                    return JSONResponse(
                        content={
                            'content': log_content,
                            'raw': False
                        },
                        status_code=response.status_code
                    )
                
                # If not a dict, return as-is but wrap in consistent format
                return JSONResponse(
                    content={
                        'content': str(content),
                        'raw': False
                    },
                    status_code=response.status_code
                )
            except ValueError:
                # If not JSON, return as text (Airflow v1 or raw logs)
                log_text = response.text
                if not log_text or log_text.strip() == '':
                    logger.warning(f"Log text is empty for {dag_id}/{dag_run_id}/{task_id}")
                    return JSONResponse(
                        content={
                            'content': '',
                            'message': 'No logs available for this task instance',
                            'raw': True,
                            'empty': True
                        },
                        status_code=200
                    )
                
                return JSONResponse(
                    content={
                        'content': log_text,
                        'raw': True
                    },
                    status_code=response.status_code
                )
        elif response.status_code == 404:
            logger.warning(f"Task instance logs not found: {dag_id}/{dag_run_id}/{task_id}")
            return JSONResponse(
                content={
                    'error': 'Logs not found',
                    'message': f'No logs available for task {task_id} in DAG run {dag_run_id}',
                    'empty': True
                },
                status_code=404
            )
        else:
            # Return error response
            try:
                error_content = response.json()
            except ValueError:
                error_content = {'error': response.text}
            
            logger.error(f"Airflow API error: {response.status_code} - {error_content}")
            return JSONResponse(content=error_content, status_code=response.status_code)
            
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout fetching logs for {dag_id}/{dag_run_id}/{task_id}: {e}")
        return JSONResponse(
            content={'error': 'Request timeout - Airflow may be slow or unavailable'}, 
            status_code=504
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get task instance logs for {dag_id}/{dag_run_id}/{task_id}: {e}")
        return JSONResponse(
            content={'error': f'Failed to fetch logs: {str(e)}'}, 
            status_code=500
        )
    except Exception as e:
        logger.error(f"Unexpected error getting task instance logs: {e}", exc_info=True)
        return JSONResponse(content={'error': str(e)}, status_code=500)

@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances')
async def task_instances(dag_id: str, dag_run_id: str, request: Request):
    """Get task instances for a DAG run"""
    try:
        session = get_airflow_session()
        # URL encode dag_run_id for Airflow API
        from urllib.parse import quote
        encoded_dag_run_id = quote(dag_run_id, safe='')
        url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{encoded_dag_run_id}/taskInstances"
        response = session.get(url, params=dict(request.query_params))
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to get task instances: {e}")
        return JSONResponse(content={'error': str(e)}, status_code=500)

@router.get('/health')
async def health():
    """Check Airflow API health"""
    try:
        session = get_airflow_session()
        url = f"{AIRFLOW_API_URL}/health"
        response = session.get(url, timeout=5)
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Airflow health check failed: {e}")
        return JSONResponse(content={'error': str(e), 'status': 'unavailable'}, status_code=503)

# Debug route to test route matching
@router.get('/debug/routes')
async def debug_routes():
    """Debug endpoint to list registered routes"""
    routes = []
    for route in router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                'path': route.path,
                'methods': list(route.methods) if route.methods else []
            })
    return JSONResponse(content={'routes': routes})

