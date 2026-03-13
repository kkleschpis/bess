"""Tab 7: Cross-Border Flow Trends — market coupling and export dependency."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_trendline_trace,
    compute_linear_trend,
)
from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_cross_border_flows,
    fetch_generation_by_source,
)

BORDER_COLORS = {
    "France": COLORS["accent_blue"],
    "Portugal": COLORS["accent_green"],
    "Morocco": COLORS["accent_amber"],
}


def layout():
    return html.Div(
        [
            html.Div(id="es-interconn-kpis"),
            html.Div(
                dcc.Graph(
                    id="es-interconn-monthly",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-interconn-net-pos",
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
                            id="es-interconn-re-corr",
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
                    id="es-interconn-congestion",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output(
                "es-interconn-kpis", "children"
            ),
            Output(
                "es-interconn-monthly", "figure"
            ),
            Output(
                "es-interconn-net-pos", "figure"
            ),
            Output(
                "es-interconn-re-corr", "figure"
            ),
            Output(
                "es-interconn-congestion",
                "figure",
            ),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_interconnections(
        start_date, end_date
    ):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()

        flows = fetch_cross_border_flows(
            start, end, time_trunc="month"
        )
        gen = fetch_generation_by_source(
            start, end, time_trunc="month"
        )

        # Monthly aggregation from raw flows
        if not flows.empty:
            flows_m = flows.copy()
            flows_m["month"] = flows_m[
                "timestamp"
            ].dt.to_period("M")

            # Per-border monthly avg
            border_monthly = (
                flows_m.groupby(
                    ["month", "country"]
                )["flow_mw"]
                .mean()
                .reset_index()
            )
            border_monthly["month_dt"] = (
                border_monthly["month"].apply(
                    lambda x: x.to_timestamp()
                )
            )

            # Total net position
            net_monthly = (
                flows_m.groupby("month")[
                    "flow_mw"
                ]
                .mean()
                .reset_index(name="net_flow")
            )
            net_monthly["month_dt"] = (
                net_monthly["month"].apply(
                    lambda x: x.to_timestamp()
                )
            )
        else:
            border_monthly = pd.DataFrame()
            net_monthly = pd.DataFrame()

        # --- KPIs ---
        france_str = "N/A"
        portugal_str = "N/A"
        net_str = "N/A"
        export_growth = "N/A"

        if not border_monthly.empty:
            for border in [
                "France",
                "Portugal",
            ]:
                bd = border_monthly[
                    border_monthly["country"]
                    == border
                ]
                if not bd.empty:
                    slope, _, _ = (
                        compute_linear_trend(
                            bd["flow_mw"]
                        )
                    )
                    val = bd["flow_mw"].iloc[-1]
                    direction = (
                        "Export"
                        if val > 0
                        else "Import"
                    )
                    trend_str = (
                        f"{val:,.0f} MW ({direction})"
                    )
                    if border == "France":
                        france_str = trend_str
                    elif border == "Portugal":
                        portugal_str = trend_str

        if not net_monthly.empty:
            net_val = net_monthly[
                "net_flow"
            ].iloc[-1]
            direction = (
                "Net Export"
                if net_val > 0
                else "Net Import"
            )
            net_str = (
                f"{net_val:,.0f} MW ({direction})"
            )
            slope, _, _ = compute_linear_trend(
                net_monthly["net_flow"]
            )
            export_growth = (
                f"{slope * 12:,.0f} MW/year"
            )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "France Net Flow",
                        france_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Portugal Net Flow",
                        portugal_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Net Position",
                        net_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Export Growth Rate",
                        export_growth,
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

        # --- Chart 1: Monthly Flows per Border ---
        if not border_monthly.empty:
            ts_fig = go.Figure()
            for border in [
                "France",
                "Portugal",
                "Morocco",
            ]:
                bd = border_monthly[
                    border_monthly["country"]
                    == border
                ]
                if bd.empty:
                    continue
                ts_fig.add_trace(
                    go.Scatter(
                        x=bd["month_dt"],
                        y=bd["flow_mw"],
                        name=border,
                        mode="lines+markers",
                        line=dict(
                            color=BORDER_COLORS.get(
                                border,
                                COLORS[
                                    "accent_blue"
                                ],
                            ),
                            width=2,
                        ),
                        marker=dict(size=5),
                        hovertemplate=(
                            f"{border}: "
                            "%{y:,.0f} MW"
                            "<extra></extra>"
                        ),
                    )
                )
                add_trendline_trace(
                    ts_fig,
                    bd["month_dt"],
                    bd["flow_mw"],
                    color=BORDER_COLORS.get(
                        border,
                        COLORS["accent_blue"],
                    ),
                    name=f"{border} Trend",
                    dash="dot",
                )
            ts_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(ts_fig)
            ts_fig.update_layout(
                title=dict(
                    text=(
                        "Monthly Cross-Border Flows"
                        " + Trends"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                hovermode="x unified",
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            ts_fig = _empty_figure(
                "Cross-Border Flows"
            )

        # --- Chart 2: Net Position Evolution ---
        if not net_monthly.empty:
            net_fig = go.Figure()
            colors = [
                COLORS["accent_green"]
                if v > 0
                else COLORS["accent_red"]
                for v in net_monthly["net_flow"]
            ]
            net_fig.add_trace(
                go.Bar(
                    x=net_monthly["month_dt"],
                    y=net_monthly["net_flow"],
                    marker_color=colors,
                    marker_line_width=0,
                    name="Net Flow",
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "%{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            add_trendline_trace(
                net_fig,
                net_monthly["month_dt"],
                net_monthly["net_flow"],
                color=COLORS["accent_cyan"],
                name="Trend",
            )
            net_fig.add_hline(
                y=0,
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(net_fig)
            net_fig.update_layout(
                title=dict(
                    text=(
                        "Net Position Evolution"
                        " (+ Export / - Import)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            net_fig = _empty_figure(
                "Net Position"
            )

        # --- Chart 3: Flow vs RE Penetration ---
        source_cols = [
            c
            for c in gen.columns
            if c != "timestamp"
        ]
        if (
            not net_monthly.empty
            and not gen.empty
            and source_cols
        ):
            gm = gen.copy()
            solar_cols = [
                c
                for c in [
                    "solar_pv",
                    "solar_thermal",
                ]
                if c in gm.columns
            ]
            wind_cols = [
                c
                for c in ["wind"]
                if c in gm.columns
            ]
            re_cols = solar_cols + wind_cols
            gm["total"] = gm[
                source_cols
            ].sum(axis=1)
            gm["re_pct"] = (
                gm[re_cols].sum(axis=1)
                / gm["total"].replace(
                    0, float("nan")
                )
                * 100
            )
            gm["month"] = gm[
                "timestamp"
            ].dt.to_period("M")

            re_monthly = (
                gm.groupby("month")["re_pct"]
                .mean()
                .reset_index()
            )
            scatter_data = pd.merge(
                net_monthly,
                re_monthly,
                on="month",
            )

            if not scatter_data.empty:
                re_corr_fig = go.Figure(
                    go.Scatter(
                        x=scatter_data["re_pct"],
                        y=scatter_data[
                            "net_flow"
                        ],
                        mode="markers",
                        marker=dict(
                            color=COLORS[
                                "accent_cyan"
                            ],
                            size=8,
                            opacity=0.7,
                        ),
                        hovertemplate=(
                            "RE: %{x:.1f}%<br>"
                            "Net Flow: %{y:,.0f} MW"
                            "<extra></extra>"
                        ),
                    )
                )
                apply_theme(re_corr_fig)
                re_corr_fig.update_layout(
                    title=dict(
                        text=(
                            "RE Penetration vs"
                            " Net Exports"
                        ),
                        font=dict(size=15),
                    ),
                    xaxis=dict(
                        title="Renewable %"
                    ),
                    yaxis=dict(title="Net MW"),
                )
            else:
                re_corr_fig = _empty_figure(
                    "RE vs Exports"
                )
        else:
            re_corr_fig = _empty_figure(
                "RE vs Exports"
            )

        # --- Chart 4: Congestion Proxy ---
        if not flows.empty:
            flows_c = flows.copy()
            flows_c["month"] = flows_c[
                "timestamp"
            ].dt.to_period("M")

            # Extreme days: flow > 90th percentile or < 10th
            q90 = flows_c["flow_mw"].quantile(
                0.90
            )
            q10 = flows_c["flow_mw"].quantile(
                0.10
            )
            extreme = flows_c[
                (flows_c["flow_mw"] > q90)
                | (flows_c["flow_mw"] < q10)
            ]
            cong_monthly = (
                extreme.groupby("month")
                .size()
                .reset_index(name="extreme_days")
            )
            cong_monthly["month_dt"] = (
                cong_monthly["month"].apply(
                    lambda x: x.to_timestamp()
                )
            )

            if not cong_monthly.empty:
                cong_fig = go.Figure()
                cong_fig.add_trace(
                    go.Bar(
                        x=cong_monthly[
                            "month_dt"
                        ],
                        y=cong_monthly[
                            "extreme_days"
                        ],
                        marker_color=COLORS[
                            "accent_purple"
                        ],
                        marker_line_width=0,
                        hovertemplate=(
                            "%{x|%Y-%m}<br>"
                            "%{y} extreme days"
                            "<extra></extra>"
                        ),
                    )
                )
                add_trendline_trace(
                    cong_fig,
                    cong_monthly["month_dt"],
                    cong_monthly[
                        "extreme_days"
                    ].astype(float),
                    color=COLORS["accent_red"],
                    name="Trend",
                )
                apply_theme(cong_fig)
                cong_fig.update_layout(
                    title=dict(
                        text=(
                            "Congestion Proxy"
                            " \u2014 Extreme Flow"
                            " Days/Month"
                        ),
                        font=dict(size=15),
                    ),
                    yaxis=dict(title="Days"),
                    legend=dict(
                        orientation="h",
                        y=-0.15,
                    ),
                )
            else:
                cong_fig = _empty_figure(
                    "Congestion Proxy"
                )
        else:
            cong_fig = _empty_figure(
                "Congestion Proxy"
            )

        return (
            kpis,
            ts_fig,
            net_fig,
            re_corr_fig,
            cong_fig,
        )
