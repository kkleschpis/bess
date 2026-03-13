"""Tab 2: Generation Trends & Derivatives — how fast is the mix shifting?"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.analytics import (
    add_trendline_trace,
    compute_acceleration,
    compute_linear_trend,
    compute_monthly_derivative,
    compute_yoy_comparison,
    trend_arrow,
)
from components.charts import (
    _empty_figure,
    generation_stacked_area,
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
                            id="es-gen-1st-deriv",
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
                            id="es-gen-2nd-deriv",
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
                    id="es-gen-displacement",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                dcc.Graph(
                    id="es-gen-yoy",
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
            Output("es-gen-1st-deriv", "figure"),
            Output("es-gen-2nd-deriv", "figure"),
            Output(
                "es-gen-displacement", "figure"
            ),
            Output("es-gen-yoy", "figure"),
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
        gen = fetch_generation_by_source(
            start, end, time_trunc="month"
        )

        source_cols = [
            c
            for c in gen.columns
            if c != "timestamp"
        ]

        # Compute monthly RE %
        if not gen.empty and source_cols:
            gen_m = gen.copy()
            gen_m["total"] = gen_m[
                source_cols
            ].sum(axis=1)
            solar_cols = [
                c
                for c in [
                    "solar_pv",
                    "solar_thermal",
                ]
                if c in gen.columns
            ]
            wind_cols = [
                c
                for c in ["wind"]
                if c in gen.columns
            ]
            re_cols = solar_cols + wind_cols
            gen_m["re_total"] = gen_m[
                re_cols
            ].sum(axis=1)
            gen_m["re_pct"] = (
                gen_m["re_total"]
                / gen_m["total"].replace(
                    0, float("nan")
                )
                * 100
            )

            # Source shares
            for col in source_cols:
                gen_m[f"{col}_pct"] = (
                    gen_m[col]
                    / gen_m["total"].replace(
                        0, float("nan")
                    )
                    * 100
                )
        else:
            gen_m = pd.DataFrame()

        # --- KPIs ---
        solar_rate = "N/A"
        wind_rate = "N/A"
        ccgt_rate = "N/A"
        accel_str = "N/A"

        if not gen_m.empty:
            if "solar_pv_pct" in gen_m.columns:
                slope, _, _ = compute_linear_trend(
                    gen_m["solar_pv_pct"]
                )
                solar_rate = (
                    f"{slope * 12:.1f} pp/year"
                )
            if "wind_pct" in gen_m.columns:
                slope, _, _ = compute_linear_trend(
                    gen_m["wind_pct"]
                )
                wind_rate = (
                    f"{slope * 12:.1f} pp/year"
                )
            if (
                "combined_cycle_pct"
                in gen_m.columns
            ):
                slope, _, _ = compute_linear_trend(
                    gen_m["combined_cycle_pct"]
                )
                ccgt_rate = (
                    f"{slope * 12:.1f} pp/year"
                )

            if "re_pct" in gen_m.columns:
                accel = compute_acceleration(
                    gen_m["re_pct"]
                )
                recent = accel.dropna().tail(3)
                if not recent.empty:
                    avg_accel = recent.mean()
                    if avg_accel > 0.1:
                        accel_str = "Accelerating"
                    elif avg_accel < -0.1:
                        accel_str = "Decelerating"
                    else:
                        accel_str = "Steady"

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Solar Growth",
                        solar_rate,
                        "Linear fit pp/year",
                        color=SOURCE_COLORS.get(
                            "solar_pv",
                            COLORS["accent_amber"],
                        ),
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Wind Growth",
                        wind_rate,
                        "Linear fit pp/year",
                        color=SOURCE_COLORS.get(
                            "wind",
                            COLORS["accent_blue"],
                        ),
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "CCGT Decline",
                        ccgt_rate,
                        "Linear fit pp/year",
                        color=COLORS[
                            "accent_red"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "RE Acceleration",
                        accel_str,
                        "2nd derivative",
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

        # --- Chart 1: Monthly Stacked Area ---
        stacked_fig = generation_stacked_area(
            gen,
            "Monthly Generation Share",
            source_order=SPAIN_SOURCE_ORDER,
        )

        # --- Chart 2: RE Penetration 1st Derivative ---
        if (
            not gen_m.empty
            and "re_pct" in gen_m.columns
        ):
            deriv1 = compute_monthly_derivative(
                gen_m["re_pct"]
            )
            colors = [
                COLORS["accent_green"]
                if v >= 0
                else COLORS["accent_red"]
                for v in deriv1.fillna(0)
            ]
            d1_fig = go.Figure(
                go.Bar(
                    x=gen_m["timestamp"],
                    y=deriv1,
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "MoM Change: %{y:+.2f} pp"
                        "<extra></extra>"
                    ),
                )
            )
            apply_theme(d1_fig)
            d1_fig.update_layout(
                title=dict(
                    text=(
                        "RE Penetration"
                        " \u2014 1st Derivative"
                        " (MoM Change)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(
                    title="Change (pp)"
                ),
            )
            d1_fig.add_hline(
                y=0,
                line_color=COLORS["text_muted"],
                line_width=1,
            )
        else:
            d1_fig = _empty_figure(
                "1st Derivative"
            )

        # --- Chart 3: RE Penetration 2nd Derivative ---
        if (
            not gen_m.empty
            and "re_pct" in gen_m.columns
        ):
            accel_series = compute_acceleration(
                gen_m["re_pct"]
            )
            d2_fig = go.Figure(
                go.Scatter(
                    x=gen_m["timestamp"],
                    y=accel_series,
                    mode="lines+markers",
                    line=dict(
                        color=COLORS[
                            "accent_purple"
                        ],
                        width=2,
                    ),
                    marker=dict(size=5),
                    fill="tozeroy",
                    fillcolor=(
                        "rgba(139,92,246,0.1)"
                    ),
                    hovertemplate=(
                        "%{x|%Y-%m}<br>"
                        "Acceleration: %{y:+.3f}"
                        "<extra></extra>"
                    ),
                )
            )
            d2_fig.add_hline(
                y=0,
                line_dash="dash",
                line_color=COLORS["text_muted"],
                line_width=1,
                annotation_text=(
                    "Above = accelerating"
                ),
                annotation_font_color=COLORS[
                    "text_muted"
                ],
            )
            apply_theme(d2_fig)
            d2_fig.update_layout(
                title=dict(
                    text=(
                        "RE Penetration"
                        " \u2014 2nd Derivative"
                        " (Acceleration)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(
                    title="Acceleration (pp)"
                ),
            )
        else:
            d2_fig = _empty_figure(
                "2nd Derivative"
            )

        # --- Chart 4: Source Displacement Curves ---
        displacement_sources = [
            "solar_pv",
            "wind",
            "combined_cycle",
            "coal",
        ]
        disp_fig = go.Figure()
        has_disp = False

        if not gen.empty:
            for src in displacement_sources:
                if src not in gen.columns:
                    continue
                has_disp = True
                disp_fig.add_trace(
                    go.Scatter(
                        x=gen["timestamp"],
                        y=gen[src],
                        name=SOURCE_LABELS.get(
                            src, src
                        ),
                        mode="lines",
                        line=dict(
                            color=SOURCE_COLORS.get(
                                src,
                                COLORS[
                                    "accent_blue"
                                ],
                            ),
                            width=2,
                        ),
                        hovertemplate=(
                            f"{SOURCE_LABELS.get(src, src)}"
                            ": %{y:,.0f} MWh"
                            "<extra></extra>"
                        ),
                    )
                )
                # Add trendline for each
                add_trendline_trace(
                    disp_fig,
                    gen["timestamp"],
                    gen[src],
                    color=SOURCE_COLORS.get(
                        src,
                        COLORS["accent_blue"],
                    ),
                    name=f"{SOURCE_LABELS.get(src, src)} Trend",
                    dash="dot",
                )

        if has_disp:
            apply_theme(disp_fig)
            disp_fig.update_layout(
                title=dict(
                    text=(
                        "Source Displacement Curves"
                        " + Trendlines"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MWh"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
                hovermode="x unified",
            )
        else:
            disp_fig = _empty_figure(
                "Source Displacement"
            )

        # --- Chart 5: YoY Comparison ---
        if (
            not gen_m.empty
            and "re_pct" in gen_m.columns
        ):
            yoy = compute_yoy_comparison(
                gen_m, "timestamp", "re_pct"
            )
            if not yoy.empty:
                month_names = [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ]
                yoy["month_name"] = yoy[
                    "month"
                ].apply(
                    lambda m: month_names[m - 1]
                    if 1 <= m <= 12
                    else str(m)
                )
                yoy_fig = go.Figure()
                yoy_fig.add_trace(
                    go.Bar(
                        x=yoy["month_name"],
                        y=yoy["prior_year"],
                        name=yoy[
                            "prior_label"
                        ].iloc[0],
                        marker_color=COLORS[
                            "text_muted"
                        ],
                        marker_line_width=0,
                        opacity=0.5,
                    )
                )
                yoy_fig.add_trace(
                    go.Bar(
                        x=yoy["month_name"],
                        y=yoy["current_year"],
                        name=yoy[
                            "current_label"
                        ].iloc[0],
                        marker_color=COLORS[
                            "accent_green"
                        ],
                        marker_line_width=0,
                    )
                )
                apply_theme(yoy_fig)
                yoy_fig.update_layout(
                    title=dict(
                        text=(
                            "RE Share"
                            " \u2014 Year-over-Year"
                        ),
                        font=dict(size=15),
                    ),
                    yaxis=dict(
                        title="Renewable %"
                    ),
                    barmode="group",
                    legend=dict(
                        orientation="h", y=-0.15
                    ),
                )
            else:
                yoy_fig = _empty_figure(
                    "YoY Comparison"
                )
        else:
            yoy_fig = _empty_figure(
                "YoY Comparison"
            )

        return (
            kpis,
            stacked_fig,
            d1_fig,
            d2_fig,
            disp_fig,
            yoy_fig,
        )
