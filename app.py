#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║  BRUTE-FORCE DEFENDER - Web API (Flask + JWT Authentication)        ║
║                                                                      ║
║  Adım 5 Analizi: Kaynak Kod ve Akış Analizi (Threat Modeling)       ║
║                                                                      ║
║  ENTRYPOINT (Başlangıç Noktası): Bu dosya (app.py)                 ║
║  AUTH MEKANİZMASI: JWT (JSON Web Token)                             ║
║                                                                      ║
║  Tersine Mühendislik Dersi - Vize Projesi                           ║
╚══════════════════════════════════════════════════════════════════════╝

=== ENTRYPOINT ANALİZİ ===

Uygulama akışı:
  1. app.py çalıştırılır (ENTRYPOINT)
  2. Flask app oluşturulur, config yüklenir
  3. JWT secret key ortam değişkeninden okunur
  4. Route'lar tanımlanır:
     - POST /api/register    → Kullanıcı kaydı (salt'lı hash oluşturur)
     - POST /api/login       → Giriş + JWT token üretimi
     - GET  /api/profile     → JWT doğrulaması gerektirir (korumalı)
     - POST /api/hash        → Şifre hashleme servisi (korumalı)
     - POST /api/demo/attack → Saldırı simülasyonu (korumalı)
     - GET  /health          → Sağlık kontrolü (Docker healthcheck)
  5. Flask sunucu dinlemeye başlar (port 5000)

=== JWT (JSON Web Token) AUTHENTICATION ANALİZİ ===

JWT Nedir?
  Kullanıcı kimliğini doğrulamak için kullanılan, dijital olarak
  imzalanmış bir JSON nesnesidir. 3 bölümden oluşur:

  Header.Payload.Signature
  xxxxxx.yyyyyy.zzzzzz

  Header:  {"alg": "HS256", "typ": "JWT"}
  Payload: {"user_id": "ali", "exp": 1234567890, "iat": 1234567800}
  Signature: HMAC-SHA256(base64(header) + "." + base64(payload), SECRET_KEY)

JWT Akışı:
  1. Kullanıcı /api/login'e username+password gönderir
  2. Sunucu şifreyi salt'lı hash ile DOĞRULAR
  3. Doğruysa → JWT token oluşturulur ve döndürülür
  4. Kullanıcı sonraki isteklerde token'ı Header'da gönderir:
     Authorization: Bearer <JWT_TOKEN>
  5. Sunucu her istekte token'ı doğrular (imza + süre kontrolü)

=== THREAT MODELING (Tehdit Modelleme) ===

Potansiyel saldırı vektörleri:
  1. Brute-force login → Rate limiting ile korunur
  2. JWT token çalma   → HTTPS + kısa ömür ile azaltılır
  3. SQL Injection      → JSON veritabanı, SQL yok (ancak NoSQL injection riski)
  4. XSS                → API-only, HTML render yok
  5. JWT secret leak    → .env dosyasında, .gitignore'da
  6. Timing attack      → Hash karşılaştırma zamanından bilgi sızması riski
"""

import os
import sys
import json
import time
import datetime
import functools
import hashlib
import hmac
from collections import defaultdict

# Flask ve JWT
from flask import Flask, request, jsonify, g

# Proje modülleri
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.hasher import BLAKE3Hasher
from src.database import UserDatabase
from src.attacker import BruteForceAttacker
from src.benchmark import PerformanceBenchmark

# ====================================================================== #
#  UYGULAMA KONFİGÜRASYONU
# ====================================================================== #

app = Flask(__name__)

# Konfigürasyon (.env veya ortam değişkenlerinden)
app.config.update(
    SECRET_KEY=os.environ.get('JWT_SECRET_KEY', 'dev-secret-key-CHANGE-IN-PRODUCTION'),
    JWT_EXPIRATION_HOURS=int(os.environ.get('JWT_EXPIRATION_HOURS', '24')),
    SALT_LENGTH=int(os.environ.get('SALT_LENGTH', '16')),
    MAX_LOGIN_ATTEMPTS=int(os.environ.get('MAX_LOGIN_ATTEMPTS', '5')),
    LOCKOUT_DURATION=int(os.environ.get('LOCKOUT_DURATION_MINUTES', '15')) * 60,
    DATABASE_PATH=os.environ.get('DATABASE_PATH', 'data/users.json'),
)

# Global nesneler
hasher = BLAKE3Hasher(salt_length=app.config['SALT_LENGTH'])
db = UserDatabase(db_path=app.config['DATABASE_PATH'])
attacker = BruteForceAttacker()
benchmark = PerformanceBenchmark()

# Rate limiting için login deneme sayacı
# {ip_address: {"count": int, "lockout_until": float}}
login_attempts = defaultdict(lambda: {"count": 0, "lockout_until": 0})


# ====================================================================== #
#  JWT TOKEN İŞLEMLERİ (Manuel Implementasyon)
# ====================================================================== #
# Not: Gerçek projelerde PyJWT kullanılır.
# Burada JWT'nin iç yapısını anlamak için manuel implementasyon var.

def base64url_encode(data: bytes) -> str:
    """URL-safe Base64 encoding (padding olmadan)."""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def base64url_decode(s: str) -> bytes:
    """URL-safe Base64 decoding."""
    import base64
    s += '=' * (4 - len(s) % 4)  # Padding ekle
    return base64.urlsafe_b64decode(s)

def create_jwt(payload: dict) -> str:
    """JWT token oluştur.

    Token yapısı: Header.Payload.Signature

    Args:
        payload: Token payload'ı (user_id, exp, iat vb.)

    Returns:
        JWT token string
    """
    # Header
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64url_encode(json.dumps(header, separators=(',', ':')).encode())

    # Payload - süre bilgilerini ekle
    now = datetime.datetime.utcnow()
    payload.update({
        "iat": int(now.timestamp()),  # Issued At (oluşturulma zamanı)
        "exp": int((now + datetime.timedelta(
            hours=app.config['JWT_EXPIRATION_HOURS']
        )).timestamp()),  # Expiration (son geçerlilik)
    })
    payload_b64 = base64url_encode(json.dumps(payload, separators=(',', ':')).encode())

    # Signature (HMAC-SHA256)
    # İmza = HMAC-SHA256(header_b64 + "." + payload_b64, SECRET_KEY)
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(
        app.config['SECRET_KEY'].encode(),
        signing_input,
        hashlib.sha256
    ).digest()
    signature_b64 = base64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{signature_b64}"

def verify_jwt(token: str) -> dict:
    """JWT token doğrula.

    Doğrulama adımları:
      1. Token'ı 3 parçaya ayır
      2. İmzayı kontrol et (manipülasyon tespiti)
      3. Süre kontrolü (expired mı?)

    Args:
        token: JWT token string

    Returns:
        Decode edilmiş payload

    Raises:
        ValueError: Token geçersiz veya süresi dolmuş
    """
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Geçersiz token formatı")

    header_b64, payload_b64, signature_b64 = parts

    # 1. İmza doğrulaması
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_signature = hmac.new(
        app.config['SECRET_KEY'].encode(),
        signing_input,
        hashlib.sha256
    ).digest()
    expected_b64 = base64url_encode(expected_signature)

    # Timing-safe karşılaştırma (timing attack'a karşı)
    if not hmac.compare_digest(signature_b64, expected_b64):
        raise ValueError("Geçersiz token imzası")

    # 2. Payload decode
    payload = json.loads(base64url_decode(payload_b64))

    # 3. Süre kontrolü
    if 'exp' in payload and payload['exp'] < time.time():
        raise ValueError("Token süresi dolmuş")

    return payload


# ====================================================================== #
#  MIDDLEWARE / DECORATOR
# ====================================================================== #

def jwt_required(f):
    """JWT doğrulama decorator'ı.

    Korumalı endpoint'ler bu decorator ile işaretlenir.
    Authorization header'ında geçerli JWT token gerektirir.

    Kullanım:
        @app.route('/protected')
        @jwt_required
        def protected():
            user = g.current_user  # Doğrulanmış kullanıcı
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Authorization header'ını kontrol et
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return jsonify({
                "error": "Authorization header eksik veya hatalı",
                "hint": "Header formatı: Authorization: Bearer <JWT_TOKEN>"
            }), 401

        token = auth_header.split(' ', 1)[1]

        try:
            payload = verify_jwt(token)
            g.current_user = payload.get('user_id')
            g.token_payload = payload
        except ValueError as e:
            return jsonify({"error": f"Token doğrulama hatası: {str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated


def rate_limit_check(ip: str) -> bool:
    """Rate limiting kontrolü (brute-force login koruması).

    Args:
        ip: İstek yapan IP adresi

    Returns:
        True eğer IP kilitliyse (çok fazla deneme)
    """
    attempts = login_attempts[ip]

    # Kilit süresi dolmuş mu?
    if attempts["lockout_until"] > 0 and time.time() > attempts["lockout_until"]:
        attempts["count"] = 0
        attempts["lockout_until"] = 0

    # Kilitli mi?
    if attempts["lockout_until"] > time.time():
        return True

    return False


# ====================================================================== #
#  API ENDPOINT'LERİ
# ====================================================================== #

# ─────────────────── SAĞLIK KONTROLÜ ─────────────────── #

@app.route('/health', methods=['GET'])
def health_check():
    """Sağlık kontrolü endpoint'i.

    Docker HEALTHCHECK ve load balancer'lar bu endpoint'i kullanır.
    Uygulama ve bağımlılıkların durumunu kontrol eder.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "checks": {
            "blake3": False,
            "database": False,
        }
    }

    # BLAKE3 kontrolü
    try:
        test_hash = hasher.hash_without_salt("health_check")
        health["checks"]["blake3"] = len(test_hash) == 64
    except Exception:
        health["status"] = "unhealthy"

    # Veritabanı kontrolü
    try:
        health["checks"]["database"] = True
        health["checks"]["user_count"] = len(db.salted_users)
    except Exception:
        health["status"] = "unhealthy"

    status_code = 200 if health["status"] == "healthy" else 503
    return jsonify(health), status_code


# ─────────────────── KULLANICI KAYDI ─────────────────── #

@app.route('/api/register', methods=['POST'])
def register():
    """Yeni kullanıcı kaydı.

    Request Body:
        {"username": "ali", "password": "secure_password"}

    İşlem:
        1. Kullanıcı adı benzersizlik kontrolü
        2. Şifre güçlülük kontrolü
        3. Salt'lı BLAKE3 hash oluşturma
        4. Veritabanına kaydetme

    Response:
        201: Kayıt başarılı
        400: Geçersiz girdi
        409: Kullanıcı zaten mevcut
    """
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "username ve password alanları gerekli"}), 400

    username = data['username'].strip()
    password = data['password']

    # Validasyon
    if len(username) < 3:
        return jsonify({"error": "Kullanıcı adı en az 3 karakter olmalı"}), 400
    if len(password) < 6:
        return jsonify({"error": "Şifre en az 6 karakter olmalı"}), 400

    # Benzersizlik kontrolü
    if username in db.salted_users:
        return jsonify({"error": "Bu kullanıcı adı zaten mevcut"}), 409

    # Salt'lı hash oluştur ve kaydet
    hash_val, salt_hex = db.add_user_salted(username, password)

    # Veritabanını diske kaydet
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)
    db.save_to_disk()

    return jsonify({
        "message": "Kayıt başarılı",
        "username": username,
        "hash_algorithm": "BLAKE3",
        "salt_length_bytes": app.config['SALT_LENGTH'],
        "hash_preview": hash_val[:16] + "...",
        # GÜVENLİK: Tam hash ve salt değerleri DÖNDÜRÜLMEZ
    }), 201


# ─────────────────── GİRİŞ (LOGIN) ─────────────────── #

@app.route('/api/login', methods=['POST'])
def login():
    """Kullanıcı girişi + JWT token üretimi.

    Request Body:
        {"username": "ali", "password": "secure_password"}

    İşlem:
        1. Rate limiting kontrolü (brute-force koruması)
        2. Kullanıcı var mı kontrolü
        3. Salt'lı hash doğrulaması
        4. Başarılıysa JWT token üretimi

    Response:
        200: Giriş başarılı + JWT token
        401: Hatalı kimlik bilgileri
        429: Çok fazla deneme (rate limit)

    === THREAT MODELING: LOGIN SALDIRI VEKTÖRLERİ ===
    1. Brute-force: Rate limiting ile azaltılır
    2. Credential stuffing: Account lockout ile azaltılır
    3. Timing attack: hmac.compare_digest kullanılır
    4. Response bilgi sızıntısı: Genel hata mesajı döndürülür
    """
    client_ip = request.remote_addr

    # KORUMA 1: Rate limiting
    if rate_limit_check(client_ip):
        remaining = int(login_attempts[client_ip]["lockout_until"] - time.time())
        return jsonify({
            "error": "Çok fazla başarısız deneme. Hesap geçici olarak kilitlendi.",
            "retry_after_seconds": remaining,
        }), 429

    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "username ve password alanları gerekli"}), 400

    username = data['username'].strip()
    password = data['password']

    # Doğrulama
    is_valid = db.verify_login_salted(username, password)

    if not is_valid:
        # Başarısız deneme sayacını artır
        login_attempts[client_ip]["count"] += 1
        if login_attempts[client_ip]["count"] >= app.config['MAX_LOGIN_ATTEMPTS']:
            login_attempts[client_ip]["lockout_until"] = time.time() + app.config['LOCKOUT_DURATION']

        # GÜVENLİK: "Kullanıcı bulunamadı" vs "Şifre yanlış" AYIRT EDİLMEZ
        # Bu, saldırganın kullanıcı adı keşfini önler (username enumeration)
        return jsonify({"error": "Geçersiz kullanıcı adı veya şifre"}), 401

    # Başarılı giriş → sayacı sıfırla
    login_attempts[client_ip]["count"] = 0

    # JWT Token oluştur
    token = create_jwt({
        "user_id": username,
        "role": "user",
    })

    return jsonify({
        "message": "Giriş başarılı",
        "token": token,
        "token_type": "Bearer",
        "expires_in": app.config['JWT_EXPIRATION_HOURS'] * 3600,
    }), 200


# ─────────────────── KORUNAN ENDPOINT'LER ─────────────────── #

@app.route('/api/profile', methods=['GET'])
@jwt_required
def profile():
    """Kullanıcı profili (JWT korumalı).

    Headers:
        Authorization: Bearer <JWT_TOKEN>

    Bu endpoint'e erişmek için geçerli JWT token gereklidir.
    Token olmadan 401 Unauthorized döner.
    """
    username = g.current_user
    user_data = db.salted_users.get(username, {})

    return jsonify({
        "username": username,
        "hash_algorithm": "BLAKE3",
        "salt_length": app.config['SALT_LENGTH'],
        "has_salted_hash": bool(user_data),
        "token_issued_at": g.token_payload.get('iat'),
        "token_expires_at": g.token_payload.get('exp'),
    })


@app.route('/api/hash', methods=['POST'])
@jwt_required
def hash_password():
    """Şifre hashleme servisi (JWT korumalı).

    Request Body:
        {"password": "test", "method": "salted"}   → Salt'lı hash
        {"password": "test", "method": "unsalted"} → Salt'sız hash
        {"password": "test", "method": "compare"}  → Her iki yöntem

    Response:
        Hash sonuçları ve karşılaştırma
    """
    data = request.get_json()
    if not data or 'password' not in data:
        return jsonify({"error": "password alanı gerekli"}), 400

    password = data['password']
    method = data.get('method', 'compare')

    result = {"password_length": len(password)}

    if method in ('unsalted', 'compare'):
        result["unsalted"] = {
            "hash": hasher.hash_without_salt(password),
            "algorithm": "BLAKE3",
            "salt": None,
            "warning": "Salt'sız hash güvenli DEĞİLDİR!"
        }

    if method in ('salted', 'compare'):
        h, salt = hasher.hash_with_salt(password)
        result["salted"] = {
            "hash": h,
            "algorithm": "BLAKE3",
            "salt_hex": salt.hex(),
            "salt_length_bytes": len(salt),
        }

    if method == 'compare':
        result["comparison"] = {
            "same_password_same_unsalted_hash": True,
            "same_password_different_salted_hash": True,
            "explanation": "Salt'sız hash her zaman aynı, salt'lı hash her seferinde farklı"
        }

    return jsonify(result)


@app.route('/api/demo/attack', methods=['POST'])
@jwt_required
def demo_attack():
    """Saldırı simülasyonu servisi (JWT korumalı).

    Request Body:
        {"target_password": "123456", "wordlist_size": 40}

    Bu endpoint, salt'lı ve salt'sız hash'lere karşı
    sözlük saldırısı simülasyonu çalıştırır.
    """
    data = request.get_json()
    target_password = data.get('target_password', '123456')
    wordlist_size = min(data.get('wordlist_size', 40), 100)  # Max 100

    # Yaygın şifreler
    common = [
        "123456", "password", "123456789", "12345678", "12345",
        "qwerty", "abc123", "111111", "123123", "admin",
        "letmein", "welcome", "monkey", "dragon", "master",
        "1234567", "696969", "football", "shadow", "michael",
        "654321", "trustno1", "iloveyou", "sunshine", "princess",
        "baseball", "access", "hello", "charlie", "donald",
        "loveme", "freedom", "whatever", "nicole", "jordan",
        "batman", "starwars", "121212", "1q2w3e4r", "passwd",
    ][:wordlist_size]

    # Salt'sız saldırı
    target_unsalted = hasher.hash_without_salt(target_password)
    result_unsalted = attacker.dictionary_attack_unsalted(target_unsalted, common)

    # Salt'lı saldırı
    target_salted, salt = hasher.hash_with_salt(target_password)
    result_salted = attacker.dictionary_attack_salted(target_salted, salt, common)

    return jsonify({
        "target_password_in_wordlist": target_password in common,
        "wordlist_size": len(common),
        "unsalted_attack": result_unsalted,
        "salted_attack": result_salted,
        "conclusion": (
            "Salt'lı hash'ler için her kullanıcı ayrı ayrı saldırılmalıdır. "
            "Rainbow table KULLANILAMAZ. Bu, saldırı süresini N katına çıkarır."
        )
    })


@app.route('/api/benchmark', methods=['GET'])
@jwt_required
def run_benchmark():
    """Performans benchmark endpoint'i (JWT korumalı)."""
    iterations = min(int(request.args.get('iterations', 10000)), 50000)

    speed = benchmark.measure_hash_speed(iterations=iterations)
    comparison = benchmark.blake3_vs_sha256(iterations=iterations)

    return jsonify({
        "iterations": iterations,
        "hash_speed": speed,
        "blake3_vs_sha256": comparison,
    })


# ─────────────────── HATA YÖNETİMİ ─────────────────── #

@app.errorhandler(404)
def not_found(e):
    return jsonify({
        "error": "Endpoint bulunamadı",
        "available_endpoints": [
            "POST /api/register",
            "POST /api/login",
            "GET  /api/profile (JWT)",
            "POST /api/hash (JWT)",
            "POST /api/demo/attack (JWT)",
            "GET  /api/benchmark (JWT)",
            "GET  /health",
        ]
    }), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Bu HTTP metodu bu endpoint için desteklenmiyor"}), 405

@app.errorhandler(500)
def internal_error(e):
    # GÜVENLİK: İç hata detayları DÖNDÜRÜLMEZ
    return jsonify({"error": "Sunucu hatası"}), 500


# ====================================================================== #
#  UYGULAMA BAŞLATMA
# ====================================================================== #

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║  🛡️  Brute-Force Defender - Web API                  ║
    ║                                                      ║
    ║  Endpoints:                                          ║
    ║    POST /api/register    → Kullanıcı kaydı          ║
    ║    POST /api/login       → Giriş + JWT token        ║
    ║    GET  /api/profile     → Profil (JWT gerekli)     ║
    ║    POST /api/hash        → Hash servisi (JWT)       ║
    ║    POST /api/demo/attack → Saldırı demo (JWT)       ║
    ║    GET  /api/benchmark   → Benchmark (JWT)          ║
    ║    GET  /health          → Sağlık kontrolü          ║
    ╚══════════════════════════════════════════════════════╝
    """)

    # Veritabanı dizinini oluştur
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)

    # Varsa veritabanını yükle
    try:
        db.load_from_disk()
        print(f"  Veritabanı yüklendi: {len(db.salted_users)} kullanıcı")
    except FileNotFoundError:
        print("  Yeni veritabanı oluşturulacak.")

    # Demo kullanıcıları ekle (yoksa)
    if not db.salted_users:
        demo_users = {"demo": "demo123", "admin": "admin_pass"}
        db.populate_demo_users(demo_users)
        db.save_to_disk()
        print("  Demo kullanıcılar eklendi: demo/demo123, admin/admin_pass")

    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', '0') == '1'

    app.run(
        host='0.0.0.0',   # Tüm arayüzlerde dinle (Docker için gerekli)
        port=port,
        debug=debug,
    )
