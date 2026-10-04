# Lab 12 — Final Projesi: Ziyaretçi Defteri API

**Süre:** 45 dk · **Çalışma şekli:** 2'li gruplar (12 kişi → 6 grup) · **Klasör:** `ornekler/12-final-proje`

## Amaç
Eğitimde öğrendiğiniz **her şeyi** tek bir projede birleştirmek. Uygulama kodu hazır; siz onu **production'a hazır şekilde** container'laştıracaksınız.

---

## Uygulama

`baslangic/app/` klasöründe bir **Flask + PostgreSQL** API var:

| Endpoint | Açıklama |
|---|---|
| `GET /` | Uygulama bilgisi |
| `GET /health` | Sağlık kontrolü (DB bağlantısını da test eder) |
| `GET /mesajlar` | Tüm mesajları listeler |
| `POST /mesajlar` | `{"isim": "...", "mesaj": "..."}` ile yeni mesaj ekler |

Uygulama konfigürasyonu:
- `DATABASE_URL` — ör. `postgresql://defter:sifre@db:5432/defter`
- `APP_ADI` — opsiyonel başlık
- Production sunucusu: `gunicorn --bind 0.0.0.0:5000 app:app`

Klasör içeriği:
```
baslangic/app/
├── app.py
├── requirements.txt
├── NOTLAR.md          ← image'a girmemeli
└── tests/             ← image'a girmemeli
```

---

## Görevler

Çalışmanızı `baslangic/` klasöründe yapın. Başlangıç için `baslangic/.env.ornek` dosyasını `.env` adıyla kopyalayın.

### Görev 1 — Dockerfile (`baslangic/app/Dockerfile`)
- [ ] Uygun bir base image seçin (gerekçenizi yorum satırı olarak yazın)
- [ ] **Multi-stage** build kullanın (bağımlılık kurulumu ayrı aşamada)
- [ ] **Layer cache** dostu sıralama (önce `requirements.txt`, sonra kod)
- [ ] **Root olmayan** bir kullanıcı ile çalışsın
- [ ] `HEALTHCHECK` tanımlayın (`/health` endpoint'i)
- [ ] `CMD` **exec form** ile gunicorn'u başlatsın
- [ ] `LABEL` ile en az başlık bilgisi

### Görev 2 — `.dockerignore` (`baslangic/app/.dockerignore`)
- [ ] `tests/`, `*.md`, `__pycache__/`, `.env` ve Docker dosyaları image'a girmesin

### Görev 3 — `compose.yaml` (`baslangic/compose.yaml`)
- [ ] `api` servisi (build ile) ve `db` servisi (`postgres:16-alpine`)
- [ ] DB verisi **named volume**'da kalıcı olsun
- [ ] DB için **healthcheck**; `api`, DB **healthy** olunca başlasın
- [ ] **İki network:** `frontend` (api) ve `backend` (api + db). DB host'a **port açmasın**
- [ ] Tüm şifre/kullanıcı bilgileri **`.env` dosyasından** gelsin (YAML içinde şifre yazmayın)
- [ ] `api` için `restart: unless-stopped`
- [ ] Image adı: `localhost:5001/<grup-adi>/ziyaretci-defteri:${APP_SURUM}`

### Görev 4 — Çalıştır ve test et

```bash
cd ornekler/12-final-proje/baslangic
docker compose up -d --build
docker compose ps
```

**bash / Git Bash:**
```bash
curl http://localhost:8000/health
curl -X POST http://localhost:8000/mesajlar -H "Content-Type: application/json" -d '{"isim":"Ayşe","mesaj":"Docker eğitimi harikaydı!"}'
curl http://localhost:8000/mesajlar
```

**PowerShell:**
```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod -Method Post -Uri http://localhost:8000/mesajlar -ContentType "application/json" -Body '{"isim":"Ayse","mesaj":"Docker egitimi harikaydi!"}'
Invoke-RestMethod http://localhost:8000/mesajlar
```

### Görev 5 — Kalıcılığı kanıtla
- [ ] `docker compose down` → `docker compose up -d` → mesajlar hâlâ duruyor mu?

### Görev 6 — Registry'e push
- [ ] Lab 11'deki yerel registry'yi başlatın
- [ ] `docker compose push api` ile image'ı push edin
- [ ] `http://localhost:5001/v2/_catalog` ile doğrulayın

---

## Değerlendirme kriterleri (toplam 100)

| Kriter | Puan |
|---|---|
| Uygulama çalışıyor, POST/GET başarılı | 20 |
| Multi-stage + cache dostu Dockerfile | 15 |
| Root olmayan kullanıcı + HEALTHCHECK + exec form CMD | 15 |
| `.dockerignore` doğru (image içinde `tests/` ve `.md` yok) | 10 |
| Volume ile kalıcılık kanıtlandı | 10 |
| Network izolasyonu (DB host'a kapalı, sadece backend'de) | 10 |
| Şifreler `.env`'den geliyor, YAML'da yok | 10 |
| Image doğru tag'le registry'e push edildi | 10 |

### Kendi kendini kontrol komutları

```bash
# Image boyutu (hedef: < 200 MB)
docker images --filter reference="*ziyaretci-defteri*"

# Kim olarak çalışıyor? (root OLMAMALI)
docker compose exec api whoami

# tests/ ve NOTLAR.md image'da OLMAMALI
docker compose exec api ls -la /app

# Healthcheck durumu
docker compose ps

# DB host'tan erişilebilir OLMAMALI (bağlantı reddedilmeli)
docker run --rm postgres:16-alpine pg_isready -h host.docker.internal -p 5432
```

---

## 🎁 Bonus görevler (erken bitirenler için)
1. `db` servisinin şifresini `.env` yerine **Compose secret** ile verin (`POSTGRES_PASSWORD_FILE` kullanın).
2. `backend` network'ünü `internal: true` yapın. Ne değişti? (`docker compose exec db ping -c 1 8.8.8.8`)
3. Bir `adminer` servisi ekleyip (`adminer:latest`, port `8081:8080`) veritabanını web arayüzünden inceleyin. Hangi ağ(lar)a bağlanması gerektiğini düşünün (`internal: true` bir ağdaki servis host'tan port ile erişilebilir mi?).
4. `docker scout quickview` ile image'ınızı tarayın, kritik açık var mı?

---

## 🎓 Eğitmen notu

- `cozum/` klasöründe referans çözüm var. Katılımcılara **proje sonunda** gösterin; grupların kendi çözümleriyle farkları konuşun.
- Gruplardan 2–3 tanesine 3'er dakikalık "demo" yaptırın: `docker compose up`, bir POST, `down`/`up`, verinin durduğunu gösterme.
- Sık görülen hatalar:
  - `DATABASE_URL` içinde host olarak `localhost` yazmak (doğrusu: servis adı `db`)
  - Postgres healthcheck'te `$` karakterini kaçırmamak (`$${POSTGRES_USER}` gerekir, yoksa compose değişkeni sanılır)
  - `.dockerignore`'u `app/` yerine üst klasöre koymak (build context `./app` olduğu için yanlış yer)
  - `down -v` ile veriyi silip "kalıcılık çalışmıyor" sanmak

### Referans çözümü çalıştırmak

```bash
cd ornekler/12-final-proje/cozum
docker compose up -d --build
```
