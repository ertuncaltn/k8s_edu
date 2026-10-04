import os
import socket

import redis
from flask import Flask

app = Flask(__name__)

# Servis adı ("redis") compose network'ündeki DNS sayesinde IP'ye çözülür
r = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
)

BASLIK = os.getenv("APP_BASLIK", "Ziyaret Sayacı")


@app.route("/")
def index():
    sayi = r.incr("ziyaret")
    return f"{BASLIK}: Bu sayfa {sayi} kez görüntülendi. (cevap veren container: {socket.gethostname()})\n"


@app.route("/health")
def health():
    r.ping()
    return "ok\n"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG") == "1")
