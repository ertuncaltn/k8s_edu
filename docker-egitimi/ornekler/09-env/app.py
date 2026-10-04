"""Ortam değişkenlerinden konfigürasyon okuyan, bağımlılıksız küçük web sunucusu."""
import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer

# Konfigürasyon SADECE ortam değişkenlerinden okunur (12-Factor App, Madde III)
MESAJ = os.getenv("APP_MESAJ", "Varsayılan mesaj")
ORTAM = os.getenv("APP_ORTAM", "gelistirme")
RENK = os.getenv("APP_RENK", "#555555")
PORT = int(os.getenv("APP_PORT", "8000"))
DB_SIFRE = os.getenv("DB_SIFRE")  # gizli bilgi - asla ekrana basmayın!


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        sifre_durumu = "tanımlı" if DB_SIFRE else "TANIMLI DEĞİL"
        html = f"""<!doctype html><html lang="tr"><meta charset="utf-8">
<body style="font-family:sans-serif;background:{RENK};color:#fff;padding:40px">
<h1>{MESAJ}</h1>
<ul>
  <li>Ortam: <b>{ORTAM}</b></li>
  <li>Port: <b>{PORT}</b></li>
  <li>DB şifresi: <b>{sifre_durumu}</b></li>
  <li>Container: <b>{socket.gethostname()}</b></li>
</ul></body></html>"""
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    print(f"[{ORTAM}] {PORT} portunda dinleniyor...", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
