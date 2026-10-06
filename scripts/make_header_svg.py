"""Gera o banner do topo (assets/header.svg): nome em gradiente + frases digitadas em loop."""

import os
from pathlib import Path

from theme import ACCENT, ACCENT_2, BORDER, FG, GREEN, MONO, MUTED, PURPLE, esc

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "header.svg"
STATIC = os.environ.get("STATIC") == "1"

W, H = 860, 170
PHRASES = [
    "Desenvolvedor Full Stack",
    "Next.js · Nest.js · TypeScript",
    "Docker & MySQL no dia a dia",
    "Transformo café em deploy ☕",
]
SLOT = 3.6  # segundos por frase
CHAR_W = 10.2  # 17px monospace


def main():
    cycle = SLOT * len(PHRASES)
    t_in, t_hold, t_out = (p / cycle * 100 for p in (1.1, 2.9, 3.3))
    phrases = []
    for i, text in enumerate(PHRASES):
        anim = "" if STATIC else f' style="animation-delay:{i * SLOT:.2f}s"'
        visible = "" if (not STATIC or i == 0) else ' visibility="hidden"'
        phrases.append(
            f'<text class="p" x="{W / 2}" y="128" text-anchor="middle"{anim}{visible}>'
            f'<tspan fill="{GREEN}">❯ </tspan>{esc(text)}</text>'
        )

    out = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}">
  <title>Tiago Rafael — Desenvolvedor Full Stack</title>
  <defs>
    <linearGradient id="name" x1="0" x2="1" spreadMethod="reflect">
      <stop offset="0" stop-color="{ACCENT}"/>
      <stop offset=".5" stop-color="{ACCENT_2}"/>
      <stop offset="1" stop-color="{PURPLE}"/>
      {"" if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" values="-1 0; 1 0; -1 0" dur="8s" repeatCount="indefinite"/>'}
    </linearGradient>
    <linearGradient id="glow" x1="0" x2="1">
      <stop offset="0" stop-color="{ACCENT}" stop-opacity="0"/>
      <stop offset=".5" stop-color="{ACCENT}" stop-opacity=".9"/>
      <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <pattern id="dots" width="18" height="18" patternUnits="userSpaceOnUse">
      <circle cx="1.5" cy="1.5" r="1" fill="{BORDER}"/>
    </pattern>
  </defs>
  <style>
    .hi {{ fill: {MUTED}; font-size: 15px; }}
    .name {{ font-size: 46px; font-weight: 800; letter-spacing: -1px; }}
    .p {{ fill: {FG}; font-size: 17px; }}
    {"" if STATIC else f'''
    .hi, .name {{ opacity: 0; animation: up .8s cubic-bezier(.2,.7,.3,1) forwards; }}
    .name {{ animation-delay: .15s; }}
    .p {{ clip-path: inset(0 100% 0 0); animation: cycle {cycle:.1f}s linear infinite; }}
    .bar {{ transform-box: fill-box; transform-origin: center; animation: pulse 3s ease-in-out infinite; }}
    @keyframes up {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes cycle {{
      0% {{ clip-path: inset(0 100% 0 0); animation-timing-function: steps(28); }}
      {t_in:.2f}% {{ clip-path: inset(0 0 0 0); }}
      {t_hold:.2f}% {{ clip-path: inset(0 0 0 0); animation-timing-function: steps(14); }}
      {t_out:.2f}% {{ clip-path: inset(0 100% 0 0); }}
      100% {{ clip-path: inset(0 100% 0 0); }}
    }}
    @keyframes pulse {{ 0%,100% {{ transform: scaleX(.6); opacity: .6; }} 50% {{ transform: scaleX(1); opacity: 1; }} }}'''}
  </style>
  <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="12" fill="#0d1117" stroke="{BORDER}"/>
  <rect x="1" y="1" width="{W - 2}" height="{H - 2}" rx="12" fill="url(#dots)" opacity=".55"/>
  <text class="hi" x="{W / 2}" y="44" text-anchor="middle">olá, mundo! 👋 eu sou o</text>
  <text class="name" x="{W / 2}" y="92" text-anchor="middle" fill="url(#name)">Tiago Rafael</text>
  {"".join(phrases)}
  <rect class="bar" x="{W / 2 - 140}" y="150" width="280" height="2" rx="1" fill="url(#glow)"/>
</svg>
"""
    OUT.write_text(out)
    print(f"-> {OUT.relative_to(ROOT)} ({W}x{H})")


if __name__ == "__main__":
    main()
