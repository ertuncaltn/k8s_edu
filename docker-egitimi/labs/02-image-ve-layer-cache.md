# Lab 02 — Image Layer Yapısı ve Layer Cache

**Süre:** 60 dk · **Klasör:** `ornekler/02-layer-cache`

## Amaç
- Image'ın **üst üste binmiş salt okunur katmanlardan** oluştuğunu görmek
- Container'ın **yazılabilir katmanını** anlamak
- Build cache'in nasıl çalıştığını ve **Dockerfile sırasının** build süresine etkisini ölçmek

---

## Kavram

### Image = katmanlar yığını

Dockerfile'daki dosya sistemini değiştiren her komut (`RUN`, `COPY`, `ADD`) **yeni bir katman** oluşturur. Katmanlar salt okunurdur ve **içerik hash'i** ile tanımlanır.

```
                    ┌─────────────────────────────────────┐
  Container  ─────▶ │  Yazılabilir katman (container'a özel)│  ← docker rm ile silinir
                    ╞═════════════════════════════════════╡
                    │  COPY . .              (app.py)      │  ┐
                    ├─────────────────────────────────────┤  │
                    │  RUN pip install ...   (flask)       │  │  IMAGE
                    ├─────────────────────────────────────┤  │  (salt okunur,
                    │  COPY requirements.txt               │  │   tüm container'lar
                    ├─────────────────────────────────────┤  │   paylaşır)
                    │  WORKDIR /app                        │  │
                    ├─────────────────────────────────────┤  │
                    │  python:3.12-slim katmanları         │  ┘
                    └─────────────────────────────────────┘
```

- 10 container aynı image'dan başlarsa, image katmanları **diskte 1 kez** tutulur (copy-on-write).
- Bir katman değişirse, **o katman ve üstündeki TÜM katmanlar** yeniden oluşturulur.

### Cache kuralları (özet)

| Komut | Cache ne zaman geçersiz olur? |
|---|---|
| `FROM` | Base image değişirse |
| `RUN` | Komut **metni** değişirse (dış dünyadaki değişikliği bilmez!) |
| `COPY` / `ADD` | Kopyalanan dosyaların **içeriği** değişirse |
| Herhangi biri | Kendinden **önceki** bir katman yeniden oluşturulduysa |

> 🎓 **Eğitmen notu:** `RUN apt-get update` örneğini verin: komut metni aynı kaldıkça Docker onu cache'ten getirir, yani paket listesi haftalarca eski kalabilir. Bu yüzden `apt-get update && apt-get install ...` her zaman **aynı RUN** satırında olmalı.

---

## Adımlar

```bash
cd ornekler/02-layer-cache
```

Klasörde şunlar var: `app.py`, `requirements.txt`, `Dockerfile` (iyi), `Dockerfile.kotu`.

### 1. Bir image'ın katmanlarını inceleyin

```bash
docker pull python:3.12-slim
docker history python:3.12-slim
```

Her satır bir katmandır. `SIZE` sütununa bakın; bazı satırlar `0B`'dır (sadece metadata değiştiren `ENV`, `CMD` gibi komutlar).

```bash
docker image inspect python:3.12-slim --format "{{json .RootFS.Layers}}"
```

Çıktıdaki her `sha256:...` bir katmanın içerik hash'idir.

### 2. KÖTÜ Dockerfile ile build

Önce dosyayı inceleyin:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .                                             # ← tüm kaynak kod ÖNCE
RUN pip install --no-cache-dir -r requirements.txt   # ← sonra bağımlılıklar
EXPOSE 5000
CMD ["python", "app.py"]
```

Build edin:

```bash
docker build -f Dockerfile.kotu -t cache-demo:kotu .
```

> 💡 **İpucu:** Komutun sonundaki **`.`** build context'tir: "bu klasördeki dosyaları Docker Engine'e gönder" demektir. Unutulursa hata alırsınız.

Şimdi `app.py` dosyasını açıp `MESAJ` satırını değiştirin:

```python
MESAJ = "Merhaba Docker! (v2)"
```

Tekrar build edin ve **süreyi gözlemleyin**:

```bash
docker build -f Dockerfile.kotu -t cache-demo:kotu .
```

Çıktıda şuna benzer satırlar göreceksiniz:

```
 => CACHED [2/4] WORKDIR /app
 => [3/4] COPY . .
 => [4/4] RUN pip install --no-cache-dir -r requirements.txt     ← YENİDEN ÇALIŞTI!
```

> ❓ **Soru:** Sadece `app.py`'de bir kelime değiştirdik, `requirements.txt` aynı kaldı. Neden `pip install` yeniden çalıştı?

### 3. İYİ Dockerfile ile build

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .                              # ← önce SADECE bağımlılık listesi
RUN pip install --no-cache-dir -r requirements.txt
COPY . .                                             # ← kaynak kod EN SONDA
EXPOSE 5000
CMD ["python", "app.py"]
```

```bash
docker build -t cache-demo:iyi .
```

`app.py`'deki mesajı tekrar değiştirin (`v3` yapın) ve yeniden build edin:

```bash
docker build -t cache-demo:iyi .
```

Beklenen:

```
 => CACHED [2/5] WORKDIR /app
 => CACHED [3/5] COPY requirements.txt .
 => CACHED [4/5] RUN pip install --no-cache-dir -r requirements.txt   ← CACHE!
 => [5/5] COPY . .
```

> 🎓 **Eğitmen notu:** Bu, eğitimin en önemli "aha" anlarından biri. İki build süresini tahtaya yazdırın. Gerçek projelerde (Node `npm install`, Java `mvn dependency:resolve`) fark dakikalar mertebesindedir ve CI maliyetine doğrudan yansır.

### 4. Uygulamayı çalıştırın

```bash
docker run -d --name cache-app -p 5000:5000 cache-demo:iyi
```

Tarayıcıda http://localhost:5000 → `Merhaba Docker! (v3) (container: ...)`

> ⚠️ **Dikkat (macOS):** 5000 portu AirPlay Receiver tarafından kullanılıyorsa `-p 5050:5000` kullanıp http://localhost:5050 adresine gidin.

### 5. Container'ın yazılabilir katmanını görün

```bash
docker exec cache-app sh -c "echo test > /app/yeni-dosya.txt && mkdir /tmp/deneme"
docker diff cache-app
```

Beklenen çıktı (sıra farklı olabilir):

```
C /app
A /app/yeni-dosya.txt
C /tmp
A /tmp/deneme
```

`A` = eklendi (Added), `C` = değişti (Changed), `D` = silindi (Deleted). Bunlar **sadece bu container'ın** yazılabilir katmanındadır; image değişmedi.

### 6. Katman paylaşımını görün

```bash
docker images cache-demo
docker system df -v
```

> ❓ **Soru:** `cache-demo:kotu` ve `cache-demo:iyi` ayrı ayrı ~150 MB görünüyor. Diskte gerçekten 300 MB mı yer kaplıyorlar? (`docker system df -v` çıktısındaki `SHARED SIZE` ve `UNIQUE SIZE` sütunlarına bakın.)

### 7. Cache'i bilerek devre dışı bırakma

```bash
docker build --no-cache -t cache-demo:iyi .
```

Tüm adımlar sıfırdan çalışır. Ne zaman gerekir? Örneğin `RUN apt-get update` ile gelen paketleri güncellemek istediğinizde.

---

## 🧪 Kendin dene
1. `requirements.txt` dosyasına `requests==2.32.3` satırını ekleyin ve `cache-demo:iyi`'yi yeniden build edin. Hangi adımlar cache'ten geldi, hangileri yeniden çalıştı?
2. `docker history cache-demo:iyi` çıktısında kendi eklediğiniz katmanları bulun. Hangisi en büyük?
3. Dockerfile'a `RUN echo "tarih: $(date)"` satırı ekleyin. İki kez build edin. İkincisinde tarih değişti mi? Bu size `RUN` cache'i hakkında ne söylüyor?

## 🧹 Temizlik
```bash
docker rm -f cache-app
docker image rm cache-demo:kotu cache-demo:iyi
```

## 📌 Özet
- Image, **salt okunur katmanların** yığınıdır; container bunun üstüne **ince bir yazılabilir katman** ekler.
- Bir katman değişince, **üstündeki her şey** yeniden oluşturulur.
- **Altın kural:** Az değişen şeyler Dockerfile'ın **üstüne**, sık değişenler **altına**.
- `RUN` cache'i komut **metnine** bakar, sonuca değil.
