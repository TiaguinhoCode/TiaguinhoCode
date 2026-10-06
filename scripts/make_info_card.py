"""Gera o card estilo neofetch (assets/info-card.svg) com dados reais da API do GitHub.

Usa GITHUB_TOKEN se existir (no Actions já existe); sem token funciona dentro do limite público.
STATIC=1 gera um frame congelado, útil para preview.
"""

import json
import os
import re
import urllib.request
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from theme import ACCENT, ACCENT_2, BORDER, FG, GREEN, MONO, MUTED, PINK, PURPLE, RED, YELLOW, esc, window_chrome

USER = "TiaguinhoCode"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "info-card.svg"
PORTRAIT = ROOT / "assets" / "ascii-portrait.svg"
CONTRIB = ROOT / "data" / "contributions.json"
STATIC = os.environ.get("STATIC") == "1"
W = 490

LANG_COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "HTML": "#e34c26", "CSS": "#663399",
    "Java": "#b07219", "Python": "#3572A5", "Dockerfile": "#384d54", "Shell": "#89e051",
    "SCSS": "#c6538c", "Go": "#00ADD8", "PHP": "#4F5D95", "C++": "#f34b7d",
    "CMake": "#DA3434", "C": "#555555", "Rust": "#dea584",
}

# Campos fixos — edite à vontade.
PROFILE = [
    ("Role", "Desenvolvedor Full Stack", None),
    ("Local", "Fortaleza, CE · Brasil", None),
    ("Front", "Next.js · React · Vite · Tailwind", None),
    ("Back", "Nest.js · Node.js · TypeScript", None),
    ("Infra", "Docker · MySQL · Vercel", None),
    ("Estudando", "MySQL · arquitetura limpa", None),
    ("Curto", "automatizar tudo que se repete", None),
    ("Contato", "tiagorafael019@gmail.com", None),
]


def gh(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-art"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read())


def github_stats():
    user = gh(f"/users/{USER}")
    repos = [r for r in gh(f"/users/{USER}/repos?per_page=100&type=owner") if not r["fork"]]
    langs = Counter()
    for r in repos:
        if r["name"].lower() == USER.lower():
            continue
        for lang, size in gh(f"/repos/{USER}/{r['name']}/languages").items():
            langs[lang] += size
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    return {
        "repos": user["public_repos"],
        "followers": user["followers"],
        "stars": sum(r["stargazers_count"] for r in repos),
        "since": created.date(),
        "langs": langs,
    }


def uptime(since):
    today = datetime.now(timezone.utc).date()
    months = (today.year - since.year) * 12 + today.month - since.month
    anos, meses = divmod(months, 12)
    return f"{anos} anos, {meses} meses" if meses else f"{anos} anos"


def portrait_height():
    m = re.search(r'height="(\d+)"', PORTRAIT.read_text()) if PORTRAIT.exists() else None
    return int(m.group(1)) if m else 470


def main():
    s = github_stats()
    contrib = json.loads(CONTRIB.read_text())["stats"] if CONTRIB.exists() else None

    rows = list(PROFILE)
    rows.append(None)  # separador
    rows.append(("Uptime", f"{uptime(s['since'])} no GitHub", None))
    rows.append(("Repos", f"{s['repos']} públicos · {s['stars']} ★ · {s['followers']} seguidores", None))
    if contrib:
        rows.append(("Commits", f"{contrib['total']:,} no último ano".replace(",", "."), None))

    H = portrait_height()
    x0, y0, lh = 24, 62, 21
    key_colors = [ACCENT, GREEN, YELLOW, PINK, PURPLE, ACCENT_2, RED]

    parts = []
    head = "tiago@github"
    parts.append(
        f'<text x="{x0}" y="{y0}" class="t" font-weight="700"><tspan fill="{ACCENT}">tiago</tspan>'
        f'<tspan fill="{FG}">@</tspan><tspan fill="{ACCENT}">github</tspan></text>'
    )
    parts.append(f'<text x="{x0}" y="{y0 + lh}" class="t" fill="{MUTED}">{"─" * len(head)}</text>')

    y = y0 + 2 * lh + 4
    line_i = 2
    for i, row in enumerate(rows):
        delay = 0.3 + line_i * 0.11
        anim = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        if row is None:
            parts.append(f'<line class="ln" x1="{x0}" x2="{W - x0}" y1="{y - 10}" y2="{y - 10}" stroke="{BORDER}" stroke-dasharray="3 4"{anim}/>')
            y += 10
            continue
        key, value, _ = row
        color = key_colors[i % len(key_colors)]
        parts.append(
            f'<text class="ln t" x="{x0}" y="{y}"{anim}><tspan fill="{color}" font-weight="700">{esc(key)}</tspan>'
            f'<tspan x="{x0 + 104}" fill="{FG}">{esc(value)}</tspan></text>'
        )
        y += lh
        line_i += 1

    # Barra de linguagens (por bytes de código nos repositórios públicos)
    y += 8
    top = s["langs"].most_common(5)
    total = sum(v for _, v in top) or 1
    bar_w = W - 2 * x0
    anim = "" if STATIC else f' style="animation-delay:{0.3 + line_i * 0.11:.2f}s"'
    parts.append(f'<g class="ln"{anim}><text x="{x0}" y="{y}" class="t" fill="{YELLOW}" font-weight="700">Linguagens</text>')
    y += 10
    parts.append(f'<clipPath id="bar"><rect x="{x0}" y="{y}" width="{bar_w}" height="8" rx="4"/></clipPath><g clip-path="url(#bar)">')
    cx = x0
    for lang, v in top:
        wseg = bar_w * v / total
        parts.append(f'<rect class="seg" x="{cx:.1f}" y="{y}" width="{wseg + 0.5:.1f}" height="8" fill="{LANG_COLORS.get(lang, MUTED)}"/>')
        cx += wseg
    parts.append("</g>")
    y += 26
    lx = x0
    for lang, v in top:
        label = f"{lang} {100 * v / total:.0f}%"
        parts.append(
            f'<circle cx="{lx + 4}" cy="{y - 4}" r="4" fill="{LANG_COLORS.get(lang, MUTED)}"/>'
            f'<text x="{lx + 13}" y="{y}" class="s" fill="{MUTED}">{esc(label)}</text>'
        )
        lx += 13 + len(label) * 6.6 + 10
    parts.append("</g>")

    # Blocos de cor do neofetch no rodapé
    by = H - 46
    blocks = ["#484f58", RED, GREEN, YELLOW, ACCENT, PURPLE, "#39c5cf", FG]
    anim = "" if STATIC else f' style="animation-delay:{0.45 + line_i * 0.11:.2f}s"'
    parts.append(f'<g class="ln"{anim}>' + "".join(
        f'<rect x="{x0 + i * 26}" y="{by}" width="22" height="14" rx="2" fill="{c}"/>' for i, c in enumerate(blocks)
    ) + "</g>")
    parts.append(
        f'<text x="{W - x0}" y="{by + 11}" text-anchor="end" class="s" fill="{MUTED}">atualizado em {date.today():%d/%m/%Y}</text>'
    )

    out = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}">
  <title>tiago@github — neofetch</title>
  <style>
    .t {{ font-size: 13px; fill: {FG}; }}
    .s {{ font-size: 11px; }}
    {"" if STATIC else '''
    .ln { opacity: 0; animation: in .5s cubic-bezier(.2,.7,.3,1) forwards; }
    .seg { transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: grow .9s cubic-bezier(.2,.7,.3,1) 1.9s forwards; }
    @keyframes in { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: none; } }
    @keyframes grow { to { transform: scaleX(1); } }'''}
  </style>
  {window_chrome(W, H, "tiago@github: ~ — neofetch")}
  {"".join(parts)}
</svg>
"""
    OUT.write_text(out)
    print(f"-> {OUT.relative_to(ROOT)} ({W}x{H})")


if __name__ == "__main__":
    main()
