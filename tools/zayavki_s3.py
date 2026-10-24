#!/usr/bin/env python3
"""Приём заявок сайта без сервера: форма пишет прямо в бакет mafclub-leads (Яндекс, РФ).

Браузер шлёт POST в Object Storage по подписанной политике: писать можно только
в leads-opressuem/, не больше 15 МБ, до даты expiration. Секретный ключ в браузер
не попадает. Дальше заявку забирает ~/core/bin/storozh-zayavok.py и шлёт в Telegram.

  python3 tools/zayavki_s3.py cors     — разрешить POST с opressuem.ru (один раз)
  python3 tools/zayavki_s3.py policy   — выпустить политику → tools/zayavki-policy.json
"""
import base64, hashlib, hmac, json, sys, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENV = Path.home() / "core" / ".zayavki.env"
HOST, REGION = "storage.yandexcloud.net", "ru-central1"
PREFIX = "leads-opressuem/"
ORIGINS = ["https://www.opressuem.ru", "https://opressuem.ru", "https://lifeexplorer230.github.io", "http://localhost:8765"]
OUT = Path(__file__).resolve().parent / "zayavki-policy.json"


def env():
    return dict(l.split("=", 1) for l in ENV.read_text().splitlines() if "=" in l and not l.startswith("#"))


def key(secret, date):
    k = hmac.new(("AWS4" + secret).encode(), date.encode(), hashlib.sha256).digest()
    for p in (REGION, "s3", "aws4_request"):
        k = hmac.new(k, p.encode(), hashlib.sha256).digest()
    return k


def put_cors(cfg):
    body = ("<CORSConfiguration><CORSRule>" + "".join(f"<AllowedOrigin>{o}</AllowedOrigin>" for o in ORIGINS) +
            "<AllowedMethod>POST</AllowedMethod><AllowedHeader>*</AllowedHeader><MaxAgeSeconds>3600</MaxAgeSeconds>"
            "</CORSRule></CORSConfiguration>").encode()
    now = datetime.now(timezone.utc); amz = now.strftime("%Y%m%dT%H%M%SZ"); d = amz[:8]
    ph = hashlib.sha256(body).hexdigest(); md5 = base64.b64encode(hashlib.md5(body).digest()).decode()
    path = f"/{cfg['S3_BUCKET']}"
    hdrs = f"content-md5:{md5}\nhost:{HOST}\nx-amz-content-sha256:{ph}\nx-amz-date:{amz}\n"
    signed = "content-md5;host;x-amz-content-sha256;x-amz-date"
    creq = "\n".join(["PUT", path, "cors=", hdrs, signed, ph])
    scope = f"{d}/{REGION}/s3/aws4_request"
    sts = "\n".join(["AWS4-HMAC-SHA256", amz, scope, hashlib.sha256(creq.encode()).hexdigest()])
    sig = hmac.new(key(cfg["S3_SECRET"], d), sts.encode(), hashlib.sha256).hexdigest()
    req = urllib.request.Request(f"https://{HOST}{path}?cors=", data=body, method="PUT", headers={
        "Content-MD5": md5, "x-amz-date": amz, "x-amz-content-sha256": ph,
        "Authorization": f"AWS4-HMAC-SHA256 Credential={cfg['S3_KEY_ID']}/{scope}, SignedHeaders={signed}, Signature={sig}"})
    print(urllib.request.urlopen(req, timeout=20).status)


def policy(cfg, days=365):
    now = datetime.now(timezone.utc); d = now.strftime("%Y%m%d")
    cred = f"{cfg['S3_KEY_ID']}/{d}/{REGION}/s3/aws4_request"
    exp = datetime.fromtimestamp(now.timestamp() + days * 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pol = {"expiration": exp, "conditions": [
        {"bucket": cfg["S3_BUCKET"]}, ["starts-with", "$key", PREFIX], ["starts-with", "$Content-Type", ""],
        ["content-length-range", 1, 15 * 1024 * 1024],
        {"x-amz-algorithm": "AWS4-HMAC-SHA256"}, {"x-amz-credential": cred}, {"x-amz-date": d + "T000000Z"}]}
    b64 = base64.b64encode(json.dumps(pol).encode()).decode()
    sig = hmac.new(key(cfg["S3_SECRET"], d), b64.encode(), hashlib.sha256).hexdigest()
    out = {"url": f"https://{HOST}/{cfg['S3_BUCKET']}", "prefix": PREFIX, "expires": exp, "fields": {
        "Policy": b64, "X-Amz-Algorithm": "AWS4-HMAC-SHA256", "X-Amz-Credential": cred,
        "X-Amz-Date": d + "T000000Z", "X-Amz-Signature": sig}}
    OUT.write_text(json.dumps(out, indent=1)); print("политика до", exp, "→", OUT)


if __name__ == "__main__":
    cfg = env()
    {"cors": put_cors, "policy": policy}[sys.argv[1]](cfg)
