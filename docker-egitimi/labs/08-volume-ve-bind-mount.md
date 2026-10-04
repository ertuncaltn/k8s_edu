# Lab 08 — Volume vs Bind Mount, Kalıcı Veri Yönetimi

**Süre:** 60 dk · **Klasör:** `ornekler/08-volume` · **Image'lar:** `postgres:16-alpine`, `nginx:1.27-alpine`, `alpine:3.20`

## Amaç
- Container'ın yazılabilir katmanındaki verinin neden **geçici** olduğunu hatırlamak
- **Named volume**, **bind mount** ve **tmpfs** farklarını deneyerek öğrenmek
- Bir veritabanının verisini container silinse bile korumak
- Volume **yedekleme / geri yükleme** yapmak

---

## Kavram

```
                         HOST
 ┌────────────────────────────────────────────────────────────────────┐
 │  Sizin klasörünüz            Docker'ın yönettiği alan               │
 │  C:\proje\html  ◀── bind ─┐   /var/lib/docker/volumes/pgdata ◀─┐    │
 │                          │                                   │    │
 │                 ┌────────┴──────────────┐          ┌─────────┴──┐ │
 │                 │ nginx                 │          │ postgres   │ │
 │                 │ /usr/share/nginx/html │          │ /var/lib/  │ │
 │                 └───────────────────────┘          │ postgresql │ │
 │                                                    └────────────┘ │
 │                     RAM ◀── tmpfs (/tmp/cache)                     │
 └────────────────────────────────────────────────────────────────────┘
```

| | **Named volume** | **Bind mount** | **tmpfs** |
|---|---|---|---|
| Nerede? | Docker'ın yönettiği alan | Host'ta **sizin seçtiğiniz** yol | RAM |
| Söz dizimi | `-v pgdata:/data` | `-v "${PWD}/html:/data"` | `--tmpfs /data` |
| Kim yönetir? | Docker (`docker volume ...`) | Siz (dosya sistemi) | — |
| Container silinince | **Kalır** | **Kalır** (zaten sizin dosyanız) | Kaybolur |
| Taşınabilir mi? | ✅ Host yolundan bağımsız | ❌ Host yoluna bağlı | — |
| Performans (Docker Desktop) | ✅ Hızlı | Windows/macOS'ta daha yavaş olabilir | ✅ En hızlı |
| Tipik kullanım | **Veritabanı, production verisi** | **Geliştirme (canlı kod), config dosyası** | Geçici, hassas veri |

---

## Bölüm A — Sorunu hatırlayalım: container verisi geçicidir

```bash
docker run -d --name pg-gecici -e POSTGRES_PASSWORD=egitim postgres:16-alpine
```

~5 saniye bekleyin, sonra bir tablo oluşturun:

```bash
docker exec pg-gecici psql -U postgres -c "CREATE TABLE ogrenci(id serial, ad text); INSERT INTO ogrenci(ad) VALUES ('Ayşe'),('Mehmet');"
docker exec pg-gecici psql -U postgres -c "SELECT * FROM ogrenci;"
```

Container'ı silip yeniden oluşturun:

```bash
docker rm -f pg-gecici
docker run -d --name pg-gecici -e POSTGRES_PASSWORD=egitim postgres:16-alpine
```

~5 sn sonra:

```bash
docker exec pg-gecici psql -U postgres -c "SELECT * FROM ogrenci;"
```

❌ Beklenen: `ERROR:  relation "ogrenci" does not exist` → **Veri kayboldu.**

```bash
docker rm -f pg-gecici
```

---

## Bölüm B — Named volume ile kalıcı veri

### B1. Volume oluşturun ve kullanın

```bash
docker volume create pgdata
docker volume ls
docker volume inspect pgdata
```

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=egitim -v pgdata:/var/lib/postgresql/data postgres:16-alpine
```

~5 sn sonra veri ekleyin:

```bash
docker exec pg psql -U postgres -c "CREATE TABLE ogrenci(id serial, ad text); INSERT INTO ogrenci(ad) VALUES ('Ayşe'),('Mehmet'),('Zeynep');"
```

### B2. Container'ı yok edin, veri yaşasın

```bash
docker rm -f pg
docker run -d --name pg-yeni -e POSTGRES_PASSWORD=egitim -v pgdata:/var/lib/postgresql/data postgres:16-alpine
```

~5 sn sonra:

```bash
docker exec pg-yeni psql -U postgres -c "SELECT * FROM ogrenci;"
```

✅ Beklenen:

```
 id |   ad
----+--------
  1 | Ayşe
  2 | Mehmet
  3 | Zeynep
```

> 🎓 **Eğitmen notu:** Burada vurgulanacak nokta **container ile verinin yaşam döngülerinin ayrılmasıdır**. Container'ı istediğimiz kadar silip yeniden oluşturabiliriz (ör. postgres'i 16.3'ten 16.4'e güncellemek için) — veri volume'da güvende. Bu, "container'lar değiştirilebilir (ephemeral/disposable), veri kalıcıdır" prensibidir.

> ⚠️ **Dikkat:** Majör sürüm yükseltmesi (ör. postgres 16 → 17) volume'u doğrudan açamaz; `pg_dump`/`pg_upgrade` gerekir. Volume veri formatını sihirli şekilde dönüştürmez.

### B3. `--mount` söz dizimi (daha açık, önerilen)

`-v` ile aynı işi yapar ama daha okunaklıdır ve hata yapmayı zorlaştırır:

```bash
docker run --rm --mount type=volume,source=pgdata,target=/veri,readonly alpine:3.20 ls /veri
```

| `-v` | `--mount` |
|---|---|
| `-v pgdata:/data` | `--mount type=volume,source=pgdata,target=/data` |
| `-v "${PWD}/html:/data:ro"` | `--mount type=bind,source="${PWD}/html",target=/data,readonly` |

> 💡 **İpucu:** `-v` ile verilen host yolu yoksa Docker onu **boş bir klasör olarak oluşturur** (sessizce!). `--mount` ise hata verir. Yazım hatalarını yakalamak için `--mount` daha güvenlidir.

---

## Bölüm C — Bind mount ile canlı geliştirme

```bash
cd ornekler/08-volume
```

`html/index.html` dosyası hazır.

```bash
docker run -d --name canli -p 8080:80 -v "${PWD}/html:/usr/share/nginx/html:ro" nginx:1.27-alpine
```

Tarayıcı: http://localhost:8080 → "Bu sayfa bilgisayarınızdaki dosyadan geliyor!"

Şimdi **editörünüzde** `html/index.html` dosyasını açın, başlığı değiştirin, kaydedin ve tarayıcıyı yenileyin.

✅ Değişiklik **anında** görünür — image yeniden build edilmedi, container yeniden başlatılmadı.

`:ro` (read-only) etkisini test edin:

```bash
docker exec canli sh -c "echo hack > /usr/share/nginx/html/index.html"
```

Beklenen: `sh: can't create /usr/share/nginx/html/index.html: Read-only file system`

> ⚠️ **Dikkat — Bind mount image içeriğini GİZLER:** Bind mount edilen klasör, image'daki aynı yolun içeriğini **tamamen örter**. Örneğin boş bir klasörü `/usr/share/nginx/html`'e bağlasaydınız nginx'in varsayılan sayfası kaybolurdu. Aynı durum Node projelerinde `node_modules` klasöründe sık yaşanır.

> 💡 **Windows ipucu:** Docker Desktop + WSL 2 kullanıyorsanız, bind mount performansı için proje dosyalarınızı Windows dosya sistemi (`C:\...`) yerine **WSL dosya sisteminde** (`\\wsl$\Ubuntu\home\...`) tutmak build ve dosya izleme hızını belirgin şekilde artırır.

---

## Bölüm D — tmpfs mount

```bash
docker run --rm --tmpfs /gecici:size=16m alpine:3.20 sh -c "df -h /gecici; echo sifre > /gecici/token; cat /gecici/token"
```

tmpfs RAM'de yaşar, diske hiç yazılmaz, container durunca yok olur. Geçici token, cache gibi hassas/geçici veriler için uygundur.

---

## Bölüm E — Volume yedekleme ve geri yükleme

Volume'lar doğrudan dosya sisteminde gezilemediği için **geçici bir container** ile yedeklenir:

```bash
cd ornekler/08-volume
```

### E1. Yedek al

```bash
docker stop pg-yeni
docker run --rm -v pgdata:/kaynak:ro -v "${PWD}:/yedek" alpine:3.20 tar czf /yedek/pgdata-yedek.tar.gz -C /kaynak .
docker start pg-yeni
```

Klasörünüzde `pgdata-yedek.tar.gz` oluştu.

> 💡 **İpucu:** Tutarlı bir yedek için veritabanını durdurduk. Canlı sistemlerde dosya kopyası yerine veritabanının kendi aracını tercih edin: `docker exec pg-yeni pg_dump -U postgres postgres > yedek.sql`

### E2. Yeni bir volume'a geri yükle

```bash
docker volume create pgdata-geri
docker run --rm -v pgdata-geri:/hedef -v "${PWD}:/yedek:ro" alpine:3.20 tar xzf /yedek/pgdata-yedek.tar.gz -C /hedef
docker run -d --name pg-geri -e POSTGRES_PASSWORD=egitim -v pgdata-geri:/var/lib/postgresql/data postgres:16-alpine
```

~5 sn sonra:

```bash
docker exec pg-geri psql -U postgres -c "SELECT * FROM ogrenci;"
```

✅ Aynı üç kayıt.

---

## Bölüm F — Volume temizliği

```bash
docker volume ls
docker volume ls -f dangling=true      # hiçbir container'a bağlı olmayanlar
```

> ⚠️ **Dikkat:** `docker volume prune` ve `docker compose down -v` **veriyi kalıcı olarak siler**. Geri dönüşü yoktur. Production'da bu komutları kullanmadan önce iki kez düşünün.

---

## 🧪 Kendin dene
1. `docker run -d --name n2 -v bosvolume:/usr/share/nginx/html nginx:1.27-alpine` çalıştırın. Sonra `docker run --rm -v bosvolume:/v alpine:3.20 ls /v` ile volume'a bakın. İçi boş mu? (İpucu: named volume **ilk bağlandığında boşsa**, Docker image'daki içeriği volume'a kopyalar. Bind mount bunu yapmaz!)
2. Bind mount'u `:ro` olmadan tekrar başlatın ve container içinden `index.html`'e yazın. Host'taki dosyanız değişti mi?
3. `docker system df -v` ile volume'ların kapladığı alanı görün.

## 🧹 Temizlik

```bash
docker rm -f pg-yeni pg-geri canli n2
docker volume rm pgdata pgdata-geri bosvolume
```

**bash:** `rm -f pgdata-yedek.tar.gz` · **PowerShell:** `Remove-Item pgdata-yedek.tar.gz`

## 📌 Özet
- Container katmanı **geçicidir**; kalıcı veri **volume**'a yazılmalı.
- **Named volume** → production verisi (DB). **Bind mount** → geliştirme, config dosyaları. **tmpfs** → geçici/hassas.
- Container'lar değiştirilebilir, veri kalıcıdır: **yaşam döngülerini ayırın**.
- Bind mount image içeriğini gizler; named volume ilk bağlantıda image içeriğini kopyalar.
- Yedek: geçici container + `tar`, veya veritabanının kendi dump aracı.
