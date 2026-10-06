"""Gera o card do avatar (assets/avatar-card.svg) a partir de assets/avatar-gamer.svg.

Anima o avatar (flutuando, brilho nos óculos, LEDs do headset, pixels piscando) e
mostra um "nível" calculado a partir das contribuições do último ano.
STATIC=1 gera um frame congelado.
"""

import json
import math
import os
import re
from pathlib import Path

from theme import ACCENT, BORDER, FG, GREEN, MONO, MUTED, PURPLE, esc, window_chrome

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "avatar-gamer.svg"
OUT = ROOT / "assets" / "avatar-card.svg"
CONTRIB = ROOT / "data" / "contributions.json"
STATIC = os.environ.get("STATIC") == "1"

W, H = 370, 472
SIZE = 236  # diâmetro do avatar
CX, CY = W / 2, 56 + SIZE / 2


def avatar_body():
    """Conteúdo interno do SVG do avatar, com classes para animação."""
    s = SRC.read_text()
    s = re.sub(r"<metadata>.*?</metadata>", "", s, flags=re.S)
    s = re.sub(r"^.*?<svg[^>]*>", "", s, flags=re.S)
    s = re.sub(r"</svg>\s*$", "", s)
    s = re.sub(r"<title>.*?</title>", "", s)

    # pixels do fundo piscando, cada um no seu tempo
    count = 0

    def pixel(m):
        nonlocal count
        count += 1
        return f'<rect class="px" style="animation-delay:{(count * 0.37) % 3:.2f}s"{m.group(1)}'

    s = re.sub(r'<rect( x="\d+" y="\d+" width="10" height="10")', pixel, s)
    # reflexo passando pelas lentes
    s = re.sub(
        r'(<g fill="#FFFFFF" opacity="\.5">.*?)(</g>)',
        r'\1<polygon class="shine" points="44,124 54,124 74,86 64,86"/>'
        r'<polygon class="shine" points="58,124 62,124 82,86 78,86"/>\2',
        s,
        count=1,
    )
    # LEDs do headset e ponta do microfone
    s = s.replace('<rect x="36" y="104" width="6" height="24" rx="3" fill="#00E5A0"/>',
                  '<rect class="led" x="36" y="104" width="6" height="24" rx="3" fill="#00E5A0"/>')
    s = s.replace('<rect x="158" y="104" width="6" height="24" rx="3" fill="#00E5A0"/>',
                  '<rect class="led" x="158" y="104" width="6" height="24" rx="3" fill="#00E5A0"/>')
    s = s.replace('<circle cx="80" cy="146" r="4.5" fill="#00E5A0"/>',
                  '<circle class="mic" cx="80" cy="146" r="4.5" fill="#00E5A0"/>')
    return s


def level(total):
    """Nível estilo RPG: precisa de 8·n² XP (contribuições) para chegar no nível n."""
    lvl = int(math.sqrt(total / 8))
    cur, nxt = 8 * lvl**2, 8 * (lvl + 1) ** 2
    return lvl, total, nxt, (total - cur) / (nxt - cur)


def fmt(n):
    return f"{n:,}".replace(",", ".")


def main():
    stats = json.loads(CONTRIB.read_text())["stats"] if CONTRIB.exists() else {}
    total = stats.get("total", 0)
    lvl, xp, nxt, pct = level(total)

    x0 = 24
    info_y = CY + SIZE / 2 + 34
    bar_w = W - 2 * x0

    # Conquistas em "pílulas" logo abaixo da barra de XP
    badges = []
    if stats:
        badges = [
            (f"🔥 {stats['longest_streak']}d em sequência", "#ff7b72"),
            (f"⚡ {stats['best_day']['count']}/dia", "#d29922"),
            (f"📅 {stats['active_days']} dias on", GREEN),
        ]
    pills, px_ = [], x0
    for label, color in badges:
        w = len(label) * 6.1 + 18
        pills.append(
            f'<rect x="{px_:.1f}" y="{{y}}" width="{w:.1f}" height="22" rx="11" fill="{color}" fill-opacity=".12" stroke="{color}" stroke-opacity=".5"/>'
            f'<text x="{px_ + w / 2:.1f}" y="{{ty}}" text-anchor="middle" class="b" fill="{color}">{esc(label)}</text>'
        )
        px_ += w + 8
    out = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}">
  <title>Avatar gamer do Tiago — nível {lvl}</title>
  <defs>
    <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{ACCENT}"/>
      <stop offset=".5" stop-color="{PURPLE}"/>
      <stop offset="1" stop-color="#00e5a0"/>
    </linearGradient>
    <linearGradient id="xp" x1="0" x2="1">
      <stop offset="0" stop-color="#00e5a0"/>
      <stop offset="1" stop-color="{ACCENT}"/>
    </linearGradient>
    <radialGradient id="halo">
      <stop offset=".55" stop-color="{PURPLE}" stop-opacity=".35"/>
      <stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <style>
    .t {{ font-size: 12px; fill: {FG}; }}
    .k {{ font-size: 11px; fill: {MUTED}; letter-spacing: 1px; }}
    .b {{ font-size: 10.5px; }}
    {"" if STATIC else f'''
    .pop {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: pop .8s cubic-bezier(.2,1.4,.4,1) .2s forwards; }}
    .float {{ animation: float 4.5s ease-in-out 1s infinite; }}
    .spin {{ transform-origin: {CX}px {CY}px; animation: spin 14s linear infinite; }}
    .halo {{ transform-box: fill-box; transform-origin: center; animation: breathe 4.5s ease-in-out 1s infinite; }}
    .px {{ animation: twinkle 3s ease-in-out infinite; }}
    .shine {{ animation: shine 4s ease-in-out 1.4s infinite; }}
    .led {{ animation: led 1.6s ease-in-out infinite; }}
    .mic {{ animation: led 1s steps(1) infinite; }}
    .ln {{ opacity: 0; animation: rise .5s ease-out forwards; }}
    .fill {{ transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow 1.6s cubic-bezier(.2,.7,.3,1) 1.6s forwards; }}
    .dot {{ animation: led 2s ease-in-out infinite; }}
    @keyframes pop {{ from {{ opacity: 0; transform: scale(.6); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes float {{ 0%,100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @keyframes breathe {{ 0%,100% {{ transform: scale(.96); opacity: .7; }} 50% {{ transform: scale(1.04); opacity: 1; }} }}
    @keyframes twinkle {{ 0%,100% {{ opacity: .15; }} 50% {{ opacity: 1; }} }}
    @keyframes shine {{ 0% {{ transform: translateX(0); }} 35%,100% {{ transform: translateX(110px); }} }}
    @keyframes led {{ 0%,100% {{ opacity: 1; }} 50% {{ opacity: .35; }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(6px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes grow {{ to {{ transform: scaleX(1); }} }}'''}
  </style>
  {window_chrome(W, H, "~/player-1 — tiago")}

  <circle class="halo" cx="{CX}" cy="{CY}" r="{SIZE / 2 + 22}" fill="url(#halo)"/>
  <g class="spin">
    <circle cx="{CX}" cy="{CY}" r="{SIZE / 2 + 9}" fill="none" stroke="url(#ring)" stroke-width="2.5" stroke-dasharray="46 14 6 14" stroke-linecap="round"/>
  </g>
  <g class="pop"><g class="float">
    <svg x="{CX - SIZE / 2}" y="{CY - SIZE / 2}" width="{SIZE}" height="{SIZE}" viewBox="0 0 256 256">{avatar_body()}</svg>
  </g></g>

  <g class="ln" style="animation-delay:1.1s">
    <text x="{x0}" y="{info_y}" class="k">PLAYER</text>
    <text x="{x0 + 66}" y="{info_y}" class="t" font-weight="700" fill="{ACCENT}">TiaguinhoCode</text>
    <circle class="dot" cx="{W - x0 - 56}" cy="{info_y - 4}" r="4" fill="{GREEN}"/>
    <text x="{W - x0}" y="{info_y}" class="k" text-anchor="end" fill="{GREEN}">online</text>
  </g>
  <g class="ln" style="animation-delay:1.25s">
    <text x="{x0}" y="{info_y + 22}" class="k">CLASSE</text>
    <text x="{x0 + 66}" y="{info_y + 22}" class="t">Full Stack Dev</text>
  </g>
  <g class="ln" style="animation-delay:1.4s">
    <text x="{x0}" y="{info_y + 50}" class="t" font-weight="700" fill="#00e5a0">LVL {lvl}</text>
    <text x="{W - x0}" y="{info_y + 50}" class="k" text-anchor="end">{fmt(xp)} / {fmt(nxt)} XP</text>
    <rect x="{x0}" y="{info_y + 58}" width="{bar_w}" height="8" rx="4" fill="#161b22" stroke="{BORDER}"/>
    <rect class="fill" x="{x0}" y="{info_y + 58}" width="{max(8, bar_w * pct):.1f}" height="8" rx="4" fill="url(#xp)"/>
  </g>
  <g class="ln" style="animation-delay:1.9s">{"".join(pills).replace("{y}", str(info_y + 84)).replace("{ty}", str(info_y + 99))}</g>
</svg>
"""
    OUT.write_text(out)
    print(f"-> {OUT.relative_to(ROOT)} ({W}x{H}, nível {lvl}, {pct:.0%} pro próximo)")


if __name__ == "__main__":
    main()
