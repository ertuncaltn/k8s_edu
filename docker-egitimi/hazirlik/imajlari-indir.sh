#!/usr/bin/env bash
# Eğitimde kullanılan tüm image'ları önceden indirir (macOS / Linux / WSL / Git Bash)
# Kullanım: bash imajlari-indir.sh
set -e
IMAJLAR="hello-world alpine:3.20 nginx:1.27-alpine python:3.12 python:3.12-slim python:3.12-alpine python:3.11-slim golang:1.23 golang:1.23-alpine gcr.io/distroless/static-debian12:nonroot gcr.io/distroless/python3-debian12:nonroot redis:7-alpine postgres:16-alpine registry:2 nicolaka/netshoot"
for i in $IMAJLAR; do echo ">>> $i"; docker pull "$i"; done
echo; echo "Tamamlandı. İndirilen image'lar:"; docker images
