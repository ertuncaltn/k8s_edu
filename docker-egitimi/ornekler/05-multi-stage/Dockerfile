# syntax=docker/dockerfile:1
# ============================================================
# MULTI-STAGE BUILD
#   Aşama 1 (build)   : derleyici + araçlar  -> binary üretir
#   Aşama 2 (runtime) : SADECE binary        -> küçük & güvenli image
# ============================================================

# ---------- Aşama 1: build ----------
FROM golang:1.23-alpine AS build
WORKDIR /src

# Bağımlılıkları önce indir (cache için)
COPY go.mod ./
RUN go mod download

COPY . .
# CGO_ENABLED=0 -> statik binary (libc gerektirmez, scratch/distroless'ta çalışır)
# -ldflags="-s -w" -> debug sembollerini at, binary küçülsün
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /out/merhaba .

# ---------- Aşama 2: runtime ----------
FROM gcr.io/distroless/static-debian12:nonroot AS runtime
COPY --from=build /out/merhaba /merhaba
EXPOSE 8080
USER nonroot:nonroot
ENTRYPOINT ["/merhaba"]
