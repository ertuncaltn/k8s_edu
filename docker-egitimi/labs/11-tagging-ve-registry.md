# Lab 11 — Image Tagging Stratejisi ve Registry'e Push Akışı

**Süre:** 45 dk · **Klasör:** `ornekler/11-registry` (+ `ornekler/05-multi-stage`)

## Amaç
- Image adının parçalarını (**registry / repository : tag @ digest**) anlamak
- Sağlam bir **tagging stratejisi** kurmak (semver, git SHA, `latest` tuzağı)
- Yerel bir registry çalıştırıp **tag → push → pull** akışını uçtan uca yapmak
- Docker Hub'a push akışını öğrenmek

---

## Kavram: Image adının anatomisi

```
   registry.ornek.com:5000 / ekip/sayac-web : 1.4.2 @ sha256:3f5a...
   └──────── registry ────┘ └─ repository ─┘ └ tag ┘  └── digest ──┘
          (varsayılan:           (namespace/       (değişebilir   (içerik hash'i,
         docker.io)               isim)             etiket)        DEĞİŞMEZ)
```

| Yazdığınız | Docker'ın anladığı |
|---|---|
| `nginx` | `docker.io/library/nginx:latest` |
| `nginx:1.27-alpine` | `docker.io/library/nginx:1.27-alpine` |
| `kullanici/uygulama:1.0` | `docker.io/kullanici/uygulama:1.0` |
| `localhost:5001/uygulama:1.0` | Yerel registry'deki `uygulama:1.0` |
| `ghcr.io/org/uygulama:1.0` | GitHub Container Registry |

> 🎓 **Eğitmen notu:** Kritik ayrım: **tag değişebilir bir etikettir**, bir "sürüm" garantisi değildir. Aynı `1.0` tag'i bugün bir image'ı, yarın başka bir image'ı gösterebilir. **Digest** ise içeriğin hash'idir ve asla değişmez. "Kesinlikle bu image çalışsın" diyorsanız digest kullanın.

---

## Tagging stratejisi

### `latest` tuzağı

- `latest` otomatik olarak "en yeni" **değildir** — sadece tag verilmediğinde kullanılan isimdir.
- `latest` ile deploy edilen bir sistemde "hangi sürüm çalışıyor?" sorusu cevapsız kalır.
- Rollback yapamazsınız: "bir önceki latest" diye bir şey yoktur.

### Önerilen: çoklu tag

Aynı image'a birden fazla tag verin — tag'ler **ücretsizdir** (aynı image'ı gösteren işaretçilerdir):

```
sayac-web:1.4.2          ← tam sürüm (DEĞİŞMEZ olarak davranın — üzerine yazmayın)
sayac-web:1.4            ← minör kanal (1.4.x'in en yenisi)
sayac-web:1              ← majör kanal
sayac-web:sha-3f5a9c1    ← git commit SHA (izlenebilirlik: hangi koddan build edildi?)
sayac-web:latest         ← sadece geliştirme / kolaylık
```

| Strateji | Artı | Eksi | Kullanım |
|---|---|---|---|
| **SemVer** (`1.4.2`) | İnsan okur, anlamlı | Manuel yönetim | Release'ler |
| **Git SHA** (`sha-3f5a9c1`) | Koda birebir izlenebilir | İnsan için anlamsız | CI build'leri |
| **Tarih/Build no** (`2026.09.28-45`) | Sıralanabilir | Kod ile bağ zayıf | Nightly build |
| **Ortam** (`prod`, `staging`) | — | ❌ Hangi sürüm olduğu belirsiz | **Kaçının** |

**Altın kurallar:**
1. Production deploy'ları **asla `latest`** kullanmaz.
2. Tam sürüm tag'i (`1.4.2`) bir kez push edildikten sonra **üzerine yazılmaz** (immutable). Birçok registry bunu zorlayabilir.
3. Her image'da git SHA bilgisi olsun (tag veya `LABEL org.opencontainers.image.revision`).

---

## Bölüm A — Yerel registry kurun

```bash
cd ornekler/11-registry
docker compose up -d
docker compose ps
```

Tarayıcıda http://localhost:5001/v2/_catalog → `{"repositories":[]}`

> 💡 **İpucu:** Bu, Docker'ın resmi açık kaynak registry'sidir (`registry:2`). Kurumlarda genellikle **Harbor**, **Nexus**, **GitLab Container Registry** veya bulut registry'leri (ECR, ACR, GCR) kullanılır — hepsi aynı API'yi konuşur, akış birebir aynıdır.

---

## Bölüm B — Tag → Push → Pull akışı

Lab 05'teki Go uygulamasını kullanalım:

```bash
cd ../05-multi-stage
docker build -t merhaba:1.0.0 .
```

### B1. Registry adıyla tag'leyin

`docker tag` **yeni image oluşturmaz**, var olana yeni bir isim ekler:

```bash
docker tag merhaba:1.0.0 localhost:5001/egitim/merhaba:1.0.0
docker tag merhaba:1.0.0 localhost:5001/egitim/merhaba:1.0
docker tag merhaba:1.0.0 localhost:5001/egitim/merhaba:1
docker tag merhaba:1.0.0 localhost:5001/egitim/merhaba:latest
```

```bash
docker images --filter reference="*merhaba*"
docker images --filter reference="localhost:5001/*/*"
```

> ❓ **Soru:** `IMAGE ID` sütununa bakın. Beş satırın ID'leri aynı mı? Diskte kaç kopya var?

### B2. Push

```bash
docker push localhost:5001/egitim/merhaba:1.0.0
docker push localhost:5001/egitim/merhaba:1.0
```

İkinci push'un çıktısına dikkat:

```
xxxxxxxx: Layer already exists
```

Katmanlar zaten registry'de → tekrar yüklenmez, sadece yeni tag kaydedilir.

Tüm tag'leri tek seferde:

```bash
docker push --all-tags localhost:5001/egitim/merhaba
```

Push çıktısının son satırındaki **digest**'i not edin:

```
1.0.0: digest: sha256:ab12... size: 1234
```

### B3. Registry'yi sorgulayın

Tarayıcıda açın:
- http://localhost:5001/v2/_catalog → `{"repositories":["egitim/merhaba"]}`
- http://localhost:5001/v2/egitim/merhaba/tags/list → `{"name":"egitim/merhaba","tags":["1","1.0","1.0.0","latest"]}`

### B4. Yerelden silip registry'den çekin

```bash
docker image rm localhost:5001/egitim/merhaba:1.0.0 localhost:5001/egitim/merhaba:1.0 localhost:5001/egitim/merhaba:1 localhost:5001/egitim/merhaba:latest merhaba:1.0.0
docker images --filter reference="*merhaba*"
```

```bash
docker pull localhost:5001/egitim/merhaba:1.0.0
docker run -d --name reg-test -p 8090:8080 localhost:5001/egitim/merhaba:1.0.0
```

http://localhost:8090 → uygulama registry'den gelen image ile çalışıyor.

### B5. Digest ile çekme

```bash
docker inspect --format "{{index .RepoDigests 0}}" localhost:5001/egitim/merhaba:1.0.0
```

Çıkan değeri kullanın:

```bash
docker pull localhost:5001/egitim/merhaba@sha256:<DIGEST>
```

> 💡 **İpucu:** Kubernetes manifest'lerinde ve kritik production deploy'larında `image: registry/app@sha256:...` kullanmak, tag'in değiştirilmesine karşı tam koruma sağlar.

---

## Bölüm C — "Tag üzerine yazma" tehlikesini görün

```bash
cd ../05-multi-stage
```

`main.go`'da mesajı `"Merhaba Multi-Stage Build! (SÜRPRİZ)"` yapın ve:

```bash
docker build -t localhost:5001/egitim/merhaba:1.0.0 .
docker push localhost:5001/egitim/merhaba:1.0.0
```

Push başarılı oldu → **1.0.0 artık farklı bir kod çalıştırıyor!** Bu image'ı `1.0.0` olarak çeken biri eski davranışı beklerken yenisini alır.

> ⚠️ **Dikkat:** Bu yüzden: (1) sürüm tag'lerinin üzerine yazmayın, yeni sürüm = yeni tag (`1.0.1`); (2) registry'de **tag immutability** özelliğini açın (Harbor, ECR, ACR destekler).

`main.go` dosyasını eski haline getirin.

---

## Bölüm D — Docker Hub'a push (opsiyonel, hesap gerekir)

```bash
docker login
```

```bash
docker build -t merhaba:1.0.0 .
docker tag merhaba:1.0.0 <dockerhub-kullanici-adiniz>/merhaba:1.0.0
docker push <dockerhub-kullanici-adiniz>/merhaba:1.0.0
```

https://hub.docker.com/r/<dockerhub-kullanici-adiniz>/merhaba adresinde görün.

> ⚠️ **Dikkat:** Docker Hub'daki repository'ler varsayılan olarak **public** olabilir. Kurum kodu içeren image'ları public registry'e push etmeyin.

```bash
docker logout
```

---

## Bölüm E — Çoklu mimari (bilgi)

Apple Silicon (arm64) Mac'te build edilen bir image, amd64 bir sunucuda çalışmayabilir (`exec format error`). Çözüm:

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t <registry>/merhaba:1.0.0 --push .
```

Registry'de tek bir tag altında iki mimari için ayrı image (manifest list) tutulur; her makine kendine uygun olanı çeker.

---

## Bölüm F — Eğitmen için: Sınıf registry'si (opsiyonel)

Eğitmen makinesinde registry'yi çalıştırıp tüm katılımcıların **ortak registry'ye** push etmesini sağlayabilirsiniz.

1. Eğitmen: `ornekler/11-registry` içinde `docker compose up -d`. IP adresini paylaşır (ör. `192.168.1.50`).
2. Her katılımcı: Docker Desktop → **Settings → Docker Engine** JSON'una ekler, **Apply & restart**:
   ```json
   {
     "insecure-registries": ["192.168.1.50:5001"]
   }
   ```
3. Katılımcı push eder:
   ```bash
   docker tag merhaba:1.0.0 192.168.1.50:5001/<adiniz>/merhaba:1.0.0
   docker push 192.168.1.50:5001/<adiniz>/merhaba:1.0.0
   ```
4. Katılımcılar **birbirlerinin** image'larını çekip çalıştırır.

> ⚠️ **Dikkat:** `insecure-registries` sadece eğitim içindir (TLS yok). Gerçek ortamda registry mutlaka TLS + kimlik doğrulama ile çalışmalıdır. Kurum ağında 5001 portu firewall tarafından engellenebilir; önceden test edin.

---

## 🧪 Kendin dene
1. `ornekler/10-compose/web` image'ını `1.0.0`, `1.0`, `1` ve `sha-<rastgele7karakter>` tag'leriyle yerel registry'ye push edin.
2. Bir `1.1.0` sürümü çıkarın (kodda küçük bir değişiklik), `1.1` ve `1` tag'lerini yeni sürüme taşıyın. `tags/list` endpoint'inde durumu doğrulayın. `1.0.0` hâlâ eski kodu mu gösteriyor?
3. `docker compose` dosyasında `image: localhost:5001/egitim/sayac-web:${APP_SURUM}` kullanın; `docker compose build` + `docker compose push` deneyin.

## 🧹 Temizlik
```bash
docker rm -f reg-test
docker image prune -f
cd ../11-registry
docker compose down -v
```

## 📌 Özet
- İsim = `registry/repository:tag@digest`. Registry belirtilmezse **Docker Hub**.
- **Tag değişebilir, digest değişmez.** Kritik deploy'larda digest kullanın.
- Strateji: **SemVer + git SHA**, çoklu tag; production'da **`latest` yok**; sürüm tag'lerinin **üzerine yazılmaz**.
- Akış: `docker build` → `docker tag` → `docker push` → (başka makinede) `docker pull` → `docker run`.
