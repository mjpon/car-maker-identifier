"""Visual design for the app: Swiss railway (SBB / ÖBB) timetable language.

White paper, one signal red, charcoal rules, flat panels, large tabular numerals.
Everything visual lives here so app.py can stay about data and layout.
"""

from html import escape

import streamlit as st

# Colour tokens. Red is the signal colour, blue is reserved for a second data series.
RED = "#E2001A"
RED_DARK = "#B30015"
BLUE = "#0C4DA2"
INK = "#2D2D2D"
MUTED = "#686868"
BAR = "#6B6B6B"
LINE = "#D5D5D5"
PANEL = "#F4F4F4"
GRAY_MID = "#9A9A9A"
GRAY_LIGHT = "#DCDCDC"

FONT_STACK = '"Hanken Grotesk", "Helvetica Neue", Helvetica, Arial, sans-serif'

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&display=swap');

:root {
  --red: %(red)s;
  --red-dark: %(red_dark)s;
  --blue: %(blue)s;
  --ink: %(ink)s;
  --muted: %(muted)s;
  --line: %(line)s;
  --panel: %(panel)s;
  --font: %(font)s;
}

/* Base */
.stApp,
.stApp button,
.stApp input,
.stApp textarea,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stWidgetLabel"] {
  font-family: var(--font) !important;
}
.stApp { color: var(--ink); background: #fff; }
.stApp * { font-variant-numeric: tabular-nums; }

[data-testid="stHeader"] {
  background: #fff;
  border-top: 6px solid var(--red);
}
.block-container {
  max-width: 1200px;
  padding: 5rem 24px 4rem;
}
@media (max-width: 640px) {
  .block-container { padding: 4.5rem 16px 3rem; }
}

*:focus-visible {
  outline: 2px solid var(--red) !important;
  outline-offset: 2px;
}

/* Masthead */
.sbb-masthead {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
  flex-wrap: wrap;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}
.sbb-wordmark { font-size: 18px; font-weight: 700; letter-spacing: -0.01em; }
.sbb-source { font-size: 14px; color: var(--muted); }
.sbb-source a { color: var(--muted); text-underline-offset: 3px; }

.sbb-title {
  font-size: clamp(34px, 5vw, 56px);
  line-height: 1.05;
  font-weight: 800;
  letter-spacing: -0.03em;
  margin: 40px 0 16px;
  padding: 0;
}
.sbb-intro {
  max-width: 62ch;
  font-size: 18px;
  line-height: 1.5;
  color: var(--ink);
  margin: 0 0 32px;
}

/* Filter panel */
.st-key-filters {
  background: var(--panel);
  padding: 20px 20px 8px;
  margin-bottom: 24px;
  border-radius: 2px;
}
.stApp [data-testid="stWidgetLabel"] p { font-size: 14px; font-weight: 600; }
.stApp [data-testid="stMultiSelect"] [role="group"],
.stApp [data-testid="stSelectbox"] [role="group"],
.stApp [data-testid="stTextInputRootElement"] {
  background: #fff;
  border: 1px solid #767676;
  border-radius: 2px;
  min-height: 48px;
}
.stApp [data-tag] {
  background: var(--ink) !important;
  color: #fff !important;
  border-radius: 2px;
  font-weight: 600;
}
.stApp [data-tag] * { color: #fff !important; }

/* Departure board: the headline numbers */
.sbb-board {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  border-top: 3px solid var(--ink);
  border-bottom: 1px solid var(--line);
  margin: 8px 0 40px;
}
.sbb-cell { padding: 16px 20px 18px 0; }
.sbb-cell + .sbb-cell { padding-left: 20px; border-left: 1px solid var(--line); }
.sbb-num {
  font-size: clamp(36px, 5vw, 60px);
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.03em;
}
.sbb-num.is-signal { color: var(--red); }
.sbb-label { font-size: 14px; color: var(--muted); margin-top: 8px; line-height: 1.3; }
@media (max-width: 720px) {
  .sbb-board { grid-template-columns: repeat(2, 1fr); }
  .sbb-cell:nth-child(3) { padding-left: 0; border-left: 0; }
  .sbb-cell:nth-child(n+3) { border-top: 1px solid var(--line); }
}

/* Tabs */
.stApp [role="tablist"] { gap: 28px; border-bottom: 1px solid var(--line); }
.stApp [data-testid="stTab"] { padding: 12px 0; background: transparent; }
.stApp [data-testid="stTab"] p { font-size: 17px !important; font-weight: 600; color: var(--muted) !important; }
.stApp [data-testid="stTab"][aria-selected="true"] p,
.stApp [data-testid="stTab"]:hover p { color: var(--ink) !important; }
.stApp [data-testid="stTab"][aria-selected="true"] { box-shadow: inset 0 -4px 0 var(--red); }

/* Section and chart headings */
.sbb-h2 { font-size: 28px; line-height: 1.15; font-weight: 700; letter-spacing: -0.02em; margin: 24px 0 4px; padding: 0; }
.sbb-h3 { font-size: 18px; line-height: 1.25; font-weight: 700; margin: 16px 0 2px; padding: 0; }
.sbb-note { font-size: 14px; line-height: 1.45; color: var(--muted); max-width: 70ch; margin: 0 0 12px; }

/* Notice (alert strip, like a service message on a timetable) */
.sbb-notice {
  border-left: 4px solid var(--red);
  background: var(--panel);
  padding: 12px 16px;
  font-size: 15px;
  line-height: 1.45;
  margin: 8px 0 16px;
}

/* Legend for charts whose series are colours */
.sbb-legend { display: flex; flex-wrap: wrap; gap: 8px 24px; margin: 4px 0 8px; font-size: 14px; }
.sbb-legend span { display: inline-flex; align-items: center; gap: 8px; }
.sbb-legend i { width: 12px; height: 12px; display: inline-block; }

/* Buttons */
.stApp [data-testid="stDownloadButton"] button {
  background: var(--red);
  color: #fff;
  border: 0;
  border-radius: 2px;
  min-height: 48px;
  padding: 0 24px;
}
.stApp [data-testid="stDownloadButton"] button p { color: #fff; font-weight: 600; font-size: 16px; }
.stApp [data-testid="stDownloadButton"] button:hover { background: var(--red-dark); }

/* Footer */
.sbb-footer {
  margin-top: 56px;
  padding-top: 16px;
  border-top: 1px solid var(--line);
  font-size: 14px;
  line-height: 1.5;
  color: var(--muted);
}
.sbb-footer a { color: var(--ink); text-underline-offset: 3px; }
.sbb-footer p { margin: 0 0 8px; max-width: 80ch; }
""" % {
    "red": RED,
    "red_dark": RED_DARK,
    "blue": BLUE,
    "ink": INK,
    "muted": MUTED,
    "line": LINE,
    "panel": PANEL,
    "font": FONT_STACK,
}


def apply() -> None:
    """Inject the global stylesheet. Call once, right after set_page_config."""
    st.html(f"<style>{_CSS}</style>")


def masthead(source_text: str) -> None:
    st.html(
        '<div class="sbb-masthead">'
        '<span class="sbb-wordmark">Vehicle parts origin</span>'
        f'<span class="sbb-source">{escape(source_text)}</span>'
        "</div>"
    )


def title(text: str, intro: str) -> None:
    st.html(f'<h1 class="sbb-title">{escape(text)}</h1><p class="sbb-intro">{escape(intro)}</p>')


def board(cells: list[tuple[str, str, bool]]) -> None:
    """Large-numeral summary row. Each cell is (value, label, is_signal)."""
    items = "".join(
        f'<div class="sbb-cell"><div class="sbb-num{" is-signal" if signal else ""}">{escape(value)}</div>'
        f'<div class="sbb-label">{escape(label)}</div></div>'
        for value, label, signal in cells
    )
    st.html(f'<div class="sbb-board">{items}</div>')


def heading(text: str, note: str | None = None, level: int = 2) -> None:
    tag = "sbb-h2" if level == 2 else "sbb-h3"
    html = f'<h{level} class="{tag}">{escape(text)}</h{level}>'
    if note:
        html += f'<p class="sbb-note">{escape(note)}</p>'
    st.html(html)


def notice(text: str) -> None:
    st.html(f'<div class="sbb-notice">{escape(text)}</div>')


def footer(html_body: str) -> None:
    """Footer copy is written by us (not user input), so it may contain links."""
    st.html(f'<div class="sbb-footer">{html_body}</div>')


def legend(items: list[tuple[str, str]]) -> None:
    """Colour key above a chart. Each item is (label, hex colour)."""
    keys = "".join(
        f'<span><i style="background:{color}"></i>{escape(label)}</span>' for label, color in items
    )
    st.html(f'<div class="sbb-legend">{keys}</div>')
