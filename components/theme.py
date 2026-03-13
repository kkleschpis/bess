"""
Dark theme styling shared across country dashboards.
Extracted from the Modo Energy-inspired theme in the main BESS app.
"""

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
    "#3b82f6",
    "#10b981",
    "#f59e0b",
    "#ef4444",
    "#8b5cf6",
    "#06b6d4",
    "#ec4899",
    "#84cc16",
]

# Colors for generation sources (Germany + Spain)
SOURCE_COLORS = {
    # Shared / Germany
    "solar": "#f59e0b",
    "wind_onshore": "#3b82f6",
    "wind_offshore": "#06b6d4",
    "gas": "#ef4444",
    "hard_coal": "#6b7280",
    "lignite": "#92400e",
    "hydro": "#2563eb",
    "biomass": "#10b981",
    "nuclear": "#8b5cf6",
    "oil": "#991b1b",
    "pumped_storage": "#1d4ed8",
    "geothermal": "#dc2626",
    "other": "#9ca3af",
    # Spain-specific
    "combined_cycle": "#ef4444",
    "coal": "#6b7280",
    "cogeneration": "#b45309",
    "waste": "#9ca3af",
    "hydro_pumped": "#1d4ed8",
    "wind": "#3b82f6",
    "solar_pv": "#f59e0b",
    "solar_thermal": "#d97706",
}

# Human-readable labels for sources (Germany + Spain)
SOURCE_LABELS = {
    # Shared / Germany
    "solar": "Solar",
    "wind_onshore": "Wind Onshore",
    "wind_offshore": "Wind Offshore",
    "gas": "Gas",
    "hard_coal": "Hard Coal",
    "lignite": "Lignite",
    "hydro": "Hydro",
    "biomass": "Biomass",
    "nuclear": "Nuclear",
    "oil": "Oil",
    "pumped_storage": "Pumped Storage",
    "geothermal": "Geothermal",
    "other": "Other",
    # Spain-specific
    "combined_cycle": "Combined Cycle (Gas)",
    "coal": "Coal",
    "cogeneration": "Cogeneration",
    "waste": "Waste",
    "hydro_pumped": "Pumped Hydro",
    "wind": "Wind",
    "solar_pv": "Solar PV",
    "solar_thermal": "Solar Thermal",
}

PLOT_LAYOUT = dict(
    paper_bgcolor=COLORS["card"],
    plot_bgcolor=COLORS["card"],
    font=dict(
        color=COLORS["text"],
        family="Inter, system-ui, sans-serif",
        size=12,
    ),
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

AXIS_STYLE = dict(
    gridcolor=COLORS["grid"],
    zerolinecolor=COLORS["grid"],
)


def apply_theme(fig):
    """Apply common dark theme to a plotly figure."""
    fig.update_layout(**PLOT_LAYOUT)
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def card_style(height=None):
    """Return a card container style dict."""
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
