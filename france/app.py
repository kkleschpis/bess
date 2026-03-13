"""
BW ESS — French Power Market Dashboard
Strategic Investment View for BESS deployments in France.
Data source: Fraunhofer ISE / Energy-Charts (country=fr, bzn=FR).
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add BESS root to sys.path so shared components resolve.
# Use append (not insert) so local france/data takes priority
# over root data/.
_bess_root = str(Path(__file__).resolve().parent.parent)
if _bess_root not in sys.path:
    sys.path.append(_bess_root)

import dash
from dash import Input, Output, dcc, html

from components.theme import COLORS
from pages import (
    ancillary,
    bess_revenue,
    commodities,
    generation,
    interconnections,
    nuclear,
    overview,
    prices,
    residual_load,
)

app = dash.Dash(
    __name__,
    title="BW ESS \u2014 French Power Market",
    suppress_callback_exceptions=True,
)

# Default date range: last 7 days
today = datetime.now().date()
default_start = today - timedelta(days=7)
default_end = today + timedelta(days=1)

TAB_STYLE = {
    "backgroundColor": COLORS["card"],
    "color": COLORS["text_muted"],
    "border": "none",
    "borderBottom": (
        f"2px solid {COLORS['card_border']}"
    ),
    "padding": "10px 16px",
    "fontWeight": "500",
    "fontSize": "13px",
}

TAB_SELECTED_STYLE = {
    **TAB_STYLE,
    "color": COLORS["text"],
    "borderBottom": (
        f"2px solid {COLORS['accent_blue']}"
    ),
}

PRESET_BUTTON_STYLE = {
    "backgroundColor": COLORS["card"],
    "color": COLORS["text_muted"],
    "border": f"1px solid {COLORS['card_border']}",
    "borderRadius": "6px",
    "padding": "4px 12px",
    "fontSize": "12px",
    "cursor": "pointer",
    "marginRight": "4px",
}

app.layout = html.Div(
    [
        # Header
        html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "BW ESS \u2014 French Power"
                            " Market",
                            style={
                                "fontSize": "24px",
                                "fontWeight": "700",
                                "color": COLORS[
                                    "text"
                                ],
                                "margin": "0",
                            },
                        ),
                        html.Div(
                            "Strategic Investment"
                            " View \u2022 Long-Term"
                            " Market Intelligence",
                            style={
                                "color": COLORS[
                                    "text_muted"
                                ],
                                "fontSize": "13px",
                                "marginTop": "4px",
                            },
                        ),
                    ],
                ),
                html.Div(
                    "Data: Fraunhofer ISE /"
                    " Energy-Charts",
                    style={
                        "color": COLORS[
                            "text_muted"
                        ],
                        "fontSize": "12px",
                        "textAlign": "right",
                    },
                ),
            ],
            style={
                "display": "flex",
                "justifyContent": "space-between",
                "alignItems": "center",
                "padding": "16px 24px",
                "borderBottom": (
                    "1px solid "
                    f"{COLORS['card_border']}"
                ),
            },
        ),
        # Controls bar
        html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            "Today",
                            id="preset-today",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "7D",
                            id="preset-7d",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "30D",
                            id="preset-30d",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "90D",
                            id="preset-90d",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "YTD",
                            id="preset-ytd",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginRight": "16px",
                    },
                ),
                html.Div(
                    [
                        html.Label(
                            "From:",
                            style={
                                "color": COLORS[
                                    "text_muted"
                                ],
                                "fontSize": "12px",
                                "marginRight": "6px",
                            },
                        ),
                        dcc.DatePickerSingle(
                            id="date-start",
                            date=(
                                default_start.isoformat()
                            ),
                            display_format=(
                                "YYYY-MM-DD"
                            ),
                            style={
                                "marginRight": "12px"
                            },
                        ),
                        html.Label(
                            "To:",
                            style={
                                "color": COLORS[
                                    "text_muted"
                                ],
                                "fontSize": "12px",
                                "marginRight": "6px",
                            },
                        ),
                        dcc.DatePickerSingle(
                            id="date-end",
                            date=(
                                default_end.isoformat()
                            ),
                            display_format=(
                                "YYYY-MM-DD"
                            ),
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "marginRight": "16px",
                    },
                ),
                html.Div(
                    [
                        dcc.Checklist(
                            id="auto-refresh",
                            options=[
                                {
                                    "label": (
                                        " Auto-refresh"
                                        " (5 min)"
                                    ),
                                    "value": "on",
                                },
                            ],
                            value=[],
                            style={
                                "color": COLORS[
                                    "text_muted"
                                ],
                                "fontSize": "12px",
                            },
                        ),
                    ],
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": "12px 24px",
                "borderBottom": (
                    "1px solid "
                    f"{COLORS['card_border']}"
                ),
                "backgroundColor": COLORS["card"],
            },
        ),
        # Auto-refresh interval
        dcc.Interval(
            id="refresh-interval",
            interval=5 * 60 * 1000,
            disabled=True,
        ),
        # Tabs — 9 tabs for France
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            children=[
                dcc.Tab(
                    label="Market Overview",
                    value="overview",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Price Analysis",
                    value="prices",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Generation Mix",
                    value="generation",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="BESS Arbitrage",
                    value="bess",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Nuclear Fleet",
                    value="nuclear",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Ancillary Services",
                    value="ancillary",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Residual Load",
                    value="residual",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Commodities",
                    value="commodities",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
                dcc.Tab(
                    label="Interconnections",
                    value="interconnections",
                    style=TAB_STYLE,
                    selected_style=(
                        TAB_SELECTED_STYLE
                    ),
                ),
            ],
            style={
                "padding": "0 24px",
                "marginTop": "8px",
            },
        ),
        # Tab content
        html.Div(
            id="tab-content",
            style={
                "padding": "20px 24px 24px"
            },
        ),
    ],
    style={
        "backgroundColor": COLORS["bg"],
        "minHeight": "100vh",
        "fontFamily": (
            "Inter, system-ui,"
            " -apple-system, sans-serif"
        ),
    },
)


# --- Callbacks ---


@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "value"),
)
def render_tab(tab):
    if tab == "overview":
        return overview.layout()
    elif tab == "prices":
        return prices.layout()
    elif tab == "generation":
        return generation.layout()
    elif tab == "bess":
        return bess_revenue.layout()
    elif tab == "nuclear":
        return nuclear.layout()
    elif tab == "ancillary":
        return ancillary.layout()
    elif tab == "residual":
        return residual_load.layout()
    elif tab == "commodities":
        return commodities.layout()
    elif tab == "interconnections":
        return interconnections.layout()
    return html.Div("Select a tab")


@app.callback(
    Output("refresh-interval", "disabled"),
    Input("auto-refresh", "value"),
)
def toggle_refresh(value):
    return "on" not in (value or [])


@app.callback(
    [
        Output("date-start", "date"),
        Output("date-end", "date"),
    ],
    [
        Input("preset-today", "n_clicks"),
        Input("preset-7d", "n_clicks"),
        Input("preset-30d", "n_clicks"),
        Input("preset-90d", "n_clicks"),
        Input("preset-ytd", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def apply_preset(
    today_clicks,
    seven_clicks,
    thirty_clicks,
    ninety_clicks,
    ytd_clicks,
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    button_id = ctx.triggered[0][
        "prop_id"
    ].split(".")[0]
    now = datetime.now().date()
    end = now + timedelta(days=1)

    if button_id == "preset-today":
        start = now
    elif button_id == "preset-7d":
        start = now - timedelta(days=7)
    elif button_id == "preset-30d":
        start = now - timedelta(days=30)
    elif button_id == "preset-90d":
        start = now - timedelta(days=90)
    elif button_id == "preset-ytd":
        start = now.replace(month=1, day=1)
    else:
        return dash.no_update, dash.no_update

    return start.isoformat(), end.isoformat()


# Register page-level callbacks
overview.register_callbacks(app)
prices.register_callbacks(app)
generation.register_callbacks(app)
bess_revenue.register_callbacks(app)
nuclear.register_callbacks(app)
ancillary.register_callbacks(app)
residual_load.register_callbacks(app)
commodities.register_callbacks(app)
interconnections.register_callbacks(app)


if __name__ == "__main__":
    print(
        "\n  BW ESS \u2014 French Power"
        " Market Dashboard"
    )
    print("  http://localhost:8053\n")
    app.run(debug=True, port=8053)
