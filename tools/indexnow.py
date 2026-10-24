#!/usr/bin/env python3
"""Сообщить Яндексу (и Bing) о страницах сайта по протоколу IndexNow — работает и когда Вебмастер «только чтение».
Ключ — файл <ключ>.txt в корне сайта (не удалять). Запуск после выкладки: python3 tools/indexnow.py"""
import json, re, urllib.request
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
KEY = "f6daa32c54fc4265a14b94205e5185e0"
urls = re.findall(r"<loc>(.*?)</loc>", (ROOT / "sitemap.xml").read_text())
body = json.dumps({"host": "www.opressuem.ru", "key": KEY, "keyLocation": f"https://www.opressuem.ru/{KEY}.txt", "urlList": urls}).encode()
for ep in ("https://yandex.com/indexnow", "https://api.indexnow.org/indexnow"):
    req = urllib.request.Request(ep, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(ep, r.status, len(urls), "адресов")
    except Exception as e:
        print(ep, "ошибка:", e, getattr(e, "read", lambda: b"")()[:200])
