# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  BRUTE-FORCE DEFENDER - Dockerfile                                    ║
# ║                                                                       ║
# ║  Adım 4 Analizi: Docker Mimarisi ve Konteyner Güvenliği             ║
# ║  Tersine Mühendislik Dersi - Vize Projesi                           ║
# ╚═══════════════════════════════════════════════════════════════════════╝
#
# === DOCKER MİMARİSİ ANALİZİ ===
#
# Docker İmajı Nedir?
#   Bir Docker imajı, uygulamanın çalışması için gereken TÜM bileşenleri
#   (OS, kütüphaneler, kod, config) içeren salt-okunur bir şablondur.
#   Katmanlı dosya sistemi (UnionFS) kullanır.
#
# KATMAN (Layer) YAPISI (Bu Dockerfile için):
#   Katman 1: python:3.10-slim-bookworm (Base OS + Python)  ~150MB
#   Katman 2: Sistem paketleri (gcc, libffi)                ~30MB
#   Katman 3: requirements.txt COPY                         ~1KB
#   Katman 4: pip install (Python paketleri)                ~80MB
#   Katman 5: Proje kodu COPY                               ~50KB
#   Katman 6: Non-root kullanıcı + izinler                  ~1KB
#
# GÜVENLİK ÖNLEMLERİ:
#   1. Multi-stage build → Gereksiz build araçları final imajda YOK
#   2. Non-root kullanıcı → Konteyner root olarak ÇALIŞMAZ
#   3. Minimal base image → slim variant (full Debian yerine)
#   4. .dockerignore → Hassas dosyalar imaja GİRMEZ
#   5. HEALTHCHECK → Konteyner sağlık durumu izlenir
#   6. Sabit sürüm tag'leri → "latest" yerine belirli sürüm

# ====================================================================== #
#  STAGE 1: BUILD (Derleme Aşaması)
# ====================================================================== #
# Bu aşama, derleme araçlarını kurar ve bağımlılıkları hazırlar.
# Final imaja TAŞINMAZ, sadece pip paketleri kopyalanır.

FROM python:3.10-slim-bookworm AS builder

# Derleme araçları (blake3 native extension için gerekli)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        && rm -rf /var/lib/apt/lists/*
    # AÇIKLAMA:
    #   gcc: C compiler (blake3 Python binding'i Rust→C extension kullanır)
    #   libffi-dev: Foreign Function Interface (ctypes için)
    #   rm -rf /var/lib/apt/lists/*: apt cache temizle (imaj boyutunu küçült)

# Sanal ortam oluştur (izolasyon)
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Önce requirements.txt'yi kopyala (Docker cache optimizasyonu)
# Eğer requirements.txt değişmezse, bu katman cache'den gelir
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# ====================================================================== #
#  STAGE 2: PRODUCTION (Çalışma Aşaması)
# ====================================================================== #
# Sadece gerekli dosyalar kopyalanır. Build araçları YOKTUR.

FROM python:3.10-slim-bookworm AS production

# Metadata (OCI standart etiketleri)
LABEL maintainer="Tersine Muhendislik Dersi"
LABEL description="BLAKE3 Salting Mekanizmasi Demonstrasyonu"
LABEL version="1.0.0"

# Ortam değişkenleri
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    APP_HOME=/app

# ====================================================================== #
#  GÜVENLİK: Non-root kullanıcı oluştur
# ====================================================================== #
# Konteyner ROOT olarak çalışMAMALI!
# Eğer uygulama ele geçirilirse, saldırgan root yetkilerine sahip olmaz.
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --create-home --shell /bin/bash appuser

# Uygulama dizinini oluştur
RUN mkdir -p ${APP_HOME}/results ${APP_HOME}/logs ${APP_HOME}/data && \
    chown -R appuser:appuser ${APP_HOME}

WORKDIR ${APP_HOME}

# Builder stage'den sadece sanal ortamı kopyala (build araçları YOK)
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Proje dosyalarını kopyala
COPY --chown=appuser:appuser src/ ${APP_HOME}/src/
COPY --chown=appuser:appuser tests/ ${APP_HOME}/tests/
COPY --chown=appuser:appuser main.py ${APP_HOME}/
COPY --chown=appuser:appuser app.py ${APP_HOME}/
COPY --chown=appuser:appuser requirements.txt ${APP_HOME}/

# ====================================================================== #
#  SAĞLIK KONTROLÜ (Healthcheck)
# ====================================================================== #
# Docker ve orchestrator'lar (K8s) bu endpoint'i kontrol eder
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Non-root kullanıcıya geç
USER appuser

# Port bilgisi (dokümantasyon amaçlı, güvenlik duvarını açmaz)
EXPOSE 5000

# ====================================================================== #
#  ENTRYPOINT ve CMD
# ====================================================================== #
# ENTRYPOINT: Değiştirilemez komut (konteyner her zaman python çalıştırır)
# CMD: Varsayılan argümanlar (docker run ile override edilebilir)
#
# Örnekler:
#   docker run brute-force-defender               → Flask API başlatır
#   docker run brute-force-defender python main.py → Demo çalıştırır
#   docker run brute-force-defender pytest tests/  → Testleri çalıştırır

ENTRYPOINT ["python"]
CMD ["app.py"]
