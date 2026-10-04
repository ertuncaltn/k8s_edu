"""Ziyaretçi Defteri API — Flask + PostgreSQL.

NOT: Lab klasörünüzde orijinal app.py zaten var; bu dosya aynı arayüzü
(endpoint'ler, DATABASE_URL, APP_ADI) sağlayan bir eşdeğerdir.
"""
import os

import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request

app = Flask(__name__)
app.json.ensure_ascii = False  # Türkçe karakterler JSON'da düzgün görünsün

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://defter:sifre@db:5432/defter")
APP_ADI = os.environ.get("APP_ADI", "Ziyaretçi Defteri")


def baglan():
    return psycopg2.connect(DATABASE_URL, connect_timeout=3)


def tablo_olustur():
    with baglan() as conn, conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS mesajlar (
                id         SERIAL PRIMARY KEY,
                isim       VARCHAR(100) NOT NULL,
                mesaj      TEXT         NOT NULL,
                olusturma  TIMESTAMPTZ  NOT NULL DEFAULT now()
            )
            """
        )


_tablo_hazir = False


@app.before_request
def hazirla():
    global _tablo_hazir
    if not _tablo_hazir and request.path != "/":
        try:
            tablo_olustur()
            _tablo_hazir = True
        except psycopg2.Error:
            pass  # /health bunu raporlayacak


@app.get("/")
def bilgi():
    return jsonify(
        uygulama=APP_ADI,
        surum=os.environ.get("APP_SURUM", "1.0.0"),
        endpointler=["GET /", "GET /health", "GET /mesajlar", "POST /mesajlar"],
    )


@app.get("/health")
def health():
    try:
        with baglan() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
        return jsonify(durum="saglikli", veritabani="bagli"), 200
    except psycopg2.Error as e:
        return jsonify(durum="sagliksiz", veritabani="baglanamadi", hata=str(e).strip()), 503


@app.get("/mesajlar")
def mesajlari_listele():
    with baglan() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, isim, mesaj, olusturma FROM mesajlar ORDER BY id")
        satirlar = cur.fetchall()
    for s in satirlar:
        s["olusturma"] = s["olusturma"].isoformat()
    return jsonify(satirlar)


@app.post("/mesajlar")
def mesaj_ekle():
    veri = request.get_json(silent=True) or {}
    isim = (veri.get("isim") or "").strip()
    mesaj = (veri.get("mesaj") or "").strip()
    if not isim or not mesaj:
        return jsonify(hata="'isim' ve 'mesaj' alanları zorunludur"), 400
    with baglan() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "INSERT INTO mesajlar (isim, mesaj) VALUES (%s, %s) RETURNING id, isim, mesaj, olusturma",
            (isim, mesaj),
        )
        yeni = cur.fetchone()
    yeni["olusturma"] = yeni["olusturma"].isoformat()
    return jsonify(yeni), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
