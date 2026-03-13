"""Tab 4: Duck Curve Evolution — residual load changes driving BESS value."""

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
    fetch_generation_by_source,
    fetch_total_load,
)


def _compute_residual_monthly(load_df, gen_df):
    """Compute monthly residual load stats."""
    if load_df.empty or gen_df.empty:
        return pd.DataFrame()

    ws_cols = [
        c
        for c in [
            "solar_pv",
            "solar_thermal",
            "wind",
        ]
        if c in gen_df.columns
    ]
    if not ws_cols:
        return pd.DataFrame()

    gen_sub = gen_df[
        ["timestamp"] + ws_cols
    ].copy()
    gen_sub["renewable_mw"] = gen_sub[
        ws_cols
    ].sum(axis=1)

    merged = pd.merge_asof(
        load_df.sort_values("timestamp"),
        gen_sub[
            ["timestamp", "renewable_mw"]
        ].sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
    )
    merged["residual_load"] = (
        merged["load_mw"]
        - merged["renewable_mw"]
    )
    return merged


def layout():
    return html.Div(
        [
            html.Div(id="es-residual-kpis"),
            html.Div(
                dcc.Graph(
                    id="es-residual-monthly",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-residual-duck",
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
                            id="es-residual-neg-trend",
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
                    id="es-residual-min-deriv",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("es-residual-kpis", "children"),
            Output(
                "es-residual-monthly", "figure"
            ),
            Output("es-residual-duck", "figure"),
            Output(
                "es-residual-neg-trend", "figure"
            ),
            Output(
                "es-residual-min-deriv", "figure"
            ),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_residual(start_date, end_date):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()

        load_df = fetch_total_load(
            start, end, time_trunc="month"
        )
        gen_df = fetch_generation_by_source(
            start, end, time_trunc="month"
        )

        # Also fetch daily for duck curve overlay
        load_daily = fetch_total_load(start, end)
        gen_daily = fetch_generation_by_source(
            start, end
        )

        merged_m = _compute_residual_monthly(
            load_df, gen_df
        )
        merged_d = _compute_residual_monthly(
            load_daily, gen_daily
        )

        # Monthly stats from daily data
        if not merged_d.empty:
            md = merged_d.copy()
            md["month"] = md[
                "timestamp"
            ].dt.to_period("M")
            monthly_stats = (
                md.groupby("month")
                .agg(
                    avg_residual=(
                        "residual_load",
                        "mean",
                    ),
                    min_residual=(
                        "residual_load",
                        "min",
                    ),
                    max_residual=(
                        "residual_load",
                        "max",
                    ),
                )
                .reset_index()
            )
            monthly_stats["month_dt"] = (
                monthly_stats["month"].apply(
                    lambda x: x.to_timestamp()
                )
            )
            neg_res = (
                md[md["residual_load"] < 0]
                .groupby("month")
                .size()
                .reset_index(name="neg_count")
            )
            neg_res["month_dt"] = neg_res[
                "month"
            ].apply(lambda x: x.to_timestamp())
        else:
            monthly_stats = pd.DataFrame()
            neg_res = pd.DataFrame()

        # --- KPIs ---
        avg_trend = "N/A"
        min_res = "N/A"
        neg_trend = "N/A"
        duck_depth = "N/A"

        if not monthly_stats.empty:
            slope, _, _ = compute_linear_trend(
                monthly_stats["avg_residual"]
            )
            avg_trend = (
                f"{slope * 12:,.0f} MW/year"
            )
            min_res = (
                f"{monthly_stats['min_residual'].iloc[-1]:,.0f}"
                " MW"
            )
            if not neg_res.empty:
                neg_slope, _, _ = (
                    compute_linear_trend(
                        neg_res["neg_count"].astype(
                            float
                        )
                    )
                )
                neg_trend = (
                    f"{neg_slope:+.1f}/mo"
                )
            # Duck depth rate
            min_slope, _, _ = (
                compute_linear_trend(
                    monthly_stats["min_residual"]
                )
            )
            duck_depth = (
                f"{min_slope * 12:,.0f} MW/year"
            )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Avg Residual Trend",
                        avg_trend,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Latest Min Residual",
                        min_res,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Neg Residual Hrs/Mo",
                        neg_trend,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Duck Depth Rate",
                        duck_depth,
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

        # --- Chart 1: Monthly Residual Envelope ---
        if not monthly_stats.empty:
            m_fig = go.Figure()
            m_fig.add_trace(
                go.Scatter(
                    x=monthly_stats["month_dt"],
                    y=monthly_stats[
                        "max_residual"
                    ],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
            m_fig.add_trace(
                go.Scatter(
                    x=monthly_stats["month_dt"],
                    y=monthly_stats[
                        "min_residual"
                    ],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor=(
                        "rgba(6,182,212,0.15)"
                    ),
                    name="Min-Max Band",
                    hoverinfo="skip",
                )
            )
            m_fig.add_trace(
                go.Scatter(
                    x=monthly_stats["month_dt"],
                    y=monthly_stats[
                        "avg_residual"
                    ],
                    mode="lines+markers",
                    name="Avg Residual",
                    line=dict(
                        color=COLORS[
                            "accent_cyan"
                        ],
                        width=2.5,
                    ),
                    marker=dict(size=5),
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "Avg: %{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                m_fig,
                monthly_stats["month_dt"],
                monthly_stats["avg_residual"],
                color=COLORS["accent_red"],
                name="Trend",
            )
            m_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color=COLORS["accent_red"],
                line_width=1,
            )
            apply_theme(m_fig)
            m_fig.update_layout(
                title=dict(
                    text=(
                        "Monthly Residual Load"
                        " (Avg + Min/Max Band)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            m_fig = _empty_figure(
                "Monthly Residual"
            )

        # --- Chart 2: Duck Curve Overlay ---
        if not merged_d.empty:
            duck_fig = go.Figure()
            md = merged_d.copy()
            md["hour"] = md["timestamp"].dt.hour
            md["quarter"] = (
                md["timestamp"]
                .dt.to_period("Q")
                .astype(str)
            )
            unique_q = sorted(
                md["quarter"].unique()
            )
            # Pick up to 4 quarters spread out
            if len(unique_q) > 4:
                step = max(1, len(unique_q) // 4)
                q_pick = unique_q[::step][:4]
            else:
                q_pick = unique_q

            q_colors = [
                COLORS["accent_blue"],
                COLORS["accent_green"],
                COLORS["accent_amber"],
                COLORS["accent_red"],
            ]
            for i, q in enumerate(q_pick):
                q_data = md[md["quarter"] == q]
                hourly_avg = (
                    q_data.groupby("hour")[
                        "residual_load"
                    ]
                    .mean()
                    .reset_index()
                )
                duck_fig.add_trace(
                    go.Scatter(
                        x=hourly_avg["hour"],
                        y=hourly_avg[
                            "residual_load"
                        ],
                        mode="lines",
                        name=q,
                        line=dict(
                            color=q_colors[
                                i
                                % len(q_colors)
                            ],
                            width=2.5,
                        ),
                        hovertemplate=(
                            f"{q} H%{{x}}: "
                            "%{y:,.0f} MW"
                            "<extra></extra>"
                        ),
                    )
                )
            duck_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(duck_fig)
            duck_fig.update_layout(
                title=dict(
                    text=(
                        "Duck Curve Overlay"
                        " by Quarter"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(
                    title="Hour of Day",
                    dtick=2,
                ),
                yaxis=dict(title="MW"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            duck_fig = _empty_figure(
                "Duck Curve"
            )

        # --- Chart 3: Negative Residual Hours ---
        if not neg_res.empty:
            neg_fig = go.Figure()
            neg_fig.add_trace(
                go.Bar(
                    x=neg_res["month_dt"],
                    y=neg_res["neg_count"],
                    marker_color=COLORS[
                        "accent_green"
                    ],
                    marker_line_width=0,
                    name="Neg Hours",
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "%{y} intervals"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                neg_fig,
                neg_res["month_dt"],
                neg_res["neg_count"].astype(
                    float
                ),
                color=COLORS["accent_red"],
                name="Trend",
            )
            apply_theme(neg_fig)
            neg_fig.update_layout(
                title=dict(
                    text=(
                        "Negative Residual"
                        " Hours/Month + Trend"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="Count"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            neg_fig = _empty_figure(
                "Negative Residual Hours"
            )

        # --- Chart 4: Min Residual 1st Derivative ---
        if not monthly_stats.empty:
            d1 = compute_monthly_derivative(
                monthly_stats["min_residual"]
            )
            colors = [
                COLORS["accent_green"]
                if v <= 0
                else COLORS["accent_red"]
                for v in d1.fillna(0)
            ]
            min_d_fig = go.Figure(
                go.Bar(
                    x=monthly_stats["month_dt"],
                    y=d1,
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "Change: %{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            min_d_fig.add_hline(
                y=0,
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(min_d_fig)
            min_d_fig.update_layout(
                title=dict(
                    text=(
                        "Min Residual Load"
                        " \u2014 1st Derivative"
                        " (Deepening Rate)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(
                    title="MoM Change (MW)"
                ),
            )
        else:
            min_d_fig = _empty_figure(
                "Min Residual Derivative"
            )

        return (
            kpis,
            m_fig,
            duck_fig,
            neg_fig,
            min_d_fig,
        )
