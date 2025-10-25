"""Logging and monitoring API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import Optional, List
from datetime import datetime, timezone, timedelta
from backend.core.database import get_db
from backend.models.workflow_log import WorkflowLog
from backend.models.workflow import WorkflowExecution
import json
import csv
import io
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def query_logs(
    workflow_execution_id: Optional[int] = None,
    step_type: Optional[str] = None,
    success: Optional[bool] = None,
    code: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 1000,
    db: Session = Depends(get_db)
):
    """Query logs with comprehensive filtering options."""
    query = db.query(WorkflowLog)
    
    # Apply filters
    if workflow_execution_id:
        query = query.filter(WorkflowLog.workflow_execution_id == workflow_execution_id)
    
    if step_type:
        query = query.filter(WorkflowLog.step_type == step_type)
    
    if success is not None:
        query = query.filter(WorkflowLog.success == success)
    
    if code:
        query = query.filter(WorkflowLog.code == code)
    
    if date_from:
        query = query.filter(WorkflowLog.created_at >= date_from)
    
    if date_to:
        query = query.filter(WorkflowLog.created_at <= date_to)
    
    # Search in step_name, error_message, and JSON data
    if search:
        search_filter = or_(
            WorkflowLog.step_name.ilike(f"%{search}%"),
            WorkflowLog.error_message.ilike(f"%{search}%"),
            WorkflowLog.input_data.cast(db.String).ilike(f"%{search}%"),
            WorkflowLog.output_data.cast(db.String).ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Order by most recent first
    query = query.order_by(desc(WorkflowLog.created_at))
    
    # Get total count before pagination
    total_count = query.count()
    
    # Apply pagination
    logs = query.offset(skip).limit(limit).all()
    
    return {
        "total": total_count,
        "skip": skip,
        "limit": limit,
        "logs": [{
            "id": log.id,
            "workflow_execution_id": log.workflow_execution_id,
            "step_name": log.step_name,
            "step_type": log.step_type,
            "code": log.code,
            "conid": log.conid,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "success": log.success,
            "error_message": log.error_message,
            "duration_ms": log.duration_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs]
    }


@router.get("/export")
async def export_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    workflow_execution_id: Optional[int] = None,
    step_type: Optional[str] = None,
    success: Optional[bool] = None,
    code: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Export logs in JSON or CSV format."""
    query = db.query(WorkflowLog)
    
    # Apply same filters as query endpoint
    if workflow_execution_id:
        query = query.filter(WorkflowLog.workflow_execution_id == workflow_execution_id)
    
    if step_type:
        query = query.filter(WorkflowLog.step_type == step_type)
    
    if success is not None:
        query = query.filter(WorkflowLog.success == success)
    
    if code:
        query = query.filter(WorkflowLog.code == code)
    
    if date_from:
        query = query.filter(WorkflowLog.created_at >= date_from)
    
    if date_to:
        query = query.filter(WorkflowLog.created_at <= date_to)
    
    query = query.order_by(desc(WorkflowLog.created_at))
    logs = query.all()
    
    # Generate filename
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"workflow_logs_{timestamp}.{format}"
    
    if format == "json":
        # Export as JSON
        logs_data = [{
            "id": log.id,
            "workflow_execution_id": log.workflow_execution_id,
            "step_name": log.step_name,
            "step_type": log.step_type,
            "code": log.code,
            "conid": log.conid,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "success": log.success,
            "error_message": log.error_message,
            "duration_ms": log.duration_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in logs]
        
        json_str = json.dumps(logs_data, indent=2)
        
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif format == "csv":
        # Export as CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "id", "workflow_execution_id", "step_name", "step_type", "code", "conid",
            "success", "error_message", "duration_ms", "created_at",
            "input_data", "output_data"
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.id,
                log.workflow_execution_id,
                log.step_name,
                log.step_type,
                log.code,
                log.conid,
                log.success,
                log.error_message or "",
                log.duration_ms,
                log.created_at.isoformat() if log.created_at else "",
                json.dumps(log.input_data) if log.input_data else "",
                json.dumps(log.output_data) if log.output_data else ""
            ])
        
        csv_str = output.getvalue()
        
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )


@router.get("/statistics")
async def get_log_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    """Get log statistics for monitoring dashboard."""
    query = db.query(WorkflowLog)
    
    # Default to last 30 days if no date range specified
    if not date_from:
        date_from = datetime.now(timezone.utc) - timedelta(days=30)
    
    if not date_to:
        date_to = datetime.now(timezone.utc)
    
    query = query.filter(
        WorkflowLog.created_at >= date_from,
        WorkflowLog.created_at <= date_to
    )
    
    # Total logs
    total_logs = query.count()
    
    # Failed logs
    failed_logs = query.filter(WorkflowLog.success == False).count()
    
    # Success rate
    success_rate = ((total_logs - failed_logs) / total_logs * 100) if total_logs > 0 else 0
    
    # Logs by step type
    step_type_counts = db.query(
        WorkflowLog.step_type,
        func.count(WorkflowLog.id)
    ).filter(
        WorkflowLog.created_at >= date_from,
        WorkflowLog.created_at <= date_to
    ).group_by(WorkflowLog.step_type).all()
    
    # Average duration by step type
    avg_duration_by_type = db.query(
        WorkflowLog.step_type,
        func.avg(WorkflowLog.duration_ms)
    ).filter(
        WorkflowLog.created_at >= date_from,
        WorkflowLog.created_at <= date_to,
        WorkflowLog.duration_ms.isnot(None)
    ).group_by(WorkflowLog.step_type).all()
    
    # Logs per day
    logs_per_day = db.query(
        func.date(WorkflowLog.created_at).label('date'),
        func.count(WorkflowLog.id)
    ).filter(
        WorkflowLog.created_at >= date_from,
        WorkflowLog.created_at <= date_to
    ).group_by(func.date(WorkflowLog.created_at)).order_by(func.date(WorkflowLog.created_at)).all()
    
    return {
        "period": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat()
        },
        "total_logs": total_logs,
        "failed_logs": failed_logs,
        "success_rate": round(success_rate, 2),
        "by_step_type": {
            step_type: count for step_type, count in step_type_counts
        },
        "avg_duration_by_type": {
            step_type: round(avg_duration, 2) if avg_duration else 0
            for step_type, avg_duration in avg_duration_by_type
        },
        "logs_per_day": [
            {"date": date.isoformat(), "count": count}
            for date, count in logs_per_day
        ]
    }


@router.get("/{log_id}")
async def get_log_detail(
    log_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed information about a single log entry."""
    log = db.query(WorkflowLog).filter(WorkflowLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    # Get execution details
    execution = db.query(WorkflowExecution).filter(
        WorkflowExecution.id == log.workflow_execution_id
    ).first()
    
    # Get previous and next logs in the same execution
    prev_log = db.query(WorkflowLog).filter(
        WorkflowLog.workflow_execution_id == log.workflow_execution_id,
        WorkflowLog.created_at < log.created_at
    ).order_by(desc(WorkflowLog.created_at)).first()
    
    next_log = db.query(WorkflowLog).filter(
        WorkflowLog.workflow_execution_id == log.workflow_execution_id,
        WorkflowLog.created_at > log.created_at
    ).order_by(WorkflowLog.created_at).first()
    
    return {
        "id": log.id,
        "workflow_execution_id": log.workflow_execution_id,
        "execution_status": execution.status if execution else None,
        "step_name": log.step_name,
        "step_type": log.step_type,
        "code": log.code,
        "conid": log.conid,
        "input_data": log.input_data,
        "output_data": log.output_data,
        "success": log.success,
        "error_message": log.error_message,
        "duration_ms": log.duration_ms,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "navigation": {
            "previous_log_id": prev_log.id if prev_log else None,
            "next_log_id": next_log.id if next_log else None
        }
    }

