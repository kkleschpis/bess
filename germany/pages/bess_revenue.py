"""Tab 4: BESS Arbitrage & Revenue — spread analysis and revenue estimates."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import (
    _empty_figure,
    heatmap_chart,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import fetch_day_ahead_prices


def layout():
    controls = html.Div(
        [
            html.Div(
                [
                    html.Label(
                        "BESS Power (MW)",
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Input(
                        id="bess-mw",
                        type="number",
                        value=10,
                        min=1,
                        max=500,
                        step=1,
                        style={
                            "backgroundColor": COLORS[
                                "bg"
                            ],
                            "color": COLORS["text"],
                            "border": (
                                "1px solid "
                                + COLORS["card_border"]
                            ),
                            "borderRadius": "6px",
                            "padding": "8px 12px",
                            "width": "100px",
                        },
                    ),
                ],
                style={"marginRight": "24px"},
            ),
            html.Div(
                [
                    html.Label(
                        "Duration (hours)",
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Dropdown(
                        id="bess-duration",
                        options=[
                            {"label": "1h", "value": 1},
                            {"label": "2h", "value": 2},
                            {"label": "4h", "value": 4},
                        ],
                        value=2,
                        clearable=False,
                        style={
                            "width": "100px",
                            "backgroundColor": COLORS[
                                "bg"
                            ],
                            "color": COLORS["text"],
                        },
                    ),
                ],
                style={"marginRight": "24px"},
            ),
            html.Div(
                [
                    html.Label(
                        "Round-Trip Efficiency (%)",
                        style={
                            "color": COLORS["text_muted"],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Slider(
                        id="bess-efficiency",
                        min=70,
                        max=95,
                        step=1,
                        value=85,
                        marks={
                            70: "70%",
                            80: "80%",
                            85: "85%",
                            90: "90%",
                            95: "95%",
                        },
                        tooltip={
                            "placement": "bottom",
                            "always_visible": True,
                        },
                    ),
                ],
                style={
                    "flex": "1",
                    "minWidth": "200px",
                },
            ),
        ],
        style={
            **card_style(),
            "display": "flex",
            "alignItems": "flex-end",
        },
    )

    return html.Div(
        [
            controls,
            html.Div(id="bess-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="bess-spread-chart",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="bess-revenue-chart",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={**card_style(), "flex": "1"},
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
                            id="bess-volatility-chart",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="bess-optimal-chart",
                            config={
                                "displayModeBar": False
                            },
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                ],
                style={
                    "display": "flex",
                    "gap": "16px",
                },
            ),
            html.Div(
                dcc.Graph(
                    id="bess-monthly-chart",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("bess-kpis", "children"),
            Output("bess-spread-chart", "figure"),
            Output("bess-revenue-chart", "figure"),
            Output("bess-volatility-chart", "figure"),
            Output("bess-optimal-chart", "figure"),
            Output("bess-monthly-chart", "figure"),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
            Input("bess-mw", "value"),
            Input("bess-duration", "value"),
            Input("bess-efficiency", "value"),
        ],
    )
    def update_bess(
        start_date,
        end_date,
        mw,
        duration,
        efficiency,
    ):
        start = pd.Timestamp(start_date).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()
        df = fetch_day_ahead_prices(start, end)

        mw = mw or 10
        duration = duration or 2
        efficiency = (efficiency or 85) / 100.0
        mwh = mw * duration

        if df.empty:
            empty = _empty_figure("No Data")
            kpis = html.Div(
                [
                    html.Div(
                        kpi_card(
                            "Daily Spread", "N/A"
                        ),
                        style={"flex": "1"},
                    ),
                    html.Div(
                        kpi_card(
                            "Est. Daily Revenue",
                            "N/A",
                        ),
                        style={"flex": "1"},
                    ),
                    html.Div(
                        kpi_card(
                            "Profitable Days", "N/A"
                        ),
                        style={"flex": "1"},
                    ),
                    html.Div(
                        kpi_card(
                            "Best Spread", "N/A"
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

        # Daily min/max/spread
        df_daily = df.copy()
        df_daily["date"] = df_daily[
            "timestamp"
        ].dt.date
        daily = df_daily.groupby("date").agg(
            price_min=("price_eur_mwh", "min"),
            price_max=("price_eur_mwh", "max"),
            price_std=("price_eur_mwh", "std"),
        )
        daily["spread"] = (
            daily["price_max"] - daily["price_min"]
        )
        daily["revenue_1cycle"] = (
            daily["spread"] * mwh * efficiency
        )
        daily = daily.reset_index()

        avg_spread = daily["spread"].mean()
        avg_revenue = daily["revenue_1cycle"].mean()
        profitable = int(
            (daily["revenue_1cycle"] > 0).sum()
        )
        best_spread = daily["spread"].max()

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Avg Daily Spread",
                        f"{avg_spread:.1f} EUR/MWh",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Est. Daily Revenue (1 cycle)",
                        f"\u20ac{avg_revenue:,.0f}",
                        f"{mw} MW / {mwh} MWh"
                        f" / {efficiency*100:.0f}% eff",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Profitable Days",
                        f"{profitable}"
                        f" / {len(daily)}",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Best Daily Spread",
                        f"{best_spread:.1f} EUR/MWh",
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

        # Spread chart
        spread_fig = go.Figure()
        spread_fig.add_trace(
            go.Bar(
                x=daily["date"],
                y=daily["spread"],
                name="Spread",
                marker_color=COLORS["accent_amber"],
                marker_line_width=0,
                hovertemplate=(
                    "%{x}<br>"
                    "Spread: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        spread_fig.add_trace(
            go.Scatter(
                x=daily["date"],
                y=daily["price_min"],
                name="Min (Buy)",
                mode="markers",
                marker=dict(
                    color=COLORS["accent_green"],
                    size=6,
                ),
            )
        )
        spread_fig.add_trace(
            go.Scatter(
                x=daily["date"],
                y=daily["price_max"],
                name="Max (Sell)",
                mode="markers",
                marker=dict(
                    color=COLORS["accent_red"],
                    size=6,
                ),
            )
        )
        apply_theme(spread_fig)
        spread_fig.update_layout(
            title=dict(
                text="Daily Min/Max Price Spread",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(orientation="h", y=-0.15),
        )

        # Revenue chart (1-cycle and 2-cycle)
        rev_fig = go.Figure()
        rev_fig.add_trace(
            go.Bar(
                x=daily["date"],
                y=daily["revenue_1cycle"],
                name="1 Cycle/Day",
                marker_color=COLORS["accent_blue"],
                marker_line_width=0,
                hovertemplate=(
                    "%{x}<br>"
                    "Revenue: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        rev_fig.add_trace(
            go.Bar(
                x=daily["date"],
                y=daily["revenue_1cycle"] * 1.7,
                name="2 Cycles/Day (est.)",
                marker_color=COLORS["accent_cyan"],
                marker_line_width=0,
                opacity=0.6,
                hovertemplate=(
                    "%{x}<br>"
                    "Revenue: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(rev_fig)
        rev_fig.update_layout(
            title=dict(
                text="Estimated Arbitrage Revenue",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            barmode="group",
            legend=dict(orientation="h", y=-0.15),
        )

        # Volatility (std dev by day)
        vol_fig = go.Figure(
            go.Scatter(
                x=daily["date"],
                y=daily["price_std"],
                mode="lines+markers",
                line=dict(
                    color=COLORS["accent_purple"],
                    width=2,
                ),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(139,92,246,0.1)",
                hovertemplate=(
                    "%{x}<br>"
                    "Std Dev: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(vol_fig)
        vol_fig.update_layout(
            title=dict(
                text="Intraday Price Volatility"
                " (Std Dev)",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
        )

        # Optimal charge/discharge heatmap
        df_tmp = df.copy()
        df_tmp["hour"] = df_tmp["timestamp"].dt.hour
        df_tmp["date"] = df_tmp[
            "timestamp"
        ].dt.date.astype(str)
        pivot = df_tmp.pivot_table(
            values="price_eur_mwh",
            index="date",
            columns="hour",
            aggfunc="mean",
        )
        pivot = pivot.sort_index(ascending=True)
        hours = list(range(24))
        existing = [
            h for h in hours if h in pivot.columns
        ]

        opt_fig = heatmap_chart(
            z_data=pivot[existing].values,
            x_labels=[
                f"{h:02d}:00" for h in existing
            ],
            y_labels=list(pivot.index),
            title="Optimal Charge/Discharge Hours",
            colorscale="RdYlGn_r",
            z_label="EUR/MWh",
        )

        # Monthly revenue potential
        daily["month"] = pd.to_datetime(
            daily["date"]
        ).dt.to_period("M")
        monthly = (
            daily.groupby("month")
            .agg(
                total_revenue=(
                    "revenue_1cycle",
                    "sum",
                ),
                avg_spread=("spread", "mean"),
                days=("date", "count"),
            )
            .reset_index()
        )
        monthly["month"] = monthly["month"].astype(str)

        monthly_fig = go.Figure()
        monthly_fig.add_trace(
            go.Bar(
                x=monthly["month"],
                y=monthly["total_revenue"],
                name="Monthly Revenue",
                marker_color=COLORS["accent_green"],
                marker_line_width=0,
                hovertemplate=(
                    "%{x}<br>"
                    "Revenue: \u20ac%{y:,.0f}<br>"
                    "<extra></extra>"
                ),
            )
        )
        monthly_fig.add_trace(
            go.Scatter(
                x=monthly["month"],
                y=monthly["avg_spread"],
                name="Avg Spread",
                mode="lines+markers",
                line=dict(
                    color=COLORS["accent_amber"],
                    width=2.5,
                ),
                marker=dict(size=7),
                yaxis="y2",
            )
        )
        apply_theme(monthly_fig)
        monthly_fig.update_layout(
            title=dict(
                text="Monthly Revenue Potential",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            yaxis2=dict(
                title="Avg Spread (EUR/MWh)",
                overlaying="y",
                side="right",
                gridcolor="rgba(0,0,0,0)",
            ),
            legend=dict(orientation="h", y=-0.15),
        )

        return (
            kpis,
            spread_fig,
            rev_fig,
            vol_fig,
            opt_fig,
            monthly_fig,
        )
