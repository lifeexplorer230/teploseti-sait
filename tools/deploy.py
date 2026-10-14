#!/usr/bin/env python3
"""Заливка сайта в Yandex Object Storage (бакет www.opressuem.ru).

Запуск: python3 tools/deploy.py          — залить изменённые файлы
        python3 tools/deploy.py --all    — залить всё заново
Ключи S3 берутся из ~/core/.zayavki.env (S3_KEY_ID, S3_SECRET) — в репозиторий не кладём.
Сравнение по md5 (ETag), удаляет из бакета файлы, которых больше нет локально.
"""
import hashlib
import hmac
import mimetypes
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUCKET = 'www.opressuem.ru'
HOST, REG = 'storage.yandexcloud.net', 'ru-central1'
SKIP_DIRS = {'.git', 'tools', '_src'}
SKIP_FILES = {'README.md', '.nojekyll', '.gitignore'}

cfg = dict(l.strip().split('=', 1) for l in open(os.path.expanduser('~/core/.zayavki.env'))
           if '=' in l and not l.startswith('#'))
KID, SEC = cfg['S3_KEY_ID'], cfg['S3_SECRET']


def _sig(k, m):
    return hmac.new(k, m.encode(), hashlib.sha256).digest()


def req(method, path, query='', body=b'', headers=None):
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    t = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    d = t[:8]
    ph = hashlib.sha256(body).hexdigest()
    h = {'host': HOST, 'x-amz-content-sha256': ph, 'x-amz-date': t, **headers}
    sh = ';'.join(sorted(h))
    ch = ''.join(f'{k}:{h[k]}\n' for k in sorted(h))
    qpath = urllib.parse.quote(path)
    cr = '\n'.join([method, qpath, query, ch, sh, ph])
    sc = f'{d}/{REG}/s3/aws4_request'
    sts = '\n'.join(['AWS4-HMAC-SHA256', t, sc, hashlib.sha256(cr.encode()).hexdigest()])
    k = _sig(('AWS4' + SEC).encode(), d)
    for p in (REG, 's3', 'aws4_request'):
        k = _sig(k, p)
    sig = hmac.new(k, sts.encode(), hashlib.sha256).hexdigest()
    hh = {k: v for k, v in h.items() if k != 'host'}
    hh['Authorization'] = f'AWS4-HMAC-SHA256 Credential={KID}/{sc}, SignedHeaders={sh}, Signature={sig}'
    url = f'https://{HOST}{qpath}' + ('?' + query if query else '')
    r = urllib.request.Request(url, data=body if method in ('PUT', 'POST') else None, method=method, headers=hh)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.status, resp.read().decode(errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors='replace')


def remote():
    """ключ -> md5 всех объектов бакета"""
    out, token = {}, None
    while True:
        q = 'list-type=2' + (f'&continuation-token={urllib.parse.quote(token, safe="")}' if token else '')
        st, body = req('GET', f'/{BUCKET}', q)
        if st != 200:
            raise SystemExit(f'не смог прочитать бакет: {st} {body[:300]}')
        for key, etag in re.findall(r'<Key>(.*?)</Key>.*?<ETag>(.*?)</ETag>', body, re.S):
            out[key] = etag.replace('&quot;', '').strip('"')
        m = re.search(r'<NextContinuationToken>(.*?)</NextContinuationToken>', body)
        if not m:
            return out
        token = m.group(1)


def local():
    for p in sorted(ROOT.rglob('*')):
        rel = p.relative_to(ROOT)
        if p.is_file() and not (set(rel.parts) & SKIP_DIRS) and rel.name not in SKIP_FILES:
            yield rel.as_posix(), p


def ctype(name):
    t = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    if name.endswith('.webp'):
        t = 'image/webp'
    return t + ('; charset=utf-8' if t.startswith('text/') or t in ('application/xml', 'application/javascript') else '')


def main():
    full = '--all' in sys.argv
    have = remote()
    seen, sent = set(), 0
    for key, p in local():
        seen.add(key)
        data = p.read_bytes()
        if not full and have.get(key) == hashlib.md5(data).hexdigest():
            continue
        st, body = req('PUT', f'/{BUCKET}/{key}', body=data, headers={'Content-Type': ctype(key)})
        if st != 200:
            raise SystemExit(f'{key}: {st} {body[:300]}')
        print('↑', key)
        sent += 1
    gone = [k for k in have if k not in seen]
    for key in gone:
        st, _ = req('DELETE', f'/{BUCKET}/{key}')
        print('✗', key, st)
    print(f'залито {sent}, удалено {len(gone)}, всего в бакете {len(seen)}')


if __name__ == '__main__':
    main()
