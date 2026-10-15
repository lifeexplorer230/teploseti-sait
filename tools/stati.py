#!/usr/bin/env python3
"""Сборка раздела «Статьи»: stati/_src/*.md -> stati/<slug>/index.html, stati/index.html,
sitemap.xml, robots.txt. Заодно синхронизирует мету robots на главной.

Статья — markdown с шапкой:
    ---
    title: Заголовок для поиска (до ~65 знаков)
    description: Описание для выдачи (до ~160 знаков)
    date: 2026-10-15
    h1: Заголовок на странице (если не задан — title)
    lead: Вводный абзац под заголовком
    related: slug1, slug2  # «Ещё по теме» (иначе — свежие)
    draft: true          # черновик не публикуется
    ---
Имя файла = адрес: stati/_src/opressovka-teplotrassy.md -> /stati/opressovka-teplotrassy/

Запуск: python3 tools/stati.py
Индексация включается одним флагом "index" в tools/site.json.
Там же: номер счётчика Метрики (metrika) и коды подтверждения Вебмастера и Search Console.
"""
import html
import json
import re
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'stati' / '_src'
OUT = ROOT / 'stati'
CFG = json.loads((ROOT / 'tools' / 'site.json').read_text())
BASE = CFG['base'].rstrip('/')
ROBOTS = 'index, follow' if CFG['index'] else 'noindex, nofollow'
MES = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа',
       'сентября', 'октября', 'ноября', 'декабря']

STYLE = """
body{margin:0;background:#FFFFFF;font-family:'Manrope',system-ui,sans-serif;color:#16202B;font-size:17px;line-height:1.6}
*{box-sizing:border-box}
a{color:#C4501A}a:hover{color:#9E3F12}
.wrap{max-width:1200px;margin:0 auto;padding:0 24px}
.hdr{position:sticky;top:0;z-index:10;background:rgba(255,255,255,0.96);border-bottom:1px solid #E3E7EB}
.hdr .wrap{padding-top:14px;padding-bottom:14px;display:flex;align-items:center;gap:24px;flex-wrap:wrap}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;color:#16202B;font-weight:800;font-size:19px}
.nav{display:flex;gap:22px;font-size:15px;font-weight:600;margin-left:8px}
.nav a{color:#3A4552;text-decoration:none}.nav a.on{color:#C4501A}
.hdr-r{margin-left:auto;display:flex;align-items:center;gap:18px}
.ph{text-align:right;line-height:1.3}.ph a{color:#16202B;font-weight:800;font-size:18px;text-decoration:none}.ph div{font-size:13px;color:#5A6573}
.btn{background:#C4501A;color:#FFFFFF !important;text-decoration:none;font-weight:700;font-size:15px;padding:12px 18px;border-radius:8px;min-height:44px;display:inline-flex;align-items:center}
.btn:hover{background:#9E3F12}
.crumbs{font-size:14px;color:#5A6573;padding-top:28px}.crumbs a{color:#5A6573}
.art{max-width:760px;margin:0 auto;padding:0 24px 24px}
.art h1{margin:14px 0 0;font-size:clamp(30px,4vw,44px);line-height:1.12;font-weight:800;letter-spacing:-0.02em}
.meta{margin-top:14px;font-family:'IBM Plex Mono',monospace;font-size:13px;color:#5A6573;letter-spacing:0.04em}
.lead{margin-top:22px;font-size:20px;color:#3A4552}
.body h2{margin:44px 0 0;font-size:28px;line-height:1.2;font-weight:800;letter-spacing:-0.01em}
.body h3{margin:30px 0 0;font-size:21px;font-weight:700}
.body p,.body ul,.body ol{margin:16px 0 0}
.body li{margin-top:6px}
.body table{border-collapse:collapse;width:100%;margin-top:18px;font-size:15px;display:block;overflow-x:auto}
.body th,.body td{border:1px solid #E3E7EB;padding:10px 12px;text-align:left;vertical-align:top}
.body th{background:#F3F5F7}
.body blockquote{margin:22px 0 0;padding:14px 18px;background:#FFF3EC;border-left:4px solid #C4501A;border-radius:0 8px 8px 0}
.body blockquote p{margin:0}
.body img{max-width:100%;border-radius:12px}
.cta{margin:48px 0 0;background:#0F2235;color:#FFFFFF;border-radius:16px;padding:32px}
.cta h2{margin:0;font-size:24px;line-height:1.25}.cta p{margin:12px 0 0;color:#C9D3DD}
.cta .row{display:flex;flex-wrap:wrap;gap:12px;margin-top:22px}
.cta .b2{border:1.5px solid #6B7C8E;color:#FFFFFF;text-decoration:none;font-weight:700;padding:12px 18px;border-radius:8px;min-height:44px;display:inline-flex;align-items:center}
.more{max-width:760px;margin:0 auto;padding:40px 24px 72px}
.more h2{font-size:22px;margin:0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;margin-top:20px}
.card{display:block;border:1px solid #E3E7EB;border-radius:14px;padding:22px;text-decoration:none;color:#16202B;background:#FFFFFF}
.card:hover{border-color:#C4501A;color:#16202B}
.card b{display:block;font-size:19px;line-height:1.3}.card span{display:block;margin-top:10px;font-size:15px;color:#5A6573}
.card i{display:block;margin-top:14px;font-style:normal;font-family:'IBM Plex Mono',monospace;font-size:12px;color:#5A6573}
.ftr{background:#16202B;color:#AEB8C3;font-size:14px;margin-top:24px}
.ftr .wrap{padding-top:40px;padding-bottom:96px;display:flex;flex-wrap:wrap;gap:32px;justify-content:space-between}
.ftr a{color:#AEB8C3}
.callbar{display:none;position:fixed;left:12px;right:12px;bottom:12px;z-index:20;background:#C4501A;color:#FFFFFF;text-decoration:none;font-weight:700;border-radius:10px;min-height:52px;align-items:center;justify-content:center}
@media (max-width:900px){.nav{display:none}}
@media (max-width:640px){.ph{display:none}.callbar{display:flex}.hdr .btn{display:none}}
"""

LOGO = ('<svg width="34" height="34" viewBox="0 0 34 34" fill="none" stroke="#16202B" stroke-width="2" '
        'aria-hidden="true"><rect x="2" y="2" width="30" height="30" rx="7"></rect><path d="M8 13h18M8 21h18" '
        'stroke="#C4501A"></path><circle cx="13" cy="13" r="2.4" fill="#FFFFFF"></circle><circle cx="21" '
        'cy="21" r="2.4" fill="#FFFFFF"></circle></svg>')


def esc(s):
    return html.escape(s, quote=True)


def ru_date(d):
    return f'{d.day} {MES[d.month - 1]} {d.year}'


def head_extra():
    """Метрика и коды подтверждения Вебмастера/Search Console из site.json.
    Пустые значения — блок пустой. Тот же блок ставится на главную между маркерами."""
    out = []
    if CFG.get('yandex_verification'):
        out.append(f'<meta name="yandex-verification" content="{esc(CFG["yandex_verification"])}">')
    if CFG.get('google_verification'):
        out.append(f'<meta name="google-site-verification" content="{esc(CFG["google_verification"])}">')
    m = str(CFG.get('metrika') or '')
    if m:
        out.append(f"""<script>(function(m,e,t,r,i,k,a){{m[i]=m[i]||function(){{(m[i].a=m[i].a||[]).push(arguments)}};
m[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){{if(document.scripts[j].src===r){{return;}}}}
k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)}})
(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");
ym({m},"init",{{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true}});
document.addEventListener("click",function(e){{var a=e.target.closest&&e.target.closest('a[href^="tel:"]');if(a)ym({m},"reachGoal","call");}});
document.addEventListener("submit",function(e){{if(e.target.id==="lead-form")ym({m},"reachGoal","lead");}});</script>
<noscript><div><img src="https://mc.yandex.ru/watch/{m}" style="position:absolute;left:-9999px" alt=""></div></noscript>""")
    return '<!-- head-extra -->' + '\n'.join(out) + '<!-- /head-extra -->'


def page(*, title, description, canonical, root, body, jsonld, active_stati=True):
    """root — относительный путь до корня сайта ('../', '../../'): работает и на домене,
    и на GitHub Pages в подпапке."""
    p, pt, hrs = CFG['phone'], CFG['phone_tel'], CFG['hours']
    ld = '\n'.join(f'<script type="application/ld+json">{json.dumps(j, ensure_ascii=False)}</script>'
                   for j in jsonld)
    return f"""<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="{ROBOTS}">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&amp;family=IBM+Plex+Mono:wght@500&amp;display=swap">
<style>{STYLE}</style>
{ld}
{head_extra()}
</head>
<body>
<header class="hdr"><div class="wrap">
<a class="logo" href="{root}">{LOGO}<span>Опрессуем<span style="color:#C4501A">.ru</span></span></a>
<nav class="nav">
<a href="{root}#uslugi">Услуги</a><a href="{root}#etapy">Как работаем</a><a href="{root}#obekty">Объекты</a>
<a href="{root}stati/"{' class="on"' if active_stati else ''}>Статьи</a><a href="{root}#kontakty">Контакты</a>
</nav>
<div class="hdr-r"><div class="ph"><a href="tel:{pt}">{p}</a><div>{hrs}</div></div>
<a class="btn" href="{root}#kontakty">Обсудить объект</a></div>
</div></header>
{body}
<footer class="ftr"><div class="wrap">
<div><div style="color:#FFFFFF;font-weight:800;font-size:17px">Опрессуем.ru</div><div style="margin-top:8px">Тепловые пункты и наружные сети · Москва и МО</div></div>
<div style="line-height:1.8">Подрядчик — «Гидросфера» · Москва<br>{p} · {hrs}</div>
<div style="line-height:1.8"><a href="{root}stati/">Статьи</a><br>© {date.today().year}</div>
</div></footer>
<a class="callbar" href="tel:{pt}">Позвонить инженеру</a>
</body>
</html>
"""


def read(path):
    text = path.read_text()
    meta = {}
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    for k in ('title', 'description', 'date'):
        if not meta.get(k):
            raise SystemExit(f'{path.name}: в шапке нет поля {k}')
    meta['slug'] = path.stem
    meta['date'] = date.fromisoformat(meta['date'])
    meta['h1'] = meta.get('h1') or meta['title']
    meta['html'] = markdown.markdown(text, extensions=['tables', 'sane_lists', 'smarty'],
                                     extension_configs={'smarty': {'substitutions': {
                                         'left-double-quote': '«', 'right-double-quote': '»'}}})
    meta['draft'] = meta.get('draft', '').lower() in ('true', 'да', 'yes')
    return meta


def card(a, root):
    return (f'<a class="card" href="{root}stati/{a["slug"]}/"><b>{esc(a["h1"])}</b>'
            f'<span>{esc(a["description"])}</span><i>{ru_date(a["date"])}</i></a>')


def cta(root):
    return f"""<div class="cta"><h2>Есть объект — обсудим с инженером</h2>
<p>Выезжаем на обследование по Москве и области, готовим техническое решение и смету. Цену фиксируем в договоре.</p>
<div class="row"><a class="btn" href="{root}#kontakty">Оставить заявку</a><a class="b2" href="tel:{CFG['phone_tel']}">{CFG['phone']}</a></div></div>"""


def build():
    arts = sorted((read(p) for p in SRC.glob('*.md')), key=lambda a: a['date'], reverse=True)
    pub = [a for a in arts if not a['draft']]
    live = {a['slug'] for a in pub}

    # удалить страницы статей, которых больше нет (или ушли в черновики)
    for d in OUT.iterdir():
        if d.is_dir() and d.name != '_src' and d.name not in live and (d / 'index.html').exists():
            (d / 'index.html').unlink()
            d.rmdir()

    crumbs_ld = lambda items: {'@context': 'https://schema.org', '@type': 'BreadcrumbList',
                               'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
                                                   for i, (n, u) in enumerate(items)]}

    for a in pub:
        url = f'{BASE}/stati/{a["slug"]}/'
        root = '../../'
        by_slug = {o['slug']: o for o in pub}
        rel = [by_slug[x.strip()] for x in a.get('related', '').split(',') if x.strip() in by_slug and x.strip() != a['slug']]
        others = (rel + [o for o in pub if o is not a and o not in rel])[:3]
        more = (f'<section class="more"><h2>Ещё по теме</h2><div class="cards">'
                f'{"".join(card(o, root) for o in others)}</div></section>') if others else ''
        lead = f'<p class="lead">{esc(a["lead"])}</p>' if a.get('lead') else ''
        body = f"""<main>
<article class="art">
<div class="crumbs"><a href="{root}">Главная</a> → <a href="{root}stati/">Статьи</a></div>
<h1>{esc(a["h1"])}</h1>
<div class="meta">{ru_date(a["date"])}</div>
{lead}
<div class="body">{a["html"]}</div>
{cta(root)}
</article>
{more}
</main>"""
        ld = [{'@context': 'https://schema.org', '@type': 'Article', 'headline': a['h1'],
               'description': a['description'], 'datePublished': a['date'].isoformat(),
               'mainEntityOfPage': url, 'inLanguage': 'ru',
               'publisher': {'@type': 'Organization', 'name': 'Опрессуем.ru', 'url': BASE + '/'}},
              crumbs_ld([('Главная', BASE + '/'), ('Статьи', BASE + '/stati/'), (a['h1'], url)])]
        d = OUT / a['slug']
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(page(title=a['title'], description=a['description'], canonical=url,
                                           root=root, body=body, jsonld=ld))

    root = '../'
    lst = (f'<div class="cards">{"".join(card(a, root) for a in pub)}</div>' if pub
           else '<p>Скоро здесь появятся статьи.</p>')
    body = f"""<main class="wrap" style="padding-bottom:72px">
<div class="crumbs"><a href="{root}">Главная</a> → Статьи</div>
<h1 style="margin:14px 0 0;font-size:clamp(30px,4vw,44px);line-height:1.12;font-weight:800;letter-spacing:-0.02em">Статьи о тепловых пунктах и теплосетях</h1>
<p style="margin:18px 0 0;font-size:19px;color:#3A4552;max-width:720px">Разбираем реконструкцию ЦТП и ИТП, перекладку теплотрасс, испытания и документы — для управляющих компаний, собственников зданий и предприятий Москвы и области.</p>
<div style="margin-top:36px">{lst}</div>
<div style="max-width:760px">{cta(root)}</div>
</main>"""
    ld = [crumbs_ld([('Главная', BASE + '/'), ('Статьи', BASE + '/stati/')])]
    (OUT / 'index.html').write_text(page(title='Статьи о ЦТП, ИТП и теплотрассах — Опрессуем.ru',
                                         description='Реконструкция тепловых пунктов, перекладка теплотрасс, опрессовка и документы: разборы для управляющих компаний и собственников зданий в Москве и МО.',
                                         canonical=BASE + '/stati/', root=root, body=body, jsonld=ld))

    # sitemap и robots
    urls = [(BASE + '/', date.today()), (BASE + '/stati/', max([a['date'] for a in pub], default=date.today()))]
    urls += [(f'{BASE}/stati/{a["slug"]}/', a['date']) for a in pub]
    (ROOT / 'sitemap.xml').write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'<url><loc>{u}</loc><lastmod>{d.isoformat()}</lastmod></url>\n' for u, d in urls)
        + '</urlset>\n')
    # robots.txt всегда открыт: закрытие идёт метой noindex, иначе робот её не увидит
    (ROOT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')

    # мета robots на главной — по тому же флагу
    idx = ROOT / 'index.html'
    s = idx.read_text()
    s2 = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{ROBOTS}">', s)
    # Метрика и подтверждения — тот же блок, что в статьях
    if '<!-- head-extra -->' in s2:
        s2 = re.sub(r'<!-- head-extra -->.*?<!-- /head-extra -->', lambda _: head_extra(), s2, flags=re.S)
    else:
        s2 = s2.replace('</head>', head_extra() + '\n</head>', 1)
    if s2 != s:
        idx.write_text(s2)

    print(f'статей: {len(pub)} опубликовано, {len(arts) - len(pub)} черновиков; robots: {ROBOTS}')


if __name__ == '__main__':
    build()
