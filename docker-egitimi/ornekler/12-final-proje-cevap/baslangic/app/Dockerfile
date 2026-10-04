# syntax=docker/dockerfile:1
# =============================================================================
# Ziyaretçi Defteri API — Production Dockerfile
# =============================================================================
#
# BASE IMAGE SEÇİMİ: python:3.12-slim
#   - Resmî (Docker Official Image), düzenli güvenlik yamaları alıyor.
#   - Debian tabanlı "slim": ~45 MB sıkıştırılmış, gereksiz paket yok.
#   - glibc kullandığı için psycopg2-binary gibi hazır wheel'ler sorunsuz kurulur.
#     (alpine musl kullanır; bazı paketler kaynaktan derlenir, build yavaşlar,
#      image da çoğu zaman beklenenden küçük çıkmaz.)
#   - Sürüm sabit (3.12): "latest" sürprizlerinden kaçınıyoruz.
# =============================================================================

ARG PYTHON_VERSION=3.12

# -----------------------------------------------------------------------------
# AŞAMA 1: builder — bağımlılıkları izole bir virtualenv'e kur
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Tüm bağımlılıklar tek bir klasörde toplanır → final aşamaya tek COPY ile taşınır
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# LAYER CACHE: Önce SADECE requirements.txt kopyalanır.
# Kod değişse bile requirements.txt değişmediği sürece bu katman cache'ten gelir
# ve pip install tekrar çalışmaz.
COPY requirements.txt .
RUN pip install -r requirements.txt

# -----------------------------------------------------------------------------
# AŞAMA 2: runtime — sadece çalışmak için gerekenler
# -----------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.title="Ziyaretçi Defteri API" \
      org.opencontainers.image.description="Flask + PostgreSQL ziyaretçi defteri" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="Docker Eğitimi - Lab 12"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

# Root olmayan sistem kullanıcısı (sabit UID: volume/izin işlerinde öngörülebilir)
RUN groupadd --system --gid 10001 app \
 && useradd  --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app

# Builder'dan hazır virtualenv'i al (pip, derleme artıkları vb. gelmez)
COPY --from=builder /opt/venv /opt/venv

# Uygulama kodu EN SON kopyalanır (en sık değişen katman en üstte)
# .dockerignore sayesinde tests/, *.md, .env vb. buraya hiç gelmez
COPY --chown=app:app . .

USER app

EXPOSE 5000

# slim image'da curl yok → ek paket kurmak yerine Python'un kendisiyle kontrol.
# /health endpoint'i DB bağlantısını da test ediyor.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=4).status == 200 else 1)"]

# EXEC FORM: gunicorn PID 1 olur → docker stop'un gönderdiği SIGTERM'i
# doğrudan alır ve düzgün (graceful) kapanır. Shell form'da sinyal
# /bin/sh'a gider, uygulama 10 sn sonra SIGKILL ile öldürülür.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
