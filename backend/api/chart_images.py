"""
Chart Image Proxy API - Serve chart images from MinIO or local paths
"""
from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
import os
import requests
from pathlib import Path
import logging
from backend.core.database import get_db
from backend.models.artifact import Artifact

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{artifact_id}/image")
async def get_chart_image(artifact_id: int, db: Session = Depends(get_db)):
    """
    Get chart image for an artifact.
    If image_path is a MinIO URL, proxy the request.
    If image_path is a local path, serve the file.
    """
    try:
        # Get artifact from database
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        if artifact.type != 'chart':
            raise HTTPException(status_code=400, detail="Artifact is not a chart")
        
        if not artifact.image_path:
            raise HTTPException(status_code=404, detail="Chart image path not found")
        
        # Check for MinIO URL in chart_data first (even if image_path is local)
        minio_url = None
        if artifact.chart_data and isinstance(artifact.chart_data, dict):
            minio_url = artifact.chart_data.get('minio_url')
        
        # Use MinIO URL from chart_data if available, otherwise check image_path
        image_url = minio_url if minio_url else artifact.image_path
        
        # Check if it's a MinIO URL
        if image_url and image_url.startswith('http'):
            # Proxy request to MinIO
            # Replace localhost:9000 with minio:9000 for internal access
            minio_url = image_url.replace('localhost:9000', 'minio:9000')
            try:
                logger.info(f"Fetching chart from MinIO: {minio_url} (original: {image_url})")
                response = requests.get(minio_url, stream=True, timeout=10)
                response.raise_for_status()
                
                return StreamingResponse(
                    response.iter_content(chunk_size=8192),
                    media_type=response.headers.get('content-type', 'image/png'),
                    headers={
                        'Content-Disposition': f'inline; filename="chart-{artifact_id}.png"'
                    }
                )
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to fetch chart from MinIO: {e}")
                raise HTTPException(status_code=502, detail=f"Failed to fetch chart from MinIO: {str(e)}")
        else:
            # Local file path - try to find file in common locations
            file_path = Path(artifact.image_path)
            
            # Try to find file in common locations
            # First check shared volume (primary location)
            shared_volume_path = Path('/app/charts')
            possible_paths = [
                shared_volume_path / file_path.name,  # Shared volume (primary)
                shared_volume_path / file_path,  # Shared volume with full path
            ]
            
            # Then check original path and other common locations
            possible_paths.extend([
                file_path,  # Original path
                Path('/opt/airflow') / file_path,  # Airflow container path
                Path('/opt/airflow') / file_path.name,  # Just filename in Airflow
                Path('/tmp') / file_path.name,  # Just filename in /tmp
            ])
            
            # If path is absolute, also try relative to common directories
            if file_path.is_absolute():
                possible_paths.extend([
                    Path('/opt/airflow/dags') / file_path.name,
                    Path('/opt/airflow/logs') / file_path.name,
                ])
            
            found_path = None
            for path in possible_paths:
                if path.exists() and path.is_file():
                    found_path = path
                    logger.info(f"Found chart file at: {found_path}")
                    break
            
            # If exact file not found, try to find by filename pattern (for old artifacts)
            if not found_path and artifact.symbol and artifact.chart_type:
                try:
                    # Extract symbol and timeframe from filename or use artifact metadata
                    symbol = artifact.symbol
                    timeframe = artifact.chart_type  # e.g., 'daily', 'weekly'
                    
                    # Map chart_type to timeframe code: 'daily' -> '1D', 'weekly' -> '1W'
                    timeframe_map = {'daily': '1D', 'weekly': '1W', 'monthly': '1M'}
                    timeframe_code = timeframe_map.get(timeframe.lower(), timeframe[0].upper() if timeframe else '')
                    
                    # Search for files matching pattern: {symbol}_{timeframe_code}_*.png
                    pattern = f"{symbol}_{timeframe_code}*.png" if timeframe_code else f"{symbol}_*.png"
                    matching_files = list(shared_volume_path.glob(pattern))
                    
                    if matching_files:
                        # Use the most recent file
                        found_path = max(matching_files, key=lambda p: p.stat().st_mtime)
                        logger.info(f"Found chart file by pattern at: {found_path}")
                except Exception as e:
                    logger.debug(f"Error searching for file by pattern: {e}")
            
            if not found_path:
                logger.warning(f"Chart file not found in any location. Tried: {possible_paths}")
                # Return a helpful error message
                error_detail = (
                    f"Chart file not found: {artifact.image_path}. "
                    f"This may be an old artifact where the file was stored in /tmp/ and has been deleted. "
                    f"New artifacts store charts in /app/charts and upload to MinIO."
                )
                raise HTTPException(status_code=404, detail=error_detail)
            
            return FileResponse(
                str(found_path),
                media_type='image/png',
                filename=f"chart-{artifact_id}.png"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error serving chart image for artifact {artifact_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

