"""Ziyaretçi Defteri API — Final projesi için hazır uygulama.

Endpoint'ler:
  GET  /health      -> sağlık kontrolü (DB bağlantısını da test eder)
  GET  /mesajlar    -> tüm mesajları listeler
  POST /mesajlar    -> {"isim": "...", "mesaj": "..."} ile yeni mesaj ekler

Konfigürasyon (ortam değişkenleri):
  DATABASE_URL  örn: postgresql://defter:defter@db:5432/defter
  APP_ADI       sayfa başlığı (opsiyonel)
"""
import os
import time

import psycopg
from flask import Flask, jsonify, request

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://defter:defter@db:5432/defter")
APP_ADI = os.environ.get("APP_ADI", "Ziyaretçi Defteri")

app = Flask(__name__)


def baglan():
    return psycopg.connect(DATABASE_URL, autocommit=True)


def tabloyu_hazirla(deneme=10):
    """DB hazır olana kadar birkaç kez dener, sonra tabloyu oluşturur."""
    for i in range(1, deneme + 1):
        try:
            with baglan() as c:
                c.execute(
                    """CREATE TABLE IF NOT EXISTS mesajlar (
                           id     SERIAL PRIMARY KEY,
                           isim   TEXT NOT NULL,
                           mesaj  TEXT NOT NULL,
                           zaman  TIMESTAMPTZ NOT NULL DEFAULT now()
                       )"""
                )
            print("Veritabanı hazır.", flush=True)
            return
        except psycopg.OperationalError as e:
            print(f"DB bekleniyor ({i}/{deneme}): {e}", flush=True)
            time.sleep(2)
    raise SystemExit("Veritabanına bağlanılamadı!")


@app.get("/")
def anasayfa():
    return jsonify(uygulama=APP_ADI, endpointler=["/health", "/mesajlar"])


@app.get("/health")
def health():
    with baglan() as c:
        c.execute("SELECT 1")
    return jsonify(durum="ok")


@app.get("/mesajlar")
def listele():
    with baglan() as c:
        satirlar = c.execute("SELECT id, isim, mesaj, zaman FROM mesajlar ORDER BY id DESC").fetchall()
    return jsonify([
        {"id": s[0], "isim": s[1], "mesaj": s[2], "zaman": s[3].isoformat()} for s in satirlar
    ])


@app.post("/mesajlar")
def ekle():
    veri = request.get_json(silent=True) or {}
    isim, mesaj = veri.get("isim"), veri.get("mesaj")
    if not isim or not mesaj:
        return jsonify(hata="'isim' ve 'mesaj' alanları zorunlu"), 400
    with baglan() as c:
        yeni_id = c.execute(
            "INSERT INTO mesajlar (isim, mesaj) VALUES (%s, %s) RETURNING id", (isim, mesaj)
        ).fetchone()[0]
    return jsonify(id=yeni_id, isim=isim, mesaj=mesaj), 201


# gunicorn ile import edildiğinde de tablo hazırlansın
tabloyu_hazirla()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
