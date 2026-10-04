# Lab 04 — .dockerignore

**Süre:** 30 dk · **Klasör:** `ornekler/04-dockerignore`

## Amaç
- **Build context** kavramını anlamak
- `.dockerignore` olmadan neler olabileceğini görmek: **yavaş build, şişkin image, sızan gizli bilgiler**
- İyi bir `.dockerignore` dosyası yazmak

---

## Kavram: Build context

`docker build -t x .` komutundaki **`.`** → "bu klasördeki **her şeyi** Docker Engine'e gönder" demektir.

```
  Sizin klasörünüz                          Docker Engine (BuildKit)
  ┌─────────────────────┐    build context   ┌────────────────────────┐
  │ app.py              │ ─────────────────▶ │ COPY . .  → image'a    │
  │ requirements.txt    │   (gönderilen her  │                        │
  │ .env   (şifreler!)  │    şey COPY . .    │                        │
  │ .git/  (tüm geçmiş) │    ile image'a     │                        │
  │ logs/               │    girebilir)      │                        │
  │ buyuk.bin (200 MB)  │                    │                        │
  └─────────────────────┘                    └────────────────────────┘
```

`.dockerignore` dosyası, context'e **gönderilmeyecek** dosyaları belirler. Söz dizimi `.gitignore`'a benzer.

---

## Adımlar

```bash
cd ornekler/04-dockerignore
```

Klasörde `app.py`, `requirements.txt`, `Dockerfile`, bir `.env` dosyası (sahte şifrelerle), `logs/` klasörü ve `.dockerignore.hazir` dosyası var.

### 1. Büyük bir "gereksiz" dosya oluşturun

Docker'ın kendisini kullanarak 200 MB'lık bir dosya üretelim (tüm işletim sistemlerinde aynı çalışır):

```bash
docker run --rm -v "${PWD}:/w" alpine:3.20 dd if=/dev/zero of=/w/buyuk.bin bs=1M count=200
```

> 💡 **İpucu:** Bu gerçek hayatta `node_modules/`, `.git/`, test verisi, veritabanı dump'ı, IDE cache'i vb. olabilir.

### 2. `.dockerignore` OLMADAN build

```bash
docker build --progress=plain -t ignore-demo:yok . 2>&1 | grep -i "transferring context"
```

**PowerShell:**
```powershell
docker build --progress=plain -t ignore-demo:yok . 2>&1 | Select-String "transferring context"
```

Beklenen: `transferring context: 209.72MB` civarı.

Image boyutuna bakın:

```bash
docker images ignore-demo
```

### 3. 🔥 Gizli bilgi sızıntısı

```bash
docker run --rm ignore-demo:yok cat /app/.env
docker run --rm ignore-demo:yok ls -la /app
```

Beklenen:

```
DB_SIFRE=CokGizliSifre123
API_ANAHTARI=sk-bu-bir-sir
```

> ⚠️ **Dikkat:** Bu image bir registry'e push edilseydi, image'ı çekebilen **herkes** şifreleri okuyabilirdi. `.env` dosyasını sonradan `RUN rm .env` ile silmek **işe yaramaz** — dosya önceki katmanda durmaya devam eder ve `docker save` ile çıkarılabilir.

> 🎓 **Eğitmen notu:** Bu, gerçek dünyada çok sık yaşanan bir güvenlik olayıdır. Public registry'lerde taranan image'larda yüzlerce gerçek API anahtarı bulunduğunu gösteren araştırmalar vardır. Katılımcılara `RUN rm .env` "çözümünün" neden işe yaramadığını Lab 02'deki katman şeması üzerinden sorun.

### 4. `.dockerignore` ekleyin

Hazır dosyayı yeniden adlandırın:

**bash / zsh:**
```bash
cp .dockerignore.hazir .dockerignore
```

**PowerShell:**
```powershell
Copy-Item .dockerignore.hazir .dockerignore
```

İçeriğini inceleyin (önemli kısımlar):

```gitignore
# Versiyon kontrol
.git
.gitignore

# Gizli bilgiler — image'a ASLA girmemeli
.env
.env.*
*.pem
*.key

# Büyük / gereksiz dosyalar
*.bin
logs/
*.log

# Python artıkları
__pycache__/
*.pyc
.venv/

# Docker dosyalarının kendisi
Dockerfile*
.dockerignore*
compose*.yaml
```

### 5. `.dockerignore` İLE build

```bash
docker build --progress=plain -t ignore-demo:var . 2>&1 | grep -i "transferring context"
```

**PowerShell:**
```powershell
docker build --progress=plain -t ignore-demo:var . 2>&1 | Select-String "transferring context"
```

Beklenen: birkaç **KB**.

```bash
docker images ignore-demo
docker run --rm ignore-demo:var ls -la /app
docker run --rm ignore-demo:var cat /app/.env
```

Beklenen son çıktı: `cat: /app/.env: No such file or directory`

### 6. Karşılaştırma tablosu

Kendi değerlerinizi doldurun:

| | `.dockerignore` yok | `.dockerignore` var |
|---|---|---|
| Context boyutu | | |
| Image boyutu | | |
| `.env` image'da mı? | | |

---

## .dockerignore kural örnekleri

| Kural | Anlamı |
|---|---|
| `*.log` | Kök dizindeki `.log` dosyaları |
| `**/*.log` | Tüm alt klasörlerdeki `.log` dosyaları |
| `logs/` | `logs` klasörü |
| `!logs/.gitkeep` | Hariç tutulan bir dosyayı **geri dahil et** |
| `#` | Yorum satırı |

> 💡 **İpucu:** Tersine yaklaşım da mümkün — **her şeyi hariç tut, sadece gerekeni dahil et**:
> ```gitignore
> *
> !app.py
> !requirements.txt
> !src/
> ```

> 💡 **İpucu:** Birden fazla Dockerfile varsa, her biri için ayrı ignore dosyası olabilir: `Dockerfile.prod` için `Dockerfile.prod.dockerignore`.

---

## 🧪 Kendin dene
1. `.dockerignore` dosyasına sadece `*` ve `!app.py` `!requirements.txt` satırlarını yazın. Build hâlâ çalışıyor mu? Image içinde ne var?
2. `.dockerignore` içinden `Dockerfile*` satırını silin. Image'ın içinde Dockerfile görünüyor mu? Bir sakıncası var mı?
3. Gerçek bir projeniz için (Node, Java, .NET...) `.dockerignore` taslağı yazın.

## 🧹 Temizlik

**bash / zsh:**
```bash
rm -f buyuk.bin .dockerignore
docker image rm ignore-demo:yok ignore-demo:var
```

**PowerShell:**
```powershell
Remove-Item buyuk.bin, .dockerignore -ErrorAction SilentlyContinue
docker image rm ignore-demo:yok ignore-demo:var
```

## 📌 Özet
- `docker build .` → klasördeki **her şey** Engine'e gönderilir.
- `.dockerignore` → **daha hızlı build**, **daha küçük image**, **sızmayan şifreler**, daha **stabil cache**.
- Gizli bilgiyi image'a koyduktan sonra silmek **işe yaramaz**; baştan girmemesini sağlayın.
- Her projenin kökünde bir `.dockerignore` olmalı — `.gitignore` kadar standart.
