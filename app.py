"""
BESS Market Intelligence Dashboard
Modo Energy-style interactive dashboard for Battery Energy Storage Systems.
Data sourced from Volta Foundation Battery Reports (2021-2024).
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import plotly.express as px
from data.bess_data import (
    bess_deployments,
    bess_by_region,
    battery_prices,
    battery_prices_by_chemistry,
    chemistry_mix,
    bess_chemistry,
    manufacturing_capacity,
    manufacturing_by_region,
    raw_materials_combined,
    investment_data,
    demand_by_application,
    bess_cost_breakdown,
    bess_system_cost,
    key_watchpoints,
    key_developments_timeline,
)

# =============================================================================
# THEME & STYLING (Modo Energy-inspired dark theme)
# =============================================================================
COLORS = {
    "bg": "#0a0e17",
    "card": "#111827",
    "card_border": "#1e293b",
    "text": "#e2e8f0",
    "text_muted": "#94a3b8",
    "accent_blue": "#3b82f6",
    "accent_green": "#10b981",
    "accent_amber": "#f59e0b",
    "accent_red": "#ef4444",
    "accent_purple": "#8b5cf6",
    "accent_cyan": "#06b6d4",
    "grid": "#1e293b",
    "highlight": "#1e3a5f",
}

CHART_COLORS = [
    "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
]

PLOT_LAYOUT = dict(
    paper_bgcolor=COLORS["card"],
    plot_bgcolor=COLORS["card"],
    font=dict(color=COLORS["text"], family="Inter, system-ui, sans-serif", size=12),
    margin=dict(l=50, r=20, t=40, b=40),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=11, color=COLORS["text_muted"]),
    ),
    hoverlabel=dict(
        bgcolor=COLORS["card"],
        font_size=12,
        font_family="Inter, system-ui, sans-serif",
        bordercolor=COLORS["accent_blue"],
    ),
)

AXIS_STYLE = dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"])


def apply_theme(fig):
    """Apply common theme to a plotly figure."""
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def card_style(height=None):
    style = {
        "backgroundColor": COLORS["card"],
        "border": f"1px solid {COLORS['card_border']}",
        "borderRadius": "12px",
        "padding": "20px",
        "marginBottom": "16px",
    }
    if height:
        style["height"] = height
    return style


def kpi_card(title, value, change=None, change_positive=True):
    change_el = []
    if change:
        color = COLORS["accent_green"] if change_positive else COLORS["accent_red"]
        arrow = "\u25B2" if change_positive else "\u25BC"
        change_el = [
            html.Span(
                f" {arrow} {change}",
                style={"color": color, "fontSize": "14px", "fontWeight": "500"},
            )
        ]
    return html.Div(
        [
            html.Div(
                title,
                style={
                    "color": COLORS["text_muted"],
                    "fontSize": "12px",
                    "fontWeight": "500",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.05em",
                    "marginBottom": "8px",
                },
            ),
            html.Div(
                [
                    html.Span(
                        value,
                        style={
                            "color": COLORS["text"],
                            "fontSize": "28px",
                            "fontWeight": "700",
                        },
                    ),
                    *change_el,
                ],
            ),
        ],
        style=card_style(),
    )


# =============================================================================
# CHARTS
# =============================================================================
def create_bess_deployment_chart():
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=bess_deployments["Year"],
        y=bess_deployments["Annual Installations (GWh)"],
        name="Annual (GWh)",
        marker_color=COLORS["accent_blue"],
        marker_line_width=0,
        opacity=0.85,
    ))
    fig.add_trace(go.Scatter(
        x=bess_deployments["Year"],
        y=bess_deployments["Cumulative Capacity (GWh)"],
        name="Cumulative (GWh)",
        mode="lines+markers",
        line=dict(color=COLORS["accent_cyan"], width=2.5),
        marker=dict(size=7),
        yaxis="y2",
    ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Global Grid-Scale BESS Deployments", font=dict(size=15)),
        yaxis=dict(title="Annual (GWh)"),
        yaxis2=dict(
            title="Cumulative (GWh)",
            overlaying="y",
            side="right",
            gridcolor="rgba(0,0,0,0)",
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(0,0,0,0)"),
        barmode="group",
    )
    return fig


def create_bess_by_region_chart():
    fig = px.bar(
        bess_by_region,
        x="Year",
        y="Installations (GWh)",
        color="Region",
        barmode="stack",
        color_discrete_sequence=CHART_COLORS,
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="BESS Deployments by Region", font=dict(size=15)),
    )
    return fig


def create_price_trend_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=battery_prices["Year"],
        y=battery_prices["Pack Price ($/kWh)"],
        name="Pack Price",
        mode="lines+markers",
        line=dict(color=COLORS["accent_blue"], width=2.5),
        marker=dict(size=7),
        fill="tozeroy",
        fillcolor="rgba(59, 130, 246, 0.1)",
    ))
    fig.add_trace(go.Scatter(
        x=battery_prices["Year"],
        y=battery_prices["Cell Price ($/kWh)"],
        name="Cell Price",
        mode="lines+markers",
        line=dict(color=COLORS["accent_green"], width=2.5),
        marker=dict(size=7),
    ))
    fig.add_hline(
        y=100, line_dash="dash", line_color=COLORS["accent_amber"],
        annotation_text="$100/kWh target",
        annotation_font_color=COLORS["accent_amber"],
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Battery Pack & Cell Prices ($/kWh)", font=dict(size=15)),
        yaxis=dict(title="$/kWh"),
    )
    return fig


def create_chemistry_by_price_chart():
    fig = go.Figure()
    lfp = battery_prices_by_chemistry[battery_prices_by_chemistry["Chemistry"] == "LFP"]
    nmc = battery_prices_by_chemistry[battery_prices_by_chemistry["Chemistry"] == "NMC"]
    fig.add_trace(go.Bar(
        x=lfp["Year"], y=lfp["Pack Price ($/kWh)"],
        name="LFP", marker_color=COLORS["accent_green"], opacity=0.85,
    ))
    fig.add_trace(go.Bar(
        x=nmc["Year"], y=nmc["Pack Price ($/kWh)"],
        name="NMC", marker_color=COLORS["accent_blue"], opacity=0.85,
    ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Pack Price by Chemistry ($/kWh)", font=dict(size=15)),
        yaxis=dict(title="$/kWh"),
        barmode="group",
    )
    return fig


def create_chemistry_mix_chart():
    fig = go.Figure()
    for col, color in [
        ("LFP (%)", COLORS["accent_green"]),
        ("NMC (%)", COLORS["accent_blue"]),
        ("NCA (%)", COLORS["accent_amber"]),
        ("Other (%)", COLORS["accent_purple"]),
    ]:
        fig.add_trace(go.Scatter(
            x=chemistry_mix["Year"],
            y=chemistry_mix[col],
            name=col.replace(" (%)", ""),
            mode="lines+markers",
            line=dict(width=2.5, color=color),
            marker=dict(size=6),
            stackgroup="one",
        ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Global Battery Chemistry Market Share", font=dict(size=15)),
        yaxis=dict(title="Market Share (%)", range=[0, 100]),
    )
    return fig


def create_bess_chemistry_chart():
    fig = go.Figure()
    for col, color in [
        ("LFP (%)", COLORS["accent_green"]),
        ("NMC (%)", COLORS["accent_blue"]),
        ("Other (%)", COLORS["accent_purple"]),
    ]:
        fig.add_trace(go.Bar(
            x=bess_chemistry["Year"],
            y=bess_chemistry[col],
            name=col.replace(" (%)", ""),
            marker_color=color,
            opacity=0.85,
        ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="BESS Chemistry Mix (Grid Storage)", font=dict(size=15)),
        yaxis=dict(title="Share (%)"),
        barmode="stack",
    )
    return fig


def create_manufacturing_chart():
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=manufacturing_capacity["Year"],
        y=manufacturing_capacity["Global Capacity (GWh)"],
        name="Nameplate Capacity",
        marker_color=COLORS["accent_blue"],
        opacity=0.4,
    ))
    fig.add_trace(go.Bar(
        x=manufacturing_capacity["Year"],
        y=manufacturing_capacity["Actual Production (GWh)"],
        name="Actual Production",
        marker_color=COLORS["accent_blue"],
        opacity=0.85,
    ))
    fig.add_trace(go.Scatter(
        x=manufacturing_capacity["Year"],
        y=manufacturing_capacity["Utilization Rate (%)"],
        name="Utilization %",
        mode="lines+markers",
        line=dict(color=COLORS["accent_amber"], width=2.5),
        marker=dict(size=7),
        yaxis="y2",
    ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Global Cell Manufacturing Capacity vs Production", font=dict(size=15)),
        yaxis=dict(title="GWh"),
        yaxis2=dict(
            title="Utilization %",
            overlaying="y",
            side="right",
            range=[0, 100],
            gridcolor="rgba(0,0,0,0)",
        ),
        barmode="overlay",
    )
    return fig


def create_manufacturing_region_chart():
    df = manufacturing_by_region[manufacturing_by_region["Year"] == 2024]
    fig = go.Figure(go.Pie(
        labels=df["Region"],
        values=df["Capacity Share (%)"],
        marker=dict(colors=CHART_COLORS),
        hole=0.55,
        textinfo="label+percent",
        textfont=dict(size=12, color=COLORS["text"]),
    ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Manufacturing Capacity by Region (2024)", font=dict(size=15)),
        showlegend=False,
    )
    return fig


def create_raw_materials_chart():
    fig = go.Figure()
    for material, color in [
        ("Lithium Carbonate", COLORS["accent_green"]),
        ("Cobalt", COLORS["accent_blue"]),
        ("Nickel", COLORS["accent_amber"]),
    ]:
        df = raw_materials_combined[raw_materials_combined["Material"] == material]
        fig.add_trace(go.Scatter(
            x=df["Year"],
            y=df["Price ($/tonne)"],
            name=material,
            mode="lines+markers",
            line=dict(width=2.5, color=color),
            marker=dict(size=6),
        ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Raw Material Price Trends ($/tonne)", font=dict(size=15)),
        yaxis=dict(title="$/tonne"),
    )
    return fig


def create_investment_chart():
    fig = go.Figure()
    for col, color in [
        ("Manufacturing ($B)", COLORS["accent_blue"]),
        ("Mining & Materials ($B)", COLORS["accent_amber"]),
        ("BESS Projects ($B)", COLORS["accent_green"]),
        ("R&D & Other ($B)", COLORS["accent_purple"]),
    ]:
        fig.add_trace(go.Bar(
            x=investment_data["Year"],
            y=investment_data[col],
            name=col.replace(" ($B)", ""),
            marker_color=color,
            opacity=0.85,
        ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Battery Industry Investment ($B)", font=dict(size=15)),
        yaxis=dict(title="$ Billion"),
        barmode="stack",
    )
    return fig


def create_demand_chart():
    fig = px.area(
        demand_by_application,
        x="Year",
        y="Demand (GWh)",
        color="Application",
        color_discrete_sequence=[COLORS["accent_blue"], COLORS["accent_green"], COLORS["accent_amber"]],
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Battery Demand by Application (GWh)", font=dict(size=15)),
        yaxis=dict(title="GWh"),
    )
    return fig


def create_bess_system_cost_chart():
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=bess_system_cost["Year"],
        y=bess_system_cost["System Cost ($/kWh)"],
        mode="lines+markers",
        line=dict(color=COLORS["accent_cyan"], width=3),
        marker=dict(size=8),
        fill="tozeroy",
        fillcolor="rgba(6, 182, 212, 0.1)",
        name="System Cost",
    ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="Utility-Scale BESS System Cost ($/kWh, 4hr)", font=dict(size=15)),
        yaxis=dict(title="$/kWh installed"),
    )
    return fig


def create_bess_cost_breakdown_chart():
    fig = go.Figure(go.Pie(
        labels=bess_cost_breakdown["Component"],
        values=bess_cost_breakdown["Cost ($/kWh)"],
        marker=dict(colors=CHART_COLORS),
        hole=0.55,
        textinfo="label+percent",
        textfont=dict(size=11, color=COLORS["text"]),
    ))
    apply_theme(fig)
    fig.update_layout(
        title=dict(text="BESS System Cost Breakdown (2024)", font=dict(size=15)),
        showlegend=False,
    )
    return fig


# =============================================================================
# WATCHPOINT CARDS
# =============================================================================
def impact_badge(impact):
    color_map = {
        "High": COLORS["accent_red"],
        "Medium": COLORS["accent_amber"],
        "Low": COLORS["accent_green"],
    }
    return html.Span(
        impact,
        style={
            "backgroundColor": f"{color_map.get(impact, COLORS['accent_blue'])}22",
            "color": color_map.get(impact, COLORS["accent_blue"]),
            "padding": "2px 10px",
            "borderRadius": "12px",
            "fontSize": "11px",
            "fontWeight": "600",
            "textTransform": "uppercase",
        },
    )


def category_badge(cat):
    color_map = {
        "Technology": COLORS["accent_blue"],
        "Market": COLORS["accent_green"],
        "Pricing": COLORS["accent_cyan"],
        "Supply Chain": COLORS["accent_amber"],
        "Policy": COLORS["accent_purple"],
        "Risk": COLORS["accent_red"],
    }
    return html.Span(
        cat,
        style={
            "backgroundColor": f"{color_map.get(cat, COLORS['accent_blue'])}22",
            "color": color_map.get(cat, COLORS["accent_blue"]),
            "padding": "2px 10px",
            "borderRadius": "12px",
            "fontSize": "11px",
            "fontWeight": "600",
        },
    )


def watchpoint_card(wp):
    return html.Div(
        [
            html.Div(
                [category_badge(wp["category"]), impact_badge(wp["impact"])],
                style={"display": "flex", "gap": "8px", "marginBottom": "8px"},
            ),
            html.Div(
                wp["title"],
                style={
                    "color": COLORS["text"],
                    "fontSize": "15px",
                    "fontWeight": "600",
                    "marginBottom": "6px",
                },
            ),
            html.Div(
                wp["description"],
                style={
                    "color": COLORS["text_muted"],
                    "fontSize": "13px",
                    "lineHeight": "1.5",
                },
            ),
        ],
        style={
            **card_style(),
            "borderLeft": f"3px solid {COLORS['accent_blue']}",
        },
    )


# =============================================================================
# APP LAYOUT
# =============================================================================
app = dash.Dash(
    __name__,
    title="BESS Market Intelligence",
    suppress_callback_exceptions=True,
)

app.layout = html.Div(
    [
        # Header
        html.Div(
            [
                html.Div(
                    [
                        html.H1(
                            "BESS Market Intelligence",
                            style={
                                "fontSize": "24px",
                                "fontWeight": "700",
                                "color": COLORS["text"],
                                "margin": "0",
                            },
                        ),
                        html.Div(
                            "Battery Energy Storage Systems \u2022 Global Market Dashboard",
                            style={
                                "color": COLORS["text_muted"],
                                "fontSize": "13px",
                                "marginTop": "4px",
                            },
                        ),
                    ],
                ),
                html.Div(
                    "Source: Volta Foundation Battery Reports 2021\u20132024",
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
                "borderBottom": f"1px solid {COLORS['card_border']}",
                "marginBottom": "20px",
            },
        ),
        # Navigation tabs
        dcc.Tabs(
            id="main-tabs",
            value="overview",
            children=[
                dcc.Tab(label="Overview", value="overview"),
                dcc.Tab(label="BESS Deployments", value="deployments"),
                dcc.Tab(label="Pricing & Costs", value="pricing"),
                dcc.Tab(label="Technology & Chemistry", value="technology"),
                dcc.Tab(label="Supply Chain", value="supply_chain"),
                dcc.Tab(label="Watchpoints", value="watchpoints"),
            ],
            style={"marginBottom": "20px", "padding": "0 24px"},
            colors={
                "border": COLORS["card_border"],
                "primary": COLORS["accent_blue"],
                "background": COLORS["card"],
            },
        ),
        # Tab content
        html.Div(id="tab-content", style={"padding": "0 24px 24px"}),
    ],
    style={
        "backgroundColor": COLORS["bg"],
        "minHeight": "100vh",
        "fontFamily": "Inter, system-ui, -apple-system, sans-serif",
    },
)


# =============================================================================
# TAB CONTENT CALLBACK
# =============================================================================
@app.callback(Output("tab-content", "children"), Input("main-tabs", "value"))
def render_tab(tab):
    if tab == "overview":
        return render_overview()
    elif tab == "deployments":
        return render_deployments()
    elif tab == "pricing":
        return render_pricing()
    elif tab == "technology":
        return render_technology()
    elif tab == "supply_chain":
        return render_supply_chain()
    elif tab == "watchpoints":
        return render_watchpoints()
    return html.Div("Select a tab")


def render_overview():
    return html.Div([
        # KPI row
        html.Div(
            [
                html.Div(kpi_card("BESS Installations 2024", "75 GWh", "+63% YoY", True), style={"flex": "1"}),
                html.Div(kpi_card("Battery Pack Price", "$115/kWh", "-17% YoY", True), style={"flex": "1"}),
                html.Div(kpi_card("BESS System Cost", "$190/kWh", "-27% YoY", True), style={"flex": "1"}),
                html.Div(kpi_card("LFP Market Share", "58%", "+6pp YoY", True), style={"flex": "1"}),
                html.Div(kpi_card("Industry Investment", "$150B", "+11% YoY", True), style={"flex": "1"}),
            ],
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        ),
        # Charts row 1
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_bess_deployment_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
                html.Div(
                    dcc.Graph(figure=create_price_trend_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
        # Charts row 2
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_demand_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
                html.Div(
                    dcc.Graph(figure=create_investment_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
        # Key developments timeline
        html.Div(
            [
                html.H3(
                    "Key Developments Timeline",
                    style={"color": COLORS["text"], "fontSize": "16px", "fontWeight": "600", "marginBottom": "16px"},
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            str(row["Year"]),
                                            style={
                                                "color": COLORS["accent_blue"],
                                                "fontWeight": "700",
                                                "fontSize": "14px",
                                                "minWidth": "40px",
                                            },
                                        ),
                                        category_badge(row["Category"]),
                                    ],
                                    style={"display": "flex", "alignItems": "center", "gap": "10px", "marginBottom": "4px"},
                                ),
                                html.Div(
                                    row["Event"],
                                    style={"color": COLORS["text"], "fontSize": "14px", "paddingLeft": "50px"},
                                ),
                            ],
                            style={"padding": "10px 0", "borderBottom": f"1px solid {COLORS['card_border']}"},
                        )
                        for _, row in key_developments_timeline.iterrows()
                    ],
                ),
            ],
            style=card_style(),
        ),
    ])


def render_deployments():
    return html.Div([
        # KPI row
        html.Div(
            [
                html.Div(kpi_card("2024 Annual Installations", "75 GWh", "+63% YoY", True), style={"flex": "1"}),
                html.Div(kpi_card("Cumulative Global Capacity", "179.5 GWh", "", True), style={"flex": "1"}),
                html.Div(kpi_card("Power Capacity 2024", "32 GW", "+60% YoY", True), style={"flex": "1"}),
                html.Div(kpi_card("China Share of 2024", "53%", "", True), style={"flex": "1"}),
            ],
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_bess_deployment_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
                html.Div(
                    dcc.Graph(figure=create_bess_by_region_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
        html.Div(
            dcc.Graph(figure=create_demand_chart(), config={"displayModeBar": False}),
            style=card_style(),
        ),
    ])


def render_pricing():
    return html.Div([
        html.Div(
            [
                html.Div(kpi_card("Pack Price 2024", "$115/kWh", "-17% vs 2023", True), style={"flex": "1"}),
                html.Div(kpi_card("Cell Price 2024", "$76/kWh", "-18% vs 2023", True), style={"flex": "1"}),
                html.Div(kpi_card("LFP Pack 2024", "$89/kWh", "Lowest ever", True), style={"flex": "1"}),
                html.Div(kpi_card("BESS System 2024", "$190/kWh", "-27% vs 2023", True), style={"flex": "1"}),
            ],
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_price_trend_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
                html.Div(
                    dcc.Graph(figure=create_chemistry_by_price_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_bess_system_cost_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
                html.Div(
                    dcc.Graph(figure=create_bess_cost_breakdown_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
    ])


def render_technology():
    return html.Div([
        html.Div(
            [
                html.Div(kpi_card("LFP Global Share", "58%", "+6pp vs 2023", True), style={"flex": "1"}),
                html.Div(kpi_card("LFP in BESS", "92%", "Dominant", True), style={"flex": "1"}),
                html.Div(kpi_card("NMC Global Share", "28%", "-4pp vs 2023", False), style={"flex": "1"}),
                html.Div(kpi_card("Emerging: Sodium-Ion", "Mass production", "2024 start", True), style={"flex": "1"}),
            ],
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_chemistry_mix_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
                html.Div(
                    dcc.Graph(figure=create_bess_chemistry_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
        # Technology insights
        html.Div(
            [
                html.H3(
                    "Technology Outlook",
                    style={"color": COLORS["text"], "fontSize": "16px", "fontWeight": "600", "marginBottom": "16px"},
                ),
                html.Div([
                    html.Div(
                        [
                            html.Div("\u26A1 LFP Dominance", style={"color": COLORS["accent_green"], "fontWeight": "600", "marginBottom": "4px"}),
                            html.Div(
                                "LFP has become the default chemistry for grid-scale BESS, with >90% market share. "
                                "Advantages: lower cost, longer cycle life, no cobalt/nickel dependency, superior thermal safety.",
                                style={"color": COLORS["text_muted"], "fontSize": "13px", "lineHeight": "1.5"},
                            ),
                        ],
                        style={"padding": "12px 0", "borderBottom": f"1px solid {COLORS['card_border']}"},
                    ),
                    html.Div(
                        [
                            html.Div("\u26A1 Sodium-Ion Emergence", style={"color": COLORS["accent_cyan"], "fontWeight": "600", "marginBottom": "4px"}),
                            html.Div(
                                "Sodium-ion batteries entered mass production in 2023-2024 (CATL, BYD, HiNa). "
                                "~30% cheaper than LFP but lower energy density. Target: short-duration grid storage, cold climates.",
                                style={"color": COLORS["text_muted"], "fontSize": "13px", "lineHeight": "1.5"},
                            ),
                        ],
                        style={"padding": "12px 0", "borderBottom": f"1px solid {COLORS['card_border']}"},
                    ),
                    html.Div(
                        [
                            html.Div("\u26A1 Long-Duration Storage (LDES)", style={"color": COLORS["accent_amber"], "fontWeight": "600", "marginBottom": "4px"}),
                            html.Div(
                                "Iron-air (Form Energy), zinc-based, vanadium flow batteries gaining traction for 8-100+ hour storage. "
                                "Targeting $20/kWh for seasonal storage. Still pre-commercial at scale.",
                                style={"color": COLORS["text_muted"], "fontSize": "13px", "lineHeight": "1.5"},
                            ),
                        ],
                        style={"padding": "12px 0"},
                    ),
                ]),
            ],
            style=card_style(),
        ),
    ])


def render_supply_chain():
    return html.Div([
        html.Div(
            [
                html.Div(kpi_card("Cell Mfg Capacity", "2.8 TWh", "+56% vs 2023", True), style={"flex": "1"}),
                html.Div(kpi_card("Utilization Rate", "46%", "Overcapacity", False), style={"flex": "1"}),
                html.Div(kpi_card("Lithium Price", "$11K/t", "-80% from peak", True), style={"flex": "1"}),
                html.Div(kpi_card("China Mfg Share", "80%", "Concentration risk", False), style={"flex": "1"}),
            ],
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        ),
        html.Div(
            [
                html.Div(
                    dcc.Graph(figure=create_manufacturing_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "2"},
                ),
                html.Div(
                    dcc.Graph(figure=create_manufacturing_region_chart(), config={"displayModeBar": False}),
                    style={**card_style(), "flex": "1"},
                ),
            ],
            style={"display": "flex", "gap": "16px"},
        ),
        html.Div(
            dcc.Graph(figure=create_raw_materials_chart(), config={"displayModeBar": False}),
            style=card_style(),
        ),
    ])


def render_watchpoints():
    # Group by category
    categories = {}
    for wp in key_watchpoints:
        cat = wp["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(wp)

    high_impact = [wp for wp in key_watchpoints if wp["impact"] == "High"]
    medium_impact = [wp for wp in key_watchpoints if wp["impact"] == "Medium"]
    low_impact = [wp for wp in key_watchpoints if wp["impact"] == "Low"]

    return html.Div([
        html.Div(
            [
                html.Div(kpi_card("High Impact", str(len(high_impact)), "items", False), style={"flex": "1"}),
                html.Div(kpi_card("Medium Impact", str(len(medium_impact)), "items", True), style={"flex": "1"}),
                html.Div(kpi_card("Low Impact", str(len(low_impact)), "items", True), style={"flex": "1"}),
                html.Div(kpi_card("Total Watchpoints", str(len(key_watchpoints)), "", True), style={"flex": "1"}),
            ],
            style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        ),
        # High impact section
        html.H3(
            "High Impact",
            style={"color": COLORS["accent_red"], "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px"},
        ),
        html.Div(
            [watchpoint_card(wp) for wp in high_impact],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px", "marginBottom": "20px"},
        ),
        # Medium impact section
        html.H3(
            "Medium Impact",
            style={"color": COLORS["accent_amber"], "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px"},
        ),
        html.Div(
            [watchpoint_card(wp) for wp in medium_impact],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px", "marginBottom": "20px"},
        ),
        # Low impact section
        html.H3(
            "Low Impact",
            style={"color": COLORS["accent_green"], "fontSize": "16px", "fontWeight": "600", "marginBottom": "12px"},
        ),
        html.Div(
            [watchpoint_card(wp) for wp in low_impact],
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"},
        ),
    ])


# =============================================================================
# RUN
# =============================================================================
if __name__ == "__main__":
    print("\n  BESS Market Intelligence Dashboard")
    print("  http://localhost:8050\n")
    app.run(debug=True, port=8050)
