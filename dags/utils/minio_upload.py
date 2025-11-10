"""
MinIO Upload Utility - Upload chart images to MinIO from Airflow DAGs
"""
import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    logger.warning("MinIO package not available. Chart uploads will be skipped.")

# MinIO configuration from environment
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
MINIO_BUCKET = os.getenv('MINIO_BUCKET_CHARTS', 'trading-charts')
MINIO_SECURE = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
MINIO_PUBLIC_ENDPOINT = os.getenv('MINIO_PUBLIC_ENDPOINT', 'localhost:9000')


def upload_chart_to_minio(
    file_path: str,
    symbol: str,
    timeframe: str,
    execution_id: Optional[str] = None
) -> Optional[str]:
    """
    Upload a chart image to MinIO and return the public URL.
    
    Args:
        file_path: Local path to the chart image file
        symbol: Stock symbol (e.g., 'TSLA', 'NVDA')
        timeframe: Chart timeframe (e.g., 'daily', 'weekly')
        execution_id: Workflow execution ID (optional)
    
    Returns:
        MinIO public URL or None if upload fails
    """
    if not MINIO_AVAILABLE:
        logger.warning("MinIO not available. Skipping chart upload.")
        return None
    
    try:
        # Initialize MinIO client
        client = Minio(
            MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE
        )
        
        # Ensure bucket exists
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
            logger.info(f"Created MinIO bucket: {MINIO_BUCKET}")
        
        # Read file
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            logger.error(f"Chart file not found: {file_path}")
            return None
        
        # Generate object name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        file_ext = file_path_obj.suffix or '.png'
        object_name = f"charts/{symbol}/{timeframe}/{timestamp}_{unique_id}{file_ext}"
        
        # Upload file
        with open(file_path, 'rb') as file_data:
            file_stat = os.stat(file_path)
            client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=object_name,
                data=file_data,
                length=file_stat.st_size,
                content_type='image/png' if file_ext == '.png' else 'image/jpeg'
            )
        
        # Generate public URL
        protocol = "https" if MINIO_SECURE else "http"
        public_url = f"{protocol}://{MINIO_PUBLIC_ENDPOINT}/{MINIO_BUCKET}/{object_name}"
        
        logger.info(f"Uploaded chart to MinIO: {object_name} -> {public_url}")
        return public_url
        
    except S3Error as e:
        logger.error(f"MinIO S3 error uploading chart: {e}")
        return None
    except Exception as e:
        logger.error(f"Error uploading chart to MinIO: {e}", exc_info=True)
        return None

