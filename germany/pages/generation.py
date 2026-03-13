"""Tab 3: Capacity & Generation — installed capacity buildout and derivatives."""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import (
    COLORS,
    SOURCE_COLORS,
    apply_theme,
    card_style,
)
from data.api_client import (
    fetch_generation_by_source,
    fetch_installed_capacity_timeseries,
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
                            id="gen-wind-profile",
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
                            id="gen-capacity",
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
                            id="gen-fossil-decline",
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
            Output("gen-kpis", "children"),
            Output("gen-stacked", "figure"),
            Output("gen-solar-profile", "figure"),
            Output("gen-wind-profile", "figure"),
            Output("gen-capacity", "figure"),
            Output("gen-fossil-decline", "figure"),
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

        cap_ts = fetch_installed_capacity_timeseries()
        gen = fetch_generation_by_source(start, end)

        current_year = pd.Timestamp.now().year
        cap_cur = cap_ts[
            cap_ts["year"] == current_year
        ]
        cap_prev = cap_ts[
            cap_ts["year"] == current_year - 1
        ]

        def _get_cap(df, src):
            vals = df[df["source"] == src][
                "capacity_gw"
            ]
            return vals.iloc[0] if len(vals) > 0 else 0

        def _growth_rate(src):
            cur = _get_cap(cap_cur, src)
            prev = _get_cap(cap_prev, src)
            if prev > 0:
                return (cur - prev) / prev * 100
            return 0

        solar_gw = _get_cap(cap_cur, "solar")
        solar_gr = _growth_rate("solar")
        wind_gw = _get_cap(
            cap_cur, "wind_onshore"
        ) + _get_cap(cap_cur, "wind_offshore")
        wind_prev = _get_cap(
            cap_prev, "wind_onshore"
        ) + _get_cap(cap_prev, "wind_offshore")
        wind_gr = (
            (wind_gw - wind_prev) / wind_prev * 100
            if wind_prev > 0
            else 0
        )
        bess_gw = _get_cap(
            cap_cur, "battery_storage"
        )
        bess_gr = _growth_rate("battery_storage")

        fossil_sources = [
            "gas",
            "hard_coal",
            "lignite",
            "oil",
            "nuclear",
        ]
        fossil_gw = sum(
            _get_cap(cap_cur, s)
            for s in fossil_sources
        )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Solar Installed",
                        f"{solar_gw:.1f} GW",
                        f"+{solar_gr:.1f}% YoY",
                        color=SOURCE_COLORS["solar"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Wind Installed",
                        f"{wind_gw:.1f} GW",
                        f"+{wind_gr:.1f}% YoY",
                        color=SOURCE_COLORS[
                            "wind_onshore"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "BESS Installed",
                        f"{bess_gw:.1f} GW",
                        f"+{bess_gr:.1f}% YoY",
                        color=COLORS["accent_cyan"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Fossil Capacity",
                        f"{fossil_gw:.1f} GW",
                        "Remaining dispatchable",
                        color=COLORS["accent_red"],
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

        # --- Chart 1: Installed capacity stacked area ---
        key_sources = [
            "solar",
            "wind_onshore",
            "wind_offshore",
            "battery_storage",
            "gas",
            "hard_coal",
            "lignite",
        ]
        source_labels = {
            "solar": "Solar",
            "wind_onshore": "Wind Onshore",
            "wind_offshore": "Wind Offshore",
            "battery_storage": "Battery Storage",
            "gas": "Gas",
            "hard_coal": "Hard Coal",
            "lignite": "Lignite",
        }
        source_colors = {
            "solar": SOURCE_COLORS["solar"],
            "wind_onshore": SOURCE_COLORS[
                "wind_onshore"
            ],
            "wind_offshore": SOURCE_COLORS[
                "wind_offshore"
            ],
            "battery_storage": COLORS["accent_cyan"],
            "gas": SOURCE_COLORS["gas"],
            "hard_coal": SOURCE_COLORS["hard_coal"],
            "lignite": SOURCE_COLORS["lignite"],
        }

        if not cap_ts.empty:
            cap_filt = cap_ts[
                (cap_ts["source"].isin(key_sources))
                & (cap_ts["year"] >= 2010)
            ]
            stacked_fig = go.Figure()
            for src in key_sources:
                src_data = cap_filt[
                    cap_filt["source"] == src
                ].sort_values("year")
                if src_data.empty:
                    continue
                stacked_fig.add_trace(
                    go.Scatter(
                        x=src_data["year"],
                        y=src_data["capacity_gw"],
                        name=source_labels.get(
                            src, src
                        ),
                        mode="lines",
                        line=dict(width=0),
                        fillcolor=source_colors.get(
                            src,
                            COLORS["accent_blue"],
                        ),
                        stackgroup="cap",
                        hovertemplate=(
                            f"{source_labels.get(src, src)}"
                            ": %{y:.1f} GW"
                            "<extra></extra>"
                        ),
                    )
                )
            apply_theme(stacked_fig)
            stacked_fig.update_layout(
                title=dict(
                    text=(
                        "Installed Capacity by Source"
                        " (2010-2030)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="GW"),
                hovermode="x unified",
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            stacked_fig = _empty_figure(
                "Installed Capacity"
            )

        # --- Chart 2: Annual capacity additions (1st derivative) ---
        re_sources = [
            "solar",
            "wind_onshore",
            "wind_offshore",
            "battery_storage",
        ]
        if not cap_ts.empty:
            additions_rows = []
            for src in re_sources:
                src_data = (
                    cap_ts[cap_ts["source"] == src]
                    .sort_values("year")
                    .copy()
                )
                if len(src_data) < 2:
                    continue
                src_data["addition"] = src_data[
                    "capacity_gw"
                ].diff()
                for _, row in src_data.iterrows():
                    if pd.notna(row["addition"]):
                        additions_rows.append({
                            "year": row["year"],
                            "source": src,
                            "addition_gw": row[
                                "addition"
                            ],
                        })
            additions = pd.DataFrame(additions_rows)

            if not additions.empty:
                additions_filt = additions[
                    additions["year"] >= 2015
                ]
                add_fig = go.Figure()
                for src in re_sources:
                    src_d = additions_filt[
                        additions_filt["source"] == src
                    ]
                    if src_d.empty:
                        continue
                    add_fig.add_trace(
                        go.Bar(
                            x=src_d["year"],
                            y=src_d["addition_gw"],
                            name=source_labels.get(
                                src, src
                            ),
                            marker_color=(
                                source_colors.get(
                                    src,
                                    COLORS[
                                        "accent_blue"
                                    ],
                                )
                            ),
                            hovertemplate=(
                                f"{source_labels.get(src, src)}"
                                ": %{y:.2f} GW"
                                "<extra></extra>"
                            ),
                        )
                    )
                apply_theme(add_fig)
                add_fig.update_layout(
                    title=dict(
                        text=(
                            "Annual Capacity Additions"
                            " (GW/year)"
                        ),
                        font=dict(size=15),
                    ),
                    yaxis=dict(title="GW"),
                    barmode="group",
                    legend=dict(
                        orientation="h", y=-0.15
                    ),
                )
            else:
                add_fig = _empty_figure(
                    "Capacity Additions"
                )
        else:
            add_fig = _empty_figure(
                "Capacity Additions"
            )

        # --- Chart 3: Capacity addition acceleration (2nd derivative) ---
        if not cap_ts.empty and not additions.empty:
            accel_rows = []
            for src in re_sources:
                src_add = (
                    additions[
                        additions["source"] == src
                    ]
                    .sort_values("year")
                    .copy()
                )
                if len(src_add) < 2:
                    continue
                src_add["acceleration"] = src_add[
                    "addition_gw"
                ].diff()
                for _, row in src_add.iterrows():
                    if pd.notna(row["acceleration"]):
                        accel_rows.append({
                            "year": row["year"],
                            "source": src,
                            "accel_gw": row[
                                "acceleration"
                            ],
                        })
            accel = pd.DataFrame(accel_rows)

            if not accel.empty:
                accel_filt = accel[
                    accel["year"] >= 2015
                ]
                accel_fig = go.Figure()
                for src in re_sources:
                    src_d = accel_filt[
                        accel_filt["source"] == src
                    ]
                    if src_d.empty:
                        continue
                    accel_fig.add_trace(
                        go.Bar(
                            x=src_d["year"],
                            y=src_d["accel_gw"],
                            name=source_labels.get(
                                src, src
                            ),
                            marker_color=(
                                source_colors.get(
                                    src,
                                    COLORS[
                                        "accent_blue"
                                    ],
                                )
                            ),
                            hovertemplate=(
                                f"{source_labels.get(src, src)}"
                                ": %{y:.2f} GW"
                                "<extra></extra>"
                            ),
                        )
                    )
                accel_fig.add_hline(
                    y=0,
                    line_dash="dash",
                    line_color=COLORS["text_muted"],
                    line_width=1,
                )
                apply_theme(accel_fig)
                accel_fig.update_layout(
                    title=dict(
                        text=(
                            "Capacity Addition"
                            " Acceleration"
                            " (YoY change in additions)"
                        ),
                        font=dict(size=15),
                    ),
                    yaxis=dict(title="GW"),
                    barmode="group",
                    legend=dict(
                        orientation="h", y=-0.15
                    ),
                )
            else:
                accel_fig = _empty_figure(
                    "Addition Acceleration"
                )
        else:
            accel_fig = _empty_figure(
                "Addition Acceleration"
            )

        # --- Chart 4: Monthly solar + wind capacity factor ---
        if not gen.empty and not cap_ts.empty:
            gen_c = gen.copy()
            gen_c["month"] = gen_c[
                "timestamp"
            ].dt.to_period("M")
            gen_c["year"] = gen_c[
                "timestamp"
            ].dt.year

            re_gen_cols = [
                c
                for c in [
                    "solar",
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in gen_c.columns
            ]
            if re_gen_cols:
                gen_c["re_total"] = gen_c[
                    re_gen_cols
                ].sum(axis=1)
                monthly_gen = (
                    gen_c.groupby("month")
                    .agg(
                        re_mw=("re_total", "mean"),
                        hours=(
                            "timestamp",
                            "count",
                        ),
                    )
                    .reset_index()
                )
                # Approximate installed capacity
                # from yearly data
                latest_re_gw = sum(
                    _get_cap(cap_cur, s)
                    for s in [
                        "solar",
                        "wind_onshore",
                        "wind_offshore",
                    ]
                )
                installed_mw = latest_re_gw * 1000
                if installed_mw > 0:
                    monthly_gen["cap_factor"] = (
                        monthly_gen["re_mw"]
                        / installed_mw
                        * 100
                    )
                    monthly_gen["month_str"] = (
                        monthly_gen["month"].astype(
                            str
                        )
                    )

                    cf_fig = go.Figure()
                    cf_fig.add_trace(
                        go.Scatter(
                            x=monthly_gen[
                                "month_str"
                            ].tolist(),
                            y=monthly_gen[
                                "cap_factor"
                            ].tolist(),
                            mode="lines+markers",
                            name="Capacity Factor",
                            line=dict(
                                color=COLORS[
                                    "accent_green"
                                ],
                                width=2,
                            ),
                            marker=dict(size=4),
                            hovertemplate=(
                                "%{x}<br>"
                                "%{y:.1f}%"
                                "<extra></extra>"
                            ),
                        )
                    )
                    apply_theme(cf_fig)
                    cf_fig.update_layout(
                        title=dict(
                            text=(
                                "Monthly Solar+Wind"
                                " Capacity Factor (%)"
                            ),
                            font=dict(size=15),
                        ),
                        yaxis=dict(title="%"),
                    )
                else:
                    cf_fig = _empty_figure(
                        "Capacity Factor"
                    )
            else:
                cf_fig = _empty_figure(
                    "Capacity Factor"
                )
        else:
            cf_fig = _empty_figure("Capacity Factor")

        # --- Chart 5: Fossil generation decline ---
        fossil_gen_cols = [
            c
            for c in [
                "gas",
                "hard_coal",
                "lignite",
                "oil",
            ]
            if c in gen.columns
        ]
        if not gen.empty and fossil_gen_cols:
            gen_f = gen.copy()
            gen_f["month"] = gen_f[
                "timestamp"
            ].dt.to_period("M")
            gen_f["fossil_mw"] = gen_f[
                fossil_gen_cols
            ].sum(axis=1)
            monthly_fossil = (
                gen_f.groupby("month")["fossil_mw"]
                .mean()
                .reset_index()
            )
            monthly_fossil["month_str"] = (
                monthly_fossil["month"].astype(str)
            )

            fossil_series = pd.Series(
                monthly_fossil["fossil_mw"].values
            )
            rolling_6 = fossil_series.rolling(
                6, min_periods=1
            ).mean()

            fossil_fig = go.Figure()
            fossil_fig.add_trace(
                go.Scatter(
                    x=monthly_fossil[
                        "month_str"
                    ].tolist(),
                    y=monthly_fossil[
                        "fossil_mw"
                    ].tolist(),
                    mode="lines",
                    name="Monthly Avg",
                    line=dict(
                        color=COLORS["accent_red"],
                        width=1.5,
                    ),
                    fill="tozeroy",
                    fillcolor=(
                        "rgba(239,68,68,0.1)"
                    ),
                )
            )
            fossil_fig.add_trace(
                go.Scatter(
                    x=monthly_fossil[
                        "month_str"
                    ].tolist(),
                    y=rolling_6.tolist(),
                    mode="lines",
                    name="6M Trend",
                    line=dict(
                        color=COLORS[
                            "accent_amber"
                        ],
                        width=2.5,
                    ),
                )
            )
            apply_theme(fossil_fig)
            fossil_fig.update_layout(
                title=dict(
                    text=(
                        "Monthly Avg Fossil"
                        " Generation (MW)"
                    ),
                    font=dict(size=15),
                ),
                yaxis=dict(title="MW"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            fossil_fig = _empty_figure(
                "Fossil Generation"
            )

        return (
            kpis,
            stacked_fig,
            add_fig,
            accel_fig,
            cf_fig,
            fossil_fig,
        )
