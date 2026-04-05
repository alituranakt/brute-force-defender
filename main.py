#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║              BRUTE-FORCE DEFENDER                                    ║
║              BLAKE3 Salt Mekanizması Demonstrasyonu                  ║
║                                                                      ║
║  Tersine Mühendislik Dersi - Vize Projesi                           ║
║  Bu proje, BLAKE3 hash algoritması kullanarak tuzlama (salting)     ║
║  mekanizmasının brute-force saldırılara karşı etkisini gösterir.    ║
╚══════════════════════════════════════════════════════════════════════╝

Kullanım:
    python main.py              → Tam demo (tüm senaryolar)
    python main.py --demo 1     → Sadece belirli demo
    python main.py --benchmark  → Sadece performans testi
    python main.py --interactive → İnteraktif mod
"""

import argparse
import sys
import os
import json
import time

# Proje kök dizinini path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.hasher import BLAKE3Hasher
from src.database import UserDatabase
from src.attacker import BruteForceAttacker
from src.benchmark import PerformanceBenchmark
from src.visualizer import ResultVisualizer

# ====================================================================== #
#  Yardımcı Fonksiyonlar
# ====================================================================== #

def print_header(title: str, char: str = "="):
    width = 70
    print(f"\n{'=' * width}")
    print(f"  {title}")
    print(f"{'=' * width}\n")


def print_subheader(title: str):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def print_result(label: str, value, indent: int = 2):
    print(f"{' ' * indent}• {label}: {value}")


def print_table(headers, rows, col_widths=None):
    """Basit tablo yazdırma."""
    if col_widths is None:
        col_widths = [max(len(str(h)), max(len(str(r[i])) for r in rows))
                      for i, h in enumerate(headers)]

    header_line = " | ".join(f"{h:<{w}}" for h, w in zip(headers, col_widths))
    separator = "-+-".join("-" * w for w in col_widths)
    print(f"  {header_line}")
    print(f"  {separator}")
    for row in rows:
        row_line = " | ".join(f"{str(v):<{w}}" for v, w in zip(row, col_widths))
        print(f"  {row_line}")


# ====================================================================== #
#  Demo Kullanıcı Verileri
# ====================================================================== #
DEMO_USERS = {
    "ali": "123456",
    "ayse": "password",
    "mehmet": "123456",       # Ali ile AYNI şifre! (salt farkını gösterir)
    "zeynep": "qwerty",
    "ahmet": "letmein",
    "fatma": "password",      # Ayşe ile AYNI şifre!
    "mustafa": "abc123",
    "elif": "admin",
}

# Yaygın şifreler sözlüğü (sözlük saldırısı için)
COMMON_PASSWORDS = [
    "123456", "password", "123456789", "12345678", "12345",
    "qwerty", "abc123", "111111", "123123", "admin",
    "letmein", "welcome", "monkey", "dragon", "master",
    "1234567", "696969", "football", "shadow", "michael",
    "654321", "trustno1", "iloveyou", "sunshine", "princess",
    "baseball", "access", "hello", "charlie", "donald",
    "loveme", "freedom", "whatever", "nicole", "jordan",
    "batman", "starwars", "121212", "1q2w3e4r", "passwd",
]


# ====================================================================== #
#  DEMO 1: Hash Temelleri ve Salt Farkı
# ====================================================================== #
def demo1_hash_basics():
    """BLAKE3 hash temelleri ve salt'ın etkisini gösterir."""
    print_header("DEMO 1: BLAKE3 Hash Temelleri ve Salt Mekanizması")

    hasher = BLAKE3Hasher()

    # 1.1 - Temel hash
    print_subheader("1.1 - Temel BLAKE3 Hash (Salt'sız)")
    test_passwords = ["123456", "password", "hello"]
    for pwd in test_passwords:
        h = hasher.hash_without_salt(pwd)
        print(f"  '{pwd}' → {h}")

    # 1.2 - Aynı şifre = aynı hash (ZAFİYET!)
    print_subheader("1.2 - Aynı Şifre = Aynı Hash (ZAFİYET)")
    pwd = "123456"
    h1 = hasher.hash_without_salt(pwd)
    h2 = hasher.hash_without_salt(pwd)
    h3 = hasher.hash_without_salt(pwd)
    print(f"  '{pwd}' (1. hash): {h1}")
    print(f"  '{pwd}' (2. hash): {h2}")
    print(f"  '{pwd}' (3. hash): {h3}")
    print(f"\n  ⚠️  Hepsi AYNI! Saldırgan bir kez bulursa, aynı şifreyi kullanan")
    print(f"     TÜM kullanıcıları ele geçirir!")

    # 1.3 - Salt'lı hash
    print_subheader("1.3 - Salt'lı BLAKE3 Hash (GÜVENLİ)")
    pwd = "123456"
    h1, s1 = hasher.hash_with_salt(pwd)
    h2, s2 = hasher.hash_with_salt(pwd)
    h3, s3 = hasher.hash_with_salt(pwd)
    print(f"  '{pwd}' + salt({s1.hex()[:16]}...) → {h1[:48]}...")
    print(f"  '{pwd}' + salt({s2.hex()[:16]}...) → {h2[:48]}...")
    print(f"  '{pwd}' + salt({s3.hex()[:16]}...) → {h3[:48]}...")
    print(f"\n  ✅ Hepsi FARKLI! Aynı şifre olsa bile her hash benzersiz.")

    # 1.4 - BLAKE3 Keyed Hash (HMAC alternatifi)
    print_subheader("1.4 - BLAKE3 Keyed Hash (BLAKE3'e Özgü)")
    h_keyed, key = hasher.hash_with_key(pwd)
    print(f"  Keyed hash: {h_keyed}")
    print(f"  Key (hex) : {key.hex()[:32]}...")
    print(f"\n  ℹ️  BLAKE3, HMAC'a gerek kalmadan doğrudan anahtar tabanlı hash destekler.")

    return True


# ====================================================================== #
#  DEMO 2: Veritabanı Simülasyonu
# ====================================================================== #
def demo2_database_simulation():
    """Kullanıcı veritabanı simülasyonu ve duplicate hash problemi."""
    print_header("DEMO 2: Kullanıcı Veritabanı Simülasyonu")

    db = UserDatabase()
    db.populate_demo_users(DEMO_USERS)

    # 2.1 - Salt'sız tablo
    print_subheader("2.1 - Salt'sız Kullanıcı Tablosu")
    unsalted = db.get_unsalted_table()
    print_table(
        ["Kullanıcı", "Hash (BLAKE3)"],
        [(u, h[:48] + "...") for u, h in unsalted],
        [12, 52]
    )

    # 2.2 - Duplicate hash tespiti (salt'sız)
    print_subheader("2.2 - Aynı Hash'e Sahip Kullanıcılar (Salt'sız)")
    duplicates = db.find_duplicate_hashes_unsalted()
    if duplicates:
        for hash_val, users in duplicates.items():
            print(f"  ⚠️  {', '.join(users)} → aynı hash!")
            print(f"     {hash_val[:48]}...")
        print(f"\n  ❌ {len(duplicates)} adet tekrarlayan hash bulundu!")
        print(f"     Salt kullanılmadığı için aynı şifreler aynı hash üretiyor.")
    else:
        print("  Tekrarlayan hash bulunamadı.")

    # 2.3 - Salt'lı tablo
    print_subheader("2.3 - Salt'lı Kullanıcı Tablosu")
    salted = db.get_salted_table()
    print_table(
        ["Kullanıcı", "Hash (BLAKE3)", "Salt"],
        [(u, h[:32] + "...", s[:16] + "...") for u, h, s in salted],
        [12, 36, 20]
    )

    # 2.4 - Duplicate hash tespiti (salt'lı)
    print_subheader("2.4 - Aynı Hash'e Sahip Kullanıcılar (Salt'lı)")
    duplicates_salted = db.find_duplicate_hashes_salted()
    if duplicates_salted:
        for hash_val, users in duplicates_salted.items():
            print(f"  ⚠️  {', '.join(users)} → aynı hash!")
    else:
        print(f"  ✅ Hiç tekrarlayan hash YOK! Her kullanıcının hash'i benzersiz.")
        print(f"     Ali ve Mehmet aynı şifreyi ('123456') kullanmasına rağmen")
        print(f"     farklı salt değerleri sayesinde hash'leri farklı.")

    # 2.5 - Giriş doğrulama
    print_subheader("2.5 - Giriş Doğrulama Testi")
    test_cases = [
        ("ali", "123456", True),
        ("ali", "wrong_password", False),
        ("ayse", "password", True),
        ("mehmet", "123456", True),
    ]
    for username, pwd, expected in test_cases:
        result_unsalted = db.verify_login_unsalted(username, pwd)
        result_salted = db.verify_login_salted(username, pwd)
        status = "✅" if result_salted == expected else "❌"
        print(f"  {status} {username} / '{pwd}': "
              f"Salt'sız={result_unsalted}, Salt'lı={result_salted}")

    return db


# ====================================================================== #
#  DEMO 3: Saldırı Simülasyonu
# ====================================================================== #
def demo3_attack_simulation(db: UserDatabase = None):
    """Brute-force ve sözlük saldırısı simülasyonu."""
    print_header("DEMO 3: Saldırı Simülasyonu")

    if db is None:
        db = UserDatabase()
        db.populate_demo_users(DEMO_USERS)

    attacker = BruteForceAttacker()

    # 3.1 - Tek kullanıcıya sözlük saldırısı
    print_subheader("3.1 - Sözlük Saldırısı: ali (şifre: 123456)")

    target_hash_unsalted = db.unsalted_users["ali"]
    result_unsalted = attacker.dictionary_attack_unsalted(
        target_hash_unsalted, COMMON_PASSWORDS
    )

    salt_ali = bytes.fromhex(db.salted_users["ali"]["salt"])
    target_hash_salted = db.salted_users["ali"]["hash"]
    result_salted = attacker.dictionary_attack_salted(
        target_hash_salted, salt_ali, COMMON_PASSWORDS
    )

    print(f"\n  {'Salt sız Saldırı':.<40}")
    print_result("Sonuç", "BAŞARILI ✅" if result_unsalted["success"] else "BAŞARISIZ ❌")
    print_result("Bulunan şifre", result_unsalted.get("password", "-"))
    print_result("Deneme sayısı", f"{result_unsalted['attempts']:,}")
    print_result("Süre", f"{result_unsalted['time_seconds']:.6f} saniye")
    print_result("Hız", f"{result_unsalted['hashes_per_second']:,} hash/sn")

    print(f"\n  {'Salt lı Saldırı':.<40}")
    print_result("Sonuç", "BAŞARILI ✅" if result_salted["success"] else "BAŞARISIZ ❌")
    print_result("Bulunan şifre", result_salted.get("password", "-"))
    print_result("Deneme sayısı", f"{result_salted['attempts']:,}")
    print_result("Süre", f"{result_salted['time_seconds']:.6f} saniye")
    print_result("Hız", f"{result_salted['hashes_per_second']:,} hash/sn")

    # 3.2 - Rainbow Table saldırısı
    print_subheader("3.2 - Rainbow Table Saldırısı (Çoklu Kullanıcı)")

    unsalted_multi = attacker.attack_multiple_users_unsalted(
        db.unsalted_users, COMMON_PASSWORDS
    )
    salted_multi = attacker.attack_multiple_users_salted(
        db.salted_users, COMMON_PASSWORDS
    )

    print(f"\n  {'Rainbow Table (Salt sız)':.<45}")
    print_result("Kırılan kullanıcı", f"{unsalted_multi['cracked_count']}/{unsalted_multi['total_users']}")
    print_result("Rainbow table oluşturma", f"{unsalted_multi['rainbow_build_time']:.6f} sn")
    print_result("Arama süresi", f"{unsalted_multi['total_lookup_time']:.6f} sn")
    print_result("TOPLAM süre", f"{unsalted_multi['total_time']:.6f} sn")
    if unsalted_multi['cracked_users']:
        print(f"\n  Kırılan hesaplar:")
        for user, pwd in unsalted_multi['cracked_users'].items():
            print(f"    → {user}: '{pwd}'")

    print(f"\n  {'Sözlük Saldırısı (Salt lı)':.<45}")
    print_result("Kırılan kullanıcı", f"{salted_multi['cracked_count']}/{salted_multi['total_users']}")
    print_result("Toplam deneme", f"{salted_multi['total_attempts']:,}")
    print_result("TOPLAM süre", f"{salted_multi['total_time']:.6f} sn")
    if salted_multi['cracked_users']:
        print(f"\n  Kırılan hesaplar:")
        for user, pwd in salted_multi['cracked_users'].items():
            print(f"    → {user}: '{pwd}'")

    # 3.3 - Karşılaştırma özeti
    print_subheader("3.3 - Saldırı Sonuç Karşılaştırması")
    if unsalted_multi['total_time'] > 0:
        ratio = salted_multi['total_time'] / unsalted_multi['total_time']
    else:
        ratio = float('inf')
    print(f"\n  Salt'lı saldırı, salt'sız saldırıya göre {ratio:.1f}x daha yavaş!")
    print(f"  Salt'sız: Rainbow table 1 kez oluşturulur → TÜM kullanıcılar anında kırılır")
    print(f"  Salt'lı:  Her kullanıcı için AYRI AYRI saldırı gerekir")

    return result_unsalted, result_salted, unsalted_multi, salted_multi


# ====================================================================== #
#  DEMO 4: Brute-Force Saldırı (Kısa Şifreler)
# ====================================================================== #
def demo4_brute_force():
    """Kısa şifreler üzerinde kaba kuvvet saldırısı."""
    print_header("DEMO 4: Brute-Force (Kaba Kuvvet) Saldırısı")

    hasher = BLAKE3Hasher()
    attacker = BruteForceAttacker()

    short_password = "ab1"  # Kısa şifre (3 karakter)
    hash_unsalted = hasher.hash_without_salt(short_password)
    hash_salted, salt = hasher.hash_with_salt(short_password)

    print(f"  Hedef şifre: '{short_password}' (3 karakter, a-z + 0-9)")
    print(f"  Olası kombinasyon: 36^1 + 36^2 + 36^3 = {36 + 36**2 + 36**3:,}")

    print_subheader("4.1 - Salt'sız Brute-Force")
    result_bf_unsalted = attacker.brute_force_unsalted(
        hash_unsalted, max_length=3, verbose=False
    )
    print_result("Sonuç", "KIRILDI ✅" if result_bf_unsalted["success"] else "BAŞARISIZ")
    print_result("Bulunan şifre", result_bf_unsalted.get("password", "-"))
    print_result("Deneme sayısı", f"{result_bf_unsalted['attempts']:,}")
    print_result("Süre", f"{result_bf_unsalted['time_seconds']:.4f} saniye")
    print_result("Hız", f"{result_bf_unsalted['hashes_per_second']:,} hash/sn")

    print_subheader("4.2 - Salt'lı Brute-Force")
    result_bf_salted = attacker.brute_force_salted(
        hash_salted, salt, max_length=3, verbose=False
    )
    print_result("Sonuç", "KIRILDI ✅" if result_bf_salted["success"] else "BAŞARISIZ")
    print_result("Bulunan şifre", result_bf_salted.get("password", "-"))
    print_result("Deneme sayısı", f"{result_bf_salted['attempts']:,}")
    print_result("Süre", f"{result_bf_salted['time_seconds']:.4f} saniye")
    print_result("Hız", f"{result_bf_salted['hashes_per_second']:,} hash/sn")

    return result_bf_unsalted, result_bf_salted


# ====================================================================== #
#  DEMO 5: Benchmark ve Görselleştirme
# ====================================================================== #
def demo5_benchmark_and_visualize():
    """Performans benchmark ve grafik oluşturma."""
    print_header("DEMO 5: Performans Benchmark ve Görselleştirme")

    benchmark = PerformanceBenchmark()
    viz = ResultVisualizer(output_dir="results")

    # 5.1 - Hash hızı ölçümü
    print_subheader("5.1 - Hash Hızı Ölçümü (100,000 iterasyon)")
    speed = benchmark.measure_hash_speed(iterations=100000)
    print_result("Salt'sız", f"{speed['unsalted']['hashes_per_second']:,} hash/sn "
                 f"({speed['unsalted']['total_seconds']:.4f}s)")
    print_result("Salt'lı (yeni salt)", f"{speed['salted_new_salt']['hashes_per_second']:,} hash/sn "
                 f"({speed['salted_new_salt']['total_seconds']:.4f}s)")
    print_result("Salt'lı (sabit salt)", f"{speed['salted_fixed_salt']['hashes_per_second']:,} hash/sn "
                 f"({speed['salted_fixed_salt']['total_seconds']:.4f}s)")

    # 5.2 - BLAKE3 vs SHA-256
    print_subheader("5.2 - BLAKE3 vs SHA-256 Karşılaştırması")
    comparison = benchmark.blake3_vs_sha256(iterations=100000)
    print(f"  {'Algoritma':<15} {'Salt sız (h/s)':<20} {'Salt lı (h/s)':<20}")
    print(f"  {'-' * 55}")
    print(f"  {'BLAKE3':<15} {comparison['blake3']['unsalted_hps']:>15,}   "
          f"{comparison['blake3']['salted_hps']:>15,}")
    print(f"  {'SHA-256':<15} {comparison['sha256']['unsalted_hps']:>15,}   "
          f"{comparison['sha256']['salted_hps']:>15,}")
    print(f"\n  BLAKE3 hız avantajı: {comparison['blake3_speedup']}x")

    # 5.3 - Salt uzunluğu etkisi
    print_subheader("5.3 - Salt Uzunluğu Etkisi")
    salt_impact = benchmark.salt_length_impact()
    for length, data in salt_impact['results'].items():
        print(f"  {data['salt_bits']:>4} bit ({length:>3} byte): "
              f"{data['hashes_per_second']:>10,} hash/sn  |  "
              f"Keyspace: {data['keyspace']}")

    # 5.4 - Saldırı süresi projeksiyonu
    print_subheader("5.4 - Şifre Kırılma Süresi Projeksiyonu (100 kullanıcı)")
    estimations = []
    for length in range(3, 9):
        est = benchmark.estimate_crack_time(
            password_length=length, charset_size=36, num_users=100
        )
        estimations.append(est)
        print(f"  {length} karakter: Salt'sız={est['unsalted']['human_readable']:>15} | "
              f"Salt'lı={est['salted']['human_readable']:>15}")

    # 5.5 - Grafikleri oluştur
    print_subheader("5.5 - Grafik Oluşturma")

    path1 = viz.plot_blake3_vs_sha256(comparison)
    print(f"  ✅ {path1}")

    path2 = viz.plot_salt_length_impact(salt_impact)
    print(f"  ✅ {path2}")

    path3 = viz.plot_crack_time_estimation(estimations)
    print(f"  ✅ {path3}")

    # Aynı şifre farklı hash görseli
    hasher = BLAKE3Hasher()
    pwd = "123456"
    unsalted_list = [hasher.hash_without_salt(pwd) for _ in range(5)]
    salted_list = [hasher.hash_with_salt(pwd)[0] for _ in range(5)]
    path4 = viz.plot_same_password_different_hashes(pwd, unsalted_list, salted_list)
    print(f"  ✅ {path4}")

    return comparison, salt_impact, estimations


# ====================================================================== #
#  İNTERAKTİF MOD
# ====================================================================== #
def interactive_mode():
    """Kullanıcının kendi şifrelerini test edebileceği interaktif mod."""
    print_header("İNTERAKTİF MOD")

    hasher = BLAKE3Hasher()
    attacker = BruteForceAttacker()

    while True:
        print("\n  Seçenekler:")
        print("  1) Bir şifreyi hashle (salt'lı ve salt'sız)")
        print("  2) Bir şifreye brute-force dene")
        print("  3) Rainbow table demo")
        print("  4) Çıkış")

        choice = input("\n  Seçiminiz (1-4): ").strip()

        if choice == "1":
            pwd = input("  Şifreyi girin: ").strip()
            if not pwd:
                continue

            print(f"\n  Salt'sız BLAKE3 : {hasher.hash_without_salt(pwd)}")
            h, s = hasher.hash_with_salt(pwd)
            print(f"  Salt'lı BLAKE3  : {h}")
            print(f"  Salt (hex)      : {s.hex()}")
            print(f"  SHA-256         : {BLAKE3Hasher.sha256_hash(pwd)}")

        elif choice == "2":
            pwd = input("  Kırılacak şifreyi girin (max 4 karakter): ").strip()
            if not pwd or len(pwd) > 4:
                print("  ⚠️  Lütfen 1-4 karakter arası bir şifre girin.")
                continue

            target = hasher.hash_without_salt(pwd)
            print(f"  Hedef hash: {target}")
            print(f"  Brute-force başlıyor...")

            result = attacker.brute_force_unsalted(target, max_length=len(pwd))
            if result["success"]:
                print(f"  ✅ Kırıldı! Şifre: '{result['password']}'")
                print(f"     {result['attempts']:,} denemede, {result['time_seconds']:.4f} saniyede")
            else:
                print(f"  ❌ Kırılamadı ({result['attempts']:,} deneme)")

        elif choice == "3":
            print(f"\n  {len(COMMON_PASSWORDS)} yaygın şifreyle rainbow table oluşturuluyor...")
            rt, build_time = attacker.build_rainbow_table(COMMON_PASSWORDS)
            print(f"  Rainbow table hazır ({build_time:.4f} sn)")

            pwd = input("  Test şifresini girin: ").strip()
            h = hasher.hash_without_salt(pwd)
            result = attacker.rainbow_table_lookup(h, rt)
            if result["success"]:
                print(f"  ⚠️  BULUNDU! Rainbow table'da mevcut: '{result['password']}'")
                print(f"     Arama süresi: {result['lookup_time_seconds']:.9f} saniye (anlık!)")
            else:
                print(f"  ✅ Bulunamadı. Bu şifre rainbow table'da yok.")

        elif choice == "4":
            print("  Çıkış yapılıyor...")
            break
        else:
            print("  Geçersiz seçim!")


# ====================================================================== #
#  ANA FONKSİYON
# ====================================================================== #
def main():
    parser = argparse.ArgumentParser(
        description="Brute-Force Defender: BLAKE3 Salt Mekanizması Demonstrasyonu",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python main.py              Tüm demoları çalıştır
  python main.py --demo 1     Sadece Demo 1 (Hash Temelleri)
  python main.py --demo 3     Sadece Demo 3 (Saldırı Simülasyonu)
  python main.py --benchmark  Sadece benchmark testi
  python main.py --interactive İnteraktif mod
        """
    )
    parser.add_argument('--demo', type=int, choices=[1, 2, 3, 4, 5],
                        help='Belirli bir demo numarası çalıştır (1-5)')
    parser.add_argument('--benchmark', action='store_true',
                        help='Sadece benchmark testlerini çalıştır')
    parser.add_argument('--interactive', action='store_true',
                        help='İnteraktif modu başlat')

    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║           🛡️  BRUTE-FORCE DEFENDER  🛡️                      ║
    ║                                                              ║
    ║   BLAKE3 Tuzlama (Salting) Mekanizması Demonstrasyonu       ║
    ║   Tersine Mühendislik Dersi - Vize Projesi                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    if args.interactive:
        interactive_mode()
        return

    if args.benchmark:
        demo5_benchmark_and_visualize()
        return

    if args.demo:
        demos = {
            1: demo1_hash_basics,
            2: demo2_database_simulation,
            3: lambda: demo3_attack_simulation(),
            4: demo4_brute_force,
            5: demo5_benchmark_and_visualize,
        }
        demos[args.demo]()
        return

    # Tam demo (hepsini çalıştır)
    print("  Tüm demolar sırasıyla çalıştırılacak...\n")

    demo1_hash_basics()
    db = demo2_database_simulation()
    r_unsalted, r_salted, multi_unsalted, multi_salted = demo3_attack_simulation(db)
    bf_unsalted, bf_salted = demo4_brute_force()
    comparison, salt_impact, estimations = demo5_benchmark_and_visualize()

    # Saldırı grafikleri
    viz = ResultVisualizer(output_dir="results")
    viz.plot_attack_comparison(r_unsalted, r_salted)
    viz.plot_rainbow_table_effect(multi_unsalted, multi_salted)

    print_header("TÜM DEMOLAR TAMAMLANDI")
    print("  Grafikler 'results/' dizinine kaydedildi.")
    print("  İnteraktif mod için: python main.py --interactive")

    # Sonuçları JSON olarak kaydet
    all_results = {
        "attack_single_unsalted": r_unsalted,
        "attack_single_salted": r_salted,
        "attack_multi_unsalted": multi_unsalted,
        "attack_multi_salted": multi_salted,
        "bruteforce_unsalted": bf_unsalted,
        "bruteforce_salted": bf_salted,
        "blake3_vs_sha256": comparison,
    }
    results_path = os.path.join("results", "all_results.json")
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"  Tüm sonuçlar '{results_path}' dosyasına kaydedildi.")


if __name__ == "__main__":
    main()
