# Lab 06 — Base Image Seçim Kriterleri

**Süre:** 45 dk · **Klasör:** `ornekler/06-base-image`

## Amaç
- Aynı uygulamayı farklı base image'larla paketleyip **boyut, güvenlik, debug kolaylığı** açısından karşılaştırmak
- **Minimal image** ile **debug kolaylığı** arasındaki dengeyi yönetmeyi öğrenmek
- Shell'i olmayan bir container'ı nasıl debug edeceğimizi görmek

---

## Kavram: Base image ailesi

| Varyant | Örnek | Tipik boyut | İçinde ne var? | Ne zaman? |
|---|---|---|---|---|
| **Full** | `python:3.12` | ~1 GB | Debian + gcc + git + build araçları | Build aşaması, CI |
| **Slim** | `python:3.12-slim` | ~130 MB | Minimal Debian + runtime | **Çoğu uygulama için varsayılan** |
| **Alpine** | `python:3.12-alpine` | ~50 MB | musl libc + busybox | Küçük araçlar, uyumluluk test edildiyse |
| **Distroless** | `gcr.io/distroless/python3` | ~50 MB | Sadece runtime, **shell yok** | Güvenlik öncelikli production |
| **Scratch** | `scratch` | 0 | Hiçbir şey | Statik binary'ler (Go, Rust) |

```
      DEBUG KOLAYLIĞI  ◀─────────────────────────────────▶  GÜVENLİK / KÜÇÜKLÜK
     full ────── slim ────── alpine ────── distroless ────── scratch
      │                                                          │
   shell, apt, curl, gcc                                   hiçbir şey
   çok CVE                                                 neredeyse 0 CVE
```

### Seçim kriterleri kontrol listesi

1. **Güvenilir kaynak:** Docker Official Image, Verified Publisher veya kurumunuzun onaylı image'ı mı?
2. **Bakım:** Düzenli güncelleniyor mu? Güvenlik yamaları hızlı geliyor mu?
3. **Boyut:** Pull süresi, disk, registry maliyeti.
4. **Saldırı yüzeyi / CVE sayısı:** Ne kadar az paket, o kadar az açık.
5. **Uyumluluk:** glibc mi musl mu? (Alpine'da bazı Python/Node native paketleri sorun çıkarabilir.)
6. **Debug ihtiyacı:** Ekibin production'da `exec` ile içeri girme alışkanlığı var mı?
7. **Mimari desteği:** amd64 + arm64 var mı?
8. **Sürüm sabitleme:** `3.12-slim` gibi net tag (hatta digest).

---

## Adımlar

```bash
cd ornekler/06-base-image
```

Aynı Flask uygulaması için 4 Dockerfile var: `Dockerfile.full`, `Dockerfile.slim`, `Dockerfile.alpine`, `Dockerfile.distroless`.

### 1. Dördünü de build edin

```bash
docker build -f Dockerfile.full       -t base-demo:full .
docker build -f Dockerfile.slim       -t base-demo:slim .
docker build -f Dockerfile.alpine     -t base-demo:alpine .
docker build -f Dockerfile.distroless -t base-demo:distroless .
```

> 🎓 **Eğitmen notu:** Build'ler arka arkaya çalışırken Dockerfile'ları ekrana yan yana yansıtıp farkları konuşun. `full` build'i en uzun süreni olacak — bu da bir veri noktası.

### 2. Boyutları karşılaştırın

```bash
docker images base-demo
```

Tabloyu doldurun:

| Tag | Boyut | Shell var mı? | Paket yöneticisi? |
|---|---|---|---|
| full | | | |
| slim | | | |
| alpine | | | |
| distroless | | | |

### 3. Hepsi çalışıyor mu?

```bash
docker run -d --name b-full       -p 5001:5000 base-demo:full
docker run -d --name b-slim       -p 5002:5000 base-demo:slim
docker run -d --name b-alpine     -p 5003:5000 base-demo:alpine
docker run -d --name b-distroless -p 5004:5000 base-demo:distroless
docker ps --filter name=b-
```

Tarayıcıda http://localhost:5001 ... http://localhost:5004 adreslerini açın. Dördü de aynı cevabı vermeli.

### 4. Debug kolaylığını test edin

```bash
docker exec -it b-full sh -c "cat /etc/os-release | head -2; which gcc git curl"
docker exec -it b-slim sh -c "cat /etc/os-release | head -2; which gcc git curl"
docker exec -it b-alpine sh -c "cat /etc/os-release | head -2; ldd --version 2>&1 | head -1"
docker exec -it b-distroless sh
```

> ❓ **Soru:** `b-full`'da `gcc` ve `git` var. Bir web uygulamasının production'da bunlara ihtiyacı var mı? Bir saldırgan bunlarla ne yapabilir?

### 5. 🔧 Shell'i olmayan container'ı debug etmek

Distroless container'a `exec` ile giremiyoruz. Üç yöntem:

**Yöntem 1 — Debug sidecar container (her yerde çalışır):**
Aynı network ve process namespace'ini paylaşan, içi araç dolu bir container başlatın:

```bash
docker run --rm -it --network container:b-distroless --pid container:b-distroless --cap-add SYS_PTRACE nicolaka/netshoot
```

İçeride:

```sh
ps aux                        # distroless container'ın process'lerini görürsünüz
curl -s localhost:5000        # aynı network namespace → localhost ona ait
ss -tlnp                      # dinlenen portlar
ls /proc/1/root/app           # hedef container'ın dosya sistemi
exit
```

**Yöntem 2 — `docker debug` (Docker Desktop):**
```bash
docker debug b-distroless
```
Docker Desktop, container'a geçici bir araç kutusu bağlar. (Kullanılabilirlik Docker Desktop sürümünüze ve aboneliğinize göre değişebilir.)

**Yöntem 3 — `:debug` varyantı:**
Distroless image'larının `:debug` tag'li sürümleri busybox shell içerir. Sorun ararken geçici olarak bu tag'e geçilebilir:
```dockerfile
FROM gcr.io/distroless/python3-debian12:debug
```

> 🎓 **Eğitmen notu:** Buradaki mesaj: *"Minimal image = debug edilemez"* **değildir**. Doğru yaklaşım, debug araçlarını **production image'ına koymak yerine ihtiyaç anında dışarıdan bağlamaktır**. Kubernetes'te bunun karşılığı `kubectl debug` ve ephemeral container'lardır.

### 6. 🛡️ Güvenlik taraması

Docker Desktop'ta **Docker Scout** hazır gelir:

```bash
docker scout quickview base-demo:full
docker scout quickview base-demo:slim
docker scout quickview base-demo:distroless
```

Kritik (C) / Yüksek (H) / Orta (M) / Düşük (L) açık sayılarını karşılaştırın.

> 💡 **İpucu:** Açık kaynak alternatif: **Trivy**. Kurmadan container olarak çalıştırabilirsiniz:
> ```bash
> docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy image --severity HIGH,CRITICAL base-demo:slim
> ```

### 7. ⚠️ Alpine uyarısı: musl vs glibc

Alpine, standart `glibc` yerine `musl` kullanır. Sonuçları:
- Python'da bazı paketlerin hazır derlenmiş (wheel) sürümü yoksa build sırasında **derlenmesi** gerekir → `gcc`, `musl-dev` eklemek gerekir, build yavaşlar.
- DNS çözümleme, locale, performans davranışları glibc'den farklı olabilir.

**Kural:** Alpine'ı ancak uygulamanızı **onunla test ettiyseniz** kullanın. Emin değilseniz `-slim` güvenli varsayılandır.

---

## Karar ağacı

```
Uygulama statik binary mi? (Go, Rust)
 ├─ Evet → distroless/static  (veya scratch)
 └─ Hayır → Runtime gerekiyor (Python, Node, Java...)
      ├─ Güvenlik ekibi / regülasyon minimal image şart koşuyor mu?
      │    └─ Evet → distroless (+ debug için sidecar / docker debug)
      └─ Hayır → -slim varyantı  ✅ çoğu durumda doğru cevap
                 (Alpine sadece test edilmiş, uyumluluğu doğrulanmışsa)

Build aşaması için → full / SDK image'ı (multi-stage ile runtime'dan ayrılır)
```

---

## 🧪 Kendin dene
1. `Dockerfile.slim`'i multi-stage'e çevirin: build aşamasında `python:3.12` (full), runtime'da `python:3.12-slim`. Boyut değişti mi? (İpucu: `pip install --prefix=/install` + `COPY --from=build /install /usr/local`)
2. `docker history base-demo:full` ile `docker history base-demo:slim` çıktılarını karşılaştırın. Aradaki farkın çoğu hangi katmanlardan geliyor?

## 🧹 Temizlik
```bash
docker rm -f b-full b-slim b-alpine b-distroless
docker image rm base-demo:full base-demo:slim base-demo:alpine base-demo:distroless
```

## 📌 Özet
- Varsayılan tercih: **`-slim`**. Production'da güvenlik öncelikliyse **distroless**.
- **Full** image'lar build aşamasına aittir, runtime'a değil.
- Minimal image'ı debug etmek için araçları image'a koymayın; **sidecar / `docker debug`** kullanın.
- Tag'i **sabitleyin**, image'ları **düzenli tarayın** (Docker Scout / Trivy).
