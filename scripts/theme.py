"""Paleta e helpers compartilhados entre os geradores de SVG."""

BG = "#0d1117"
PANEL = "#161b22"
BORDER = "#30363d"
FG = "#c9d1d9"
MUTED = "#8b949e"
ACCENT = "#2e9ef7"
ACCENT_2 = "#79c0ff"
GREEN = "#3fb950"
YELLOW = "#d29922"
PINK = "#f778ba"
PURPLE = "#bc8cff"
RED = "#ff7b72"

# none -> mais intenso (nível 5 é o "neon")
HEAT = ["#161b22", "#0c2d48", "#0f4c81", "#1f6feb", "#2e9ef7", "#79c0ff"]

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def window_chrome(width, height, title):
    """Moldura de terminal (fundo, borda, barra de título com os três botões)."""
    return f"""
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{BG}" stroke="{BORDER}"/>
  <path d="M0.5 32 V10.5 a10 10 0 0 1 10 -10 H{width - 10.5} a10 10 0 0 1 10 10 V32 Z" fill="{PANEL}"/>
  <line x1="0.5" y1="32" x2="{width - 0.5}" y2="32" stroke="{BORDER}"/>
  <circle cx="18" cy="16" r="5.5" fill="#ff5f56"/>
  <circle cx="36" cy="16" r="5.5" fill="#ffbd2e"/>
  <circle cx="54" cy="16" r="5.5" fill="#27c93f"/>
  <text x="{width / 2}" y="20.5" text-anchor="middle" fill="{MUTED}" font-size="12">{esc(title)}</text>"""
