"""Strategy schemas for API validation."""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class StrategyBase(BaseModel):
    """Base strategy schema."""
    name: str
    code: str
    workflow_id: Optional[int] = None
    param: Optional[Dict[str, Any]] = None
    active: Optional[bool] = True


class StrategyCreate(StrategyBase):
    """Schema for creating a strategy."""
    pass


class StrategyUpdate(BaseModel):
    """Schema for updating a strategy."""
    name: Optional[str] = None
    code: Optional[str] = None
    workflow_id: Optional[int] = None
    param: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class StrategyResponse(StrategyBase):
    """Schema for strategy response."""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
