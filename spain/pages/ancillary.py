"""Tab 9: Ancillary Revenue Trends — reserve market evolution.

Uses 5 years of realistic synthetic data.
Structure ready for live ESIOS swap.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_projection_trace,
    add_trendline_trace,
    compute_linear_trend,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style


def _sample_5y_ancillary() -> pd.DataFrame:
    """5 years of monthly ancillary revenue data (10 MW BESS)."""
    dates = pd.date_range(
        "2021-01-01", periods=60, freq="MS"
    )
    np.random.seed(99)

    # aFRR: growing market over 5 years
    afrr_base = np.concatenate([
        np.linspace(8000, 12000, 12),
        np.linspace(11000, 16000, 12),
        np.linspace(15000, 20000, 12),
        np.linspace(18000, 22000, 12),
        np.linspace(20000, 24000, 12),
    ])
    # Seasonal pattern
    seasonal = 3000 * np.sin(
        np.linspace(0, 10 * np.pi, 60)
    )
    afrr = np.clip(
        afrr_base + seasonal
        + np.random.normal(0, 1500, 60),
        3000,
        35000,
    )

    # mFRR: more volatile, moderate growth
    mfrr_base = np.concatenate([
        np.linspace(3000, 4500, 12),
        np.linspace(4000, 6000, 12),
        np.linspace(5500, 7000, 12),
        np.linspace(6500, 7500, 12),
        np.linspace(7000, 8500, 12),
    ])
    mfrr = np.clip(
        mfrr_base
        + np.random.normal(0, 1000, 60),
        1000,
        15000,
    )

    # Arbitrage for comparison
    arb_base = np.concatenate([
        np.linspace(10000, 15000, 12),
        np.linspace(18000, 35000, 6),
        np.linspace(30000, 18000, 6),
        np.linspace(16000, 13000, 12),
        np.linspace(12000, 11000, 12),
        np.linspace(10500, 12000, 12),
    ])
    arb = np.clip(
        arb_base
        + np.random.normal(0, 2000, 60),
        2000,
        50000,
    )

    return pd.DataFrame({
        "date": dates,
        "afrr_eur": afrr,
        "mfrr_eur": mfrr,
        "arbitrage_eur": arb,
    })


def layout():
    return html.Div(
        [
            html.Div(
                "Ancillary data: 5-year synthetic"
                " trends (10 MW BESS). Structure"
                " ready for live ESIOS integration.",
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
            html.Div(id="es-ancillary-kpis"),
            html.Div(
                dcc.Graph(
                    id="es-ancillary-stacked",
                    config={
                        "displayModeBar": False
                    },
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-ancillary-ratio",
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
                            id="es-ancillary-projection",
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
                    id="es-ancillary-reliability",
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
                "es-ancillary-kpis", "children"
            ),
            Output(
                "es-ancillary-stacked", "figure"
            ),
            Output(
                "es-ancillary-ratio", "figure"
            ),
            Output(
                "es-ancillary-projection",
                "figure",
            ),
            Output(
                "es-ancillary-reliability",
                "figure",
            ),
        ],
        [Input("date-start", "date")],
    )
    def update_ancillary(_start_date):
        data = _sample_5y_ancillary()
        data["total"] = (
            data["afrr_eur"]
            + data["mfrr_eur"]
            + data["arbitrage_eur"]
        )
        data["ancillary_total"] = (
            data["afrr_eur"] + data["mfrr_eur"]
        )
        data["anc_ratio"] = (
            data["ancillary_total"]
            / data["total"].replace(
                0, float("nan")
            )
            * 100
        )

        # --- KPIs ---
        afrr_slope, _, _ = compute_linear_trend(
            data["afrr_eur"]
        )
        mfrr_slope, _, _ = compute_linear_trend(
            data["mfrr_eur"]
        )
        combined_slope, _, _ = (
            compute_linear_trend(
                data["ancillary_total"]
            )
        )
        ratio_slope, _, _ = compute_linear_trend(
            data["anc_ratio"]
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "aFRR Trend",
                        f"{afrr_slope:+,.0f}"
                        " EUR/mo/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "mFRR Trend",
                        f"{mfrr_slope:+,.0f}"
                        " EUR/mo/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Combined Ancillary",
                        f"{combined_slope:+,.0f}"
                        " EUR/mo/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Ancillary Ratio Trend",
                        f"{ratio_slope:+.2f}"
                        " pp/mo",
                        "Ancillary / Total",
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

        # --- Chart 1: Monthly Revenue by Type ---
        stack_fig = go.Figure()
        stack_fig.add_trace(
            go.Bar(
                x=data["date"],
                y=data["arbitrage_eur"],
                name="Arbitrage",
                marker_color=COLORS[
                    "accent_amber"
                ],
                marker_line_width=0,
                hovertemplate=(
                    "Arb: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        stack_fig.add_trace(
            go.Bar(
                x=data["date"],
                y=data["afrr_eur"],
                name="aFRR",
                marker_color=COLORS[
                    "accent_blue"
                ],
                marker_line_width=0,
                hovertemplate=(
                    "aFRR: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        stack_fig.add_trace(
            go.Bar(
                x=data["date"],
                y=data["mfrr_eur"],
                name="mFRR",
                marker_color=COLORS[
                    "accent_green"
                ],
                marker_line_width=0,
                hovertemplate=(
                    "mFRR: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            stack_fig,
            data["date"],
            data["total"],
            color=COLORS["accent_red"],
            name="Total Trend",
        )
        apply_theme(stack_fig)
        stack_fig.update_layout(
            title=dict(
                text=(
                    "Monthly Revenue by Type"
                    " (10 MW BESS) + Total Trend"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            barmode="stack",
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 2: Arbitrage vs Ancillary Ratio ---
        ratio_fig = go.Figure()
        ratio_fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["anc_ratio"],
                mode="lines+markers",
                name="Ancillary %",
                line=dict(
                    color=COLORS["accent_cyan"],
                    width=2,
                ),
                marker=dict(size=5),
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Ancillary: %{y:.1f}%"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            ratio_fig,
            data["date"],
            data["anc_ratio"],
            color=COLORS["accent_red"],
            name="Trend",
        )
        ratio_fig.add_hline(
            y=50,
            line_dash="dot",
            line_color=COLORS["text_muted"],
            line_width=1,
            annotation_text="50%",
            annotation_font_color=COLORS[
                "text_muted"
            ],
        )
        apply_theme(ratio_fig)
        ratio_fig.update_layout(
            title=dict(
                text=(
                    "Ancillary vs Arbitrage"
                    " Ratio + Trend"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(
                title="Ancillary % of Total"
            ),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 3: Revenue Stack Projection ---
        proj_fig = go.Figure()
        proj_fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["total"],
                mode="lines",
                name="Total Revenue",
                line=dict(
                    color=COLORS["accent_blue"],
                    width=2.5,
                ),
                hovertemplate=(
                    "\u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            proj_fig,
            data["date"],
            data["total"],
            color=COLORS["accent_amber"],
            name="Trend",
        )
        add_projection_trace(
            proj_fig,
            list(data["date"]),
            data["total"],
            n_future=12,
            color=COLORS["accent_cyan"],
            name="12M Projection",
        )
        apply_theme(proj_fig)
        proj_fig.update_layout(
            title=dict(
                text=(
                    "Combined Revenue Stack"
                    " + 12M Projection"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 4: Revenue Reliability ---
        # Monthly minimum revenue trend
        # Use rolling 3-month minimum
        data["rolling_min"] = (
            data["total"]
            .rolling(3, min_periods=1)
            .min()
        )
        rel_fig = go.Figure()
        rel_fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["total"],
                mode="lines",
                name="Monthly Revenue",
                line=dict(
                    color=COLORS["accent_blue"],
                    width=1,
                ),
                opacity=0.4,
            )
        )
        rel_fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["rolling_min"],
                mode="lines",
                name="3M Rolling Min",
                line=dict(
                    color=COLORS[
                        "accent_green"
                    ],
                    width=2.5,
                ),
                fill="tozeroy",
                fillcolor=(
                    "rgba(16,185,129,0.1)"
                ),
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Min: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            rel_fig,
            data["date"],
            data["rolling_min"],
            color=COLORS["accent_red"],
            name="Reliability Trend",
        )
        apply_theme(rel_fig)
        rel_fig.update_layout(
            title=dict(
                text=(
                    "Revenue Reliability"
                    " (3M Rolling Minimum)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        return (
            kpis,
            stack_fig,
            ratio_fig,
            proj_fig,
            rel_fig,
        )
