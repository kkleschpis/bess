"""Tab 3: Generation Mix — solar, wind, fossil breakdown."""

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
from data.api_client import (
    fetch_generation_by_source,
    fetch_installed_capacity,
)


def layout():
    return html.Div(
        [
            html.Div(id="gen-kpis"),
            html.Div(
                dcc.Graph(
                    id="gen-stacked",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="gen-solar-profile",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                    html.Div(
                        dcc.Graph(
                            id="gen-wind-profile",
                            config={"displayModeBar": False},
                        ),
                        style={**card_style(), "flex": "1"},
                    ),
                ],
                style={"display": "flex", "gap": "16px"},
            ),
            html.Div(
                dcc.Graph(
                    id="gen-capacity",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
        ]
    )


def register_callbacks(app):
    @app.callback(
        [
            Output("gen-kpis", "children"),
            Output("gen-stacked", "figure"),
            Output("gen-solar-profile", "figure"),
            Output("gen-wind-profile", "figure"),
            Output("gen-capacity", "figure"),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_generation(start_date, end_date):
        start = pd.Timestamp(start_date).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()
        gen = fetch_generation_by_source(start, end)

        # Calculate shares
        source_cols = [
            c for c in gen.columns if c != "timestamp"
        ]
        if not gen.empty and source_cols:
            total = gen[source_cols].sum(axis=1)
            total_sum = total.sum()

            solar_sum = (
                gen["solar"].sum()
                if "solar" in gen.columns
                else 0
            )
            wind_sum = sum(
                gen[c].sum()
                for c in [
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in gen.columns
            )
            fossil_sum = sum(
                gen[c].sum()
                for c in [
                    "gas",
                    "hard_coal",
                    "lignite",
                    "oil",
                ]
                if c in gen.columns
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
            gen, "Generation by Source"
        )

        # Solar daily profile (avg by hour of day)
        if not gen.empty and "solar" in gen.columns:
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
                    fillcolor="rgba(245,158,11,0.15)",
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
                    text="Avg Solar Generation by Hour",
                    font=dict(size=15),
                ),
                xaxis=dict(
                    title="Hour of Day",
                    dtick=2,
                ),
                yaxis=dict(title="MW"),
            )
        else:
            solar_fig = _empty_figure("Solar Profile")

        # Wind profile
        wind_cols = [
            c
            for c in ["wind_onshore", "wind_offshore"]
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
                gen_tmp.groupby("hour")["wind_total"]
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
                    fillcolor="rgba(59,130,246,0.15)",
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
                    text="Wind Generation by Hour"
                    " (Avg / Min / Max)",
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

        # Installed capacity
        cap = fetch_installed_capacity()
        if not cap.empty:
            # Map to our source names for coloring
            cap_sorted = cap.sort_values(
                "capacity_mw", ascending=True
            )
            colors = [
                SOURCE_COLORS.get(
                    s.lower().replace(" ", "_"),
                    COLORS["accent_blue"],
                )
                for s in cap_sorted["source"]
            ]
            cap_fig = go.Figure(
                go.Bar(
                    y=cap_sorted["source"],
                    x=cap_sorted["capacity_mw"],
                    orientation="h",
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate=(
                        "%{y}: %{x:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(cap_fig)
            cap_fig.update_layout(
                title=dict(
                    text="Installed Capacity by Source"
                    " (MW)",
                    font=dict(size=15),
                ),
                xaxis=dict(title="MW"),
                height=400,
            )
        else:
            cap_fig = _empty_figure(
                "Installed Capacity"
            )

        return (
            kpis,
            stacked_fig,
            solar_fig,
            wind_fig,
            cap_fig,
        )
