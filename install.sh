#!/usr/bin/env bash

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/venv"
LOG_DIR="${PROJECT_DIR}/logs"
RESULTS_DIR="${PROJECT_DIR}/results"
DATA_DIR="${PROJECT_DIR}/data"
INSTALL_LOG="${LOG_DIR}/install.log"
ENV_FILE="${PROJECT_DIR}/.env"
ENV_EXAMPLE_FILE="${PROJECT_DIR}/.env.example"
MIN_PYTHON_VERSION="3.8"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${GREEN}[OK]${NC} ${message}"
    echo "[${timestamp}] [INFO] ${message}" >> "${INSTALL_LOG}" 2>/dev/null || true
}

warn() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${YELLOW}[WARN]${NC} ${message}"
    echo "[${timestamp}] [WARN] ${message}" >> "${INSTALL_LOG}" 2>/dev/null || true
}

fail() {
    local message="$1"
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${RED}[ERR]${NC} ${message}" >&2
    echo "[${timestamp}] [ERROR] ${message}" >> "${INSTALL_LOG}" 2>/dev/null || true
    exit 1
}

header() {
    echo
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}${1}${NC}"
    echo -e "${CYAN}============================================================${NC}"
}

find_python() {
    for cmd in python3 python; do
        if command -v "${cmd}" >/dev/null 2>&1; then
            PYTHON_CMD="${cmd}"
            return
        fi
    done
    fail "Python bulunamadi. Python ${MIN_PYTHON_VERSION}+ gereklidir."
}

check_python_version() {
    local major minor
    major=$("${PYTHON_CMD}" -c "import sys; print(sys.version_info.major)")
    minor=$("${PYTHON_CMD}" -c "import sys; print(sys.version_info.minor)")

    if [ "${major}" -lt 3 ] || ([ "${major}" -eq 3 ] && [ "${minor}" -lt 8 ]); then
        fail "Python ${MIN_PYTHON_VERSION}+ gerekli."
    fi
}

prepare_directories() {
    mkdir -p "${LOG_DIR}" "${RESULTS_DIR}" "${DATA_DIR}"
    : > "${INSTALL_LOG}"
    log "Kurulum logu hazirlandi: ${INSTALL_LOG}"
}

setup_venv() {
    if [ ! -d "${VENV_DIR}" ]; then
        log "Sanal ortam olusturuluyor."
        "${PYTHON_CMD}" -m venv "${VENV_DIR}"
    else
        warn "Sanal ortam zaten mevcut, tekrar kullanilacak."
    fi

    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate" 2>/dev/null || source "${VENV_DIR}/Scripts/activate" 2>/dev/null || fail "Sanal ortam aktif edilemedi."

    python -m pip install --upgrade pip >> "${INSTALL_LOG}" 2>&1
    log "pip guncellendi."
}

install_dependencies() {
    [ -f "${PROJECT_DIR}/requirements.txt" ] || fail "requirements.txt bulunamadi."
    python -m pip install -r "${PROJECT_DIR}/requirements.txt" >> "${INSTALL_LOG}" 2>&1
    log "Python bagimliliklari kuruldu."
}

create_env_file() {
    if [ -f "${ENV_FILE}" ]; then
        warn ".env dosyasi zaten mevcut, degistirilmeyecek."
        return
    fi

    if [ -f "${ENV_EXAMPLE_FILE}" ]; then
        cp "${ENV_EXAMPLE_FILE}" "${ENV_FILE}"
        log ".env.example kopyalanarak .env olusturuldu."
    else
        cat > "${ENV_FILE}" <<'EOF'
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=0
FLASK_PORT=5000
JWT_SECRET_KEY=change-this-secret-in-production
JWT_EXPIRATION_HOURS=24
DATABASE_PATH=data/users.json
SALT_LENGTH=16
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=15
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
        log ".env dosyasi varsayilan degerlerle olusturuldu."
    fi

    if grep -q "^JWT_SECRET_KEY=change-this-secret-in-production$" "${ENV_FILE}"; then
        local secret_key
        secret_key=$("${PYTHON_CMD}" -c "import secrets; print(secrets.token_hex(32))")
        "${PYTHON_CMD}" -c "from pathlib import Path; p=Path(r'${ENV_FILE}'); p.write_text(p.read_text(encoding='utf-8').replace('JWT_SECRET_KEY=change-this-secret-in-production', 'JWT_SECRET_KEY=${secret_key}'), encoding='utf-8')"
        log "JWT secret uretildi ve .env icine yazildi."
    fi
}

set_permissions() {
    chmod +x "${PROJECT_DIR}/install.sh" "${PROJECT_DIR}/uninstall.sh" 2>/dev/null || true
    chmod 600 "${ENV_FILE}" 2>/dev/null || true
    log "Temel dosya izinleri ayarlandi."
}

verify_installation() {
    local modules=("blake3" "flask" "dotenv" "matplotlib")

    for module in "${modules[@]}"; do
        python -c "import ${module}" >> "${INSTALL_LOG}" 2>&1 || fail "Modul dogrulamasi basarisiz: ${module}"
    done

    python -m pytest tests/ -q >> "${INSTALL_LOG}" 2>&1 || warn "pytest calismadi. Ayrintilar install logunda."
    log "Kurulum dogrulamasi tamamlandi."
}

print_summary() {
    header "Kurulum tamamlandi"
    echo "Proje dizini : ${PROJECT_DIR}"
    echo "Sanal ortam  : ${VENV_DIR}"
    echo "Log dosyasi  : ${INSTALL_LOG}"
    echo
    echo "Kullanim:"
    echo "  source venv/bin/activate"
    echo "  python main.py"
    echo "  python app.py"
    echo "  python -m pytest tests/ -v"
    echo "  docker compose up --build"
}

main() {
    header "Brute-Force Defender kurulumu basliyor"
    find_python
    check_python_version
    prepare_directories
    setup_venv
    install_dependencies
    create_env_file
    set_permissions
    verify_installation
    print_summary
}

main "$@"
