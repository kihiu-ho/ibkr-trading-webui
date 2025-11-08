"""
Airflow API Proxy Routes (FastAPI)
Proxy requests to Airflow REST API
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
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
            body = await request.json()
            response = session.post(url, json=body)
        else:
            response = session.get(url, params=dict(request.query_params))
            
        return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        logger.error(f"Failed to handle DAG runs for {dag_id}: {e}")
        return JSONResponse(content={'error': str(e)}, status_code=500)

@router.get('/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances')
async def task_instances(dag_id: str, dag_run_id: str, request: Request):
    """Get task instances for a DAG run"""
    try:
        session = get_airflow_session()
        url = f"{AIRFLOW_API_URL}/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances"
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

