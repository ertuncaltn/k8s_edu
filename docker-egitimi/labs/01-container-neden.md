# Lab 01 — Container'ın Çözdüğü Sorun

**Süre:** 45 dk · **Kullanılan image'lar:** `alpine:3.20`, `nginx:1.27-alpine`, `python:3.12-slim`, `python:3.11-slim`

## Amaç
- "Benim makinemde çalışıyordu" problemini ve container'ın buna çözümünü anlamak
- **İzolasyon**, **taşınabilirlik** ve **kaynak verimliliği** kavramlarını *deneyerek* görmek
- Container yaşam döngüsünü (run → ps → logs → exec → stop → rm) öğrenmek

---

## Kavram

| Problem | Container'ın çözümü |
|---|---|
| Geliştiricide Python 3.12, sunucuda 3.8 var | Uygulama **kendi runtime'ı ile birlikte** paketlenir |
| İki uygulama aynı kütüphanenin farklı sürümünü istiyor | Her container'ın **kendi dosya sistemi** vardır |
| VM başına GB'larca RAM ve dakikalarca açılış süresi | Container'lar **host çekirdeğini paylaşır**; MB'lar ve milisaniyeler |
| "Kurulum dokümanı" güncel değil | Kurulum **Dockerfile** olarak koddadır, tekrarlanabilir |

```
       SANAL MAKİNE                              CONTAINER
┌───────┐┌───────┐┌───────┐            ┌───────┐┌───────┐┌───────┐
│ App A ││ App B ││ App C │            │ App A ││ App B ││ App C │
│ Libs  ││ Libs  ││ Libs  │            │ Libs  ││ Libs  ││ Libs  │
│Guest OS││Guest OS││Guest OS│          └───────┘└───────┘└───────┘
└───────┘└───────┘└───────┘            ┌──────────────────────────┐
┌──────────────────────────┐            │   Container Runtime      │
│       Hypervisor         │            ├──────────────────────────┤
├──────────────────────────┤            │  Host OS (tek çekirdek)  │
│        Host OS           │            ├──────────────────────────┤
├──────────────────────────┤            │       Donanım            │
│       Donanım            │            └──────────────────────────┘
└──────────────────────────┘
```

> 🎓 **Eğitmen notu:** Container bir "hafif VM" **değildir**. Linux çekirdeğinin iki özelliği üzerine kurulmuş, **izole edilmiş bir süreçtir (process)**:
> - **Namespaces** → *ne görebilir?* (process, network, dosya sistemi, hostname, kullanıcı)
> - **cgroups** → *ne kadar kullanabilir?* (CPU, RAM, I/O)
>
> Bu lab'daki her deney bu iki kavramdan birini gösteriyor. Deneyleri yaptırırken hangisi olduğunu sorun.

---

## Bölüm A — İzolasyon

### A1. Process izolasyonu (PID namespace)

Container içindeki process'leri listeleyin:

```bash
docker run --rm alpine:3.20 ps aux
```

Beklenen çıktı:

```
PID   USER     TIME  COMMAND
    1 root      0:00 ps aux
```

> ❓ **Soru:** Bilgisayarınızda yüzlerce process çalışıyor. Container neden sadece **bir** tane görüyor? `ps` neden **PID 1**?

docker run -d --name test alpine sleep infinity

### A2. Hostname izolasyonu (UTS namespace)

```bash
docker run --rm alpine:3.20 hostname
docker run --rm alpine:3.20 hostname
docker run --rm --hostname egitim-kutusu alpine:3.20 hostname
```

Her container kendi hostname'ine sahiptir (varsayılan: container ID'nin ilk 12 karakteri).

### A3. Dosya sistemi izolasyonu (mount namespace)

İki ayrı terminal açın.

**Terminal 1:**
```bash
docker run -it --rm --name kutu1 alpine:3.20 sh
```
Container içindeyken:
```sh
echo "kutu1'in gizli dosyası" > /tmp/gizli.txt
cat /tmp/gizli.txt
```

**Terminal 2:**
```bash
docker run -it --rm --name kutu2 alpine:3.20 sh
```
Container içindeyken:
```sh
ls /tmp
cat /tmp/gizli.txt
```

Beklenen: `cat: can't open '/tmp/gizli.txt': No such file or directory`

İki terminalde de `exit` yazarak çıkın.

> ❓ **Soru:** İki container **aynı image**'dan başladı. Neden birinin yazdığı dosyayı diğeri görmüyor? (İpucu: Lab 02'de "container writable layer" kavramını göreceğiz.)

### A4. Kaynak izolasyonu (cgroups)

Belleği 64 MB ile sınırlı bir container başlatın ve limiti görün:

```bash
docker run -d --name sinirli --memory 64m --cpus 0.5 nginx:1.27-alpine
docker stats --no-stream sinirli
```

Beklenen: `MEM USAGE / LIMIT` sütununda `... / 64MiB` görmelisiniz.

```bash
docker rm -f sinirli
```

> 💡 **İpucu:** Production'da her container'a **mutlaka** bellek limiti verin. Limitsiz bir container, bellek sızıntısında host'taki diğer tüm servisleri etkileyebilir.

---

## Bölüm B — Taşınabilirlik

Aynı makinede, **hiçbir şey kurmadan**, iki farklı Python sürümünü yan yana çalıştırın:

```bash
docker run --rm python:3.11-slim python --version
docker run --rm python:3.12-slim python --version
```

Şimdi Python'un kurulu olup olmadığını host'ta kontrol edin:

```bash
python --version
```

> ❓ **Soru:** Host'ta Python kurulu olmasa bile container'daki Python nasıl çalıştı? Aynı image'ı bir Linux sunucusunda çalıştırsaydık sonuç değişir miydi?

> 🎓 **Eğitmen notu:** Burada "taşınabilirlik"in sınırını da söyleyin: image'lar **CPU mimarisine** bağlıdır (amd64 / arm64). Apple Silicon Mac'lerde Docker Desktop çoğu resmi image'ın arm64 sürümünü otomatik çeker. Kendi image'larımızda bunu `docker buildx --platform` ile yöneteceğiz (Lab 11).

---

## Bölüm C — Kaynak verimliliği

### C1. Başlangıç süresi

**bash / zsh:**
```bash
time docker run --rm alpine:3.20 echo "merhaba"
```

**PowerShell:**
```powershell
Measure-Command { docker run --rm alpine:3.20 echo "merhaba" }
```

Beklenen: genellikle **1 saniyenin altında**. Bir VM'in açılmasıyla karşılaştırın.

### C2. Aynı anda 10 web sunucusu

**bash / zsh:**
```bash
for i in 1 2 3 4 5 6 7 8 9 10; do docker run -d --name web$i nginx:1.27-alpine; done
```

**PowerShell:**
```powershell
1..10 | ForEach-Object { docker run -d --name "web$_" nginx:1.27-alpine }
```

Kaynak tüketimine bakın:

```bash
docker stats --no-stream
```

> ❓ **Soru:** 10 nginx container'ı toplam ne kadar RAM kullanıyor? 10 VM olsaydı ne kadar olurdu?

Temizlik:

**bash / zsh:**
```bash
docker rm -f web1 web2 web3 web4 web5 web6 web7 web8 web9 web10
```

**PowerShell:**
```powershell
1..10 | ForEach-Object { docker rm -f "web$_" }
```

---

## Bölüm D — Container yaşam döngüsü

```
  docker create      docker start        docker stop / kill      docker rm
 ─────────────▶ Created ─────────▶ Running ──────────────▶ Exited ────────▶ (silindi)
        └────────────── docker run (= create + start) ──────────┘
```

Adım adım uygulayın:

```bash
# 1) Arka planda (-d) bir web sunucusu başlat, host'un 8080'ini container'ın 80'ine bağla
docker run -d --name websunucu -p 8080:80 nginx:1.27-alpine

# 2) Çalışan container'ları listele
docker ps

# 3) Tarayıcıda http://localhost:8080 adresini açın, sonra logları görün
docker logs websunucu

# 4) Logları canlı takip et (Ctrl+C ile çıkın) — tarayıcıda sayfayı birkaç kez yenileyin
docker logs -f websunucu

# 5) Çalışan container'ın içine gir
docker exec -it websunucu sh
```

Container içinde:
```sh
cat /etc/os-release
ls /usr/share/nginx/html
echo "<h1>Container icinden degistirildi</h1>" > /usr/share/nginx/html/index.html
exit
```

Tarayıcıyı yenileyin → sayfa değişti.

```bash
# 6) Durdur ve tüm container'ları (durmuşlar dahil) listele
docker stop websunucu
docker ps -a

# 7) Tekrar başlat -> yaptığınız değişiklik HÂLÂ duruyor mu?
docker start websunucu
```

Tarayıcıyı yenileyin. Değişiklik duruyor. Şimdi:

```bash
# 8) Sil ve aynı image'dan yeniden oluştur
docker rm -f websunucu
docker run -d --name websunucu -p 8080:80 nginx:1.27-alpine
```

Tarayıcıyı yenileyin → **değişiklik kayboldu**, varsayılan nginx sayfası geri geldi.

> ⚠️ **Dikkat:** Container'ın içinde yaptığınız değişiklikler **container silinince kaybolur**. `stop` veriyi silmez, `rm` siler. Kalıcı veri için volume kullanılır (Lab 08).

> 💡 **İpucu:** `docker inspect websunucu` container'ın tüm detaylarını (IP, mount'lar, env, restart policy) JSON olarak verir. Tek bir alanı almak için:
> ```bash
> docker inspect --format "{{.State.Status}}" websunucu
> ```

---

## 🧪 Kendin dene
1. `nginx:1.27-alpine` image'ından `--name deneme` ile bir container başlatın ama **host port 9090**'dan erişilebilir olsun.
2. `docker exec` ile container'ın içinde `nginx -v` çalıştırın (interaktif shell açmadan).
3. `docker run --rm -it alpine:3.20 sh` ile girip `apk add curl` yapın, çıkın, tekrar girin. `curl` hâlâ var mı? Neden?

## 🧹 Temizlik
```bash
docker rm -f websunucu deneme
```

## 📌 Özet
- Container = namespaces (ne görür) + cgroups (ne kadar kullanır) ile izole edilmiş **process**
- Image → **salt okunur şablon**, Container → image'ın **çalışan örneği**
- `run` = `create` + `start`; `stop` veriyi korur, `rm` siler
- `--rm` → container durunca otomatik silinir (denemeler için ideal)
