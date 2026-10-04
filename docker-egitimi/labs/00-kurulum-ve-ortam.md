# Lab 00 — Kurulum ve Ortam Kontrolü

**Süre:** 15 dk · **Önkoşul:** Docker Desktop kurulu

## Amaç
- Docker Desktop'ın doğru çalıştığını doğrulamak
- Docker'ın **client–server** mimarisini anlamak
- Temel komut yapısını öğrenmek

---

## 1. Docker Desktop çalışıyor mu?

Docker Desktop uygulamasını açın. Sol alttaki durum göstergesi **"Engine running"** olmalı.

```bash
docker version
```

Beklenen çıktı (sürümler farklı olabilir):

```
Client:
 Version:           2x.x.x
 ...
Server: Docker Desktop 4.x.x
 Engine:
  Version:          2x.x.x
```

> ⚠️ **Dikkat:** `Server` bölümü yoksa veya *"Cannot connect to the Docker daemon"* / *"error during connect"* hatası alıyorsanız Docker Desktop çalışmıyordur. Uygulamayı başlatıp 30 sn bekleyin.

> 🎓 **Eğitmen notu:** `Client` ve `Server` bölümlerini göstererek mimariyi anlatın: yazdığımız `docker` komutu sadece bir **istemci**dir, asıl işi arka plandaki **Docker Engine (dockerd)** yapar. Docker Desktop, bu engine'i Windows/macOS'ta küçük bir Linux sanal makinesinde çalıştırır. Container'lar Linux çekirdeği özellikleri (namespaces, cgroups) kullandığı için bu gereklidir.

```
┌────────────────────┐   REST API    ┌──────────────────────────────┐
│  docker CLI        │ ────────────▶ │  Docker Engine (dockerd)      │
│  (sizin terminal)  │               │   ├─ image'lar                │
└────────────────────┘               │   ├─ container'lar            │
                                     │   ├─ network'ler / volume'lar │
                                     └──────────────┬───────────────┘
                                                    │ pull / push
                                              ┌─────▼──────┐
                                              │  Registry  │ (Docker Hub vb.)
                                              └────────────┘
```

## 2. Compose sürümü

```bash
docker compose version
```

Beklenen: `Docker Compose version v2.x.x` (veya daha yeni).

> 💡 **İpucu:** Eski `docker-compose` (tireli) komutu artık kullanılmıyor. Bu eğitimde her zaman **`docker compose`** (boşluklu) kullanacağız.

## 3. İlk container

```bash
docker run hello-world
```

Çıktıda şu satırları arayın:

```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
...
Hello from Docker!
```

> ❓ **Soru:** Çıktıdaki 4 adımlık açıklamayı okuyun. `docker run` komutu arka planda hangi işleri sırayla yaptı?

## 4. Sistem bilgisi

```bash
docker info
docker system df
```

`docker system df` → image, container, volume ve build cache'in ne kadar disk kullandığını gösterir. Eğitim boyunca bu sayıların nasıl büyüdüğünü izleyeceğiz.

## 5. Komut yapısı

Modern Docker CLI'ı **`docker <nesne> <eylem>`** biçimindedir:

| Nesne | Örnek komutlar |
|---|---|
| `container` | `docker container ls`, `docker container rm` |
| `image` | `docker image ls`, `docker image rm` |
| `network` | `docker network ls`, `docker network create` |
| `volume` | `docker volume ls`, `docker volume create` |

Kısa yollar da çalışır: `docker ps` = `docker container ls`, `docker images` = `docker image ls`.

```bash
docker --help
docker container --help
docker run --help
```

## Ortam kontrolü betiği (opsiyonel)

macOS / Linux / Git Bash kullanıyorsanız:

```bash
bash hazirlik/ortam-kontrol.sh
```

## ✅ Kontrol listesi
- [ ] `docker version` hem Client hem Server gösteriyor
- [ ] `docker compose version` çalışıyor
- [ ] `hello-world` başarıyla çalıştı
