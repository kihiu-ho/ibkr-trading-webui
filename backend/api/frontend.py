"""Frontend template routes."""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="frontend/templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Redirect to dashboard."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/strategies", response_class=HTMLResponse)
async def strategies(request: Request):
    """Strategies management page."""
    return templates.TemplateResponse("strategies.html", {"request": request})


@router.get("/workflows", response_class=HTMLResponse)
async def workflows(request: Request):
    """Workflows management page."""
    return templates.TemplateResponse("workflows.html", {"request": request})


@router.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    """Orders page."""
    return templates.TemplateResponse("orders.html", {"request": request})


@router.get("/positions", response_class=HTMLResponse)
async def positions(request: Request):
    """Portfolio positions page."""
    return templates.TemplateResponse("positions.html", {"request": request})


@router.get("/analysis", response_class=HTMLResponse)
async def analysis(request: Request):
    """Analysis page."""
    return templates.TemplateResponse("analysis.html", {"request": request})


@router.get("/tasks", response_class=HTMLResponse)
async def tasks(request: Request):
    """Task queue page."""
    return templates.TemplateResponse("tasks.html", {"request": request})


@router.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    """Settings page."""
    return templates.TemplateResponse("settings.html", {"request": request})

