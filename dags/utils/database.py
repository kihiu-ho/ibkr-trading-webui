"""
Database utilities for IBKR workflows
Handles PostgreSQL connections and queries
"""
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from .config import config

logger = logging.getLogger(__name__)


class DatabaseClient:
    """PostgreSQL database client with connection pooling"""
    
    def __init__(self):
        self.pool: Optional[SimpleConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.pool = SimpleConnectionPool(
                minconn=1,
                maxconn=5,
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password
            )
            logger.info(f"Database connection pool initialized for {config.db_host}:{config.db_port}/{config.db_name}")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn = None
        try:
            conn = self.pool.getconn()
            yield conn
        finally:
            if conn:
                self.pool.putconn(conn)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results as list of dicts"""
        if config.debug_mode:
            logger.debug(f"Executing query: {query}")
            if params:
                logger.debug(f"Query parameters: {params}")
        
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                return [dict(row) for row in results]
    
    def fetch_stock_data(self, symbols: List[str], limit: Optional[int] = None) -> pd.DataFrame:
        """
        Fetch stock data for given symbols from PostgreSQL
        
        Args:
            symbols: List of stock symbols (e.g., ['TSLA', 'NVDA'])
            limit: Optional limit on number of rows per symbol
            
        Returns:
            DataFrame with stock data
        """
        logger.info(f"Fetching stock data for symbols: {', '.join(symbols)}")
        
        # Build query - assuming a 'stock_data' table exists
        # Adjust table name and columns based on actual schema
        placeholders = ','.join(['%s'] * len(symbols))
        
        query = f"""
            SELECT 
                symbol,
                date,
                open,
                high,
                low,
                close,
                volume,
                created_at
            FROM stock_data
            WHERE symbol IN ({placeholders})
            ORDER BY symbol, date DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        try:
            results = self.execute_query(query, tuple(symbols))
            
            if not results:
                logger.warning(f"No data found for symbols: {', '.join(symbols)}")
                return pd.DataFrame()
            
            df = pd.DataFrame(results)
            logger.info(f"Retrieved {len(df)} rows for {df['symbol'].nunique()} symbols")
            
            if config.debug_mode:
                logger.debug(f"Data shape: {df.shape}")
                logger.debug(f"Columns: {df.columns.tolist()}")
                logger.debug(f"Sample data:\n{df.head()}")
            
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch stock data: {e}")
            raise
    
    def check_symbols_exist(self, symbols: List[str]) -> Dict[str, bool]:
        """
        Check which symbols have data in the database
        
        Returns:
            Dict mapping symbol to existence (True/False)
        """
        placeholders = ','.join(['%s'] * len(symbols))
        query = f"""
            SELECT DISTINCT symbol
            FROM stock_data
            WHERE symbol IN ({placeholders})
        """
        
        try:
            results = self.execute_query(query, tuple(symbols))
            existing_symbols = {row['symbol'] for row in results}
            
            return {symbol: symbol in existing_symbols for symbol in symbols}
        
        except Exception as e:
            logger.error(f"Failed to check symbol existence: {e}")
            raise
    
    def close(self):
        """Close all database connections"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Global database client instance
db_client = DatabaseClient()

