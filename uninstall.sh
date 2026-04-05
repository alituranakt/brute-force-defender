#!/usr/bin/env bash
# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  BRUTE-FORCE DEFENDER - Temiz Kaldırma Scripti (uninstall.sh)        ║
# ║                                                                       ║
# ║  Bu script, uygulamayı sistemden İZ BIRAKMADAN kaldırır.             ║
# ║  Forensics & Cleanup - Adım 2 Analizi                               ║
# ║                                                                       ║
# ║  Tersine Mühendislik Dersi - Vize Projesi                           ║
# ╚═══════════════════════════════════════════════════════════════════════╝
#
# === uninstall.sh ANALİZİ (Adım 2 - Forensics & Cleanup) ===
#
# Bu script aşağıdaki kalıntıları TEMİZLER:
#   1. Python sanal ortam (venv/) → pip cache dahil
#   2. Konfigürasyon dosyaları (.env, *.json)
#   3. Log dosyaları (logs/)
#   4. Çıktı dosyaları (results/)
#   5. Geçici dosyalar (__pycache__, .pyc, .egg-info)
#   6. Docker konteyner ve imajları
#   7. Arka plan servisleri (Flask, port dinleyen süreçler)
#   8. pip cache temizliği
#   9. Bash/shell history'den komut izlerini uyarır
#  10. Doğrulama: Hiçbir iz kalmadığını kontrol eder
#
# DOĞRULAMA YÖNTEMLERİ:
#   - Dosya sistemi taraması (find komutu)
#   - Port taraması (lsof/ss/netstat)
#   - Süreç kontrolü (ps)
#   - Docker konteyner kontrolü
#   - pip cache kontrolü

set -euo pipefail

# ====================================================================== #
#  RENK TANIMLARI
# ====================================================================== #
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# ====================================================================== #
#  GLOBAL DEĞİŞKENLER
# ====================================================================== #
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="brute-force-defender"
FLASK_PORT=5000

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }
error(){ echo -e "${RED}[✗]${NC} $1" >&2; }
header() {
    echo ""
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# ====================================================================== #
#  ONAY İSTE
# ====================================================================== #

confirm_uninstall() {
    header "Brute-Force Defender - Kaldırma İşlemi"

    echo -e "${RED}  ⚠️  DİKKAT: Bu işlem geri alınamaz!${NC}"
    echo ""
    echo "  Kaldırılacak öğeler:"
    echo "  ─────────────────────────────────────────"
    echo "  • Python sanal ortam (venv/)"
    echo "  • Konfigürasyon dosyaları (.env)"
    echo "  • Log dosyaları (logs/)"
    echo "  • Çıktı/sonuç dosyaları (results/)"
    echo "  • Veri dosyaları (data/)"
    echo "  • Docker konteyner ve imajları"
    echo "  • Arka plan süreçleri"
    echo "  • Python cache dosyaları"
    echo "  ─────────────────────────────────────────"
    echo ""

    read -rp "  Devam etmek istiyor musunuz? (evet/hayir): " answer
    case "${answer}" in
        [eE]vet|[eE]VET|[yY]es|[yY])
            log "Kaldırma işlemi başlatılıyor..."
            ;;
        *)
            echo "  İşlem iptal edildi."
            exit 0
            ;;
    esac
}

# ====================================================================== #
#  ADIM 1: ARKA PLAN SÜREÇLERİNİ DURDUR
# ====================================================================== #

stop_services() {
    header "Adım 1: Arka Plan Süreçlerini Durdurma"

    # Flask/Python süreçlerini kontrol et
    local pids
    pids=$(pgrep -f "python.*app.py" 2>/dev/null || true)

    if [ -n "${pids}" ]; then
        log "Flask süreci bulundu (PID: ${pids})"
        kill "${pids}" 2>/dev/null && log "Flask süreci durduruldu." || warn "Süreç zaten durmuş olabilir."
        sleep 1
    else
        log "Çalışan Flask süreci bulunamadı."
    fi

    # Port kontrolü
    if command -v lsof &> /dev/null; then
        local port_check
        port_check=$(lsof -i ":${FLASK_PORT}" 2>/dev/null | grep -v "^COMMAND" || true)
        if [ -n "${port_check}" ]; then
            warn "Port ${FLASK_PORT} hala kullanımda:"
            echo "  ${port_check}"
            local port_pid
            port_pid=$(echo "${port_check}" | awk '{print $2}' | head -1)
            kill "${port_pid}" 2>/dev/null && log "Port ${FLASK_PORT} serbest bırakıldı." || true
        else
            log "Port ${FLASK_PORT} serbest."
        fi
    elif command -v ss &> /dev/null; then
        local ss_check
        ss_check=$(ss -tlnp 2>/dev/null | grep ":${FLASK_PORT}" || true)
        if [ -n "${ss_check}" ]; then
            warn "Port ${FLASK_PORT} hala kullanımda."
        else
            log "Port ${FLASK_PORT} serbest."
        fi
    fi

    # Genel Python süreç kontrolü (proje ile ilgili)
    local project_procs
    project_procs=$(pgrep -f "${PROJECT_NAME}" 2>/dev/null || true)
    if [ -n "${project_procs}" ]; then
        warn "Proje ile ilişkili süreçler bulundu: ${project_procs}"
        kill "${project_procs}" 2>/dev/null || true
        log "Proje süreçleri durduruldu."
    fi
}

# ====================================================================== #
#  ADIM 2: DOCKER TEMİZLİĞİ
# ====================================================================== #

cleanup_docker() {
    header "Adım 2: Docker Temizliği"

    if ! command -v docker &> /dev/null; then
        log "Docker kurulu değil, atlanıyor."
        return
    fi

    # Konteynerleri durdur ve kaldır
    local containers
    containers=$(docker ps -a --filter "name=${PROJECT_NAME}" -q 2>/dev/null || true)
    if [ -n "${containers}" ]; then
        log "Docker konteynerleri durduruluyor ve kaldırılıyor..."
        docker stop ${containers} 2>/dev/null || true
        docker rm ${containers} 2>/dev/null || true
        log "Konteynerler kaldırıldı."
    else
        log "İlgili Docker konteyneri bulunamadı."
    fi

    # İmajları kaldır
    local images
    images=$(docker images --filter "reference=*${PROJECT_NAME}*" -q 2>/dev/null || true)
    if [ -n "${images}" ]; then
        log "Docker imajları kaldırılıyor..."
        docker rmi ${images} 2>/dev/null || true
        log "İmajlar kaldırıldı."
    else
        log "İlgili Docker imajı bulunamadı."
    fi

    # Docker compose ile oluşturulan ağları kaldır
    if [ -f "${PROJECT_DIR}/docker-compose.yml" ]; then
        docker-compose -f "${PROJECT_DIR}/docker-compose.yml" down --volumes --remove-orphans 2>/dev/null || true
        log "Docker Compose kaynakları temizlendi."
    fi

    # Dangling (sahipsiz) Docker volume'ları
    docker volume prune -f 2>/dev/null || true
    log "Docker volume temizliği yapıldı."
}

# ====================================================================== #
#  ADIM 3: SANAL ORTAM TEMİZLİĞİ
# ====================================================================== #

cleanup_venv() {
    header "Adım 3: Python Sanal Ortam Temizliği"

    # Sanal ortamı deaktive et
    deactivate 2>/dev/null || true

    local venv_dir="${PROJECT_DIR}/venv"
    if [ -d "${venv_dir}" ]; then
        local venv_size
        venv_size=$(du -sh "${venv_dir}" 2>/dev/null | awk '{print $1}')
        rm -rf "${venv_dir}"
        log "Sanal ortam kaldırıldı: ${venv_dir} (${venv_size})"
    else
        log "Sanal ortam dizini bulunamadı."
    fi

    # pip cache temizliği
    if command -v pip &> /dev/null; then
        pip cache purge 2>/dev/null && log "pip cache temizlendi." || true
    fi
    # Kullanıcı pip cache dizinini de kontrol et
    local pip_cache_dir="${HOME}/.cache/pip"
    if [ -d "${pip_cache_dir}" ]; then
        warn "pip cache dizini mevcut: ${pip_cache_dir}"
        warn "Tamamen temizlemek için: rm -rf ${pip_cache_dir}"
    fi
}

# ====================================================================== #
#  ADIM 4: PROJE DOSYALARI TEMİZLİĞİ
# ====================================================================== #

cleanup_project_files() {
    header "Adım 4: Proje Dosyaları Temizliği"

    # 4.1 - Konfigürasyon dosyaları
    local config_files=(".env" "data/users.json" "user_db.json")
    for f in "${config_files[@]}"; do
        local filepath="${PROJECT_DIR}/${f}"
        if [ -f "${filepath}" ]; then
            # Güvenli silme: Önce sıfırlarla üzerine yaz, sonra sil
            dd if=/dev/zero of="${filepath}" bs=1 count="$(wc -c < "${filepath}")" 2>/dev/null || true
            rm -f "${filepath}"
            log "Güvenli silme: ${f} (üzerine yazıldı + silindi)"
        fi
    done

    # 4.2 - Log dosyaları
    if [ -d "${PROJECT_DIR}/logs" ]; then
        local log_count
        log_count=$(find "${PROJECT_DIR}/logs" -type f | wc -l)
        rm -rf "${PROJECT_DIR}/logs"
        log "Log dizini kaldırıldı (${log_count} dosya)"
    fi

    # 4.3 - Sonuç dosyaları
    if [ -d "${PROJECT_DIR}/results" ]; then
        local result_count
        result_count=$(find "${PROJECT_DIR}/results" -type f | wc -l)
        rm -rf "${PROJECT_DIR}/results"
        log "Sonuç dizini kaldırıldı (${result_count} dosya)"
    fi

    # 4.4 - Veri dizini
    if [ -d "${PROJECT_DIR}/data" ]; then
        rm -rf "${PROJECT_DIR}/data"
        log "Veri dizini kaldırıldı."
    fi

    # 4.5 - Python cache dosyaları
    find "${PROJECT_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "${PROJECT_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true
    find "${PROJECT_DIR}" -type f -name "*.pyo" -delete 2>/dev/null || true
    find "${PROJECT_DIR}" -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find "${PROJECT_DIR}" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find "${PROJECT_DIR}" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    log "Python cache dosyaları temizlendi (__pycache__, .pyc, .egg-info, .pytest_cache)"
}

# ====================================================================== #
#  ADIM 5: SİSTEM SEVİYESİ KALINTI KONTROLÜ
# ====================================================================== #

verify_cleanup() {
    header "Adım 5: Kalıntı Doğrulama (Forensics)"

    local issues=0

    # 5.1 - Dosya sistemi kontrolü
    log "Dosya sistemi taraması..."

    local leftover_dirs=("venv" "logs" "results" "data" "__pycache__")
    for d in "${leftover_dirs[@]}"; do
        if [ -d "${PROJECT_DIR}/${d}" ]; then
            error "  Kalıntı dizin bulundu: ${d}/"
            issues=$((issues + 1))
        else
            log "  ✓ ${d}/ temiz"
        fi
    done

    local leftover_files=(".env" "user_db.json")
    for f in "${leftover_files[@]}"; do
        if [ -f "${PROJECT_DIR}/${f}" ]; then
            error "  Kalıntı dosya bulundu: ${f}"
            issues=$((issues + 1))
        else
            log "  ✓ ${f} temiz"
        fi
    done

    # 5.2 - Port kontrolü
    log "Port taraması..."
    if command -v lsof &> /dev/null; then
        if lsof -i ":${FLASK_PORT}" &>/dev/null; then
            error "  Port ${FLASK_PORT} hala kullanımda!"
            issues=$((issues + 1))
        else
            log "  ✓ Port ${FLASK_PORT} serbest"
        fi
    elif command -v ss &> /dev/null; then
        if ss -tlnp 2>/dev/null | grep -q ":${FLASK_PORT}"; then
            error "  Port ${FLASK_PORT} hala kullanımda!"
            issues=$((issues + 1))
        else
            log "  ✓ Port ${FLASK_PORT} serbest"
        fi
    fi

    # 5.3 - Süreç kontrolü
    log "Süreç taraması..."
    if pgrep -f "python.*app.py" &>/dev/null || pgrep -f "${PROJECT_NAME}" &>/dev/null; then
        error "  Proje ile ilişkili süreç hala çalışıyor!"
        issues=$((issues + 1))
    else
        log "  ✓ İlişkili süreç bulunamadı"
    fi

    # 5.4 - Docker kontrolü
    if command -v docker &> /dev/null; then
        log "Docker taraması..."
        if docker ps -a --filter "name=${PROJECT_NAME}" -q 2>/dev/null | grep -q .; then
            error "  Docker konteyneri hala mevcut!"
            issues=$((issues + 1))
        else
            log "  ✓ Docker konteyneri temiz"
        fi
    fi

    # 5.5 - Sonuç
    echo ""
    if [ "${issues}" -eq 0 ]; then
        echo -e "${GREEN}  ══════════════════════════════════════════════════${NC}"
        echo -e "${GREEN}  ✓ TEMİZLİK BAŞARILI: Hiçbir kalıntı bulunamadı!${NC}"
        echo -e "${GREEN}  ══════════════════════════════════════════════════${NC}"
    else
        echo -e "${RED}  ══════════════════════════════════════════════════${NC}"
        echo -e "${RED}  ✗ ${issues} kalıntı tespit edildi!${NC}"
        echo -e "${RED}  ══════════════════════════════════════════════════${NC}"
    fi

    # 5.6 - Ek öneriler
    echo ""
    warn "EK ÖNERİLER (Manuel kontrol gerektiren):"
    echo "  ─────────────────────────────────────────────────"
    echo "  1. Shell history temizliği:"
    echo "     history -c && history -w    # Bash history"
    echo "     # veya ~/.bash_history, ~/.zsh_history dosyalarını kontrol edin"
    echo ""
    echo "  2. Sistem logları (/var/log/):"
    echo "     # Docker logları, syslog vb. kontrol edin"
    echo ""
    echo "  3. Tarayıcı geçmişi:"
    echo "     # localhost:${FLASK_PORT} kayıtları tarayıcı geçmişinde olabilir"
    echo ""
    echo "  4. Git global config:"
    echo "     # ~/.gitconfig içinde proje ile ilgili kayıt olabilir"
    echo ""
    echo "  5. DNS cache:"
    echo "     # sudo systemd-resolve --flush-caches (Linux)"
    echo "     # sudo dscacheutil -flushcache (macOS)"
    echo "  ─────────────────────────────────────────────────"
    echo ""
    echo "  TAVSİYE: En güvenli yöntem, bu projeyi sanal makinede (VM)"
    echo "  çalıştırıp, işlem bitince VM'i silmektir."
}

# ====================================================================== #
#  ANA AKIŞ
# ====================================================================== #

main() {
    confirm_uninstall
    stop_services
    cleanup_docker
    cleanup_venv
    cleanup_project_files
    verify_cleanup

    echo ""
    log "Kaldırma işlemi tamamlandı."
    echo ""
    echo "  Proje kaynak kodlarını da silmek istiyorsanız:"
    echo "  rm -rf ${PROJECT_DIR}"
}

main "$@"
