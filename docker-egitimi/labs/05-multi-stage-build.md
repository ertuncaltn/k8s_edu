# Lab 05 — Multi-Stage Build

**Süre:** 60 dk · **Klasör:** `ornekler/05-multi-stage`

## Amaç
- **Build-time** bağımlılıklarını (derleyici, SDK, test araçları) **runtime** image'ından ayırmak
- Image boyutundaki ve saldırı yüzeyindeki farkı ölçmek
- `COPY --from`, `AS`, `--target` kullanımını öğrenmek

---

## Kavram

Bir Go / Java / .NET / Node (frontend) uygulamasını derlemek için **SDK** gerekir (yüzlerce MB). Ama çalıştırmak için genellikle **sadece çıktı** yeterlidir.

```
 TEK AŞAMA                                MULTI-STAGE
┌──────────────────────────┐          ┌──────────────────────────┐
│ golang:1.23  (~800 MB)   │          │ AŞAMA 1: build           │
│  ├─ Go derleyici         │          │ golang:1.23-alpine       │
│  ├─ kaynak kod           │          │  ├─ derleyici            │
│  ├─ modül cache          │          │  ├─ kaynak kod           │
│  └─ merhaba (binary)     │          │  └─ merhaba ─────────┐   │
└──────────────────────────┘          └──────────────────────┼───┘
  ⇒ Son image: ~800+ MB                                     │ COPY --from=build
  ⇒ İçinde derleyici, git, shell...   ┌──────────────────────▼───┐
                                      │ AŞAMA 2: runtime         │
                                      │ distroless/static        │
                                      │  └─ merhaba (binary)     │
                                      └──────────────────────────┘
                                        ⇒ Son image: ~10 MB
                                        ⇒ Shell yok, paket yok
```

**Sadece son aşama** image olarak kaydedilir; önceki aşamalar build cache'te kalır ama dağıtılmaz.

---

## Adımlar

```bash
cd ornekler/05-multi-stage
```

Klasörde basit bir Go web sunucusu (`main.go`, `go.mod`) ve üç Dockerfile var.

> 💡 **İpucu:** Go bilmenize gerek yok. Go'yu seçtik çünkü tek bir statik binary üretiyor ve fark çok net görünüyor. Aynı prensip Java (JDK → JRE), .NET (SDK → runtime), Node/React (node → nginx) için de geçerli.

### 1. Tek aşamalı build

`Dockerfile.tek-asama`:
```dockerfile
FROM golang:1.23
WORKDIR /src
COPY . .
RUN go build -o /app/merhaba .
EXPOSE 8080
CMD ["/app/merhaba"]
```

```bash
docker build -f Dockerfile.tek-asama -t merhaba:tek .
docker run -d --name tek -p 8080:8080 merhaba:tek
```

Tarayıcıda http://localhost:8080 → uygulama çalışıyor.

### 2. Multi-stage build

`Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1

# ---------- Aşama 1: build ----------
FROM golang:1.23-alpine AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/merhaba .

# ---------- Aşama 2: runtime ----------
FROM gcr.io/distroless/static-debian12:nonroot AS runtime
COPY --from=build /out/merhaba /merhaba
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/merhaba"]
```

Satır satır:

| Satır | Açıklama |
|---|---|
| `FROM ... AS build` | Aşamaya bir **isim** verir |
| `COPY go.mod` + `go mod download` | Bağımlılıklar ayrı katmanda → cache (Lab 02) |
| `CGO_ENABLED=0` | C kütüphanesine bağımlı olmayan **statik** binary |
| `-ldflags="-s -w"` | Debug sembollerini çıkar → daha küçük binary |
| `FROM gcr.io/distroless/...` | İkinci aşama **sıfırdan** başlar; ilk aşamadan hiçbir şey otomatik gelmez |
| `COPY --from=build` | Sadece binary'yi ilk aşamadan al |
| `:nonroot` / `USER nonroot` | Root olmayan kullanıcı |

```bash
docker build -t merhaba:multi .
docker run -d --name multi -p 8081:8080 merhaba:multi
```

Tarayıcıda http://localhost:8081 → aynı uygulama.

### 3. 📏 Boyut karşılaştırması

```bash
docker images merhaba
```

Beklenen (yaklaşık):

```
REPOSITORY   TAG     SIZE
merhaba      multi   ~10 MB
merhaba      tek     ~850 MB
```

> 🎓 **Eğitmen notu:** Katılımcılardan bu farkın **pratik sonuçlarını** saymalarını isteyin:
> - Registry'e push / pull süresi (CI/CD ve Kubernetes'te pod açılış süresi)
> - Disk ve registry depolama maliyeti
> - **Güvenlik:** image'da ne kadar az yazılım varsa, CVE tarayıcılarının bulacağı açık o kadar az

### 4. 🔒 Saldırı yüzeyi karşılaştırması

```bash
# Tek aşamalı image'da neler var?
docker exec tek sh -c "which go git curl gcc; ls /src"

# Multi-stage image'da shell bile yok
docker exec multi sh
```

İkinci komutun beklenen çıktısı:

```
OCI runtime exec failed: exec failed: unable to start container process: exec: "sh": executable file not found in $PATH
```

> ❓ **Soru:** Bir saldırgan uygulamanızdaki bir açıktan container'a sızsa, hangi image'da daha çok iş yapabilir? Kaynak kodunuz hangi image'da duruyor?

### 5. Belirli bir aşamaya kadar build (`--target`)

Build aşamasında test çalıştırmak veya debug etmek için:

```bash
docker build --target build -t merhaba:build-asamasi .
docker run --rm merhaba:build-asamasi ls -la /out
docker run --rm merhaba:build-asamasi go version
```

### 6. En uç nokta: `scratch`

`Dockerfile.scratch` → `FROM scratch` tamamen **boş** bir image'dır.

```bash
docker build -f Dockerfile.scratch -t merhaba:scratch .
docker images merhaba
```

> ⚠️ **Dikkat:** `scratch` içinde CA sertifikaları, timezone verisi, `/tmp` ve kullanıcı tanımları yoktur. Uygulamanız HTTPS isteği atıyorsa sertifika hatası alırsınız. `distroless/static` bunları içerdiği için genellikle daha güvenli bir tercihtir.

---

## Diğer dillerde multi-stage örnekleri (referans)

**Node.js / React (SPA) → nginx:**
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
```

**Java (Maven) → JRE:**
```dockerfile
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -q dependency:go-offline
COPY src ./src
RUN mvn -q package -DskipTests

FROM eclipse-temurin:21-jre-alpine
COPY --from=build /src/target/*.jar /app/app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

**.NET:**
```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY *.csproj .
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /out

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /out .
ENTRYPOINT ["dotnet", "Uygulama.dll"]
```

> 💡 **İpucu:** Ortak desen hep aynı: **(1)** bağımlılık dosyasını kopyala → **(2)** bağımlılıkları indir → **(3)** kaynak kodu kopyala → **(4)** derle → **(5)** yeni bir aşamada sadece çıktıyı al.

---

## 🧪 Kendin dene
1. `main.go`'daki mesajı değiştirip `merhaba:multi`'yi yeniden build edin. Hangi adımlar cache'ten geldi?
2. Multi-stage Dockerfile'a `test` adında üçüncü bir aşama ekleyin (`FROM build AS test` + `RUN go vet ./...`). `--target test` ile build edin.
3. Aynı uygulamayı `PORT=9000` ortam değişkeniyle çalıştırın: `docker run --rm -e PORT=9000 -p 9000:9000 merhaba:multi`.

## 🧹 Temizlik
```bash
docker rm -f tek multi
docker image rm merhaba:tek merhaba:multi merhaba:scratch merhaba:build-asamasi
```

## 📌 Özet
- Multi-stage → **derleme ortamı** ile **çalışma ortamını** ayırır.
- Son image'a sadece **son aşama** girer; önceki aşamalardan `COPY --from=` ile seçerek alırsınız.
- Kazanç: **~%90+ boyut azalması**, **daha az CVE**, **daha hızlı dağıtım**.
- `--target` ile ara aşamaları test / debug için build edebilirsiniz.
