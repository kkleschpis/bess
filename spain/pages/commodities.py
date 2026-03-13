"""Tab 8: Commodity & Marginal Cost Drivers — gas/carbon trends for BESS.

Uses 5 years of realistic synthetic data.
Structure ready for live MIBGAS/EEX swap.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_trendline_trace,
    compute_linear_trend,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_5y_gas() -> pd.DataFrame:
    """5 years of realistic MIBGAS gas prices (EUR/MWh)."""
    dates = pd.date_range(
        "2021-01-01", periods=60, freq="MS"
    )
    np.random.seed(42)
    # 2021-2022 spike, then decline, then stabilize
    base = np.concatenate([
        np.linspace(20, 35, 12),   # 2021
        np.linspace(40, 95, 6),    # H1 2022 spike
        np.linspace(85, 45, 6),    # H2 2022 decline
        np.linspace(42, 32, 12),   # 2023
        np.linspace(30, 28, 12),   # 2024
        np.linspace(27, 30, 12),   # 2025
    ])
    noise = np.random.normal(0, 2, 60)
    return pd.DataFrame({
        "date": dates,
        "gas_eur_mwh": np.clip(
            base + noise, 12, 120
        ),
    })


def _sample_5y_carbon() -> pd.DataFrame:
    """5 years of EU ETS carbon prices (EUR/tonne)."""
    dates = pd.date_range(
        "2021-01-01", periods=60, freq="MS"
    )
    np.random.seed(123)
    base = np.concatenate([
        np.linspace(33, 55, 12),   # 2021
        np.linspace(58, 85, 12),   # 2022
        np.linspace(82, 70, 12),   # 2023
        np.linspace(68, 65, 12),   # 2024
        np.linspace(63, 68, 12),   # 2025
    ])
    noise = np.random.normal(0, 3, 60)
    return pd.DataFrame({
        "date": dates,
        "carbon_eur_t": np.clip(
            base + noise, 25, 110
        ),
    })


def _sample_5y_elec() -> pd.DataFrame:
    """5 years of avg monthly electricity prices."""
    dates = pd.date_range(
        "2021-01-01", periods=60, freq="MS"
    )
    np.random.seed(77)
    base = np.concatenate([
        np.linspace(30, 55, 12),   # 2021
        np.linspace(70, 180, 6),   # H1 2022
        np.linspace(160, 80, 6),   # H2 2022
        np.linspace(70, 50, 12),   # 2023
        np.linspace(48, 42, 12),   # 2024
        np.linspace(40, 45, 12),   # 2025
    ])
    noise = np.random.normal(0, 5, 60)
    return pd.DataFrame({
        "date": dates,
        "elec_eur_mwh": np.clip(
            base + noise, 10, 250
        ),
    })


def layout():
    return html.Div(
        [
            html.Div(
                "Commodity data: 5-year synthetic"
                " trends. Structure ready for live"
                " MIBGAS/EEX integration.",
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
            html.Div(id="es-commodities-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-gas-power-spread",
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
                            id="es-carbon-cost",
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
                            id="es-ccgt-bess-crossover",
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
                            id="es-commodity-corr",
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
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output(
                "es-commodities-kpis", "children"
            ),
            Output(
                "es-gas-power-spread", "figure"
            ),
            Output("es-carbon-cost", "figure"),
            Output(
                "es-ccgt-bess-crossover", "figure"
            ),
            Output(
                "es-commodity-corr", "figure"
            ),
        ],
        [Input("date-start", "date")],
    )
    def update_commodities(_start_date):
        gas = _sample_5y_gas()
        carbon = _sample_5y_carbon()
        elec = _sample_5y_elec()

        merged = pd.merge(
            gas, elec, on="date", how="inner"
        )
        merged = pd.merge(
            merged, carbon, on="date", how="inner"
        )

        # Gas-power spread: Elec - Gas * heat_rate
        heat_rate = 2.0  # Typical CCGT
        merged["gas_power_spread"] = (
            merged["elec_eur_mwh"]
            - merged["gas_eur_mwh"] * heat_rate
        )

        # Carbon cost per MWh
        co2_rate = 0.37  # tCO2/MWh for CCGT
        merged["carbon_cost_mwh"] = (
            merged["carbon_eur_t"] * co2_rate
        )

        # CCGT marginal cost
        merged["ccgt_marginal"] = (
            merged["gas_eur_mwh"] * heat_rate
            + merged["carbon_cost_mwh"]
        )

        # --- KPIs ---
        gas_slope, _, _ = compute_linear_trend(
            merged["gas_eur_mwh"]
        )
        carbon_slope, _, _ = compute_linear_trend(
            merged["carbon_eur_t"]
        )
        ccgt_slope, _, _ = compute_linear_trend(
            merged["ccgt_marginal"]
        )
        gps_slope, _, _ = compute_linear_trend(
            merged["gas_power_spread"]
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Gas Price Trend",
                        f"{gas_slope:.2f}"
                        " EUR/MWh/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Carbon Price Trend",
                        f"{carbon_slope:.2f}"
                        " EUR/t/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "CCGT Marginal Trend",
                        f"{ccgt_slope:.2f}"
                        " EUR/MWh/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Gas-Power Spread Trend",
                        f"{gps_slope:.2f}"
                        " EUR/MWh/mo",
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

        # --- Chart 1: Gas-Power Spread Evolution ---
        gps_fig = go.Figure()
        colors = [
            COLORS["accent_green"]
            if v > 0
            else COLORS["accent_red"]
            for v in merged["gas_power_spread"]
        ]
        gps_fig.add_trace(
            go.Bar(
                x=merged["date"],
                y=merged["gas_power_spread"],
                marker_color=colors,
                marker_line_width=0,
                name="Gas-Power Spread",
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "%{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            gps_fig,
            merged["date"],
            merged["gas_power_spread"],
            color=COLORS["accent_cyan"],
            name="Trend",
        )
        gps_fig.add_hline(
            y=0,
            line_color=COLORS["text_muted"],
            line_width=1,
        )
        apply_theme(gps_fig)
        gps_fig.update_layout(
            title=dict(
                text=(
                    "Gas-Power Spread Evolution"
                    " (Elec - Gas*HR)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 2: Carbon Cost per MWh ---
        carbon_fig = go.Figure()
        carbon_fig.add_trace(
            go.Scatter(
                x=merged["date"],
                y=merged["carbon_cost_mwh"],
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
                name="Carbon Cost/MWh",
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "%{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            carbon_fig,
            merged["date"],
            merged["carbon_cost_mwh"],
            color=COLORS["accent_red"],
            name="Trend",
        )
        apply_theme(carbon_fig)
        carbon_fig.update_layout(
            title=dict(
                text=(
                    "Carbon Cost per MWh"
                    " (CCGT @ 0.37 tCO2/MWh)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 3: CCGT vs BESS LCOE Crossover ---
        # BESS LCOE declining over time
        bess_lcoe_start = 120
        bess_lcoe_end = 55
        n = len(merged)
        bess_lcoe = np.linspace(
            bess_lcoe_start, bess_lcoe_end, n
        )

        cross_fig = go.Figure()
        cross_fig.add_trace(
            go.Scatter(
                x=merged["date"],
                y=merged["ccgt_marginal"],
                mode="lines",
                name="CCGT Marginal Cost",
                line=dict(
                    color=COLORS["accent_red"],
                    width=2.5,
                ),
                hovertemplate=(
                    "CCGT: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        cross_fig.add_trace(
            go.Scatter(
                x=merged["date"],
                y=bess_lcoe,
                mode="lines",
                name="BESS LCOE (est.)",
                line=dict(
                    color=COLORS[
                        "accent_green"
                    ],
                    width=2.5,
                    dash="dash",
                ),
                hovertemplate=(
                    "BESS: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        # Find crossover
        diff = (
            merged["ccgt_marginal"].values
            - bess_lcoe
        )
        sign_changes = np.where(
            np.diff(np.sign(diff))
        )[0]
        if len(sign_changes) > 0:
            cross_idx = sign_changes[-1]
            cross_fig.add_vline(
                x=merged["date"].iloc[cross_idx],
                line_dash="dot",
                line_color=COLORS[
                    "accent_amber"
                ],
                line_width=2,
                annotation_text="Crossover",
                annotation_font_color=COLORS[
                    "accent_amber"
                ],
            )
        apply_theme(cross_fig)
        cross_fig.update_layout(
            title=dict(
                text=(
                    "CCGT vs BESS LCOE"
                    " Crossover Projection"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
            hovermode="x unified",
        )

        # --- Chart 4: Rolling Gas-Elec Correlation ---
        window = 6
        rolling_corr = (
            merged["gas_eur_mwh"]
            .rolling(window, min_periods=3)
            .corr(merged["elec_eur_mwh"])
        )
        corr_fig = go.Figure()
        corr_fig.add_trace(
            go.Scatter(
                x=merged["date"],
                y=rolling_corr,
                mode="lines",
                line=dict(
                    color=COLORS["accent_cyan"],
                    width=2,
                ),
                name=f"{window}M Rolling Corr",
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Corr: %{y:.3f}"
                    "<extra></extra>"
                ),
            )
        )
        corr_fig.add_hline(
            y=0,
            line_dash="dash",
            line_color=COLORS["text_muted"],
            line_width=1,
        )
        apply_theme(corr_fig)
        corr_fig.update_layout(
            title=dict(
                text=(
                    "Gas-Electricity"
                    f" {window}M Rolling"
                    " Correlation"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="Correlation"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        return (
            kpis,
            gps_fig,
            carbon_fig,
            cross_fig,
            corr_fig,
        )
