"""
BW ESS — German Power Market Dashboard
Strategic market analysis for BESS investment decisions.
Data source: Fraunhofer ISE Energy-Charts API.
"""

from datetime import datetime, timedelta

import dash
from dash import Input, Output, dcc, html

from components.theme import COLORS
from pages import (
    ancillary,
    bess_revenue,
    generation,
    overview,
    prices,
    residual_load,
)

app = dash.Dash(
    __name__,
    title="BW ESS — German Power Market",
    suppress_callback_exceptions=True,
)

# Default date range: last 1 year
today = datetime.now().date()
default_start = today - timedelta(days=365)
default_end = today + timedelta(days=1)

TAB_STYLE = {
    "backgroundColor": COLORS["card"],
    "color": COLORS["text_muted"],
    "border": "none",
    "borderBottom": (
        f"2px solid {COLORS['card_border']}"
    ),
    "padding": "10px 20px",
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
                            "BW ESS \u2014 German Power Market",
                            style={
                                "fontSize": "24px",
                                "fontWeight": "700",
                                "color": COLORS["text"],
                                "margin": "0",
                            },
                        ),
                        html.Div(
                            "Strategic Market Analysis",
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
                    "Data: Fraunhofer ISE Energy-Charts",
                    style={
                        "color": COLORS["text_muted"],
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
                    f"1px solid {COLORS['card_border']}"
                ),
            },
        ),
        # Controls bar: date range + presets
        html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            "90D",
                            id="preset-90d",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "1Y",
                            id="preset-1y",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "2Y",
                            id="preset-2y",
                            n_clicks=0,
                            style=PRESET_BUTTON_STYLE,
                        ),
                        html.Button(
                            "5Y",
                            id="preset-5y",
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
                            date=default_start.isoformat(),
                            display_format="YYYY-MM-DD",
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
                            date=default_end.isoformat(),
                            display_format="YYYY-MM-DD",
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                    },
                ),
            ],
            style={
                "display": "flex",
                "alignItems": "center",
                "padding": "12px 24px",
                "borderBottom": (
                    f"1px solid {COLORS['card_border']}"
                ),
                "backgroundColor": COLORS["card"],
            },
        ),
        # Tabs
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            children=[
                dcc.Tab(
                    label="Strategic Overview",
                    value="overview",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Price Regime",
                    value="prices",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Capacity & Generation",
                    value="generation",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="BESS Business Case",
                    value="bess",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Ancillary Services",
                    value="ancillary",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
                ),
                dcc.Tab(
                    label="Residual Load Structural",
                    value="residual",
                    style=TAB_STYLE,
                    selected_style=TAB_SELECTED_STYLE,
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
            style={"padding": "20px 24px 24px"},
        ),
    ],
    style={
        "backgroundColor": COLORS["bg"],
        "minHeight": "100vh",
        "fontFamily": (
            "Inter, system-ui, -apple-system, sans-serif"
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
    elif tab == "ancillary":
        return ancillary.layout()
    elif tab == "residual":
        return residual_load.layout()
    return html.Div("Select a tab")


@app.callback(
    [
        Output("date-start", "date"),
        Output("date-end", "date"),
    ],
    [
        Input("preset-90d", "n_clicks"),
        Input("preset-1y", "n_clicks"),
        Input("preset-2y", "n_clicks"),
        Input("preset-5y", "n_clicks"),
        Input("preset-ytd", "n_clicks"),
    ],
    prevent_initial_call=True,
)
def apply_preset(
    ninety_clicks,
    one_y_clicks,
    two_y_clicks,
    five_y_clicks,
    ytd_clicks,
):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(
        "."
    )[0]
    now = datetime.now().date()
    end = now + timedelta(days=1)

    if button_id == "preset-90d":
        start = now - timedelta(days=90)
    elif button_id == "preset-1y":
        start = now - timedelta(days=365)
    elif button_id == "preset-2y":
        start = now - timedelta(days=730)
    elif button_id == "preset-5y":
        start = now - timedelta(days=1826)
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
ancillary.register_callbacks(app)
residual_load.register_callbacks(app)


if __name__ == "__main__":
    print(
        "\n  BW ESS — German Power Market"
        " (Strategic Analysis)"
    )
    print("  http://localhost:8051\n")
    app.run(debug=True, port=8051)
