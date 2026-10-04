# Docker Cheatsheet ve Sorun Giderme

> Bu sayfayı eğitim boyunca açık tutun.

## Image

| Komut | Açıklama |
|---|---|
| `docker build -t ad:tag .` | Bulunduğun klasördeki Dockerfile ile build |
| `docker build -f Dockerfile.prod -t ad:tag .` | Farklı Dockerfile |
| `docker build --no-cache -t ad:tag .` | Cache'siz build |
| `docker build --target build -t ad:build .` | Multi-stage'de belirli aşamaya kadar |
| `docker build --build-arg X=1 -t ad:tag .` | ARG değeri ver |
| `docker build --progress=plain ...` | Build çıktısını düz metin göster |
| `docker images` / `docker image ls` | Image'ları listele |
| `docker history ad:tag` | Katmanları göster |
| `docker image inspect ad:tag` | Tüm metadata |
| `docker tag kaynak:tag hedef:tag` | Yeni isim/tag ekle |
| `docker push registry/ad:tag` | Registry'e gönder |
| `docker pull ad:tag` | Registry'den çek |
| `docker image rm ad:tag` | Sil |
| `docker image prune` | Etiketsiz (dangling) image'ları sil |

## Container

| Komut | Açıklama |
|---|---|
| `docker run -d --name x -p 8080:80 img` | Arka planda, isimli, port açık başlat |
| `docker run --rm -it img sh` | İnteraktif, çıkınca silinsin |
| `docker run -e K=V --env-file f.env img` | Ortam değişkenleri |
| `docker run -v vol:/data img` | Named volume |
| `docker run -v "${PWD}/dir:/data:ro" img` | Bind mount (salt okunur) |
| `docker run --network net img` | Belirli ağda |
| `docker run --memory 256m --cpus 0.5 img` | Kaynak limiti |
| `docker ps` / `docker ps -a` | Çalışanlar / tümü |
| `docker logs -f --tail 50 x` | Canlı log (son 50 satırdan) |
| `docker exec -it x sh` | İçeri gir |
| `docker stop x` / `docker start x` | Durdur / başlat |
| `docker rm -f x` | Zorla sil |
| `docker inspect x` | Tüm detay |
| `docker stats` | Canlı kaynak kullanımı |
| `docker diff x` | Yazılabilir katmandaki değişiklikler |
| `docker cp x:/yol/dosya .` | Container'dan dosya kopyala |
| `docker port x` | Port eşlemeleri |

## Network & Volume

| Komut | Açıklama |
|---|---|
| `docker network create net` | Kullanıcı tanımlı bridge |
| `docker network ls` / `inspect net` | Listele / detay |
| `docker network connect net x` | Çalışan container'ı ağa ekle |
| `docker volume create vol` | Volume oluştur |
| `docker volume ls` / `inspect vol` | Listele / detay |
| `docker volume rm vol` | Sil (**veri gider**) |

## Compose

| Komut | Açıklama |
|---|---|
| `docker compose up -d --build` | Build + başlat |
| `docker compose ps` | Durum |
| `docker compose logs -f servis` | Log |
| `docker compose exec servis sh` | İçeri gir |
| `docker compose run --rm servis komut` | Tek seferlik container |
| `docker compose config` | Yorumlanmış YAML |
| `docker compose down` | Kaldır (volume kalır) |
| `docker compose down -v` | Kaldır + **volume sil** |
| `docker compose up -d --scale web=3` | Ölçekle |
| `docker compose watch` | Canlı geliştirme |

## Temizlik

| Komut | Siler |
|---|---|
| `docker container prune` | Durmuş container'lar |
| `docker image prune -a` | Hiçbir container'ın kullanmadığı tüm image'lar |
| `docker volume prune` | Kullanılmayan volume'lar (**veri gider**) |
| `docker builder prune` | Build cache |
| `docker system prune` | Hepsinden biraz (volume hariç) |
| `docker system df` | Ne kadar yer kaplanıyor? |

## Dockerfile şablonu (Python)

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
RUN useradd --create-home --uid 10001 uygulama
WORKDIR /app
COPY --from=build /install /usr/local
COPY --chown=uygulama:uygulama . .
USER uygulama
EXPOSE 5000
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

## Dockerfile best-practice kontrol listesi

- [ ] Base image tag'i sabit (`latest` değil)
- [ ] `.dockerignore` var
- [ ] Bağımlılık dosyası kaynak koddan **önce** kopyalanıyor
- [ ] `RUN` komutları `&&` ile birleştirilmiş, cache temizleniyor (`--no-cache`, `rm -rf /var/lib/apt/lists/*`)
- [ ] Derleme gerekiyorsa **multi-stage**
- [ ] Root olmayan `USER`
- [ ] `CMD` / `ENTRYPOINT` **exec form**
- [ ] Image'da şifre / token yok
- [ ] `HEALTHCHECK` tanımlı
- [ ] `COPY` tercih ediliyor (ADD sadece tar için)

---

# 🔧 Sorun Giderme

| Belirti / Hata | Olası neden | Çözüm |
|---|---|---|
| `Cannot connect to the Docker daemon` / `error during connect` | Docker Desktop çalışmıyor | Docker Desktop'ı başlatın, 30 sn bekleyin |
| `port is already allocated` | Host portu başka container/uygulama tarafından kullanılıyor | `docker ps` ile bulun, durdurun veya farklı host portu seçin |
| macOS'ta 5000 portu çalışmıyor | AirPlay Receiver 5000'i kullanıyor | `-p 5050:5000` gibi farklı port |
| `toomanyrequests: You have reached your pull rate limit` | Docker Hub anonim çekme limiti | `docker login` yapın veya image'ları önceden indirin |
| `pull access denied` / `repository does not exist` | Image adı yanlış veya private | Adı/tag'i kontrol edin, gerekirse `docker login` |
| `COPY failed: file not found in build context` | Dosya context dışında veya `.dockerignore` hariç tutuyor | `docker build` komutunun **son argümanını** (`.`) ve `.dockerignore`'u kontrol edin |
| Container hemen çıkıyor (`Exited (0)` / `Exited (1)`) | Ana process bitti veya hata verdi | `docker logs <container>` |
| `exec: "sh": executable file not found` | Distroless / scratch image, shell yok | Debug sidecar veya `docker debug` (Lab 06) |
| `exec format error` | CPU mimarisi uyumsuz (arm64 ↔ amd64) | `--platform linux/amd64` veya `buildx` ile çoklu mimari |
| Container'dan `localhost:5432`'ye bağlanamıyorum | Container içinde `localhost` = container'ın kendisi | Aynı compose'taysa **servis adı** (`db`), host'taysa `host.docker.internal` |
| `ping: bad address 'xxx'` | Varsayılan bridge ağı (DNS yok) veya farklı ağlar | Kullanıcı tanımlı ağ oluşturun, iki container'ı aynı ağa bağlayın |
| Bind mount'ta dosyalar görünmüyor (Windows) | Yanlış yol / sürücü paylaşımı | `${PWD}` kullandığınızdan ve doğru klasörde olduğunuzdan emin olun; PowerShell önerilir |
| Bind mount boş klasör gibi görünüyor | Bind mount image içeriğini gizler | Doğru host klasörünü bağladığınızı kontrol edin |
| Compose'ta web, DB'den önce başlayıp hata veriyor | `depends_on` sadece başlama sırası sağlar | `condition: service_healthy` + DB healthcheck |
| Veritabanı verisi kayboldu | `docker compose down -v` veya volume tanımsız | Named volume tanımlayın, `-v` bayrağını kullanmayın |
| Build her seferinde baştan çalışıyor | Dockerfile sırası kötü veya context sürekli değişiyor | Lab 02 + Lab 04 |
| Disk doldu | Image / cache / volume birikti | `docker system df`, ardından `docker system prune` |
| Kurumsal ağda pull çalışmıyor | Proxy / SSL denetimi | Docker Desktop → Settings → Resources → Proxies; kurum CA sertifikası |
