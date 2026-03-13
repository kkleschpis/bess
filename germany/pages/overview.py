"""Tab 1: Strategic Overview — multi-year KPIs and headline trends."""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import (
    _empty_figure,
    monthly_bar_with_rolling_avg,
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
    fetch_installed_capacity_timeseries,
    fetch_monthly_prices,
)


def layout():
    return html.Div(
        [
            html.Div(id="overview-kpis"),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="overview-price-chart",
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
                            id="overview-gen-chart",
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
                            id="overview-residual-chart",
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
                            id="overview-trend-chart",
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
            Output("overview-kpis", "children"),
            Output("overview-price-chart", "figure"),
            Output("overview-gen-chart", "figure"),
            Output(
                "overview-residual-chart", "figure"
            ),
            Output("overview-trend-chart", "figure"),
        ],
        [
            Input("date-start", "date"),
            Input("date-end", "date"),
        ],
    )
    def update_overview(start_date, end_date):
        start = pd.Timestamp(start_date).to_pydatetime()
        end = pd.Timestamp(end_date).to_pydatetime()

        monthly = fetch_monthly_prices(start, end)
        cap_ts = fetch_installed_capacity_timeseries()

        # --- KPIs ---
        # Solar/Wind/BESS installed capacity
        current_year = pd.Timestamp.now().year
        cap_current = cap_ts[
            cap_ts["year"] == current_year
        ]
        cap_prev = cap_ts[
            cap_ts["year"] == current_year - 1
        ]

        def _cap_kpi(source_name):
            cur = cap_current[
                cap_current["source"] == source_name
            ]["capacity_gw"]
            prev = cap_prev[
                cap_prev["source"] == source_name
            ]["capacity_gw"]
            cur_val = (
                cur.iloc[0] if len(cur) > 0 else 0
            )
            prev_val = (
                prev.iloc[0] if len(prev) > 0 else 0
            )
            delta = cur_val - prev_val
            sign = "+" if delta >= 0 else ""
            return (
                f"{cur_val:.1f} GW",
                f"YoY: {sign}{delta:.1f} GW",
            )

        solar_val, solar_delta = _cap_kpi("solar")
        wind_on_val, _ = _cap_kpi("wind_onshore")
        wind_off_val, _ = _cap_kpi("wind_offshore")

        # Combine wind
        wind_on_cur = cap_current[
            cap_current["source"] == "wind_onshore"
        ]["capacity_gw"]
        wind_off_cur = cap_current[
            cap_current["source"] == "wind_offshore"
        ]["capacity_gw"]
        wind_on_prev = cap_prev[
            cap_prev["source"] == "wind_onshore"
        ]["capacity_gw"]
        wind_off_prev = cap_prev[
            cap_prev["source"] == "wind_offshore"
        ]["capacity_gw"]
        wind_cur = (
            (
                wind_on_cur.iloc[0]
                if len(wind_on_cur) > 0
                else 0
            )
            + (
                wind_off_cur.iloc[0]
                if len(wind_off_cur) > 0
                else 0
            )
        )
        wind_prev = (
            (
                wind_on_prev.iloc[0]
                if len(wind_on_prev) > 0
                else 0
            )
            + (
                wind_off_prev.iloc[0]
                if len(wind_off_prev) > 0
                else 0
            )
        )
        wind_delta = wind_cur - wind_prev
        wind_sign = "+" if wind_delta >= 0 else ""
        wind_val = f"{wind_cur:.1f} GW"
        wind_delta_str = (
            f"YoY: {wind_sign}{wind_delta:.1f} GW"
        )

        bess_val, bess_delta = _cap_kpi(
            "battery_storage"
        )

        # Trailing 12m avg price
        if not monthly.empty and len(monthly) >= 2:
            trail_12 = monthly.tail(12)[
                "avg_price"
            ].mean()
            if len(monthly) >= 24:
                prior_12 = monthly.iloc[-24:-12][
                    "avg_price"
                ].mean()
                price_yoy = trail_12 - prior_12
                sign = "+" if price_yoy >= 0 else ""
                price_sub = (
                    f"vs prior 12m:"
                    f" {sign}{price_yoy:.1f}"
                )
            else:
                price_sub = "Trailing 12 months"
            price_str = f"{trail_12:.1f} EUR/MWh"
        else:
            price_str = "N/A"
            price_sub = ""

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Installed Solar",
                        solar_val,
                        solar_delta,
                        color=SOURCE_COLORS["solar"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Installed Wind",
                        wind_val,
                        wind_delta_str,
                        color=SOURCE_COLORS[
                            "wind_onshore"
                        ],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Installed BESS",
                        bess_val,
                        bess_delta,
                        color=COLORS["accent_cyan"],
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Avg DA Price (12m)",
                        price_str,
                        price_sub,
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

        # --- Chart 1: Monthly avg DA price ---
        if not monthly.empty:
            price_fig = monthly_bar_with_rolling_avg(
                x=monthly["month_str"],
                y=monthly["avg_price"],
                title="Monthly Avg DA Price",
                y_title="EUR/MWh",
                bar_color=COLORS["accent_blue"],
                rolling_windows=[
                    (
                        12,
                        "12M Rolling Avg",
                        COLORS["accent_amber"],
                    ),
                ],
            )
        else:
            price_fig = _empty_figure(
                "Monthly Avg DA Price"
            )

        # --- Chart 2: Monthly renewable share ---
        gen = fetch_generation_by_source(start, end)
        if not gen.empty:
            gen_c = gen.copy()
            gen_c["month"] = gen_c[
                "timestamp"
            ].dt.to_period("M")
            source_cols = [
                c
                for c in gen_c.columns
                if c not in ("timestamp", "month")
            ]
            monthly_gen = (
                gen_c.groupby("month")[source_cols]
                .sum()
                .reset_index()
            )
            re_cols = [
                c
                for c in [
                    "solar",
                    "wind_onshore",
                    "wind_offshore",
                ]
                if c in monthly_gen.columns
            ]
            monthly_gen["total"] = monthly_gen[
                source_cols
            ].sum(axis=1)
            monthly_gen["re_total"] = monthly_gen[
                re_cols
            ].sum(axis=1)
            monthly_gen["re_share"] = (
                monthly_gen["re_total"]
                / monthly_gen["total"]
                * 100
            )
            monthly_gen["month_str"] = monthly_gen[
                "month"
            ].astype(str)

            re_series = pd.Series(
                monthly_gen["re_share"].values
            )
            rolling_12 = re_series.rolling(
                12, min_periods=1
            ).mean()

            gen_fig = go.Figure()
            gen_fig.add_trace(
                go.Scatter(
                    x=monthly_gen[
                        "month_str"
                    ].tolist(),
                    y=monthly_gen[
                        "re_share"
                    ].tolist(),
                    mode="lines+markers",
                    name="Monthly RE Share",
                    line=dict(
                        color=COLORS["accent_green"],
                        width=2,
                    ),
                    marker=dict(size=4),
                    hovertemplate=(
                        "%{x}<br>"
                        "%{y:.1f}%<extra></extra>"
                    ),
                )
            )
            gen_fig.add_trace(
                go.Scatter(
                    x=monthly_gen[
                        "month_str"
                    ].tolist(),
                    y=rolling_12.tolist(),
                    mode="lines",
                    name="12M Trend",
                    line=dict(
                        color=COLORS["accent_amber"],
                        width=2.5,
                        dash="dash",
                    ),
                )
            )
            apply_theme(gen_fig)
            gen_fig.update_layout(
                title=dict(
                    text="Monthly Renewable Share (%)",
                    font=dict(size=15),
                ),
                yaxis=dict(title="%"),
                legend=dict(
                    orientation="h", y=-0.15
                ),
            )
        else:
            gen_fig = _empty_figure(
                "Monthly Renewable Share"
            )

        # --- Chart 3: Monthly peak/off-peak spread ---
        if not monthly.empty:
            spread_fig = monthly_bar_with_rolling_avg(
                x=monthly["month_str"],
                y=monthly["spread"],
                title=(
                    "Monthly Avg Peak/Off-Peak Spread"
                ),
                y_title="EUR/MWh",
                bar_color=COLORS["accent_amber"],
                rolling_windows=[
                    (
                        6,
                        "6M Rolling",
                        COLORS["accent_cyan"],
                    ),
                ],
            )
        else:
            spread_fig = _empty_figure(
                "Peak/Off-Peak Spread"
            )

        # --- Chart 4: Installed capacity trajectory ---
        if not cap_ts.empty:
            key_sources = [
                "solar",
                "wind_onshore",
                "wind_offshore",
                "battery_storage",
            ]
            cap_chart = cap_ts[
                (cap_ts["source"].isin(key_sources))
                & (cap_ts["year"] >= 2015)
            ].copy()

            source_colors = {
                "solar": SOURCE_COLORS["solar"],
                "wind_onshore": SOURCE_COLORS[
                    "wind_onshore"
                ],
                "wind_offshore": SOURCE_COLORS[
                    "wind_offshore"
                ],
                "battery_storage": COLORS[
                    "accent_cyan"
                ],
            }
            source_labels = {
                "solar": "Solar",
                "wind_onshore": "Wind Onshore",
                "wind_offshore": "Wind Offshore",
                "battery_storage": "Battery Storage",
            }

            cap_fig = go.Figure()
            for src in key_sources:
                src_data = cap_chart[
                    cap_chart["source"] == src
                ].sort_values("year")
                if src_data.empty:
                    continue
                cap_fig.add_trace(
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

            # EEG 2023 target markers
            eeg_targets = {
                2030: {
                    "solar": 215,
                    "wind_onshore": 115,
                    "wind_offshore": 30,
                },
            }
            for year, targets in eeg_targets.items():
                total_target = sum(targets.values())
                cap_fig.add_trace(
                    go.Scatter(
                        x=[year],
                        y=[total_target],
                        mode="markers",
                        marker=dict(
                            symbol="star",
                            size=14,
                            color=COLORS[
                                "accent_red"
                            ],
                            line=dict(
                                width=1,
                                color=COLORS["text"],
                            ),
                        ),
                        name=f"EEG {year} Target",
                        hovertemplate=(
                            f"EEG {year}:"
                            f" {total_target} GW"
                            "<extra></extra>"
                        ),
                    )
                )

            apply_theme(cap_fig)
            cap_fig.update_layout(
                title=dict(
                    text=(
                        "Installed Capacity Trajectory"
                        " (2015-2030)"
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
            cap_fig = _empty_figure(
                "Installed Capacity"
            )

        return (
            kpis,
            price_fig,
            gen_fig,
            spread_fig,
            cap_fig,
        )
