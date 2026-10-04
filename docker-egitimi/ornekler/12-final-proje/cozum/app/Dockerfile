# syntax=docker/dockerfile:1
# ===================== ÇÖZÜM =====================
# Multi-stage: wheel'ler build aşamasında hazırlanır, runtime'a sadece kurulu paketler taşınır.

# ---------- build ----------
FROM python:3.12-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------- runtime ----------
FROM python:3.12-slim AS runtime
LABEL org.opencontainers.image.title="ziyaretci-defteri" \
      org.opencontainers.image.source="egitim/docker-temelleri"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Root olmayan kullanıcı
RUN useradd --create-home --uid 10001 uygulama
WORKDIR /app

COPY --from=build /install /usr/local
COPY --chown=uygulama:uygulama . .

USER uygulama
EXPOSE 5000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
