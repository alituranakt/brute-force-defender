"""
attacker.py - Brute-Force Saldırı Simülatörü
==============================================
Bu modül brute-force saldırı senaryolarını simüle eder:
  1. Salt'sız hash'lere karşı sözlük saldırısı
  2. Salt'lı hash'lere karşı sözlük saldırısı
  3. Rainbow table saldırısı simülasyonu
  4. Performans karşılaştırması

Tersine Mühendislik Dersi - Vize Projesi
"""

import time
import itertools
import string
from typing import Dict, List, Tuple, Optional, Callable
from src.hasher import BLAKE3Hasher


class BruteForceAttacker:
    """Brute-force saldırı simülasyonu."""

    def __init__(self):
        self.hasher = BLAKE3Hasher()
        self.attempts = 0
        self.start_time = 0.0
        self.end_time = 0.0

    def _reset_stats(self):
        """Saldırı istatistiklerini sıfırlar."""
        self.attempts = 0
        self.start_time = time.perf_counter()
        self.end_time = 0.0

    def _elapsed(self) -> float:
        """Geçen süreyi saniye olarak döndürür."""
        return self.end_time - self.start_time

    # ================================================================== #
    #  SÖZLÜK SALDIRISI (Dictionary Attack)
    # ================================================================== #
    def dictionary_attack_unsalted(
        self,
        target_hash: str,
        wordlist: List[str],
        verbose: bool = False
    ) -> Dict:
        """Salt'sız hash'e karşı sözlük saldırısı.

        Her kelimeyi hashleyip hedef hash ile karşılaştırır.
        Salt olmadığı için tek bir hash hesaplaması yeterlidir.

        Args:
            target_hash: Kırılmak istenen hash değeri
            wordlist: Denenecek şifre listesi
            verbose: Detaylı çıktı göster

        Returns:
            Saldırı sonuç raporu
        """
        self._reset_stats()

        found_password = None
        for password in wordlist:
            self.attempts += 1
            computed_hash = self.hasher.hash_without_salt(password)

            if verbose and self.attempts % 10000 == 0:
                print(f"  [{self.attempts:>8,}] deneme yapıldı...")

            if computed_hash == target_hash:
                found_password = password
                break

        self.end_time = time.perf_counter()

        return {
            "success": found_password is not None,
            "password": found_password,
            "attempts": self.attempts,
            "time_seconds": round(self._elapsed(), 6),
            "hashes_per_second": round(self.attempts / max(self._elapsed(), 0.000001)),
            "method": "Dictionary Attack (Salt'sız)",
        }

    def dictionary_attack_salted(
        self,
        target_hash: str,
        salt: bytes,
        wordlist: List[str],
        verbose: bool = False
    ) -> Dict:
        """Salt'lı hash'e karşı sözlük saldırısı.

        Her kelime için salt ile birlikte hash hesaplanmalıdır.
        Her kullanıcının farklı salt'ı olduğundan, önceden hesaplanmış
        hash tabloları (rainbow table) kullanılamaz.

        Args:
            target_hash: Kırılmak istenen hash değeri
            salt: Kullanıcıya ait salt değeri
            wordlist: Denenecek şifre listesi
            verbose: Detaylı çıktı göster

        Returns:
            Saldırı sonuç raporu
        """
        self._reset_stats()

        found_password = None
        for password in wordlist:
            self.attempts += 1
            computed_hash, _ = self.hasher.hash_with_salt(password, salt=salt)

            if verbose and self.attempts % 10000 == 0:
                print(f"  [{self.attempts:>8,}] deneme yapıldı...")

            if computed_hash == target_hash:
                found_password = password
                break

        self.end_time = time.perf_counter()

        return {
            "success": found_password is not None,
            "password": found_password,
            "attempts": self.attempts,
            "time_seconds": round(self._elapsed(), 6),
            "hashes_per_second": round(self.attempts / max(self._elapsed(), 0.000001)),
            "method": "Dictionary Attack (Salt'lı)",
        }

    # ================================================================== #
    #  BRUTE-FORCE SALDIRISI (Tüm Kombinasyonlar)
    # ================================================================== #
    def brute_force_unsalted(
        self,
        target_hash: str,
        charset: str = string.ascii_lowercase + string.digits,
        max_length: int = 4,
        verbose: bool = False
    ) -> Dict:
        """Salt'sız hash'e karşı kaba kuvvet saldırısı.

        Belirtilen karakter setindeki tüm olası kombinasyonları dener.

        Args:
            target_hash: Kırılmak istenen hash
            charset: Kullanılacak karakter seti
            max_length: Maksimum şifre uzunluğu
            verbose: Detaylı çıktı

        Returns:
            Saldırı sonuç raporu
        """
        self._reset_stats()

        found_password = None
        total_combinations = sum(len(charset) ** i for i in range(1, max_length + 1))

        for length in range(1, max_length + 1):
            for combo in itertools.product(charset, repeat=length):
                self.attempts += 1
                candidate = ''.join(combo)
                computed_hash = self.hasher.hash_without_salt(candidate)

                if verbose and self.attempts % 50000 == 0:
                    progress = (self.attempts / total_combinations) * 100
                    print(f"  [{self.attempts:>10,}/{total_combinations:,}] "
                          f"(%{progress:.1f}) Deneniyor: {candidate}")

                if computed_hash == target_hash:
                    found_password = candidate
                    break
            if found_password:
                break

        self.end_time = time.perf_counter()

        return {
            "success": found_password is not None,
            "password": found_password,
            "attempts": self.attempts,
            "total_possible": total_combinations,
            "time_seconds": round(self._elapsed(), 6),
            "hashes_per_second": round(self.attempts / max(self._elapsed(), 0.000001)),
            "method": f"Brute-Force (Salt'sız, max_len={max_length})",
        }

    def brute_force_salted(
        self,
        target_hash: str,
        salt: bytes,
        charset: str = string.ascii_lowercase + string.digits,
        max_length: int = 4,
        verbose: bool = False
    ) -> Dict:
        """Salt'lı hash'e karşı kaba kuvvet saldırısı.

        Args:
            target_hash: Kırılmak istenen hash
            salt: Kullanıcıya ait salt
            charset: Kullanılacak karakter seti
            max_length: Maksimum şifre uzunluğu
            verbose: Detaylı çıktı

        Returns:
            Saldırı sonuç raporu
        """
        self._reset_stats()

        found_password = None
        total_combinations = sum(len(charset) ** i for i in range(1, max_length + 1))

        for length in range(1, max_length + 1):
            for combo in itertools.product(charset, repeat=length):
                self.attempts += 1
                candidate = ''.join(combo)
                computed_hash, _ = self.hasher.hash_with_salt(candidate, salt=salt)

                if verbose and self.attempts % 50000 == 0:
                    progress = (self.attempts / total_combinations) * 100
                    print(f"  [{self.attempts:>10,}/{total_combinations:,}] "
                          f"(%{progress:.1f}) Deneniyor: {candidate}")

                if computed_hash == target_hash:
                    found_password = candidate
                    break
            if found_password:
                break

        self.end_time = time.perf_counter()

        return {
            "success": found_password is not None,
            "password": found_password,
            "attempts": self.attempts,
            "total_possible": total_combinations,
            "time_seconds": round(self._elapsed(), 6),
            "hashes_per_second": round(self.attempts / max(self._elapsed(), 0.000001)),
            "method": f"Brute-Force (Salt'lı, max_len={max_length})",
        }

    # ================================================================== #
    #  RAINBOW TABLE SALDIRISI SİMÜLASYONU
    # ================================================================== #
    def build_rainbow_table(
        self,
        wordlist: List[str],
        verbose: bool = False
    ) -> Tuple[Dict[str, str], float]:
        """Rainbow table (önceden hesaplanmış hash tablosu) oluşturur.

        Bu tablo, salt'sız hash'lere karşı anında eşleşme sağlar.
        Salt'lı hash'lere karşı ise İŞE YARAMAZ çünkü her kullanıcının
        farklı salt değeri vardır.

        Args:
            wordlist: Hash'lenecek şifre listesi
            verbose: Detaylı çıktı

        Returns:
            (rainbow_table, build_time) → {hash: password} sözlüğü ve oluşturma süresi
        """
        start = time.perf_counter()
        rainbow_table: Dict[str, str] = {}

        for i, password in enumerate(wordlist):
            hash_val = self.hasher.hash_without_salt(password)
            rainbow_table[hash_val] = password

            if verbose and (i + 1) % 10000 == 0:
                print(f"  Rainbow table: {i + 1:,}/{len(wordlist):,} hash hesaplandı")

        build_time = time.perf_counter() - start
        return rainbow_table, build_time

    def rainbow_table_lookup(
        self,
        target_hash: str,
        rainbow_table: Dict[str, str]
    ) -> Dict:
        """Rainbow table ile anlık hash eşleşmesi.

        O(1) karmaşıklığında arama - salt'sız hash'ler için yıkıcı.

        Args:
            target_hash: Aranan hash değeri
            rainbow_table: Önceden oluşturulmuş rainbow table

        Returns:
            Arama sonucu
        """
        start = time.perf_counter()
        password = rainbow_table.get(target_hash)
        lookup_time = time.perf_counter() - start

        return {
            "success": password is not None,
            "password": password,
            "lookup_time_seconds": round(lookup_time, 9),
            "table_size": len(rainbow_table),
            "method": "Rainbow Table Lookup",
        }

    # ================================================================== #
    #  ÇOKLU KULLANICI SALDIRISI KARŞILAŞTIRMASI
    # ================================================================== #
    def attack_multiple_users_unsalted(
        self,
        user_hashes: Dict[str, str],
        wordlist: List[str]
    ) -> Dict:
        """Birden fazla salt'sız hash'e aynı anda saldırı.

        Rainbow table bir kez oluşturulur, TÜM kullanıcılar anında kontrol edilir.
        Bu, salt kullanmamanın en büyük zafiyetidir.

        Args:
            user_hashes: {username: hash} sözlüğü
            wordlist: Şifre listesi

        Returns:
            Toplu saldırı raporu
        """
        # 1. Rainbow table oluştur (tek seferlik maliyet)
        rainbow_table, build_time = self.build_rainbow_table(wordlist)

        # 2. Tüm kullanıcıları kontrol et
        start = time.perf_counter()
        cracked = {}
        for username, target_hash in user_hashes.items():
            result = self.rainbow_table_lookup(target_hash, rainbow_table)
            if result["success"]:
                cracked[username] = result["password"]
        lookup_time = time.perf_counter() - start

        return {
            "total_users": len(user_hashes),
            "cracked_count": len(cracked),
            "cracked_users": cracked,
            "rainbow_build_time": round(build_time, 6),
            "total_lookup_time": round(lookup_time, 6),
            "total_time": round(build_time + lookup_time, 6),
            "method": "Rainbow Table (Çoklu Kullanıcı - Salt'sız)",
        }

    def attack_multiple_users_salted(
        self,
        user_data: Dict[str, Dict[str, str]],
        wordlist: List[str]
    ) -> Dict:
        """Birden fazla salt'lı hash'e saldırı.

        Her kullanıcı için AYRI AYRI sözlük saldırısı yapılmalıdır.
        Rainbow table KULLANILAMAZ çünkü her salt farklıdır.

        Args:
            user_data: {username: {"hash": ..., "salt": ...}} sözlüğü
            wordlist: Şifre listesi

        Returns:
            Toplu saldırı raporu
        """
        start = time.perf_counter()
        cracked = {}
        total_attempts = 0

        for username, data in user_data.items():
            salt = bytes.fromhex(data["salt"])
            result = self.dictionary_attack_salted(
                data["hash"], salt, wordlist
            )
            total_attempts += result["attempts"]
            if result["success"]:
                cracked[username] = result["password"]

        total_time = time.perf_counter() - start

        return {
            "total_users": len(user_data),
            "cracked_count": len(cracked),
            "cracked_users": cracked,
            "total_attempts": total_attempts,
            "total_time": round(total_time, 6),
            "method": "Dictionary Attack (Çoklu Kullanıcı - Salt'lı)",
        }
