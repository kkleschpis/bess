"""Tab 5: Ancillary Services — FCR/aFRR revenue analysis.

v1 uses realistic sample/historical data with the structure ready
to swap in live feeds from regelleistung.net later.
"""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_fcr_data() -> pd.DataFrame:
    """Realistic sample FCR capacity price data (EUR/MW/week)."""
    dates = pd.date_range(
        "2025-01-06", periods=52, freq="W-MON"
    )
    prices = [
        3850, 4100, 3700, 3500, 3900, 4200, 3600,
        3400, 3800, 4000, 3550, 3300, 3150, 2900,
        2700, 2500, 2800, 3100, 3400, 3000, 2600,
        2400, 2200, 2000, 1900, 2100, 2400, 2700,
        3000, 3200, 3500, 3800, 4000, 3700, 3400,
        3600, 3900, 4100, 3800, 3500, 3700, 4000,
        4200, 3900, 3600, 3800, 4100, 4300, 4000,
        3700, 3900, 4200,
    ]
    return pd.DataFrame({
        "date": dates[:len(prices)],
        "fcr_price_eur_mw_week": prices,
    })


def _sample_afrr_data() -> pd.DataFrame:
    """Realistic sample aFRR data (EUR/MW/h capacity, EUR/MWh energy)."""
    dates = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": dates,
        "afrr_cap_pos": [
            12.5, 11.8, 13.2, 10.5, 9.8, 8.5,
            7.2, 8.0, 9.5, 11.0, 12.0, 13.5,
        ],
        "afrr_cap_neg": [
            8.0, 7.5, 9.0, 7.0, 6.5, 5.5,
            4.8, 5.2, 6.5, 7.8, 8.5, 9.2,
        ],
        "afrr_energy_pos": [
            120, 135, 110, 95, 80, 65,
            55, 60, 75, 100, 115, 130,
        ],
        "afrr_energy_neg": [
            -45, -50, -40, -35, -30, -25,
            -20, -22, -28, -38, -42, -48,
        ],
    })


def _sample_revenue_comparison() -> pd.DataFrame:
    """Monthly revenue comparison: arbitrage vs FCR vs aFRR for 10 MW/20 MWh."""
    months = pd.date_range(
        "2025-01-01", periods=12, freq="MS"
    )
    return pd.DataFrame({
        "month": months,
        "arbitrage": [
            18500, 22000, 15800, 12500, 9800, 7500,
            6200, 8000, 11500, 16000, 19500, 21000,
        ],
        "fcr": [
            16600, 17700, 16000, 15100, 16800, 18100,
            15500, 14700, 16400, 17200, 15100, 14300,
        ],
        "afrr": [
            9000, 8500, 9500, 7500, 7000, 6000,
            5200, 5600, 7000, 8400, 8800, 9600,
        ],
    })


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "Ancillary data uses representative "
                        "historical samples. Live regelleistung.net "
                        "integration planned for v2.",
                        style={
                            "color": COLORS["accent_amber"],
                            "fontSize": "13px",
                            "padding": "8px 16px",
                            "backgroundColor": (
                                COLORS["accent_amber"] + "15"
                            ),
                            "borderRadius": "8px",
                            "marginBottom": "16px",
                        },
                    ),
                ],
            ),
            html.Div(id="ancillary-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="ancillary-fcr",
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
                            id="ancillary-afrr",
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
                    id="ancillary-comparison",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("ancillary-kpis", "children"),
            Output("ancillary-fcr", "figure"),
            Output("ancillary-afrr", "figure"),
            Output("ancillary-comparison", "figure"),
        ],
        [Input("date-start", "date")],
    )
    def update_ancillary(_start_date):
        fcr = _sample_fcr_data()
        afrr = _sample_afrr_data()
        comparison = _sample_revenue_comparison()

        latest_fcr = fcr["fcr_price_eur_mw_week"].iloc[
            -1
        ]
        latest_afrr_cap = afrr["afrr_cap_pos"].iloc[-1]
        # Combined for 10 MW: FCR weekly + aFRR monthly
        combined = (
            latest_fcr * 10 / 7
            + latest_afrr_cap * 10 * 24
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Latest FCR Price",
                        f"\u20ac{latest_fcr:,.0f}"
                        " /MW/week",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "aFRR Capacity (pos)",
                        f"\u20ac{latest_afrr_cap:.1f}"
                        " /MW/h",
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
                        "regelleistung.net v2",
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
                y=fcr["fcr_price_eur_mw_week"],
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
                    "\u20ac%{y:,.0f} /MW/week"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(fcr_fig)
        fcr_fig.update_layout(
            title=dict(
                text="FCR Capacity Price Trend"
                " (EUR/MW/week)",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MW/week"),
        )

        # aFRR
        afrr_fig = go.Figure()
        afrr_fig.add_trace(
            go.Bar(
                x=afrr["month"],
                y=afrr["afrr_cap_pos"],
                name="Positive Cap",
                marker_color=COLORS["accent_green"],
                marker_line_width=0,
            )
        )
        afrr_fig.add_trace(
            go.Bar(
                x=afrr["month"],
                y=afrr["afrr_cap_neg"],
                name="Negative Cap",
                marker_color=COLORS["accent_red"],
                marker_line_width=0,
            )
        )
        apply_theme(afrr_fig)
        afrr_fig.update_layout(
            title=dict(
                text="aFRR Capacity Prices"
                " (EUR/MW/h)",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MW/h"),
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
                y=comparison["fcr"],
                name="FCR",
                marker_color=COLORS["accent_blue"],
                marker_line_width=0,
            )
        )
        comp_fig.add_trace(
            go.Bar(
                x=comparison["month"],
                y=comparison["afrr"],
                name="aFRR",
                marker_color=COLORS["accent_green"],
                marker_line_width=0,
            )
        )
        apply_theme(comp_fig)
        comp_fig.update_layout(
            title=dict(
                text="Monthly Revenue Comparison"
                " (10 MW BESS)",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            barmode="group",
            legend=dict(orientation="h", y=-0.15),
        )

        return kpis, fcr_fig, afrr_fig, comp_fig
