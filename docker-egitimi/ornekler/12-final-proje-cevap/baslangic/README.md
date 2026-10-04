# Lab 12 — Final Projesi: Ziyaretçi Defteri API 🐳

Flask + PostgreSQL ile yazılmış bir API'nin **production'a hazır** şekilde container'laştırılması.
Bu README hem **çözümün ne yaptığını** hem de **neden böyle yapıldığını** açıklar.

---

## 📁 Klasör yapısı

```
baslangic/
├── README.md               ← bu dosya
├── compose.yaml            ← Görev 3: ana Compose dosyası
├── compose.bonus.yaml      ← Bonus 1-2-3: secret + internal network + adminer
├── .env.ornek              ← örnek ortam değişkenleri (.env olarak kopyalanır)
├── .gitignore              ← .env ve secrets/ git'e girmez
└── app/
    ├── Dockerfile          ← Görev 1
    ├── .dockerignore       ← Görev 2
    ├── app.py
    ├── requirements.txt
    ├── NOTLAR.md           ← image'a girmez
    └── tests/              ← image'a girmez
```

> **Not:** Lab klasörünüzde `app.py`, `requirements.txt`, `NOTLAR.md` ve `tests/` zaten var.
> Buradakiler aynı arayüzü sağlayan eşdeğerlerdir (paket tek başına da çalışsın diye).
> Kendi klasörünüze **sadece** şunları kopyalamanız yeterli:
> `app/Dockerfile`, `app/.dockerignore`, `compose.yaml`, `compose.bonus.yaml`, `.env.ornek`, `.gitignore`.
> Orijinal `requirements.txt`'niz farklı paketler içerse bile Dockerfile genel yazıldığı için değişiklik gerekmez.

---

## 🚀 Hızlı başlangıç

```bash
cd ornekler/12-final-proje/baslangic
cp .env.ornek .env          # Windows PowerShell: Copy-Item .env.ornek .env
# .env içindeki GRUP_ADI'yi kendi grup adınızla değiştirin (küçük harf!)
docker compose up -d --build
docker compose ps           # api ve db "healthy" olmalı
```

---

## Görev 1 — Dockerfile

```
┌──────────── builder (python:3.12-slim) ────────────┐
│  venv oluştur → requirements.txt → pip install       │
└──────────────────────┬──────────────────────────────┘
                       │  COPY --from=builder /opt/venv
┌──────────── runtime (python:3.12-slim) ────────────┐
│  app kullanıcısı → venv → kod → HEALTHCHECK → CMD   │
└─────────────────────────────────────────────────────┘
```

| Gereksinim | Nasıl karşılandı | Neden |
|---|---|---|
| **Base image** | `python:3.12-slim` | Resmî image, küçük, glibc tabanlı → `psycopg2-binary` hazır wheel ile kurulur. Alpine'da (musl) paketler derlenmek zorunda kalabilir. Sürüm sabit, `latest` değil. |
| **Multi-stage** | `builder` aşaması bağımlılıkları `/opt/venv`'e kurar; `runtime` sadece bu klasörü alır | pip cache'i, derleme artıkları final image'a girmez. Tek `COPY` ile taşınabilmesi için virtualenv kullanıldı. |
| **Layer cache** | Önce `COPY requirements.txt` + `pip install`, kod en son | Sadece kod değiştiğinde `pip install` katmanı cache'ten gelir → rebuild saniyeler sürer. |
| **Root olmayan kullanıcı** | `useradd --system --uid 10001 app` + `USER app` | Container kaçışı durumunda saldırganın yetkisi sınırlı kalır. Dosyalar `COPY --chown=app:app` ile kopyalanır. |
| **HEALTHCHECK** | `python -c "urllib.request.urlopen('.../health')"` | slim image'da `curl` yok; sırf healthcheck için paket kurup image'ı büyütmek yerine zaten var olan Python kullanıldı. `/health` DB'yi de test ettiği için gerçek sağlık durumunu yansıtır. |
| **Exec form CMD** | `CMD ["gunicorn", "--bind", "0.0.0.0:5000", ...]` | gunicorn PID 1 olur, `docker stop`'un SIGTERM'ini doğrudan alır ve düzgün kapanır. Shell form'da sinyal `/bin/sh`'a gider, 10 sn sonra SIGKILL gelir. |
| **LABEL** | OCI standart etiketleri (`org.opencontainers.image.title` vb.) | `docker inspect` ile image hakkında bilgi alınabilir. |

Ek olarak: `PYTHONUNBUFFERED=1` (loglar anında `docker logs`'a düşer), `PYTHONDONTWRITEBYTECODE=1` (container içinde `.pyc` üretilmez).

---

## Görev 2 — `.dockerignore`

`app/.dockerignore` dışarıda bırakılanlar: `tests/`, `*.md`, `__pycache__/`, `.env`, `.env.*`, `Dockerfile*`, `compose*.yaml`, `.git/`, editör klasörleri.

> ⚠️ **En sık hata:** `.dockerignore` **build context'in kökünde** olmalı.
> Compose'ta `context: ./app` olduğu için dosya `app/` içinde; `baslangic/` altına koyulursa **hiç etkisi olmaz**.

`.env`'i dışlamak kritik: `COPY . .` şifreleri image'a gömerse, image'ı çeken herkes `docker history`/katmanlardan şifreyi okuyabilir.

---

## Görev 3 — `compose.yaml`

```
            Host (sizin bilgisayarınız)
                 │ :8000
   ┌─────────────┼──────── frontend ────────┐
   │        ┌────▼────┐                     │
   │        │   api   │                     │
   └────────┤  :5000  ├─────────────────────┘
   ┌────────┤         ├──── backend ────────┐
   │        └────┬────┘                     │
   │             │ db:5432                  │
   │        ┌────▼────┐     ┌────────────┐  │
   │        │   db    │────▶│ db-verisi  │  │
   │        │(no port)│     │  (volume)  │  │
   │        └─────────┘     └────────────┘  │
   └────────────────────────────────────────┘
```

| Gereksinim | Çözüm |
|---|---|
| `api` (build) + `db` (`postgres:16-alpine`) | ✅ |
| Named volume | `db-verisi:/var/lib/postgresql/data` |
| DB healthcheck | `pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}` |
| api, DB healthy olunca başlar | `depends_on: db: condition: service_healthy` |
| İki network | `api` → frontend + backend, `db` → **sadece** backend |
| DB host'a port açmaz | `db` servisinde `ports:` **yok** |
| Şifreler `.env`'den | `${POSTGRES_PASSWORD:?...}` — YAML'da tek bir şifre bile yok |
| `restart: unless-stopped` | ✅ (db'ye de eklendi) |
| Image adı | `localhost:5001/${GRUP_ADI}/ziyaretci-defteri:${APP_SURUM}` |

### Önemli detaylar

- **`$$` kaçışı:** Compose, `${...}` gördüğünde değeri `.env`'den doldurmaya çalışır. `$${POSTGRES_USER}` yazınca Compose bunu `${POSTGRES_USER}` olarak bırakır ve değişken **container içindeki shell** tarafından açılır.
- **`DATABASE_URL`'de host = `db`:** Container içinde `localhost` container'ın kendisidir. Compose'un dahili DNS'i servis adını (`db`) doğru IP'ye çözer.
- **`${VAR:?mesaj}` sözdizimi:** Değişken tanımlı değilse Compose anlamlı bir hatayla durur; boş şifreyle sessizce başlamaz.
- **`.env` iki iş görür:** Compose dosyasındaki `${...}` değerlerini doldurur; container'a ise sadece `environment:` altında açıkça verilenler geçer.

Kontrol: `docker compose config` çalıştırınca değişkenlerin doldurulmuş halini görebilirsiniz.

---

## Görev 4 — Çalıştır ve test et

**bash / Git Bash:**
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/mesajlar -H "Content-Type: application/json" \
     -d '{"isim":"Ayşe","mesaj":"Docker eğitimi harikaydı!"}'
curl http://localhost:8000/mesajlar
```

**PowerShell:**
```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod -Method Post -Uri http://localhost:8000/mesajlar -ContentType "application/json" `
  -Body '{"isim":"Ayse","mesaj":"Docker egitimi harikaydi!"}'
Invoke-RestMethod http://localhost:8000/mesajlar
```

Beklenen çıktı örnekleri:
```json
{"durum": "saglikli", "veritabani": "bagli"}
{"id": 1, "isim": "Ayşe", "mesaj": "Docker eğitimi harikaydı!", "olusturma": "2026-10-04T12:14:46+00:00"}
```

---

## Görev 5 — Kalıcılığı kanıtla

```bash
docker compose down          # container'lar ve network'ler silinir, VOLUME KALIR
docker compose up -d
curl http://localhost:8000/mesajlar   # Ayşe'nin mesajı hâlâ orada ✅
docker volume ls | grep db-verisi
```

> ⚠️ `docker compose down -v` **volume'u da siler** → veri gider. "Kalıcılık çalışmıyor" sanmayın.

---

## Görev 6 — Registry'e push

```bash
# Lab 11'deki yerel registry (çalışmıyorsa):
docker run -d -p 5001:5000 --name registry --restart unless-stopped registry:2

docker compose push api
curl http://localhost:5001/v2/_catalog
# {"repositories":["grup1/ziyaretci-defteri"]}
curl http://localhost:5001/v2/grup1/ziyaretci-defteri/tags/list
# {"name":"grup1/ziyaretci-defteri","tags":["1.0.0"]}
```

`localhost` registry'leri Docker tarafından varsayılan olarak "insecure" kabul edilir, ek ayar gerekmez.

---

## ✅ Kendi kendini kontrol

| Kontrol | Komut | Beklenen |
|---|---|---|
| Image boyutu | `docker images --filter reference="*ziyaretci-defteri*"` | < 200 MB (~150 MB civarı) |
| Root değil | `docker compose exec api whoami` | `app` |
| tests/ ve .md yok | `docker compose exec api ls -la /app` | sadece `app.py`, `requirements.txt` |
| Healthcheck | `docker compose ps` | `(healthy)` |
| DB host'a kapalı | `docker run --rm postgres:16-alpine pg_isready -h host.docker.internal -p 5432` | `no response` |
| Şifre YAML'da yok | `grep -i sifre compose.yaml` | eşleşme yok |
| Network'ler | `docker network inspect baslangic_backend` | api + db |

---

## 🎁 Bonus görevler — `compose.bonus.yaml`

Ana stack'i kapatıp bonus dosyasıyla başlatın (aynı volume kullanılır, veri korunur):

```bash
docker compose down
mkdir -p secrets
printf '%s' "GucluBirSifre2026" > secrets/db_sifre.txt   # .env'deki şifreyle AYNI
docker compose -f compose.bonus.yaml up -d --build
```

PowerShell için secret dosyası (sonda satır sonu olmaması önemli):
```powershell
New-Item -ItemType Directory -Force secrets | Out-Null
[IO.File]::WriteAllText("$PWD\secrets\db_sifre.txt", "GucluBirSifre2026")
```

### 1. Compose secret
`db` servisi şifreyi `POSTGRES_PASSWORD_FILE=/run/secrets/db_sifre` ile **dosyadan** okur.
Fark: `docker inspect <db>` çıktısında artık şifre ortam değişkeni olarak görünmez.

> Not: Postgres şifreyi **sadece volume ilk oluşturulurken** ayarlar. Volume zaten varsa şifreyi değiştirmek mevcut DB'yi etkilemez.

### 2. `backend` → `internal: true`
```bash
docker compose -f compose.bonus.yaml exec db ping -c 1 8.8.8.8
# ping: sendto: Network unreachable   ← db'nin internete çıkışı kesildi
```
`api` hâlâ çalışır çünkü `frontend` ağına da bağlı. DB ise artık hem host'tan hem internetten tamamen izole.

### 3. Adminer → http://localhost:8081
Giriş: Sistem `PostgreSQL`, Sunucu `db`, kullanıcı/şifre/veritabanı `.env`'deki değerler.

**Hangi ağlara bağlanmalı?** `backend` (db'ye erişim için) **ve** `frontend`.
Sadece `internal: true` bir ağdaki servisin portu host'a **yayınlanamaz** — `8081:8080` yazsanız bile erişilemez. Bu yüzden internal olmayan bir ağ da gerekir.

### 4. Güvenlik taraması
```bash
docker scout quickview localhost:5001/grup1/ziyaretci-defteri:1.0.0
docker scout cves      localhost:5001/grup1/ziyaretci-defteri:1.0.0 --only-severity critical,high
```
Slim base image + sabit sürümlü paketler kritik açık sayısını düşük tutar; çıkan açıklar genelde base image'dan gelir ve `docker compose build --pull` ile güncel base çekilerek azaltılır.

---

## 🩺 Sorun giderme

| Belirti | Sebep / çözüm |
|---|---|
| `api` sürekli restart | `docker compose logs api` — çoğunlukla `DATABASE_URL` hatası |
| `required variable GRUP_ADI is missing` | `.env` dosyası yok → `cp .env.ornek .env` |
| `/health` 503 | DB'ye bağlanamıyor: şifre `.env` ile volume'daki DB uyuşmuyor olabilir → `docker compose down -v` (veri silinir!) |
| `invalid reference format` | `GRUP_ADI` büyük harf/boşluk içeriyor; küçük harf ve tire kullanın |
| Push `connection refused` | Registry çalışmıyor → Görev 6'daki `docker run` komutu |
| Şifrede `@ : / #` var | `DATABASE_URL`'i bozar; harf+rakam kullanın veya URL-encode edin |

---

## 🧹 Temizlik

```bash
docker compose down            # veriyi korur
docker compose down -v         # veriyi de siler
docker compose -f compose.bonus.yaml down -v
```
