# Lab 03 — Dockerfile Direktifleri

**Süre:** 60 dk · **Klasör:** `ornekler/03-direktifler`

## Amaç
- Tüm temel Dockerfile direktiflerini tanımak
- **COPY ile ADD** farkını deneyerek görmek
- **CMD ile ENTRYPOINT** farkını ve birlikte kullanımını öğrenmek
- **Shell form** ile **exec form** farkını anlamak

---

## Direktif referansı

| Direktif | Ne yapar | Katman oluşturur mu? |
|---|---|---|
| `FROM` | Base image'ı seçer. Her Dockerfile bununla başlar. | — (base) |
| `RUN` | Build sırasında komut çalıştırır | ✅ |
| `COPY` | Build context'ten image'a dosya kopyalar | ✅ |
| `ADD` | COPY + tar açma + URL'den indirme | ✅ |
| `WORKDIR` | Çalışma dizinini ayarlar (yoksa oluşturur) | metadata |
| `ENV` | Kalıcı ortam değişkeni (build + runtime) | metadata |
| `ARG` | Sadece build-time değişkeni | — |
| `EXPOSE` | Hangi portun dinlendiğini **belgeler** (açmaz!) | metadata |
| `USER` | Sonraki komutların çalışacağı kullanıcı | metadata |
| `LABEL` | Image'a metadata (sahip, sürüm, kaynak) | metadata |
| `CMD` | Varsayılan komut / argüman | metadata |
| `ENTRYPOINT` | Sabit çalıştırılabilir | metadata |
| `HEALTHCHECK` | Container sağlık kontrolü | metadata |
| `VOLUME` | Anonim volume noktası tanımlar | metadata |

---

## Bölüm A — Base image seçimi (`FROM`)

```dockerfile
FROM python:3.12-slim          # ✅ sürüm sabitlenmiş
FROM python:latest             # ❌ yarın farklı bir Python gelebilir
FROM python:3.12-slim@sha256:… # ✅✅ digest ile tamamen sabit (en tekrarlanabilir)
```

> ⚠️ **Dikkat:** `latest` tag'i "en yeni" demek **değildir**; sadece tag verilmediğinde kullanılan varsayılan isimdir. Production Dockerfile'larında `latest` kullanmayın. Base image seçimini Lab 06'da detaylı işleyeceğiz.

---

## Bölüm B — COPY vs ADD

```bash
cd ornekler/03-direktifler
```

Klasörde `arsiv.tar.gz` adında hazır bir arşiv var (içinde `ornek-klasor/benioku.txt` ve `not.txt`).

`Dockerfile.add-copy`:

```dockerfile
FROM alpine:3.20
WORKDIR /demo

# COPY: dosyayı olduğu gibi kopyalar (arşiv, arşiv olarak kalır)
COPY arsiv.tar.gz /demo/copy/

# ADD: yerel tar arşivini OTOMATİK AÇAR (ayrıca URL'den indirme yapabilir)
ADD arsiv.tar.gz /demo/add/

CMD ["sh", "-c", "echo '=== COPY ile ==='; ls -la /demo/copy; echo; echo '=== ADD ile ==='; ls -laR /demo/add"]
```

```bash
docker build -f Dockerfile.add-copy -t demo:addcopy .
docker run --rm demo:addcopy
```

Beklenen:

```
=== COPY ile ===
-rw-r--r--    1 root  root  233 ... arsiv.tar.gz

=== ADD ile ===
/demo/add:
drwxr-xr-x    2 root  root  ... ornek-klasor

/demo/add/ornek-klasor:
-rw-r--r--    1 root  root  ... benioku.txt
-rw-r--r--    1 root  root  ... not.txt
```

### Hangisini kullanmalı?

| Durum | Tercih |
|---|---|
| Normal dosya / klasör kopyalama | **COPY** (her zaman varsayılan) |
| Yerel tar arşivini image içinde açmak | ADD |
| URL'den dosya indirmek | Genelde `RUN curl ...` (checksum kontrolü yapılabilir, sonra temizlenebilir) |

> 🎓 **Eğitmen notu:** ADD'in "sihirli" davranışı (otomatik açma) sürpriz yaratır: `.tar.gz` bir dosyayı *olduğu gibi* kopyalamak isteyen biri ADD kullanırsa içeriği açılmış bulur. Docker'ın resmi best-practice önerisi: **açıkça gerekmedikçe COPY**.

### Faydalı COPY seçenekleri

```dockerfile
COPY --chown=uygulama:uygulama . /app      # sahipliği ayarla (ayrı RUN chown gerekmez → ekstra katman yok)
COPY --from=build /out/app /app            # başka bir aşamadan kopyala (Lab 05)
COPY src/ /app/src/                        # klasörün İÇERİĞİNİ kopyalar
COPY *.txt /app/                           # joker karakter
```

---

## Bölüm C — CMD vs ENTRYPOINT

### C1. Sadece CMD

`Dockerfile.cmd`:
```dockerfile
FROM alpine:3.20
CMD ["echo", "Merhaba, ben CMD ile geldim"]
```

```bash
docker build -f Dockerfile.cmd -t demo:cmd .

docker run --rm demo:cmd
docker run --rm demo:cmd echo "Başka bir şey"
docker run --rm demo:cmd ls /
```

| Komut | Çıktı |
|---|---|
| `docker run --rm demo:cmd` | `Merhaba, ben CMD ile geldim` |
| `docker run --rm demo:cmd echo "Başka bir şey"` | `Başka bir şey` |
| `docker run --rm demo:cmd ls /` | kök dizin listesi |

**Sonuç:** `docker run IMAGE` sonrasına yazılan her şey **CMD'nin tamamen yerine geçer**.

### C2. Sadece ENTRYPOINT

`Dockerfile.entrypoint`:
```dockerfile
FROM alpine:3.20
ENTRYPOINT ["echo", "Merhaba"]
```

```bash
docker build -f Dockerfile.entrypoint -t demo:ep .

docker run --rm demo:ep
docker run --rm demo:ep Dünya
docker run --rm demo:ep ls /
```

| Komut | Çıktı |
|---|---|
| `docker run --rm demo:ep` | `Merhaba` |
| `docker run --rm demo:ep Dünya` | `Merhaba Dünya` |
| `docker run --rm demo:ep ls /` | `Merhaba ls /` ← ls **çalışmadı**, argüman oldu! |

**Sonuç:** `docker run IMAGE` sonrasına yazılanlar ENTRYPOINT'e **argüman olarak eklenir**.

### C3. İkisi birlikte (en yaygın desen)

`Dockerfile.ikisi`:
```dockerfile
FROM alpine:3.20
ENTRYPOINT ["ping", "-c", "3"]   # program (sabit)
CMD ["localhost"]                # varsayılan argüman (değiştirilebilir)
```

```bash
docker build -f Dockerfile.ikisi -t demo:ping .

docker run --rm demo:ping
docker run --rm demo:ping 8.8.8.8
```

- İlk komut → `ping -c 3 localhost`
- İkinci komut → `ping -c 3 8.8.8.8`

### C4. ENTRYPOINT'i ezmek

```bash
docker run --rm --entrypoint sh demo:ping -c "echo ENTRYPOINT ezildi; cat /etc/alpine-release"
```

> ⚠️ **Dikkat:** `--entrypoint` yalnızca **çalıştırılabilir dosyanın adını** alır; argümanlar image adından **sonra** yazılır.

### Özet tablo

```
                       docker run IMAGE             docker run IMAGE arg1 arg2
                     ┌──────────────────────┐     ┌───────────────────────────┐
 Sadece CMD [c]      │  c                   │     │  arg1 arg2                │
 Sadece EP  [e]      │  e                   │     │  e arg1 arg2              │
 EP [e] + CMD [c]    │  e c                 │     │  e arg1 arg2              │
                     └──────────────────────┘     └───────────────────────────┘
```

> 🎓 **Eğitmen notu:** Pratik kural: *"Container bir **araç** gibi davranacaksa (ör. `mycli --help`) ENTRYPOINT; bir **uygulama** çalıştırıyorsa ve kullanıcı debug için içine `sh` ile girmek isteyebilirse CMD."* Resmi image'ların çoğu (nginx, postgres) ikisini birlikte kullanır: ENTRYPOINT bir başlangıç betiği, CMD asıl süreç.

---

## Bölüm D — Shell form vs Exec form

```dockerfile
CMD python app.py              # shell form → /bin/sh -c "python app.py"
CMD ["python", "app.py"]       # exec form  → doğrudan python çalışır
```

`Dockerfile.shell-exec`:
```dockerfile
FROM alpine:3.20
ENV SEHIR=Ankara
RUN echo "shell form  -> $SEHIR"
RUN ["echo", "exec form   -> $SEHIR"]
CMD ["sh", "-c", "echo \"CMD icinde sh -c ile -> $SEHIR\""]
```

Build çıktısını düz metin olarak görmek için `--progress=plain` kullanın:

```bash
docker build --no-cache --progress=plain -f Dockerfile.shell-exec -t demo:form .
```

Çıktıda arayın:

```
#5 ... shell form  -> Ankara
#6 ... exec form   -> $SEHIR          ← değişken GENİŞLETİLMEDİ
```

```bash
docker run --rm demo:form
```

| | Shell form | Exec form |
|---|---|---|
| Değişken genişletme (`$VAR`) | ✅ | ❌ (shell yok) |
| Pipe, `&&`, yönlendirme | ✅ | ❌ |
| PID 1 kim? | `/bin/sh` | Uygulamanın kendisi |
| `docker stop` sinyali (SIGTERM) uygulamaya ulaşır mı? | Genelde **hayır** → 10 sn sonra SIGKILL | ✅ Evet → düzgün kapanış |
| Shell'siz image'da (distroless, scratch) çalışır mı? | ❌ | ✅ |

> ⚠️ **Dikkat:** `CMD` ve `ENTRYPOINT` için **her zaman exec form** kullanın. Shell form'da `docker stop` komutu uygulamanıza SIGTERM iletemeyebilir; uygulama bağlantıları düzgün kapatamaz ve 10 saniye sonra zorla öldürülür.

---

## Bölüm E — Tüm direktifler bir arada

`Dockerfile.tam-ornek` dosyasını açın ve satır satır birlikte okuyun (her satırda açıklama var). Sonra:

```bash
docker build -f Dockerfile.tam-ornek --build-arg UYGULAMA_SURUM=2.1.0 -t demo:tam .
docker run -d --name tam -p 8081:8080 demo:tam
```

Tarayıcıda http://localhost:8081 → `Direktif demo v2.1.0`

Direktiflerin etkisini doğrulayın:

```bash
# LABEL'lar
docker inspect demo:tam --format "{{json .Config.Labels}}"

# ENV
docker inspect demo:tam --format "{{json .Config.Env}}"

# USER → root DEĞİL
docker exec tam whoami

# WORKDIR
docker exec tam pwd

# HEALTHCHECK → 10-20 sn bekleyin, STATUS sütununda (healthy) görünmeli
docker ps --filter name=tam
```

> ❓ **Soru:** `EXPOSE 8080` satırını silip yeniden build etseydik, `-p 8081:8080` hâlâ çalışır mıydı?

---

## 🧪 Kendin dene
1. `curl` aracını container olarak paketleyin: `ENTRYPOINT ["curl", "-s"]` ve `CMD ["https://example.com"]` kullanan bir Dockerfile yazın (base: `alpine:3.20`, `RUN apk add --no-cache curl`). `docker run --rm mycurl` ve `docker run --rm mycurl -I https://example.com` deneyin.
2. `Dockerfile.tam-ornek`'teki `USER uygulama` satırını kaldırın, build edip `whoami` çalıştırın. Güvenlik açısından ne değişti?
3. `ARG` ile tanımlanan `UYGULAMA_SURUM` değişkeni çalışan container'da görünür mü? `docker exec tam env` ile kontrol edin. Neden görünüyor/görünmüyor?

## 🧹 Temizlik
```bash
docker rm -f tam
docker image rm demo:addcopy demo:cmd demo:ep demo:ping demo:form demo:tam
```

## 📌 Özet
- **COPY** varsayılan; **ADD** sadece tar açma gerektiğinde.
- **CMD** = ezilebilir varsayılan; **ENTRYPOINT** = sabit program; birlikte → "program + varsayılan argüman".
- `CMD`/`ENTRYPOINT` için **exec form** (`["...", "..."]`) kullanın.
- `EXPOSE` portu açmaz, belgeler. `USER` ile root olmayan kullanıcıya geçin.
