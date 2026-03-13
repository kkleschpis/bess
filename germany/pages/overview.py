"""Tab 1: Market Overview — current snapshot of the German power market."""

from datetime import datetime, timedelta

import pandas as pd
from dash import Input, Output, callback, dcc, html

from components.charts import (
    generation_stacked_area,
    line_chart,
    price_bar_chart,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_day_ahead_prices,
    fetch_generation_by_source,
    fetch_total_load,
)
import plotly.graph_objects as go


def layout():
    return html.Div(
        [
            html.Div(id="overview-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="overview-price-chart",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="overview-gen-chart",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                ],
                style={"display": "flex", "gap": "16px"},
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="overview-residual-chart",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="overview-trend-chart",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                ],
                style={"display": "flex", "gap": "16px"},
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("overview-kpis", "children"),
            Output("overview-price-chart", "figure"),
            Output("overview-gen-chart", "figure"),
            Output("overview-residual-chart", "figure"),
            Output("overview-trend-chart", "figure"),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_overview(start_date, end_date):
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)
        start_dt = start.to_pydatetime()
        end_dt = end.to_pydatetime()

        prices = fetch_day_ahead_prices(start_dt, end_dt)
        gen = fetch_generation_by_source(start_dt, end_dt)
        load = fetch_total_load(start_dt, end_dt)

        # KPIs
        if not prices.empty:
            current_price = (
                f"{prices['price_eur_mwh'].iloc[-1]:.1f}"
            )
            price_min = f"{prices['price_eur_mwh'].min():.1f}"
            price_max = f"{prices['price_eur_mwh'].max():.1f}"
            price_range = f"{price_min} / {price_max}"
        else:
            current_price = "N/A"
            price_range = "N/A"

        wind_solar_avg = "N/A"
        if not gen.empty:
            ws_cols = [
                c
                for c in [
                    "solar",
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in gen.columns
            ]
            if ws_cols:
                avg_ws = gen[ws_cols].sum(axis=1).mean()
                wind_solar_avg = f"{avg_ws:,.0f} MW"

        residual_val = "N/A"
        if not load.empty and not gen.empty:
            merged = pd.merge_asof(
                load.sort_values("timestamp"),
                gen[
                    ["timestamp"]
                    + [
                        c
                        for c in [
                            "solar",
                            "wind_onshore",
                            "wind_offshore",
                        ]
                        if c in gen.columns
                    ]
                ].sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            ws = [
                c
                for c in [
                    "solar",
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in merged.columns
            ]
            merged["residual"] = (
                merged["load_mw"] - merged[ws].sum(axis=1)
            )
            residual_val = (
                f"{merged['residual'].iloc[-1]:,.0f} MW"
            )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Current DA Price",
                        f"{current_price} EUR/MWh",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Price Range (Min/Max)",
                        price_range,
                        "EUR/MWh",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg Wind + Solar",
                        wind_solar_avg,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Residual Load",
                        residual_val,
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

        # Today's price chart
        today = datetime.now().date()
        today_prices = prices[
            prices["timestamp"].dt.date == today
        ]
        if today_prices.empty:
            today_prices = prices.tail(24)
        price_fig = price_bar_chart(
            today_prices, "Today's Day-Ahead Prices"
        )

        # Generation stacked area (last 24h subset)
        gen_24h = gen.tail(96)  # 96 x 15min = 24h
        gen_fig = generation_stacked_area(
            gen_24h, "Generation Mix (Last 24h)"
        )

        # Residual load chart
        if not load.empty and not gen.empty:
            merged = pd.merge_asof(
                load.sort_values("timestamp"),
                gen[
                    ["timestamp"]
                    + [
                        c
                        for c in [
                            "solar",
                            "wind_onshore",
                            "wind_offshore",
                        ]
                        if c in gen.columns
                    ]
                ].sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            ws = [
                c
                for c in [
                    "solar",
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in merged.columns
            ]
            merged["residual_load"] = (
                merged["load_mw"] - merged[ws].sum(axis=1)
            )
            merged_24h = merged.tail(96)

            res_fig = go.Figure()
            res_fig.add_trace(
                go.Scatter(
                    x=merged_24h["timestamp"],
                    y=merged_24h["residual_load"],
                    mode="lines",
                    fill="tozeroy",
                    line=dict(
                        color=COLORS["accent_cyan"],
                        width=2,
                    ),
                    fillcolor="rgba(6, 182, 212, 0.15)",
                    hovertemplate=(
                        "%{x|%H:%M}<br>"
                        "%{y:,.0f} MW<extra></extra>"
                    ),
                )
            )
            # Highlight negative residual (excess renewables)
            neg = merged_24h[
                merged_24h["residual_load"] < 0
            ]
            if not neg.empty:
                res_fig.add_trace(
                    go.Scatter(
                        x=neg["timestamp"],
                        y=neg["residual_load"],
                        mode="markers",
                        marker=dict(
                            color=COLORS["accent_green"],
                            size=5,
                        ),
                        name="Charge Zone",
                        hovertemplate=(
                            "Charge: %{y:,.0f} MW"
                            "<extra></extra>"
                        ),
                    )
                )
            apply_theme(res_fig)
            res_fig.update_layout(
                title=dict(
                    text="Residual Load (Last 24h)",
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                showlegend=False,
            )
        else:
            from components.charts import (
                _empty_figure,
            )

            res_fig = _empty_figure("Residual Load")

        # 7-day price trend
        trend_fig = line_chart(
            prices,
            "timestamp",
            "price_eur_mwh",
            title="Price Trend",
            y_title="EUR/MWh",
            color=COLORS["accent_blue"],
        )

        return kpis, price_fig, gen_fig, res_fig, trend_fig
