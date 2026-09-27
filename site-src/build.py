#!/usr/bin/env python3
"""Static site generator for meding.dev.

Reads content/<lang>.json (en is the master), data/extracted.json (speaking, press, quotes)
and data/refs.json (sources), and writes a ready-to-deploy site to ./public.

Usage: python3 build.py [--preview]
  --preview  internal links point at explicit index.html files (for hosts without directory indexes)
"""
import hashlib, html, json, os, re, shutil, sys, datetime
from urllib.parse import urlparse

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get('MEDING_OUT') or os.path.join(ROOT, 'public')
ASSETS = os.path.join(ROOT, 'assets')
PREVIEW = '--preview' in sys.argv
SITE = 'https://meding.dev'
TODAY = datetime.date(2026, 9, 27)

LANGS = ['en', 'es', 'de', 'ja', 'zh']
HREFLANG = {'en': 'en', 'es': 'es', 'de': 'de', 'ja': 'ja', 'zh': 'zh-Hans'}
HTML_LANG = HREFLANG
LANG_CODE_LABEL = {'en': 'EN', 'es': 'ES', 'de': 'DE', 'ja': '日本語', 'zh': '中文'}
PAGES = ['home', 'la', 'speaking', 'press']
SLUG = {'home': '', 'la': 'los-azules/', 'speaking': 'speaking/', 'press': 'press/'}

def _ver(name):
    """Short content hash, appended to CSS and JS links so browsers and the CDN fetch a changed file at once."""
    return hashlib.sha256(open(os.path.join(ASSETS, name), 'rb').read()).hexdigest()[:10]


VER = {n: _ver(n) for n in ('site.css', 'site.js')}
C = {l: json.load(open(os.path.join(ROOT, 'content', f'{l}.json'), encoding='utf-8')) for l in LANGS}
X = json.load(open(os.path.join(ROOT, 'data', 'extracted.json'), encoding='utf-8'))
REFS = json.load(open(os.path.join(ROOT, 'data', 'refs.json'), encoding='utf-8'))

# ---------------------------------------------------------------- localisation helpers
MON = {
    'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    'es': ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'],
    'de': ['Jan.', 'Feb.', 'März', 'Apr.', 'Mai', 'Juni', 'Juli', 'Aug.', 'Sept.', 'Okt.', 'Nov.', 'Dez.'],
}
MON_LONG = {
    'en': ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
    'es': ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'],
    'de': ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'],
}


def month_short(l, m):
    if m is None:
        return ''
    if l in ('ja', 'zh'):
        return f'{m}月'
    return MON[l][m - 1]


def day_month(l, m, day):
    """Speaking table date cell (year is in its own column)."""
    if m is None:
        return ''
    if not day:
        return month_short(l, m)
    if l in ('ja', 'zh'):
        parts = day.split('–')
        sep = '〜' if l == 'ja' else '至'
        return f'{m}月' + sep.join(p + '日' for p in parts)
    if l == 'de':
        return '.–'.join(day.split('–')) + '. ' + MON['de'][m - 1]
    return f'{day} {MON[l][m - 1]}'


def full_date(l, iso):
    y, m, d = (int(x) for x in iso.split('-'))
    if l in ('ja', 'zh'):
        return f'{y}年{m}月{d}日'
    if l == 'de':
        return f'{d}. {MON["de"][m - 1]} {y}'
    return f'{d} {MON[l][m - 1]} {y}'


def long_date(l, dt):
    if l in ('ja', 'zh'):
        return f'{dt.year}年{dt.month}月{dt.day}日'
    if l == 'de':
        return f'{dt.day}. {MON_LONG["de"][dt.month - 1]} {dt.year}'
    if l == 'es':
        return f'{dt.day} de {MON_LONG["es"][dt.month - 1]} de {dt.year}'
    return f'{dt.day} {MON_LONG["en"][dt.month - 1]} {dt.year}'


# Localised big numbers for the stat tiles: (value, small unit)
STATS = {
    'home': {
        'reserves': {'en': ('10.2', 'B lb'), 'es': ('10.200', 'M lb'), 'de': ('10,2', 'Mrd. lb'), 'ja': ('102', '億ポンド'), 'zh': ('102', '亿磅')},
        'npv': {'en': ('US$2.9', 'B'), 'es': ('US$2.900', 'M'), 'de': ('2,9', 'Mrd. US$'), 'ja': ('29', '億米ドル'), 'zh': ('29', '亿美元')},
        'loan': {'en': ('US$240', 'M'), 'es': ('US$240', 'M'), 'de': ('240', 'Mio. US$'), 'ja': ('2.4', '億米ドル'), 'zh': ('2.4', '亿美元')},
        'rigi': {'en': ('1', 'st'), 'es': ('1', '.er'), 'de': ('1.', ''), 'ja': ('第1号', ''), 'zh': ('首个', '')},
        'cathode': {l: ('2030', '') for l in LANGS},
        'placements': {'en': ('US$453', 'M'), 'es': ('US$453', 'M'), 'de': ('453', 'Mio. US$'), 'ja': ('4.53', '億米ドル'), 'zh': ('4.53', '亿美元')},
    },
    'la': {
        'reserves': {'en': ('10.2', 'B lb'), 'es': ('10.200', 'M lb'), 'de': ('10,2', 'Mrd. lb'), 'ja': ('102', '億ポンド'), 'zh': ('102', '亿磅')},
        'mi': {'en': ('5.4', 'B lb'), 'es': ('5.400', 'M lb'), 'de': ('5,4', 'Mrd. lb'), 'ja': ('54', '億ポンド'), 'zh': ('54', '亿磅')},
        'inf': {'en': ('20.0', 'B lb'), 'es': ('20.000', 'M lb'), 'de': ('20,0', 'Mrd. lb'), 'ja': ('200', '億ポンド'), 'zh': ('200', '亿磅')},
        'lom': {'en': ('21', 'years'), 'es': ('21', 'años'), 'de': ('21', 'Jahre'), 'ja': ('21', '年'), 'zh': ('21', '年')},
        'upside': {'en': ('30+', 'years'), 'es': ('30+', 'años'), 'de': ('30+', 'Jahre'), 'ja': ('30', '年以上'), 'zh': ('30', '年以上')},
        'output': {'en': ('204.8', 'kt'), 'es': ('204,8', 'kt'), 'de': ('204,8', 'kt'), 'ja': ('20.48', '万トン'), 'zh': ('20.48', '万吨')},
        'capex': {'en': ('US$3.17', 'B'), 'es': ('US$3.170', 'M'), 'de': ('3,17', 'Mrd. US$'), 'ja': ('31.7', '億米ドル'), 'zh': ('31.7', '亿美元')},
        'npv': {'en': ('US$2.9', 'B'), 'es': ('US$2.900', 'M'), 'de': ('2,9', 'Mrd. US$'), 'ja': ('29', '億米ドル'), 'zh': ('29', '亿美元')},
        'irr': {'en': ('19.8', '%'), 'es': ('19,8', '%'), 'de': ('19,8', '%'), 'ja': ('19.8', '％'), 'zh': ('19.8', '%')},
    },
}
STAT_LABEL_OVERRIDE = {('zh', 'home', 'rigi'): '获RIGI批准的铜矿项目'}

RAIL_POS = [1, 35, 44.5, 55, 66, 102]  # months after Jan 2022, to scale; 2030 placed mid-year
RAIL_TODAY = 56.9  # 27 Sep 2026
RAIL_TARGET = [False, False, False, False, True, True]
RAIL_DATES = {
    'en': ['Feb 2022', 'Dec 2024', 'Sep–Oct 2025', 'Aug 2026', 'Mid 2027', '2030'],
    'es': ['feb 2022', 'dic 2024', 'sep–oct 2025', 'ago 2026', 'mediados de 2027', '2030'],
    'de': ['Feb. 2022', 'Dez. 2024', 'Sept.–Okt. 2025', 'Aug. 2026', 'Mitte 2027', '2030'],
    'ja': ['2022年2月', '2024年12月', '2025年9〜10月', '2026年8月', '2027年半ば', '2030年'],
    'zh': ['2022年2月', '2024年12月', '2025年9–10月', '2026年8月', '2027年年中', '2030年'],
}


RES_TABLE = {  # feasibility study, effective 3 Sep 2025 (McEwen Inc. release 7 Oct 2025)
    'reserves': [('res_proven', '229.9', '0.683', '3,463'), ('res_probable', '793.2', '0.386', '6,754'), ('res_total', '1,023.1', '0.453', '10,217')],
    'resources': [('rs_mi', '965.5', '0.255', '5.4'), ('rs_inf', '4,239.3', '0.214', '20.0')],
}


def loc_num(l, s):
    """Localise decimal/thousands separators of a plain number string."""
    if l in ('es', 'de'):
        return s.replace(',', '\u0001').replace('.', ',').replace('\u0001', '.')
    return s


# ---------------------------------------------------------------- page context
class Page:
    def __init__(self, lang, key):
        self.lang, self.key = lang, key
        self.c = C[lang]
        self.refs = []  # order of first citation

    # paths
    def path(self, lang=None, key=None):
        lang = lang or self.lang
        key = key or self.key
        return ('' if lang == 'en' else f'{lang}/') + SLUG[key]

    def url(self, lang=None, key=None):
        return f'{SITE}/{self.path(lang, key)}'

    def depth(self):
        return self.path().count('/')

    def rel(self, target_path):
        """Relative link from this page to a site path ('' = root)."""
        up = '../' * self.depth()
        p = up + target_path
        if PREVIEW:
            if p == '' or p.endswith('/'):
                p += 'index.html'
        return p or './'

    def link(self, lang=None, key=None):
        return self.rel(self.path(lang, key))

    def asset(self, p):
        return '../' * self.depth() + p

    # citations
    def cite(self, keys):
        items = []
        for k in keys:
            if k not in REFS:
                raise KeyError(f'unknown ref {k}')
            if k not in self.refs:
                self.refs.append(k)
            items.append((self.refs.index(k) + 1, k))
        items.sort()
        runs, cur = [], [items[0]]
        for it in items[1:]:
            if it[0] == cur[-1][0] + 1:
                cur.append(it)
            else:
                runs.append(cur)
                cur = [it]
        runs.append(cur)
        parts = []
        for r in runs:
            a = lambda it: f'<a href="#ref-{it[1]}">{it[0]}</a>'
            parts.append(a(r[0]) + '–' + a(r[-1]) if len(r) >= 3 else ', '.join(a(it) for it in r))
        return '<sup class="cite">[' + ', '.join(parts) + ']</sup>'

    def t(self, s):
        """Escape text and turn [[r:...]] tokens into citation links."""
        out, pos = [], 0
        for m in re.finditer(r'\[\[r:([^\]]+)\]\]', s):
            out.append(html.escape(s[pos:m.start()], quote=False))
            out.append(self.cite(m.group(1).split(',')))
            pos = m.end()
        out.append(html.escape(s[pos:], quote=False))
        return ''.join(out)

    def tr(self, keystr):
        """Citation for a comma-separated key string (table rows)."""
        return self.cite(keystr.split(',')) if keystr else ''


def paren(l, s):
    return f'（{esc(s)}）' if l in ('ja', 'zh') else f' ({esc(s)})'


def strip_tokens(s):
    return re.sub(r'\s*\[\[r:[^\]]+\]\]', '', s).strip()


def esc(s):
    return html.escape(s, quote=True)


def domain(u):
    return urlparse(u).netloc


# ---------------------------------------------------------------- images
IMG = {  # file: (width, height)
    'portrait.jpg': (1600, 1066), 'site-delegations.jpg': (1400, 1048), 'ifc-2025.jpg': (1400, 788),
    'entrepreneur-2025.jpg': (1167, 1600), 'diploma-2024.jpg': (1400, 785), 'new-york-2024.jpg': (1400, 1050),
    'washington-2026-colour.jpg': (1600, 1067),
}


def img(p, name, alt, pos='50% 50%', eager=False, sizes='(min-width: 960px) 390px, 100vw'):
    """eager=True: first image in view (high priority); eager='plain': load normally; False: lazy."""
    w, h = IMG[name]
    base = name[:-4]
    src = p.asset(f'img/{name}')
    srcset = f'{p.asset("img/" + base + "-800.jpg")} 800w, {src} {w}w'
    load = 'fetchpriority="high"' if eager is True else ('decoding="async"' if eager else 'loading="lazy" decoding="async"')
    return (f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" alt="{esc(alt)}" width="{w}" height="{h}" '
            f'{load} style="object-position:{pos}">')


# ---------------------------------------------------------------- shared chrome
def head(p, title, desc, jsonld, og_type='website'):
    l = p.lang
    alts = ''.join(f'<link rel="alternate" hreflang="{HREFLANG[x]}" href="{p.url(x)}">' for x in LANGS)
    alts += f'<link rel="alternate" hreflang="x-default" href="{p.url("en")}">'
    ogalt = ''.join(f'<meta property="og:locale:alternate" content="{C[x]["meta"]["og_locale"]}">' for x in LANGS if x != l)
    return f'''<!doctype html>
<html lang="{HTML_LANG[l]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{p.url()}">
{alts}
<link rel="alternate" type="text/plain" href="{SITE}/llms.txt" title="llms.txt">
<link rel="alternate" type="text/plain" href="{SITE}/llms-full.txt" title="llms-full.txt">
<link rel="alternate" type="application/json" href="{SITE}/facts.json" title="Structured facts">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="author" content="Michael Meding">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Michael Meding">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{p.url()}">
<meta property="og:image" content="{SITE}/img/og-{l}.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Michael Meding">
<meta property="og:locale" content="{C[l]["meta"]["og_locale"]}">
{ogalt}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@mmeding">
<meta name="theme-color" content="#0b1517">
<link rel="icon" href="{p.asset("favicon.ico")}" sizes="32x32">
<link rel="icon" href="{p.asset("favicon.svg")}" type="image/svg+xml">
<link rel="apple-touch-icon" href="{p.asset("apple-touch-icon.png")}">
<link rel="preload" href="{p.asset("fonts/source-serif-4-latin-opsz-normal.woff2")}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{p.asset("site.css")}?v={VER["site.css"]}">
<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False, separators=(",", ":"))}</script>
</head>
<body><!--email_off-->
'''


def header(p):
    ui = p.c['ui']
    nav = ''
    for k, lab in (('home', ui['nav_home']), ('la', ui['nav_la']), ('speaking', ui['nav_speaking']), ('press', ui['nav_press'])):
        cur = ' aria-current="page"' if k == p.key else ''
        nav += f'<a href="{p.link(key=k)}"{cur}>{esc(lab)}</a>'
    langs = ''
    for x in LANGS:
        cur = ' aria-current="true"' if x == p.lang else ''
        langs += (f'<a href="{p.link(lang=x)}" hreflang="{HREFLANG[x]}" lang="{HTML_LANG[x]}" '
                  f'title="{esc(C[x]["meta"]["lang_name"])}"{cur}>{LANG_CODE_LABEL[x]}</a>')
    return f'''<a class="skip" href="#main">{esc(ui["skip"])}</a>
<header class="bar"><div class="in">
<a class="brand" href="{p.link(key="home")}">Michael Meding</a>
<nav class="nav" aria-label="{esc(ui["nav_home"])}">{nav}</nav>
<nav class="lang" aria-label="{esc(ui["lang_label"])}">{langs}</nav>
</div></header>
'''


def footer(p):
    ui = p.c['ui']
    langs = ' · '.join(f'<a href="{p.link(lang=x)}" hreflang="{HREFLANG[x]}" lang="{HTML_LANG[x]}">{esc(C[x]["meta"]["lang_name"])}</a>' for x in LANGS)
    return f'''<footer class="foot"><div class="wrap">
<p>{esc(ui["footer_note"])} {esc(ui["reviewed"])}: {long_date(p.lang, TODAY)}.</p>
<p class="disc">{esc(ui["footer_disclaimer"])}</p>
<p class="fl">{langs}</p>
<p>© Michael Meding · San Juan · Toronto · <a href="mailto:michael@meding.dev">michael@meding.dev</a> · <a href="https://www.linkedin.com/in/michaelmeding" rel="me">LinkedIn</a> · <a href="https://x.com/mmeding" rel="me">X</a></p>
</div></footer>
<script src="{p.asset("site.js")}?v={VER["site.js"]}" defer></script>
<!--/email_off--></body>
</html>
'''


def section(id_, h, body, cls='s'):
    return f'<section id="{id_}" class="{cls}"><h2>{h}</h2>{body}</section>\n'


def toc(p, items):
    if not items:
        return ''
    lis = ''.join(f'<li><a href="#{i}">{esc(h)}</a></li>' for i, h in items)
    return f'<nav class="toc" aria-label="{esc(p.c["ui"]["contents"])}"><p class="toc-h">{esc(p.c["ui"]["contents"])}</p><ol>{lis}</ol></nav>'


def refs_section(p):
    if not p.refs:
        return ''
    lis = ''
    for i, k in enumerate(p.refs, 1):
        r = REFS[k]
        date = r['date']
        lis += (f'<li id="ref-{k}"><span class="rn">{i}</span><span><b>{esc(r["publisher"])}</b>. {esc(r["title"])}. '
                f'{esc(date)}. <a href="{esc(r["url"])}" rel="noopener">{esc(domain(r["url"]))}</a></span></li>')
    return section('references', esc(p.c['ui']['refs']), f'<ol class="refs">{lis}</ol>')


def stats_html(p, page, items):
    out = ''
    for key, label in items:
        v, u = STATS[page][key][p.lang]
        label = STAT_LABEL_OVERRIDE.get((p.lang, page, key), label)
        # label may carry a citation token
        out += f'<div><dt>{esc(v)}{f"<small>{esc(u)}</small>" if u else ""}</dt><dd>{p.t(label)}</dd></div>'
    return f'<dl class="stats">{out}</dl>'


def facts_table(p, rows):
    trs = ''.join(f'<tr><th scope="row">{esc(r["k"])}</th><td>{p.t(r["v"])}{p.tr(r.get("r", ""))}</td></tr>' for r in rows)
    return f'<table class="ft">{trs}</table>'


def quote_fig(p, i, q):
    tr = p.c['quotes_tr'][i]
    trh = f'<p class="qt" lang="{HTML_LANG[p.lang]}">{esc(tr)}</p>' if tr else ''
    return (f'<figure class="q"><blockquote lang="{q["orig_lang"]}">{esc(q["text"])}</blockquote>{trh}'
            f'<figcaption><a href="{esc(q["url"])}" rel="noopener">{esc(q["source"])}</a></figcaption></figure>')


def speaking_rows(p, rows, stack=True):
    ui = p.c['ui']
    sp = p.c['speaking']
    trs = ''
    for s in rows:
        up = f' <span class="tag">{esc(ui["upcoming"])}</span>' if s['upcoming'] else ''
        k = s['year'] + (' up' if s['upcoming'] else '')
        trs += (f'<tr data-k="{k}"><td class="n" data-l="{esc(ui["th_year"])}">{s["year"]}</td>'
                f'<td class="n" data-l="{esc(ui["th_date"])}">{esc(day_month(p.lang, s["month"], s["day"]))}</td>'
                f'<td data-l="{esc(ui["th_city"])}">{esc(sp["cities"][s["city"]])}</td>'
                f'<td data-l="{esc(ui["th_event"])}"><b>{esc(s["event"])}</b>{up}</td>'
                f'<td data-l="{esc(ui["th_role"])}">{esc(sp["roles"][s["id"]])}</td></tr>')
    th = ''.join(f'<th scope="col">{esc(ui[k])}</th>' for k in ('th_year', 'th_date', 'th_city', 'th_event', 'th_role'))
    return f'<table class="tb sp stack" id="sp"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>'


def press_items(p, items, id_='pr'):
    lis = ''
    for it in items:
        lang = it['lang'] or 'es'
        tag = p.c['ui'].get(f'lang_tag_{lang}', lang.upper())
        k = ' '.join(it['cats'])
        lis += (f'<li data-k="{k}"><span class="n pd"><time datetime="{it["iso"]}">{full_date(p.lang, it["iso"])}</time></span>'
                f'<span class="po">{esc(it["outlet"])}</span>'
                f'<a href="{esc(it["url"])}" rel="noopener" lang="{lang}" hreflang="{lang}">{esc(it["headline"])}</a>'
                f'<span class="lt" aria-hidden="true">{esc(tag)}</span></li>')
    return f'<ol class="pr" id="{id_}">{lis}</ol>'


def life_bar(p):
    """Base case (21 years, to scale) then a gap, then the potential extension drawn open-ended and not to a dated scale."""
    a = p.c['la']
    return (f'<figure class="life" aria-label="{esc(a["h_life"])}"><div class="lb">'
            f'<div class="lb-base" style="flex:21"><b>{esc(a["life_base"])}</b></div>'
            f'<span class="lb-gap" aria-hidden="true">+</span>'
            f'<div class="lb-up" style="flex:30"><b>{esc(a["life_up"])}</b><small>{esc(a["life_opts"])}</small></div></div></figure>')


def inventory(p):
    """Copper in each category, drawn to one scale and never summed."""
    a, l = p.c['la'], p.lang

    def bars(rows):
        out = ''
        for key, val, sk, cls in rows:
            v, u = STATS['la'][sk][l]
            out += (f'<li><span class="iv-l">{esc(a[key])}</span><span class="iv-t"><span class="iv-b {cls}" style="width:{val / 20.0 * 100:.1f}%"></span></span>'
                    f'<span class="iv-v">{esc(v)} <small>{esc(u)}</small></span></li>')
        return f'<ol class="inv">{out}</ol>'
    return (f'<h3>{esc(a["h_inventory"])}</h3>{bars([("inv_reserves", 10.217, "reserves", "iv-r")])}'
            f'<p class="iv-h">{esc(a["h_inv_res"])}</p>{bars([("inv_mi", 5.4, "mi", "iv-m"), ("inv_inf", 20.0, "inf", "iv-i")])}'
            f'<p class="note">{esc(a["inventory_note"])}</p>')


def aside_card(p):
    h = p.c['home']
    load = 'plain' if p.key in ('speaking', 'press') else False
    rows = [('card_role', 'card_role_v', 'mux-bio'), ('card_leads', 'card_leads_v', 'join'), ('card_also', 'card_also_v', 'gemera-ej,la-cobre26'),
            ('card_born', 'card_born_v', 'gbm'), ('card_based', 'card_based_v', ''), ('card_langs', 'card_langs_v', 'mux-bio'),
            ('card_honours', 'card_honours_v', 'fm-2024,fm-2025'), ('card_edu', 'card_edu_v', '')]
    dl = ''.join(f'<div><dt>{esc(h[a])}</dt><dd>{esc(h[b])}{p.tr(r)}</dd></div>' for a, b, r in rows)
    return f'''<aside class="ib">
<figure class="ib-p">{img(p, "portrait.jpg", h["card_photo_alt"], "69% 20%", eager=load, sizes="(min-width: 960px) 320px, 100vw")}<figcaption>{esc(h["card_photo_cap"])}</figcaption></figure>
<p class="ib-n">Michael Meding</p>
<dl>{dl}</dl>
<div class="ib-l"><a href="https://www.linkedin.com/in/michaelmeding" rel="me noopener">LinkedIn</a><a href="https://x.com/mmeding" rel="me noopener">X</a><a href="{p.link(key="press")}#kit">{esc(p.c["press"]["h_kit"])}</a></div>
<div class="ib-m"><span>{esc(h["card_contact"])}</span><b id="em">michael@meding.dev</b><button class="cp" type="button" data-copy="em" data-done="{esc(p.c["ui"]["copied"])}">{esc(p.c["ui"]["copy"])}</button></div>
</aside>'''


# ---------------------------------------------------------------- JSON-LD
QUOTES_SHOWN = [0, 3, 4, 6, 7, 9, 10, 13]
PERSON_ID = f'{SITE}/#person'
LA_ID = f'{SITE}/#los-azules'
MC_ID = f'{SITE}/#mcewen-copper'
SITE_ID = f'{SITE}/#website'


def person_node(l, full=True):
    h = C[l]['home']
    if not full:
        return {'@type': 'Person', '@id': PERSON_ID, 'name': 'Michael Meding', 'url': f'{SITE}/'}
    return {
        '@type': 'Person', '@id': PERSON_ID, 'name': 'Michael Meding', 'givenName': 'Michael', 'familyName': 'Meding',
        'alternateName': ['Mike Meding', 'Michael E. Meding', 'マイケル・メディング', '迈克尔·梅丁'],
        'url': f'{SITE}/', 'image': {'@type': 'ImageObject', 'url': f'{SITE}/img/michael-meding-headshot.jpg', 'width': 423, 'height': 423},
        'jobTitle': 'Managing Director', 'worksFor': {'@id': MC_ID},
        'description': strip_tokens(h['lede']),
        'email': 'michael@meding.dev', 'nationality': {'@type': 'Country', 'name': 'Germany'},
        'birthPlace': {'@type': 'Place', 'name': 'Düsseldorf, Germany'},
        'homeLocation': [{'@type': 'Place', 'name': 'San Juan, Argentina'}, {'@type': 'Place', 'name': 'Toronto, Canada'}],
        'knowsLanguage': ['de', 'en', 'es'],
        'knowsAbout': ['Copper mining', 'Mine development', 'Project finance', 'Mining finance', 'Heap leach and SX-EW', 'Mining policy in Argentina', 'RIGI', 'Social licence to operate', 'Artificial intelligence in mining'],
        'award': ['Mining Entrepreneur of the Year 2025 (Panorama Minero)', 'Mining Entrepreneur of the Year 2024 (Panorama Minero)', 'Diploma Migrante destacado 2024 (Dirección Nacional de Migraciones, Argentina)'],
        'hasOccupation': {'@type': 'Occupation', 'name': 'Mining executive', 'occupationLocation': {'@type': 'Country', 'name': 'Argentina'}},
        'memberOf': [
            {'@type': 'OrganizationRole', 'roleName': 'President', 'startDate': '2024', 'memberOf': {'@type': 'Organization', 'name': 'GEMERA (Grupo de Empresas Mineras Exploradoras de la República Argentina)'}},
            {'@type': 'OrganizationRole', 'roleName': 'Vice President', 'startDate': '2025', 'memberOf': {'@type': 'Organization', 'name': 'CAEM (Cámara Argentina de Empresarios Mineros)'}},
            {'@type': 'OrganizationRole', 'roleName': 'Board member', 'startDate': '2025', 'memberOf': {'@type': 'Organization', 'name': 'Cámara Minera de San Juan'}},
        ],
        'alumniOf': [{'@type': 'CollegeOrUniversity', 'name': n} for n in ('Ruhr-Universität Bochum', 'HHL Leipzig Graduate School of Management', 'Indiana University of Pennsylvania')],
        'sameAs': [
            'https://www.linkedin.com/in/michaelmeding', 'https://x.com/mmeding',
            'https://www.mcewenmining.com/about-us/management-team/management-details/default.aspx?ItemId=14f233db-6a66-4b48-b6d6-6ae6426ec645',
            'https://www.bloomberg.com/profile/person/22717063', 'https://github.com/mimeding',
        ],
        'mainEntityOfPage': f'{SITE}/',
    }


def org_node():
    return {
        '@type': 'Organization', '@id': MC_ID, 'name': 'McEwen Copper', 'legalName': 'McEwen Copper Inc.', 'foundingDate': '2021-07',
        'address': {'@type': 'PostalAddress', 'streetAddress': '150 King Street West', 'addressLocality': 'Toronto', 'addressRegion': 'ON', 'addressCountry': 'CA'},
        'parentOrganization': {'@type': 'Corporation', 'name': 'McEwen Inc.', 'tickerSymbol': ['NYSE: MUX', 'TSX: MUX'], 'url': 'https://www.mcewenmining.com/'},
        'subOrganization': {'@type': 'Organization', 'name': 'Andes Corporación Minera S.A.', 'address': {'@type': 'PostalAddress', 'addressRegion': 'San Juan', 'addressCountry': 'AR'}},
        'employee': {'@id': PERSON_ID},
        'url': 'https://www.mcewenmining.com/',
        'sameAs': ['https://www.linkedin.com/company/mcewencopper'],
    }


def place_node(l):
    return {
        '@type': 'Place', '@id': LA_ID, 'name': 'Los Azules copper project', 'alternateName': ['Proyecto Los Azules', 'Los Azules mine', 'ロス・アスレス', '洛斯阿苏莱斯'],
        'description': strip_tokens(C[l]['la']['lede']),
        'address': {'@type': 'PostalAddress', 'addressLocality': 'Calingasta', 'addressRegion': 'San Juan', 'addressCountry': 'AR'},
        'containedInPlace': {'@type': 'AdministrativeArea', 'name': 'San Juan Province, Argentina'},
        'url': f'{SITE}/{"" if l == "en" else l + "/"}los-azules/',
        'sameAs': ['https://en.wikipedia.org/wiki/Los_Azules_mine', 'https://www.wikidata.org/wiki/Q16999581', 'https://www.mcewenmining.com/operations/los-azules/default.aspx'],
    }


def scholarly_nodes():
    return [
        {'@type': 'ScholarlyArticle', '@id': 'https://doi.org/10.18623/rvd.v23.n1.3939', 'headline': 'The Legitimacy Trilemma: Strategic Communication, Crisis of Trust, and the Maintenance of the Social License to Operate in Large-Scale Mining in Latin America',
         'datePublished': '2026', 'isPartOf': {'@type': 'Periodical', 'name': 'Veredas do Direito'}, 'url': 'https://doi.org/10.18623/rvd.v23.n1.3939',
         'identifier': {'@type': 'PropertyValue', 'propertyID': 'DOI', 'value': '10.18623/rvd.v23.n1.3939'},
         'author': [{'@id': PERSON_ID}, {'@type': 'Person', 'name': 'M. B. Arias-Valle'}, {'@type': 'Person', 'name': 'A. A. Ocampo Abadía'}]},
        {'@type': 'ScholarlyArticle', '@id': 'https://doi.org/10.2139/ssrn.5407877', 'headline': 'Mapping the Knowledge Landscape of Social License to Operate in Mining: A Bibliometric Study',
         'datePublished': '2025', 'publisher': {'@type': 'Organization', 'name': 'SSRN'}, 'url': 'https://doi.org/10.2139/ssrn.5407877',
         'identifier': {'@type': 'PropertyValue', 'propertyID': 'DOI', 'value': '10.2139/ssrn.5407877'},
         'author': [{'@id': PERSON_ID}, {'@type': 'Person', 'name': 'M. B. Arias Valle'}, {'@type': 'Person', 'name': 'A. Ocampo Abadía'}]},
    ]


def website_node():
    return {'@type': 'WebSite', '@id': SITE_ID, 'url': f'{SITE}/', 'name': 'Michael Meding', 'inLanguage': [HREFLANG[x] for x in LANGS], 'publisher': {'@id': PERSON_ID}}


def faq_node(p, faq):
    return {'@type': 'FAQPage', '@id': p.url() + '#faq', 'inLanguage': HREFLANG[p.lang],
            'mainEntity': [{'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': strip_tokens(f['a'])}} for f in faq]}


def breadcrumb(p, name):
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Michael Meding', 'item': p.url(key='home')},
        {'@type': 'ListItem', 'position': 2, 'name': name, 'item': p.url()}]}


def webpage(p, typ, name, desc, extra=None):
    n = {'@type': typ, '@id': p.url() + '#page', 'url': p.url(), 'name': name, 'description': desc, 'inLanguage': HREFLANG[p.lang],
         'isPartOf': {'@id': SITE_ID}, 'dateModified': TODAY.isoformat(), 'author': {'@id': PERSON_ID},
         'primaryImageOfPage': {'@type': 'ImageObject', 'url': f'{SITE}/img/og-{p.lang}.jpg'}}
    if extra:
        n.update(extra)
    return n


def event_date(s):
    if s['month'] is None:
        return s['year']
    if s['day']:
        d = s['day'].split('–')[0]
        return f'{s["year"]}-{s["month"]:02d}-{int(d):02d}'
    return f'{s["year"]}-{s["month"]:02d}'


# ---------------------------------------------------------------- pages
def page_home(l):
    p = Page(l, 'home')
    c, h, ui = p.c, p.c['home'], p.c['ui']
    name_extra = ''
    if l == 'ja':
        name_extra = '<span class="h1-t">マイケル・メディング</span>'
    if l == 'zh':
        name_extra = '<span class="h1-t">迈克尔·梅丁</span>'
    sep = '／' if l == 'ja' else ' · '
    role_parts = h['roles'].split(sep)
    role1, role2 = role_parts[0].strip(), '<br>'.join(esc(x.strip()) for x in role_parts[1:])
    lede_html = p.t(h['hero_lede'])
    cred_html = p.t(h['hero_cred'])
    cta = (f'<p class="cta"><a class="btn btn-p" href="{p.link(key="la")}">{esc(ui["open_la"])}</a>'
           f'<a class="btn" href="{p.link(key="press")}#kit">{esc(c["press"]["h_kit"])}</a>'
           f'<a class="btn btn-t" href="https://www.linkedin.com/in/michaelmeding" rel="me noopener">LinkedIn</a></p>')
    photo = (f'<figure class="hp">{img(p, "new-york-2024.jpg", c["speaking"]["alt_ny"], "50% 35%", eager=True, sizes="(min-width: 860px) 45vw, 100vw")}'
             f'<figcaption>{esc(c["speaking"]["cap_ny"])}</figcaption></figure>')
    # milestone rail, drawn to scale from Jan 2022 to Dec 2030
    span = 108.0
    ticks = ''.join(f'<span class="rt" data-t="{y}" style="--x:{(y - 2022) * 12 / span * 100:.2f}%"></span>' for y in range(2022, 2031))
    pts = ''
    for i, (pos, lab) in enumerate(zip(RAIL_POS, h['rail'])):
        tgt = RAIL_TARGET[i]
        side = 'up' if i % 2 == 0 else 'dn'
        tg = paren(l, ui['target']) if tgt else ''
        end = ' end' if pos / span > 0.8 else ''
        pts += (f'<li class="rp {side}{" tgt" if tgt else ""}{end}" style="--x:{pos / span * 100:.2f}%">'
                f'<span class="rb"><span class="rd">{esc(RAIL_DATES[l][i])}</span><span class="rl">{esc(lab)}<small>{tg}</small></span></span></li>')
    today = f'<span class="rnow" data-t="{esc(h["rail_today"])}" style="--x:{RAIL_TODAY / span * 100:.2f}%"></span>'
    rail = (f'<div class="rail" aria-labelledby="rail-h"><p class="rail-h" id="rail-h">{esc(h["h_milestones"])}</p>'
            f'<div class="rail-t"><div class="rail-line" style="--now:{RAIL_TODAY / span * 100:.2f}%"></div>{ticks}{today}<ol>{pts}</ol></div></div>')
    stats_s = stats_html(p, "home", [("reserves", h["stat_reserves"] + "[[r:fs]]"), ("npv", h["stat_npv"] + "[[r:fs]]"), ("loan", h["stat_loan"] + "[[r:loan-pr]]"), ("rigi", h["stat_rigi"] + "[[r:rigi-ln]]"), ("placements", h["stat_placements"] + "[[r:mux-la]]")])
    prt = ''.join(f'<li><span>{esc(x["k"])}</span><b>{esc(x["v"])}</b>{p.tr(x["r"])}</li>' for x in h['partners'])
    partners = f'<div class="prt"><p class="rail-h">{esc(h["h_partners"])}</p><ul>{prt}</ul></div>'
    hero = f'''<section class="hero"><div class="wrap"><div class="hg">
<div class="ht">
<p class="kick">{esc(h["kicker"])}</p>
<h1><span class="h1-l">Michael Meding</span>{name_extra}</h1>
<p class="role"><b>{esc(role1)}</b><span>{role2}</span></p>
<p class="lead">{lede_html}</p>
<p class="cred">{cred_html}</p>
{cta}
</div>
{photo}
</div>
{rail}
{stats_s}
<p class="snote"><a href="{p.link(key="la")}#technical">{esc(h["stats_note"])}</a></p>
{partners}
</div></section>'''
    secs = []
    # latest financing (short quote here; full quote on the Los Azules page)
    lq = c['la']
    qtr = f'<p class="qt">{esc(lq["loan_quote_short_tr"])}<span class="qn">{paren(l, lq["loan_quote_note"])}</span></p>' if lq['loan_quote_short_tr'] else ''
    latest = (f'<p>{p.t(h["latest"])}</p><figure class="q q-lg"><blockquote lang="en" cite="{esc(REFS["loan-pr"]["url"])}">{esc(lq["loan_quote_short"])}</blockquote>{qtr}'
              f'<figcaption>{esc(h["latest_quote_attr"])}{p.cite(["loan-pr"])}</figcaption></figure>'
              f'<p class="more-l"><a href="{p.link(key="la")}#financing">{esc(h["latest_more"])} →</a></p>')
    secs.append(section('latest', esc(h['h_latest']), latest, 's s-hi s-first'))
    # overview
    diagram = (f'<figure class="egw egw-in"><figcaption>{esc(h["diagram_caption"])}</figcaption><div class="egs">'
               f'<img class="eg" src="{p.asset(f"img/diagram-{l}.svg")}" width="820" height="380" alt="{esc(h["diagram_alt"])}" loading="lazy"></div></figure>')
    secs.append(section('overview', esc(h['h_overview']), ''.join(f'<p>{p.t(x)}</p>' for x in h['overview']) + diagram))
    # capabilities
    caps = ''
    for cp in h['caps']:
        lis = ''.join(f'<li>{p.t(e)}</li>' for e in cp['e'])
        caps += f'<article class="cap"><h3>{esc(cp["t"])}</h3><p class="cap-c">{esc(cp["c"])}</p><ul>{lis}</ul></article>'
    secs.append(section('capabilities', esc(h['h_caps']), f'<p class="sub">{esc(h["caps_sub"])}</p><div class="caps">{caps}</div>'))
    # Los Azules brief
    secs.append(section('los-azules', esc(h['h_la']), f'<p>{p.t(h["la_brief"])}</p><p class="more-l"><a href="{p.link(key="la")}">{esc(ui["open_la"])} →</a></p>'))
    # milestones
    tl = ''
    for m in h['milestones']:
        cls = 't-n' if m.get('target') else 't-d'
        mon = h['mid_year'] if m.get('mid') else month_short(l, m['m'])
        tgt = (f'<span class="tg">（{esc(ui["target"])}）</span>' if l in ('ja', 'zh') else f' <span class="tg">({esc(ui["target"])})</span>') if m.get('target') else ''
        tl += f'<li class="{cls}"><span class="t-y">{m["y"]}</span><span class="t-m">{esc(mon)}</span><span class="t-t">{esc(m["t"])}{tgt}</span></li>'
    secs.append(section('milestones', esc(h['h_milestones']), f'<p class="sub">{p.t(h["milestones_sub"])}</p><ol class="tl">{tl}</ol>'))
    # honours
    figs = (f'<div class="figs2"><figure class="fig">{img(p, "entrepreneur-2025.jpg", h["honours_alt_1"], "56% 21%")}<figcaption>{esc(h["honours_cap_1"])}</figcaption></figure>'
            f'<figure class="fig">{img(p, "diploma-2024.jpg", h["honours_alt_2"], "45% 27%")}<figcaption>{esc(h["honours_cap_2"])}</figcaption></figure></div>')
    trs = ''
    for r in h['honours']:
        to = ui['to_personal'] if r['to'] == 'personal' else ui['to_la']
        trs += (f'<tr><td class="n" data-l="{esc(ui["th_year"])}">{r["y"]}</td><td data-l="{esc(ui["th_distinction"])}"><b>{esc(r["n"])}</b><br><small>{esc(r["d"])}</small> '
                f'<a class="ext" href="{esc(r["url"])}" rel="noopener">{esc(ui["source"])} ↗</a></td>'
                f'<td data-l="{esc(ui["th_by"])}">{esc(r["by"])}</td><td data-l="{esc(ui["th_to"])}">{esc(to)}</td></tr>')
    th = ''.join(f'<th scope="col">{esc(ui[k])}</th>' for k in ('th_year', 'th_distinction', 'th_by', 'th_to'))
    secs.append(section('honours', esc(h['h_honours']), figs + f'<div class="tw"><table class="tb stack"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'))
    # roles & career
    cur = ''.join(f'<li><span class="car-r">{esc(r["role"])}</span><b>{esc(r["o"])}</b><em>{esc(r["x"])}</em></li>' for r in h['current'])
    car = ''.join(f'<li><b>{esc(r["o"])}</b><span>{esc(r["d"])}</span><em>{esc(r["p"])}</em></li>' for r in h['career'])
    edu = ''.join(f'<li>{esc(e)}</li>' for e in h['education'])
    research = ('<ul class="edu"><li>Meding, M., Arias-Valle, M. B., &amp; Ocampo Abadía, A. A. (2026). “The Legitimacy Trilemma: Strategic Communication, Crisis of Trust, and the Maintenance of the Social License to Operate in Large-Scale Mining in Latin America.” <i>Veredas do Direito</i>, 23(1), e233939. '
                '<a href="https://doi.org/10.18623/rvd.v23.n1.3939" rel="noopener">doi:10.18623/rvd.v23.n1.3939</a></li>'
                '<li>Meding, M. E., Arias Valle, M. B., &amp; Ocampo Abadía, A. (2025). “Mapping the Knowledge Landscape of Social License to Operate in Mining: A Bibliometric Study.” SSRN preprint. '
                '<a href="https://doi.org/10.2139/ssrn.5407877" rel="noopener">doi:10.2139/ssrn.5407877</a></li></ul>')
    roles = (f'<h3>{esc(h["h_current"])}</h3><ol class="car cur">{cur}</ol><h3>{esc(h["h_career"])}</h3><ol class="car">{car}</ol>'
             f'<h3>{esc(h["h_education"])}</h3><ul class="edu">{edu}</ul><h3 id="research">{esc(h["h_research"])}</h3>{research}')
    secs.append(section('roles', esc(h['h_roles']), roles))
    # quotes
    qs = ''.join(quote_fig(p, i, X['quotes'][i]) for i in QUOTES_SHOWN)
    secs.append(section('quotes', esc(h['h_quotes']), f'<div class="qs">{qs}</div>'))
    # recent speaking & press
    rows = X['speaking'][:6]
    secs.append(section('stages', esc(h['h_sel_speaking']), f'<div class="tw">{speaking_rows(p, rows)}</div><p class="more-l"><a href="{p.link(key="speaking")}">{esc(ui["open_speaking"])} →</a></p>'.replace('id="sp"', 'id="sp-recent"')))
    secs.append(section('coverage', esc(h['h_sel_press']), press_items(p, X['press'][:6], 'pr-recent') + f'<p class="more-l"><a href="{p.link(key="press")}">{esc(ui["open_press"])} →</a></p>'))
    # faq
    faq = ''.join(f'<details class="faq"><summary>{esc(f["q"])}</summary><p>{p.t(f["a"])}</p></details>' for f in h['faq'])
    secs.append(section('faq', esc(h['h_faq']), faq))
    aside = aside_card(p)
    secs.append(refs_section(p))

    tocitems = [('latest', h['h_latest']), ('overview', h['h_overview']), ('capabilities', h['h_caps']), ('los-azules', h['h_la']),
                ('milestones', h['h_milestones']), ('honours', h['h_honours']), ('roles', h['h_roles']), ('quotes', h['h_quotes']),
                ('stages', h['h_sel_speaking']), ('coverage', h['h_sel_press']), ('faq', h['h_faq']), ('references', ui['refs'])]
    return p, hero, secs, aside, tocitems


def assemble(p, hero, secs, aside, tocitems, title, desc, jsonld, og_type='website'):
    body = ''.join(secs)
    return (head(p, title, desc, jsonld, og_type) + header(p) + '<main id="main">' + hero +
            f'<div class="wrap"><div class="grid{"" if tocitems else " nt"}">{toc(p, tocitems)}<article class="art">{body}</article>{aside}</div></div></main>' + footer(p))


def render_home(l):
    p, hero, secs, aside, tocitems = page_home(l)
    c = C[l]
    graph = [website_node(), person_node(l), org_node(), place_node(l), *scholarly_nodes(),
             webpage(p, 'ProfilePage', c['meta']['home_title'], c['meta']['home_desc'], {'mainEntity': {'@id': PERSON_ID}, 'about': [{'@id': PERSON_ID}, {'@id': LA_ID}, {'@id': MC_ID}]}),
             faq_node(p, c['home']['faq'])]
    jl = {'@context': 'https://schema.org', '@graph': graph}
    return p, assemble(p, hero, secs, aside, tocitems, c['meta']['home_title'], c['meta']['home_desc'], jl, 'profile')


def render_la(l):
    p = Page(l, 'la')
    c, a, ui = p.c, p.c['la'], p.c['ui']
    # hero citations first
    hero = f'''<section class="hero hero-s"><div class="wrap"><div class="hg">
<div class="ht">
<p class="kick">{esc(a["kicker"])}</p>
<h1>{esc(a["h1"])}</h1>
<p class="lead">{p.t(a["lede"])}</p>
</div>
<figure class="hp">{img(p, "site-delegations.jpg", a["fig_alt"], "50% 45%", eager=True, sizes="(min-width: 860px) 45vw, 100vw")}<figcaption>{esc(a["fig_cap"])}</figcaption></figure>
</div>
{stats_html(p, "la", [("reserves", a["stat_reserves"] + "[[r:fs]]"), ("output", a["stat_output"] + "[[r:fs]]"), ("capex", a["stat_capex"] + "[[r:fs]]"), ("npv", a["stat_npv"] + "[[r:fs]]"), ("irr", a["stat_irr"] + "[[r:fs]]")])}
<p class="snote"><a href="#technical">{esc(a["stats_note"])}</a></p>
<p class="hnote">{esc(a["la_notice"])}</p>
</div></section>'''
    secs = []
    secs.append(section('life', esc(a['h_life']), f'<p>{p.t(a["life_p"])}</p>{life_bar(p)}<p class="note">{esc(a["life_note"])} <a href="#technical">{esc(a["h_tech"])} ↓</a></p>', 's s-first'))
    secs.append(section('facts', esc(a['h_facts']), facts_table(p, a['facts'])))
    # reserves & resources
    def rtable(rows, unit):
        th = f'<tr><th scope="col">{esc(ui["th_category"])}</th><th scope="col" class="r">{esc(ui["th_tonnes"])}</th><th scope="col" class="r">{esc(ui["th_grade"])}</th><th scope="col" class="r">{esc(ui["th_contained"])}{f"（{esc(unit)}）" if l in ("ja", "zh") else f" ({esc(unit)})"}</th></tr>'
        trs = ''
        for key, t, g, cu in rows:
            b = key in ('res_total',)
            cell = (lambda s: f'<b>{s}</b>') if b else (lambda s: s)
            trs += (f'<tr><th scope="row">{cell(esc(a[key]))}</th><td class="n r">{cell(loc_num(l, t))}</td>'
                    f'<td class="n r">{cell(loc_num(l, g))}</td><td class="n r">{cell(loc_num(l, cu))}</td></tr>')
        return f'<div class="tw"><table class="tb num"><thead>{th}</thead><tbody>{trs}</tbody></table></div>'
    res = (f'<p class="sub">{p.t(a["reserves_intro"])}</p>{inventory(p)}<h3>{esc(a["h_res_table"])}</h3>{rtable(RES_TABLE["reserves"], a["unit_mlb"])}'
           f'<p class="note">{esc(a["res_note"])}</p><h3>{esc(a["h_resources_table"])}</h3>{rtable(RES_TABLE["resources"], a["unit_blb"])}'
           f'<p class="note">{esc(a["resources_note"])}</p><p class="note"><a href="#technical">{esc(a["h_tech"])} ↓</a></p>')
    secs.append(section('reserves', esc(a['h_reserves']), res))
    secs.append(section('economics', esc(a['h_econ']), facts_table(p, a['econ']) + f'<p class="note">{p.t(a["econ_note"])}</p>'))
    # financing
    qtr = f'<p class="qt">{esc(a["loan_quote_tr"])}<span class="qn">{paren(l, a["loan_quote_note"])}</span></p>' if a['loan_quote_tr'] else ''
    lenders = ''.join(f'<tr><th scope="row">{esc(r["k"])}</th><td class="n r">{esc(r["v"])}</td></tr>' for r in a['lenders'])
    fin = (f'<h3 id="loan">{esc(a["h_loan"])}</h3><p>{p.t(a["loan_intro"])}</p>{facts_table(p, a["loan_terms"])}'
           f'<div class="tw"><table class="tb num lend"><thead><tr><th scope="col">{esc(ui["th_lender"])}</th><th scope="col" class="r">{esc(ui["th_amount"])}</th></tr></thead><tbody>{lenders}</tbody></table></div>'
           f'<figure class="q q-lg"><blockquote lang="en" cite="{esc(REFS["loan-pr"]["url"])}">{esc(a["loan_quote"])}</blockquote>{qtr}<figcaption>{esc(a["loan_quote_attr"])}{p.cite(["loan-pr"])}</figcaption></figure>'
           f'<h3>{esc(a["h_fin_record"])}</h3>{facts_table(p, a["fin_record"])}')
    secs.append(section('financing', esc(a['h_fin']), fin, 's s-hi'))
    # McEwen Copper + shareholders
    sh = [('sh_mux', 46.3, 'o0'), ('sh_stellantis', 18.2, 'o1'), ('sh_nuton', 17.2, 'o2'), ('sh_rob', 13.0, 'o3'), ('sh_vsg', 3.0, 'o4'), ('sh_other', 2.3, 'o5')]
    pct = lambda v: loc_num(l, f'{v:.1f}') + ('％' if l == 'ja' else '%')
    bar = ''.join(f'<span class="{c_}" style="width:{v}%"><b>{pct(v)}</b></span>' for k, v, c_ in sh)
    leg = ''.join(f'<li><i class="{c_}"></i>{esc(a[k])} <b>{pct(v)}</b></li>' for k, v, c_ in sh)
    mc = (facts_table(p, a['mcewen']) + f'<h3>{esc(a["h_shareholders"])}</h3><div class="own" aria-hidden="true">{bar}</div><ul class="own-l">{leg}</ul>'
          f'<p class="note">{p.t(a["shareholders_src"])}</p>'
          f'<figure class="fig">{img(p, "ifc-2025.jpg", a["ifc_alt"], "64% 25%", sizes="(min-width: 960px) 780px, 100vw")}<figcaption>{esc(a["ifc_cap"])}</figcaption></figure>')
    secs.append(section('mcewen-copper', esc(a['h_mcewen']), mc))
    secs.append(section('argentina', esc(a['h_argentina']), '<ul class="ar">' + ''.join(f'<li>{p.t(x)}</li>' for x in a['argentina']) + '</ul>'))
    tn = f'<p class="note tnote">{esc(a["tech_translation_note"])}</p>' if a['tech_translation_note'] else ''
    tech = ''.join(f'<p>{p.t(a[k])}</p>' for k in ('tech_p1', 'tech_p2', 'tech_p3', 'tech_p4')) + tn
    secs.append(section('technical', esc(a['h_tech']), tech, 's s-legal'))
    faq = ''.join(f'<details class="faq"><summary>{esc(f["q"])}</summary><p>{p.t(f["a"])}</p></details>' for f in a['faq'])
    secs.append(section('faq', esc(a['h_faq']), faq))
    aside = aside_card(p)
    secs.append(refs_section(p))
    tocitems = [('life', a['h_life']), ('facts', a['h_facts']), ('reserves', a['h_reserves']), ('economics', a['h_econ']), ('financing', a['h_fin']), ('mcewen-copper', a['h_mcewen']),
                ('argentina', a['h_argentina']), ('technical', a['h_tech']), ('faq', a['h_faq']), ('references', ui['refs'])]
    graph = [website_node(), person_node(l, False), org_node(), place_node(l),
             webpage(p, 'WebPage', c['meta']['la_title'], c['meta']['la_desc'], {'about': [{'@id': LA_ID}, {'@id': MC_ID}], 'mainEntity': {'@id': LA_ID}, 'mentions': {'@id': PERSON_ID}}),
             faq_node(p, a['faq']), breadcrumb(p, ui['nav_la'])]
    jl = {'@context': 'https://schema.org', '@graph': graph}
    return p, assemble(p, hero, secs, aside, tocitems, c['meta']['la_title'], c['meta']['la_desc'], jl)


def render_speaking(l):
    p = Page(l, 'speaking')
    c, s, ui = p.c, p.c['speaking'], p.c['ui']
    cta = esc(s['cta']).replace('michael@meding.dev', '<a href="mailto:michael@meding.dev">michael@meding.dev</a>')
    hero = f'<section class="hero hero-s"><div class="wrap"><h1>{esc(s["h1"])}</h1><p class="lead">{esc(s["sub"])}</p><p class="cred">{cta}</p></div></section>'
    figs = (f'<div class="figs2"><figure class="fig">{img(p, "new-york-2024.jpg", s["alt_ny"], "74% 32%", eager=True)}<figcaption>{esc(s["cap_ny"])}</figcaption></figure>'
            f'<figure class="fig">{img(p, "washington-2026-colour.jpg", s["alt_dc"], "71% 28%", eager="plain")}<figcaption>{esc(s["cap_dc"])}</figcaption></figure></div>')
    years = ['2026', '2025', '2024', '2023', '2022']
    cnt = {y: sum(1 for r in X['speaking'] if r['year'] == y) for y in years}
    filt = (f'<div class="filt" data-filter-for="sp"><button type="button" data-f="all" aria-pressed="true">{esc(ui["all"])} <small>{len(X["speaking"])}</small></button>' +
            ''.join(f'<button type="button" data-f="{y}" aria-pressed="false">{y} <small>{cnt[y]}</small></button>' for y in years) + '</div>')
    body = figs + filt + f'<div class="tw">{speaking_rows(p, X["speaking"])}</div>'
    secs = [f'<section id="all" class="s s-first">{body}</section>']
    aside = aside_card(p)
    secs.append(refs_section(p))
    items = []
    for i, r in enumerate(X['speaking'], 1):
        virtual = 'irtual' in r['city']
        ev = {'@type': 'Event', 'name': r['event'], 'description': C['en']['speaking']['roles'][r['id']],
              'eventAttendanceMode': 'https://schema.org/OnlineEventAttendanceMode' if virtual else 'https://schema.org/OfflineEventAttendanceMode',
              'location': {'@type': 'VirtualLocation', 'url': f'{SITE}/speaking/'} if virtual else {'@type': 'Place', 'name': r['city'], 'address': {'@type': 'PostalAddress', 'addressLocality': r['city'].split(',')[0].strip()}},
              'performer': {'@id': PERSON_ID}}
        d = event_date(r)
        if len(d) == 10:  # full dates only
            ev['startDate'] = d
        if r['upcoming']:
            ev['eventStatus'] = 'https://schema.org/EventScheduled'
        items.append({'@type': 'ListItem', 'position': i, 'item': ev})
    graph = [website_node(), person_node(l, False),
             webpage(p, 'CollectionPage', c['meta']['speaking_title'], c['meta']['speaking_desc'], {'about': {'@id': PERSON_ID}, 'mainEntity': {'@type': 'ItemList', 'name': 'Speaking engagements 2022–2026', 'numberOfItems': len(items), 'itemListElement': items}}),
             breadcrumb(p, ui['nav_speaking'])]
    jl = {'@context': 'https://schema.org', '@graph': graph}
    return p, assemble(p, hero, secs, aside, [], c['meta']['speaking_title'], c['meta']['speaking_desc'], jl)


def render_press(l):
    p = Page(l, 'press')
    c, pr, ui = p.c, p.c['press'], p.c['ui']
    hero = f'<section class="hero hero-s"><div class="wrap"><h1>{esc(pr["h1"])}</h1><p class="lead">{esc(pr["sub"])}</p></div></section>'
    secs = []
    kit = (f'<p class="sub">{esc(pr["kit_sub"])}</p>'
           f'<h3>{esc(pr["h_bio_short"])}</h3><div class="bio" id="bio-s" lang="{HTML_LANG[l]}"><p>{esc(pr["bio_short"])}</p></div><button class="cp" type="button" data-copy="bio-s" data-done="{esc(ui["copied"])}">{esc(ui["copy"])}</button>'
           f'<h3>{esc(pr["h_bio_long"])}</h3><div class="bio" id="bio-l" lang="{HTML_LANG[l]}"><p>{esc(pr["bio_long"])}</p></div><button class="cp" type="button" data-copy="bio-l" data-done="{esc(ui["copied"])}">{esc(ui["copy"])}</button>'
           f'<h3>{esc(pr["h_photos"])}</h3><ul class="kitp">'
           f'<li><img src="{p.asset("img/michael-meding-headshot.jpg")}" alt="Michael Meding" width="423" height="423" loading="lazy"><span>{esc(pr["photo_headshot"])}</span><a href="{p.asset("img/michael-meding-headshot.jpg")}" download>{esc(pr["download"])}</a></li>'
           f'<li><img src="{p.asset("img/portrait-800.jpg")}" alt="{esc(c["home"]["card_photo_alt"])}" width="800" height="533" loading="lazy"><span>{esc(pr["photo_stage"])}</span><a href="{p.asset("img/portrait.jpg")}" download>{esc(pr["download"])}</a></li>'
           f'<li><img src="{p.asset("img/washington-2026-colour-800.jpg")}" alt="{esc(c["speaking"]["alt_dc"])}" width="800" height="534" loading="lazy"><span>{esc(pr["photo_dc"])}</span><a href="{p.asset("img/washington-2026-colour.jpg")}" download>{esc(pr["download"])}</a></li></ul>'
           f'<h3>{esc(pr["h_data"])}</h3><p>{esc(pr["data_p"])}</p><ul class="mfiles"><li><a href="{p.asset("llms.txt")}">{esc(pr["data_llms"])}</a> · <a href="{p.asset("llms-full.txt")}">llms-full.txt</a></li><li><a href="{p.asset("facts.json")}">{esc(pr["data_facts"])}</a></li></ul>'
           f'<p class="kitc">{esc(pr["contact"])}: <a href="mailto:michael@meding.dev">michael@meding.dev</a></p>')
    secs.append(section('kit', esc(pr['h_kit']), kit, 's s-first'))
    vids = [it for it in X['press'] if 'video' in it['cats']]
    secs.append(section('video', esc(pr['h_video']), press_items(p, vids, 'pr-video')))
    cats = [('all', ui['all'], len(X['press'])), ('ar', ui['cat_ar'], 0), ('intl', ui['cat_intl'], 0), ('de', ui['cat_de'], 0), ('video', ui['cat_video'], 0)]
    cats = [(k, lab, n if k == 'all' else sum(1 for it in X['press'] if k in it['cats'])) for k, lab, n in cats]
    filt = '<div class="filt" data-filter-for="pr">' + ''.join(f'<button type="button" data-f="{k}" aria-pressed="{str(k == "all").lower()}">{esc(lab)} <small>{n}</small></button>' for k, lab, n in cats) + '</div>'
    secs.append(section('coverage', esc(pr['h_coverage']), filt + press_items(p, X['press'])))
    aside = aside_card(p)
    secs.append(refs_section(p))
    tocitems = [('kit', pr['h_kit']), ('video', pr['h_video']), ('coverage', pr['h_coverage']), ('references', ui['refs'])]
    items = [{'@type': 'ListItem', 'position': i, 'item': {'@type': 'NewsArticle', 'headline': it['headline'], 'url': it['url'], 'datePublished': it['iso'],
                                                          'inLanguage': it['lang'] or 'es', 'publisher': {'@type': 'Organization', 'name': it['outlet']}, 'about': {'@id': PERSON_ID}}}
             for i, it in enumerate(X['press'], 1)]
    graph = [website_node(), person_node(l, False),
             webpage(p, 'CollectionPage', c['meta']['press_title'], c['meta']['press_desc'], {'about': {'@id': PERSON_ID}, 'mainEntity': {'@type': 'ItemList', 'name': 'Press coverage', 'numberOfItems': len(items), 'itemListElement': items}}),
             breadcrumb(p, ui['nav_press'])]
    jl = {'@context': 'https://schema.org', '@graph': graph}
    return p, assemble(p, hero, secs, aside, tocitems, c['meta']['press_title'], c['meta']['press_desc'], jl)


def render_404():
    en = C['en']
    blocks = ''
    for l in LANGS:
        u = C[l]['ui']
        base = '/' if l == 'en' else f'/{l}/'
        blocks += (f'<section lang="{HTML_LANG[l]}"><h2>{esc(u["notfound_h1"])}</h2><p>{esc(u["notfound_p"])}</p>'
                   f'<p><a href="{base}">{esc(u["nav_home"])}</a> · <a href="{base}los-azules/">{esc(u["nav_la"])}</a> · '
                   f'<a href="{base}speaking/">{esc(u["nav_speaking"])}</a> · <a href="{base}press/">{esc(u["nav_press"])}</a></p></section>')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(en["meta"]["notfound_title"])}</title><meta name="robots" content="noindex">
<link rel="icon" href="/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/site.css"></head>
<body><header class="bar"><div class="in"><a class="brand" href="/">Michael Meding</a></div></header>
<main id="main" class="wrap nf">{blocks}</main></body></html>
'''


# ---------------------------------------------------------------- machine-readable files
def llms_full_txt():
    e = C['en']
    h, a = e['home'], e['la']

    def src(s):
        keys = [k for m in re.finditer(r'\[\[r:([^\]]+)\]\]', s) for k in m.group(1).split(',')]
        links = ', '.join(f'[{REFS[k]["publisher"]}]({REFS[k]["url"]})' for k in dict.fromkeys(keys))
        return strip_tokens(s) + (f' (sources: {links})' if links else '')

    lines = ['# Michael Meding (full text)', '', '> ' + strip_tokens(h['lede']), '',
             f'Full text of meding.dev in English: verified public facts about Michael Meding, the Los Azules copper project and McEwen Copper, with a source link for each. Reviewed {long_date("en", TODAY)}. Short version: {SITE}/llms.txt. Structured form: {SITE}/facts.json', '',
             NOTICE, '',
             '## Pages', '']
    for l in LANGS:
        pre = f'{SITE}/' + ('' if l == 'en' else f'{l}/')
        lines.append(f'- {C[l]["meta"]["lang_name"]}: [Profile]({pre}), [Los Azules]({pre}los-azules/), [Speaking]({pre}speaking/), [Press and press kit]({pre}press/)')
    lines += ['', '## Michael Meding', '']
    lines += ['- ' + src(x) for x in h['overview']]
    lines += ['', '## Latest: US$240 million term loan (27 August 2026)', '', '- ' + src(a['loan_intro'])]
    lines += [f'- {r["k"]}: {r["v"]}' for r in a['loan_terms']]
    lines += [f'- Lender: {r["k"]}, {r["v"]}' for r in a['lenders']]
    lines += [f'- Statement by Michael Meding, Managing Director of McEwen Copper: “{a["loan_quote"]}” (source: [McEwen Inc.]({REFS["loan-pr"]["url"]}))']
    lines += ['', '## Capabilities, with evidence', '']
    for cp in h['caps']:
        lines.append(f'- {cp["t"]}: {cp["c"]}')
        lines += [f'  - {src(x)}' for x in cp['e']]
    lines += ['', '## Los Azules', '', '- ' + src(a['lede']), '- ' + src(a['life_p']), '- ' + a['life_note']]
    lines += [f'- {r["k"]}: {src(r["v"] + "[[r:" + r["r"] + "]]")}' for r in a['facts']]
    lines += ['', '### Mineral reserves and resources (feasibility study, effective 3 September 2025)', '',
              '- Proven: 229.9 Mt at 0.683% Cu, 3,463 M lb Cu',
              '- Probable: 793.2 Mt at 0.386% Cu, 6,754 M lb Cu',
              '- Total proven and probable: 1,023.1 Mt at 0.453% Cu, 10,217 M lb Cu (copper price US$4.25/lb)',
              '- Measured and indicated, exclusive of reserves: 965.5 Mt at 0.255% Cu, 5.4 B lb Cu',
              '- Inferred, exclusive of reserves: 4,239.3 Mt at 0.214% Cu, 20.0 B lb Cu (resource copper price US$4.80/lb)',
              f'- Source: [McEwen Inc., 7 October 2025]({REFS["fs"]["url"]}); [S-K 1300 Technical Report Summary]({REFS["trs"]["url"]})']
    lines += ['', '### Technical information, qualified persons and cautionary notes', ''] + [strip_tokens(a[k]) + '\n' for k in ('tech_p1', 'tech_p2', 'tech_p3', 'tech_p4')]
    lines += ['### Feasibility study economics (base case)', ''] + [f'- {r["k"]}: {r["v"]}' for r in a['econ']]
    lines += ['', '### Financing record', ''] + [f'- {r["k"]}: {src(r["v"] + "[[r:" + r["r"] + "]]")}' for r in a['fin_record']]
    lines += ['', '### McEwen Copper', ''] + [f'- {r["k"]}: {src(r["v"] + "[[r:" + r["r"] + "]]")}' for r in a['mcewen']]
    lines += ['- Shareholders: McEwen Inc. 46.3%, Stellantis 18.2%, Nuton/Rio Tinto 17.2%, Rob McEwen 13.0%, Victor Smorgon Group 3.0%, others 2.3% (source: [McEwen Inc.](' + REFS['mux-la']['url'] + '))']
    lines += ['', "## Argentina's copper moment", ''] + ['- ' + src(x) for x in a['argentina']]
    lines += ['', '## Honours', ''] + [f'- {r["y"]}: {r["n"]}, {r["by"]}. {r["d"]} ({r["url"]})' for r in h['honours']]
    lines += ['', '## Roles', ''] + [f'- {r["role"]}, {r["o"]}' + (f' ({r["x"]})' if r['x'] else '') for r in h['current']]
    lines += ['', '## Career', ''] + [f'- {r["o"]}: {r["d"]} ({r["p"]})' for r in h['career']]
    lines += ['', '## Education', ''] + [f'- {x}' for x in h['education']]
    lines += ['', '## Research', '', '- Meding, M., Arias-Valle, M. B., & Ocampo Abadía, A. A. (2026). The Legitimacy Trilemma. Veredas do Direito, 23(1), e233939. https://doi.org/10.18623/rvd.v23.n1.3939',
              '- Meding, M. E., Arias Valle, M. B., & Ocampo Abadía, A. (2025). Mapping the Knowledge Landscape of Social License to Operate in Mining: A Bibliometric Study. SSRN. https://doi.org/10.2139/ssrn.5407877']
    lines += ['', '## Questions and answers', '']
    for f in h['faq'] + a['faq']:
        lines += [f'### {f["q"]}', '', src(f['a']), '']
    past = sum(1 for x in X['speaking'] if not x['upcoming'])
    lines += [f'## Speaking ({past} appearances since 2022, plus {len(X["speaking"]) - past} confirmed)', '']
    for s in X['speaking']:
        lines.append(f'- {event_date(s)}: {s["event"]}, {s["city"]}. {C["en"]["speaking"]["roles"][s["id"]]}' + (' (upcoming)' if s['upcoming'] else ''))
    lines += ['', '## Press coverage', ''] + [f'- {it["iso"]}, {it["outlet"]}: [{it["headline"]}]({it["url"]})' for it in X['press']]
    lines += ['', '## Contact', '', '- Press: michael@meding.dev', '- LinkedIn: https://www.linkedin.com/in/michaelmeding', '- X: https://x.com/mmeding', '']
    return '\n'.join(lines)


NOTICE = ('Notice: meding.dev is the personal website of Michael Meding. It is not issued by McEwen Inc. or McEwen Copper and is not an offer or '
          'solicitation to buy or sell securities. Official disclosure: https://www.mcewenmining.com/, SEDAR+ and EDGAR. Feasibility study figures are from '
          'the NI 43-101 / S-K 1300 technical reports; targets and upside cases are forward-looking and may not be achieved.')


def llms_txt():
    e = C['en']
    h, a = e['home'], e['la']
    lines = ['# Michael Meding', '', '> ' + strip_tokens(h['lede']), '', NOTICE, '',
             f'Reviewed {long_date("en", TODAY)}. Full text: {SITE}/llms-full.txt. Structured facts with sources: {SITE}/facts.json', '',
             '## Key facts', '',
             '- Role: Managing Director, McEwen Copper; President and General Manager, Andes Corporación Minera; leads the Los Azules copper project (San Juan, Argentina) since February 2022.',
             f'- Los Azules feasibility study (effective 3 September 2025): proven and probable reserves 1,023.1 Mt at 0.453% Cu (10.2 billion lb Cu); 21-year mine life; after-tax NPV8 US$2.9 billion and IRR 19.8% at US$4.35/lb; initial capital US$3.17 billion. Source: {REFS["fs"]["url"]}',
             '- Resources exclusive of reserves: measured and indicated 5.4 billion lb Cu; inferred 20.0 billion lb Cu. Categories must not be added together; inferred resources are too speculative to have economic considerations applied.',
             f'- First copper project approved under Argentina\'s RIGI investment regime (Resolución 1553/2025, published 14 October 2025). Source: {REFS["rigi-bo"]["url"]}',
             f'- US$240 million senior secured term loan closed 27 August 2026. Source: {REFS["loan-pr"]["url"]}',
             '- Honours: Mining Entrepreneur of the Year 2024 and 2025 (Panorama Minero). President of GEMERA since 2024.', '',
             '## Pages', '']
    for l in LANGS:
        pre = f'{SITE}/' + ('' if l == 'en' else f'{l}/')
        lines.append(f'- {C[l]["meta"]["lang_name"]}: [Profile]({pre}), [Los Azules]({pre}los-azules/), [Speaking]({pre}speaking/), [Press and press kit]({pre}press/)')
    lines += ['', '## Machine-readable', '', f'- [llms-full.txt]({SITE}/llms-full.txt): full English text with sources',
              f'- [facts.json]({SITE}/facts.json): structured facts, FAQ in five languages, speaking and press lists', f'- [sitemap.xml]({SITE}/sitemap.xml)', '',
              '## Official sources', '', f'- [McEwen Inc., Los Azules]({REFS["mux-la"]["url"]})', f'- [Feasibility study announcement]({REFS["fs"]["url"]})',
              f'- [S-K 1300 technical report summary]({REFS["trs"]["url"]})', f'- [Term loan announcement]({REFS["loan-pr"]["url"]})', '',
              '## Contact', '', '- michael@meding.dev', '- https://www.linkedin.com/in/michaelmeding', '- https://x.com/mmeding', '']
    return '\n'.join(lines)


def facts_json():
    out = {'reviewed': TODAY.isoformat(), 'site': f'{SITE}/', 'person': {'name': 'Michael Meding', 'alternate_names': ['Mike Meding', 'マイケル・メディング', '迈克尔·梅丁'],
           'role': 'Managing Director, McEwen Copper', 'leads': 'Los Azules copper project, San Juan, Argentina, since February 2022',
           'nationality': 'German', 'born': 'Düsseldorf', 'based': ['San Juan, Argentina', 'Toronto, Canada'], 'languages': ['de', 'en', 'es'],
           'roles': [{'role': r['role'], 'organisation': r['o'], 'detail': r['x']} for r in C['en']['home']['current']],
           'career': [{'organisation': r['o'], 'role': r['d'], 'period': r['p']} for r in C['en']['home']['career']],
           'education': C['en']['home']['education'],
           'email': 'michael@meding.dev', 'links': {'linkedin': 'https://www.linkedin.com/in/michaelmeding', 'x': 'https://x.com/mmeding', 'bloomberg': 'https://www.bloomberg.com/profile/person/22717063'}},
           'summary': {l: strip_tokens(C[l]['home']['lede']) for l in LANGS},
           'los_azules_summary': {l: strip_tokens(C[l]['la']['lede']) for l in LANGS},
           'los_azules': {
               'location': 'Calingasta, San Juan, Argentina; about 3,500 m above sea level; 6 km east of the Chilean border',
               'owner': 'McEwen Copper Inc. (through Andes Corporación Minera S.A.)',
               'feasibility_study': {'announced': '2025-10-07', 'effective_date': '2025-09-03',
                                     'reserves': {'proven': {'mt': 229.9, 'cu_pct': 0.683, 'cu_mlb': 3463}, 'probable': {'mt': 793.2, 'cu_pct': 0.386, 'cu_mlb': 6754},
                                                  'total': {'mt': 1023.1, 'cu_pct': 0.453, 'cu_mlb': 10217}, 'copper_price_usd_lb': 4.25},
                                     'resources_exclusive_of_reserves': {'measured_indicated': {'mt': 965.5, 'cu_pct': 0.255, 'cu_blb': 5.4}, 'inferred': {'mt': 4239.3, 'cu_pct': 0.214, 'cu_blb': 20.0}, 'copper_price_usd_lb': 4.80},
                                     'mine_life_years_base_case': 21,
                                     'upside_case': {'potential_extension': '30 years or more', 'routes': ["Rio Tinto's Nuton leaching technology", 'a conventional concentrator (also recovering gold and silver)'],
                                                     'status': 'potential upside; not part of the base-case mine plan or economics'},
                                     'economics': {'initial_capex_usd_m': 3168, 'npv8_after_tax_usd_m': 2940, 'irr_after_tax_pct': 19.8, 'payback_years': 3.9, 'mine_life_years': 21,
                                                   'copper_price_usd_lb': 4.35, 'c1_usd_lb': 1.71, 'aisc_usd_lb': 2.11, 'output_t_y_years_1_5': 204800, 'output_t_y_lom': 148200},
                                     'qualified_persons': ['James L. Sorensen, FAusIMM (project execution)', 'David Tyler, SME RM (McEwen information)', 'Michael McGlynn, SME RM (metallurgy)',
                                                           'Jeff Sullivan, FAusIMM (mineral resources)', 'Gordon Zurowski, P.Eng. (mineral reserves)', 'Steve Pozder, P.E. (financial modelling)'],
                                     'sources': [REFS['fs']['url'], REFS['trs']['url']]},
               'rigi': {'resolution': 'Resolución 1553/2025', 'published': '2025-10-14', 'investment_plan_usd_m': 2672, 'first_copper_project': True, 'source': REFS['rigi-bo']['url']},
               'environmental_permit': {'granted': '2024-12', 'source': REFS['eia']['url']},
               'targets': {'final_investment_decision': 'mid-2027', 'first_commercial_cathode': 2030, 'source': REFS['loan-pr']['url']},
               'shareholders_pct': {'McEwen Inc.': 46.3, 'Stellantis': 18.2, 'Nuton/Rio Tinto': 17.2, 'Rob McEwen': 13.0, 'Victor Smorgon Group': 3.0, 'Others': 2.3},
           },
           'term_loan_2026': {'closed': '2026-08-27', 'amount_usd_m': 240, 'type': 'senior secured term loan', 'term_years': 4, 'interest_pct': 12.0, 'interest_paid': 'monthly',
                              'lenders_usd_m': {'Sprott Natural Resource Investment Partners': 112, 'Rob McEwen': 85, 'Other lenders': 43},
                              'warrants': '15,000 five-year McEwen Copper share purchase warrants per US$1 million of principal, exercise price US$40',
                              'use_of_proceeds': 'Engineering and early works at Los Azules; general corporate purposes',
                              'quote_meding': C['en']['la']['loan_quote'], 'source': REFS['loan-pr']['url']},
           'faq': {l: [{'q': f['q'], 'a': strip_tokens(f['a'])} for f in C[l]['home']['faq'] + C[l]['la']['faq']] for l in LANGS},
           'honours': [{'year': r['y'], 'name': r['n'], 'by': r['by'], 'source': r['url']} for r in C['en']['home']['honours']],
           'speaking': [{'date': event_date(s), 'event': s['event'], 'city': s['city'], 'role': C['en']['speaking']['roles'][s['id']], 'upcoming': s['upcoming']} for s in X['speaking']],
           'press': [{'date': it['iso'], 'outlet': it['outlet'], 'headline': it['headline'], 'url': it['url'], 'language': it['lang']} for it in X['press']],
           'references': REFS,
           'notice': NOTICE,
           'cautionary_notes': {'mineral_resources': strip_tokens(C['en']['la']['tech_p3']), 'forward_looking': strip_tokens(C['en']['la']['tech_p4']),
                                'upside_case': C['en']['la']['life_note'], 'inventory': C['en']['la']['inventory_note']},
           'disclaimer': C['en']['ui']['footer_disclaimer']}
    return json.dumps(out, ensure_ascii=False, indent=1)


SITEMAP_IMGS = {'home': ['new-york-2024.jpg', 'portrait.jpg', 'michael-meding-headshot.jpg', 'entrepreneur-2025.jpg', 'diploma-2024.jpg'],
                'la': ['site-delegations.jpg', 'ifc-2025.jpg'], 'speaking': ['new-york-2024.jpg', 'washington-2026-colour.jpg'],
                'press': ['michael-meding-headshot.jpg', 'portrait.jpg', 'washington-2026-colour.jpg']}


def sitemap():
    urls = ''
    p = Page('en', 'home')
    for k in PAGES:
        for l in LANGS:
            loc = p.url(l, k)
            alts = ''.join(f'<xhtml:link rel="alternate" hreflang="{HREFLANG[x]}" href="{p.url(x, k)}"/>' for x in LANGS)
            alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{p.url("en", k)}"/>'
            imgs = ''.join(f'<image:image><image:loc>{SITE}/img/{f}</image:loc></image:image>' for f in SITEMAP_IMGS[k])
            urls += f'<url><loc>{loc}</loc><lastmod>{TODAY.isoformat()}</lastmod>{alts}{imgs}</url>\n'
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
            'xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n' + urls + '</urlset>\n')


# ---------------------------------------------------------------- write
def write(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(text)


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(ASSETS, OUT)
    for l in LANGS:
        for fn in (render_home, render_la, render_speaking, render_press):
            p, doc = fn(l)
            write(p.path() + 'index.html', doc)
    write('404.html', render_404())
    write('llms.txt', llms_txt())
    write('llms-full.txt', llms_full_txt())
    write('facts.json', facts_json())
    write('sitemap.xml', sitemap())
    print('built', sum(len(fs) for _, _, fs in os.walk(OUT)), 'files into', OUT, '(preview links)' if PREVIEW else '')


if __name__ == '__main__':
    main()
