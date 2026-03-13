"""Tab 5: Nuclear Fleet Monitor — FRANCE-UNIQUE strategic differentiator.

France's ~70% nuclear generation dominance means nuclear fleet
availability is THE dominant price driver. This tab provides
CEO-level nuclear fleet analytics for BESS investment decisions.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import (
    _empty_figure,
    heatmap_chart,
)
from components.kpi_cards import kpi_card
from components.theme import (
    COLORS,
    SOURCE_COLORS,
    apply_theme,
    card_style,
)
from data.api_client import (
    fetch_day_ahead_prices,
    fetch_generation_by_source,
)


def layout():
    return html.Div(
        [
            html.Div(id="fr-nuclear-kpis"),
            html.Div(
                dcc.Graph(
                    id="fr-nuclear-trend",
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
                            id="fr-nuclear-scatter",
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
                            id="fr-nuclear-heatmap",
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
                    id="fr-nuclear-histogram",
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
                "fr-nuclear-kpis", "children"
            ),
            Output("fr-nuclear-trend", "figure"),
            Output(
                "fr-nuclear-scatter", "figure"
            ),
            Output(
                "fr-nuclear-heatmap", "figure"
            ),
            Output(
                "fr-nuclear-histogram", "figure"
            ),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_nuclear(start_date, end_date):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()

        gen = fetch_generation_by_source(
            start, end
        )
        prices = fetch_day_ahead_prices(start, end)

        has_nuclear = (
            not gen.empty
            and "nuclear" in gen.columns
        )

        # KPIs
        if has_nuclear:
            source_cols = [
                c
                for c in gen.columns
                if c != "timestamp"
            ]
            total = gen[source_cols].sum(axis=1)

            current_nuc = gen["nuclear"].iloc[-1]
            nuc_share = (
                gen["nuclear"].sum() / total.sum()
                * 100
                if total.sum() > 0
                else 0
            )
            avg_capacity_factor = (
                gen["nuclear"].mean()
                / gen["nuclear"].max()
                * 100
                if gen["nuclear"].max() > 0
                else 0
            )
            nuc_std = gen["nuclear"].std()

            current_str = f"{current_nuc:,.0f} MW"
            share_str = f"{nuc_share:.1f}%"
            cf_str = f"{avg_capacity_factor:.1f}%"
            std_str = f"{nuc_std:,.0f} MW"
        else:
            current_str = "N/A"
            share_str = "N/A"
            cf_str = "N/A"
            std_str = "N/A"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Current Nuclear Output",
                        current_str,
                        color=SOURCE_COLORS[
                            "nuclear"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Nuclear Share of Gen",
                        share_str,
                        color=SOURCE_COLORS[
                            "nuclear"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg Capacity Factor",
                        cf_str,
                        "vs period max output",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Nuclear Variability",
                        std_str,
                        "Standard deviation",
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

        # Nuclear generation trend with fill
        if has_nuclear:
            trend_fig = go.Figure()
            trend_fig.add_trace(
                go.Scatter(
                    x=gen["timestamp"],
                    y=gen["nuclear"],
                    mode="lines",
                    fill="tozeroy",
                    line=dict(
                        color=SOURCE_COLORS[
                            "nuclear"
                        ],
                        width=2,
                    ),
                    fillcolor=(
                        "rgba(139,92,246,0.15)"
                    ),
                    hovertemplate=(
                        "%{x|%Y-%m-%d %H:%M}<br>"
                        "Nuclear: %{y:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            # Add average line
            avg_nuc = gen["nuclear"].mean()
            trend_fig.add_hline(
                y=avg_nuc,
                line_dash="dash",
                line_color=COLORS["accent_amber"],
                line_width=1,
                annotation_text=(
                    f"Avg: {avg_nuc:,.0f} MW"
                ),
                annotation_font_color=COLORS[
                    "accent_amber"
                ],
            )
            apply_theme(trend_fig)
            trend_fig.update_layout(
                title=dict(
                    text=(
                        "Nuclear Generation Trend"
                        " (Fleet Availability)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                showlegend=False,
            )
        else:
            trend_fig = _empty_figure(
                "Nuclear Generation"
            )

        # Nuclear vs Price scatter
        if has_nuclear and not prices.empty:
            merged = pd.merge_asof(
                gen[
                    ["timestamp", "nuclear"]
                ].sort_values("timestamp"),
                prices.sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            scatter_fig = go.Figure(
                go.Scatter(
                    x=merged["nuclear"],
                    y=merged["price_eur_mwh"],
                    mode="markers",
                    marker=dict(
                        color=COLORS[
                            "accent_cyan"
                        ],
                        size=4,
                        opacity=0.6,
                    ),
                    hovertemplate=(
                        "Nuclear: %{x:,.0f} MW<br>"
                        "Price: %{y:.1f} EUR/MWh"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(scatter_fig)
            scatter_fig.update_layout(
                title=dict(
                    text=(
                        "Nuclear Output vs"
                        " DA Price"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(
                    title="Nuclear Output (MW)"
                ),
                yaxis=dict(title="EUR/MWh"),
            )
        else:
            scatter_fig = _empty_figure(
                "Nuclear vs Price"
            )

        # Nuclear share heatmap (hour x date)
        if has_nuclear:
            source_cols = [
                c
                for c in gen.columns
                if c != "timestamp"
            ]
            gen_tmp = gen.copy()
            total = gen_tmp[source_cols].sum(axis=1)
            gen_tmp["nuc_share"] = (
                gen_tmp["nuclear"]
                / total.replace(0, np.nan)
                * 100
            )
            gen_tmp["hour"] = gen_tmp[
                "timestamp"
            ].dt.hour
            gen_tmp["date"] = gen_tmp[
                "timestamp"
            ].dt.date.astype(str)

            pivot = gen_tmp.pivot_table(
                values="nuc_share",
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
                    f"{h:02d}:00"
                    for h in existing
                ],
                y_labels=list(pivot.index),
                title=(
                    "Nuclear Share Heatmap"
                    " (% by Hour & Date)"
                ),
                colorscale="Purples",
                z_label="%",
            )
        else:
            hm_fig = _empty_figure(
                "Nuclear Share Heatmap"
            )

        # Nuclear output distribution histogram
        if has_nuclear:
            hist_fig = go.Figure(
                go.Histogram(
                    x=gen["nuclear"],
                    nbinsx=40,
                    marker_color=SOURCE_COLORS[
                        "nuclear"
                    ],
                    marker_line_width=0,
                    opacity=0.8,
                    hovertemplate=(
                        "Output: %{x:,.0f} MW<br>"
                        "Count: %{y}"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(hist_fig)
            hist_fig.update_layout(
                title=dict(
                    text=(
                        "Nuclear Output Distribution"
                        " (Operating Range)"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(title="MW"),
                yaxis=dict(
                    title="Frequency (intervals)"
                ),
            )
        else:
            hist_fig = _empty_figure(
                "Nuclear Distribution"
            )

        return (
            kpis,
            trend_fig,
            scatter_fig,
            hm_fig,
            hist_fig,
        )
