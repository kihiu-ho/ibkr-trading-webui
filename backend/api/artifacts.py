"""
Artifacts API - OpenSpec 2 Compliant
Store and retrieve ML/LLM artifacts (inputs/outputs, charts, signals)
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.core.database import get_db
from backend.models.artifact import Artifact
from typing import List, Dict, Any, Optional
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def get_artifacts(
    db: Session = Depends(get_db),
    type: Optional[str] = None,
    symbol: Optional[str] = None,
    execution_id: Optional[str] = None,
    group_by: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Get all artifacts with optional filtering and grouping.
    
    Args:
        type: Filter by artifact type (llm, chart, signal, order, trade, portfolio)
        symbol: Filter by trading symbol
        execution_id: Filter by execution_id
        group_by: Group artifacts by 'execution_id' or None for flat list
        limit: Maximum number of artifacts to return
    """
    try:
        query = db.query(Artifact)
        
        if type:
            # Support filtering by artifact_type in signal_data for order/trade/portfolio
            if type in ['order', 'trade', 'portfolio']:
                # These are stored as 'signal' type with artifact_type in signal_data
                query = query.filter(Artifact.type == 'signal')
                # Note: Further filtering by signal_data would require JSON query
            else:
                query = query.filter(Artifact.type == type)
        if symbol:
            query = query.filter(Artifact.symbol == symbol)
        if execution_id:
            query = query.filter(Artifact.execution_id == execution_id)
        
        artifacts = query.order_by(desc(Artifact.created_at)).limit(limit).all()
        artifacts_dict = [a.to_dict() for a in artifacts]
        
        # Filter by artifact_type in signal_data if needed
        if type in ['order', 'trade', 'portfolio']:
            artifacts_dict = [
                a for a in artifacts_dict
                if a.get('signal_data', {}).get('artifact_type') == type
            ]
        
        # Group by execution_id if requested
        if group_by == 'execution_id':
            logger.debug(f"Grouping artifacts by execution_id. Found {len(artifacts_dict)} artifacts")
            grouped = {}
            for artifact in artifacts_dict:
                exec_id = artifact.get('execution_id') or 'ungrouped'
                if exec_id not in grouped:
                    grouped[exec_id] = []
                grouped[exec_id].append(artifact)
            
            # Sort groups by most recent first
            sorted_groups = {}
            if grouped:
                for exec_id in sorted(grouped.keys(), key=lambda x: (
                    grouped[x][0].get('created_at', '') if grouped[x] else ''
                ), reverse=True):
                    sorted_groups[exec_id] = grouped[exec_id]
            
            logger.debug(f"Returning grouped structure with {len(sorted_groups)} groups")
            return {
                "artifacts": artifacts_dict,  # Still return flat list for compatibility
                "grouped": sorted_groups,  # Add grouped view (empty dict if no artifacts)
                "total": len(artifacts_dict),
                "group_count": len(sorted_groups)
            }
        
        return {
            "artifacts": artifacts_dict,
            "total": len(artifacts_dict)
        }
    except Exception as e:
        logger.error(f"Error fetching artifacts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{artifact_id}")
async def get_artifact(
    artifact_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get a single artifact by ID."""
    try:
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        return artifact.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_artifact(
    artifact_data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Create a new artifact.
    
    Expected payload:
    {
        "name": "LLM Analysis for TSLA",
        "type": "llm|chart|signal",
        "symbol": "TSLA",
        "prompt": "Analyze TSLA...",
        "response": "Based on analysis...",
        "run_id": "mlflow_run_id",
        ...
    }
    """
    try:
        # Validate required fields
        if 'name' not in artifact_data or 'type' not in artifact_data:
            raise HTTPException(status_code=400, detail="name and type are required")
        
        if artifact_data['type'] not in ['llm', 'chart', 'signal']:
            raise HTTPException(status_code=400, detail="type must be llm, chart, or signal")
        
        # Calculate lengths for LLM artifacts
        if artifact_data['type'] == 'llm':
            if 'prompt' in artifact_data:
                artifact_data['prompt_length'] = len(artifact_data['prompt'])
            if 'response' in artifact_data:
                artifact_data['response_length'] = len(artifact_data['response'])
        
        # Handle metadata field rename (metadata -> artifact_metadata)
        if 'metadata' in artifact_data:
            artifact_data['artifact_metadata'] = artifact_data.pop('metadata')
        
        # Create artifact
        artifact = Artifact(**artifact_data)
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        logger.info(f"Created artifact: {artifact.id} ({artifact.type})")
        
        return artifact.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating artifact: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{artifact_id}/market-data")
async def get_artifact_market_data(
    artifact_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get market data for a chart artifact.
    Returns OHLCV data for the artifact's symbol.
    """
    try:
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        if artifact.type != 'chart':
            raise HTTPException(status_code=400, detail="Market data is only available for chart artifacts")
        
        if not artifact.symbol:
            raise HTTPException(status_code=400, detail="Artifact does not have a symbol")
        
        # Query market_data table for the symbol
        # market_data table stores data in JSONB format with 'data' key containing array of bars
        # Each bar has: c (close), h (high), l (low), o (open), t (timestamp), v (volume)
        from sqlalchemy import text
        from datetime import datetime
        
        query = text("""
            SELECT 
                md.data->'data' as bars_data
            FROM market_data md
            JOIN codes c ON md.conid = c.conid
            WHERE c.symbol = :symbol
            ORDER BY md.created_at DESC
            LIMIT 1
        """)
        
        result = db.execute(query, {"symbol": artifact.symbol})
        row = result.fetchone()
        
        # Convert to list of dicts
        market_data = []
        if row and row.bars_data:
            # bars_data is a JSONB array of bars
            bars = row.bars_data if isinstance(row.bars_data, list) else []
            
            # Take only the requested limit (most recent first)
            bars = bars[-limit:] if len(bars) > limit else bars
            bars.reverse()  # Show most recent first
            
            for bar in bars:
                if isinstance(bar, dict):
                    # Convert timestamp (milliseconds) to date string
                    timestamp_ms = bar.get("t") or bar.get("timestamp")
                    if timestamp_ms:
                        try:
                            date_str = datetime.fromtimestamp(timestamp_ms / 1000).isoformat()
                        except (ValueError, TypeError):
                            date_str = str(timestamp_ms)
                    else:
                        date_str = None
                    
                    market_data.append({
                        "date": date_str,
                        "open": float(bar.get("o", 0)) if bar.get("o") else None,
                        "high": float(bar.get("h", 0)) if bar.get("h") else None,
                        "low": float(bar.get("l", 0)) if bar.get("l") else None,
                        "close": float(bar.get("c", 0)) if bar.get("c") else None,
                        "volume": int(bar.get("v", 0)) if bar.get("v") else None,
                    })
        
        return {
            "symbol": artifact.symbol,
            "count": len(market_data),
            "data": market_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data for artifact {artifact_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{artifact_id}/download")
async def download_artifact(
    artifact_id: int,
    db: Session = Depends(get_db)
):
    """Download artifact as JSON file."""
    try:
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Convert to JSON
        artifact_json = json.dumps(artifact.to_dict(), indent=2)
        
        return Response(
            content=artifact_json,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=artifact-{artifact_id}.json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading artifact {artifact_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{artifact_id}")
async def update_artifact(
    artifact_id: int,
    artifact_updates: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update an artifact (partial update)."""
    try:
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        # Handle metadata field rename
        if 'metadata' in artifact_updates:
            artifact_updates['artifact_metadata'] = artifact_updates.pop('metadata')
        
        # Update fields
        for key, value in artifact_updates.items():
            if hasattr(artifact, key):
                setattr(artifact, key, value)
        
        db.commit()
        db.refresh(artifact)
        
        logger.info(f"Updated artifact: {artifact_id}")
        
        return artifact.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating artifact {artifact_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{artifact_id}")
async def delete_artifact(
    artifact_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, str]:
    """Delete an artifact."""
    try:
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        
        if not artifact:
            raise HTTPException(status_code=404, detail="Artifact not found")
        
        db.delete(artifact)
        db.commit()
        
        logger.info(f"Deleted artifact: {artifact_id}")
        
        return {"message": "Artifact deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting artifact {artifact_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/summary")
async def get_artifact_stats(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get artifact statistics."""
    try:
        total = db.query(Artifact).count()
        llm_count = db.query(Artifact).filter(Artifact.type == 'llm').count()
        chart_count = db.query(Artifact).filter(Artifact.type == 'chart').count()
        signal_count = db.query(Artifact).filter(Artifact.type == 'signal').count()
        
        return {
            "total": total,
            "by_type": {
                "llm": llm_count,
                "chart": chart_count,
                "signal": signal_count
            }
        }
    except Exception as e:
        logger.error(f"Error fetching artifact stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

