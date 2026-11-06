#!/usr/bin/env python3
"""Verifica disponibilidade e calcula SRI SHA-384 de dependências externas.
Execute: python3 scripts/verificar_dependencias.py
Não altera arquivos da aplicação.
"""
import base64
import hashlib
import sys
import urllib.error
import urllib.request

URLS = {
    "Supabase JS": "https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js",
    "jsPDF": "https://cdnjs.cloudflare.com/ajax/libs/jspdf/4.2.1/jspdf.umd.min.js",
    "Mammoth": "https://cdnjs.cloudflare.com/ajax/libs/mammoth/1.13.0/mammoth.browser.min.js",
    "PDF.js módulo": "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.5.438/build/pdf.mjs",
    "PDF.js worker": "https://cdn.jsdelivr.net/npm/pdfjs-dist@6.5.438/build/pdf.worker.mjs",
}

def main():
    failed = False
    for name, url in URLS.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Match-de-Vagas-dependency-audit/1.0"})
            with urllib.request.urlopen(req, timeout=25) as response:
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
                if not data or ("javascript" not in content_type and "text/plain" not in content_type and "octet-stream" not in content_type):
                    raise ValueError(f"Resposta inesperada: {content_type!r}; bytes={len(data)}")
            digest = base64.b64encode(hashlib.sha384(data).digest()).decode("ascii")
            print(f"OK {name}: {len(data)} bytes")
            print(f"   URL: {url}")
            print(f"   SRI: sha384-{digest}")
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            failed = True
            print(f"FALHA {name}: {exc}", file=sys.stderr)
    if failed:
        print("Verificação incompleta. Não publique as atualizações.", file=sys.stderr)
        return 1
    print("Arquivos acessíveis. Ainda é necessário validar segurança, compatibilidade e funcionamento no navegador.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
