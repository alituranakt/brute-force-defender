# Brute-Force Defender - Proje Analiz Raporu

## Tersine Mühendislik Dersi - Vize Projesi

**Proje:** 14. Brute-Force Defender
**Konu:** BLAKE3 kullanarak bir hash kırma denemesine karşı tuzlama (salting) mekanizmasının etkisini gösterme

---

## Adım 1: Kurulum ve install.sh Analizi (Reverse Engineering)

### 1.1 install.sh Ne Yapıyor?

`install.sh` scripti 8 aşamadan oluşur ve her aşama ayrıntılı olarak loglanır:

**Aşama 0 - Ön Kontroller:**
- İşletim sistemi tespiti (`uname -s`) → Linux, macOS, Windows (Cygwin/MSYS) ayrımı
- Root yetkisi kontrolü → Root olarak çalıştırılırsa uyarı verilir (gerekli değil)
- `main.py` varlık kontrolü → Script doğru dizinden mi çalışıyor?
- Disk alanı kontrolü (`df -m`) → Minimum 100MB boş alan gerekli

**Aşama 1 - Python Kontrolü:**
- `python3` veya `python` komutunu arar
- Sürüm kontrolü: Python 3.8+ gerekli (major.minor karşılaştırması)
- pip varlık kontrolü

**Aşama 2 - Dizin Oluşturma:**
- `logs/` → Uygulama ve kurulum logları
- `results/` → Grafik çıktıları ve JSON raporları
- `data/` → Veritabanı dosyaları (users.json)
- `docs/` → Dokümantasyon

**Aşama 3 - Sanal Ortam (venv):**
- `python -m venv venv` ile izole Python ortamı
- `source venv/bin/activate` ile aktifleştirme
- pip güncelleme

**Aşama 4 - Bağımlılık Kurulumu:**
- `pip install -r requirements.txt` ile paket kurulumu
- Her paketin import kontrolü ile doğrulama
- Kurulan paketler `pip freeze` ile loglanır

**Aşama 5 - Konfigürasyon:**
- `.env` dosyası oluşturulur
- `secrets.token_hex(32)` ile kriptografik güvenli JWT secret key üretilir
- `chmod 600` ile sadece dosya sahibi okuyabilir

**Aşama 6 - Dosya İzinleri:**
- `install.sh`, `uninstall.sh`, `main.py`, `app.py` → `chmod +x` (çalıştırılabilir)
- `.env` → `chmod 600` (sadece sahip)
- `logs/` → `chmod 750` (sahip + grup)

**Aşama 7 - Doğrulama:**
- Python import testleri (blake3, flask, jwt, matplotlib)
- Proje modül testi (BLAKE3Hasher)
- Birim testleri (pytest/unittest)
- Dizin yapısı kontrolü

### 1.2 Güvenlik Analizi

| Kriter | Durum | Açıklama |
|--------|-------|----------|
| `curl \| bash` kalıbı | YOK | Güvensiz kalıp kullanılmıyor |
| Hash doğrulaması | KISMİ | pip HTTPS + TLS kullanır, ancak `--require-hashes` zorunlu değil |
| Dışarıdan kaynak | PyPI | Sadece resmi Python paket deposu kullanılır |
| Root yetkisi | GEREKMİYOR | Tüm işlemler kullanıcı dizininde |
| Secret yönetimi | GÜVENLİ | `secrets.token_hex()` ile CSPRNG kullanılır |
| Log kaydı | TAM | Her adım tarih/saat ile loglanır |

### 1.3 Potansiyel Riskler

1. **PyPI paketi değiştirilmiş olabilir (supply chain attack):** pip hash doğrulaması (`--require-hashes`) zorunlu değil. Çözüm: `requirements.txt` dosyasına hash'ler eklenmeli.
2. **Sanal ortam dışında paket kalıntısı:** venv kullanılarak izole edilmiş.
3. **`.env` dosyası Git'e push edilebilir:** `.gitignore` dosyasında tanımlı, ancak geliştirici dikkati gerekli.

---

## Adım 2: İzolasyon ve İz Bırakmadan Temizlik (Forensics & Cleanup)

### 2.1 uninstall.sh Ne Yapıyor?

**Aşama 1 - Arka Plan Süreçlerini Durdurma:**
- `pgrep -f "python.*app.py"` ile Flask sürecini bulur ve durdurur
- `lsof -i :5000` veya `ss -tlnp` ile port kontrolü
- İlişkili tüm Python süreçlerini `kill` eder

**Aşama 2 - Docker Temizliği:**
- `docker ps -a --filter "name=brute-force-defender"` ile konteynerleri bulur
- `docker stop` + `docker rm` ile kaldırır
- `docker rmi` ile imajları siler
- `docker-compose down --volumes --remove-orphans` ile tüm compose kaynaklarını temizler
- `docker volume prune` ile sahipsiz volume'ları siler

**Aşama 3 - Sanal Ortam Temizliği:**
- `deactivate` ile venv'den çıkar
- `rm -rf venv/` ile sanal ortamı tamamen siler
- `pip cache purge` ile pip cache'ini temizler

**Aşama 4 - Dosya Temizliği:**
- `.env` ve `users.json` → Güvenli silme (`dd if=/dev/zero` ile üzerine yaz + `rm`)
- `logs/`, `results/`, `data/` dizinleri tamamen silinir
- `__pycache__`, `.pyc`, `.egg-info`, `.pytest_cache` temizlenir

**Aşama 5 - Doğrulama (Forensics):**
- Dosya sistemi taraması (kalan dizin/dosya kontrolü)
- Port taraması (`lsof` veya `ss`)
- Süreç taraması (`pgrep`)
- Docker konteyner/imaj kontrolü

### 2.2 Kalıntı Olmadığının İspatı

Doğrulama yöntemleri:

```bash
# 1. Dosya sistemi kontrolü
find /path/to/project -name "*.pyc" -o -name "__pycache__" -o -name ".env"
# Sonuç: Hiçbir şey bulunmamalı

# 2. Port kontrolü
lsof -i :5000
ss -tlnp | grep 5000
# Sonuç: Boş çıktı

# 3. Süreç kontrolü
ps aux | grep brute-force-defender
pgrep -f "app.py"
# Sonuç: Sadece grep komutu kendisi

# 4. Docker kontrolü
docker ps -a | grep bfd
docker images | grep brute-force
# Sonuç: Boş çıktı

# 5. pip cache
pip cache dir && ls $(pip cache dir)
# Sonuç: İlgili paket yok
```

### 2.3 Manuel Kontrol Gerektiren Kalıntılar

- Shell history (`~/.bash_history`, `~/.zsh_history`)
- Sistem logları (`/var/log/`)
- Tarayıcı geçmişi (`localhost:5000` kayıtları)
- DNS cache

**TAVSİYE:** Projeyi sanal makine (VM) içinde çalıştırıp, işlem bitince VM'i silmek en güvenli yöntemdir.

---

## Adım 3: İş Akışları ve CI/CD Pipeline Analizi

### 3.1 Pipeline Yapısı (`.github/workflows/ci.yml`)

Pipeline 5 job'dan oluşur ve belirli bir bağımlılık sırasına göre çalışır:

```
[push/PR tetiklenir]
        │
        ▼
    ┌──────┐
    │ lint │  (Kod kalite kontrolü - flake8)
    └──┬───┘
       │
       ├───────────────┐
       ▼               ▼
  ┌────────┐     ┌──────────┐
  │  test  │     │ security │
  │(matrix)│     │ (bandit) │
  └────┬───┘     └────┬─────┘
       │              │
       ▼              │
  ┌────────┐          │
  │ docker │          │
  └────┬───┘          │
       │              │
       ▼              ▼
    ┌──────────────────┐
    │     deploy       │
    │ (sadece main)    │
    └──────────────────┘
```

### 3.2 Her Job'un Detaylı Analizi

**Job 1 - Lint:**
- `flake8` ile Python kod kalitesi kontrolü
- Söz dizimi hataları (E9, F63, F7, F82) → Kritik
- Stil uyarıları → Bilgilendirme (başarısız yapmaz)

**Job 2 - Test (Matrix):**
- 5 Python sürümünde paralel test: 3.8, 3.9, 3.10, 3.11, 3.12
- `pytest` ile birim testleri + coverage raporu
- `fail-fast: false` → Bir sürüm başarısız olursa diğerleri devam eder
- Coverage raporu artifact olarak kaydedilir

**Job 3 - Security:**
- `bandit`: Python güvenlik açıklarını tarar (SQL injection, XSS, hardcoded password vb.)
- `safety`: Bilinen güvenlik açığı olan paketleri kontrol eder
- Raporlar artifact olarak kaydedilir

**Job 4 - Docker:**
- Docker imajı build edilir
- Konteyner içinde testler çalıştırılır
- Demo çalıştırılır
- İmaj boyutu kontrol edilir (500MB sınırı)

**Job 5 - Deploy:**
- Sadece `main` branch'ine push'ta çalışır
- Tüm önceki job'lar başarılı olmalı
- Deploy simülasyonu (gerçek deploy senaryosunda Docker Hub, K8s vb.)

### 3.3 Webhook Nedir?

**Webhook**, bir sunucunun belirli bir olay gerçekleştiğinde başka bir sunucuya otomatik HTTP isteği göndermesidir. CI/CD bağlamında:

1. Geliştirici GitHub'a kod push eder
2. GitHub, önceden tanımlanmış URL'ye HTTP POST isteği gönderir (webhook)
3. Bu istek, GitHub Actions runner'ına "yeni iş var" sinyali verir
4. Runner, `ci.yml` dosyasındaki pipeline'ı başlatır
5. Pipeline sonucu (başarılı/başarısız) GitHub'a geri bildirilir
6. PR'da yeşil tik (✓) veya kırmızı çarpı (✗) görünür

**Bu projede webhook kullanımı:**
- `on: push` → Push webhook'u tetiklenir
- `on: pull_request` → PR webhook'u tetiklenir
- `on: workflow_dispatch` → Manuel tetikleme (webhook değil, API çağrısı)

---

## Adım 4: Docker Mimarisi ve Konteyner Güvenliği

### 4.1 Docker İmajı Nedir?

Docker imajı, uygulamanın çalışması için gereken tüm bileşenleri (işletim sistemi, kütüphaneler, kod, konfigürasyon) içeren salt-okunur bir şablondur. Katmanlı dosya sistemi (UnionFS) kullanır.

### 4.2 Katman (Layer) Yapısı

Bu projenin Dockerfile'ı multi-stage build kullanır:

**Stage 1 - Builder (Geçici):**

| Katman | İçerik | Boyut |
|--------|--------|-------|
| 1 | python:3.10-slim-bookworm | ~150MB |
| 2 | gcc, libffi-dev (derleme araçları) | ~30MB |
| 3 | pip install (blake3, flask vb.) | ~80MB |

**Stage 2 - Production (Final):**

| Katman | İçerik | Boyut |
|--------|--------|-------|
| 1 | python:3.10-slim-bookworm | ~150MB |
| 2 | /opt/venv (builder'dan kopyalanan) | ~80MB |
| 3 | Proje kodu | ~50KB |
| 4 | Non-root kullanıcı + izinler | ~1KB |

Multi-stage build avantajı: gcc ve derleme araçları final imajda **YOKTUR** (~30MB tasarruf + güvenlik).

### 4.3 Konteyner Güvenlik Önlemleri

| Önlem | Açıklama |
|-------|----------|
| Non-root kullanıcı | `USER appuser` → Konteyner root olarak çalışmaz |
| `no-new-privileges` | Yetki yükseltme (privilege escalation) engeli |
| `read_only` (demo) | Dosya sistemi salt-okunur |
| `tmpfs /tmp` | Geçici dosyalar RAM'de (disk erişimi yok) |
| `mem_limit` | 512MB bellek sınırı (DoS koruması) |
| `pids_limit` (compose) | Süreç sayısı sınırı (fork bomb koruması) |
| HEALTHCHECK | Konteyner sağlık durumu izlenir |
| `.dockerignore` | `.env`, credentials imaja girmez |

### 4.4 Konteyner Nerelere Erişebilir?

```
Host Sistemi
├── Port 5000 (mapped) → Konteyner:5000
├── Volume: bfd-results → /app/results (yazma)
├── Volume: bfd-logs → /app/logs (yazma)
└── Network: bfd-network (izole bridge network)
    └── Konteyner sadece aynı ağdaki diğer konteynerlere erişebilir
```

### 4.5 Docker vs VM vs Kubernetes Karşılaştırması

| Özellik | Docker | VM | Kubernetes |
|---------|--------|----|------------|
| İzolasyon | Süreç seviyesi (namespace) | Donanım seviyesi (hypervisor) | Pod/namespace seviyesi |
| Başlatma | Saniyeler | Dakikalar | Saniyeler (pod) |
| Kaynak | Düşük (kernel paylaşımı) | Yüksek (tam OS) | Orta (orchestration overhead) |
| Güvenlik | Orta (kernel paylaşımı riski) | Yüksek (tam izolasyon) | Yüksek (RBAC, NetworkPolicy) |
| Ölçekleme | Manuel | Manuel | Otomatik (HPA) |
| Orchestration | docker-compose | Yok | Yerleşik |

---

## Adım 5: Kaynak Kod ve Akış Analizi (Threat Modeling)

### 5.1 Entrypoint (Başlangıç Noktası)

Uygulamanın iki entrypoint'i vardır:

**1. CLI Entrypoint: `main.py`**
```
main.py → argparse → demo1..5 veya interactive mode
   └── src/hasher.py (BLAKE3 hash işlemleri)
   └── src/database.py (kullanıcı veritabanı)
   └── src/attacker.py (saldırı simülasyonu)
   └── src/benchmark.py (performans ölçümü)
   └── src/visualizer.py (grafik oluşturma)
```

**2. Web API Entrypoint: `app.py`**
```
app.py → Flask app oluştur → route'ları kaydet → dinlemeye başla
   └── /api/register → Kullanıcı kaydı (salt'lı hash)
   └── /api/login → Şifre doğrulama + JWT token üretimi
   └── /api/profile → [JWT KORUMALI] Profil bilgisi
   └── /api/hash → [JWT KORUMALI] Hash servisi
   └── /api/demo/attack → [JWT KORUMALI] Saldırı simülasyonu
   └── /health → Sağlık kontrolü
```

### 5.2 Kimlik Doğrulama (Authentication) Mekanizması

Bu proje **JWT (JSON Web Token)** kullanır.

**JWT Token Yapısı:**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.    ← Header (Base64)
eyJ1c2VyX2lkIjoiYWxpIiwiZXhwIjoxMjM0fQ.  ← Payload (Base64)
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c  ← Signature (HMAC-SHA256)
```

**Doğrulama Akışı:**
1. Kullanıcı `POST /api/login` ile username + password gönderir
2. Sunucu salt'lı BLAKE3 hash ile şifreyi doğrular
3. Başarılıysa JWT token oluşturulur (HMAC-SHA256 ile imzalanır)
4. Kullanıcı sonraki isteklerde `Authorization: Bearer <token>` header'ı ekler
5. Sunucu her istekte:
   - Token'ı 3 parçaya ayırır
   - İmzayı doğrular (manipülasyon tespiti)
   - Süre kontrolü yapar (expired mı?)
   - `hmac.compare_digest()` ile timing-safe karşılaştırma

### 5.3 Threat Modeling (Tehdit Modelleme)

**Saldırı Vektörleri ve Korunma Yöntemleri:**

| Saldırı | Risk | Korunma | Durum |
|---------|------|---------|-------|
| Brute-force login | YÜKSEK | Rate limiting (5 deneme → 15dk kilit) | ✅ |
| Credential stuffing | YÜKSEK | Account lockout + salt'lı hash | ✅ |
| Rainbow table | YÜKSEK | Salt'lı BLAKE3 hash | ✅ |
| JWT token çalma | ORTA | HTTPS zorunlu + kısa ömür (24h) | ⚠️ HTTPS henüz yok |
| JWT secret leak | YÜKSEK | `.env` dosyasında, `.gitignore`'da | ✅ |
| Timing attack | ORTA | `hmac.compare_digest()` kullanılır | ✅ |
| Username enumeration | ORTA | Genel hata mesajı ("Geçersiz kullanıcı adı veya şifre") | ✅ |
| SQL Injection | DÜŞÜK | SQL kullanılmıyor (JSON veritabanı) | ✅ |
| XSS | DÜŞÜK | API-only, HTML render yok | ✅ |
| DoS | ORTA | Docker kaynak limitleri (512MB, 1 CPU) | ✅ |
| Privilege escalation | DÜŞÜK | Docker non-root + no-new-privileges | ✅ |

### 5.4 Hacker Perspektifinden Analiz

Bir saldırgan bu kaynak kodu incelediğinde şu verileri hedefleyebilir:

1. **JWT Secret Key:** `.env` dosyasındaki `JWT_SECRET_KEY`. Ele geçirilirse tüm token'lar taklit edilebilir.
2. **Kullanıcı veritabanı:** `data/users.json` dosyasındaki hash + salt değerleri.
3. **Şifre hash'leri:** Salt'sız hash kullanılsaydı rainbow table ile kırılabilirdi. Salt sayesinde her kullanıcı için ayrı saldırı gerekir.

**Auth mekanizmasına dışarıdan saldırı senaryosu:**

```
1. Hedef: POST /api/login endpoint'i
2. Saldırı: Sözlük saldırısı (yaygın şifreleri dene)
3. Engel: Rate limiting (5 denemede kilit)
4. Bypass denemesi: Farklı IP'lerden saldırı (IP rotation)
5. Engel: Her IP ayrı sayılır ama proxy/VPN maliyetli
6. Sonuç: Salt'lı hash + rate limiting kombinasyonu etkili koruma sağlar
```

---

## Sonuç

Bu proje, BLAKE3 hash algoritması ve tuzlama mekanizmasının brute-force saldırılara karşı etkisini hem teorik hem pratik olarak gösterir. 5 analiz aşaması kapsamında kurulumdan güvenlik analizine kadar tüm yönler incelenmiştir.

**Temel Bulgular:**
- Salt'sız hash kullanmak, rainbow table saldırılarına karşı savunmasız bırakır
- Salt'lı hash, aynı şifre kullanan kullanıcıları bile korur
- JWT authentication ile API güvenliği sağlanabilir
- Docker konteynerleştirme ile izolasyon ve güvenlik artırılabilir
- CI/CD pipeline ile sürekli güvenlik taraması otomatikleştirilebilir
