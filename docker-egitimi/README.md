# Docker Temelleri — Uygulamalı Eğitim Seti

Bu set üç parçadan oluşur:

| Parça | Ne işe yarar |
|---|---|
| **`labs/` klasörü** | Her konu için adım adım uygulama dokümanı (komutlar + beklenen çıktılar + sorular) |
| **`ornekler/` klasörü** | Lab'larda kullanılan hazır kod, Dockerfile ve YAML dosyaları |

---

## Klasör yapısı

```
docker-egitimi/
├── README.md                  
├── hazirlik/
│   ├── imajlari-indir.ps1     ← Windows: tüm image'ları önceden indir
│   ├── imajlari-indir.sh      ← macOS/Linux: tüm image'ları önceden indir
│   └── ortam-kontrol.sh       ← ortam hazır mı testi
├── labs/
│   ├── 00-kurulum-ve-ortam.md
│   ├── 01-container-neden.md
│   ├── 02-image-ve-layer-cache.md
│   ├── 03-dockerfile-direktifleri.md
│   ├── 04-dockerignore.md
│   ├── 05-multi-stage-build.md
│   ├── 06-base-image-secimi.md
│   ├── 07-networking.md
│   ├── 08-volume-ve-bind-mount.md
│   ├── 09-environment-variables.md
│   ├── 10-docker-compose.md
│   ├── 11-tagging-ve-registry.md
│   ├── 12-final-projesi.md
│   └── cheatsheet.md          ← tek sayfalık komut özeti + sorun giderme
└── ornekler/
    ├── 02-layer-cache/        ← Flask uygulaması, iyi/kötü Dockerfile
    ├── 03-direktifler/        ← CMD/ENTRYPOINT/ADD/COPY demoları
    ├── 04-dockerignore/       ← .dockerignore etkisi + sızan .env demosu
    ├── 05-multi-stage/        ← Go uygulaması, tek aşama vs multi-stage
    ├── 06-base-image/         ← full / slim / alpine / distroless karşılaştırması
    ├── 08-volume/html/        ← bind mount için statik sayfa
    ├── 09-env/                ← ortam değişkeniyle konfigüre edilen uygulama
    ├── 10-compose/            ← web + redis (+ nginx proxy) compose projesi
    ├── 11-registry/           ← yerel registry compose dosyası
    └── 12-final-proje/        ← başlangıç kodu + çözüm
```

---

## Eğitim günü

```bash
# Herkes çalıştırsın (macOS/Linux/Git Bash):
bash hazirlik/ortam-kontrol.sh
```

```powershell
# Windows PowerShell:
docker version
docker compose version
docker run --rm hello-world
```

---

## Önerilen ders akışı

### 1. Gün — Image dünyası

| Saat | Süre | Modül | Lab |
|---|---|---|---|
| 09:30 | 15 dk | Tanışma, ortam kontrolü | `00-kurulum-ve-ortam.md` |
| 09:45 | 45 dk | Container'ın çözdüğü sorun, ilk container'lar | `01-container-neden.md` |
| 10:30 | 15 dk | *Ara* | |
| 10:45 | 60 dk | Image, layer yapısı, layer cache | `02-image-ve-layer-cache.md` |
| 11:45 | 60 dk | Dockerfile direktifleri (COPY/ADD, CMD/ENTRYPOINT) | `03-dockerfile-direktifleri.md` |
| 12:45 | 60 dk | *Öğle arası* | |
| 13:45 | 30 dk | .dockerignore | `04-dockerignore.md` |
| 14:15 | 60 dk | Multi-stage build | `05-multi-stage-build.md` |
| 15:15 | 15 dk | *Ara* | |
| 15:30 | 45 dk | Base image seçimi, minimal vs debug | `06-base-image-secimi.md` |
| 16:15 | 15 dk | Gün 1 tekrar + soru | |

### 2. Gün — Çalışma zamanı ve çok servisli uygulamalar

| Saat | Süre | Modül | Lab |
|---|---|---|---|
| 09:30 | 15 dk | Gün 1 hızlı tekrar (quiz) | |
| 09:45 | 60 dk | Networking | `07-networking.md` |
| 10:45 | 15 dk | *Ara* | |
| 11:00 | 60 dk | Volume vs bind mount | `08-volume-ve-bind-mount.md` |
| 12:00 | 30 dk | Environment variable ile konfigürasyon | `09-environment-variables.md` |
| 12:30 | 60 dk | *Öğle arası* | |
| 13:30 | 75 dk | Docker Compose | `10-docker-compose.md` |
| 14:45 | 15 dk | *Ara* | |
| 15:00 | 45 dk | Image tagging, registry push akışı | `11-tagging-ve-registry.md` |
| 15:45 | 45 dk | Final projesi (çiftler halinde) | `12-final-projesi.md` |
| 16:30 | 15 dk | Kapanış, değerlendirme | |

> **Zaman sıkışırsa:** `06` base image lab'ının distroless kısmı, `10` compose lab'ının `watch` bonusu ve `11` registry lab'ının "sınıf registry'si" bölümü atlanabilir.

---

## Katılımcılar için: Lab'ları nasıl takip edeceğim?

- Her lab dokümanı aynı yapıdadır: **Amaç → Kavram → Adımlar → Gözlem soruları → Kendin dene → Temizlik**.
- Komutları **kopyala-yapıştır** yapmak yerine mümkünse **yazın** — kas hafızası önemli.
- Komutlar tek satır halinde verilmiştir; **PowerShell, bash ve zsh'de aynı şekilde** çalışır.
  Farklı olduğu yerlerde iki versiyon ayrıca verilmiştir.
- `${PWD}` ifadesi "bulunduğum klasör" demektir ve PowerShell + bash'te çalışır.
  (Klasik `cmd.exe` kullanıyorsanız `%cd%` yazın — ama PowerShell kullanmanız önerilir.)
- Her lab'ın sonundaki **Temizlik** adımını atlamayın; port ve isim çakışmalarını önler.
- Takıldığınızda: önce `labs/cheatsheet.md` içindeki **Sorun giderme** bölümüne bakın.

### Doküman işaretleri

> ⚠️ **Dikkat:** Sık yapılan hata veya güvenlik uyarısı.

> 💡 **İpucu:** Bilmeniz faydalı ek bilgi.

> ❓ **Soru:** Cevabını kendiniz bulmanız beklenen soru.
