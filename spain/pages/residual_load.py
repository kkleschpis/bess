"""Tab 6: Residual Load & System — fundamental metric for BESS in Spain."""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import (
    _empty_figure,
    heatmap_chart,
    scatter_chart,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_cross_border_flows,
    fetch_day_ahead_prices,
    fetch_generation_by_source,
    fetch_total_load,
)


def _compute_residual(load_df, gen_df):
    """Compute residual load = Total Load - Solar - Wind."""
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

    gen_sub = gen_df[["timestamp"] + ws_cols].copy()
    gen_sub["renewable_mw"] = gen_sub[ws_cols].sum(
        axis=1
    )

    merged = pd.merge_asof(
        load_df.sort_values("timestamp"),
        gen_sub[
            ["timestamp", "renewable_mw"]
        ].sort_values("timestamp"),
        on="timestamp",
        direction="nearest",
    )
    merged["residual_load"] = (
        merged["load_mw"] - merged["renewable_mw"]
    )
    return merged


def layout():
    return html.Div(
        [
            html.Div(id="es-residual-kpis"),
            html.Div(
                dcc.Graph(
                    id="es-residual-curve",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-residual-scatter",
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
                            id="es-residual-flows",
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
                    id="es-residual-heatmap",
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
            Output("es-residual-curve", "figure"),
            Output(
                "es-residual-scatter", "figure"
            ),
            Output("es-residual-flows", "figure"),
            Output(
                "es-residual-heatmap", "figure"
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

        load_df = fetch_total_load(start, end)
        gen_df = fetch_generation_by_source(
            start, end
        )
        prices_df = fetch_day_ahead_prices(
            start, end
        )
        flows_df = fetch_cross_border_flows(
            start, end
        )

        merged = _compute_residual(load_df, gen_df)

        # KPIs
        if not merged.empty:
            current_res = (
                f"{merged['residual_load'].iloc[-1]:,.0f}"
                " MW"
            )
            avg_res = (
                f"{merged['residual_load'].mean():,.0f}"
                " MW"
            )
            neg_hours = int(
                (merged["residual_load"] < 0).sum()
            )
            neg_hours_str = str(neg_hours)
        else:
            current_res = "N/A"
            avg_res = "N/A"
            neg_hours_str = "N/A"

        if not flows_df.empty:
            net_flow = flows_df["flow_mw"].sum()
            flow_str = f"{net_flow:,.0f} MW"
            flow_dir = (
                "(Net Export)"
                if net_flow > 0
                else "(Net Import)"
            )
        else:
            flow_str = "N/A"
            flow_dir = ""

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Current Residual Load",
                        current_res,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg Residual Load",
                        avg_res,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Negative Residual Intervals",
                        neg_hours_str,
                        "Excess RE generation",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Cross-Border Net Flow",
                        flow_str,
                        flow_dir,
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

        # Residual load curve
        if not merged.empty:
            curve_fig = go.Figure()
            curve_fig.add_trace(
                go.Scatter(
                    x=merged["timestamp"],
                    y=merged["load_mw"],
                    name="Total Load",
                    mode="lines",
                    line=dict(
                        color=COLORS["text_muted"],
                        width=1,
                        dash="dot",
                    ),
                    hovertemplate=(
                        "Load: %{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            curve_fig.add_trace(
                go.Scatter(
                    x=merged["timestamp"],
                    y=merged["renewable_mw"],
                    name="Solar + Wind",
                    mode="lines",
                    line=dict(
                        color=COLORS[
                            "accent_green"
                        ],
                        width=1.5,
                    ),
                    fill="tozeroy",
                    fillcolor=(
                        "rgba(16,185,129,0.1)"
                    ),
                    hovertemplate=(
                        "RE: %{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            curve_fig.add_trace(
                go.Scatter(
                    x=merged["timestamp"],
                    y=merged["residual_load"],
                    name="Residual Load",
                    mode="lines",
                    line=dict(
                        color=COLORS["accent_cyan"],
                        width=2.5,
                    ),
                    hovertemplate=(
                        "Residual: %{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            curve_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color=COLORS["accent_red"],
                line_width=1,
            )
            apply_theme(curve_fig)
            curve_fig.update_layout(
                title=dict(
                    text=(
                        "Residual Load"
                        " (Total Load"
                        " - Solar - Wind)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                hovermode="x unified",
                legend=dict(
                    orientation="h", y=-0.12
                ),
            )
        else:
            curve_fig = _empty_figure(
                "Residual Load"
            )

        # Residual vs price scatter
        if (
            not merged.empty
            and not prices_df.empty
        ):
            scatter_merged = pd.merge_asof(
                merged[
                    ["timestamp", "residual_load"]
                ].sort_values("timestamp"),
                prices_df.sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            sc_fig = scatter_chart(
                scatter_merged,
                "residual_load",
                "price_eur_mwh",
                title="Residual Load vs DA Price",
                x_title="Residual Load (MW)",
                y_title="EUR/MWh",
            )
        else:
            sc_fig = _empty_figure(
                "Residual Load vs Price"
            )

        # Cross-border flows
        if not flows_df.empty:
            country_avg = (
                flows_df.groupby("country")[
                    "flow_mw"
                ]
                .mean()
                .sort_values()
                .reset_index()
            )
            colors = [
                COLORS["accent_green"]
                if v > 0
                else COLORS["accent_red"]
                for v in country_avg["flow_mw"]
            ]
            flows_fig = go.Figure(
                go.Bar(
                    y=country_avg["country"],
                    x=country_avg["flow_mw"],
                    orientation="h",
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate=(
                        "%{y}: %{x:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            flows_fig.add_vline(
                x=0,
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(flows_fig)
            flows_fig.update_layout(
                title=dict(
                    text=(
                        "Avg Cross-Border Flows"
                        " (+ Export / - Import)"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(title="MW"),
                height=300,
            )
        else:
            flows_fig = _empty_figure(
                "Cross-Border Flows"
            )

        # Residual load heatmap
        if not merged.empty:
            m = merged.copy()
            m["hour"] = m["timestamp"].dt.hour
            m["date"] = m[
                "timestamp"
            ].dt.date.astype(str)
            pivot = m.pivot_table(
                values="residual_load",
                index="date",
                columns="hour",
                aggfunc="mean",
            )
            pivot = pivot.sort_index(ascending=True)
            hours = list(range(24))
            existing = [
                h
                for h in hours
                if h in pivot.columns
            ]
            hm_fig = heatmap_chart(
                z_data=pivot[existing].values,
                x_labels=[
                    f"{h:02d}:00" for h in existing
                ],
                y_labels=list(pivot.index),
                title=(
                    "Residual Load Heatmap"
                    " (MW by Hour & Date)"
                ),
                colorscale="RdBu_r",
                z_label="MW",
            )
        else:
            hm_fig = _empty_figure(
                "Residual Load Heatmap"
            )

        return (
            kpis,
            curve_fig,
            sc_fig,
            flows_fig,
            hm_fig,
        )
