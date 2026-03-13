"""Tab 1: Strategic Overview — executive summary of BESS investment signals."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_projection_trace,
    add_trendline_trace,
    compute_linear_trend,
    strategic_signal,
    trend_arrow,
)
from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_day_ahead_prices,
    fetch_generation_by_source,
    fetch_renewable_vs_nonrenewable,
)


def layout():
    return html.Div(
        [
            html.Div(id="es-overview-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-overview-re-trajectory",
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
                            id="es-overview-spread-evo",
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
                    id="es-overview-signals",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                id="es-overview-signal-table",
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("es-overview-kpis", "children"),
            Output(
                "es-overview-re-trajectory", "figure"
            ),
            Output(
                "es-overview-spread-evo", "figure"
            ),
            Output(
                "es-overview-signals", "figure"
            ),
            Output(
                "es-overview-signal-table", "children"
            ),
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

        re_df = fetch_renewable_vs_nonrenewable(
            start_dt, end_dt, time_trunc="month"
        )
        price_df = fetch_day_ahead_prices(
            start_dt, end_dt
        )
        gen_df = fetch_generation_by_source(
            start_dt, end_dt, time_trunc="month"
        )

        # --- Monthly RE penetration ---
        if (
            not re_df.empty
            and "renewable_mw" in re_df.columns
            and "non_renewable_mw" in re_df.columns
        ):
            re_df["total_mw"] = (
                re_df["renewable_mw"]
                + re_df["non_renewable_mw"]
            )
            re_df["re_pct"] = (
                re_df["renewable_mw"]
                / re_df["total_mw"].replace(
                    0, float("nan")
                )
                * 100
            )
            re_monthly = re_df.dropna(
                subset=["re_pct"]
            )
        else:
            re_monthly = pd.DataFrame()

        # --- Monthly price stats ---
        if not price_df.empty:
            p = price_df.copy()
            p["month"] = p[
                "timestamp"
            ].dt.to_period("M")
            p["hour"] = p["timestamp"].dt.hour

            monthly_price = (
                p.groupby("month")
                .agg(
                    avg_price=(
                        "price_eur_mwh",
                        "mean",
                    ),
                    std_price=(
                        "price_eur_mwh",
                        "std",
                    ),
                )
                .reset_index()
            )
            monthly_price["month_dt"] = monthly_price[
                "month"
            ].apply(lambda x: x.to_timestamp())

            # Peak/off-peak spread
            peak = (
                p[p["hour"].between(8, 19)]
                .groupby("month")["price_eur_mwh"]
                .mean()
            )
            offpeak = (
                p[~p["hour"].between(8, 19)]
                .groupby("month")["price_eur_mwh"]
                .mean()
            )
            spread_df = pd.DataFrame({
                "month": peak.index,
                "peak": peak.values,
                "offpeak": offpeak.reindex(
                    peak.index
                ).values,
            }).dropna()
            spread_df["spread"] = (
                spread_df["peak"]
                - spread_df["offpeak"]
            )
            spread_df["month_dt"] = spread_df[
                "month"
            ].apply(lambda x: x.to_timestamp())

            # Negative price hours per month
            neg_hours = (
                p[p["price_eur_mwh"] < 0]
                .groupby("month")
                .size()
                .reset_index(name="neg_hours")
            )
            neg_hours["month_dt"] = neg_hours[
                "month"
            ].apply(lambda x: x.to_timestamp())
        else:
            monthly_price = pd.DataFrame()
            spread_df = pd.DataFrame()
            neg_hours = pd.DataFrame()

        # --- KPIs with trend arrows ---
        re_val = "N/A"
        re_sub = ""
        spread_val = "N/A"
        spread_sub = ""
        neg_val = "N/A"
        neg_sub = ""
        rev_val = "N/A"
        rev_sub = ""

        if not re_monthly.empty and len(re_monthly) > 1:
            current_re = re_monthly[
                "re_pct"
            ].iloc[-1]
            prev_re = re_monthly["re_pct"].iloc[-2]
            arrow, _ = trend_arrow(
                current_re, prev_re
            )
            re_val = f"{current_re:.1f}%"
            re_sub = f"MoM{arrow}"

        if not spread_df.empty and len(spread_df) > 1:
            current_sp = spread_df[
                "spread"
            ].iloc[-1]
            prev_sp = spread_df["spread"].iloc[-2]
            arrow, _ = trend_arrow(
                current_sp, prev_sp
            )
            spread_val = (
                f"{current_sp:.1f} EUR/MWh"
            )
            spread_sub = f"MoM{arrow}"

        if (
            not neg_hours.empty
            and len(neg_hours) > 1
        ):
            current_neg = neg_hours[
                "neg_hours"
            ].iloc[-1]
            prev_neg = neg_hours[
                "neg_hours"
            ].iloc[-2]
            arrow, _ = trend_arrow(
                current_neg, prev_neg
            )
            neg_val = str(int(current_neg))
            neg_sub = f"MoM{arrow}"

        # Estimated monthly BESS revenue (simple)
        if not spread_df.empty:
            mwh = 20  # 10 MW x 2h
            eff = 0.85
            current_rev = (
                spread_df["spread"].iloc[-1]
                * mwh
                * eff
                * 30
            )
            if len(spread_df) > 1:
                prev_rev = (
                    spread_df["spread"].iloc[-2]
                    * mwh
                    * eff
                    * 30
                )
                arrow, _ = trend_arrow(
                    current_rev, prev_rev
                )
                rev_sub = f"MoM{arrow}"
            rev_val = f"\u20ac{current_rev:,.0f}"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "RE Penetration",
                        re_val,
                        re_sub,
                        color=COLORS[
                            "accent_green"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg Monthly Spread",
                        spread_val,
                        spread_sub,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Neg Price Hrs/Month",
                        neg_val,
                        neg_sub,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Est. Monthly Revenue",
                        rev_val,
                        rev_sub + " (10MW/2h)",
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

        # --- Chart 1: RE Penetration Trajectory ---
        if not re_monthly.empty:
            re_fig = go.Figure()
            re_fig.add_trace(
                go.Scatter(
                    x=re_monthly["timestamp"],
                    y=re_monthly["re_pct"],
                    mode="lines+markers",
                    name="RE %",
                    line=dict(
                        color=COLORS[
                            "accent_green"
                        ],
                        width=2.5,
                    ),
                    marker=dict(size=5),
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "RE: %{y:.1f}%"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                re_fig,
                re_monthly["timestamp"],
                re_monthly["re_pct"],
                color=COLORS["accent_red"],
                name="Linear Trend",
            )
            add_projection_trace(
                re_fig,
                list(re_monthly["timestamp"]),
                re_monthly["re_pct"],
                n_future=12,
                color=COLORS["accent_cyan"],
                name="12M Projection",
            )
            apply_theme(re_fig)
            re_fig.update_layout(
                title=dict(
                    text=(
                        "RE Penetration Trajectory"
                        " + 12M Projection"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="Renewable %"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            re_fig = _empty_figure(
                "RE Penetration Trajectory"
            )

        # --- Chart 2: Spread Evolution ---
        if not spread_df.empty:
            spread_fig = go.Figure()
            spread_fig.add_trace(
                go.Bar(
                    x=spread_df["month_dt"],
                    y=spread_df["spread"],
                    name="Peak/Off-Peak Spread",
                    marker_color=COLORS[
                        "accent_amber"
                    ],
                    marker_line_width=0,
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "Spread: %{y:.1f} EUR/MWh"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                spread_fig,
                spread_df["month_dt"],
                spread_df["spread"],
                color=COLORS["accent_red"],
                name="Trend",
            )
            apply_theme(spread_fig)
            spread_fig.update_layout(
                title=dict(
                    text=(
                        "Monthly Peak/Off-Peak"
                        " Spread Evolution"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="EUR/MWh"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            spread_fig = _empty_figure(
                "Spread Evolution"
            )

        # --- Chart 3: Key Signals (multi-line) ---
        signals_fig = go.Figure()
        has_signal = False

        if not re_monthly.empty:
            signals_fig.add_trace(
                go.Scatter(
                    x=re_monthly["timestamp"],
                    y=re_monthly["re_pct"],
                    name="RE %",
                    mode="lines",
                    line=dict(
                        color=COLORS[
                            "accent_green"
                        ],
                        width=2,
                    ),
                    yaxis="y",
                )
            )
            has_signal = True

        if not spread_df.empty:
            signals_fig.add_trace(
                go.Scatter(
                    x=spread_df["month_dt"],
                    y=spread_df["spread"],
                    name="Spread EUR/MWh",
                    mode="lines",
                    line=dict(
                        color=COLORS[
                            "accent_amber"
                        ],
                        width=2,
                    ),
                    yaxis="y2",
                )
            )
            has_signal = True

        if not neg_hours.empty:
            signals_fig.add_trace(
                go.Scatter(
                    x=neg_hours["month_dt"],
                    y=neg_hours["neg_hours"],
                    name="Neg Price Hours",
                    mode="lines",
                    line=dict(
                        color=COLORS[
                            "accent_red"
                        ],
                        width=2,
                    ),
                    yaxis="y3",
                )
            )
            has_signal = True

        if has_signal:
            apply_theme(signals_fig)
            signals_fig.update_layout(
                title=dict(
                    text=(
                        "Key Strategic Signals"
                        " — Multi-Axis"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(
                    title="RE %",
                    titlefont=dict(
                        color=COLORS[
                            "accent_green"
                        ]
                    ),
                    side="left",
                ),
                yaxis2=dict(
                    title="Spread (EUR/MWh)",
                    titlefont=dict(
                        color=COLORS[
                            "accent_amber"
                        ]
                    ),
                    overlaying="y",
                    side="right",
                    gridcolor="rgba(0,0,0,0)",
                ),
                yaxis3=dict(
                    title="Neg Hours",
                    titlefont=dict(
                        color=COLORS[
                            "accent_red"
                        ]
                    ),
                    overlaying="y",
                    side="right",
                    position=0.95,
                    gridcolor="rgba(0,0,0,0)",
                ),
                legend=dict(
                    orientation="h", y=-0.15
                ),
                hovermode="x unified",
            )
        else:
            signals_fig = _empty_figure(
                "Key Signals"
            )

        # --- Signal Table ---
        signals = []

        if not re_monthly.empty:
            slope, _, r2 = compute_linear_trend(
                re_monthly["re_pct"]
            )
            label, color = strategic_signal(
                slope, 0.3, 0.05
            )
            signals.append(
                ("RE Growth Rate", f"{slope:.2f} pp/mo", label, color)
            )

        if not spread_df.empty:
            slope, _, _ = compute_linear_trend(
                spread_df["spread"]
            )
            label, color = strategic_signal(
                slope, 0.2, -0.1
            )
            signals.append(
                ("Spread Trend", f"{slope:.2f} EUR/MWh/mo", label, color)
            )

        if (
            not monthly_price.empty
            and "std_price" in monthly_price.columns
        ):
            slope, _, _ = compute_linear_trend(
                monthly_price["std_price"]
            )
            label, color = strategic_signal(
                slope, 0.1, -0.1
            )
            signals.append(
                ("Volatility Trend", f"{slope:.2f}/mo", label, color)
            )

        if not neg_hours.empty:
            slope, _, _ = compute_linear_trend(
                neg_hours["neg_hours"].astype(float)
            )
            label, color = strategic_signal(
                slope, 0.5, 0.0
            )
            signals.append(
                ("Neg Hours Growth", f"{slope:.1f} hrs/mo", label, color)
            )

        if signals:
            header = html.Div(
                "Strategic Signal Summary",
                style={
                    "color": COLORS["text"],
                    "fontSize": "15px",
                    "fontWeight": "600",
                    "marginBottom": "12px",
                },
            )
            rows = []
            for (
                name,
                value,
                label,
                color,
            ) in signals:
                rows.append(
                    html.Div(
                        [
                            html.Span(
                                name,
                                style={
                                    "color": COLORS[
                                        "text_muted"
                                    ],
                                    "width": "200px",
                                    "display": (
                                        "inline-block"
                                    ),
                                },
                            ),
                            html.Span(
                                value,
                                style={
                                    "color": COLORS[
                                        "text"
                                    ],
                                    "width": "200px",
                                    "display": (
                                        "inline-block"
                                    ),
                                },
                            ),
                            html.Span(
                                f"\u25cf {label}",
                                style={
                                    "color": color,
                                    "fontWeight": (
                                        "600"
                                    ),
                                },
                            ),
                        ],
                        style={
                            "padding": "8px 0",
                            "borderBottom": (
                                "1px solid "
                                + COLORS[
                                    "card_border"
                                ]
                            ),
                        },
                    )
                )
            signal_table = html.Div(
                [header] + rows
            )
        else:
            signal_table = html.Div(
                "No signal data available",
                style={
                    "color": COLORS["text_muted"]
                },
            )

        return (
            kpis,
            re_fig,
            spread_fig,
            signals_fig,
            signal_table,
        )
