"""IBKR Gateway authentication endpoints."""
from fastapi import APIRouter, HTTPException
from backend.services.ibkr_service import IBKRService
from backend.config.settings import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def get_auth_status():
    """
    Get IBKR Gateway authentication status.
    
    Returns connection status, authenticated account, and server info.
    """
    try:
        ibkr = IBKRService()
        
        # Check auth status
        try:
            auth_response = await ibkr.check_auth_status()
            authenticated = auth_response.get('authenticated', False)
        except Exception:
            authenticated = False
        
        # Get accounts if authenticated
        account_id = None
        accounts = []
        if authenticated:
            try:
                accounts_list = await ibkr.get_accounts()
                if accounts_list:
                    accounts = accounts_list
                    account_id = settings.IBKR_ACCOUNT_ID or (accounts[0] if accounts else None)
            except Exception as e:
                logger.warning(f"Failed to fetch accounts: {e}")
        
        # Get server status via tickle
        server_online = False
        server_error = None
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
                tickle_response = await client.get(f"{settings.IBKR_API_BASE_URL}/v1/api/tickle")
                server_online = tickle_response.status_code == 200
                if server_online:
                    tickle_data = tickle_response.json()
                    # Check if authenticated from tickle response
                    if tickle_data.get('iserver', {}).get('authStatus', {}).get('authenticated'):
                        authenticated = True
        except httpx.ConnectError:
            server_error = "Cannot connect to IBKR Gateway. Is it running?"
        except httpx.TimeoutException:
            server_error = "Connection to IBKR Gateway timed out"
        except Exception as e:
            server_error = f"Gateway connection error: {str(e)}"
            logger.warning(f"Gateway status check failed: {e}")
        
        result = {
            "authenticated": authenticated,
            "account_id": account_id,
            "accounts": accounts,
            "server_online": server_online,
            "gateway_url": settings.IBKR_API_BASE_URL
        }
        
        if server_error:
            result["server_error"] = server_error
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get auth status: {str(e)}")
        return {
            "authenticated": False,
            "account_id": None,
            "accounts": [],
            "server_online": False,
            "gateway_url": settings.IBKR_API_BASE_URL,
            "error": str(e),
            "server_error": "Failed to check gateway status"
        }


@router.post("/login")
async def initiate_login():
    """
    Initiate IBKR Gateway authentication.
    
    This will trigger the authentication flow. User may need to complete
    2FA on IBKR mobile app.
    """
    try:
        ibkr = IBKRService()
        
        # Trigger re-authentication
        result = await ibkr.reauthenticate()
        
        return {
            "success": True,
            "message": "Authentication initiated. Please check IBKR mobile app for 2FA if required.",
            "result": result
        }
    
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@router.post("/logout")
async def logout():
    """
    Logout from IBKR Gateway.
    
    Note: This may require IBKR Gateway restart for full logout.
    """
    try:
        ibkr = IBKRService()
        
        # IBKR Gateway doesn't have a direct logout endpoint
        # The session is managed by the gateway itself
        # We'll just verify the current state
        
        logger.info("Logout requested - IBKR Gateway session is managed by the gateway")
        
        return {
            "success": True,
            "message": "To fully logout, restart IBKR Gateway or use the gateway UI"
        }
    
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Logout failed: {str(e)}")


@router.get("/accounts")
async def get_accounts():
    """
    Get list of available trading accounts.
    
    Returns list of account IDs the user has access to.
    """
    try:
        ibkr = IBKRService()
        accounts = await ibkr.get_accounts()
        
        return {
            "accounts": accounts,
            "count": len(accounts)
        }
    
    except Exception as e:
        logger.error(f"Failed to fetch accounts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch accounts: {str(e)}")


@router.get("/health")
async def check_gateway_health():
    """
    Check IBKR Gateway health via tickle endpoint.
    
    This endpoint should be called periodically to monitor connection health.
    """
    try:
        import httpx
        
        async with httpx.AsyncClient(timeout=5.0, verify=False) as client:
            response = await client.get(f"{settings.IBKR_API_BASE_URL}/v1/api/tickle")
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "healthy": True,
                    "session_active": data.get('iserver', {}).get('authStatus', {}).get('authenticated', False),
                    "details": data
                }
            else:
                return {
                    "healthy": False,
                    "session_active": False,
                    "error": f"Tickle returned status {response.status_code}"
                }
    
    except Exception as e:
        logger.warning(f"Gateway health check failed: {str(e)}")
        return {
            "healthy": False,
            "session_active": False,
            "error": str(e)
        }

