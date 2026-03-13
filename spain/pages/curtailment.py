"""Tab 8: Solar Curtailment — oversupply analysis for Spain.

Analyzes solar generation vs demand to identify curtailment periods
and oversupply risk.
"""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import (
    _empty_figure,
    heatmap_chart,
)
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_day_ahead_prices,
    fetch_generation_by_source,
    fetch_total_load,
)


def layout():
    return html.Div(
        [
            html.Div(id="es-curtailment-kpis"),
            html.Div(
                dcc.Graph(
                    id="es-curtailment-heatmap",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-curtailment-timeline",
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
                            id="es-curtailment-price-vs-solar",
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
                "es-curtailment-heatmap", "figure"
            ),
            Output(
                "es-curtailment-timeline", "figure"
            ),
            Output(
                "es-curtailment-price-vs-solar",
                "figure",
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

        gen = fetch_generation_by_source(start, end)
        load = fetch_total_load(start, end)
        prices = fetch_day_ahead_prices(start, end)

        source_cols = [
            c
            for c in gen.columns
            if c != "timestamp"
        ]

        # Calculate solar penetration
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
                gen_analysis = gen.copy()
                gen_analysis["solar_total"] = (
                    gen_analysis[solar_cols].sum(
                        axis=1
                    )
                )
                gen_analysis["total_gen"] = (
                    gen_analysis[source_cols].sum(
                        axis=1
                    )
                )
                gen_analysis["solar_pct"] = (
                    gen_analysis["solar_total"]
                    / gen_analysis[
                        "total_gen"
                    ].replace(0, float("nan"))
                    * 100
                )

                # Curtailment proxy: hours where solar > 50% of total gen
                curtailment_hours = int(
                    (
                        gen_analysis["solar_pct"] > 50
                    ).sum()
                )
                max_solar_pct = (
                    gen_analysis["solar_pct"].max()
                )
                zero_price_hours = 0
                if not prices.empty:
                    zero_price_hours = int(
                        (
                            prices["price_eur_mwh"]
                            <= 0
                        ).sum()
                    )

                # Midday price (11:00-15:00)
                if not prices.empty:
                    prices_tmp = prices.copy()
                    prices_tmp["hour"] = prices_tmp[
                        "timestamp"
                    ].dt.hour
                    midday = prices_tmp[
                        prices_tmp["hour"].between(
                            11, 15
                        )
                    ]
                    avg_midday = (
                        midday[
                            "price_eur_mwh"
                        ].mean()
                        if not midday.empty
                        else float("nan")
                    )
                    midday_str = (
                        f"{avg_midday:.1f} EUR/MWh"
                    )
                else:
                    midday_str = "N/A"

                curtailment_str = str(
                    curtailment_hours
                )
                max_solar_str = (
                    f"{max_solar_pct:.1f}%"
                )
                zero_str = str(zero_price_hours)
            else:
                curtailment_str = "N/A"
                max_solar_str = "N/A"
                midday_str = "N/A"
                zero_str = "N/A"
                gen_analysis = pd.DataFrame()
        else:
            curtailment_str = "N/A"
            max_solar_str = "N/A"
            midday_str = "N/A"
            zero_str = "N/A"
            gen_analysis = pd.DataFrame()

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Solar >50% Hours",
                        curtailment_str,
                        "Oversupply risk",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Max Solar Penetration",
                        max_solar_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg Midday Price",
                        midday_str,
                        "11:00-15:00",
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Zero/Neg Price Hours",
                        zero_str,
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

        # Solar saturation heatmap
        if not gen_analysis.empty:
            ga = gen_analysis.copy()
            ga["hour"] = ga["timestamp"].dt.hour
            ga["date"] = ga[
                "timestamp"
            ].dt.date.astype(str)
            pivot = ga.pivot_table(
                values="solar_pct",
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
                    "Solar Penetration Heatmap"
                    " (% of Total Gen)"
                ),
                colorscale="YlOrRd",
                z_label="Solar %",
            )
        else:
            hm_fig = _empty_figure(
                "Solar Saturation Heatmap"
            )

        # Curtailment events timeline
        if not gen_analysis.empty:
            high_solar = gen_analysis[
                gen_analysis["solar_pct"] > 40
            ].copy()
            if not high_solar.empty:
                timeline_fig = go.Figure()
                timeline_fig.add_trace(
                    go.Scatter(
                        x=gen_analysis["timestamp"],
                        y=gen_analysis["solar_pct"],
                        mode="lines",
                        line=dict(
                            color=COLORS[
                                "accent_amber"
                            ],
                            width=1.5,
                        ),
                        name="Solar %",
                        hovertemplate=(
                            "%{x|%Y-%m-%d %H:%M}<br>"
                            "Solar: %{y:.1f}%"
                            "<extra></extra>"
                        ),
                    )
                )
                timeline_fig.add_hline(
                    y=50,
                    line_dash="dash",
                    line_color=COLORS[
                        "accent_red"
                    ],
                    annotation_text=(
                        "50% threshold"
                    ),
                    annotation_font_color=COLORS[
                        "accent_red"
                    ],
                )
                apply_theme(timeline_fig)
                timeline_fig.update_layout(
                    title=dict(
                        text=(
                            "Solar Penetration"
                            " Over Time"
                        ),
                        font=dict(size=15),
                    ),
                    yaxis=dict(
                        title="Solar Share (%)"
                    ),
                    showlegend=False,
                )
            else:
                timeline_fig = _empty_figure(
                    "Solar Penetration Timeline"
                )
        else:
            timeline_fig = _empty_figure(
                "Solar Penetration Timeline"
            )

        # Solar peak vs trough prices
        if (
            not gen_analysis.empty
            and not prices.empty
        ):
            # Merge generation solar % with prices
            merged = pd.merge_asof(
                gen_analysis[
                    ["timestamp", "solar_pct"]
                ].sort_values("timestamp"),
                prices.sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            price_solar_fig = go.Figure(
                go.Scatter(
                    x=merged["solar_pct"],
                    y=merged["price_eur_mwh"],
                    mode="markers",
                    marker=dict(
                        color=COLORS["accent_cyan"],
                        size=4,
                        opacity=0.6,
                    ),
                    hovertemplate=(
                        "Solar: %{x:.1f}%<br>"
                        "Price: %{y:.1f} EUR/MWh"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(price_solar_fig)
            price_solar_fig.update_layout(
                title=dict(
                    text=(
                        "Solar Penetration"
                        " vs DA Price"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(
                    title="Solar Share (%)"
                ),
                yaxis=dict(title="EUR/MWh"),
            )
        else:
            price_solar_fig = _empty_figure(
                "Solar vs Price"
            )

        return (
            kpis,
            hm_fig,
            timeline_fig,
            price_solar_fig,
        )
