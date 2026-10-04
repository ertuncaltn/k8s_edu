# Eğitimde kullanılan tüm image'ları önceden indirir (Windows PowerShell)
# Kullanım: powershell -ExecutionPolicy Bypass -File .\imajlari-indir.ps1
$imajlar = @(
  "hello-world"
  "alpine:3.20"
  "nginx:1.27-alpine"
  "python:3.12"
  "python:3.12-slim"
  "python:3.12-alpine"
  "python:3.11-slim"
  "golang:1.23"
  "golang:1.23-alpine"
  "gcr.io/distroless/static-debian12:nonroot"
  "gcr.io/distroless/python3-debian12:nonroot"
  "redis:7-alpine"
  "postgres:16-alpine"
  "registry:2"
  "nicolaka/netshoot"
)
foreach ($i in $imajlar) { Write-Host ">>> $i" -ForegroundColor Cyan; docker pull $i }
Write-Host "`nTamamlandı." -ForegroundColor Green; docker images
