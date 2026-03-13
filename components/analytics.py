"""Shared strategic analysis functions for trend and derivative computation."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from components.theme import COLORS


def compute_linear_trend(
    series: pd.Series,
) -> tuple[float, float, float]:
    """Compute linear regression on a series.

    Args:
        series: Values indexed by position (0, 1, 2...).

    Returns:
        (slope, intercept, r_squared)
    """
    y = series.dropna().values
    if len(y) < 2:
        return 0.0, 0.0, 0.0
    x = np.arange(len(y), dtype=float)
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs[0], coeffs[1]
    y_pred = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_pred) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = (
        1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    )
    return float(slope), float(intercept), float(r_squared)


def compute_monthly_derivative(
    series: pd.Series,
) -> pd.Series:
    """Compute first derivative (month-over-month change).

    Args:
        series: Monthly values.

    Returns:
        Series of MoM changes (same length, first is NaN).
    """
    return series.diff()


def compute_acceleration(
    series: pd.Series,
) -> pd.Series:
    """Compute second derivative (change of the change).

    Args:
        series: Monthly values.

    Returns:
        Series of acceleration values.
    """
    return series.diff().diff()


def compute_rolling_stats(
    series: pd.Series, window: int = 3
) -> tuple[pd.Series, pd.Series]:
    """Compute rolling mean and std for smoothing.

    Args:
        series: Input values.
        window: Rolling window size.

    Returns:
        (rolling_mean, rolling_std)
    """
    return (
        series.rolling(window, min_periods=1).mean(),
        series.rolling(window, min_periods=1).std(),
    )


def compute_yoy_comparison(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
) -> pd.DataFrame:
    """Compute year-over-year comparison.

    Args:
        df: DataFrame with date and value columns.
        date_col: Name of datetime column.
        value_col: Name of value column.

    Returns:
        DataFrame with month, current_year, prior_year
        columns.
    """
    tmp = df.copy()
    tmp["year"] = tmp[date_col].dt.year
    tmp["month"] = tmp[date_col].dt.month
    years = sorted(tmp["year"].unique())
    if len(years) < 2:
        return pd.DataFrame()
    current_year = years[-1]
    prior_year = years[-2]
    current = (
        tmp[tmp["year"] == current_year]
        .groupby("month")[value_col]
        .mean()
        .reset_index()
        .rename(columns={value_col: "current_year"})
    )
    prior = (
        tmp[tmp["year"] == prior_year]
        .groupby("month")[value_col]
        .mean()
        .reset_index()
        .rename(columns={value_col: "prior_year"})
    )
    merged = pd.merge(
        current, prior, on="month", how="outer"
    )
    merged["current_label"] = str(current_year)
    merged["prior_label"] = str(prior_year)
    return merged.sort_values("month")


def add_trendline_trace(
    fig: go.Figure,
    x: np.ndarray | pd.Series,
    y: np.ndarray | pd.Series,
    color: str = COLORS["accent_red"],
    name: str = "Trend",
    dash: str = "dash",
) -> tuple[float, float]:
    """Add a linear regression trendline to a Plotly figure.

    Args:
        fig: Plotly figure to add trace to.
        x: X-axis values (numeric or datetime).
        y: Y-axis values.
        color: Line color.
        name: Trace name.
        dash: Line dash style.

    Returns:
        (slope, r_squared) of the trendline.
    """
    y_arr = np.array(y, dtype=float)
    mask = ~np.isnan(y_arr)
    if mask.sum() < 2:
        return 0.0, 0.0

    x_num = np.arange(len(y_arr), dtype=float)
    y_clean = y_arr[mask]
    x_clean = x_num[mask]

    coeffs = np.polyfit(x_clean, y_clean, 1)
    slope = coeffs[0]
    y_trend = np.polyval(coeffs, x_num)

    ss_res = np.sum(
        (y_clean - np.polyval(coeffs, x_clean)) ** 2
    )
    ss_tot = np.sum(
        (y_clean - np.mean(y_clean)) ** 2
    )
    r_sq = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    fig.add_trace(
        go.Scatter(
            x=list(x),
            y=y_trend.tolist(),
            mode="lines",
            name=name,
            line=dict(
                color=color, width=2, dash=dash
            ),
            hovertemplate=(
                f"{name}: %{{y:.2f}}<extra></extra>"
            ),
        )
    )
    return float(slope), float(r_sq)


def add_projection_trace(
    fig: go.Figure,
    x_hist: list,
    y_hist: np.ndarray | pd.Series,
    n_future: int = 12,
    color: str = COLORS["accent_cyan"],
    name: str = "Projection",
) -> None:
    """Add a projected trendline extending into the future.

    Args:
        fig: Plotly figure.
        x_hist: Historical x values (datetimes).
        y_hist: Historical y values.
        n_future: Number of future periods.
        color: Line color.
        name: Trace name.
    """
    y_arr = np.array(y_hist, dtype=float)
    mask = ~np.isnan(y_arr)
    if mask.sum() < 2:
        return

    x_num = np.arange(len(y_arr), dtype=float)
    coeffs = np.polyfit(x_num[mask], y_arr[mask], 1)

    x_future = np.arange(
        len(y_arr), len(y_arr) + n_future, dtype=float
    )
    y_future = np.polyval(coeffs, x_future)

    if hasattr(x_hist[0], "freq") or isinstance(
        x_hist[0], pd.Timestamp
    ):
        last = pd.Timestamp(x_hist[-1])
        future_dates = pd.date_range(
            last + pd.DateOffset(months=1),
            periods=n_future,
            freq="MS",
        )
        x_proj = list(future_dates)
    else:
        x_proj = list(range(
            len(y_arr), len(y_arr) + n_future
        ))

    fig.add_trace(
        go.Scatter(
            x=x_proj,
            y=y_future.tolist(),
            mode="lines",
            name=name,
            line=dict(
                color=color, width=2, dash="dot"
            ),
            hovertemplate=(
                f"{name}: %{{y:.2f}}<extra></extra>"
            ),
        )
    )


def trend_arrow(
    current: float, previous: float
) -> tuple[str, str]:
    """Return trend arrow and color for KPI display.

    Args:
        current: Current period value.
        previous: Previous period value.

    Returns:
        (arrow_str, color) e.g. ("  +2.3", "#10b981")
    """
    if previous == 0 or np.isnan(previous):
        return "", COLORS["text_muted"]
    delta = current - previous
    if abs(delta) < 0.01:
        return " \u2192 0.0", COLORS["text_muted"]
    arrow = "\u2191" if delta > 0 else "\u2193"
    color = (
        COLORS["accent_green"]
        if delta > 0
        else COLORS["accent_red"]
    )
    return f" {arrow} {delta:+.1f}", color


def trend_arrow_pct(
    current: float, previous: float
) -> tuple[str, str]:
    """Return trend arrow with percentage change.

    Args:
        current: Current period value.
        previous: Previous period value.

    Returns:
        (arrow_str, color)
    """
    if previous == 0 or np.isnan(previous):
        return "", COLORS["text_muted"]
    pct = (current - previous) / abs(previous) * 100
    if abs(pct) < 0.1:
        return " \u2192 0.0%", COLORS["text_muted"]
    arrow = "\u2191" if pct > 0 else "\u2193"
    color = (
        COLORS["accent_green"]
        if pct > 0
        else COLORS["accent_red"]
    )
    return f" {arrow} {pct:+.1f}%", color


def strategic_signal(
    slope: float,
    threshold_good: float,
    threshold_bad: float,
    higher_is_better: bool = True,
) -> tuple[str, str]:
    """Classify a trend slope into a strategic signal.

    Returns:
        (label, color) — e.g. ("Strong", "#10b981")
    """
    if higher_is_better:
        if slope >= threshold_good:
            return "Strong", COLORS["accent_green"]
        if slope >= threshold_bad:
            return "Moderate", COLORS["accent_amber"]
        return "Weak", COLORS["accent_red"]
    else:
        if slope <= threshold_good:
            return "Strong", COLORS["accent_green"]
        if slope <= threshold_bad:
            return "Moderate", COLORS["accent_amber"]
        return "Weak", COLORS["accent_red"]
