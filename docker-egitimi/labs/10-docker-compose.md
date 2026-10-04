# Lab 10 — Docker Compose ile Çok Servisli Uygulama

**Süre:** 75 dk · **Klasör:** `ornekler/10-compose`

## Amaç
- Birden fazla servisi **tek bir YAML dosyasıyla** tanımlamak ve yönetmek
- **Servis bağımlılıkları** (`depends_on` + `healthcheck`), **paylaşılan network** ve **volume** kullanmak
- `.env` dosyası ile değişken yönetimi, **ölçekleme**, **reverse proxy**, **secrets** ve **watch** ile canlı geliştirme

---

## Kavram: Neden Compose?

Şimdiye kadar yaptıklarımızı tek tek komutla yapmak:

```bash
docker network create backend
docker network create frontend
docker volume create redis-data
docker run -d --name redis --network backend -v redis-data:/data redis:7-alpine redis-server --appendonly yes
docker build -t sayac-web:1.0.0 ./web
docker run -d --name web --network backend -p 8000:5000 -e REDIS_HOST=redis sayac-web:1.0.0
docker network connect frontend web
```

...ve bunu ekipteki herkesin **aynı şekilde** hatırlaması. Compose ile bunların hepsi **bir dosyada, versiyon kontrolünde, tek komutla**:

```bash
docker compose up -d
```

### Uygulama mimarisi

```
                         Host: http://localhost:8000
                                     │
 ┌── compose projesi: "sayac" ───────┼───────────────────────────────┐
 │                                   │ ports: 8000:5000              │
 │   ┌── frontend ──────────────┐    │                               │
 │   │                  ┌───────▼──────┐                             │
 │   │                  │     web      │  Flask (build: ./web)       │
 │   │                  │    :5000     │                             │
 │   └──────────────────┴───────┬──────┘                             │
 │                              │ REDIS_HOST=redis                   │
 │   ┌── backend ───────────────┼──────┐                             │
 │   │                  ┌───────▼──────┐     ┌──────────────┐        │
 │   │                  │    redis     │────▶│ redis-data   │ volume │
 │   │                  │    :6379     │     └──────────────┘        │
 │   └──────────────────┴──────────────┘                             │
 └───────────────────────────────────────────────────────────────────┘
```

---

## Bölüm A — `compose.yaml` anatomisi

```bash
cd ornekler/10-compose
```

Dosya yapısı:

```
10-compose/
├── .env                  ← değişkenler (compose otomatik okur)
├── compose.yaml          ← AŞAMA 1: web + redis
├── compose.proxy.yaml    ← AŞAMA 2: nginx + web (ölçekli) + redis
├── compose.secrets.yaml  ← secrets demosu
├── db_sifre.txt
├── proxy/nginx.conf
└── web/
    ├── app.py
    ├── requirements.txt
    ├── Dockerfile
    └── .dockerignore
```

`compose.yaml` dosyasının tamamı:

```yaml
name: sayac

services:
  web:
    build:
      context: ./web            # Dockerfile'ın bulunduğu klasör
      dockerfile: Dockerfile
    image: sayac-web:1.0.0      # build edilen image'a verilecek isim:tag
    ports:
      - "${WEB_PORT:-8000}:5000"  # host:container  (.env yoksa 8000)
    environment:
      APP_BASLIK: ${APP_BASLIK:-Ziyaret Sayacı}
      REDIS_HOST: redis         # servis adı = DNS adı
      REDIS_PORT: "6379"
    depends_on:
      redis:
        condition: service_healthy   # redis "healthy" olmadan web başlamaz
    networks:
      - frontend
      - backend
    restart: unless-stopped
    develop:
      watch:
        - action: sync
          path: ./web
          target: /app
          ignore:
            - __pycache__/
        - action: rebuild
          path: ./web/requirements.txt

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis-data:/data        # named volume -> kalıcı veri
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
      start_period: 5s
    networks:
      - backend                 # redis dışarıya (host'a) HİÇ açılmıyor
    restart: unless-stopped

networks:
  frontend:
  backend:

volumes:
  redis-data:
```

### Anahtar alanlar

| Alan | Açıklama | `docker run` karşılığı |
|---|---|---|
| `name` | Proje adı; container/network/volume isimlerinin öneki | — |
| `build` | Image'ı Dockerfile'dan build et | `docker build` |
| `image` | Kullanılacak / oluşturulacak image adı | `IMAGE` |
| `ports` | Port mapping | `-p` |
| `environment` | Ortam değişkenleri | `-e` |
| `env_file` | Ortam dosyası | `--env-file` |
| `volumes` | Volume / bind mount | `-v` |
| `networks` | Bağlanılacak ağlar | `--network` |
| `depends_on` | Başlama sırası ve koşulu | — |
| `healthcheck` | Sağlık kontrolü | `--health-cmd` |
| `restart` | Yeniden başlatma politikası | `--restart` |
| `command` | CMD'yi ezer | `IMAGE <komut>` |
| `entrypoint` | ENTRYPOINT'i ezer | `--entrypoint` |

> 🎓 **Eğitmen notu:** Tabloyu gösterirken şunu vurgulayın: **Compose yeni bir kavram getirmiyor.** Sabahtan beri öğrendiğimiz her `docker run` bayrağının YAML karşılığı var. Compose = önceki lab'ların **bildirimsel (declarative)** hali.

> 💡 **İpucu:** Dosya adı `compose.yaml` (önerilen) veya `docker-compose.yml` (eski) olabilir. En üstteki `version: "3.8"` satırı artık **gereksizdir** ve uyarı verir; yazmayın.

### `.env` dosyası ve değişken yerleştirme

`.env`:
```ini
APP_BASLIK=Docker Egitimi Sayaci
WEB_PORT=8000
```

| Söz dizimi | Anlamı |
|---|---|
| `${DEGISKEN}` | Değeri yerleştir (yoksa boş + uyarı) |
| `${DEGISKEN:-varsayilan}` | Yoksa veya boşsa varsayılanı kullan |
| `${DEGISKEN:?hata mesajı}` | Yoksa **hata ver ve dur** (zorunlu değişkenler için) |
| `$$` | Gerçek `$` karakteri (container'a iletilir) |

Compose'un dosyayı nasıl yorumladığını görmek için:

```bash
docker compose config
```

> ❓ **Soru:** `docker compose config` çıktısında `${WEB_PORT:-8000}` neye dönüştü? `.env` dosyasında `WEB_PORT=9000` yapsaydınız ne olurdu?

---

## Bölüm B — Temel yaşam döngüsü

### B1. Ayağa kaldır

```bash
docker compose up -d --build
```

Çıktıyı izleyin: önce network'ler ve volume oluşur, sonra **redis başlar**, **healthy** olunca **web başlar**.

```
 ✔ Network sayac_frontend    Created
 ✔ Network sayac_backend     Created
 ✔ Volume "sayac_redis-data" Created
 ✔ Container sayac-redis-1   Healthy
 ✔ Container sayac-web-1     Started
```

Tarayıcı: http://localhost:8000 → Sayfayı birkaç kez yenileyin, sayaç artıyor.

### B2. Durum ve loglar

```bash
docker compose ps
docker compose logs
docker compose logs -f web          # sadece web, canlı (Ctrl+C)
docker compose logs --tail 20 redis
```

### B3. Servis içinde komut çalıştırma

```bash
docker compose exec redis redis-cli GET ziyaret
docker compose exec web python -c "import socket; print(socket.gethostbyname('redis'))"
docker compose exec web sh
```

> 💡 **İpucu:** `docker compose exec` **servis adını** kullanır (`web`), container adını (`sayac-web-1`) değil.

### B4. İsimlendirmeyi inceleyin

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker network ls --filter name=sayac
docker volume ls --filter name=sayac
```

Format: `<proje>-<servis>-<numara>`, `<proje>_<ağ>`, `<proje>_<volume>`.

### B5. İzolasyonu doğrulayın

```bash
# redis host'a açık DEĞİL → bağlantı kurulamaz
docker run --rm redis:7-alpine redis-cli -h host.docker.internal -p 6379 ping
```

Beklenen: `Could not connect to Redis at host.docker.internal:6379: Connection refused`

### B6. Durdur / başlat / kaldır

```bash
docker compose stop            # container'ları durdur (silmez)
docker compose start           # tekrar başlat
docker compose restart web     # tek servisi yeniden başlat
docker compose down            # container + network'leri SİL (volume KALIR)
```

`down` sonrası tekrar `up -d` yapın → sayaç **kaldığı yerden devam eder** (volume korundu).

```bash
docker compose up -d
```

> ⚠️ **Dikkat:** `docker compose down -v` → **volume'ları da siler**, sayaç sıfırlanır. Veritabanlı projelerde bu komutla veri kaybı çok sık yaşanır.

---

## Bölüm C — `depends_on` ve healthcheck

```yaml
depends_on:
  redis:
    condition: service_healthy
```

| Koşul | Anlamı |
|---|---|
| `service_started` | Container başladı (varsayılan) — içindeki uygulama hazır **olmayabilir** |
| `service_healthy` | Container'ın `healthcheck`'i başarılı |
| `service_completed_successfully` | Container çalışıp **0 koduyla bitti** (ör. DB migration job'u) |

Healthcheck durumunu görün:

```bash
docker compose ps
docker inspect sayac-redis-1 --format "{{json .State.Health}}"
```

> 🎓 **Eğitmen notu:** "Başladı" ≠ "Hazır". Postgres container'ı saniyeler içinde başlar ama bağlantı kabul etmesi birkaç saniye daha sürer. `condition: service_healthy` olmadan web servisi ilk istekte hata verebilir. Yine de **uygulamanın kendisi de yeniden deneme (retry) mantığına sahip olmalıdır** — production'da (ör. Kubernetes) `depends_on` diye bir şey yoktur.

---

## Bölüm D — Canlı geliştirme: `docker compose watch` (bonus)

```bash
docker compose watch
```

Ayrı bir terminalde veya editörde `web/app.py` dosyasını açın ve `return` satırındaki metni değiştirin. Kaydedin.

- `action: sync` → dosya container'a kopyalanır (image build edilmez).
- `requirements.txt` değişirse → `action: rebuild` → image otomatik yeniden build edilir.

Ctrl+C ile çıkın.

> 💡 **İpucu:** Flask'ın kod değişikliğinde kendini yeniden yüklemesi için debug modu gerekir. Denemek isterseniz `compose.yaml`'da `environment` altına `FLASK_DEBUG: "1"` ekleyin.

---

## Bölüm E — Reverse proxy ve ölçekleme

Önce Aşama 1'i kapatın:

```bash
docker compose down
```

`compose.proxy.yaml`'daki farklara bakın:

```yaml
services:
  proxy:
    image: nginx:1.27-alpine
    ports:
      - "8080:80"               # dışarıya açılan TEK servis
    volumes:
      - ./proxy/nginx.conf:/etc/nginx/conf.d/default.conf:ro   # bind mount
    depends_on:
      web:
        condition: service_healthy
    networks:
      - frontend

  web:
    build: ./web
    image: sayac-web:1.0.0
    # ports YOK! Scale edilebilmesi için host portu verilmez (çakışır).
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
    ...
```

`proxy/nginx.conf`:
```nginx
upstream web_backend {
    server web:5000;       # "web" → Docker DNS → tüm web container'larının IP'leri
}
server {
    listen 80;
    location / {
        proxy_pass http://web_backend;
    }
}
```

```bash
docker compose -f compose.proxy.yaml up -d --build --scale web=3
```

```bash
docker compose -f compose.proxy.yaml ps
```

3 adet `web` container'ı göreceksiniz. Tarayıcı: http://localhost:8080 → **birkaç kez yenileyin**, "cevap veren container" değeri değişiyor, sayaç ise **ortak** (hepsi aynı redis'i kullanıyor).

Komut satırından:

**bash:**
```bash
for i in 1 2 3 4 5 6; do curl -s http://localhost:8080; done
```

**PowerShell:**
```powershell
1..6 | ForEach-Object { (Invoke-WebRequest -UseBasicParsing http://localhost:8080).Content }
```

DNS'in birden fazla IP döndürdüğünü görün:

```bash
docker compose -f compose.proxy.yaml exec proxy nslookup web
```

Çalışırken ölçeği değiştirin:

```bash
docker compose -f compose.proxy.yaml up -d --scale web=5
docker compose -f compose.proxy.yaml restart proxy
```

> ⚠️ **Dikkat:** nginx, `web` adını **başlangıçta bir kez** çözümler. Ölçek değiştirdikten sonra proxy'yi yeniden başlatmanız gerekir. (Production'da bu iş Kubernetes Service, Traefik gibi dinamik çözümlerle yapılır.)

> ❓ **Soru:** `web` servisine `ports: - "8000:5000"` ekleyip `--scale web=3` yapsaydık ne olurdu?

```bash
docker compose -f compose.proxy.yaml down
```

---

## Bölüm F — Secrets

`compose.secrets.yaml`:
```yaml
name: secret-demo
services:
  demo:
    image: alpine:3.20
    command: ["sh", "-c", "ls -l /run/secrets; cat /run/secrets/db_sifre; env | grep -i sifre || echo 'env icinde YOK'"]
    secrets:
      - db_sifre
secrets:
  db_sifre:
    file: ./db_sifre.txt
```

```bash
docker compose -f compose.secrets.yaml up
docker compose -f compose.secrets.yaml down
```

Secret, uygulamaya **dosya** olarak (`/run/secrets/db_sifre`) sunulur; ortam değişkenlerinde ve `docker inspect` çıktısında görünmez. Resmi image'ların çoğu bunun için `_FILE` son ekli değişkenleri destekler (ör. `POSTGRES_PASSWORD_FILE: /run/secrets/db_sifre`).

---

## Sık kullanılan Compose komutları

| Komut | Açıklama |
|---|---|
| `docker compose up -d` | Arka planda başlat |
| `docker compose up -d --build` | Image'ları yeniden build edip başlat |
| `docker compose ps` | Servis durumları |
| `docker compose logs -f <servis>` | Canlı log |
| `docker compose exec <servis> <komut>` | Çalışan servis içinde komut |
| `docker compose run --rm <servis> <komut>` | Yeni, tek seferlik container |
| `docker compose build` | Sadece build |
| `docker compose pull` | Image'ları güncelle |
| `docker compose config` | Birleştirilmiş/yorumlanmış YAML'ı göster |
| `docker compose stop` / `start` | Durdur / başlat |
| `docker compose down` | Kaldır (volume kalır) |
| `docker compose down -v` | Kaldır + volume'ları **SİL** |
| `docker compose -f <dosya> ...` | Farklı dosya kullan |
| `docker compose watch` | Dosya değişikliklerini izle |

---

## 🧪 Kendin dene
1. `compose.yaml`'a **Redis Commander** web arayüzünü ekleyin:
   ```yaml
     redis-ui:
       image: rediscommander/redis-commander:latest
       environment:
         REDIS_HOSTS: local:redis:6379
       ports:
         - "8081:8081"
       networks:
         - backend
       depends_on:
         redis:
           condition: service_healthy
   ```
   `docker compose up -d` sonrası http://localhost:8081 adresinde `ziyaret` anahtarını bulun.
2. `.env` dosyasında `APP_BASLIK` değerini değiştirip `docker compose up -d` çalıştırın. Hangi container yeniden oluşturuldu? Neden sadece o?
3. `web` servisine bellek limiti ekleyin (`deploy: resources: limits: memory: 128M`) ve `docker stats` ile doğrulayın.

## 🧹 Temizlik
```bash
docker compose down -v
docker compose -f compose.proxy.yaml down -v
docker image rm sayac-web:1.0.0
```

## 📌 Özet
- Compose = çok servisli uygulamanın **bildirimsel, versiyonlanabilir** tanımı.
- Her servis için otomatik: **ortak network + servis adıyla DNS**.
- `depends_on` + `condition: service_healthy` → doğru başlama sırası.
- Sadece dışarıya açılması gereken servise `ports` verin; diğerleri iç ağda kalsın.
- `down` volume'u korur, `down -v` **siler**.
