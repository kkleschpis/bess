"""Tab 8: Commodity Prices — TTF gas and EU ETS carbon for France.

France uses TTF (Title Transfer Facility) as gas reference,
not MIBGAS (Spain) or NCG (Germany).

v1 uses realistic sample data with the structure ready
to swap in live TTF/EEX feeds later.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_gas_prices() -> pd.DataFrame:
    """Realistic TTF gas price data (EUR/MWh)."""
    dates = pd.date_range(
        "2025-01-01", periods=365, freq="D"
    )
    np.random.seed(42)
    base = 30 + 10 * np.sin(
        np.linspace(0, 2 * np.pi, 365)
    )
    noise = np.random.normal(0, 1.8, 365)
    prices = base + noise
    return pd.DataFrame({
        "date": dates,
        "gas_price_eur_mwh": np.clip(
            prices, 15, 55
        ),
    })


def _sample_carbon_prices() -> pd.DataFrame:
    """Realistic EU ETS carbon price data (EUR/tonne)."""
    dates = pd.date_range(
        "2025-01-01", periods=365, freq="D"
    )
    np.random.seed(123)
    base = np.linspace(65, 72, 365)
    noise = np.random.normal(0, 2, 365)
    prices = base + noise
    return pd.DataFrame({
        "date": dates,
        "carbon_price_eur_t": np.clip(
            prices, 50, 90
        ),
    })


def _sample_electricity_prices() -> pd.DataFrame:
    """Correlated electricity prices for scatter analysis."""
    dates = pd.date_range(
        "2025-01-01", periods=365, freq="D"
    )
    np.random.seed(77)
    base = 42 + 18 * np.sin(
        np.linspace(0, 2 * np.pi, 365)
    )
    noise = np.random.normal(0, 10, 365)
    prices = base + noise
    return pd.DataFrame({
        "date": dates,
        "elec_price_eur_mwh": np.clip(
            prices, 0, 130
        ),
    })


def layout():
    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        "Commodity data uses"
                        " representative samples."
                        " Live TTF/EEX integration"
                        " planned for v2.",
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
            html.Div(id="fr-commodities-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="fr-gas-chart",
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
                            id="fr-carbon-chart",
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
                    id="fr-gas-elec-scatter",
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
                "fr-commodities-kpis", "children"
            ),
            Output("fr-gas-chart", "figure"),
            Output("fr-carbon-chart", "figure"),
            Output(
                "fr-gas-elec-scatter", "figure"
            ),
        ],
        [Input("date-start", "date")],
    )
    def update_commodities(_start_date):
        gas = _sample_gas_prices()
        carbon = _sample_carbon_prices()
        elec = _sample_electricity_prices()

        current_gas = gas[
            "gas_price_eur_mwh"
        ].iloc[-1]
        current_carbon = carbon[
            "carbon_price_eur_t"
        ].iloc[-1]
        current_elec = elec[
            "elec_price_eur_mwh"
        ].iloc[-1]
        gas_power_spread = (
            current_elec - current_gas * 2.0
        )
        # Carbon cost per MWh (assuming ~0.37 tCO2/MWh for gas CCGT)
        carbon_cost = current_carbon * 0.37

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Current Gas Price",
                        f"{current_gas:.1f}"
                        " EUR/MWh",
                        "TTF",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Current Carbon Price",
                        f"{current_carbon:.1f}"
                        " EUR/t",
                        "EU ETS (EUA)",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Gas-Power Spread",
                        f"{gas_power_spread:.1f}"
                        " EUR/MWh",
                        "Elec - 2x Gas",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Carbon Cost / MWh",
                        f"{carbon_cost:.1f}"
                        " EUR/MWh",
                        "CCGT @ 0.37 tCO2/MWh",
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

        # Gas price trend
        gas_fig = go.Figure(
            go.Scatter(
                x=gas["date"],
                y=gas["gas_price_eur_mwh"],
                mode="lines",
                line=dict(
                    color=COLORS["accent_amber"],
                    width=2,
                ),
                fill="tozeroy",
                fillcolor=(
                    "rgba(245,158,11,0.1)"
                ),
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "%{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(gas_fig)
        gas_fig.update_layout(
            title=dict(
                text="TTF Gas Price (EUR/MWh)",
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
        )

        # Carbon price trend
        carbon_fig = go.Figure(
            go.Scatter(
                x=carbon["date"],
                y=carbon["carbon_price_eur_t"],
                mode="lines",
                line=dict(
                    color=COLORS["accent_purple"],
                    width=2,
                ),
                fill="tozeroy",
                fillcolor=(
                    "rgba(139,92,246,0.1)"
                ),
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "%{y:.1f} EUR/tonne"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(carbon_fig)
        carbon_fig.update_layout(
            title=dict(
                text=(
                    "EU ETS Carbon Price"
                    " (EUR/tonne)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/tonne"),
        )

        # Gas vs electricity scatter
        merged = pd.merge(
            gas, elec, on="date", how="inner"
        )
        scatter_fig = go.Figure(
            go.Scatter(
                x=merged["gas_price_eur_mwh"],
                y=merged["elec_price_eur_mwh"],
                mode="markers",
                marker=dict(
                    color=COLORS["accent_cyan"],
                    size=4,
                    opacity=0.6,
                ),
                hovertemplate=(
                    "Gas: %{x:.1f} EUR/MWh<br>"
                    "Elec: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(scatter_fig)
        scatter_fig.update_layout(
            title=dict(
                text=(
                    "Gas Price vs Electricity"
                    " Price Correlation"
                ),
                font=dict(size=15),
            ),
            xaxis=dict(
                title="Gas Price (EUR/MWh)"
            ),
            yaxis=dict(
                title="Electricity Price (EUR/MWh)"
            ),
        )

        return (
            kpis,
            gas_fig,
            carbon_fig,
            scatter_fig,
        )
