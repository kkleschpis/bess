"""Tab 5: Ancillary Services — aFRR/mFRR revenue analysis for Spain.

v1 uses realistic sample data with the structure ready
to swap in live feeds from ESIOS later.
"""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_secondary_data() -> pd.DataFrame:
    """Realistic sample aFRR (secondary reserve) data for Spain."""
    dates = pd.date_range(
        "2025-01-06", periods=52, freq="W-MON"
    )
    prices = [
        28, 32, 26, 24, 30, 35, 25, 22, 29, 33,
        27, 21, 20, 18, 17, 16, 19, 22, 25, 20,
        17, 15, 14, 13, 12, 14, 16, 19, 22, 24,
        27, 30, 33, 28, 25, 27, 30, 34, 29, 26,
        28, 31, 35, 30, 27, 29, 32, 36, 31, 28,
        30, 33,
    ]
    return pd.DataFrame({
        "date": dates[: len(prices)],
        "afrr_price_eur_mw_h": prices,
    })


def _sample_tertiary_data() -> pd.DataFrame:
    """Realistic sample mFRR (tertiary reserve) data for Spain."""
    dates = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": dates,
        "mfrr_up_price": [
            85, 92, 78, 65, 55, 45,
            38, 42, 58, 72, 80, 90,
        ],
        "mfrr_down_price": [
            35, 40, 30, 25, 22, 18,
            15, 17, 24, 32, 36, 42,
        ],
    })


def _sample_revenue_comparison() -> pd.DataFrame:
    """Monthly revenue comparison: arbitrage vs aFRR vs mFRR for 10 MW."""
    months = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": months,
        "arbitrage": [
            15000, 18000, 13000, 10500, 8200, 6500,
            5500, 7000, 9800, 13500, 16500, 17500,
        ],
        "afrr": [
            20200, 23000, 18700, 17300, 21600, 25200,
            18000, 15800, 20900, 17300, 21600, 23800,
        ],
        "mfrr": [
            6100, 6600, 5600, 4700, 4000, 3200,
            2700, 3000, 4200, 5200, 5800, 6500,
        ],
    })


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "Ancillary data uses representative"
                        " historical samples. Live ESIOS"
                        " integration planned for v2.",
                        style={
                            "color": COLORS[
                                "accent_amber"
                            ],
                            "fontSize": "13px",
                            "padding": "8px 16px",
                            "backgroundColor": (
                                COLORS["accent_amber"]
                                + "15"
                            ),
                            "borderRadius": "8px",
                            "marginBottom": "16px",
                        },
                    ),
                ],
            ),
            html.Div(id="es-ancillary-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-ancillary-afrr",
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
                            id="es-ancillary-mfrr",
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
                    id="es-ancillary-comparison",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output(
                "es-ancillary-kpis", "children"
            ),
            Output("es-ancillary-afrr", "figure"),
            Output("es-ancillary-mfrr", "figure"),
            Output(
                "es-ancillary-comparison", "figure"
            ),
        ],
        [Input("date-start", "date")],
    )
    def update_ancillary(_start_date):
        afrr = _sample_secondary_data()
        mfrr = _sample_tertiary_data()
        comparison = _sample_revenue_comparison()

        latest_afrr = afrr[
            "afrr_price_eur_mw_h"
        ].iloc[-1]
        latest_mfrr_up = mfrr["mfrr_up_price"].iloc[
            -1
        ]
        combined = (
            latest_afrr * 10 * 24
            + latest_mfrr_up * 10
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Latest aFRR Price",
                        f"\u20ac{latest_afrr:.0f}"
                        " /MW/h",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "mFRR Up Price",
                        f"\u20ac{latest_mfrr_up:.0f}"
                        " /MWh",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Combined Daily (10MW)",
                        f"\u20ac{combined:,.0f}",
                        "aFRR + mFRR estimate",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Data Source",
                        "Sample",
                        "ESIOS v2",
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

        # aFRR trend
        afrr_fig = go.Figure(
            go.Scatter(
                x=afrr["date"],
                y=afrr["afrr_price_eur_mw_h"],
                mode="lines+markers",
                line=dict(
                    color=COLORS["accent_blue"],
                    width=2.5,
                ),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.1)",
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "\u20ac%{y:.0f} /MW/h"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(afrr_fig)
        afrr_fig.update_layout(
            title=dict(
                text=(
                    "aFRR (Secondary Reserve)"
                    " Price Trend"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MW/h"),
        )

        # mFRR
        mfrr_fig = go.Figure()
        mfrr_fig.add_trace(
            go.Bar(
                x=mfrr["month"],
                y=mfrr["mfrr_up_price"],
                name="Up Regulation",
                marker_color=COLORS["accent_green"],
                marker_line_width=0,
            )
        )
        mfrr_fig.add_trace(
            go.Bar(
                x=mfrr["month"],
                y=mfrr["mfrr_down_price"],
                name="Down Regulation",
                marker_color=COLORS["accent_red"],
                marker_line_width=0,
            )
        )
        apply_theme(mfrr_fig)
        mfrr_fig.update_layout(
            title=dict(
                text=(
                    "mFRR (Tertiary Reserve)"
                    " Prices (EUR/MWh)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            barmode="group",
            legend=dict(orientation="h", y=-0.15),
        )

        # Revenue comparison
        comp_fig = go.Figure()
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["arbitrage"],
                name="Arbitrage",
                marker_color=COLORS["accent_amber"],
                marker_line_width=0,
            )
        )
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["afrr"],
                name="aFRR",
                marker_color=COLORS["accent_blue"],
                marker_line_width=0,
            )
        )
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["mfrr"],
                name="mFRR",
                marker_color=COLORS["accent_green"],
                marker_line_width=0,
            )
        )
        apply_theme(comp_fig)
        comp_fig.update_layout(
            title=dict(
                text=(
                    "Monthly Revenue Comparison"
                    " (10 MW BESS)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            barmode="group",
            legend=dict(orientation="h", y=-0.15),
        )

        return kpis, afrr_fig, mfrr_fig, comp_fig
