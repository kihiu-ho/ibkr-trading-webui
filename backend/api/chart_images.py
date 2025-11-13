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
from io import BytesIO
from backend.core.database import get_db
from backend.models.artifact import Artifact
from backend.config.settings import settings

logger = logging.getLogger(__name__)

# MinIO client setup
try:
    from minio import Minio
    MINIO_AVAILABLE = True
    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_SECURE
    )
except ImportError:
    MINIO_AVAILABLE = False
    minio_client = None
    logger.warning("MinIO package not available")

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
            # Extract bucket and object name from MinIO URL
            # Format: http://localhost:9000/bucket-name/path/to/object.jpg
            try:
                url_parts = image_url.replace('http://', '').replace('https://', '').split('/', 2)
                if len(url_parts) >= 3:
                    bucket_name = url_parts[1]
                    object_name = url_parts[2]
                    
                    logger.info(f"Fetching chart from MinIO: bucket={bucket_name}, object={object_name}")
                    
                    if MINIO_AVAILABLE and minio_client:
                        # Use MinIO client with authentication
                        response = minio_client.get_object(bucket_name, object_name)
                        image_data = response.read()
                        response.close()
                        response.release_conn()
                        
                        # Determine content type from file extension
                        content_type = 'image/jpeg' if object_name.lower().endswith(('.jpg', '.jpeg')) else 'image/png'
                        
                        return Response(
                            content=image_data,
                            media_type=content_type,
                            headers={
                                'Content-Disposition': f'inline; filename="chart-{artifact_id}.{object_name.split(".")[-1]}"',
                                'Cache-Control': 'public, max-age=3600'
                            }
                        )
                    else:
                        logger.error("MinIO client not available")
                        raise HTTPException(status_code=503, detail="MinIO client not available")
                else:
                    logger.error(f"Invalid MinIO URL format: {image_url}")
                    raise HTTPException(status_code=400, detail="Invalid MinIO URL format")
            except Exception as e:
                logger.error(f"Failed to fetch chart from MinIO: {e}")
                # Fall back to trying local file
                logger.info("Falling back to local file lookup")
        
        # Local file path - try to find file in common locations
        file_path = Path(artifact.image_path) if artifact.image_path else None
        
        if not file_path:
            raise HTTPException(status_code=404, detail="No image path available")
        
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

