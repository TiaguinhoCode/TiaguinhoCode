"""Converte assets/source-photo.jpg em um retrato ASCII animado (assets/ascii-portrait.svg).

Roda uma vez, localmente: python scripts/make_ascii_svg.py
Requer pillow + numpy (scripts/requirements-art.txt).
"""

import os
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

from theme import ACCENT, BORDER, FG, MONO, MUTED, esc, window_chrome

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "source-photo.jpg"
OUT = ROOT / "assets" / "ascii-portrait.svg"
STATIC = os.environ.get("STATIC") == "1"

# escuro (esparso) -> claro (denso): texto claro sobre fundo escuro
RAMP = " .'`:-=+*cs#%@"
# o brilho também vira opacidade, em poucos degraus para agrupar caracteres
SHADES = [0.28, 0.42, 0.56, 0.7, 0.85, 1.0]
COLS = 82
FONT = 7.3
CHAR_W = FONT * 0.6
LINE_H = FONT * 1.08
W, PAD_X, TOP = 370, 0, 46


def subject_mask(rgb):
    """Separa a pessoa do fundo branco e da pincelada azul do avatar."""
    a = rgb.astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    white = (r > 225) & (g > 225) & (b > 225)
    blue = (b - r > 60) & (b > 150)
    mask = Image.fromarray(((~white & ~blue) * 255).astype("uint8"))
    # fecha buracos pequenos e suaviza a borda
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    return np.asarray(mask.filter(ImageFilter.MedianFilter(5))) > 127


def main():
    img = Image.open(SRC).convert("RGB")
    # recorte focado no rosto/ombros
    w, h = img.size
    img = img.crop((int(w * 0.2), int(h * 0.04), int(w * 0.8), int(h * 0.72)))
    rgb = np.asarray(img)
    mask = subject_mask(rgb)

    gray = ImageOps.grayscale(img)
    # contraste local só dentro da silhueta
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=180, threshold=2))
    eq = np.asarray(ImageOps.equalize(gray, mask=Image.fromarray((mask * 255).astype("uint8")))).astype(float)
    eq = 0.55 * eq + 0.45 * np.asarray(ImageOps.autocontrast(gray, cutoff=1)).astype(float)

    rows = round(COLS * (img.height / img.width) * (CHAR_W / LINE_H))
    small = np.asarray(Image.fromarray(eq.astype("uint8")).resize((COLS, rows), Image.LANCZOS)).astype(float) / 255
    small_mask = np.asarray(Image.fromarray((mask * 255).astype("uint8")).resize((COLS, rows), Image.BILINEAR)) > 110

    # descarta pontos soltos fora da silhueta principal
    keep = small_mask.copy()
    for y in range(rows):
        for x in range(COLS):
            if small_mask[y, x]:
                ys, xs = slice(max(0, y - 2), y + 3), slice(max(0, x - 2), x + 3)
                keep[y, x] = small_mask[ys, xs].sum() >= 9
    small_mask = keep

    lines, shades = [], []
    for y in range(rows):
        chars, row_shades = [], []
        for x in range(COLS):
            if not small_mask[y, x]:
                chars.append(" ")
                row_shades.append(0)
                continue
            v = small[y, x] ** 1.1
            chars.append(RAMP[max(1, min(len(RAMP) - 1, int(v * (len(RAMP) - 1) + 0.5)))])
            row_shades.append(min(len(SHADES) - 1, int(v * len(SHADES))))
        lines.append("".join(chars).rstrip())
        shades.append(row_shades)

    text_w = COLS * CHAR_W
    x0 = (W - text_w) / 2
    H = round(TOP + rows * LINE_H + 16)
    rows_svg = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        y = TOP + (i + 1) * LINE_H
        anim = "" if STATIC else f' style="animation-delay:{0.2 + i * 0.045:.3f}s"'
        # agrupa caracteres vizinhos com a mesma opacidade num único tspan
        spans, start = [], 0
        for j in range(1, len(line) + 1):
            if j == len(line) or shades[i][j] != shades[i][start]:
                chunk = line[start:j]
                op = SHADES[shades[i][start]]
                spans.append(chunk if not chunk.strip() else f'<tspan fill-opacity="{op}">{esc(chunk)}</tspan>')
                start = j
        rows_svg.append(
            f'<text class="r" x="{x0:.1f}" y="{y:.1f}" xml:space="preserve"{anim}>{"".join(spans)}</text>'
        )

    out = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}">
  <title>Retrato ASCII de Tiago Rafael</title>
  <defs>
    <linearGradient id="shade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{FG}"/>
      <stop offset=".75" stop-color="{FG}"/>
      <stop offset="1" stop-color="{ACCENT}"/>
    </linearGradient>
  </defs>
  <style>
    .r {{ fill: url(#shade); font-size: {FONT}px; letter-spacing: 0; }}
    {"" if STATIC else '''
    .r { clip-path: inset(0 100% 0 0); animation: wipe .7s cubic-bezier(.4,0,.2,1) forwards; }
    .scan { animation: scan 3.2s linear .2s 1 forwards; opacity: 0; }
    @keyframes wipe { to { clip-path: inset(0 0 0 0); } }
    @keyframes scan { 0% { opacity: .55; transform: translateY(0); } 95% { opacity: .55; } 100% { opacity: 0; transform: translateY(''' + str(H - TOP) + '''px); } }'''}
  </style>
  {window_chrome(W, H, "~/tiago.png — ascii")}
  {"".join(rows_svg)}
  {"" if STATIC else f'<rect class="scan" x="1" y="{TOP}" width="{W - 2}" height="2" fill="{ACCENT}"/>'}
</svg>
"""
    OUT.write_text(out)
    print(f"-> {OUT.relative_to(ROOT)} ({W}x{H}, {COLS}x{rows} caracteres)")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
