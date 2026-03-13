"""Tab 2: Price Analysis — DA prices, heatmaps, spreads."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from components.charts import (
    build_price_heatmap,
    line_chart,
    price_bar_chart,
    _empty_figure,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import fetch_day_ahead_prices


def layout():
    return html.Div(
        [
            html.Div(id="prices-kpis"),
            html.Div(
                dcc.Graph(
                    id="prices-timeseries",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="prices-heatmap",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="prices-duration",
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
                            id="prices-spread",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="prices-negative",
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
            Output("prices-kpis", "children"),
            Output("prices-timeseries", "figure"),
            Output("prices-heatmap", "figure"),
            Output("prices-duration", "figure"),
            Output("prices-spread", "figure"),
            Output("prices-negative", "figure"),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_prices(start_date, end_date):
        start = pd.Timestamp(start_date).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()
        df = fetch_day_ahead_prices(start, end)

        # KPIs
        if not df.empty:
            avg_price = df["price_eur_mwh"].mean()
            max_price = df["price_eur_mwh"].max()
            neg_hours = int(
                (df["price_eur_mwh"] < 0).sum()
            )

            # Peak/off-peak
            df_tmp = df.copy()
            df_tmp["hour"] = df_tmp["timestamp"].dt.hour
            peak = df_tmp[
                df_tmp["hour"].between(8, 19)
            ]["price_eur_mwh"].mean()
            offpeak = df_tmp[
                ~df_tmp["hour"].between(8, 19)
            ]["price_eur_mwh"].mean()
            spread = peak - offpeak

            avg_str = f"{avg_price:.1f} EUR/MWh"
            spread_str = f"{spread:.1f} EUR/MWh"
            neg_str = str(neg_hours)
            max_str = f"{max_price:.1f} EUR/MWh"
        else:
            avg_str = "N/A"
            spread_str = "N/A"
            neg_str = "N/A"
            max_str = "N/A"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card("Avg Price", avg_str),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Peak/Off-Peak Spread",
                        spread_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Negative Price Hours", neg_str
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card("Max Price", max_str),
                    style={"flex": "1"},
                ),
            ],
            style={
                "display": "flex",
                "gap": "16px",
                "marginBottom": "16px",
            },
        )

        # Timeseries
        ts_fig = price_bar_chart(
            df, "Hourly Day-Ahead Prices"
        )

        # Heatmap
        hm_fig = build_price_heatmap(df)

        # Duration curve
        if not df.empty:
            sorted_prices = np.sort(
                df["price_eur_mwh"].dropna().values
            )[::-1]
            pct = np.linspace(0, 100, len(sorted_prices))
            dur_fig = go.Figure(
                go.Scatter(
                    x=pct,
                    y=sorted_prices,
                    mode="lines",
                    line=dict(
                        color=COLORS["accent_blue"],
                        width=2,
                    ),
                    fill="tozeroy",
                    fillcolor="rgba(59,130,246,0.1)",
                    hovertemplate=(
                        "%{x:.0f}% of hours<br>"
                        "%{y:.1f} EUR/MWh"
                        "<extra></extra>"
                    ),
                )
            )
            dur_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color=COLORS["accent_red"],
                annotation_text="0 EUR/MWh",
                annotation_font_color=COLORS[
                    "accent_red"
                ],
            )
            apply_theme(dur_fig)
            dur_fig.update_layout(
                title=dict(
                    text="Price Duration Curve",
                    font=dict(size=15),
                ),
                xaxis=dict(title="% of Hours"),
                yaxis=dict(title="EUR/MWh"),
            )
        else:
            dur_fig = _empty_figure("Price Duration Curve")

        # Peak vs off-peak spread over time
        if not df.empty:
            df_tmp = df.copy()
            df_tmp["date"] = df_tmp[
                "timestamp"
            ].dt.date
            df_tmp["hour"] = df_tmp["timestamp"].dt.hour
            daily = df_tmp.groupby("date").apply(
                lambda g: pd.Series({
                    "peak": g[g["hour"].between(8, 19)][
                        "price_eur_mwh"
                    ].mean(),
                    "offpeak": g[
                        ~g["hour"].between(8, 19)
                    ]["price_eur_mwh"].mean(),
                }),
                include_groups=False,
            )
            daily["spread"] = (
                daily["peak"] - daily["offpeak"]
            )
            daily = daily.reset_index()

            spread_fig = go.Figure()
            spread_fig.add_trace(
                go.Bar(
                    x=daily["date"],
                    y=daily["spread"],
                    marker_color=COLORS["accent_amber"],
                    marker_line_width=0,
                    hovertemplate=(
                        "%{x}<br>Spread: %{y:.1f}"
                        " EUR/MWh<extra></extra>"
                    ),
                )
            )
            apply_theme(spread_fig)
            spread_fig.update_layout(
                title=dict(
                    text="Daily Peak/Off-Peak Spread",
                    font=dict(size=15),
                ),
                yaxis=dict(title="EUR/MWh"),
            )
        else:
            spread_fig = _empty_figure(
                "Peak/Off-Peak Spread"
            )

        # Negative price hours by month
        if not df.empty:
            df_tmp = df.copy()
            df_tmp["month"] = df_tmp[
                "timestamp"
            ].dt.to_period("M")
            neg_by_month = (
                df_tmp[df_tmp["price_eur_mwh"] < 0]
                .groupby("month")
                .size()
                .reset_index(name="neg_hours")
            )
            neg_by_month["month"] = neg_by_month[
                "month"
            ].astype(str)

            if not neg_by_month.empty:
                neg_fig = go.Figure(
                    go.Bar(
                        x=neg_by_month["month"],
                        y=neg_by_month["neg_hours"],
                        marker_color=COLORS[
                            "accent_red"
                        ],
                        marker_line_width=0,
                    )
                )
            else:
                neg_fig = go.Figure(
                    go.Bar(x=[], y=[])
                )
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
                    text="Negative Price Hours by Month",
                    font=dict(size=15),
                ),
                yaxis=dict(title="Hours"),
            )
        else:
            neg_fig = _empty_figure(
                "Negative Price Hours"
            )

        return (
            kpis,
            ts_fig,
            hm_fig,
            dur_fig,
            spread_fig,
            neg_fig,
        )
