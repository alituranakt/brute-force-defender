"""
benchmark.py - Performans Ölçüm ve Karşılaştırma Modülü
=========================================================
BLAKE3 hash performansını çeşitli senaryolarda ölçer:
  - Salt'lı vs Salt'sız hashing hızı
  - BLAKE3 vs SHA-256 karşılaştırması
  - Farklı salt uzunluklarının etkisi
  - Saldırı süresi projeksiyonları

Tersine Mühendislik Dersi - Vize Projesi
"""

import time
import statistics
import string
from typing import Dict, List
from src.hasher import BLAKE3Hasher


class PerformanceBenchmark:
    """Hash performans ölçüm aracı."""

    def __init__(self):
        self.hasher = BLAKE3Hasher()

    # ------------------------------------------------------------------ #
    #  Hash Hızı Ölçümü
    # ------------------------------------------------------------------ #
    def measure_hash_speed(
        self,
        iterations: int = 100000,
        password: str = "test_password_123"
    ) -> Dict:
        """Salt'lı ve salt'sız hash hızlarını ölçer.

        Args:
            iterations: Tekrar sayısı
            password: Test şifresi

        Returns:
            Performans raporu
        """
        # Salt'sız hash hızı
        start = time.perf_counter()
        for _ in range(iterations):
            self.hasher.hash_without_salt(password)
        unsalted_time = time.perf_counter() - start

        # Salt'lı hash hızı (her seferinde yeni salt)
        start = time.perf_counter()
        for _ in range(iterations):
            self.hasher.hash_with_salt(password)
        salted_new_salt_time = time.perf_counter() - start

        # Salt'lı hash hızı (sabit salt)
        salt = self.hasher.generate_salt()
        start = time.perf_counter()
        for _ in range(iterations):
            self.hasher.hash_with_salt(password, salt=salt)
        salted_fixed_time = time.perf_counter() - start

        return {
            "iterations": iterations,
            "unsalted": {
                "total_seconds": round(unsalted_time, 4),
                "hashes_per_second": round(iterations / unsalted_time),
            },
            "salted_new_salt": {
                "total_seconds": round(salted_new_salt_time, 4),
                "hashes_per_second": round(iterations / salted_new_salt_time),
            },
            "salted_fixed_salt": {
                "total_seconds": round(salted_fixed_time, 4),
                "hashes_per_second": round(iterations / salted_fixed_time),
            },
        }

    # ------------------------------------------------------------------ #
    #  BLAKE3 vs SHA-256 Karşılaştırması
    # ------------------------------------------------------------------ #
    def blake3_vs_sha256(
        self,
        iterations: int = 100000,
        password: str = "benchmark_password"
    ) -> Dict:
        """BLAKE3 ve SHA-256 hız karşılaştırması.

        Args:
            iterations: Tekrar sayısı
            password: Test şifresi

        Returns:
            Karşılaştırma raporu
        """
        # BLAKE3
        start = time.perf_counter()
        for _ in range(iterations):
            self.hasher.hash_without_salt(password)
        blake3_time = time.perf_counter() - start

        # SHA-256
        start = time.perf_counter()
        for _ in range(iterations):
            BLAKE3Hasher.sha256_hash(password)
        sha256_time = time.perf_counter() - start

        # Salt'lı versiyonlar
        salt = self.hasher.generate_salt()

        start = time.perf_counter()
        for _ in range(iterations):
            self.hasher.hash_with_salt(password, salt=salt)
        blake3_salted_time = time.perf_counter() - start

        start = time.perf_counter()
        for _ in range(iterations):
            BLAKE3Hasher.sha256_hash_with_salt(password, salt)
        sha256_salted_time = time.perf_counter() - start

        return {
            "iterations": iterations,
            "blake3": {
                "unsalted_seconds": round(blake3_time, 4),
                "salted_seconds": round(blake3_salted_time, 4),
                "unsalted_hps": round(iterations / blake3_time),
                "salted_hps": round(iterations / blake3_salted_time),
            },
            "sha256": {
                "unsalted_seconds": round(sha256_time, 4),
                "salted_seconds": round(sha256_salted_time, 4),
                "unsalted_hps": round(iterations / sha256_time),
                "salted_hps": round(iterations / sha256_salted_time),
            },
            "blake3_speedup": round(sha256_time / blake3_time, 2),
        }

    # ------------------------------------------------------------------ #
    #  Salt Uzunluğu Etkisi
    # ------------------------------------------------------------------ #
    def salt_length_impact(
        self,
        salt_lengths: List[int] = None,
        iterations: int = 50000,
        password: str = "salt_test_pwd"
    ) -> Dict:
        """Farklı salt uzunluklarının hash hızına etkisini ölçer.

        Args:
            salt_lengths: Test edilecek salt uzunlukları (byte)
            iterations: Tekrar sayısı
            password: Test şifresi

        Returns:
            Salt uzunluğu etki raporu
        """
        if salt_lengths is None:
            salt_lengths = [4, 8, 16, 32, 64, 128]

        results = {}
        for length in salt_lengths:
            hasher = BLAKE3Hasher(salt_length=length)
            salt = hasher.generate_salt()

            start = time.perf_counter()
            for _ in range(iterations):
                hasher.hash_with_salt(password, salt=salt)
            elapsed = time.perf_counter() - start

            results[length] = {
                "salt_bytes": length,
                "salt_bits": length * 8,
                "total_seconds": round(elapsed, 4),
                "hashes_per_second": round(iterations / elapsed),
                "keyspace": f"2^{length * 8}",
            }

        return {"iterations": iterations, "results": results}

    # ------------------------------------------------------------------ #
    #  Saldırı Süresi Projeksiyonu
    # ------------------------------------------------------------------ #
    def estimate_crack_time(
        self,
        password_length: int = 8,
        charset_size: int = 62,  # a-z + A-Z + 0-9
        hashes_per_second: int = None,
        num_users: int = 1
    ) -> Dict:
        """Şifre kırma süresi tahmini.

        Args:
            password_length: Hedef şifre uzunluğu
            charset_size: Karakter seti büyüklüğü
            hashes_per_second: Saniyede hash sayısı (None ise ölçülür)
            num_users: Hedef kullanıcı sayısı

        Returns:
            Süre tahmini raporu
        """
        if hashes_per_second is None:
            bench = self.measure_hash_speed(iterations=50000)
            hashes_per_second = bench["unsalted"]["hashes_per_second"]

        total_combinations = charset_size ** password_length

        # Salt'sız: Rainbow table bir kez oluştur, tüm kullanıcıları kır
        unsalted_build_seconds = total_combinations / hashes_per_second
        unsalted_total = unsalted_build_seconds  # Tüm kullanıcılar için aynı süre

        # Salt'lı: Her kullanıcı için ayrı saldırı gerekli
        salted_per_user = total_combinations / hashes_per_second
        salted_total = salted_per_user * num_users

        def format_time(seconds: float) -> str:
            if seconds < 60:
                return f"{seconds:.1f} saniye"
            elif seconds < 3600:
                return f"{seconds / 60:.1f} dakika"
            elif seconds < 86400:
                return f"{seconds / 3600:.1f} saat"
            elif seconds < 86400 * 365:
                return f"{seconds / 86400:.1f} gün"
            else:
                return f"{seconds / (86400 * 365):.1f} yıl"

        return {
            "password_length": password_length,
            "charset_size": charset_size,
            "total_combinations": total_combinations,
            "hashes_per_second": hashes_per_second,
            "num_users": num_users,
            "unsalted": {
                "total_seconds": round(unsalted_total, 2),
                "human_readable": format_time(unsalted_total),
                "note": "Rainbow table bir kez oluşturulur, tüm kullanıcılar anında kırılır",
            },
            "salted": {
                "per_user_seconds": round(salted_per_user, 2),
                "total_seconds": round(salted_total, 2),
                "human_readable": format_time(salted_total),
                "note": f"Her kullanıcı için ayrı saldırı: {num_users} × {format_time(salted_per_user)}",
            },
            "salt_multiplier": f"{num_users}x daha yavaş (salt'lı)",
        }
