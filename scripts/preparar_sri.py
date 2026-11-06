#!/usr/bin/env python3
"""Gera uma cópia de index.html com SRI, após baixar e validar as bibliotecas.
Não altera index.html original. Uso: python3 scripts/preparar_sri.py
"""
import base64
import hashlib
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
html = (ROOT / "index.html").read_text(encoding="utf-8")
urls = {
    "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js": "static",
    "https://cdnjs.cloudflare.com/ajax/libs/jspdf/4.2.1/jspdf.umd.min.js": "static",
    "https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.13.0/mammoth.browser.min.js": "dynamic",
}
for url, mode in urls.items():
    request = urllib.request.Request(url, headers={"User-Agent": "Match-de-Vagas-SRI-audit/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type", "").lower()
        if not data or not any(t in content_type for t in ("javascript", "text/plain", "octet-stream")):
            raise RuntimeError(f"Conteúdo inesperado para {url}: {content_type}")
    sri = "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode("ascii")
    if mode == "static":
        old = f'<script src="{url}"></script>'
        new = f'<script src="{url}" integrity="{sri}" crossorigin="anonymous"></script>'
        if html.count(old) != 1:
            raise RuntimeError(f"Tag não encontrada exatamente uma vez: {url}")
        html = html.replace(old, new)
    else:
        old = f"loadScript('{url}')"
        new = f"loadScript('{url}','{sri}')"
        if html.count(old) != 1:
            raise RuntimeError(f"Carregamento dinâmico não encontrado: {url}")
        html = html.replace(old, new)
    print(f"{mode}: {url} -> {sri}")

old_fn = "function loadScript(u){return new Promise((ok,no)=>{const s=document.createElement('script');s.src=u;"
new_fn = "function loadScript(u,integrity){return new Promise((ok,no)=>{const s=document.createElement('script');s.src=u;if(integrity){s.integrity=integrity;s.crossOrigin='anonymous';}"
if html.count(old_fn) != 1:
    raise RuntimeError("Função de carregamento não encontrada")
html = html.replace(old_fn, new_fn)
output = ROOT / "index.sri-preview.html"
output.write_text(html, encoding="utf-8")
print(f"Prévia gerada: {output.name}. PDF.js ESM ainda exige validação própria e não recebeu SRI.")
