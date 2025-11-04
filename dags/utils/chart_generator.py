"""
Chart generation with technical indicators
"""
import logging
from datetime import datetime
from typing import Optional
import os
import tempfile
from decimal import Decimal

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import mplfinance as mpf

from models.market_data import MarketData
from models.indicators import TechnicalIndicators
from models.chart import ChartConfig, ChartResult, Timeframe

logger = logging.getLogger(__name__)


class ChartGenerator:
    """Generate technical analysis charts with indicators"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize chart generator
        
        Args:
            output_dir: Directory to save charts (uses temp dir if None)
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)
    
    def calculate_indicators(self, market_data: MarketData) -> TechnicalIndicators:
        """
        Calculate technical indicators from market data
        
        Args:
            market_data: Market data with OHLCV bars
            
        Returns:
            TechnicalIndicators with calculated values
        """
        # Convert to pandas DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': bar.volume
            }
            for bar in market_data.bars
        ])
        df.set_index('timestamp', inplace=True)
        
        indicators = TechnicalIndicators()
        
        # Calculate SMAs
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        indicators.sma_20 = [Decimal(str(x)) if not pd.isna(x) else None for x in df['SMA_20']]
        indicators.sma_50 = [Decimal(str(x)) if not pd.isna(x) else None for x in df['SMA_50']]
        indicators.sma_200 = [Decimal(str(x)) if not pd.isna(x) else None for x in df['SMA_200']]
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        indicators.rsi_14 = [Decimal(str(x)) if not pd.isna(x) else None for x in df['RSI']]
        
        # Calculate MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        indicators.macd_line = [Decimal(str(x)) if not pd.isna(x) else None for x in df['MACD']]
        indicators.macd_signal = [Decimal(str(x)) if not pd.isna(x) else None for x in df['MACD_Signal']]
        indicators.macd_histogram = [Decimal(str(x)) if not pd.isna(x) else None for x in df['MACD_Hist']]
        
        # Calculate Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(window=20).mean()
        bb_std = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        indicators.bb_upper = [Decimal(str(x)) if not pd.isna(x) else None for x in df['BB_Upper']]
        indicators.bb_middle = [Decimal(str(x)) if not pd.isna(x) else None for x in df['BB_Middle']]
        indicators.bb_lower = [Decimal(str(x)) if not pd.isna(x) else None for x in df['BB_Lower']]
        
        logger.info(f"Calculated indicators for {market_data.symbol}")
        return indicators
    
    def generate_chart(
        self,
        market_data: MarketData,
        config: ChartConfig,
        indicators: Optional[TechnicalIndicators] = None
    ) -> ChartResult:
        """
        Generate technical analysis chart
        
        Args:
            market_data: Market data to chart
            config: Chart configuration
            indicators: Pre-calculated indicators (calculates if None)
            
        Returns:
            ChartResult with file path and metadata
        """
        # Calculate indicators if not provided
        if indicators is None:
            indicators = self.calculate_indicators(market_data)
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'Date': bar.timestamp,
                'Open': float(bar.open),
                'High': float(bar.high),
                'Low': float(bar.low),
                'Close': float(bar.close),
                'Volume': bar.volume
            }
            for bar in market_data.bars
        ])
        df.set_index('Date', inplace=True)
        
        # Take last N periods
        df = df.tail(config.lookback_periods)
        
        # Prepare additional plots
        apds = []
        indicators_included = []
        
        # Add SMAs if requested
        if config.include_sma and indicators.has_sma:
            if indicators.sma_20:
                df['SMA_20'] = [float(x) if x is not None else np.nan for x in indicators.sma_20[-len(df):]]
                indicators_included.append("SMA_20")
            if indicators.sma_50:
                df['SMA_50'] = [float(x) if x is not None else np.nan for x in indicators.sma_50[-len(df):]]
                indicators_included.append("SMA_50")
            if indicators.sma_200:
                df['SMA_200'] = [float(x) if x is not None else np.nan for x in indicators.sma_200[-len(df):]]
                indicators_included.append("SMA_200")
        
        # Add Bollinger Bands if requested
        if config.include_bollinger and indicators.has_bollinger:
            df['BB_Upper'] = [float(x) if x is not None else np.nan for x in indicators.bb_upper[-len(df):]]
            df['BB_Middle'] = [float(x) if x is not None else np.nan for x in indicators.bb_middle[-len(df):]]
            df['BB_Lower'] = [float(x) if x is not None else np.nan for x in indicators.bb_lower[-len(df):]]
            indicators_included.append("Bollinger_Bands")
        
        # Add RSI if requested
        if config.include_rsi and indicators.has_rsi:
            df['RSI'] = [float(x) if x is not None else np.nan for x in indicators.rsi_14[-len(df):]]
            apds.append(
                mpf.make_addplot(df['RSI'], panel=1, color='purple', ylabel='RSI', 
                                ylim=(0, 100), secondary_y=False)
            )
            indicators_included.append("RSI")
        
        # Add MACD if requested
        if config.include_macd and indicators.has_macd:
            df['MACD'] = [float(x) if x is not None else np.nan for x in indicators.macd_line[-len(df):]]
            df['MACD_Signal'] = [float(x) if x is not None else np.nan for x in indicators.macd_signal[-len(df):]]
            df['MACD_Hist'] = [float(x) if x is not None else np.nan for x in indicators.macd_histogram[-len(df):]]
            
            panel_idx = 2 if config.include_rsi else 1
            apds.extend([
                mpf.make_addplot(df['MACD'], panel=panel_idx, color='blue', ylabel='MACD'),
                mpf.make_addplot(df['MACD_Signal'], panel=panel_idx, color='red'),
                mpf.make_addplot(df['MACD_Hist'], panel=panel_idx, type='bar', color='gray', alpha=0.3)
            ])
            indicators_included.append("MACD")
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timeframe_str = config.timeframe.value if hasattr(config.timeframe, 'value') else str(config.timeframe)
        filename = f"{config.symbol}_{timeframe_str}_{timestamp}.png"
        file_path = os.path.join(self.output_dir, filename)
        
        # Create style
        mc = mpf.make_marketcolors(
            up=config.up_color,
            down=config.down_color,
            edge='inherit',
            wick='inherit',
            volume='in'
        )
        s = mpf.make_mpf_style(marketcolors=mc, gridstyle=':', y_on_right=False)
        
        # Plot
        timeframe_str = config.timeframe.value if hasattr(config.timeframe, 'value') else str(config.timeframe)
        fig, axes = mpf.plot(
            df,
            type='candle',
            style=s,
            title=f"{config.symbol} - {timeframe_str} Chart",
            ylabel='Price',
            volume=config.include_volume,
            addplot=apds if apds else None,
            figsize=(config.width/100, config.height/100),
            returnfig=True,
            savefig=file_path
        )
        
        plt.close(fig)
        
        result = ChartResult(
            symbol=config.symbol,
            timeframe=config.timeframe if isinstance(config.timeframe, Timeframe) else Timeframe(config.timeframe),
            file_path=file_path,
            width=config.width,
            height=config.height,
            periods_shown=len(df),
            indicators_included=indicators_included
        )
        
        logger.info(f"Generated chart: {filename} with {len(indicators_included)} indicators")
        return result
    
    def resample_to_weekly(self, market_data: MarketData) -> MarketData:
        """
        Resample daily data to weekly timeframe
        
        Args:
            market_data: Daily market data
            
        Returns:
            Weekly market data
        """
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'timestamp': bar.timestamp,
                'open': float(bar.open),
                'high': float(bar.high),
                'low': float(bar.low),
                'close': float(bar.close),
                'volume': bar.volume
            }
            for bar in market_data.bars
        ])
        df.set_index('timestamp', inplace=True)
        
        # Resample to weekly
        weekly = df.resample('W').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        # Convert back to OHLCVBars
        from models.market_data import OHLCVBar
        
        weekly_bars = []
        for idx, row in weekly.iterrows():
            bar = OHLCVBar(
                timestamp=idx,
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=int(row['volume'])
            )
            weekly_bars.append(bar)
        
        weekly_market_data = MarketData(
            symbol=market_data.symbol,
            exchange=market_data.exchange,
            bars=weekly_bars,
            timeframe="1W",
            fetched_at=datetime.utcnow()
        )
        
        logger.info(f"Resampled {len(market_data.bars)} daily bars to {len(weekly_bars)} weekly bars")
        return weekly_market_data

