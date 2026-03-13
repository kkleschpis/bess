"""Tab 3: Price Structure Evolution — how are price patterns evolving?"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_trendline_trace,
    compute_linear_trend,
    trend_arrow,
)
from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import fetch_day_ahead_prices


def layout():
    return html.Div(
        [
            html.Div(id="es-prices-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-prices-spread-trend",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={
                            **card_style(),
                            "flex": "1",
                        },
                    ),
                    html.Div(
                        dcc.Graph(
                            id="es-prices-volatility",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={
                            **card_style(),
                            "flex": "1",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "16px",
                },
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-prices-neg-hours",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={
                            **card_style(),
                            "flex": "1",
                        },
                    ),
                    html.Div(
                        dcc.Graph(
                            id="es-prices-cannibalization",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={
                            **card_style(),
                            "flex": "1",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "16px",
                },
            ),
            html.Div(
                dcc.Graph(
                    id="es-prices-duration-comp",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("es-prices-kpis", "children"),
            Output(
                "es-prices-spread-trend", "figure"
            ),
            Output(
                "es-prices-volatility", "figure"
            ),
            Output(
                "es-prices-neg-hours", "figure"
            ),
            Output(
                "es-prices-cannibalization",
                "figure",
            ),
            Output(
                "es-prices-duration-comp", "figure"
            ),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_prices(start_date, end_date):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()
        df = fetch_day_ahead_prices(start, end)

        if df.empty:
            empty = _empty_figure("No Data")
            kpis = html.Div(
                [
                    html.Div(
                        kpi_card(
                            "Spread Trend", "N/A"
                        ),
                        style={"flex": "1"},
                    ),
                    html.Div(
                        kpi_card(
                            "Volatility", "N/A"
                        ),
                        style={"flex": "1"},
                    ),
                    html.Div(
                        kpi_card(
                            "Neg Hours", "N/A"
                        ),
                        style={"flex": "1"},
                    ),
                    html.Div(
                        kpi_card(
                            "Midday Price", "N/A"
                        ),
                        style={"flex": "1"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "16px",
                    "marginBottom": "16px",
                },
            )
            return (
                kpis,
                empty,
                empty,
                empty,
                empty,
                empty,
            )

        p = df.copy()
        p["month"] = p[
            "timestamp"
        ].dt.to_period("M")
        p["hour"] = p["timestamp"].dt.hour

        # Monthly aggregations
        peak = (
            p[p["hour"].between(8, 19)]
            .groupby("month")["price_eur_mwh"]
            .mean()
        )
        offpeak = (
            p[~p["hour"].between(8, 19)]
            .groupby("month")["price_eur_mwh"]
            .mean()
        )
        spread_monthly = pd.DataFrame({
            "month": peak.index,
            "spread": (
                peak.values
                - offpeak.reindex(
                    peak.index
                ).values
            ),
        }).dropna()
        spread_monthly["month_dt"] = spread_monthly[
            "month"
        ].apply(lambda x: x.to_timestamp())

        vol_monthly = (
            p.groupby("month")["price_eur_mwh"]
            .std()
            .reset_index(name="std")
        )
        vol_monthly["month_dt"] = vol_monthly[
            "month"
        ].apply(lambda x: x.to_timestamp())

        neg_monthly = (
            p[p["price_eur_mwh"] < 0]
            .groupby("month")
            .size()
            .reset_index(name="neg_hours")
        )
        neg_monthly["month_dt"] = neg_monthly[
            "month"
        ].apply(lambda x: x.to_timestamp())

        # Midday vs morning/evening
        midday = (
            p[p["hour"].between(11, 15)]
            .groupby("month")["price_eur_mwh"]
            .mean()
            .reset_index(name="midday")
        )
        moreve = (
            p[
                p["hour"].between(7, 10)
                | p["hour"].between(17, 21)
            ]
            .groupby("month")["price_eur_mwh"]
            .mean()
            .reset_index(name="moreve")
        )
        cannibal = pd.merge(
            midday, moreve, on="month"
        )
        cannibal["month_dt"] = cannibal[
            "month"
        ].apply(lambda x: x.to_timestamp())

        # --- KPIs ---
        spread_slope, _, _ = compute_linear_trend(
            spread_monthly["spread"]
        )
        vol_slope, _, _ = compute_linear_trend(
            vol_monthly["std"]
        )
        if not neg_monthly.empty:
            neg_slope, _, _ = compute_linear_trend(
                neg_monthly["neg_hours"].astype(
                    float
                )
            )
        else:
            neg_slope = 0.0

        midday_slope = 0.0
        if not cannibal.empty:
            midday_slope, _, _ = (
                compute_linear_trend(
                    cannibal["midday"]
                )
            )

        vol_dir = (
            "Increasing"
            if vol_slope > 0.1
            else (
                "Decreasing"
                if vol_slope < -0.1
                else "Stable"
            )
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Spread Trend",
                        f"{spread_slope:.2f}"
                        " EUR/MWh/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Volatility Trend",
                        vol_dir,
                        f"{vol_slope:+.2f}/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Neg Hours Growth",
                        f"{neg_slope:+.1f} hrs/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Midday Depression",
                        f"{midday_slope * 12:.1f}"
                        " EUR/MWh/yr",
                    ),
                    style={"flex": "1"},
                ),
            ],
            style={
                "display": "flex",
                "gap": "16px",
                "marginBottom": "16px",
            },
        )

        # --- Chart 1: Monthly Spread with Trend ---
        spread_fig = go.Figure()
        spread_fig.add_trace(
            go.Bar(
                x=spread_monthly["month_dt"],
                y=spread_monthly["spread"],
                marker_color=COLORS[
                    "accent_amber"
                ],
                marker_line_width=0,
                name="Spread",
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Spread: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            spread_fig,
            spread_monthly["month_dt"],
            spread_monthly["spread"],
            color=COLORS["accent_red"],
            name="Trend",
        )
        apply_theme(spread_fig)
        spread_fig.update_layout(
            title=dict(
                text=(
                    "Monthly Peak/Off-Peak Spread"
                    " + Trend"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 2: Monthly Volatility ---
        vol_fig = go.Figure()
        vol_fig.add_trace(
            go.Scatter(
                x=vol_monthly["month_dt"],
                y=vol_monthly["std"],
                mode="lines+markers",
                line=dict(
                    color=COLORS[
                        "accent_purple"
                    ],
                    width=2,
                ),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor=(
                    "rgba(139,92,246,0.1)"
                ),
                name="Std Dev",
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Std Dev: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            vol_fig,
            vol_monthly["month_dt"],
            vol_monthly["std"],
            color=COLORS["accent_red"],
            name="Trend",
        )
        apply_theme(vol_fig)
        vol_fig.update_layout(
            title=dict(
                text=(
                    "Monthly Price Volatility"
                    " (Std Dev) + Trend"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 3: Negative Price Hours ---
        if not neg_monthly.empty:
            colors = [
                COLORS["accent_red"]
            ] * len(neg_monthly)
            neg_fig = go.Figure()
            neg_fig.add_trace(
                go.Bar(
                    x=neg_monthly["month_dt"],
                    y=neg_monthly["neg_hours"],
                    marker_color=colors,
                    marker_line_width=0,
                    name="Neg Hours",
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "%{y} hours"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                neg_fig,
                neg_monthly["month_dt"],
                neg_monthly["neg_hours"].astype(
                    float
                ),
                color=COLORS["accent_cyan"],
                name="Trend",
            )
            apply_theme(neg_fig)
            neg_fig.update_layout(
                title=dict(
                    text=(
                        "Negative Price Hours"
                        " per Month + Trend"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="Hours"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            neg_fig = go.Figure()
            neg_fig.add_annotation(
                text="No negative price hours",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(
                    color=COLORS["text_muted"],
                    size=14,
                ),
            )
            apply_theme(neg_fig)
            neg_fig.update_layout(
                title=dict(
                    text="Negative Price Hours",
                    font=dict(size=15),
                ),
            )

        # --- Chart 4: Solar Cannibalisation ---
        if not cannibal.empty:
            cann_fig = go.Figure()
            cann_fig.add_trace(
                go.Scatter(
                    x=cannibal["month_dt"],
                    y=cannibal["midday"],
                    name="Midday (11-15h)",
                    mode="lines+markers",
                    line=dict(
                        color=COLORS[
                            "accent_amber"
                        ],
                        width=2.5,
                    ),
                    marker=dict(size=5),
                )
            )
            cann_fig.add_trace(
                go.Scatter(
                    x=cannibal["month_dt"],
                    y=cannibal["moreve"],
                    name="Morn/Eve (7-10h, 17-21h)",
                    mode="lines+markers",
                    line=dict(
                        color=COLORS[
                            "accent_blue"
                        ],
                        width=2.5,
                    ),
                    marker=dict(size=5),
                )
            )
            add_trendline_trace(
                cann_fig,
                cannibal["month_dt"],
                cannibal["midday"],
                color=COLORS["accent_amber"],
                name="Midday Trend",
                dash="dot",
            )
            apply_theme(cann_fig)
            cann_fig.update_layout(
                title=dict(
                    text=(
                        "Solar Cannibalisation"
                        " \u2014 Midday vs"
                        " Morning/Evening"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="EUR/MWh"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
                hovermode="x unified",
            )
        else:
            cann_fig = _empty_figure(
                "Solar Cannibalisation"
            )

        # --- Chart 5: Duration Curve Comparison ---
        quarters = p.copy()
        quarters["quarter"] = (
            quarters["timestamp"]
            .dt.to_period("Q")
            .astype(str)
        )
        unique_q = sorted(
            quarters["quarter"].unique()
        )

        dur_fig = go.Figure()
        # Pick first, middle, and last quarter
        q_select = []
        if len(unique_q) >= 3:
            q_select = [
                unique_q[0],
                unique_q[len(unique_q) // 2],
                unique_q[-1],
            ]
        elif len(unique_q) >= 1:
            q_select = unique_q

        q_colors = [
            COLORS["accent_blue"],
            COLORS["accent_amber"],
            COLORS["accent_green"],
        ]

        for i, q in enumerate(q_select):
            q_data = quarters[
                quarters["quarter"] == q
            ]["price_eur_mwh"].dropna()
            if q_data.empty:
                continue
            sorted_prices = np.sort(
                q_data.values
            )[::-1]
            pct = np.linspace(
                0, 100, len(sorted_prices)
            )
            dur_fig.add_trace(
                go.Scatter(
                    x=pct,
                    y=sorted_prices,
                    mode="lines",
                    name=q,
                    line=dict(
                        color=q_colors[
                            i % len(q_colors)
                        ],
                        width=2,
                    ),
                    hovertemplate=(
                        f"{q}: %{{y:.1f}} EUR/MWh"
                        "<extra></extra>"
                    ),
                )
            )

        dur_fig.add_hline(
            y=0,
            line_dash="dash",
            line_color=COLORS["accent_red"],
            line_width=1,
        )
        apply_theme(dur_fig)
        dur_fig.update_layout(
            title=dict(
                text=(
                    "Price Duration Curve"
                    " \u2014 Quarter Comparison"
                ),
                font=dict(size=15),
            ),
            xaxis=dict(title="% of Hours"),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        return (
            kpis,
            spread_fig,
            vol_fig,
            neg_fig,
            cann_fig,
            dur_fig,
        )
