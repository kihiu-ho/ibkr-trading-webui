"""
FastAPI endpoints for Prompt Template management
"""
import logging
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from backend.core.database import get_db
from backend.models.prompt import PromptTemplate, PromptPerformance
from backend.models.trading_signal import TradingSignal
from backend.schemas.prompt import (
    PromptTemplateCreate,
    PromptTemplateUpdate,
    PromptTemplateResponse,
    PromptTemplateListResponse,
    PromptPerformanceResponse,
    PromptPerformanceQuery,
    PromptPerformanceSummary,
    PromptComparisonRequest,
    PromptComparisonResponse,
    PromptLeaderboardRequest,
    PromptLeaderboardResponse,
    TemplateValidationRequest,
    TemplateValidationResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
    SignalOutcomeUpdate,
)
from backend.services.prompt_renderer import get_prompt_renderer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


# CRUD Endpoints

@router.post("/", response_model=PromptTemplateResponse, status_code=201)
def create_prompt_template(
    template: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new prompt template."""
    try:
        # Validate template syntax
        renderer = get_prompt_renderer()
        is_valid, error = renderer.validate_template(template.prompt_text)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid template syntax: {error}")
        
        # Check if default template already exists
        if template.is_default:
            existing_default = db.query(PromptTemplate).filter(
                PromptTemplate.template_type == template.template_type,
                PromptTemplate.language == template.language,
                PromptTemplate.strategy_id == template.strategy_id,
                PromptTemplate.is_default == True
            ).first()
            
            if existing_default:
                # Unset existing default
                existing_default.is_default = False
                db.add(existing_default)
        
        # Create new template
        db_template = PromptTemplate(**template.model_dump())
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        
        logger.info(f"Created prompt template: {db_template.id} - {db_template.name}")
        return db_template
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating prompt template: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")


@router.get("/", response_model=PromptTemplateListResponse)
def list_prompt_templates(
    template_type: Optional[str] = Query(None, description="Filter by template type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    strategy_id: Optional[int] = Query(None, description="Filter by strategy ID (null for global)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_default: Optional[bool] = Query(None, description="Filter by default status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Page size"),
    db: Session = Depends(get_db)
):
    """List prompt templates with filters and pagination."""
    try:
        query = db.query(PromptTemplate)
        
        # Apply filters
        if template_type:
            query = query.filter(PromptTemplate.template_type == template_type)
        if language:
            query = query.filter(PromptTemplate.language == language)
        if strategy_id is not None:
            if strategy_id == 0:  # Special case: 0 means NULL (global)
                query = query.filter(PromptTemplate.strategy_id.is_(None))
            else:
                query = query.filter(PromptTemplate.strategy_id == strategy_id)
        if is_active is not None:
            query = query.filter(PromptTemplate.is_active == is_active)
        if is_default is not None:
            query = query.filter(PromptTemplate.is_default == is_default)
        if tags:
            # Filter by any tag in the list
            query = query.filter(PromptTemplate.tags.overlap(tags))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        templates = query.order_by(desc(PromptTemplate.created_at)).offset(offset).limit(page_size).all()
        
        return PromptTemplateListResponse(
            templates=templates,
            total=total,
            page=page,
            page_size=page_size
        )
    
    except Exception as e:
        logger.error(f"Error listing prompt templates: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing templates: {str(e)}")


@router.get("/{prompt_id}", response_model=PromptTemplateResponse)
def get_prompt_template(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific prompt template by ID."""
    template = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not template:
        raise HTTPException(status_code=404, detail=f"Prompt template {prompt_id} not found")
    return template


@router.put("/{prompt_id}", response_model=PromptTemplateResponse)
def update_prompt_template(
    prompt_id: int,
    template_update: PromptTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update a prompt template."""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
        if not template:
            raise HTTPException(status_code=404, detail=f"Prompt template {prompt_id} not found")
        
        # Validate template syntax if prompt_text is being updated
        if template_update.prompt_text:
            renderer = get_prompt_renderer()
            is_valid, error = renderer.validate_template(template_update.prompt_text)
            if not is_valid:
                raise HTTPException(status_code=400, detail=f"Invalid template syntax: {error}")
            
            # Increment version if prompt_text changes
            template.template_version += 1
        
        # Handle default template logic
        if template_update.is_default and template_update.is_default != template.is_default:
            # Unset other defaults
            existing_default = db.query(PromptTemplate).filter(
                PromptTemplate.template_type == (template_update.template_type or template.template_type),
                PromptTemplate.language == (template_update.language or template.language),
                PromptTemplate.strategy_id == (template_update.strategy_id if template_update.strategy_id is not None else template.strategy_id),
                PromptTemplate.is_default == True,
                PromptTemplate.id != prompt_id
            ).first()
            
            if existing_default:
                existing_default.is_default = False
                db.add(existing_default)
        
        # Update fields
        for field, value in template_update.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        
        db.commit()
        db.refresh(template)
        
        logger.info(f"Updated prompt template: {template.id}")
        return template
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating prompt template: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating template: {str(e)}")


@router.delete("/{prompt_id}", status_code=204)
def delete_prompt_template(
    prompt_id: int,
    db: Session = Depends(get_db)
):
    """Delete a prompt template."""
    try:
        template = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
        if not template:
            raise HTTPException(status_code=404, detail=f"Prompt template {prompt_id} not found")
        
        # Check if template is being used
        signals_count = db.query(TradingSignal).filter(TradingSignal.prompt_template_id == prompt_id).count()
        if signals_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete template: {signals_count} signals still reference it. Set is_active=false instead."
            )
        
        db.delete(template)
        db.commit()
        
        logger.info(f"Deleted prompt template: {prompt_id}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting prompt template: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")


# Strategy-specific endpoints

@router.get("/strategy/{strategy_id}", response_model=List[PromptTemplateResponse])
def get_strategy_prompts(
    strategy_id: int,
    include_global: bool = Query(True, description="Include global defaults"),
    db: Session = Depends(get_db)
):
    """Get prompts for a specific strategy, including global defaults."""
    try:
        query = db.query(PromptTemplate)
        
        if include_global:
            # Get both strategy-specific and global prompts
            query = query.filter(
                or_(
                    PromptTemplate.strategy_id == strategy_id,
                    PromptTemplate.strategy_id.is_(None)
                )
            )
        else:
            # Only strategy-specific
            query = query.filter(PromptTemplate.strategy_id == strategy_id)
        
        prompts = query.filter(PromptTemplate.is_active == True).order_by(
            PromptTemplate.strategy_id.desc(),  # Strategy-specific first
            PromptTemplate.is_default.desc(),
            PromptTemplate.created_at.desc()
        ).all()
        
        return prompts
    
    except Exception as e:
        logger.error(f"Error getting strategy prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting prompts: {str(e)}")


@router.post("/strategy/{strategy_id}", response_model=PromptTemplateResponse, status_code=201)
def create_strategy_prompt(
    strategy_id: int,
    template: PromptTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a prompt template for a specific strategy."""
    # Override strategy_id
    template.strategy_id = strategy_id
    return create_prompt_template(template, db)


# Performance endpoints

@router.get("/{prompt_id}/performance", response_model=List[PromptPerformanceResponse])
def get_prompt_performance(
    prompt_id: int,
    start_date: Optional[date] = Query(None, description="Start date for performance data"),
    end_date: Optional[date] = Query(None, description="End date for performance data"),
    strategy_id: Optional[int] = Query(None, description="Filter by strategy"),
    db: Session = Depends(get_db)
):
    """Get performance metrics for a prompt template."""
    try:
        query = db.query(PromptPerformance).filter(PromptPerformance.prompt_template_id == prompt_id)
        
        if start_date:
            query = query.filter(PromptPerformance.date >= start_date)
        if end_date:
            query = query.filter(PromptPerformance.date <= end_date)
        if strategy_id is not None:
            query = query.filter(PromptPerformance.strategy_id == strategy_id)
        
        performance = query.order_by(desc(PromptPerformance.date)).all()
        
        # Add computed properties
        for perf in performance:
            perf.win_rate = perf.win_rate
            perf.execution_rate = perf.execution_rate
        
        return performance
    
    except Exception as e:
        logger.error(f"Error getting prompt performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting performance: {str(e)}")


@router.post("/compare", response_model=PromptComparisonResponse)
def compare_prompts(
    request: PromptComparisonRequest,
    db: Session = Depends(get_db)
):
    """Compare performance of multiple prompt templates."""
    try:
        summaries = []
        
        for prompt_id in request.prompt_template_ids:
            # Get template
            template = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
            if not template:
                continue
            
            # Query performance
            query = db.query(PromptPerformance).filter(PromptPerformance.prompt_template_id == prompt_id)
            
            if request.strategy_id is not None:
                query = query.filter(PromptPerformance.strategy_id == request.strategy_id)
            if request.start_date:
                query = query.filter(PromptPerformance.date >= request.start_date)
            if request.end_date:
                query = query.filter(PromptPerformance.date <= request.end_date)
            
            perf_records = query.all()
            
            if not perf_records:
                continue
            
            # Aggregate stats
            total_signals = sum(p.signals_generated for p in perf_records)
            total_executed = sum(p.signals_executed for p in perf_records)
            total_wins = sum(p.win_count for p in perf_records)
            total_losses = sum(p.loss_count for p in perf_records)
            total_pl = sum(p.total_profit_loss for p in perf_records if p.total_profit_loss)
            
            # Calculate weighted average R-multiple
            r_multiples = [(p.avg_r_multiple, p.win_count + p.loss_count) for p in perf_records if p.avg_r_multiple]
            if r_multiples:
                weighted_r = sum(r * w for r, w in r_multiples) / sum(w for _, w in r_multiples)
            else:
                weighted_r = None
            
            # Find best/worst days
            best_day_perf = max(perf_records, key=lambda p: p.avg_r_multiple or 0, default=None)
            worst_day_perf = min(perf_records, key=lambda p: p.avg_r_multiple or 0, default=None)
            
            summary = PromptPerformanceSummary(
                prompt_template_id=prompt_id,
                prompt_name=template.name,
                total_signals=total_signals,
                total_executed=total_executed,
                total_wins=total_wins,
                total_losses=total_losses,
                overall_win_rate=total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0.0,
                overall_r_multiple=weighted_r,
                total_profit_loss=total_pl if total_pl else None,
                best_day=best_day_perf.date if best_day_perf else None,
                worst_day=worst_day_perf.date if worst_day_perf else None,
                days_active=len(perf_records)
            )
            summaries.append(summary)
        
        # Sort by requested metric
        metric_key_map = {
            'avg_r_multiple': lambda s: s.overall_r_multiple or 0,
            'win_rate': lambda s: s.overall_win_rate,
            'total_profit_loss': lambda s: s.total_profit_loss or 0,
        }
        sort_key = metric_key_map.get(request.metric, metric_key_map['avg_r_multiple'])
        summaries.sort(key=sort_key, reverse=True)
        
        # Determine best
        best = summaries[0] if summaries else None
        
        return PromptComparisonResponse(
            prompts=summaries,
            metric=request.metric,
            best_prompt_id=best.prompt_template_id if best else None,
            best_prompt_name=best.prompt_name if best else None
        )
    
    except Exception as e:
        logger.error(f"Error comparing prompts: {e}")
        raise HTTPException(status_code=500, detail=f"Error comparing prompts: {str(e)}")


@router.post("/leaderboard", response_model=PromptLeaderboardResponse)
def get_prompt_leaderboard(
    request: PromptLeaderboardRequest,
    db: Session = Depends(get_db)
):
    """Get leaderboard of best-performing prompts."""
    try:
        # Get all active prompts
        query = db.query(PromptTemplate).filter(PromptTemplate.is_active == True)
        
        if request.template_type:
            query = query.filter(PromptTemplate.template_type == request.template_type)
        
        templates = query.all()
        
        summaries = []
        
        for template in templates:
            # Query performance
            perf_query = db.query(PromptPerformance).filter(PromptPerformance.prompt_template_id == template.id)
            
            if request.strategy_id is not None:
                perf_query = perf_query.filter(PromptPerformance.strategy_id == request.strategy_id)
            if request.start_date:
                perf_query = perf_query.filter(PromptPerformance.date >= request.start_date)
            if request.end_date:
                perf_query = perf_query.filter(PromptPerformance.date <= request.end_date)
            
            perf_records = perf_query.all()
            
            if not perf_records:
                continue
            
            # Aggregate
            total_signals = sum(p.signals_generated for p in perf_records)
            total_executed = sum(p.signals_executed for p in perf_records)
            total_wins = sum(p.win_count for p in perf_records)
            total_losses = sum(p.loss_count for p in perf_records)
            total_pl = sum(p.total_profit_loss for p in perf_records if p.total_profit_loss)
            
            r_multiples = [(p.avg_r_multiple, p.win_count + p.loss_count) for p in perf_records if p.avg_r_multiple]
            weighted_r = sum(r * w for r, w in r_multiples) / sum(w for _, w in r_multiples) if r_multiples else None
            
            best_day_perf = max(perf_records, key=lambda p: p.avg_r_multiple or 0, default=None)
            worst_day_perf = min(perf_records, key=lambda p: p.avg_r_multiple or 0, default=None)
            
            summary = PromptPerformanceSummary(
                prompt_template_id=template.id,
                prompt_name=template.name,
                total_signals=total_signals,
                total_executed=total_executed,
                total_wins=total_wins,
                total_losses=total_losses,
                overall_win_rate=total_wins / (total_wins + total_losses) if (total_wins + total_losses) > 0 else 0.0,
                overall_r_multiple=weighted_r,
                total_profit_loss=total_pl if total_pl else None,
                best_day=best_day_perf.date if best_day_perf else None,
                worst_day=worst_day_perf.date if worst_day_perf else None,
                days_active=len(perf_records)
            )
            summaries.append(summary)
        
        # Sort by metric
        metric_key_map = {
            'avg_r_multiple': lambda s: s.overall_r_multiple or 0,
            'win_rate': lambda s: s.overall_win_rate,
            'total_profit_loss': lambda s: s.total_profit_loss or 0,
        }
        sort_key = metric_key_map.get(request.metric, metric_key_map['avg_r_multiple'])
        summaries.sort(key=sort_key, reverse=True)
        
        # Limit results
        rankings = summaries[:request.limit]
        
        return PromptLeaderboardResponse(
            rankings=rankings,
            metric=request.metric,
            total_prompts=len(summaries)
        )
    
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting leaderboard: {str(e)}")


# Utility endpoints

@router.post("/validate", response_model=TemplateValidationResponse)
def validate_template(request: TemplateValidationRequest):
    """Validate a Jinja2 template for syntax errors."""
    try:
        renderer = get_prompt_renderer()
        is_valid, error = renderer.validate_template(request.template_text)
        
        return TemplateValidationResponse(
            is_valid=is_valid,
            error_message=error
        )
    except Exception as e:
        logger.error(f"Error validating template: {e}")
        raise HTTPException(status_code=500, detail=f"Error validating template: {str(e)}")


@router.post("/render", response_model=TemplateRenderResponse)
def render_template_preview(request: TemplateRenderRequest):
    """Render a template with provided context (for preview)."""
    try:
        renderer = get_prompt_renderer()
        rendered = renderer.render(request.template_text, request.context, strict=request.strict)
        
        return TemplateRenderResponse(
            rendered_text=rendered,
            warnings=None
        )
    except ValueError as e:
        # Template errors
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        raise HTTPException(status_code=500, detail=f"Error rendering template: {str(e)}")


# Signal outcome tracking (for performance aggregation)

@router.put("/signals/{signal_id}/outcome", response_model=dict)
def update_signal_outcome(
    signal_id: int,
    outcome: SignalOutcomeUpdate,
    db: Session = Depends(get_db)
):
    """Update trading signal outcome for performance tracking."""
    try:
        signal = db.query(TradingSignal).filter(TradingSignal.id == signal_id).first()
        if not signal:
            raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
        
        # Update outcome fields
        signal.outcome = outcome.outcome
        signal.exit_price = outcome.exit_price
        signal.exit_time = outcome.exit_time
        signal.actual_r_multiple = outcome.actual_r_multiple
        signal.profit_loss = outcome.profit_loss
        
        db.commit()
        
        logger.info(f"Updated signal outcome: {signal_id} -> {outcome.outcome}")
        return {"success": True, "signal_id": signal_id, "outcome": outcome.outcome}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating signal outcome: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating outcome: {str(e)}")

