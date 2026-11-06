#!/usr/bin/env python3
"""Verifica sintaxe do JavaScript inline no index.html usando Node.js."""
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys

class InlineScripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_script = False
        self.scripts = []
    def handle_starttag(self, tag, attrs):
        if tag == "script" and not dict(attrs).get("src"):
            self.in_script = True
            self.scripts.append("")
    def handle_endtag(self, tag):
        if tag == "script":
            self.in_script = False
    def handle_data(self, data):
        if self.in_script:
            self.scripts[-1] += data

parser = InlineScripts()
parser.feed(Path("index.html").read_text(encoding="utf-8"))
if not parser.scripts:
    sys.exit("FALHA: nenhum script inline encontrado")
for n, script in enumerate(parser.scripts, 1):
    result = subprocess.run(
        ["node", "--check", "--input-type=module"],
        input=script, text=True, capture_output=True
    )
    if result.returncode:
        print(f"FALHA no script inline {n}: {result.stderr}", file=sys.stderr)
        sys.exit(1)
print(f"OK: sintaxe validada em {len(parser.scripts)} script(s) inline")
