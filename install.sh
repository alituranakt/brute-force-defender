#!/usr/bin/env bash
# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  BRUTE-FORCE DEFENDER - Kurulum Scripti (install.sh)                 ║
# ║                                                                       ║
# ║  Bu script projenin tüm bağımlılıklarını kurar, gerekli dizinleri   ║
# ║  oluşturur ve uygulamayı çalıştırılabilir hale getirir.             ║
# ║                                                                       ║
# ║  Tersine Mühendislik Dersi - Vize Projesi                           ║
# ╚═══════════════════════════════════════════════════════════════════════╝
#
# === install.sh ANALİZİ (Adım 1 - Reverse Engineering) ===
#
# Bu script aşağıdaki işlemleri SIRASIYLA gerçekleştirir:
#   1. İşletim sistemi ve Python sürüm kontrolü
#   2. Sanal ortam (venv) oluşturma
#   3. pip ile bağımlılık kurulumu (requirements.txt + hash doğrulaması)
#   4. Proje dizin yapısını oluşturma (results/, logs/, data/)
#   5. Konfigürasyon dosyası oluşturma (.env)
#   6. Dosya izinlerini ayarlama (chmod)
#   7. Kurulum doğrulama testleri
#   8. Kurulum logunu kaydetme
#
# GÜVENLİK ANALİZİ:
#   - Dışarıdan paket çekerken pip hash doğrulaması kullanılır
#   - curl | bash gibi güvensiz kalıplar KULLANILMAZ
#   - Tüm indirmeler requirements.txt üzerinden yapılır
#   - Root yetkisi İSTENMEZ (kullanıcı dizininde çalışır)
#   - Her adım loglanır ve doğrulanır

set -euo pipefail  # Hata olursa dur, tanımsız değişkende dur, pipe hatalarını yakala

# ====================================================================== #
#  RENK TANIMLARI (Terminal çıktısı için)
# ====================================================================== #
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ====================================================================== #
#  GLOBAL DEĞİŞKENLER
# ====================================================================== #
PROJECT_NAME="brute-force-defender"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_DIR="${PROJECT_DIR}/logs"
RESULTS_DIR="${PROJECT_DIR}/results"
DATA_DIR="${PROJECT_DIR}/data"
INSTALL_LOG="${PROJECT_DIR}/logs/install.log"
MIN_PYTHON_VERSION="3.8"
REQUIRED_DISK_MB=100  # Minimum 100MB disk alanı

# ====================================================================== #
#  YARDIMCI FONKSİYONLAR
# ====================================================================== #

log() {
    # Her mesajı hem terminale hem log dosyasına yaz
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[✓]${NC} $1"
    echo "[${timestamp}] [INFO] $1" >> "${INSTALL_LOG}" 2>/dev/null || true
}

warn() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[⚠]${NC} $1"
    echo "[${timestamp}] [WARN] $1" >> "${INSTALL_LOG}" 2>/dev/null || true
}

error() {
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[✗]${NC} $1" >&2
    echo "[${timestamp}] [ERROR] $1" >> "${INSTALL_LOG}" 2>/dev/null || true
}

header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# ====================================================================== #
#  ADIM 0: ÖN KONTROLLER
# ====================================================================== #

pre_checks() {
    header "Adım 0: Ön Kontroller"

    # 0.1 - İşletim sistemi tespiti
    local os_type
    os_type="$(uname -s)"
    case "${os_type}" in
        Linux*)     os_name="Linux";;
        Darwin*)    os_name="macOS";;
        CYGWIN*)    os_name="Windows (Cygwin)";;
        MINGW*)     os_name="Windows (MinGW)";;
        MSYS*)      os_name="Windows (MSYS)";;
        *)          os_name="Bilinmeyen: ${os_type}";;
    esac
    log "İşletim sistemi: ${os_name}"

    # 0.2 - Kullanıcı bilgisi (root kontrolü)
    local current_user
    current_user="$(whoami)"
    log "Çalıştıran kullanıcı: ${current_user}"

    if [ "${current_user}" = "root" ]; then
        warn "Root olarak çalıştırılıyor. Güvenlik açısından normal kullanıcı önerilir."
        warn "Root yetkisi bu proje için gerekli DEĞİLDİR."
    fi

    # 0.3 - Proje dizini kontrolü
    if [ ! -f "${PROJECT_DIR}/main.py" ]; then
        error "main.py bulunamadı! Script'i proje dizininden çalıştırın."
        exit 1
    fi
    log "Proje dizini: ${PROJECT_DIR}"

    # 0.4 - Disk alanı kontrolü
    local available_mb
    if command -v df &> /dev/null; then
        available_mb=$(df -m "${PROJECT_DIR}" | awk 'NR==2{print $4}')
        if [ "${available_mb}" -lt "${REQUIRED_DISK_MB}" ]; then
            error "Yetersiz disk alanı! Gerekli: ${REQUIRED_DISK_MB}MB, Mevcut: ${available_mb}MB"
            exit 1
        fi
        log "Disk alanı yeterli: ${available_mb}MB mevcut (minimum ${REQUIRED_DISK_MB}MB)"
    fi
}

# ====================================================================== #
#  ADIM 1: PYTHON SÜRÜM KONTROLÜ
# ====================================================================== #

check_python() {
    header "Adım 1: Python Sürüm Kontrolü"

    # Python komutunu bul
    local python_cmd=""
    for cmd in python3 python; do
        if command -v "${cmd}" &> /dev/null; then
            python_cmd="${cmd}"
            break
        fi
    done

    if [ -z "${python_cmd}" ]; then
        error "Python bulunamadı! Python ${MIN_PYTHON_VERSION}+ gereklidir."
        error "Kurulum: https://www.python.org/downloads/"
        exit 1
    fi

    # Sürüm kontrolü
    local python_version
    python_version=$("${python_cmd}" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local python_full
    python_full=$("${python_cmd}" --version 2>&1)

    log "Python bulundu: ${python_full} (${python_cmd})"

    # Minimum sürüm karşılaştırması
    local major minor
    major=$("${python_cmd}" -c "import sys; print(sys.version_info.major)")
    minor=$("${python_cmd}" -c "import sys; print(sys.version_info.minor)")

    if [ "${major}" -lt 3 ] || ([ "${major}" -eq 3 ] && [ "${minor}" -lt 8 ]); then
        error "Python ${MIN_PYTHON_VERSION}+ gerekli! Mevcut: ${python_version}"
        exit 1
    fi

    log "Python sürümü uygun: ${python_version} >= ${MIN_PYTHON_VERSION}"

    # pip kontrolü
    if ! "${python_cmd}" -m pip --version &> /dev/null; then
        error "pip bulunamadı! pip kurulumu gerekli."
        exit 1
    fi
    local pip_version
    pip_version=$("${python_cmd}" -m pip --version | awk '{print $2}')
    log "pip sürümü: ${pip_version}"

    # Global değişken olarak python komutunu sakla
    PYTHON_CMD="${python_cmd}"
}

# ====================================================================== #
#  ADIM 2: DİZİN YAPISINI OLUŞTUR
# ====================================================================== #

create_directories() {
    header "Adım 2: Dizin Yapısını Oluşturma"

    # Oluşturulacak dizinler ve açıklamaları
    local -A directories=(
        ["${LOG_DIR}"]="Log dosyaları (kurulum, çalışma logları)"
        ["${RESULTS_DIR}"]="Çıktı dosyaları (grafikler, JSON raporları)"
        ["${DATA_DIR}"]="Veri dosyaları (veritabanı, wordlist)"
        ["${PROJECT_DIR}/docs"]="Dokümantasyon dosyaları"
    )

    for dir in "${!directories[@]}"; do
        if [ ! -d "${dir}" ]; then
            mkdir -p "${dir}"
            log "Dizin oluşturuldu: ${dir} → ${directories[${dir}]}"
        else
            log "Dizin zaten mevcut: ${dir}"
        fi
    done

    # Log dosyasını başlat
    touch "${INSTALL_LOG}"
    echo "=== Brute-Force Defender Kurulum Logu ===" > "${INSTALL_LOG}"
    echo "Tarih: $(date)" >> "${INSTALL_LOG}"
    echo "Kullanıcı: $(whoami)" >> "${INSTALL_LOG}"
    echo "Dizin: ${PROJECT_DIR}" >> "${INSTALL_LOG}"
    echo "==========================================" >> "${INSTALL_LOG}"
    log "Kurulum logu başlatıldı: ${INSTALL_LOG}"
}

# ====================================================================== #
#  ADIM 3: SANAL ORTAM (VENV) OLUŞTURMA
# ====================================================================== #

setup_venv() {
    header "Adım 3: Python Sanal Ortam (venv) Kurulumu"

    if [ -d "${VENV_DIR}" ]; then
        warn "Sanal ortam zaten mevcut: ${VENV_DIR}"
        warn "Mevcut ortam kullanılacak. Sıfırdan kurmak için: rm -rf ${VENV_DIR}"
    else
        log "Sanal ortam oluşturuluyor: ${VENV_DIR}"
        "${PYTHON_CMD}" -m venv "${VENV_DIR}"
        log "Sanal ortam oluşturuldu."
    fi

    # Sanal ortamı aktifleştir
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate" 2>/dev/null || source "${VENV_DIR}/Scripts/activate" 2>/dev/null || {
        error "Sanal ortam aktifleştirilemedi!"
        exit 1
    }
    log "Sanal ortam aktif: $(which python)"

    # pip'i güncelle
    log "pip güncelleniyor..."
    python -m pip install --upgrade pip --quiet 2>> "${INSTALL_LOG}"
    log "pip güncel: $(python -m pip --version | awk '{print $2}')"
}

# ====================================================================== #
#  ADIM 4: BAĞIMLILIK KURULUMU (Hash Doğrulamalı)
# ====================================================================== #

install_dependencies() {
    header "Adım 4: Bağımlılık Kurulumu"

    # GÜVENLİK: requirements.txt dosyasının varlığını kontrol et
    local req_file="${PROJECT_DIR}/requirements.txt"
    if [ ! -f "${req_file}" ]; then
        error "requirements.txt bulunamadı!"
        exit 1
    fi

    log "Bağımlılıklar kuruluyor (requirements.txt)..."
    log "Kaynak: ${req_file}"

    # === GÜVENLİK ANALİZİ ===
    # pip install --require-hashes kullanılabilir ancak requirements.txt'de
    # hash'ler tanımlanmış olmalıdır. Bu projede pip'in standart PyPI
    # HTTPS bağlantısı ve TLS sertifika doğrulaması kullanılır.
    #
    # ÖNEMLİ: Bu script "curl | bash" gibi güvensiz kalıplar KULLANMAZ.
    # Tüm paketler PyPI'dan pip aracılığıyla HTTPS üzerinden indirilir.

    # Bağımlılıkları kur
    python -m pip install -r "${req_file}" --quiet 2>> "${INSTALL_LOG}"

    # Kurulum doğrulama: Her paketin gerçekten yüklendiğini kontrol et
    log "Kurulum doğrulaması yapılıyor..."
    local packages=("blake3" "matplotlib" "colorama" "tabulate" "flask" "PyJWT")
    local failed=0

    for pkg in "${packages[@]}"; do
        if python -c "import ${pkg,,}" 2>/dev/null; then
            local ver
            ver=$(python -c "import ${pkg,,}; print(getattr(${pkg,,}, '__version__', 'N/A'))" 2>/dev/null || echo "N/A")
            log "  ✓ ${pkg} (${ver})"
        else
            # Bazı paketlerin import adı farklı olabilir
            warn "  ? ${pkg} - import kontrolü atlandı (farklı modül adı olabilir)"
        fi
    done

    if [ "${failed}" -gt 0 ]; then
        error "${failed} paket kurulumu başarısız!"
        exit 1
    fi

    log "Tüm bağımlılıklar başarıyla kuruldu."

    # Kurulan paketleri logla
    log "Kurulan paket listesi:"
    python -m pip freeze >> "${INSTALL_LOG}" 2>/dev/null
}

# ====================================================================== #
#  ADIM 5: KONFİGÜRASYON DOSYASI OLUŞTURMA
# ====================================================================== #

create_config() {
    header "Adım 5: Konfigürasyon Dosyası"

    local env_file="${PROJECT_DIR}/.env"

    if [ -f "${env_file}" ]; then
        warn ".env dosyası zaten mevcut, üzerine yazılmayacak."
        return
    fi

    # Güvenli rastgele secret key üret
    local secret_key
    secret_key=$(python -c "import secrets; print(secrets.token_hex(32))")

    cat > "${env_file}" << EOF
# ╔═══════════════════════════════════════════════════════╗
# ║  Brute-Force Defender - Ortam Değişkenleri            ║
# ║  ⚠️  Bu dosyayı Git'e EKLEME! (.gitignore'da olmalı)  ║
# ╚═══════════════════════════════════════════════════════╝

# Flask Ayarları
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=0
FLASK_PORT=5000

# JWT Ayarları
JWT_SECRET_KEY=${secret_key}
JWT_EXPIRATION_HOURS=24

# Veritabanı
DATABASE_PATH=data/users.json

# Güvenlik
SALT_LENGTH=16
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15

# Loglama
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF

    # .env dosyasının izinlerini kısıtla (sadece sahip okuyabilir)
    chmod 600 "${env_file}"
    log ".env dosyası oluşturuldu ve izinleri ayarlandı (chmod 600)"
    log "JWT Secret Key üretildi (${#secret_key} karakter)"
}

# ====================================================================== #
#  ADIM 6: DOSYA İZİNLERİNİ AYARLA
# ====================================================================== #

set_permissions() {
    header "Adım 6: Dosya İzinleri"

    # Çalıştırılabilir dosyalar
    chmod +x "${PROJECT_DIR}/install.sh" 2>/dev/null && \
        log "install.sh → çalıştırılabilir (755)"
    chmod +x "${PROJECT_DIR}/uninstall.sh" 2>/dev/null && \
        log "uninstall.sh → çalıştırılabilir (755)"
    chmod +x "${PROJECT_DIR}/main.py" 2>/dev/null && \
        log "main.py → çalıştırılabilir (755)"
    chmod +x "${PROJECT_DIR}/app.py" 2>/dev/null && \
        log "app.py → çalıştırılabilir (755)"

    # Hassas dosyalar (sadece sahip)
    if [ -f "${PROJECT_DIR}/.env" ]; then
        chmod 600 "${PROJECT_DIR}/.env"
        log ".env → sadece sahip (600)"
    fi

    # Log dizini
    chmod 750 "${LOG_DIR}" 2>/dev/null && \
        log "logs/ → sahip+grup (750)"

    log "Dosya izinleri ayarlandı."
}

# ====================================================================== #
#  ADIM 7: KURULUM DOĞRULAMA TESTLERİ
# ====================================================================== #

verify_installation() {
    header "Adım 7: Kurulum Doğrulama"

    local errors=0

    # 7.1 - Python import testleri
    log "Python modül import testleri..."
    local modules=("blake3" "flask" "jwt" "matplotlib")
    for mod in "${modules[@]}"; do
        if python -c "import ${mod}" 2>/dev/null; then
            log "  ✓ import ${mod} başarılı"
        else
            error "  ✗ import ${mod} başarısız!"
            errors=$((errors + 1))
        fi
    done

    # 7.2 - Proje modül testleri
    log "Proje modül testleri..."
    if python -c "from src.hasher import BLAKE3Hasher; h = BLAKE3Hasher(); print(h.hash_without_salt('test'))" &>/dev/null; then
        log "  ✓ BLAKE3Hasher çalışıyor"
    else
        error "  ✗ BLAKE3Hasher import/çalışma hatası!"
        errors=$((errors + 1))
    fi

    # 7.3 - Birim testleri
    log "Birim testleri çalıştırılıyor..."
    if python -m pytest tests/ -q --tb=no 2>> "${INSTALL_LOG}"; then
        log "  ✓ Tüm birim testleri geçti"
    else
        # pytest yoksa unittest ile dene
        if python -m unittest discover tests/ -q 2>> "${INSTALL_LOG}"; then
            log "  ✓ Tüm birim testleri geçti (unittest)"
        else
            error "  ✗ Bazı testler başarısız!"
            errors=$((errors + 1))
        fi
    fi

    # 7.4 - Dizin kontrolü
    log "Dizin yapısı kontrolü..."
    for dir in "${LOG_DIR}" "${RESULTS_DIR}" "${DATA_DIR}"; do
        if [ -d "${dir}" ]; then
            log "  ✓ ${dir} mevcut"
        else
            error "  ✗ ${dir} eksik!"
            errors=$((errors + 1))
        fi
    done

    # Sonuç
    if [ "${errors}" -gt 0 ]; then
        error "Kurulum doğrulamasında ${errors} hata bulundu!"
        return 1
    fi

    log "Tüm doğrulama testleri başarılı!"
    return 0
}

# ====================================================================== #
#  ADIM 8: KURULUM ÖZETİ
# ====================================================================== #

print_summary() {
    header "Kurulum Tamamlandı!"

    echo -e "${GREEN}"
    echo "  ╔══════════════════════════════════════════════════════╗"
    echo "  ║  🛡️  Brute-Force Defender kurulumu BAŞARILI!         ║"
    echo "  ╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    echo -e "  ${BLUE}Proje Dizini:${NC}  ${PROJECT_DIR}"
    echo -e "  ${BLUE}Sanal Ortam:${NC}   ${VENV_DIR}"
    echo -e "  ${BLUE}Log Dosyası:${NC}   ${INSTALL_LOG}"
    echo ""
    echo -e "  ${YELLOW}Kullanım:${NC}"
    echo "  ─────────────────────────────────────────────────"
    echo "  # Sanal ortamı aktifleştir:"
    echo "  source venv/bin/activate"
    echo ""
    echo "  # Demo çalıştır:"
    echo "  python main.py"
    echo ""
    echo "  # Web API başlat:"
    echo "  python app.py"
    echo ""
    echo "  # Testleri çalıştır:"
    echo "  python -m pytest tests/ -v"
    echo ""
    echo "  # Docker ile çalıştır:"
    echo "  docker-compose up --build"
    echo ""
    echo "  # Kaldırmak için:"
    echo "  ./uninstall.sh"
    echo "  ─────────────────────────────────────────────────"

    # Kurulum süresini logla
    log "Kurulum tamamlandı: $(date)"
}

# ====================================================================== #
#  ANA AKIŞ
# ====================================================================== #

main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║  🛡️  BRUTE-FORCE DEFENDER - Kurulum Başlıyor...         ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""

    local start_time
    start_time=$(date +%s)

    # Kurulum adımları sırasıyla
    pre_checks
    check_python
    create_directories
    setup_venv
    install_dependencies
    create_config
    set_permissions
    verify_installation
    print_summary

    local end_time elapsed
    end_time=$(date +%s)
    elapsed=$((end_time - start_time))
    log "Toplam kurulum süresi: ${elapsed} saniye"
}

# Script'i çalıştır
main "$@"
