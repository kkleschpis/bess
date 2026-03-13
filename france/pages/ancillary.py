"""Tab 6: Ancillary Services — FCR/aFRR/mFRR revenue analysis for France.

v1 uses realistic sample data with the structure ready
to swap in live RTE/ENTSO-E feeds later.
"""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_fcr_data() -> pd.DataFrame:
    """Realistic sample FCR price data for France."""
    dates = pd.date_range(
        "2025-01-06", periods=52, freq="W-MON"
    )
    prices = [
        18, 21, 16, 15, 20, 24, 17, 14, 19, 22,
        18, 13, 12, 11, 10, 9, 12, 15, 17, 13,
        10, 9, 8, 7, 8, 10, 12, 14, 16, 18,
        20, 22, 25, 20, 17, 19, 22, 26, 21, 18,
        20, 23, 27, 22, 19, 21, 24, 28, 23, 20,
        22, 25,
    ]
    return pd.DataFrame({
        "date": dates[: len(prices)],
        "fcr_price_eur_mw_h": prices,
    })


def _sample_afrr_data() -> pd.DataFrame:
    """Realistic sample aFRR price data for France."""
    dates = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": dates,
        "afrr_up_price": [
            65, 72, 58, 48, 40, 32,
            28, 35, 45, 55, 62, 70,
        ],
        "afrr_down_price": [
            25, 30, 22, 18, 15, 12,
            10, 13, 18, 24, 28, 32,
        ],
    })


def _sample_mfrr_data() -> pd.DataFrame:
    """Realistic sample mFRR price data for France."""
    dates = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": dates,
        "mfrr_up_price": [
            90, 98, 82, 68, 58, 48,
            42, 50, 62, 78, 85, 95,
        ],
        "mfrr_down_price": [
            38, 42, 32, 27, 24, 20,
            17, 20, 26, 34, 38, 44,
        ],
    })


def _sample_revenue_comparison() -> pd.DataFrame:
    """Monthly revenue: arbitrage vs FCR vs aFRR for 10 MW."""
    months = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": months,
        "arbitrage": [
            14000, 17000, 12000, 9500, 7500, 5800,
            5000, 6500, 9000, 12500, 15500, 16500,
        ],
        "fcr": [
            13100, 15300, 11600, 10900, 14600, 17400,
            12200, 10200, 14400, 13100, 14600, 16200,
        ],
        "afrr": [
            9400, 10400, 8400, 6900, 5800, 4600,
            4000, 5100, 6500, 8000, 9100, 10100,
        ],
    })


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "Ancillary data uses"
                        " representative historical"
                        " samples. Live RTE/ENTSO-E"
                        " integration planned"
                        " for v2.",
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
            html.Div(id="fr-ancillary-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="fr-ancillary-fcr",
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
                            id="fr-ancillary-afrr-mfrr",
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
                    id="fr-ancillary-comparison",
                    config={
                        "displayModeBar": False
                    },
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output(
                "fr-ancillary-kpis", "children"
            ),
            Output(
                "fr-ancillary-fcr", "figure"
            ),
            Output(
                "fr-ancillary-afrr-mfrr", "figure"
            ),
            Output(
                "fr-ancillary-comparison", "figure"
            ),
        ],
        [Input("date-start", "date")],
    )
    def update_ancillary(_start_date):
        fcr = _sample_fcr_data()
        afrr = _sample_afrr_data()
        comparison = _sample_revenue_comparison()

        latest_fcr = fcr[
            "fcr_price_eur_mw_h"
        ].iloc[-1]
        latest_afrr_up = afrr[
            "afrr_up_price"
        ].iloc[-1]
        combined = (
            latest_fcr * 10 * 24
            + latest_afrr_up * 10
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Latest FCR Price",
                        f"\u20ac{latest_fcr:.0f}"
                        " /MW/h",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "aFRR Up Price",
                        f"\u20ac{latest_afrr_up:.0f}"
                        " /MWh",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Combined Daily (10MW)",
                        f"\u20ac{combined:,.0f}",
                        "FCR + aFRR estimate",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Data Source",
                        "Sample",
                        "RTE/ENTSO-E v2",
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

        # FCR trend
        fcr_fig = go.Figure(
            go.Scatter(
                x=fcr["date"],
                y=fcr["fcr_price_eur_mw_h"],
                mode="lines+markers",
                line=dict(
                    color=COLORS["accent_blue"],
                    width=2.5,
                ),
                marker=dict(size=5),
                fill="tozeroy",
                fillcolor=(
                    "rgba(59,130,246,0.1)"
                ),
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "\u20ac%{y:.0f} /MW/h"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(fcr_fig)
        fcr_fig.update_layout(
            title=dict(
                text="FCR Price Trend",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MW/h"),
        )

        # aFRR/mFRR prices
        mfrr = _sample_mfrr_data()
        afrr_mfrr_fig = go.Figure()
        afrr_mfrr_fig.add_trace(
            go.Bar(
                x=afrr["month"],
                y=afrr["afrr_up_price"],
                name="aFRR Up",
                marker_color=COLORS[
                    "accent_green"
                ],
                marker_line_width=0,
            )
        )
        afrr_mfrr_fig.add_trace(
            go.Bar(
                x=afrr["month"],
                y=afrr["afrr_down_price"],
                name="aFRR Down",
                marker_color=COLORS[
                    "accent_red"
                ],
                marker_line_width=0,
            )
        )
        afrr_mfrr_fig.add_trace(
            go.Scatter(
                x=mfrr["month"],
                y=mfrr["mfrr_up_price"],
                name="mFRR Up",
                mode="lines+markers",
                line=dict(
                    color=COLORS["accent_amber"],
                    width=2,
                    dash="dot",
                ),
                marker=dict(size=5),
            )
        )
        apply_theme(afrr_mfrr_fig)
        afrr_mfrr_fig.update_layout(
            title=dict(
                text=(
                    "aFRR / mFRR Prices"
                    " (EUR/MWh)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            barmode="group",
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # Revenue comparison
        comp_fig = go.Figure()
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["arbitrage"],
                name="Arbitrage",
                marker_color=COLORS[
                    "accent_amber"
                ],
                marker_line_width=0,
            )
        )
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["fcr"],
                name="FCR",
                marker_color=COLORS[
                    "accent_blue"
                ],
                marker_line_width=0,
            )
        )
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["afrr"],
                name="aFRR",
                marker_color=COLORS[
                    "accent_green"
                ],
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
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        return (
            kpis,
            fcr_fig,
            afrr_mfrr_fig,
            comp_fig,
        )
