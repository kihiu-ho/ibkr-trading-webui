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


@router.get("/strategies/new", response_class=HTMLResponse)
async def strategies_new(request: Request):
    """Create new strategy page."""
    return templates.TemplateResponse("strategies.html", {"request": request})


@router.get("/workflows", response_class=HTMLResponse)
async def workflows_list(request: Request):
    """Workflows execution list page with ability to trigger new workflows."""
    return templates.TemplateResponse("workflows/list.html", {"request": request})


@router.get("/workflows/executions/{execution_id}", response_class=HTMLResponse)
async def workflow_execution(request: Request, execution_id: int):
    """Workflow execution detail page with real-time monitoring."""
    return templates.TemplateResponse(
        "workflows/execution.html", 
        {
            "request": request,
            "execution_id": execution_id
        }
    )


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


@router.get("/symbols", response_class=HTMLResponse)
async def symbols(request: Request):
    """Symbol lookup and management page."""
    return templates.TemplateResponse("symbols.html", {"request": request})


@router.get("/ibkr/login", response_class=HTMLResponse)
async def ibkr_login(request: Request):
    """IBKR Gateway authentication page."""
    return templates.TemplateResponse("ibkr_login.html", {"request": request})


@router.get("/indicators", response_class=HTMLResponse)
async def indicators(request: Request):
    """Indicator management page."""
    return templates.TemplateResponse("indicators.html", {"request": request})


@router.get("/charts", response_class=HTMLResponse)
async def charts(request: Request):
    """Technical analysis charts gallery page."""
    return templates.TemplateResponse("charts.html", {"request": request})


@router.get("/signals", response_class=HTMLResponse)
async def signals(request: Request):
    """LLM-based trading signals page."""
    return templates.TemplateResponse("signals.html", {"request": request})


@router.get("/prompts", response_class=HTMLResponse)
async def prompts(request: Request):
    """Prompt template manager page with Monaco Editor."""
    return templates.TemplateResponse("prompts.html", {"request": request})


@router.get("/orders", response_class=HTMLResponse)
async def orders(request: Request):
    """Orders management page."""
    return templates.TemplateResponse("orders.html", {"request": request})


@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio(request: Request):
    """Portfolio and positions page."""
    return templates.TemplateResponse("portfolio.html", {"request": request})

