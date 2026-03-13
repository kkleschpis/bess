"""Tab 6: Curtailment & Oversupply Trends — solar oversupply trajectory."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_trendline_trace,
    compute_linear_trend,
    compute_monthly_derivative,
)
from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_day_ahead_prices,
    fetch_generation_by_source,
)


def layout():
    return html.Div(
        [
            html.Div(id="es-curtailment-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-curtailment-solar-trend",
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
                            id="es-curtailment-events",
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
                            id="es-curtailment-deriv",
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
                            id="es-curtailment-corr",
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
                "es-curtailment-kpis", "children"
            ),
            Output(
                "es-curtailment-solar-trend",
                "figure",
            ),
            Output(
                "es-curtailment-events", "figure"
            ),
            Output(
                "es-curtailment-deriv", "figure"
            ),
            Output(
                "es-curtailment-corr", "figure"
            ),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_curtailment(start_date, end_date):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()

        gen = fetch_generation_by_source(
            start, end, time_trunc="month"
        )
        gen_daily = fetch_generation_by_source(
            start, end
        )
        prices = fetch_day_ahead_prices(
            start, end
        )

        source_cols = [
            c
            for c in gen.columns
            if c != "timestamp"
        ]
        source_cols_d = [
            c
            for c in gen_daily.columns
            if c != "timestamp"
        ]

        # Monthly solar penetration from monthly data
        if not gen.empty and source_cols:
            solar_cols = [
                c
                for c in [
                    "solar_pv",
                    "solar_thermal",
                ]
                if c in gen.columns
            ]
            if solar_cols:
                gm = gen.copy()
                gm["solar_total"] = gm[
                    solar_cols
                ].sum(axis=1)
                gm["total_gen"] = gm[
                    source_cols
                ].sum(axis=1)
                gm["solar_pct"] = (
                    gm["solar_total"]
                    / gm["total_gen"].replace(
                        0, float("nan")
                    )
                    * 100
                )
                gm["max_solar_pct"] = gm[
                    "solar_pct"
                ]
            else:
                gm = pd.DataFrame()
        else:
            gm = pd.DataFrame()

        # Daily analysis for curtailment events
        if (
            not gen_daily.empty
            and source_cols_d
        ):
            solar_cols_d = [
                c
                for c in [
                    "solar_pv",
                    "solar_thermal",
                ]
                if c in gen_daily.columns
            ]
            if solar_cols_d:
                gd = gen_daily.copy()
                gd["solar_total"] = gd[
                    solar_cols_d
                ].sum(axis=1)
                gd["total_gen"] = gd[
                    source_cols_d
                ].sum(axis=1)
                gd["solar_pct"] = (
                    gd["solar_total"]
                    / gd["total_gen"].replace(
                        0, float("nan")
                    )
                    * 100
                )
                gd["month"] = gd[
                    "timestamp"
                ].dt.to_period("M")

                # Hours where solar >50%
                curtail_monthly = (
                    gd[gd["solar_pct"] > 50]
                    .groupby("month")
                    .size()
                    .reset_index(
                        name="curtail_hours"
                    )
                )
                curtail_monthly["month_dt"] = (
                    curtail_monthly["month"].apply(
                        lambda x: x.to_timestamp()
                    )
                )
            else:
                gd = pd.DataFrame()
                curtail_monthly = pd.DataFrame()
        else:
            gd = pd.DataFrame()
            curtail_monthly = pd.DataFrame()

        # --- KPIs ---
        solar_trend = "N/A"
        max_solar = "N/A"
        corr_str = "N/A"
        oversupply = "N/A"

        if not gm.empty and "solar_pct" in gm.columns:
            slope, _, _ = compute_linear_trend(
                gm["solar_pct"]
            )
            solar_trend = (
                f"{slope:+.2f} pp/mo"
            )
            max_solar = (
                f"{gm['solar_pct'].max():.1f}%"
            )

        if (
            not curtail_monthly.empty
            and len(curtail_monthly) > 0
        ):
            last_val = curtail_monthly[
                "curtail_hours"
            ].iloc[-1]
            oversupply = f"{int(last_val)} hrs/mo"

        # Solar-price correlation
        if not gd.empty and not prices.empty:
            merged = pd.merge_asof(
                gd[
                    ["timestamp", "solar_pct"]
                ].sort_values("timestamp"),
                prices.sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            corr_val = merged[
                "solar_pct"
            ].corr(merged["price_eur_mwh"])
            if not np.isnan(corr_val):
                corr_str = f"{corr_val:.3f}"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Solar Share Trend",
                        solar_trend,
                        "Monthly slope",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Max Solar Penetration",
                        max_solar,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Solar/Price Correlation",
                        corr_str,
                        "Negative = cannibalisation",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Solar >50% Hours",
                        oversupply,
                        "Latest month",
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

        # --- Chart 1: Monthly Solar Penetration Trend ---
        if not gm.empty and "solar_pct" in gm.columns:
            solar_fig = go.Figure()
            solar_fig.add_trace(
                go.Scatter(
                    x=gm["timestamp"],
                    y=gm["solar_pct"],
                    mode="lines+markers",
                    name="Avg Solar %",
                    line=dict(
                        color=COLORS[
                            "accent_amber"
                        ],
                        width=2.5,
                    ),
                    marker=dict(size=5),
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "Solar: %{y:.1f}%"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                solar_fig,
                gm["timestamp"],
                gm["solar_pct"],
                color=COLORS["accent_red"],
                name="Trend",
            )
            apply_theme(solar_fig)
            solar_fig.update_layout(
                title=dict(
                    text=(
                        "Monthly Solar Penetration"
                        " + Trend"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(
                    title="Solar Share (%)"
                ),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            solar_fig = _empty_figure(
                "Solar Penetration"
            )

        # --- Chart 2: Curtailment Events/Month ---
        if not curtail_monthly.empty:
            curt_fig = go.Figure()
            curt_fig.add_trace(
                go.Bar(
                    x=curtail_monthly["month_dt"],
                    y=curtail_monthly[
                        "curtail_hours"
                    ],
                    marker_color=COLORS[
                        "accent_red"
                    ],
                    marker_line_width=0,
                    name="Hours >50% Solar",
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "%{y} hours"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                curt_fig,
                curtail_monthly["month_dt"],
                curtail_monthly[
                    "curtail_hours"
                ].astype(float),
                color=COLORS["accent_amber"],
                name="Trend",
            )
            apply_theme(curt_fig)
            curt_fig.update_layout(
                title=dict(
                    text=(
                        "Curtailment Events/Month"
                        " (Solar >50%) + Trend"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="Hours"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            curt_fig = go.Figure()
            curt_fig.add_annotation(
                text="No curtailment events detected",
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
            apply_theme(curt_fig)
            curt_fig.update_layout(
                title=dict(
                    text="Curtailment Events",
                    font=dict(size=15),
                ),
            )

        # --- Chart 3: Solar Penetration 1st Derivative ---
        if not gm.empty and "solar_pct" in gm.columns:
            d1 = compute_monthly_derivative(
                gm["solar_pct"]
            )
            colors = [
                COLORS["accent_green"]
                if v >= 0
                else COLORS["accent_red"]
                for v in d1.fillna(0)
            ]
            deriv_fig = go.Figure(
                go.Bar(
                    x=gm["timestamp"],
                    y=d1,
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "Change: %{y:+.2f} pp"
                        "<extra></extra>"
                    ),
                )
            )
            deriv_fig.add_hline(
                y=0,
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(deriv_fig)
            deriv_fig.update_layout(
                title=dict(
                    text=(
                        "Solar Penetration"
                        " \u2014 1st Derivative"
                        " (Rate of Increase)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(
                    title="MoM Change (pp)"
                ),
            )
        else:
            deriv_fig = _empty_figure(
                "Solar 1st Derivative"
            )

        # --- Chart 4: Rolling Correlation ---
        if not gd.empty and not prices.empty:
            merged = pd.merge_asof(
                gd[
                    ["timestamp", "solar_pct"]
                ].sort_values("timestamp"),
                prices.sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            merged["month"] = merged[
                "timestamp"
            ].dt.to_period("M")
            monthly_corr = (
                merged.groupby("month")
                .apply(
                    lambda g: g[
                        "solar_pct"
                    ].corr(g["price_eur_mwh"]),
                    include_groups=False,
                )
                .reset_index(name="correlation")
            )
            monthly_corr["month_dt"] = (
                monthly_corr["month"].apply(
                    lambda x: x.to_timestamp()
                )
            )

            if not monthly_corr.empty:
                corr_fig = go.Figure()
                corr_fig.add_trace(
                    go.Scatter(
                        x=monthly_corr[
                            "month_dt"
                        ],
                        y=monthly_corr[
                            "correlation"
                        ],
                        mode="lines+markers",
                        line=dict(
                            color=COLORS[
                                "accent_cyan"
                            ],
                            width=2,
                        ),
                        marker=dict(size=5),
                        hovertemplate=(
                            "%{x|%Y-%m}<br>"
                            "Corr: %{y:.3f}"
                            "<extra></extra>"
                        ),
                    )
                )
                add_trendline_trace(
                    corr_fig,
                    monthly_corr["month_dt"],
                    monthly_corr["correlation"],
                    color=COLORS["accent_red"],
                    name="Trend",
                )
                corr_fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color=COLORS[
                        "text_muted"
                    ],
                    line_width=1,
                )
                apply_theme(corr_fig)
                corr_fig.update_layout(
                    title=dict(
                        text=(
                            "Solar % vs Price"
                            " \u2014 Monthly"
                            " Correlation"
                        ),
                        font=dict(size=15),
                    ),
                    yaxis=dict(
                        title="Correlation"
                    ),
                    legend=dict(
                        orientation="h",
                        y=-0.15,
                    ),
                )
            else:
                corr_fig = _empty_figure(
                    "Solar-Price Correlation"
                )
        else:
            corr_fig = _empty_figure(
                "Solar-Price Correlation"
            )

        return (
            kpis,
            solar_fig,
            curt_fig,
            deriv_fig,
            corr_fig,
        )
