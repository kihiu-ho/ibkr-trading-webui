"""Chart generation service with technical indicators."""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChartService:
    """Service for generating technical analysis charts."""
    
    def __init__(self):
        self.width = 1920
        self.height = 1080
    
    def calculate_sma(self, data: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average."""
        return data.rolling(window=period).mean()
    
    def calculate_rsi(self, data: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator."""
        ema_fast = data.ewm(span=fast).mean()
        ema_slow = data.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, data: pd.Series, period: int = 20, std: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands."""
        sma = data.rolling(window=period).mean()
        rolling_std = data.rolling(window=period).std()
        upper = sma + (rolling_std * std)
        lower = sma - (rolling_std * std)
        
        return {
            'upper': upper,
            'middle': sma,
            'lower': lower
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def calculate_supertrend(
        self, 
        high: pd.Series, 
        low: pd.Series, 
        close: pd.Series, 
        period: int = 10, 
        multiplier: int = 3
    ) -> Dict[str, pd.Series]:
        """Calculate SuperTrend indicator."""
        atr = self.calculate_atr(high, low, close, period)
        hl_avg = (high + low) / 2
        
        upper_band = hl_avg + (multiplier * atr)
        lower_band = hl_avg - (multiplier * atr)
        
        supertrend = pd.Series(index=close.index, dtype=float)
        direction = pd.Series(index=close.index, dtype=int)
        
        # Initialize
        supertrend.iloc[0] = upper_band.iloc[0]
        direction.iloc[0] = 1
        
        for i in range(1, len(close)):
            if close.iloc[i] > supertrend.iloc[i-1]:
                direction.iloc[i] = 1
                supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
            else:
                direction.iloc[i] = -1
                supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
        
        return {
            'supertrend': supertrend,
            'direction': direction
        }
    
    def generate_chart(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str = "1D"
    ) -> bytes:
        """
        Generate technical analysis chart with indicators.
        
        Args:
            data: DataFrame with columns: date, open, high, low, close, volume
            symbol: Symbol name
            timeframe: Timeframe string (e.g., "1D", "1W")
            
        Returns:
            PNG image bytes
        """
        logger.info(f"Generating chart for {symbol} ({timeframe})")
        
        # Ensure data has required columns
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        if not all(col in data.columns for col in required_cols):
            raise ValueError(f"Data must contain columns: {required_cols}")
        
        # Calculate indicators
        data['sma_20'] = self.calculate_sma(data['close'], 20)
        data['sma_50'] = self.calculate_sma(data['close'], 50)
        data['sma_200'] = self.calculate_sma(data['close'], 200)
        
        data['rsi'] = self.calculate_rsi(data['close'])
        
        macd = self.calculate_macd(data['close'])
        data['macd'] = macd['macd']
        data['macd_signal'] = macd['signal']
        data['macd_hist'] = macd['histogram']
        
        bb = self.calculate_bollinger_bands(data['close'])
        data['bb_upper'] = bb['upper']
        data['bb_middle'] = bb['middle']
        data['bb_lower'] = bb['lower']
        
        supertrend = self.calculate_supertrend(data['high'], data['low'], data['close'])
        data['supertrend'] = supertrend['supertrend']
        data['st_direction'] = supertrend['direction']
        
        # Create subplots
        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.5, 0.15, 0.15, 0.2],
            subplot_titles=(
                f'{symbol} - {timeframe}',
                'Volume',
                'RSI',
                'MACD'
            )
        )
        
        # Candlestick chart
        fig.add_trace(
            go.Candlestick(
                x=data['date'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name='Price'
            ),
            row=1, col=1
        )
        
        # Moving Averages
        fig.add_trace(go.Scatter(x=data['date'], y=data['sma_20'], name='SMA 20', line=dict(color='orange', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data['date'], y=data['sma_50'], name='SMA 50', line=dict(color='blue', width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=data['date'], y=data['sma_200'], name='SMA 200', line=dict(color='red', width=1)), row=1, col=1)
        
        # SuperTrend
        fig.add_trace(
            go.Scatter(
                x=data['date'],
                y=data['supertrend'],
                name='SuperTrend',
                line=dict(color='green', width=2),
                mode='lines'
            ),
            row=1, col=1
        )
        
        # Bollinger Bands
        fig.add_trace(go.Scatter(x=data['date'], y=data['bb_upper'], name='BB Upper', line=dict(color='gray', width=1, dash='dash')), row=1, col=1)
        fig.add_trace(go.Scatter(x=data['date'], y=data['bb_lower'], name='BB Lower', line=dict(color='gray', width=1, dash='dash'), fill='tonexty'), row=1, col=1)
        
        # Volume
        colors = ['red' if row['close'] < row['open'] else 'green' for _, row in data.iterrows()]
        fig.add_trace(
            go.Bar(x=data['date'], y=data['volume'], name='Volume', marker_color=colors),
            row=2, col=1
        )
        
        # RSI
        fig.add_trace(go.Scatter(x=data['date'], y=data['rsi'], name='RSI', line=dict(color='purple')), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
        
        # MACD
        fig.add_trace(go.Scatter(x=data['date'], y=data['macd'], name='MACD', line=dict(color='blue')), row=4, col=1)
        fig.add_trace(go.Scatter(x=data['date'], y=data['macd_signal'], name='Signal', line=dict(color='orange')), row=4, col=1)
        fig.add_trace(go.Bar(x=data['date'], y=data['macd_hist'], name='Histogram'), row=4, col=1)
        
        # Update layout
        fig.update_layout(
            title=f'{symbol} Technical Analysis - {timeframe}',
            xaxis_rangeslider_visible=False,
            height=self.height,
            width=self.width,
            showlegend=True,
            template='plotly_white'
        )
        
        # Update y-axis labels
        fig.update_yaxes(title_text="Price", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI", row=3, col=1)
        fig.update_yaxes(title_text="MACD", row=4, col=1)
        
        # Export to PNG
        img_bytes = fig.to_image(format="png")
        logger.info(f"Chart generated successfully for {symbol}")
        
        return img_bytes

