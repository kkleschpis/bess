"""Tab 5: Ancillary Services — FCR/aFRR revenue analysis.

v1 uses realistic sample/historical data with the structure ready
to swap in live feeds from regelleistung.net later.
Extended to multi-year range for strategic context.
"""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_fcr_data() -> pd.DataFrame:
    """Realistic sample FCR capacity price data (EUR/MW/week).

    Extended to 3 years (2023-2025) for strategic context.
    """
    dates = pd.date_range(
        "2023-01-02", periods=156, freq="W-MON"
    )
    # 2023: higher prices, gradual decline
    prices_2023 = [
        5200, 5000, 4800, 4600, 4900, 5100, 4700,
        4500, 4800, 5000, 4600, 4400, 4200, 4000,
        3800, 3600, 3900, 4100, 4400, 4000, 3600,
        3400, 3200, 3000, 2800, 3000, 3300, 3600,
        3900, 4100, 4400, 4700, 4900, 4600, 4300,
        4500, 4800, 5000, 4700, 4400, 4600, 4900,
        5100, 4800, 4500, 4700, 5000, 5200, 4900,
        4600, 4800, 5100,
    ]
    # 2024: declining trend as more BESS enters
    prices_2024 = [
        4500, 4300, 4100, 3900, 4200, 4400, 4000,
        3800, 4100, 4300, 3900, 3700, 3500, 3300,
        3100, 2900, 3200, 3400, 3700, 3300, 2900,
        2700, 2500, 2300, 2100, 2300, 2600, 2900,
        3200, 3400, 3700, 4000, 4200, 3900, 3600,
        3800, 4100, 4300, 4000, 3700, 3900, 4200,
        4400, 4100, 3800, 4000, 4300, 4500, 4200,
        3900, 4100, 4400,
    ]
    # 2025: further compression
    prices_2025 = [
        3850, 4100, 3700, 3500, 3900, 4200, 3600,
        3400, 3800, 4000, 3550, 3300, 3150, 2900,
        2700, 2500, 2800, 3100, 3400, 3000, 2600,
        2400, 2200, 2000, 1900, 2100, 2400, 2700,
        3000, 3200, 3500, 3800, 4000, 3700, 3400,
        3600, 3900, 4100, 3800, 3500, 3700, 4000,
        4200, 3900, 3600, 3800, 4100, 4300, 4000,
        3700, 3900, 4200,
    ]
    all_prices = (
        prices_2023 + prices_2024 + prices_2025
    )
    n = min(len(dates), len(all_prices))
    return pd.DataFrame({
        "date": dates[:n],
        "fcr_price_eur_mw_week": all_prices[:n],
    })


def _sample_afrr_data() -> pd.DataFrame:
    """Realistic sample aFRR data extended to 3 years."""
    dates = pd.date_range(
        "2023-01-01", periods=36, freq="MS"
    )
    return pd.DataFrame({
        "month": dates,
        "afrr_cap_pos": [
            # 2023
            15.0, 14.2, 16.0, 13.5, 12.0, 10.5,
            9.0, 10.0, 12.0, 14.0, 15.0, 16.5,
            # 2024
            13.5, 12.8, 14.5, 11.5, 10.8, 9.5,
            8.0, 9.0, 10.5, 12.0, 13.0, 14.5,
            # 2025
            12.5, 11.8, 13.2, 10.5, 9.8, 8.5,
            7.2, 8.0, 9.5, 11.0, 12.0, 13.5,
        ],
        "afrr_cap_neg": [
            # 2023
            10.0, 9.5, 11.0, 9.0, 8.0, 7.0,
            6.0, 6.5, 8.0, 9.5, 10.5, 11.5,
            # 2024
            9.0, 8.5, 10.0, 8.0, 7.5, 6.5,
            5.5, 6.0, 7.5, 8.5, 9.5, 10.0,
            # 2025
            8.0, 7.5, 9.0, 7.0, 6.5, 5.5,
            4.8, 5.2, 6.5, 7.8, 8.5, 9.2,
        ],
        "afrr_energy_pos": [
            # 2023
            150, 165, 140, 120, 100, 85,
            70, 80, 95, 125, 145, 160,
            # 2024
            135, 150, 125, 108, 90, 75,
            62, 70, 85, 112, 130, 145,
            # 2025
            120, 135, 110, 95, 80, 65,
            55, 60, 75, 100, 115, 130,
        ],
        "afrr_energy_neg": [
            # 2023
            -55, -60, -50, -45, -38, -32,
            -25, -28, -35, -48, -52, -58,
            # 2024
            -50, -55, -45, -40, -34, -28,
            -22, -25, -32, -42, -48, -52,
            # 2025
            -45, -50, -40, -35, -30, -25,
            -20, -22, -28, -38, -42, -48,
        ],
    })


def _sample_revenue_comparison() -> pd.DataFrame:
    """Monthly revenue comparison extended to 3 years for 10 MW/20 MWh."""
    months = pd.date_range(
        "2023-01-01", periods=36, freq="MS"
    )
    return pd.DataFrame({
        "month": months,
        "arbitrage": [
            # 2023 - higher spreads
            25000, 28000, 22000, 18000, 14000, 11000,
            9000, 12000, 16000, 22000, 26000, 28000,
            # 2024 - declining
            21000, 25000, 18000, 15000, 12000, 9000,
            7500, 10000, 14000, 19000, 23000, 25000,
            # 2025 - further compression
            18500, 22000, 15800, 12500, 9800, 7500,
            6200, 8000, 11500, 16000, 19500, 21000,
        ],
        "fcr": [
            # 2023
            22400, 21500, 20700, 19800, 21100, 22000,
            20300, 19400, 20700, 21600, 22500, 23500,
            # 2024
            19400, 18600, 17700, 16800, 18100, 19000,
            17300, 16400, 17700, 18600, 17100, 16200,
            # 2025
            16600, 17700, 16000, 15100, 16800, 18100,
            15500, 14700, 16400, 17200, 15100, 14300,
        ],
        "afrr": [
            # 2023
            12000, 11500, 12800, 10800, 9600, 8400,
            7200, 8000, 9600, 11200, 12000, 13200,
            # 2024
            10800, 10200, 11600, 9200, 8600, 7600,
            6400, 7200, 8400, 9600, 10400, 11600,
            # 2025
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
                        "Ancillary data uses representative"
                        " historical samples (3-year range)."
                        " Live regelleistung.net"
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
            Output(
                "ancillary-comparison", "figure"
            ),
        ],
        [Input("date-start", "date")],
    )
    def update_ancillary(_start_date):
        fcr = _sample_fcr_data()
        afrr = _sample_afrr_data()
        comparison = _sample_revenue_comparison()

        latest_fcr = fcr[
            "fcr_price_eur_mw_week"
        ].iloc[-1]
        latest_afrr_cap = afrr[
            "afrr_cap_pos"
        ].iloc[-1]
        combined = (
            latest_fcr * 10 / 7
            + latest_afrr_cap * 10 * 24
        )

        # YoY FCR decline
        fcr_recent = fcr.tail(52)[
            "fcr_price_eur_mw_week"
        ].mean()
        fcr_prior = (
            fcr.iloc[-104:-52][
                "fcr_price_eur_mw_week"
            ].mean()
            if len(fcr) >= 104
            else fcr_recent
        )
        fcr_yoy = (
            (fcr_recent - fcr_prior)
            / fcr_prior
            * 100
            if fcr_prior > 0
            else 0
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Latest FCR Price",
                        f"\u20ac{latest_fcr:,.0f}"
                        " /MW/week",
                        f"YoY: {fcr_yoy:+.1f}%",
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
                        "Sample (3Y)",
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

        # FCR trend with rolling average
        fcr_rolling = (
            fcr["fcr_price_eur_mw_week"]
            .rolling(12, min_periods=1)
            .mean()
        )
        fcr_fig = go.Figure()
        fcr_fig.add_trace(
            go.Scatter(
                x=fcr["date"],
                y=fcr["fcr_price_eur_mw_week"],
                mode="lines",
                name="Weekly Price",
                line=dict(
                    color=COLORS["accent_blue"],
                    width=1.5,
                ),
                fill="tozeroy",
                fillcolor="rgba(59,130,246,0.1)",
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "\u20ac%{y:,.0f} /MW/week"
                    "<extra></extra>"
                ),
            )
        )
        fcr_fig.add_trace(
            go.Scatter(
                x=fcr["date"],
                y=fcr_rolling,
                mode="lines",
                name="12W Rolling",
                line=dict(
                    color=COLORS["accent_amber"],
                    width=2.5,
                ),
            )
        )
        apply_theme(fcr_fig)
        fcr_fig.update_layout(
            title=dict(
                text=(
                    "FCR Capacity Price Trend"
                    " (EUR/MW/week) — 3 Years"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MW/week"),
            legend=dict(orientation="h", y=-0.15),
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
                text=(
                    "aFRR Capacity Prices"
                    " (EUR/MW/h) — 3 Years"
                ),
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
                text=(
                    "Monthly Revenue Comparison"
                    " (10 MW BESS) — 3 Years"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            barmode="group",
            legend=dict(orientation="h", y=-0.15),
        )

        return kpis, fcr_fig, afrr_fig, comp_fig
