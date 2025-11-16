"""
Chart generation with technical indicators using Plotly
"""
import logging
from datetime import datetime
from typing import Optional
import os
import tempfile
from decimal import Decimal
import importlib.util
import subprocess
import sys
import threading

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from models.market_data import MarketData
from models.indicators import TechnicalIndicators
from models.chart import ChartConfig, ChartResult, Timeframe
from shared.indicator_engine import build_chart_payload, compute_indicator_series

logger = logging.getLogger(__name__)


class KaleidoMissingError(RuntimeError):
    """Raised when Kaleido cannot be imported despite auto-install attempts."""


_KALEIDO_CHECK_LOCK = threading.Lock()
_KALEIDO_READY: Optional[bool] = None


def _is_kaleido_importable() -> bool:
    return importlib.util.find_spec('kaleido') is not None


def ensure_kaleido_available(auto_install: bool = True, install_timeout: int = 120) -> bool:
    """Ensure Kaleido is available for Plotly image export."""
    global _KALEIDO_READY

    with _KALEIDO_CHECK_LOCK:
        if _KALEIDO_READY:
            return True

    if _is_kaleido_importable():
        with _KALEIDO_CHECK_LOCK:
            _KALEIDO_READY = True
        return True

    if not auto_install:
        raise KaleidoMissingError(
            "Kaleido is not installed. Rebuild the Airflow image or run 'pip install kaleido==0.2.1'."
        )

    logger.warning("Kaleido not found. Attempting on-the-fly installation (kaleido>=0.2.1)...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', '--no-cache-dir', 'kaleido>=0.2.1'],
            capture_output=True,
            text=True,
            timeout=install_timeout,
            check=True,
        )
        if result.stdout:
            logger.info(result.stdout.strip())
        if result.stderr:
            logger.debug(result.stderr.strip())
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise KaleidoMissingError(
            "Unable to auto-install Kaleido. Rebuild the ibkr-airflow image or run the verify_kaleido script."
        ) from exc

    if not _is_kaleido_importable():
        raise KaleidoMissingError(
            "Kaleido installation completed but import still fails. Ensure kaleido==0.2.1 is available."
        )

    with _KALEIDO_CHECK_LOCK:
        _KALEIDO_READY = True
    logger.info("Kaleido successfully installed and ready.")
    return True


def create_plotly_figure(df, processed_indicators, symbol, height=1400):
    """Create Plotly figure with 7 subplots for technical analysis"""
    dates = df['Date']
    latest = df.iloc[-1]
    latest_ohlc = f"Open: {latest['Open']:.2f} | High: {latest['High']:.2f} | Low: {latest['Low']:.2f} | Close: {latest['Close']:.2f}"

    fig = make_subplots(rows=7, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        subplot_titles=(f"{symbol} Price", "SuperTrend", "Volume (M)", "MACD", "RSI",
                                        f"OBV ({processed_indicators['obv_unit']})", "ATR"),
                        row_heights=[0.35, 0.15, 0.1, 0.15, 0.15, 0.1, 0.1],
                        specs=[[{"secondary_y": True}], [{"secondary_y": True}], [{"secondary_y": True}],
                               [{"secondary_y": True}], [{"secondary_y": True}], [{"secondary_y": True}],
                               [{"secondary_y": True}]])

    def _primary_yref(row_index: int) -> str:
        """Map subplot row to the corresponding primary y-axis reference."""
        if row_index <= 1:
            return "y"
        axis_index = (row_index - 1) * 2 + 1
        return f"y{axis_index}"

    def add_max_min_avg(data, row, _axis_label=None, unit=""):
        """Add max/min/average/median annotations to a subplot"""
        if not data or all(x is None for x in data):
            return
        valid_data = [x for x in data if x is not None]
        if not valid_data:
            return
        max_val, min_val = max(valid_data), min(valid_data)
        avg_val = sum(valid_data) / len(valid_data)
        median_val = sorted(valid_data)[len(valid_data) // 2]
        max_idx = data.index(max_val) if max_val in data else None
        min_idx = data.index(min_val) if min_val in data else None
        max_text = f"Max: {max_val:.2f}{unit}"
        min_text = f"Min: {min_val:.2f}{unit}"
        avg_text = f"Avg: {avg_val:.2f}{unit}"
        median_text = f"Med: {median_val:.2f}{unit}"
        if max_idx is not None:
            fig.add_annotation(
                x=dates.iloc[max_idx],
                y=max_val,
                text=max_text,
                showarrow=True,
                arrowhead=1,
                row=row,
                col=1,
                yref=_primary_yref(row)
            )
        if min_idx is not None:
            fig.add_annotation(
                x=dates.iloc[min_idx],
                y=min_val,
                text=min_text,
                showarrow=True,
                arrowhead=1,
                row=row,
                col=1,
                yref=_primary_yref(row)
            )
        fig.add_hline(y=avg_val, line_dash="dash", line_color="gray", line_width=1, row=row, col=1,
                      annotation_text=avg_text, annotation_position="right")
        fig.add_hline(y=median_val, line_dash="dot", line_color="gray", line_width=1, row=row, col=1,
                      annotation_text=median_text, annotation_position="right")

    # Price Chart
    fig.add_trace(go.Candlestick(x=dates, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                                 name=f'{symbol} Price', increasing_line_color='green', decreasing_line_color='red'),
                  row=1, col=1)
    fig.add_trace(
        go.Scatter(x=[dates.iloc[-1]], y=[latest['Close']], mode='markers+text', text=[f"{latest['Close']:.2f}"],
                   textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10), yaxis='y2'),
        row=1, col=1, secondary_y=True)
    add_max_min_avg(df['Close'].tolist(), 1, "Price")

    fig.add_trace(
        go.Scatter(x=dates, y=processed_indicators['sma_20'], mode='lines', name='SMA 20', line=dict(color='blue')),
        row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['sma_50'], mode='lines', name='SMA 50',
                             line=dict(color='rgb(47,203,13)', width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['sma_200'], mode='lines', name='SMA 200',
                             line=dict(color='rgb(240,130,21)', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['bb_upper'], mode='lines', name='BB Upper',
                             line=dict(color='rgb(33,150,243)', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['bb_lower'], mode='lines', name='BB Lower',
                             line=dict(color='rgb(33,150,243)', width=1), fill='tonexty',
                             fillcolor='rgba(33,150,243,0.1)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['bb_median'], mode='lines', name='BB Median',
                             line=dict(color='rgb(255,109,0)', width=1)), row=1, col=1)

    # SuperTrend
    st_up = [v if d == 1 else None for v, d in
             zip(processed_indicators['st_values'], processed_indicators['st_direction'])]
    st_down = [v if d == -1 else None for v, d in
               zip(processed_indicators['st_values'], processed_indicators['st_direction'])]
    fig.add_trace(go.Scatter(x=dates, y=st_up, mode='lines', name='SuperTrend Up', line=dict(color='rgb(0,128,0)')),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=dates, y=st_down, mode='lines', name='SuperTrend Down', line=dict(color='rgb(128,0,0)')),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=[dates.iloc[-1]], y=[processed_indicators['st_values'][-1]], mode='markers+text',
                             text=[f"{processed_indicators['st_values'][-1]:.2f}"],
                             textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10),
                             yaxis='y2'), row=2, col=1, secondary_y=True)
    add_max_min_avg(processed_indicators['st_values'], 2, "SuperTrend")

    # Volume
    colors = ['green' if df['Close'].iloc[i] >= df['Open'].iloc[i] else 'red' for i in range(len(df))]
    fig.add_trace(go.Bar(x=dates, y=processed_indicators['volume'], name='Volume', marker_color=colors), row=3, col=1)
    fig.add_trace(go.Scatter(x=[dates.iloc[-1]], y=[processed_indicators['volume'].iloc[-1]], mode='markers+text',
                             text=[f"{processed_indicators['volume'].iloc[-1]:.2f}M"],
                             textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10),
                             yaxis='y2'), row=3, col=1, secondary_y=True)
    add_max_min_avg(processed_indicators['volume'].tolist(), 3, "Volume", unit="M")

    # MACD
    fig.add_trace(go.Bar(x=dates, y=processed_indicators['histogram'], name='MACD Histogram', marker_color=[
        'rgb(34,171,148)' if h is not None and h > 0 and prev is not None and h >= prev else
        'rgb(172,229,220)' if h is not None and h > 0 else
        'rgb(252,203,205)' if h is not None and h < 0 and prev is not None and h <= prev else
        'rgb(255,82,82)' if h is not None and h < 0 else 'gray' for h, prev in
        zip(processed_indicators['histogram'], [0] + processed_indicators['histogram'][:-1])]), row=4, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['macd_line'], mode='lines', name='MACD',
                             line=dict(color='rgb(33,150,243)', width=1)), row=4, col=1)
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['signal_line'], mode='lines', name='Signal',
                             line=dict(color='rgb(255,109,0)', width=1)), row=4, col=1)
    fig.add_trace(go.Scatter(x=[dates.iloc[-1]], y=[processed_indicators['macd_line'][-1]], mode='markers+text',
                             text=[f"{processed_indicators['macd_line'][-1]:.2f}"],
                             textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10),
                             yaxis='y2'), row=4, col=1, secondary_y=True)
    add_max_min_avg(processed_indicators['macd_line'], 4, "MACD")

    # RSI
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['rsi'], mode='lines', name='RSI',
                             line=dict(color='rgb(126,87,194)', width=1)), row=5, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="rgb(120,123,134)", line_width=1, row=5, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="rgb(120,123,134)", line_width=1, row=5, col=1)
    fig.add_hrect(y0=30, y1=70, fillcolor="rgba(126,87,194,0.1)", line_width=0, row=5, col=1)
    fig.add_trace(go.Scatter(x=[dates.iloc[-1]], y=[processed_indicators['rsi'][-1]], mode='markers+text',
                             text=[f"{processed_indicators['rsi'][-1]:.2f}"],
                             textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10),
                             yaxis='y2'), row=5, col=1, secondary_y=True)
    add_max_min_avg(processed_indicators['rsi'], 5, "RSI")

    # OBV
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['obv_normalized'], mode='lines', name='OBV',
                             line=dict(color='rgb(33,150,243)', width=1)), row=6, col=1)
    fig.add_trace(go.Scatter(x=[dates.iloc[-1]], y=[processed_indicators['obv_normalized'][-1]], mode='markers+text',
                             text=[
                                 f"{processed_indicators['obv_normalized'][-1]:.2f}{processed_indicators['obv_unit']}"],
                             textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10),
                             yaxis='y2'), row=6, col=1, secondary_y=True)
    add_max_min_avg(processed_indicators['obv_normalized'], 6, "OBV", unit=processed_indicators['obv_unit'])

    # ATR
    fig.add_trace(go.Scatter(x=dates, y=processed_indicators['atr'], mode='lines', name='ATR',
                             line=dict(color='rgb(128,25,34)', width=1)), row=7, col=1)
    fig.add_trace(go.Scatter(x=[dates.iloc[-1]], y=[processed_indicators['atr'][-1]], mode='markers+text',
                             text=[f"{processed_indicators['atr'][-1]:.2f}"],
                             textposition="middle right", showlegend=False, marker=dict(color='yellow', size=10),
                             yaxis='y2'), row=7, col=1, secondary_y=True)
    add_max_min_avg(processed_indicators['atr'], 7, "ATR")

    # Update layout
    fig.update_layout(
        title=dict(text=f'{symbol} <br><sup>{latest_ohlc}</sup>', x=0.5, xanchor='center', font=dict(size=20)),
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        template='plotly_white',
        height=height,
        font=dict(size=16),
        legend=dict(x=0.01, y=-0.05, xanchor="left", yanchor="top", orientation="h"),
        xaxis7_title="Date"
    )
    fig.update_yaxes(title_text="Price (USD)", row=1, col=1, ticklabelposition="outside")
    fig.update_yaxes(title_text="SuperTrend", row=2, col=1, ticklabelposition="outside")
    fig.update_yaxes(title_text="Volume (M)", row=3, col=1, ticklabelposition="outside")
    fig.update_yaxes(title_text="MACD", row=4, col=1, ticklabelposition="outside")
    fig.update_yaxes(title_text="RSI", row=5, col=1, ticklabelposition="outside")
    fig.update_yaxes(title_text=f"OBV ({processed_indicators['obv_unit']})", row=6, col=1, ticklabelposition="outside")
    fig.update_yaxes(title_text="ATR", row=7, col=1, ticklabelposition="outside")
    for i in range(1, 8):
        fig.update_yaxes(showgrid=False, title_text="", row=i, col=1, secondary_y=True, ticklabelposition="outside")

    return fig


class ChartGenerator:
    """Generate technical analysis charts with indicators using Plotly"""
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize chart generator
        
        Args:
            output_dir: Directory to save charts (uses temp dir if None)
        """
        self.output_dir = output_dir or tempfile.gettempdir()
        os.makedirs(self.output_dir, exist_ok=True)

        # Ensure Kaleido is available before initializing Plotly export scope
        ensure_kaleido_available()
        # Initialize Kaleido with Chromium path if available
        self._init_kaleido()
    
    def _init_kaleido(self):
        """Initialize Kaleido using the defaults API to avoid deprecation warnings."""
        try:
            scope = getattr(pio.defaults, 'kaleido_scope', None)
            if scope is None:
                scope = getattr(pio, 'kaleido').scope  # Backward compatibility
            scope.mathjax = None
            chromium_args = list(getattr(scope, 'chromium_args', ()))
            for arg in ("--single-process", "--disable-gpu"):
                if arg not in chromium_args:
                    chromium_args.append(arg)
            scope.chromium_args = tuple(chromium_args)
            chromium_path = os.environ.get('CHROMIUM_PATH') or os.environ.get('CHROME_BIN')
            if chromium_path and os.path.exists(chromium_path):
                logger.info(f"Kaleido defaults initialized with Chromium: {chromium_path}")
            else:
                logger.debug("Kaleido defaults initialized without explicit Chromium path")
        except Exception as e:
            logger.warning(
                f"Kaleido initialization warning: {e}. HTML fallback will be used if image export fails."
            )
    
    def _save_html_fallback(self, fig, original_file_path: str, config: ChartConfig) -> str:
        """
        Save chart as HTML file when image export fails
        
        Args:
            fig: Plotly figure to save
            original_file_path: Original file path (JPEG/PNG)
            config: Chart configuration
            
        Returns:
            Path to saved HTML file
        """
        # Replace extension with .html
        html_path = os.path.splitext(original_file_path)[0] + '.html'
        
        # Export to HTML
        html_string = pio.to_html(fig, include_plotlyjs='cdn', full_html=True)
        
        # Write to file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_string)
        
        logger.info(f"Chart saved as HTML fallback: {html_path}")
        return html_path
    
    def calculate_indicators(self, market_data: MarketData) -> TechnicalIndicators:
        """
        Calculate technical indicators from market data using pandas-based logic
        
        Args:
            market_data: Market data with OHLCV bars
            
        Returns:
            TechnicalIndicators with calculated values
        """
        df = pd.DataFrame([
            {
                'Date': bar.timestamp,
                'Open': float(bar.open),
                'High': float(bar.high),
                'Low': float(bar.low),
                'Close': float(bar.close),
                'Volume': int(bar.volume)
            }
            for bar in market_data.bars
        ])

        indicator_series = compute_indicator_series(df)

        def _to_decimal_list(series: pd.Series):
            values = []
            for value in series:
                if pd.isna(value):
                    values.append(None)
                else:
                    values.append(Decimal(str(float(value))))
            return values

        indicators_obj = TechnicalIndicators()
        indicators_obj.sma_20 = _to_decimal_list(indicator_series['sma_20'])
        indicators_obj.sma_50 = _to_decimal_list(indicator_series['sma_50'])
        indicators_obj.sma_200 = _to_decimal_list(indicator_series['sma_200'])
        indicators_obj.bb_upper = _to_decimal_list(indicator_series['bb_upper'])
        indicators_obj.bb_middle = _to_decimal_list(indicator_series['bb_median'])
        indicators_obj.bb_lower = _to_decimal_list(indicator_series['bb_lower'])
        indicators_obj.rsi_14 = _to_decimal_list(indicator_series['rsi'])
        indicators_obj.macd_line = _to_decimal_list(indicator_series['macd_line'])
        indicators_obj.macd_signal = _to_decimal_list(indicator_series['signal_line'])
        indicators_obj.macd_histogram = _to_decimal_list(indicator_series['histogram'])

        logger.info("Calculated indicators for %s", market_data.symbol)
        return indicators_obj
    
    def generate_chart(
        self,
        market_data: MarketData,
        config: ChartConfig,
        indicators: Optional[TechnicalIndicators] = None
    ) -> ChartResult:
        """
        Generate technical analysis chart using Plotly
        
        Args:
            market_data: Market data to chart
            config: Chart configuration
            indicators: Pre-calculated indicators (calculates if None)
            
        Returns:
            ChartResult with file path and metadata
        """
        # Convert to DataFrame
        df = pd.DataFrame([
            {
                'Date': bar.timestamp,
                'Open': float(bar.open),
                'High': float(bar.high),
                'Low': float(bar.low),
                'Close': float(bar.close),
                'Volume': int(bar.volume)
            }
            for bar in market_data.bars
        ])
        
        # Take last N periods
        df = df.tail(config.lookback_periods).copy()
        df.reset_index(drop=True, inplace=True)
        
        processed_indicators = build_chart_payload(df)
        
        # Create Plotly figure
        fig = create_plotly_figure(df, processed_indicators, config.symbol, height=config.height)
        
        # Generate filename (JPEG format)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        timeframe_str = config.timeframe.value if hasattr(config.timeframe, 'value') else str(config.timeframe)
        filename = f"{config.symbol}_{timeframe_str}_{timestamp}.jpeg"
        file_path = os.path.join(self.output_dir, filename)
        
        # Save as JPEG with timeout handling and HTML fallback
        # Kaleido can hang, so we add a timeout
        # If Chromium is not available, fall back to HTML export
        html_fallback_used = False
        
        def _is_chrome_error(error: Exception) -> bool:
            """Check if error is related to Chrome/Chromium not found"""
            error_str = str(error).lower()
            error_type = type(error).__name__.lower()
            return ('chrome' in error_str or 'chromium' in error_str or 
                    'chromenotfounderror' in error_type or
                    ('kaleido' in error_str and 'chrome' in error_str))
        
        def _try_image_export():
            """Try to export chart as image (JPEG or PNG)"""
            try:
                from utils.timeout_utils import execute_with_timeout
                
                def save_jpeg():
                    return pio.write_image(fig, file_path, format='jpeg', width=config.width, height=config.height)
                
                def save_png_fallback():
                    # Fallback to PNG if JPEG times out
                    png_path = file_path.replace('.jpeg', '.png')
                    logger.warning(f"JPEG generation timed out, falling back to PNG: {png_path}")
                    try:
                        pio.write_image(fig, png_path, format='png', width=config.width, height=config.height)
                        return png_path
                    except Exception as png_err:
                        # If PNG also fails with Chrome error, re-raise to trigger HTML fallback
                        if _is_chrome_error(png_err):
                            raise
                        # Otherwise, re-raise as-is
                        raise
                
                # Try JPEG with 60 second timeout, fallback to PNG
                try:
                    result_path = execute_with_timeout(
                        save_jpeg,
                        timeout_seconds=60,
                        fallback=save_png_fallback
                    )
                    if result_path and result_path != file_path:
                        return result_path
                    return file_path
                except Exception as timeout_err:
                    # If execute_with_timeout raises non-TimeoutError (e.g., ChromeNotFoundError from save_jpeg or save_png_fallback)
                    if _is_chrome_error(timeout_err):
                        raise  # Re-raise Chrome errors to trigger HTML fallback
                    # For other errors, try direct save
                    raise
                    
            except ImportError:
                # If timeout utils not available, try direct save with error handling
                logger.warning("Timeout utils not available, saving without timeout")
                try:
                    pio.write_image(fig, file_path, format='jpeg', width=config.width, height=config.height)
                    return file_path
                except Exception as jpeg_err:
                    if _is_chrome_error(jpeg_err):
                        raise  # Re-raise Chrome errors to trigger HTML fallback
                    # Try PNG fallback for other errors
                    logger.warning(f"JPEG save failed: {jpeg_err}, trying PNG fallback")
                    try:
                        png_path = file_path.replace('.jpeg', '.png')
                        pio.write_image(fig, png_path, format='png', width=config.width, height=config.height)
                        return png_path
                    except Exception as png_err:
                        if _is_chrome_error(png_err):
                            raise  # Re-raise Chrome errors to trigger HTML fallback
                        # For other errors, re-raise
                        raise
        
        # Try image export, fall back to HTML if Chrome error occurs
        try:
            result_path = _try_image_export()
            if result_path and result_path != file_path:
                file_path = result_path
                filename = os.path.basename(file_path)
        except Exception as e:
            if _is_chrome_error(e):
                # Chrome/Chromium not available - use HTML fallback
                logger.warning(
                    f"Chromium not available for image export: {e}. "
                    "Falling back to HTML export. Install Chromium or set CHROMIUM_PATH environment variable."
                )
                html_fallback_used = True
                file_path = self._save_html_fallback(fig, file_path, config)
                filename = os.path.basename(file_path)
            else:
                # Other errors - try HTML fallback as last resort
                logger.error(f"Chart image export failed: {e}", exc_info=True)
                try:
                    logger.warning("Attempting HTML fallback due to image export failure")
                    html_fallback_used = True
                    file_path = self._save_html_fallback(fig, file_path, config)
                    filename = os.path.basename(file_path)
                except Exception as html_error:
                    logger.error(f"HTML fallback also failed: {html_error}", exc_info=True)
                    raise
        
        # Build indicators included list
        indicators_included = [
            "SMA_20", "SMA_50", "SMA_200",
            "Bollinger_Bands",
            "SuperTrend",
            "MACD",
            "RSI",
            "OBV",
            "ATR",
            "Volume"
        ]
        
        result = ChartResult(
            symbol=config.symbol,
            timeframe=config.timeframe if isinstance(config.timeframe, Timeframe) else Timeframe(config.timeframe),
            file_path=file_path,
            width=config.width,
            height=config.height,
            periods_shown=len(df),
            indicators_included=indicators_included
        )
        
        logger.info("Generated chart: %s with %d indicators", filename, len(indicators_included))
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
        
        logger.info("Resampled %d daily bars to %d weekly bars", len(market_data.bars), len(weekly_bars))
        return weekly_market_data
