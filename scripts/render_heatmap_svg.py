"""Renderiza data/contributions.json como um calendário SVG animado (assets/contrib-heatmap.svg)."""

import json
import os
from datetime import date
from pathlib import Path

from theme import ACCENT, ACCENT_2, BG, BORDER, FG, GREEN, HEAT, MONO, MUTED, YELLOW, PINK, esc, window_chrome

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"
STATIC = os.environ.get("STATIC") == "1"

W = 860
LEFT, TOP, RIGHT = 52, 92, 24
GAP = 3
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
DIAS = ["dom", "seg", "ter", "qua", "qui", "sex", "sáb"]
DIAS_LONGOS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def fmt_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day:02d} {MESES[d.month - 1]} {d.year}"


def main():
    payload = json.loads(DATA.read_text())
    days, stats = payload["days"], payload["stats"]

    first = date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # coluna começa no domingo, como no GitHub
    cols = (len(days) + lead + 6) // 7
    step = (W - LEFT - RIGHT + GAP) / cols
    cell = round(step - GAP, 2)

    cells, month_labels = [], []
    last_month = None
    for i, d in enumerate(days):
        idx = i + lead
        col, row = divmod(idx, 7)
        x, y = LEFT + col * step, TOP + row * step
        dt = date.fromisoformat(d["date"])
        if dt.month != last_month:
            # Rótulo na primeira coluna que começa no mês novo (igual ao GitHub).
            label_x = x if row == 0 else x + step
            if not month_labels or label_x - month_labels[-1][0] >= 3 * step:
                month_labels.append((label_x, MESES[dt.month - 1]))
            last_month = dt.month
        delay = 0.4 + (col + row) * 0.022
        level = min(d["level"], 4)
        # Os dias de pico ganham o nível "neon".
        if d["count"] and d["count"] >= max(10, stats["best_day"]["count"] * 0.6):
            level = 5
        style = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        cells.append(
            f'<rect class="c l{level}" x="{x:.2f}" y="{y:.2f}" width="{cell}" height="{cell}" rx="2.5"{style}>'
            f'<title>{d["count"]} contribuições em {fmt_date(d["date"])}</title></rect>'
        )

    grid_bottom = round(TOP + 7 * step - GAP)
    months_svg = "".join(
        f'<text x="{x:.1f}" y="{TOP - 9}" class="lbl">{m}</text>' for x, m in month_labels
    )
    days_svg = "".join(
        f'<text x="{LEFT - 10}" y="{TOP + r * step + cell - 2:.1f}" class="lbl" text-anchor="end">{DIAS[r]}</text>'
        for r in (1, 3, 5)
    )

    legend_x = W - RIGHT - 30 - 6 * 15
    legend = (
        f'<text x="{legend_x - 8}" y="{grid_bottom + 20}" class="lbl" text-anchor="end">menos</text>'
        + "".join(
            f'<rect x="{legend_x + i * 15}" y="{grid_bottom + 10}" width="11" height="11" rx="2.5" fill="{c}"/>'
            for i, c in enumerate(HEAT)
        )
        + f'<text x="{legend_x + 6 * 15 + 4}" y="{grid_bottom + 20}" class="lbl">mais</text>'
    )
    left_note = (
        f'<text x="{LEFT}" y="{grid_bottom + 20}" class="lbl">'
        f'{fmt_date(stats["from"])} → {fmt_date(stats["to"])}</text>'
    )

    best = stats["best_day"]
    tiles = [
        ("total no ano", f'{stats["total"]:,}'.replace(",", "."), ACCENT_2),
        ("sequência atual", f'{stats["current_streak"]} dias', GREEN),
        ("maior sequência", f'{stats["longest_streak"]} dias', YELLOW),
        ("melhor dia", f'{best["count"]} · {fmt_date(best["date"])[:6]}', PINK),
        ("dia mais ativo", DIAS_LONGOS[stats["busiest_weekday"]], ACCENT),
    ]
    tile_y = grid_bottom + 38
    tile_w = (W - 2 * RIGHT - 4 * 12) / 5
    tiles_svg = ""
    for i, (label, value, color) in enumerate(tiles):
        tx = RIGHT + i * (tile_w + 12)
        d = 1.8 + i * 0.12
        anim = "" if STATIC else f' style="animation-delay:{d:.2f}s"'
        tiles_svg += (
            f'<g class="tile"{anim}>'
            f'<rect x="{tx}" y="{tile_y}" width="{tile_w:.1f}" height="54" rx="8" fill="#0f1620" stroke="{BORDER}"/>'
            f'<rect x="{tx}" y="{tile_y + 12}" width="3" height="30" rx="1.5" fill="{color}"/>'
            f'<text x="{tx + 16}" y="{tile_y + 22}" class="lbl">{esc(label)}</text>'
            f'<text x="{tx + 16}" y="{tile_y + 42}" class="val" fill="{color}">{esc(value)}</text>'
            "</g>"
        )

    H = tile_y + 54 + 20
    prompt = "tiago@github:~$ ./contributions.sh --last-year"
    out = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}">
  <title>Contribuições de {payload["user"]} no último ano</title>
  <style>
    .lbl {{ fill: {MUTED}; font-size: 10.5px; }}
    .val {{ font-size: 15px; font-weight: 700; }}
    .cmd {{ fill: {FG}; font-size: 13px; }}
    .l0 {{ fill: {HEAT[0]}; }} .l1 {{ fill: {HEAT[1]}; }} .l2 {{ fill: {HEAT[2]}; }}
    .l3 {{ fill: {HEAT[3]}; }} .l4 {{ fill: {HEAT[4]}; }} .l5 {{ fill: {HEAT[5]}; }}
    {"" if STATIC else f'''
    .c {{ opacity: 0; transform-box: fill-box; transform-origin: center; animation: drop .45s cubic-bezier(.2,.8,.3,1.2) forwards; }}
    .l5 {{ animation: drop .45s cubic-bezier(.2,.8,.3,1.2) forwards, glow 2.4s ease-in-out 3s infinite; }}
    .tile {{ opacity: 0; animation: rise .6s ease-out forwards; }}
    .typed {{ clip-path: inset(0 100% 0 0); animation: type 1.1s steps({len(prompt)}) .1s forwards; }}
    .caret {{ animation: blink 1s steps(1) infinite; }}
    @keyframes drop {{ from {{ opacity: 0; transform: translateY(-14px) scale(.4); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes glow {{ 0%,100% {{ fill: {HEAT[5]}; }} 50% {{ fill: #c8e6ff; }} }}
    @keyframes rise {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: none; }} }}
    @keyframes type {{ to {{ clip-path: inset(0 0 0 0); }} }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}'''}
  </style>
  {window_chrome(W, H, "contributions — zsh")}
  <text x="24" y="60" class="cmd typed"><tspan fill="{GREEN}">tiago@github</tspan><tspan fill="{MUTED}">:</tspan><tspan fill="{ACCENT}">~</tspan><tspan fill="{MUTED}">$ </tspan>./contributions.sh --last-year</text>
  <rect class="caret" x="{24 + len(prompt) * 7.8 + 4}" y="49" width="8" height="14" fill="{ACCENT}" opacity=".8"/>
  {months_svg}
  {days_svg}
  {"".join(cells)}
  {left_note}
  {legend}
  {tiles_svg}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(out)
    print(f"-> {OUT.relative_to(ROOT)} ({W}x{H}, {len(cells)} células)")


if __name__ == "__main__":
    main()
