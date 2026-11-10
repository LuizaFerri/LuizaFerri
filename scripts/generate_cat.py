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

LEVEL_COLORS = {
    'NONE': '#171c25',
    'FIRST_QUARTILE': '#263c38',
    'SECOND_QUARTILE': '#216b59',
    'THIRD_QUARTILE': '#3fa58a',
    'FOURTH_QUARTILE': '#68dcb2'
}

# An original 18 x 14 pixel-art cat, transparent cells represented by spaces.
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
CAT_COLORS = {'P':'#9f67d7','W':'#d8c7ed','K':'#252235','R':'#ee8da8'}

def get_weeks():
    if not TOKEN:
        raise SystemExit('GH_TOKEN not found: add it to the workflow environment.')
    req = Request('https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': USER}}).encode(),
        headers={'Authorization':f'Bearer {TOKEN}', 'Content-Type':'application/json', 'User-Agent':'github-cat-generator'})
    with urlopen(req, timeout=30) as resp:
        result = json.load(resp)
    if result.get('errors'):
        raise RuntimeError(f"GitHub GraphQL errors: {result['errors']}")
    user = result.get('data', {}).get('user')
    if not user:
        raise RuntimeError(f'GitHub account {USER!r} not found')
    calendar = user['contributionsCollection']['contributionCalendar']
    return calendar['weeks'], calendar['totalContributions']

def make_svg(weeks, total):
    # 12px cells + 3px gaps. Cat walks in an 18px-tall strip below the calendar.
    cell, step, left, top = 12, 15, 22, 34
    width = left * 2 + max(1,len(weeks))*step - 3
    height = 234
    cat_scale = 2
    cat_w = max(map(len,CAT)) * cat_scale
    first = left
    last = max(first, width - left - cat_w)
    lines = [
      f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
      '<title id="title">Calendário de contribuições com gatinho pixel art</title>',
      f'<desc id="desc">{total} contribuições no último ano. Um gatinho lilás caminha embaixo do calendário.</desc>',
      '<style><![CDATA[',
      '.label{font:600 12px ui-monospace,SFMono-Regular,Consolas,monospace;fill:#a4a9b6}',
      '@media (prefers-reduced-motion:reduce){.cat-motion,.cat-bob,.paw{animation:none!important}}',
      ']]></style>',
      f'<text class="label" x="{left}" y="17">✦ {escape(USER)} · {total} contribuições</text>',
    ]
    for wi, week in enumerate(weeks):
        for day in week['contributionDays']:
            # Row 0 = Sunday, matching GitHub's calendar.
            weekday = (date.fromisoformat(day['date']).weekday() + 1) % 7
            x, y = left + wi * step, top + weekday*step
            fill = LEVEL_COLORS.get(day['contributionLevel'], LEVEL_COLORS['NONE'])
            lines.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{fill}"><title>{escape(day["date"])}: {day["contributionCount"]} contribuições</title></rect>')
    baseline = 169
    lines.append(f'<path d="M{left} {baseline+3} H{width-left}" stroke="#433154" stroke-width="1" stroke-dasharray="2 8" opacity=".6"/>')
    # Paw marks shimmer along the path, staggered to follow cat.
    count = 14
    for i in range(count):
        x = first + (last-first) * i / (count-1)
        for dx,dy,r in ((0,0,2),(-3,-3,1),(-1,-5,1),(2,-4,1)):
            lines.append(f'<circle class="paw" cx="{x+dx:.1f}" cy="{baseline+dy}" r="{r}" fill="#b886e7" opacity=".0"><animate attributeName="opacity" values="0;0;.75;.0;0" keyTimes="0;.1;.3;.6;1" dur="14s" begin="{i*0.92:.2f}s" repeatCount="indefinite"/></circle>')
    # Cat movement is SVG-native; supported by GitHub image embedding without JS.
    lines.append(f'<g class="cat-motion"><animateTransform attributeName="transform" type="translate" values="{first} 0;{last} 0;{first} 0" keyTimes="0;.5;1" dur="28s" repeatCount="indefinite"/>')
    lines.append(f'<g class="cat-bob"><animateTransform attributeName="transform" type="translate" values="0 0;0 -2;0 0" dur=".55s" repeatCount="indefinite"/>')
    # Place cat roughly on baseline, leaving space for the footer.
    cy = baseline - len(CAT)*cat_scale+2
    for row, pixels in enumerate(CAT):
        for col, symbol in enumerate(pixels):
            if symbol in CAT_COLORS:
                lines.append(f'<rect x="{col*cat_scale}" y="{cy+row*cat_scale}" width="{cat_scale}" height="{cat_scale}" fill="{CAT_COLORS[symbol]}"/>')
    # Animated tail to cat's right.
    lines.append(f'<path d="M{cat_w-2} {cy+21}q13 -10 7 -22" fill="none" stroke="#9f67d7" stroke-width="4" stroke-linecap="square"><animate attributeName="d" values="M{cat_w-2} {cy+21}q13 -10 7 -22;M{cat_w-2} {cy+21}q18 1 14 -16;M{cat_w-2} {cy+21}q13 -10 7 -22" dur="1.5s" repeatCount="indefinite"/></path>')
    lines.append('</g></g>')
    lines.append(f'<text class="label" x="{left}" y="218" opacity=".7">feito com commits e patinhas ♡</text>')
    lines.append('</svg>')
    return '\n'.join(lines)

if __name__ == '__main__':
    weeks, total = get_weeks()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(make_svg(weeks, total), encoding='utf-8')
    print(f'Created {OUT} ({len(weeks)} weeks, {total} contributions)')
