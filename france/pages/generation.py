"""Tab 3: Generation Mix — nuclear-focused breakdown for France."""

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

FRANCE_SOURCE_ORDER = [
    "solar",
    "wind_onshore",
    "wind_offshore",
    "biomass",
    "hydro",
    "nuclear",
    "gas",
    "hard_coal",
    "lignite",
    "oil",
    "pumped_storage",
    "geothermal",
    "other",
]


def layout():
    return html.Div(
        [
            html.Div(id="fr-gen-kpis"),
            html.Div(
                dcc.Graph(
                    id="fr-gen-stacked",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="fr-gen-solar-profile",
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
                            id="fr-gen-wind-profile",
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
                    id="fr-gen-pie",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("fr-gen-kpis", "children"),
            Output("fr-gen-stacked", "figure"),
            Output(
                "fr-gen-solar-profile", "figure"
            ),
            Output(
                "fr-gen-wind-profile", "figure"
            ),
            Output("fr-gen-pie", "figure"),
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

            nuclear_sum = (
                gen["nuclear"].sum()
                if "nuclear" in gen.columns
                else 0
            )
            solar_sum = (
                gen["solar"].sum()
                if "solar" in gen.columns
                else 0
            )
            wind_cols = [
                c
                for c in [
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in gen.columns
            ]
            wind_sum = (
                gen[wind_cols].sum().sum()
                if wind_cols
                else 0
            )
            renewable_sum = solar_sum + wind_sum

            nuclear_pct = (
                f"{nuclear_sum / total_sum * 100:.1f}%"
                if total_sum > 0
                else "N/A"
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
            re_pct = (
                f"{renewable_sum / total_sum * 100:.1f}%"
                if total_sum > 0
                else "N/A"
            )
        else:
            nuclear_pct = "N/A"
            solar_pct = "N/A"
            wind_pct = "N/A"
            re_pct = "N/A"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Nuclear Share",
                        nuclear_pct,
                        color=SOURCE_COLORS[
                            "nuclear"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Solar Share",
                        solar_pct,
                        color=SOURCE_COLORS["solar"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Wind Share",
                        wind_pct,
                        color=SOURCE_COLORS[
                            "wind_onshore"
                        ],
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
            source_order=FRANCE_SOURCE_ORDER,
        )

        # Solar daily profile
        if (
            not gen.empty
            and "solar" in gen.columns
        ):
            gen_tmp = gen.copy()
            gen_tmp["hour"] = gen_tmp[
                "timestamp"
            ].dt.hour
            solar_profile = (
                gen_tmp.groupby("hour")["solar"]
                .mean()
                .reset_index()
            )
            solar_fig = go.Figure(
                go.Scatter(
                    x=solar_profile["hour"],
                    y=solar_profile["solar"],
                    mode="lines+markers",
                    fill="tozeroy",
                    line=dict(
                        color=SOURCE_COLORS["solar"],
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
                        "Avg Solar Generation"
                        " by Hour"
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
        wind_cols = [
            c
            for c in [
                "wind_onshore",
                "wind_offshore",
            ]
            if c in gen.columns
        ]
        if not gen.empty and wind_cols:
            gen_tmp = gen.copy()
            gen_tmp["wind_total"] = gen_tmp[
                wind_cols
            ].sum(axis=1)
            gen_tmp["hour"] = gen_tmp[
                "timestamp"
            ].dt.hour
            wind_profile = (
                gen_tmp.groupby("hour")[
                    "wind_total"
                ]
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
                        color=SOURCE_COLORS[
                            "wind_onshore"
                        ],
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
