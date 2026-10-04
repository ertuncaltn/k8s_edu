# İYİ ÖRNEK: Az değişen katmanlar üstte, sık değişenler altta.
FROM python:3.12-slim
WORKDIR /app

# 1) Sadece bağımlılık listesi -> nadiren değişir -> cache'ten gelir
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Kaynak kod -> sık değişir -> sadece bu katman ve sonrası yeniden oluşur
COPY . .

EXPOSE 5000
CMD ["python", "app.py"]
