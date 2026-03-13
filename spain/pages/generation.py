"""Tab 3: Generation Mix — solar, wind, gas, nuclear breakdown for Spain."""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import (
    generation_stacked_area,
    _empty_figure,
)
from components.kpi_cards import kpi_card
from components.theme import (
    COLORS,
    SOURCE_COLORS,
    SOURCE_LABELS,
    apply_theme,
    card_style,
)
from data.api_client import fetch_generation_by_source

SPAIN_SOURCE_ORDER = [
    "solar_pv",
    "solar_thermal",
    "wind",
    "biomass",
    "hydro",
    "nuclear",
    "coal",
    "combined_cycle",
    "cogeneration",
    "gas",
    "oil",
    "hydro_pumped",
    "waste",
    "other",
]


def layout():
    return html.Div(
        [
            html.Div(id="es-gen-kpis"),
            html.Div(
                dcc.Graph(
                    id="es-gen-stacked",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-gen-solar-profile",
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
                            id="es-gen-wind-profile",
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
                    id="es-gen-pie",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("es-gen-kpis", "children"),
            Output("es-gen-stacked", "figure"),
            Output(
                "es-gen-solar-profile", "figure"
            ),
            Output("es-gen-wind-profile", "figure"),
            Output("es-gen-pie", "figure"),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_generation(start_date, end_date):
        start = pd.Timestamp(
            start_date
        ).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()
        gen = fetch_generation_by_source(start, end)

        source_cols = [
            c
            for c in gen.columns
            if c != "timestamp"
        ]
        if not gen.empty and source_cols:
            total = gen[source_cols].sum(axis=1)
            total_sum = total.sum()

            solar_cols = [
                c
                for c in ["solar_pv", "solar_thermal"]
                if c in gen.columns
            ]
            solar_sum = (
                gen[solar_cols].sum().sum()
                if solar_cols
                else 0
            )
            wind_sum = (
                gen["wind"].sum()
                if "wind" in gen.columns
                else 0
            )
            fossil_cols = [
                c
                for c in [
                    "combined_cycle",
                    "coal",
                    "gas",
                    "oil",
                    "cogeneration",
                ]
                if c in gen.columns
            ]
            fossil_sum = (
                gen[fossil_cols].sum().sum()
                if fossil_cols
                else 0
            )

            solar_pct = (
                f"{solar_sum / total_sum * 100:.1f}%"
                if total_sum > 0
                else "N/A"
            )
            wind_pct = (
                f"{wind_sum / total_sum * 100:.1f}%"
                if total_sum > 0
                else "N/A"
            )
            fossil_pct = (
                f"{fossil_sum / total_sum * 100:.1f}%"
                if total_sum > 0
                else "N/A"
            )
            renewable_sum = solar_sum + wind_sum
            re_pct = (
                f"{renewable_sum / total_sum * 100:.1f}%"
                if total_sum > 0
                else "N/A"
            )
        else:
            solar_pct = "N/A"
            wind_pct = "N/A"
            fossil_pct = "N/A"
            re_pct = "N/A"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Solar Share",
                        solar_pct,
                        color=SOURCE_COLORS[
                            "solar_pv"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Wind Share",
                        wind_pct,
                        color=SOURCE_COLORS["wind"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Fossil Share",
                        fossil_pct,
                        color=COLORS["accent_red"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Renewable (Solar+Wind)",
                        re_pct,
                        color=COLORS["accent_green"],
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

        # Stacked area
        stacked_fig = generation_stacked_area(
            gen,
            "Generation by Source",
            source_order=SPAIN_SOURCE_ORDER,
        )

        # Solar daily profile
        solar_cols = [
            c
            for c in ["solar_pv", "solar_thermal"]
            if c in gen.columns
        ]
        if not gen.empty and solar_cols:
            gen_tmp = gen.copy()
            gen_tmp["solar_total"] = gen_tmp[
                solar_cols
            ].sum(axis=1)
            gen_tmp["hour"] = gen_tmp[
                "timestamp"
            ].dt.hour
            solar_profile = (
                gen_tmp.groupby("hour")[
                    "solar_total"
                ]
                .mean()
                .reset_index()
            )
            solar_fig = go.Figure(
                go.Scatter(
                    x=solar_profile["hour"],
                    y=solar_profile["solar_total"],
                    mode="lines+markers",
                    fill="tozeroy",
                    line=dict(
                        color=SOURCE_COLORS[
                            "solar_pv"
                        ],
                        width=2.5,
                    ),
                    fillcolor=(
                        "rgba(245,158,11,0.15)"
                    ),
                    marker=dict(size=5),
                    hovertemplate=(
                        "Hour %{x}:00<br>"
                        "%{y:,.0f} MW avg"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(solar_fig)
            solar_fig.update_layout(
                title=dict(
                    text=(
                        "Avg Solar Generation by Hour"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(
                    title="Hour of Day",
                    dtick=2,
                ),
                yaxis=dict(title="MW"),
            )
        else:
            solar_fig = _empty_figure(
                "Solar Profile"
            )

        # Wind profile
        if (
            not gen.empty
            and "wind" in gen.columns
        ):
            gen_tmp = gen.copy()
            gen_tmp["hour"] = gen_tmp[
                "timestamp"
            ].dt.hour
            wind_profile = (
                gen_tmp.groupby("hour")["wind"]
                .agg(["mean", "min", "max"])
                .reset_index()
            )
            wind_fig = go.Figure()
            wind_fig.add_trace(
                go.Scatter(
                    x=wind_profile["hour"],
                    y=wind_profile["max"],
                    mode="lines",
                    line=dict(width=0),
                    showlegend=False,
                )
            )
            wind_fig.add_trace(
                go.Scatter(
                    x=wind_profile["hour"],
                    y=wind_profile["min"],
                    mode="lines",
                    line=dict(width=0),
                    fill="tonexty",
                    fillcolor=(
                        "rgba(59,130,246,0.15)"
                    ),
                    showlegend=False,
                )
            )
            wind_fig.add_trace(
                go.Scatter(
                    x=wind_profile["hour"],
                    y=wind_profile["mean"],
                    mode="lines+markers",
                    line=dict(
                        color=SOURCE_COLORS["wind"],
                        width=2.5,
                    ),
                    marker=dict(size=5),
                    name="Avg",
                    hovertemplate=(
                        "Hour %{x}:00<br>"
                        "%{y:,.0f} MW avg"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(wind_fig)
            wind_fig.update_layout(
                title=dict(
                    text=(
                        "Wind Generation by Hour"
                        " (Avg / Min / Max)"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(
                    title="Hour of Day",
                    dtick=2,
                ),
                yaxis=dict(title="MW"),
                showlegend=False,
            )
        else:
            wind_fig = _empty_figure("Wind Profile")

        # Generation mix pie chart
        if not gen.empty and source_cols:
            totals = {}
            for col in source_cols:
                s = gen[col].sum()
                if s > 0:
                    totals[col] = s
            if totals:
                labels = [
                    SOURCE_LABELS.get(k, k)
                    for k in totals
                ]
                values = list(totals.values())
                colors = [
                    SOURCE_COLORS.get(
                        k, COLORS["accent_blue"]
                    )
                    for k in totals
                ]
                pie_fig = go.Figure(
                    go.Pie(
                        labels=labels,
                        values=values,
                        marker=dict(colors=colors),
                        hole=0.55,
                        textinfo="label+percent",
                        textfont=dict(
                            size=11,
                            color=COLORS["text"],
                        ),
                    )
                )
                apply_theme(pie_fig)
                pie_fig.update_layout(
                    title=dict(
                        text="Generation Mix Share",
                        font=dict(size=15),
                    ),
                    showlegend=False,
                    height=400,
                )
            else:
                pie_fig = _empty_figure(
                    "Generation Mix"
                )
        else:
            pie_fig = _empty_figure(
                "Generation Mix"
            )

        return (
            kpis,
            stacked_fig,
            solar_fig,
            wind_fig,
            pie_fig,
        )
