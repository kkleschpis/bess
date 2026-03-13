"""Reusable KPI card components."""

from dash import html

from components.theme import COLORS, card_style


def kpi_card(title, value, subtitle=None, color=None):
    """Create a KPI display card.

    Args:
        title: KPI label text (uppercase).
        value: Main display value.
        subtitle: Optional secondary text below value.
        color: Optional accent color for the value text.
    """
    value_color = color or COLORS["text"]

    children = [
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
            value,
            style={
                "color": value_color,
                "fontSize": "28px",
                "fontWeight": "700",
            },
        ),
    ]

    if subtitle:
        children.append(
            html.Div(
                subtitle,
                style={
                    "color": COLORS["text_muted"],
                    "fontSize": "12px",
                    "marginTop": "4px",
                },
            )
        )

    return html.Div(children, style=card_style())
