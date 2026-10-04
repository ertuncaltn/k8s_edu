#!/usr/bin/env bash
# Öğrenci ortamının hazır olup olmadığını kontrol eder
echo "== Docker sürümü ==";          docker version --format 'Client: {{.Client.Version}}  Server: {{.Server.Version}}' || { echo "HATA: Docker çalışmıyor! Docker Desktop'ı başlatın."; exit 1; }
echo "== Compose sürümü ==";         docker compose version
echo "== Test container ==";         docker run --rm hello-world | head -3
echo "== Port 8080 testi ==";        docker run -d --rm --name port-testi -p 8080:80 nginx:1.27-alpine >/dev/null && sleep 2 && (curl -s -o /dev/null -w "HTTP %{http_code}\n" http://localhost:8080 || echo "curl yok, tarayıcıdan http://localhost:8080 açın"); docker stop port-testi >/dev/null
echo "== Disk kullanımı ==";         docker system df
echo; echo "Ortam HAZIR ✔"
