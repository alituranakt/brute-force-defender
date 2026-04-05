"""
hasher.py - BLAKE3 Hash İşlemleri Modülü
=========================================
Bu modül BLAKE3 algoritması kullanarak:
- Salt'sız (tuzlanmamış) hash oluşturma
- Salt'lı (tuzlanmış) hash oluşturma
- Hash doğrulama işlemlerini gerçekleştirir.

Tersine Mühendislik Dersi - Vize Projesi
"""

import blake3
import os
import hashlib
from typing import Tuple, Optional


class BLAKE3Hasher:
    """BLAKE3 hash algoritması ile şifreleme işlemleri."""

    def __init__(self, salt_length: int = 16):
        """
        Args:
            salt_length: Oluşturulacak salt'ın byte uzunluğu (varsayılan: 16 byte = 128 bit)
        """
        self.salt_length = salt_length

    # ------------------------------------------------------------------ #
    #  Salt Üretimi
    # ------------------------------------------------------------------ #
    def generate_salt(self) -> bytes:
        """Kriptografik olarak güvenli rastgele salt üretir.

        os.urandom() işletim sisteminin CSPRNG'sini (Cryptographically Secure
        Pseudo-Random Number Generator) kullanır.

        Returns:
            Rastgele byte dizisi (salt)
        """
        return os.urandom(self.salt_length)

    # ------------------------------------------------------------------ #
    #  Salt'sız Hash (Güvensiz Yöntem)
    # ------------------------------------------------------------------ #
    def hash_without_salt(self, password: str) -> str:
        """Şifreyi salt EKLEMEDEN BLAKE3 ile hashler.

        ⚠️  DİKKAT: Bu yöntem güvensizdir!
        Aynı şifre her zaman aynı hash'i üretir → Rainbow table saldırısına açık.

        Args:
            password: Hashlenecek düz metin şifre

        Returns:
            Hex formatında BLAKE3 hash değeri
        """
        hasher = blake3.blake3(password.encode('utf-8'))
        return hasher.hexdigest()

    # ------------------------------------------------------------------ #
    #  Salt'lı Hash (Güvenli Yöntem)
    # ------------------------------------------------------------------ #
    def hash_with_salt(self, password: str, salt: Optional[bytes] = None) -> Tuple[str, bytes]:
        """Şifreyi salt EKLEYEREK BLAKE3 ile hashler.

        ✅  GÜVENLİ YÖNTEM: Her kullanıcıya benzersiz salt atanır.
        Aynı şifre farklı salt ile farklı hash üretir → Rainbow table etkisiz.

        İşlem: BLAKE3(salt + password)

        Args:
            password: Hashlenecek düz metin şifre
            salt: Kullanılacak salt (None ise otomatik üretilir)

        Returns:
            (hash_hex, salt) tuple'ı
        """
        if salt is None:
            salt = self.generate_salt()

        # Salt + password birleştirilir
        salted_input = salt + password.encode('utf-8')
        hasher = blake3.blake3(salted_input)

        return hasher.hexdigest(), salt

    # ------------------------------------------------------------------ #
    #  Keyed Hash (BLAKE3'e Özgü - HMAC Alternatifi)
    # ------------------------------------------------------------------ #
    def hash_with_key(self, password: str, key: Optional[bytes] = None) -> Tuple[str, bytes]:
        """BLAKE3'ün yerleşik keyed hash özelliğini kullanır.

        BLAKE3, HMAC'a gerek kalmadan doğrudan anahtar tabanlı hash destekler.
        Bu, BLAKE3'ün diğer hash algoritmalarından ayırt edici özelliklerinden biridir.

        Args:
            password: Hashlenecek düz metin şifre
            key: 32-byte anahtar (None ise otomatik üretilir)

        Returns:
            (hash_hex, key) tuple'ı
        """
        if key is None:
            key = os.urandom(32)  # BLAKE3 keyed hash tam olarak 32 byte ister

        hasher = blake3.blake3(password.encode('utf-8'), key=key)
        return hasher.hexdigest(), key

    # ------------------------------------------------------------------ #
    #  Hash Doğrulama
    # ------------------------------------------------------------------ #
    def verify_without_salt(self, password: str, expected_hash: str) -> bool:
        """Salt'sız hash doğrulama."""
        return self.hash_without_salt(password) == expected_hash

    def verify_with_salt(self, password: str, expected_hash: str, salt: bytes) -> bool:
        """Salt'lı hash doğrulama."""
        computed_hash, _ = self.hash_with_salt(password, salt=salt)
        return computed_hash == expected_hash

    # ------------------------------------------------------------------ #
    #  Karşılaştırma: SHA-256 vs BLAKE3
    # ------------------------------------------------------------------ #
    @staticmethod
    def sha256_hash(password: str) -> str:
        """SHA-256 ile hash (karşılaştırma için)."""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

    @staticmethod
    def sha256_hash_with_salt(password: str, salt: bytes) -> str:
        """SHA-256 ile salt'lı hash (karşılaştırma için)."""
        return hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
