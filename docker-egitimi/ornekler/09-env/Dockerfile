FROM python:3.12-slim

# ARG: sadece build anında (docker build --build-arg ...)
ARG BUILD_VERSIYON=dev

# ENV: çalışma anındaki VARSAYILAN değerler (docker run -e ile ezilebilir)
ENV APP_MESAJ="Dockerfile'daki varsayılan mesaj" \
    APP_ORTAM=gelistirme \
    APP_PORT=8000 \
    BUILD_VERSIYON=${BUILD_VERSIYON} \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app.py .
EXPOSE 8000
CMD ["python", "app.py"]
