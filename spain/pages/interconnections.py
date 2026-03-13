"""Tab 9: Interconnection Flows — France, Portugal, Morocco borders."""

import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, dcc, html

from components.charts import _empty_figure
from components.kpi_cards import kpi_card
from components.theme import COLORS, apply_theme, card_style
from data.api_client import (
    fetch_cross_border_flows,
    fetch_day_ahead_prices,
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
                    id="es-interconn-timeseries",
                    config={"displayModeBar": False},
                ),
                style=card_style(),
            ),
            html.Div(
                [
                    html.Div(
                        dcc.Graph(
                            id="es-interconn-bar",
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
                            id="es-interconn-price-corr",
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
                "es-interconn-kpis", "children"
            ),
            Output(
                "es-interconn-timeseries", "figure"
            ),
            Output("es-interconn-bar", "figure"),
            Output(
                "es-interconn-price-corr", "figure"
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

        flows = fetch_cross_border_flows(start, end)
        prices = fetch_day_ahead_prices(start, end)

        # Per-border KPIs
        france_str = "N/A"
        portugal_str = "N/A"
        morocco_str = "N/A"
        total_str = "N/A"

        if not flows.empty:
            for border in [
                "France",
                "Portugal",
                "Morocco",
            ]:
                border_data = flows[
                    flows["country"] == border
                ]
                if not border_data.empty:
                    avg_flow = border_data[
                        "flow_mw"
                    ].mean()
                    val = f"{avg_flow:,.0f} MW"
                    direction = (
                        "(Export)"
                        if avg_flow > 0
                        else "(Import)"
                    )
                    if border == "France":
                        france_str = (
                            f"{val} {direction}"
                        )
                    elif border == "Portugal":
                        portugal_str = (
                            f"{val} {direction}"
                        )
                    elif border == "Morocco":
                        morocco_str = (
                            f"{val} {direction}"
                        )

            total_net = flows["flow_mw"].mean()
            total_dir = (
                "(Net Export)"
                if total_net > 0
                else "(Net Import)"
            )
            total_str = (
                f"{total_net:,.0f} MW {total_dir}"
            )

        kpis = html.Div(
            [
                html.Div(
                    kpi_card(
                        "Net France Flow",
                        france_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Net Portugal Flow",
                        portugal_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Net Morocco Flow",
                        morocco_str,
                    ),
                    style={"flex": "1"},
                ),
                html.Div(
                    kpi_card(
                        "Total Net Position",
                        total_str,
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

        # Flow timeseries per border
        if not flows.empty:
            ts_fig = go.Figure()
            for border in [
                "France",
                "Portugal",
                "Morocco",
            ]:
                border_data = flows[
                    flows["country"] == border
                ]
                if not border_data.empty:
                    ts_fig.add_trace(
                        go.Scatter(
                            x=border_data[
                                "timestamp"
                            ],
                            y=border_data["flow_mw"],
                            name=border,
                            mode="lines",
                            line=dict(
                                color=BORDER_COLORS.get(
                                    border,
                                    COLORS[
                                        "accent_blue"
                                    ],
                                ),
                                width=2,
                            ),
                            hovertemplate=(
                                f"{border}: "
                                "%{y:,.0f} MW"
                                "<extra></extra>"
                            ),
                        )
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
                        "Cross-Border Flows"
                        " (+ Export / - Import)"
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
            ts_fig = _empty_figure(
                "Cross-Border Flows"
            )

        # Net import/export bar per border
        if not flows.empty:
            country_net = (
                flows.groupby("country")["flow_mw"]
                .mean()
                .reset_index()
                .sort_values("flow_mw")
            )
            colors = [
                BORDER_COLORS.get(
                    c, COLORS["accent_blue"]
                )
                for c in country_net["country"]
            ]
            bar_fig = go.Figure(
                go.Bar(
                    y=country_net["country"],
                    x=country_net["flow_mw"],
                    orientation="h",
                    marker_color=colors,
                    marker_line_width=0,
                    hovertemplate=(
                        "%{y}: %{x:,.0f} MW"
                        "<extra></extra>"
                    ),
                )
            )
            bar_fig.add_vline(
                x=0,
                line_color=COLORS["text_muted"],
                line_width=1,
            )
            apply_theme(bar_fig)
            bar_fig.update_layout(
                title=dict(
                    text=(
                        "Avg Net Flow by Border"
                        " (MW)"
                    ),
                    font=dict(size=15),
                ),
                xaxis=dict(title="MW"),
                height=300,
            )
        else:
            bar_fig = _empty_figure(
                "Net Flows by Border"
            )

        # Flow vs price correlation
        if not flows.empty and not prices.empty:
            # Aggregate total flow per timestamp
            total_flow = (
                flows.groupby("timestamp")[
                    "flow_mw"
                ]
                .sum()
                .reset_index()
            )
            merged = pd.merge_asof(
                total_flow.sort_values("timestamp"),
                prices.sort_values("timestamp"),
                on="timestamp",
                direction="nearest",
            )
            if not merged.empty:
                corr_fig = go.Figure(
                    go.Scatter(
                        x=merged["flow_mw"],
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
                            "Net Flow: %{x:,.0f}"
                            " MW<br>"
                            "Price: %{y:.1f}"
                            " EUR/MWh"
                            "<extra></extra>"
                        ),
                    )
                )
                apply_theme(corr_fig)
                corr_fig.update_layout(
                    title=dict(
                        text=(
                            "Net Flow vs"
                            " DA Price"
                        ),
                        font=dict(size=15),
                    ),
                    xaxis=dict(
                        title="Net Flow (MW)"
                    ),
                    yaxis=dict(title="EUR/MWh"),
                )
            else:
                corr_fig = _empty_figure(
                    "Flow vs Price"
                )
        else:
            corr_fig = _empty_figure(
                "Flow vs Price"
            )

        return kpis, ts_fig, bar_fig, corr_fig
