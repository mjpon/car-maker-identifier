"""Plotly chart builders in the SBB / ÖBB look: flat marks, light rules, direct labels."""

from collections.abc import Sequence

import plotly.graph_objects as go

from theme import BAR, BLUE, FONT_STACK, GRAY_LIGHT, GRAY_MID, INK, LINE, MUTED, RED

ROW_HEIGHT = 30  # px per bar in a ranking, so every ranking has the same rhythm

PLOTLY_CONFIG = {"displayModeBar": False}


def _base(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=8, t=8, b=8),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(family=FONT_STACK, size=14, color=INK),
        hoverlabel=dict(
            bgcolor=INK,
            bordercolor=INK,
            font=dict(family=FONT_STACK, size=14, color="#FFFFFF"),
        ),
        showlegend=False,
    )
    return fig


def ranking(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    unit: str,
    decimals: int = 0,
    suffix: str = "",
) -> go.Figure:
    """Horizontal bars, largest first. The leader is red, the rest are gray.

    Values are printed at the bar ends instead of on an axis, like a timetable column.
    """
    labels, values = list(labels), list(values)
    colors = [RED] + [BAR] * (len(values) - 1)
    text = [f"{v:,.{decimals}f}{suffix}" for v in values]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=colors),
            text=text,
            textposition="outside",
            textfont=dict(size=14, color=INK),
            cliponaxis=False,
            hovertemplate=f"<b>%{{y}}</b><br>%{{text}} {unit}<extra></extra>",
        )
    )
    top = max(values) if values else 1
    fig.update_xaxes(visible=False, range=[0, top * 1.14])
    fig.update_yaxes(
        autorange="reversed",
        automargin=True,
        ticks="",
        showline=False,
        showgrid=False,
        tickfont=dict(size=14, color=INK),
    )
    fig.update_layout(bargap=0.3)
    return _base(fig, ROW_HEIGHT * len(values) + 24)


def columns(
    labels: Sequence[str],
    values: Sequence[float],
    *,
    unit: str,
    height: int = 300,
) -> go.Figure:
    """Vertical bars for an ordered scale (for example content bands). One colour, red on the peak."""
    labels, values = list(labels), list(values)
    peak = max(range(len(values)), key=values.__getitem__) if values else 0
    colors = [RED if i == peak else BAR for i in range(len(values))]

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors),
            text=[f"{v:,.0f}" for v in values],
            textposition="outside",
            textfont=dict(size=14, color=INK),
            cliponaxis=False,
            hovertemplate=f"<b>%{{x}}</b><br>%{{text}} {unit}<extra></extra>",
        )
    )
    fig.update_xaxes(ticks="", showline=True, linecolor=INK, tickfont=dict(size=14, color=INK))
    fig.update_yaxes(visible=False, range=[0, (max(values) if values else 1) * 1.15])
    fig.update_layout(bargap=0.35)
    return _base(fig, height)


def trend(years: Sequence[int], counts: Sequence[int], *, unit: str) -> go.Figure:
    """One red line, one marker per model year."""
    years, counts = list(years), list(counts)
    fig = go.Figure(
        go.Scatter(
            x=years,
            y=counts,
            mode="lines+markers",
            line=dict(color=RED, width=3),
            marker=dict(size=10, color=RED, line=dict(color="#FFFFFF", width=2)),
            hovertemplate=f"<b>%{{x}}</b><br>%{{y:,}} {unit}<extra></extra>",
        )
    )
    fig.update_xaxes(
        tickmode="array",
        tickvals=years,
        ticktext=[str(y) for y in years],
        showgrid=False,
        ticks="",
        showline=True,
        linecolor=INK,
        tickfont=dict(size=14, color=INK),
    )
    fig.update_yaxes(
        rangemode="tozero",
        gridcolor=LINE,
        gridwidth=1,
        zeroline=False,
        ticks="",
        showline=False,
        tickfont=dict(size=13, color=MUTED),
    )
    return _base(fig, 320)


def composition_segments(
    us_canada: float,
    foreign_main: float,
    foreign_second: float,
    other: float,
    *,
    main_country: str,
) -> list[tuple[str, float, str, str]]:
    """(name, percent, fill colour, label colour) for each part of a vehicle's content."""
    return [
        ("US and Canada", us_canada, RED, "#FFFFFF"),
        (f"Largest foreign source ({main_country})", foreign_main, BLUE, "#FFFFFF"),
        ("Second foreign source", foreign_second, GRAY_MID, INK),
        ("Other or not itemized", other, GRAY_LIGHT, INK),
    ]


def composition(segments: list[tuple[str, float, str, str]]) -> go.Figure:
    """One 100% bar showing where the average vehicle's content comes from.

    The legend is drawn in HTML above the chart (see theme.legend) so it never overlaps the bar.
    """
    fig = go.Figure()
    for name, value, color, text_color in segments:
        fig.add_trace(
            go.Bar(
                y=[""],
                x=[value],
                name=name,
                orientation="h",
                marker=dict(color=color, line=dict(color="#FFFFFF", width=2)),
                text=[f"{value:.0f}%" if value >= 4 else ""],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=16, color=text_color),
                hovertemplate=f"<b>{name}</b><br>{value:.1f}% of parts content<extra></extra>",
            )
        )
    fig.update_layout(barmode="stack", bargap=0)
    fig.update_xaxes(
        range=[0, 100],
        tickvals=[0, 25, 50, 75, 100],
        ticktext=["0%", "25%", "50%", "75%", "100%"],
        showgrid=False,
        ticks="",
        showline=False,
        tickfont=dict(size=13, color=MUTED),
    )
    fig.update_yaxes(visible=False)
    _base(fig, 110)
    fig.update_layout(margin=dict(l=24, r=24, t=4, b=8))
    return fig
