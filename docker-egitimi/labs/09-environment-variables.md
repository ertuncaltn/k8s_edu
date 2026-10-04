# Lab 09 — Environment Variable ile Konfigürasyon Yönetimi

**Süre:** 30 dk · **Klasör:** `ornekler/09-env`

## Amaç
- **"Build once, run anywhere"** prensibini uygulamak: aynı image → dev / test / prod
- `ENV`, `ARG`, `-e`, `--env-file` farklarını ve **öncelik sırasını** öğrenmek
- Gizli bilgilerin (şifre, token) neden environment variable'da **tam güvende olmadığını** görmek

---

## Kavram

**12-Factor App — Madde III:** *Konfigürasyonu ortamda saklayın.* Ortama göre değişen her şey (DB adresi, log seviyesi, özellik bayrakları) koda veya image'a gömülmez; çalışma anında dışarıdan verilir.

```
                    ┌──────────────────┐
                    │  uygulama:1.0.0  │   ← TEK image
                    └────────┬─────────┘
          ┌──────────────────┼──────────────────┐
     -e APP_ORTAM=dev   --env-file test.env  --env-file prod.env
          ▼                  ▼                  ▼
     Geliştirme            Test              Production
```

### ARG vs ENV

| | `ARG` | `ENV` |
|---|---|---|
| Ne zaman geçerli? | **Sadece build** sırasında | Build + **çalışan container** |
| Nasıl verilir? | `docker build --build-arg X=1` | Dockerfile'da / `docker run -e X=1` |
| Çalışan container'da görünür mü? | ❌ (ENV'e aktarılmadıkça) | ✅ |
| Kullanım | Sürüm numarası, base image tag'i | Uygulama konfigürasyonu |

### Öncelik sırası (yüksekten düşüğe)

```
  1. docker run -e APP_MESAJ=...            ← en yüksek
  2. docker run --env-file dosya.env
  3. Dockerfile içindeki ENV APP_MESAJ=...
  4. Uygulamanın koddaki varsayılan değeri  ← en düşük
```

---

## Adımlar

```bash
cd ornekler/09-env
```

`app.py` konfigürasyonunu **sadece** ortam değişkenlerinden okur:

```python
MESAJ = os.getenv("APP_MESAJ", "Varsayılan mesaj")
ORTAM = os.getenv("APP_ORTAM", "gelistirme")
RENK  = os.getenv("APP_RENK", "#555555")
PORT  = int(os.getenv("APP_PORT", "8000"))
DB_SIFRE = os.getenv("DB_SIFRE")
```

### 1. Build (ARG ile sürüm bilgisi)

```bash
docker build --build-arg BUILD_VERSIYON=1.4.2 -t env-demo:1.4.2 .
```

### 2. Dockerfile varsayılanlarıyla çalıştırma

```bash
docker run -d --name env-varsayilan -p 8001:8000 env-demo:1.4.2
```

http://localhost:8001 → "Dockerfile'daki varsayılan mesaj", Ortam: gelistirme, DB şifresi: TANIMLI DEĞİL

### 3. `-e` ile tek tek değişken verme

```bash
docker run -d --name env-e -p 8002:8000 -e APP_MESAJ="Komut satırından merhaba" -e APP_RENK="#6a1b9a" env-demo:1.4.2
```

http://localhost:8002 → mor arka plan, yeni mesaj.

### 4. `--env-file` ile ortam dosyası

`test.env`:
```ini
APP_MESAJ=Test ortamina hos geldiniz
APP_ORTAM=test
APP_RENK=#b35900
DB_SIFRE=test-sifresi
```

```bash
docker run -d --name env-test -p 8003:8000 --env-file test.env env-demo:1.4.2
docker run -d --name env-prod -p 8004:8000 --env-file prod.env env-demo:1.4.2
```

http://localhost:8003 (turuncu, test) ve http://localhost:8004 (yeşil, production)

> 🎓 **Eğitmen notu:** Dört sekmeyi yan yana açtırın: **aynı image**, dört farklı davranış. "Test'te çalıştı, prod'da çalışmadı" sorununun büyük kısmı, ortamlar için **ayrı image build etmekten** kaynaklanır. Doğru yaklaşım: bir kez build et, **aynı image**'ı konfigürasyonla terfi ettir (promote).

> ⚠️ **Dikkat:** `--env-file` içinde tırnak **kullanmayın**. `APP_MESAJ="Merhaba"` yazarsanız tırnaklar da değerin parçası olur. (Compose'un `.env` dosyası ise tırnakları farklı işler — Lab 10.)

### 5. Öncelik sırasını test edin

```bash
docker run --rm --env-file test.env -e APP_ORTAM=ezildi env-demo:1.4.2 sh -c "echo ORTAM=\$APP_ORTAM MESAJ=\$APP_MESAJ"
```

**PowerShell'de** `\$` yerine `` `$ `` gerekir; bunun yerine şunu kullanın:
```powershell
docker run --rm --env-file test.env -e APP_ORTAM=ezildi env-demo:1.4.2 printenv APP_ORTAM APP_MESAJ
```

Beklenen: `APP_ORTAM` = `ezildi` (`-e` kazandı), `APP_MESAJ` = test.env'den.

### 6. Host'taki değişkeni aktarma

Değer vermeden sadece isim yazarsanız, host'taki aynı isimli değişken aktarılır:

**bash:**
```bash
export APP_MESAJ="Host'tan geldim"
docker run --rm -e APP_MESAJ env-demo:1.4.2 printenv APP_MESAJ
```

**PowerShell:**
```powershell
$env:APP_MESAJ = "Host'tan geldim"
docker run --rm -e APP_MESAJ env-demo:1.4.2 printenv APP_MESAJ
```

### 7. ARG çalışan container'da var mı?

```bash
docker run --rm env-demo:1.4.2 printenv BUILD_VERSIYON
```

Çıktı `1.4.2` → çünkü Dockerfile'da `ENV BUILD_VERSIYON=${BUILD_VERSIYON}` ile ARG'ı ENV'e **aktardık**. Bu satır olmasaydı değer görünmezdi.

---

## 🔐 Bölüm B — Gizli bilgiler ve environment variable'lar

```bash
docker inspect env-prod --format "{{json .Config.Env}}"
```

Beklenen: `DB_SIFRE=bu-gercekte-secret-manager-dan-gelmeli` **açıkça görünür**.

```bash
docker exec env-prod printenv DB_SIFRE
```

> ⚠️ **Dikkat:** Environment variable'lar:
> - `docker inspect` ile Docker'a erişimi olan herkes tarafından okunabilir,
> - Hata raporlarına, log'lara, crash dump'lara sızabilir,
> - Alt process'lere otomatik miras kalır.
>
> **Asla yapmayın:** `ENV DB_SIFRE=...` veya `ARG DB_SIFRE=...` → Dockerfile'daki değer **image metadata'sına / history'sine gömülür** ve image'ı çeken herkes görür:
> ```bash
> docker history --no-trunc env-demo:1.4.2
> ```

**Daha güvenli seçenekler (olgunluk sırasıyla):**

| Yöntem | Açıklama |
|---|---|
| `--env-file` (git'e eklenmeyen) | Geliştirme için kabul edilebilir |
| **Docker / Compose secrets** | Dosya olarak `/run/secrets/<ad>` altına bağlanır, `inspect`'te görünmez (Lab 10'da örnek) |
| **Harici secret yöneticisi** | HashiCorp Vault, Kubernetes Secrets + External Secrets, bulut KMS |
| Build-time secret | `RUN --mount=type=secret,id=npmrc ...` (BuildKit) — secret image katmanına girmez |

---

## 🧪 Kendin dene
1. `dev.env` adında kendi ortam dosyanızı oluşturup `APP_PORT=9000` ile çalıştırın. Port mapping'i buna göre ayarlamanız gerekecek: `-p 8005:9000`.
2. `ARG` ile base image sürümünü dışarıdan verin: Dockerfile'ın başına `ARG PY_SURUM=3.12` ve `FROM python:${PY_SURUM}-slim` yazın, `--build-arg PY_SURUM=3.11` ile build edin.
3. `docker history --no-trunc env-demo:1.4.2` çıktısında `BUILD_VERSIYON` değerini bulun. ARG değerleri neden history'de görünüyor ve bu şifreler için neden tehlikeli?

## 🧹 Temizlik
```bash
docker rm -f env-varsayilan env-e env-test env-prod
docker image rm env-demo:1.4.2
```

## 📌 Özet
- **Bir kez build et, konfigürasyonla her yerde çalıştır.**
- `ARG` = build zamanı, `ENV` = çalışma zamanı. Öncelik: `-e` > `--env-file` > Dockerfile `ENV` > kod varsayılanı.
- Environment variable'lar **gizli değildir**: `docker inspect` ile görünür. Şifreleri asla Dockerfile'a yazmayın.
- Gerçek sırlar için **secrets** mekanizmalarını kullanın.
