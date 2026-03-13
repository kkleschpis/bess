"""Shared chart creation utilities."""

import numpy as np
import plotly.graph_objects as go

from components.theme import (
    COLORS,
    SOURCE_COLORS,
    SOURCE_LABELS,
    apply_theme,
)


def price_bar_chart(df, title="Day-Ahead Prices"):
    """Hourly DA price bar chart, color-coded by price level.

    Expects df with columns: timestamp, price_eur_mwh
    """
    if df.empty:
        return _empty_figure(title)

    colors = []
    for p in df["price_eur_mwh"]:
        if p < 0:
            colors.append(COLORS["accent_red"])
        elif p < 40:
            colors.append(COLORS["accent_green"])
        elif p < 80:
            colors.append(COLORS["accent_blue"])
        elif p < 150:
            colors.append(COLORS["accent_amber"])
        else:
            colors.append(COLORS["accent_red"])

    fig = go.Figure(
        go.Bar(
            x=df["timestamp"],
            y=df["price_eur_mwh"],
            marker_color=colors,
            marker_line_width=0,
            hovertemplate=(
                "%{x|%Y-%m-%d %H:%M}<br>"
                "%{y:.1f} EUR/MWh<extra></extra>"
            ),
        )
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        yaxis=dict(title="EUR/MWh"),
        xaxis=dict(title=""),
    )
    return fig


def generation_stacked_area(
    df, title="Generation Mix", source_order=None
):
    """Stacked area chart of generation by source.

    Expects df with timestamp column and source columns.
    """
    if df.empty:
        return _empty_figure(title)

    fig = go.Figure()
    source_cols = [
        c for c in df.columns if c != "timestamp"
    ]
    # Default order for Germany; callers can override
    if source_order is None:
        source_order = [
            "solar",
            "wind_onshore",
            "wind_offshore",
            "biomass",
            "hydro",
            "nuclear",
            "lignite",
            "hard_coal",
            "gas",
            "oil",
            "pumped_storage",
            "geothermal",
            "other",
        ]
    ordered = [
        c for c in source_order if c in source_cols
    ]

    for col in ordered:
        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df[col],
                name=SOURCE_LABELS.get(col, col),
                mode="lines",
                line=dict(width=0),
                fillcolor=SOURCE_COLORS.get(
                    col, COLORS["accent_blue"]
                ),
                stackgroup="gen",
                hovertemplate=(
                    f"{SOURCE_LABELS.get(col, col)}: "
                    "%{y:,.0f} MW<extra></extra>"
                ),
            )
        )

    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        yaxis=dict(title="MW"),
        xaxis=dict(title=""),
        hovermode="x unified",
    )
    return fig


def line_chart(
    df,
    x_col,
    y_col,
    title="",
    y_title="",
    color=None,
):
    """Simple line chart."""
    if df.empty:
        return _empty_figure(title)

    fig = go.Figure(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines",
            line=dict(
                color=color or COLORS["accent_blue"],
                width=2,
            ),
            hovertemplate="%{x|%Y-%m-%d %H:%M}<br>"
            "%{y:.1f}<extra></extra>",
        )
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        yaxis=dict(title=y_title),
    )
    return fig


def heatmap_chart(
    z_data,
    x_labels,
    y_labels,
    title="",
    colorscale="RdYlGn_r",
    z_label="EUR/MWh",
):
    """Generic heatmap chart.

    Args:
        z_data: 2D array (rows=y, cols=x).
        x_labels: X-axis tick labels.
        y_labels: Y-axis tick labels.
        title: Chart title.
        colorscale: Plotly colorscale name.
        z_label: Colorbar title.
    """
    fig = go.Figure(
        go.Heatmap(
            z=z_data,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            colorbar=dict(
                title=dict(
                    text=z_label,
                    font=dict(color=COLORS["text_muted"]),
                ),
                tickfont=dict(color=COLORS["text_muted"]),
            ),
            hovertemplate=(
                "Hour: %{x}<br>Date: %{y}<br>"
                f"{z_label}: %{{z:.1f}}<extra></extra>"
            ),
        )
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
    )
    return fig


def build_price_heatmap(df):
    """Build a price heatmap from hourly price data.

    Args:
        df: DataFrame with timestamp and price_eur_mwh.

    Returns:
        Plotly figure with hour-of-day x date heatmap.
    """
    if df.empty:
        return _empty_figure("Price Heatmap")

    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date.astype(str)

    pivot = df.pivot_table(
        values="price_eur_mwh",
        index="date",
        columns="hour",
        aggfunc="mean",
    )
    pivot = pivot.sort_index(ascending=True)

    hours = list(range(24))
    existing_hours = [h for h in hours if h in pivot.columns]
    z_data = pivot[existing_hours].values

    return heatmap_chart(
        z_data=z_data,
        x_labels=[f"{h:02d}:00" for h in existing_hours],
        y_labels=list(pivot.index),
        title="Price Heatmap (EUR/MWh by Hour & Date)",
        colorscale="RdYlGn_r",
        z_label="EUR/MWh",
    )


def scatter_chart(
    df,
    x_col,
    y_col,
    title="",
    x_title="",
    y_title="",
):
    """Simple scatter plot."""
    if df.empty:
        return _empty_figure(title)

    fig = go.Figure(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="markers",
            marker=dict(
                color=COLORS["accent_cyan"],
                size=4,
                opacity=0.6,
            ),
            hovertemplate=(
                f"{x_title}: %{{x:.0f}}<br>"
                f"{y_title}: %{{y:.1f}}<extra></extra>"
            ),
        )
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        xaxis=dict(title=x_title),
        yaxis=dict(title=y_title),
    )
    return fig


def bar_chart(
    x,
    y,
    title="",
    y_title="",
    color=None,
    horizontal=False,
):
    """Simple bar chart from lists/arrays."""
    if horizontal:
        fig = go.Figure(
            go.Bar(
                y=x,
                x=y,
                orientation="h",
                marker_color=color or COLORS["accent_blue"],
                marker_line_width=0,
            )
        )
    else:
        fig = go.Figure(
            go.Bar(
                x=x,
                y=y,
                marker_color=color or COLORS["accent_blue"],
                marker_line_width=0,
            )
        )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        yaxis=dict(title=y_title),
    )
    return fig


def _empty_figure(title="No Data"):
    """Return an empty themed figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data available for selected period",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(color=COLORS["text_muted"], size=14),
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig
