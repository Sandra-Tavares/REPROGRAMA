#!/usr/bin/env python3
"""Servidor local: entrega a página e guarda a chave de API (ela nunca vai ao navegador).
Uso: python server.py   -> abra http://localhost:8000"""
import json, os, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).parent

def load_env():
    for nome in (".env", "chave.env"):
        f = BASE / nome
        if f.exists():
            for linha in f.read_text(encoding="utf-8").splitlines():
                linha = linha.strip()
                if linha and not linha.startswith("#") and "=" in linha:
                    k, v = linha.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()
PADRAO = {"anthropic": "claude-sonnet-5-5", "openai": "gpt-4o-mini"}
PROVIDER = os.environ.get("PROVIDER", "anthropic").strip().lower()
MODEL = os.environ.get("MODEL", "").strip() or PADRAO.get(PROVIDER, "")
KEY = os.environ.get("ANTHROPIC_API_KEY" if PROVIDER == "anthropic" else "OPENAI_API_KEY", "").strip() if PROVIDER in PADRAO else ""
PORT = int(os.environ.get("PORT", "8000"))
MAX_BODY = 400_000

def call_llm(system, messages):
    if PROVIDER == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {"x-api-key": KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        body = {"model": MODEL, "max_tokens": 4000, "system": system, "messages": messages}
    else:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"authorization": "Bearer " + KEY, "content-type": "application/json"}
        body = {"model": MODEL, "messages": [{"role": "system", "content": system}] + messages,
                "response_format": {"type": "json_object"}}
    req = urllib.request.Request(url, json.dumps(body).encode(), headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.load(r)
    if PROVIDER == "anthropic":
        return "".join(c.get("text", "") for c in d["content"])
    return d["choices"][0]["message"]["content"]

ERROS = {401: "Chave de API recusada pelo provedor. Confira o arquivo .env.",
         403: "Chave de API sem permissão. Confira o arquivo .env.",
         404: "Modelo não encontrado. Ajuste MODEL no arquivo .env.",
         429: "Limite de uso ou saldo do provedor atingido. Tente de novo em instantes."}

class H(BaseHTTPRequestHandler):
    def _send(self, code, tipo, b):
        self.send_response(code)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def _json(self, code, obj):
        self._send(code, "application/json; charset=utf-8", json.dumps(obj, ensure_ascii=False).encode())

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", (BASE / "index.html").read_bytes())
        elif self.path == "/api/health":
            self._json(200, {"has_key": bool(KEY), "provider": PROVIDER, "model": MODEL})
        else:
            self._json(404, {"error": "Não encontrado."})

    def do_POST(self):
        if self.path != "/api/llm":
            return self._json(404, {"error": "Não encontrado."})
        o = self.headers.get("Origin")
        if o and o not in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}"):
            return self._json(403, {"error": "Origem não permitida."})
        if not KEY:
            return self._json(500, {"error": "Falta a chave de API no servidor. Preencha o arquivo .env e reinicie o servidor."})
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n <= 0 or n > MAX_BODY:
                return self._json(413, {"error": "Texto grande demais. Reduza o currículo ou a vaga."})
            d = json.loads(self.rfile.read(n))
            system, msgs = d["system"], d["messages"]
            assert isinstance(system, str) and isinstance(msgs, list) and msgs
            assert all(isinstance(m, dict) and m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str) for m in msgs)
        except Exception:
            return self._json(400, {"error": "Pedido inválido."})
        try:
            self._json(200, {"text": call_llm(system, msgs)})
        except urllib.error.HTTPError as e:
            self._json(502, {"error": ERROS.get(e.code, f"O provedor retornou erro {e.code}.")})
        except Exception:
            self._json(502, {"error": "O servidor não conseguiu falar com o provedor. Verifique a internet."})

if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    print(f"Abra http://localhost:{PORT}  (provedor: {PROVIDER}, modelo: {MODEL}, chave: {'ok' if KEY else 'FALTANDO'})")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrado.")
