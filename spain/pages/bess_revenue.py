"""Tab 5: BESS Revenue Outlook — long-term revenue trajectory and viability."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_projection_trace,
    add_trendline_trace,
    compute_linear_trend,
)
from components.charts import _empty_figure
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
                            "color": COLORS[
                                "text_muted"
                            ],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Input(
                        id="es-bess-mw",
                        type="number",
                        value=10,
                        min=1,
                        max=500,
                        step=1,
                        style={
                            "backgroundColor": (
                                COLORS["bg"]
                            ),
                            "color": COLORS[
                                "text"
                            ],
                            "border": (
                                "1px solid "
                                + COLORS[
                                    "card_border"
                                ]
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
                            "color": COLORS[
                                "text_muted"
                            ],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Dropdown(
                        id="es-bess-duration",
                        options=[
                            {
                                "label": "1h",
                                "value": 1,
                            },
                            {
                                "label": "2h",
                                "value": 2,
                            },
                            {
                                "label": "4h",
                                "value": 4,
                            },
                        ],
                        value=2,
                        clearable=False,
                        style={
                            "width": "100px",
                            "backgroundColor": (
                                COLORS["bg"]
                            ),
                            "color": COLORS[
                                "text"
                            ],
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
                            "color": COLORS[
                                "text_muted"
                            ],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Slider(
                        id="es-bess-efficiency",
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
                    "marginRight": "24px",
                },
            ),
            html.Div(
                [
                    html.Label(
                        "CAPEX (EUR/kWh)",
                        style={
                            "color": COLORS[
                                "text_muted"
                            ],
                            "fontSize": "12px",
                            "marginBottom": "4px",
                            "display": "block",
                        },
                    ),
                    dcc.Input(
                        id="es-bess-capex",
                        type="number",
                        value=250,
                        min=50,
                        max=800,
                        step=10,
                        style={
                            "backgroundColor": (
                                COLORS["bg"]
                            ),
                            "color": COLORS[
                                "text"
                            ],
                            "border": (
                                "1px solid "
                                + COLORS[
                                    "card_border"
                                ]
                            ),
                            "borderRadius": "6px",
                            "padding": "8px 12px",
                            "width": "100px",
                        },
                    ),
                ],
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
            html.Div(id="es-bess-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-bess-monthly-rev",
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
                            id="es-bess-breakeven",
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
                            id="es-bess-duration-rev",
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
                            id="es-bess-profitable",
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
                    id="es-bess-stacking",
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
            Output("es-bess-kpis", "children"),
            Output(
                "es-bess-monthly-rev", "figure"
            ),
            Output(
                "es-bess-breakeven", "figure"
            ),
            Output(
                "es-bess-duration-rev", "figure"
            ),
            Output(
                "es-bess-profitable", "figure"
            ),
            Output(
                "es-bess-stacking", "figure"
            ),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
            Input("es-bess-mw", "value"),
            Input("es-bess-duration", "value"),
            Input("es-bess-efficiency", "value"),
            Input("es-bess-capex", "value"),
        ],
    )
    def update_bess(
        start_date,
        end_date,
        mw,
        duration,
        efficiency,
        capex_kwh,
    ):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()
        df = fetch_day_ahead_prices(start, end)

        mw = mw or 10
        duration = duration or 2
        efficiency = (efficiency or 85) / 100.0
        capex_kwh = capex_kwh or 250
        mwh = mw * duration
        total_capex = capex_kwh * mwh * 1000

        if df.empty:
            empty = _empty_figure("No Data")
            kpis = html.Div(
                [
                    html.Div(
                        kpi_card(
                            "Revenue Trend",
                            "N/A",
                        ),
                        style={"flex": "1"},
                    ),
                ] * 4,
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

        # Daily analysis
        p = df.copy()
        p["date"] = p["timestamp"].dt.date
        daily = p.groupby("date").agg(
            price_min=("price_eur_mwh", "min"),
            price_max=("price_eur_mwh", "max"),
        )
        daily["spread"] = (
            daily["price_max"] - daily["price_min"]
        )
        daily["revenue"] = (
            daily["spread"] * mwh * efficiency
        )
        daily = daily.reset_index()
        daily["month"] = pd.to_datetime(
            daily["date"]
        ).dt.to_period("M")

        # Monthly aggregation
        monthly = (
            daily.groupby("month")
            .agg(
                total_rev=("revenue", "sum"),
                avg_spread=("spread", "mean"),
                profitable_days=(
                    "revenue",
                    lambda x: (x > 0).sum(),
                ),
                total_days=("date", "count"),
            )
            .reset_index()
        )
        monthly["month_dt"] = monthly[
            "month"
        ].apply(lambda x: x.to_timestamp())
        monthly["rev_per_mwh"] = (
            monthly["total_rev"] / (mwh * 30)
        )

        # Break-even spread
        # Annual CAPEX amortized over 15 years,
        # daily cycles * 365
        annual_capex = total_capex / 15
        daily_capex = annual_capex / 365
        breakeven_spread = daily_capex / (
            mwh * efficiency
        )

        # --- KPIs ---
        rev_slope, _, _ = compute_linear_trend(
            monthly["total_rev"]
        )
        rev_growth = "N/A"
        if monthly["total_rev"].mean() > 0:
            pct = (
                rev_slope
                / monthly["total_rev"].mean()
                * 100
                * 12
            )
            rev_growth = f"{pct:+.1f}%/year"

        avg_cycles = "~1.0/day"
        if not daily.empty:
            # Simple estimate: profitable days
            prof_ratio = (
                daily["revenue"] > 0
            ).mean()
            avg_cycles = (
                f"~{prof_ratio:.1f}/day"
            )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Revenue Trend",
                        f"{rev_slope:,.0f}"
                        " EUR/mo/mo",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Revenue Growth",
                        rev_growth,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg Profitable Ratio",
                        avg_cycles,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Break-Even Spread",
                        f"{breakeven_spread:.1f}"
                        " EUR/MWh",
                        f"CAPEX {capex_kwh}"
                        " EUR/kWh / 15yr",
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

        # --- Chart 1: Monthly Arbitrage Revenue ---
        rev_fig = go.Figure()
        rev_fig.add_trace(
            go.Bar(
                x=monthly["month_dt"],
                y=monthly["total_rev"],
                name="Monthly Revenue",
                marker_color=COLORS[
                    "accent_green"
                ],
                marker_line_width=0,
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Revenue: \u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            rev_fig,
            monthly["month_dt"],
            monthly["total_rev"],
            color=COLORS["accent_red"],
            name="Trend",
        )
        add_projection_trace(
            rev_fig,
            list(monthly["month_dt"]),
            monthly["total_rev"],
            n_future=12,
            color=COLORS["accent_cyan"],
            name="12M Projection",
        )
        apply_theme(rev_fig)
        rev_fig.update_layout(
            title=dict(
                text=(
                    "Monthly Arbitrage Revenue"
                    " + 12M Projection"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 2: Break-Even Analysis ---
        be_fig = go.Figure()
        be_fig.add_trace(
            go.Bar(
                x=monthly["month_dt"],
                y=monthly["avg_spread"],
                name="Avg Daily Spread",
                marker_color=COLORS[
                    "accent_blue"
                ],
                marker_line_width=0,
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "Spread: %{y:.1f} EUR/MWh"
                    "<extra></extra>"
                ),
            )
        )
        be_fig.add_hline(
            y=breakeven_spread,
            line_dash="dash",
            line_color=COLORS["accent_red"],
            line_width=2,
            annotation_text=(
                f"Break-even:"
                f" {breakeven_spread:.1f}"
                " EUR/MWh"
            ),
            annotation_font_color=COLORS[
                "accent_red"
            ],
        )
        add_trendline_trace(
            be_fig,
            monthly["month_dt"],
            monthly["avg_spread"],
            color=COLORS["accent_amber"],
            name="Spread Trend",
        )
        apply_theme(be_fig)
        be_fig.update_layout(
            title=dict(
                text=(
                    "Break-Even Analysis"
                    " \u2014 Spread vs Threshold"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR/MWh"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 3: Revenue Duration Curve ---
        sorted_rev = np.sort(
            monthly["total_rev"].values
        )[::-1]
        pct = np.linspace(
            0, 100, len(sorted_rev)
        )
        dur_fig = go.Figure(
            go.Scatter(
                x=pct,
                y=sorted_rev,
                mode="lines",
                line=dict(
                    color=COLORS["accent_green"],
                    width=2.5,
                ),
                fill="tozeroy",
                fillcolor=(
                    "rgba(16,185,129,0.1)"
                ),
                hovertemplate=(
                    "%{x:.0f}% of months<br>"
                    "\u20ac%{y:,.0f}"
                    "<extra></extra>"
                ),
            )
        )
        apply_theme(dur_fig)
        dur_fig.update_layout(
            title=dict(
                text=(
                    "Revenue Duration Curve"
                    " (Monthly)"
                ),
                font=dict(size=15),
            ),
            xaxis=dict(title="% of Months"),
            yaxis=dict(title="EUR"),
        )

        # --- Chart 4: Profitable Days/Month ---
        prof_fig = go.Figure()
        prof_fig.add_trace(
            go.Bar(
                x=monthly["month_dt"],
                y=monthly["profitable_days"],
                name="Profitable Days",
                marker_color=COLORS[
                    "accent_amber"
                ],
                marker_line_width=0,
                hovertemplate=(
                    "%{x|%Y-%m}<br>"
                    "%{y} days"
                    "<extra></extra>"
                ),
            )
        )
        add_trendline_trace(
            prof_fig,
            monthly["month_dt"],
            monthly["profitable_days"].astype(
                float
            ),
            color=COLORS["accent_red"],
            name="Trend",
        )
        apply_theme(prof_fig)
        prof_fig.update_layout(
            title=dict(
                text=(
                    "Profitable Days"
                    " per Month + Trend"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="Days"),
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        # --- Chart 5: Revenue Stacking ---
        # Simple estimate: arbitrage + ancillary
        stack_fig = go.Figure()
        arb_rev = monthly["total_rev"].values
        # Estimate ancillary as ~40% of arbitrage
        afrr_est = arb_rev * 0.25
        mfrr_est = arb_rev * 0.15

        stack_fig.add_trace(
            go.Bar(
                x=monthly["month_dt"],
                y=arb_rev,
                name="Arbitrage",
                marker_color=COLORS[
                    "accent_blue"
                ],
                marker_line_width=0,
            )
        )
        stack_fig.add_trace(
            go.Bar(
                x=monthly["month_dt"],
                y=afrr_est,
                name="aFRR (est.)",
                marker_color=COLORS[
                    "accent_green"
                ],
                marker_line_width=0,
            )
        )
        stack_fig.add_trace(
            go.Bar(
                x=monthly["month_dt"],
                y=mfrr_est,
                name="mFRR (est.)",
                marker_color=COLORS[
                    "accent_amber"
                ],
                marker_line_width=0,
            )
        )
        total_stack = arb_rev + afrr_est + mfrr_est
        add_trendline_trace(
            stack_fig,
            monthly["month_dt"],
            pd.Series(total_stack),
            color=COLORS["accent_red"],
            name="Total Trend",
        )
        apply_theme(stack_fig)
        stack_fig.update_layout(
            title=dict(
                text=(
                    "Revenue Stacking Evolution"
                    " (Arb + aFRR + mFRR est.)"
                ),
                font=dict(size=15),
            ),
            yaxis=dict(title="EUR"),
            barmode="stack",
            legend=dict(
                orientation="h", y=-0.15
            ),
        )

        return (
            kpis,
            rev_fig,
            be_fig,
            dur_fig,
            prof_fig,
            stack_fig,
        )
