"""Utility functions for computing technical indicators without stock_indicators."""
from __future__ import annotations

from typing import Dict, Tuple

import pandas as pd


def normalize_value(value: float) -> Tuple[float, str]:
    """Normalize large values for display and return the scaled unit suffix."""
    if pd.isna(value):
        return 0.0, ""
    if abs(value) >= 1_000_000_000:
        return value / 1_000_000_000, "B"
    if abs(value) >= 1_000_000:
        return value / 1_000_000, "M"
    return value, ""


def _series_to_list(series: pd.Series) -> list:
    return [None if pd.isna(v) else float(v) for v in series]


def calculate_obv_series(df: pd.DataFrame) -> pd.Series:
    """Return On-Balance Volume as a pandas Series aligned with df."""
    obv = [0.0]
    for i in range(1, len(df)):
        prev_close = df['Close'].iloc[i - 1]
        close = df['Close'].iloc[i]
        volume = df['Volume'].iloc[i] if not pd.isna(df['Volume'].iloc[i]) else 0
        if close > prev_close:
            obv.append(obv[-1] + volume)
        elif close < prev_close:
            obv.append(obv[-1] - volume)
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index, dtype='float64')


def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: int = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    sma = series.rolling(window=window, min_periods=1).mean()
    std = series.rolling(window=window, min_periods=1).std(ddof=0)
    upper = sma + (std * num_std)
    lower = sma - (std * num_std)
    return upper, lower, sma


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    rsi = 100 - (100 / (1 + rs))
    rsi = pd.to_numeric(rsi, errors='coerce')
    return rsi.bfill().fillna(0.0)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['High']
    low = df['Low']
    close = df['Close']
    prev_close = close.shift(1)

    tr_components = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1)
    true_range = tr_components.max(axis=1)
    atr = true_range.rolling(window=period, min_periods=1).mean()
    return atr.bfill().fillna(0)


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: int = 3) -> Tuple[pd.Series, pd.Series]:
    atr = calculate_atr(df, period)
    hl2 = (df['High'] + df['Low']) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr

    supertrend = pd.Series(index=df.index, dtype='float64')
    direction = pd.Series(index=df.index, dtype='float64')

    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = hl2.iloc[i]
            direction.iloc[i] = 1
            continue

        prev_supertrend = supertrend.iloc[i - 1]
        prev_direction = direction.iloc[i - 1]

        if df['Close'].iloc[i] > upper_band.iloc[i - 1]:
            direction.iloc[i] = 1
            supertrend.iloc[i] = lower_band.iloc[i]
        elif df['Close'].iloc[i] < lower_band.iloc[i - 1]:
            direction.iloc[i] = -1
            supertrend.iloc[i] = upper_band.iloc[i]
        else:
            direction.iloc[i] = prev_direction
            if prev_direction == 1:
                supertrend.iloc[i] = min(lower_band.iloc[i], prev_supertrend)
            else:
                supertrend.iloc[i] = max(upper_band.iloc[i], prev_supertrend)

    direction = direction.fillna(0)
    supertrend = supertrend.bfill().ffill()
    return supertrend, direction


def compute_indicator_series(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """Compute indicator series needed for chart generation."""
    data = df.copy()
    data = data.sort_values('Date').reset_index(drop=True)
    data['Volume'] = data['Volume'].fillna(0)

    close = data['Close']
    indicators: Dict[str, pd.Series] = {}
    indicators['sma_20'] = close.rolling(window=20, min_periods=1).mean()
    indicators['sma_50'] = close.rolling(window=50, min_periods=1).mean()
    indicators['sma_200'] = close.rolling(window=200, min_periods=1).mean()

    bb_upper, bb_lower, bb_middle = calculate_bollinger_bands(close)
    indicators['bb_upper'] = bb_upper
    indicators['bb_lower'] = bb_lower
    indicators['bb_median'] = bb_middle

    macd_line, signal_line, histogram = calculate_macd(close)
    indicators['macd_line'] = macd_line
    indicators['signal_line'] = signal_line
    indicators['histogram'] = histogram

    indicators['rsi'] = calculate_rsi(close)
    indicators['atr'] = calculate_atr(data)

    supertrend, direction = calculate_supertrend(data)
    indicators['supertrend'] = supertrend
    indicators['supertrend_direction'] = direction

    indicators['obv'] = calculate_obv_series(data)
    indicators['volume_millions'] = data['Volume'] / 1_000_000

    return indicators


def build_chart_payload(df: pd.DataFrame) -> Dict[str, list]:
    """Return processed indicator lists for Plotly charts."""
    indicators = compute_indicator_series(df)
    obv_series = indicators['obv']
    _, obv_unit = normalize_value(obv_series.iloc[-1] if len(obv_series) else 0)
    scale = 1_000_000_000 if obv_unit == "B" else 1_000_000 if obv_unit == "M" else 1

    volume_series = indicators['volume_millions'].copy()

    return {
        'sma_20': _series_to_list(indicators['sma_20']),
        'sma_50': _series_to_list(indicators['sma_50']),
        'sma_200': _series_to_list(indicators['sma_200']),
        'bb_upper': _series_to_list(indicators['bb_upper']),
        'bb_lower': _series_to_list(indicators['bb_lower']),
        'bb_median': _series_to_list(indicators['bb_median']),
        'st_values': _series_to_list(indicators['supertrend']),
        'st_direction': [int(x) if not pd.isna(x) else 0 for x in indicators['supertrend_direction']],
        'macd_line': _series_to_list(indicators['macd_line']),
        'signal_line': _series_to_list(indicators['signal_line']),
        'histogram': _series_to_list(indicators['histogram']),
        'rsi': _series_to_list(indicators['rsi']),
        'atr': _series_to_list(indicators['atr']),
        'obv_normalized': _series_to_list(obv_series / scale),
        'obv_unit': obv_unit,
        'volume': volume_series
    }
