"""Workflow management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.core.database import get_db
from backend.models import Workflow

router = APIRouter()


@router.get("")
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all workflows."""
    workflows = db.query(Workflow).offset(skip).limit(limit).all()
    return workflows


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    """Get workflow by ID."""
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

