"""
Timeout utilities for handling long-running operations
"""
import signal
import logging
from contextlib import contextmanager
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class TimeoutError(Exception):
    """Custom timeout error"""
    pass


@contextmanager
def timeout_context(seconds: int):
    """
    Context manager for operation timeouts using SIGALRM
    
    Args:
        seconds: Timeout in seconds
        
    Raises:
        TimeoutError: If operation exceeds timeout
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Only works on Unix systems
    if hasattr(signal, 'SIGALRM'):
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
    else:
        # Windows doesn't support SIGALRM, just execute without timeout
        logger.warning("SIGALRM not available (Windows?), timeout not enforced")
        yield


def with_timeout(timeout_seconds: int, fallback: Optional[Callable] = None):
    """
    Decorator to add timeout to a function
    
    Args:
        timeout_seconds: Timeout in seconds
        fallback: Optional fallback function to call on timeout
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                with timeout_context(timeout_seconds):
                    return func(*args, **kwargs)
            except TimeoutError as e:
                logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s: {e}")
                if fallback:
                    logger.info(f"Calling fallback function for {func.__name__}")
                    return fallback(*args, **kwargs)
                raise
        return wrapper
    return decorator


def execute_with_timeout(func: Callable, timeout_seconds: int, *args, fallback: Optional[Callable] = None, **kwargs) -> Any:
    """
    Execute a function with timeout
    
    Args:
        func: Function to execute
        timeout_seconds: Timeout in seconds
        *args: Positional arguments for func
        fallback: Optional fallback function
        **kwargs: Keyword arguments for func
        
    Returns:
        Function result or fallback result
        
    Raises:
        TimeoutError: If function exceeds timeout
    """
    try:
        with timeout_context(timeout_seconds):
            return func(*args, **kwargs)
    except TimeoutError as e:
        logger.error(f"Function {func.__name__} timed out after {timeout_seconds}s: {e}")
        if fallback:
            logger.info(f"Calling fallback function for {func.__name__}")
            return fallback(*args, **kwargs)
        raise

