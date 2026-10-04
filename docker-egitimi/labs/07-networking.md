# Lab 07 — Container Networking

**Süre:** 60 dk · **Kullanılan image'lar:** `alpine:3.20`, `nginx:1.27-alpine`, `nicolaka/netshoot`

## Amaç
- Docker network sürücülerini (`bridge`, `host`, `none`) tanımak
- **Port mapping** (`-p`) ile dış dünyaya servis açmak
- **Varsayılan bridge** ile **kullanıcı tanımlı bridge** arasındaki kritik farkı görmek (DNS!)
- Container'lar arası iletişimi ve **network izolasyonunu** kurmak

---

## Kavram

```
                         HOST (sizin bilgisayarınız)
   tarayıcı → localhost:8080
                   │  port mapping (-p 8080:80)
 ┌─────────────────▼──────────────────────────────────────────────┐
 │  Docker Engine                                                  │
 │                                                                 │
 │   ┌──── egitim-net (kullanıcı tanımlı bridge, 172.20.0.0/16) ──┐ │
 │   │                                                           │ │
 │   │   ┌───────────┐   "http://api:5000"   ┌───────────┐       │ │
 │   │   │  web      │ ────────────────────▶ │  api      │       │ │
 │   │   │  :80      │   (Docker DNS ile     │  :5000    │       │ │
 │   │   │172.20.0.2 │    isim çözümleme)    │172.20.0.3 │       │ │
 │   │   └───────────┘                       └───────────┘       │ │
 │   └───────────────────────────────────────────────────────────┘ │
 └─────────────────────────────────────────────────────────────────┘
```

| Sürücü | Açıklama |
|---|---|
| `bridge` | Varsayılan. Container'lar sanal bir switch'e bağlanır, host'tan izole ağ. |
| `host` | Container host'un ağını doğrudan kullanır (izolasyon yok). Docker Desktop'ta sınırlı destek. |
| `none` | Hiç ağ yok (sadece loopback). |
| `overlay` | Birden fazla host arasında (Swarm). Bu eğitimin kapsamı dışında. |

---

## Bölüm A — Port mapping

### A1. Temel kullanım

```bash
docker run -d --name web1 -p 8080:80 nginx:1.27-alpine
```

`-p HOST_PORT:CONTAINER_PORT` → Host'un 8080 portuna gelen trafik container'ın 80 portuna iletilir.

```bash
docker port web1
```

Tarayıcı: http://localhost:8080

### A2. Port mapping varyasyonları

```bash
# Sadece localhost'tan erişilebilir (ağdaki diğer makinelerden DEĞİL)
docker run -d --name web2 -p 127.0.0.1:8082:80 nginx:1.27-alpine

# Host portunu Docker rastgele seçsin
docker run -d --name web3 -p 80 nginx:1.27-alpine

# EXPOSE edilen TÜM portları rastgele host portlarına aç
docker run -d --name web4 -P nginx:1.27-alpine

docker ps --format "table {{.Names}}\t{{.Ports}}" --filter name=web
```

Beklenen çıktı benzeri:

```
NAMES   PORTS
web4    0.0.0.0:55001->80/tcp
web3    0.0.0.0:55000->80/tcp
web2    127.0.0.1:8082->80/tcp
web1    0.0.0.0:8080->80/tcp
```

> ⚠️ **Dikkat:** `-p 8080:80` varsayılan olarak `0.0.0.0` (tüm arayüzler) üzerinde dinler. Veritabanı gibi servisleri geliştirme ortamında bile `127.0.0.1:` önekiyle açmak iyi bir alışkanlıktır.

### A3. Port çakışması

```bash
docker run -d --name web5 -p 8080:80 nginx:1.27-alpine
```

Beklenen hata: `Bind for 0.0.0.0:8080 failed: port is already allocated`

> ❓ **Soru:** İki container **içeride** aynı portu (80) kullanabiliyor ama **host'ta** aynı portu kullanamıyor. Neden?

```bash
docker rm -f web1 web2 web3 web4 web5
```

---

## Bölüm B — Varsayılan bridge'in sınırı

```bash
docker network ls
```

`bridge`, `host`, `none` ağlarını göreceksiniz. `--network` belirtmezseniz container **varsayılan `bridge`** ağına bağlanır.

İki container'ı varsayılan bridge'de başlatın:

```bash
docker run -d --name kutu-a alpine:3.20 sleep 3600
docker run -d --name kutu-b alpine:3.20 sleep 3600
```

kutu-b'nin IP adresini öğrenin:

```bash
docker inspect -f "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" kutu-b
```

IP ile ping (çıkan IP'yi yazın, ör. `172.17.0.3`):

```bash
docker exec kutu-a ping -c 2 172.17.0.3
```

✅ Çalışır. Şimdi **isimle** deneyin:

```bash
docker exec kutu-a ping -c 2 kutu-b
```

❌ Beklenen: `ping: bad address 'kutu-b'`

> 🎓 **Eğitmen notu:** Bu, eğitimin en önemli noktalarından biri. **Varsayılan `bridge` ağında DNS ile isim çözümleme YOKTUR.** Container IP'leri her yeniden başlatmada değişebileceği için IP ile iletişim kurmak kırılgandır. Çözüm: **her zaman kullanıcı tanımlı bir network oluşturun.** Docker Compose bunu sizin için otomatik yapar (Lab 10).

```bash
docker rm -f kutu-a kutu-b
```

---

## Bölüm C — Kullanıcı tanımlı bridge network

```bash
docker network create egitim-net
docker network inspect egitim-net --format "{{json .IPAM.Config}}"
```

Bir web sunucusu ve bir istemci başlatın:

```bash
docker run -d --name api --network egitim-net nginx:1.27-alpine
docker run -d --name istemci --network egitim-net alpine:3.20 sleep 3600
```

İsimle erişim:

```bash
docker exec istemci ping -c 2 api
docker exec istemci wget -qO- http://api
```

✅ Beklenen: ping cevap verir, `wget` nginx'in HTML sayfasını döndürür.

DNS'i inceleyin:

```bash
docker exec istemci nslookup api
docker exec istemci cat /etc/resolv.conf
```

`nameserver 127.0.0.11` → Docker'ın **gömülü DNS sunucusu**.

> 💡 **İpucu:** Dikkat edin: `api` container'ı için **`-p` kullanmadık**. Aynı network'teki container'lar birbirlerinin **tüm portlarına** doğrudan erişebilir. `-p` sadece **host'tan / dış dünyadan** erişim için gereklidir.

### C2. Network alias (takma ad)

```bash
docker run -d --name api-v2 --network egitim-net --network-alias backend nginx:1.27-alpine
docker exec istemci wget -qO- http://backend | head -4
```

---

## Bölüm D — Network izolasyonu (frontend / backend)

Gerçek bir mimariyi taklit edelim:

```
   ┌──── on-yuz (frontend) ────┐     ┌──── arka-yuz (backend) ────┐
   │                           │     │                            │
   │  proxy  ◀──────▶  uygulama ◀────▶ veritabani                 │
   │                           │     │                            │
   └───────────────────────────┘     └────────────────────────────┘
      proxy veritabanına ERİŞEMEMELİ
```

```bash
docker network create on-yuz
docker network create arka-yuz

docker run -d --name veritabani --network arka-yuz nginx:1.27-alpine
docker run -d --name uygulama   --network arka-yuz nicolaka/netshoot sleep 3600
docker run -d --name proxy      --network on-yuz   nicolaka/netshoot sleep 3600

# uygulama'yı ön yüz ağına da bağla (iki ağa birden üye)
docker network connect on-yuz uygulama
```

Testler:

```bash
# uygulama → veritabani  ✅ (aynı arka-yuz ağında)
docker exec uygulama curl -s -o /dev/null -w "%{http_code}\n" http://veritabani

# proxy → uygulama  ✅ (aynı on-yuz ağında)
docker exec proxy ping -c 1 uygulama

# proxy → veritabani  ❌ (farklı ağlarda)
docker exec proxy curl -v -s -m 3 http://veritabani
```

Son komut beklenen çıktı: `curl: (6) Could not resolve host: veritabani`

> ❓ **Soru:** Bir saldırgan `proxy` container'ını ele geçirse, veritabanına doğrudan ulaşabilir mi? Bu tasarım size ne kazandırdı?

Bir container'ın hangi ağlarda olduğunu görün:

```bash
docker inspect uygulama --format "{{json .NetworkSettings.Networks}}"
docker network inspect arka-yuz --format "{{range .Containers}}{{.Name}} {{end}}"
```

---

## Bölüm E — Container'dan host'a erişim

Docker Desktop'ta container içinden **host makinedeki** bir servise (ör. bilgisayarınızda çalışan bir veritabanı) erişmek için özel isim:

```bash
docker run --rm alpine:3.20 ping -c 2 host.docker.internal
```

> 💡 **İpucu:** Container içinde `localhost` → **container'ın kendisi** demektir, host değil! Host'taki servise erişmek için `host.docker.internal` kullanın. (Linux'ta Docker Engine ile `--add-host=host.docker.internal:host-gateway` eklemek gerekir.)

---

## 🧪 Kendin dene
1. `lab-net` adında bir network oluşturun. İçinde `--name redis` ile `redis:7-alpine` başlatın (port açmadan). Aynı ağda `docker run --rm -it --network lab-net redis:7-alpine redis-cli -h redis ping` komutuyla `PONG` cevabını alın.
2. `--network none` ile bir alpine container başlatıp `ping 8.8.8.8` deneyin. Ne oldu?
3. `docker network disconnect on-yuz uygulama` sonrası `proxy` → `uygulama` ping'i ne olur?

## 🧹 Temizlik
```bash
docker rm -f api api-v2 istemci veritabani uygulama proxy redis
docker network rm egitim-net on-yuz arka-yuz lab-net
docker network prune -f
```

## 📌 Özet
- `-p HOST:CONTAINER` → dış dünyadan erişim. Container'lar arası iletişim için **gerekmez**.
- **Varsayılan bridge'de isimle çözümleme yok** → her zaman `docker network create` ile kendi ağınızı kullanın.
- Kullanıcı tanımlı ağda container adı = **DNS adı** (`127.0.0.11`).
- Bir container birden fazla ağa üye olabilir → **frontend/backend izolasyonu**.
- Container içinde `localhost` = container'ın kendisi; host için `host.docker.internal`.
