
#!/usr/bin/env python3
"""Generate animated GitHub contribution calendar with a pixel-art cat.

Environment: GH_TOKEN (required), GH_USERNAME (defaults to LuizaFerri).
Python standard library only.
"""

import json
import os
from datetime import date
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

USER = os.getenv('GH_USERNAME', 'LuizaFerri')
TOKEN = os.getenv('GH_TOKEN')
OUT = Path(os.getenv('SVG_OUT', 'dist/github-cat-contributions.svg'))

QUERY = '''query($login: String!) {
 user(login: $login) {
  contributionsCollection {
   contributionCalendar {
    totalContributions
    weeks { contributionDays { date contributionCount contributionLevel } }
   }
  }
 }
}'''

# Paleta roxa e lilás para as contribuições
LEVEL_COLORS = {
    'NONE': '#171C25',
    'FIRST_QUARTILE': '#3B1F58',
    'SECOND_QUARTILE': '#6D28D9',
    'THIRD_QUARTILE': '#A78BFA',
    'FOURTH_QUARTILE': '#D8B4FE'
}

# Gatinho pixel art original (18 x 14)
CAT = [
    '   PP        PP   ',
    '  PPPP      PPPP  ',
    '  PWWPPPPPPPPWWP  ',
    '  PWWWWWWWWWWWWP  ',
    '  PWWKWWWWWWKWWP  ',
    '  PWWKWWWWWWKWWP  ',
    '  PWWWWWWWWWWWWP  ',
    '  PWWWWWRRWWWWWP  ',
    '  PWWWWWWWWWWWWP  ',
    '   PWWWWWWWWWWP   ',
    '   PPPPPPPPPPPP   ',
    '    PWP    PWP    ',
    '    PWP    PWP    ',
    '    PPP    PPP    ',
]

CAT_COLORS = {
    'P': '#9f67d7',
    'W': '#d8c7ed',
    'K': '#252235',
    'R': '#ee8da8'
}


def get_weeks():
    if not TOKEN:
        raise SystemExit(
            'GH_TOKEN not found: add it to the workflow environment.'
        )

    req = Request(
        'https://api.github.com/graphql',
        data=json.dumps({
            'query': QUERY,
            'variables': {'login': USER}
        }).encode(),
        headers={
            'Authorization': f'Bearer {TOKEN}',
            'Content-Type': 'application/json',
            'User-Agent': 'github-cat-generator'
        }
    )

    with urlopen(req, timeout=30) as resp:
        result = json.load(resp)

    if result.get('errors'):
        raise RuntimeError(
            f"GitHub GraphQL errors: {result['errors']}"
        )

    user = result.get('data', {}).get('user')

    if not user:
        raise RuntimeError(
            f'GitHub account {USER!r} not found'
        )

    calendar = user['contributionsCollection']['contributionCalendar']

    return calendar['weeks'], calendar['totalContributions']


def make_svg(weeks, total):
    # Configuração do calendário
    cell = 12
    step = 15
    left = 22
    top = 34

    width = left * 2 + max(1, len(weeks)) * step - 3
    height = 234

    cat_scale = 2
    cat_w = max(map(len, CAT)) * cat_scale

    first = left
    last = max(first, width - left - cat_w)

    lines = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" '
            f'role="img" aria-labelledby="title desc">'
        ),

        '<title id="title">'
        'Calendário de contribuições com gatinho pixel art'
        '</title>',

        (
            f'<desc id="desc">{total} contribuições no último ano. '
            'Um gatinho lilás caminha embaixo do calendário.</desc>'
        ),

        '<style><![CDATA[',

        (
            '.label{'
            'font:600 12px ui-monospace,SFMono-Regular,Consolas,monospace;'
            'fill:#A4A9B6'
            '}'
        ),

        (
            '@media (prefers-reduced-motion:reduce){'
            '.cat-motion,.cat-bob,.paw{animation:none!important}'
            '}'
        ),

        ']]></style>',

        (
            f'<text class="label" x="{left}" y="17">'
            f'✦ {escape(USER)} · {total} contribuições'
            '</text>'
        ),
    ]

    # Quadradinhos das contribuições
    for wi, week in enumerate(weeks):
        for day in week['contributionDays']:

            weekday = (
                date.fromisoformat(day['date']).weekday() + 1
            ) % 7

            x = left + wi * step
            y = top + weekday * step

            fill = LEVEL_COLORS.get(
                day['contributionLevel'],
                LEVEL_COLORS['NONE']
            )

            lines.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{cell}" height="{cell}" '
                f'rx="2.5" fill="{fill}">'
                f'<title>{escape(day["date"])}: '
                f'{day["contributionCount"]} contribuições</title>'
                '</rect>'
            )

    # Caminho roxo do gatinho
    baseline = 169

    lines.append(
        f'<path d="M{left} {baseline+3} H{width-left}" '
        'stroke="#6D28D9" '
        'stroke-width="1" '
        'stroke-dasharray="2 8" '
        'opacity=".6"/>'
    )

    # Patinhas lilás animadas
    count = 14

    for i in range(count):
        x = first + (last - first) * i / (count - 1)

        for dx, dy, r in (
            (0, 0, 2),
            (-3, -3, 1),
            (-1, -5, 1),
            (2, -4, 1)
        ):
            lines.append(
                f'<circle class="paw" '
                f'cx="{x+dx:.1f}" '
                f'cy="{baseline+dy}" '
                f'r="{r}" '
                'fill="#C4B5FD" '
                'opacity="0">'
                '<animate attributeName="opacity" '
                'values="0;0;.75;0;0" '
                'keyTimes="0;.1;.3;.6;1" '
                'dur="14s" '
                f'begin="{i*0.92:.2f}s" '
                'repeatCount="indefinite"/>'
                '</circle>'
            )

    # Movimento horizontal do gatinho
    lines.append(
        '<g class="cat-motion">'
        '<animateTransform '
        'attributeName="transform" '
        'type="translate" '
        f'values="{first} 0;{last} 0;{first} 0" '
        'keyTimes="0;.5;1" '
        'dur="28s" '
        'repeatCount="indefinite"/>'
    )

    # Pequeno movimento vertical ao caminhar
    lines.append(
        '<g class="cat-bob">'
        '<animateTransform '
        'attributeName="transform" '
        'type="translate" '
        'values="0 0;0 -2;0 0" '
        'dur=".55s" '
        'repeatCount="indefinite"/>'
    )

    # Desenha os pixels do gatinho
    cy = baseline - len(CAT) * cat_scale + 2

    for row, pixels in enumerate(CAT):
        for col, symbol in enumerate(pixels):

            if symbol in CAT_COLORS:
                lines.append(
                    f'<rect '
                    f'x="{col*cat_scale}" '
                    f'y="{cy+row*cat_scale}" '
                    f'width="{cat_scale}" '
                    f'height="{cat_scale}" '
                    f'fill="{CAT_COLORS[symbol]}"/>'
                )

    # Rabinho animado
    lines.append(
        f'<path d="M{cat_w-2} {cy+21}q13 -10 7 -22" '
        'fill="none" '
        'stroke="#9f67d7" '
        'stroke-width="4" '
        'stroke-linecap="square">'
        '<animate attributeName="d" '
        f'values="M{cat_w-2} {cy+21}q13 -10 7 -22;'
        f'M{cat_w-2} {cy+21}q18 1 14 -16;'
        f'M{cat_w-2} {cy+21}q13 -10 7 -22" '
        'dur="1.5s" '
        'repeatCount="indefinite"/>'
        '</path>'
    )

    lines.append('</g></g>')

    # Rodapé
    lines.append(
        f'<text class="label" x="{left}" y="218" opacity=".7">'
        'feito com commits e patinhas ♡'
        '</text>'
    )

    lines.append('</svg>')

    return '\n'.join(lines)


if __name__ == '__main__':
    weeks, total = get_weeks()

    OUT.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    OUT.write_text(
        make_svg(weeks, total),
        encoding='utf-8'
    )

    print(
        f'Created {OUT} '
        f'({len(weeks)} weeks, {total} contributions)'
    )
