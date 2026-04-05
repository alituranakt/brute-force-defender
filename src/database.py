"""
database.py - Simüle Edilmiş Kullanıcı Veritabanı
===================================================
Gerçek bir uygulamadaki kullanıcı veritabanını simüle eder.
İki tablo tutar:
  1. unsalted_users → salt'sız hash'ler (güvensiz)
  2. salted_users   → salt'lı hash'ler (güvenli)

Tersine Mühendislik Dersi - Vize Projesi
"""

import json
import os
from typing import Dict, Optional, List
from src.hasher import BLAKE3Hasher


class UserDatabase:
    """Kullanıcı şifre veritabanı simülasyonu."""

    def __init__(self, db_path: Optional[str] = None):
        self.hasher = BLAKE3Hasher(salt_length=16)

        # Salt'sız tablo: {username: hash}
        self.unsalted_users: Dict[str, str] = {}

        # Salt'lı tablo: {username: {"hash": ..., "salt": ...}}
        self.salted_users: Dict[str, Dict[str, str]] = {}

        self.db_path = db_path

    # ------------------------------------------------------------------ #
    #  Kullanıcı Ekleme
    # ------------------------------------------------------------------ #
    def add_user_unsalted(self, username: str, password: str) -> str:
        """Kullanıcıyı salt'sız hash ile ekler (GÜVENSİZ).

        Returns:
            Oluşturulan hash değeri
        """
        hash_value = self.hasher.hash_without_salt(password)
        self.unsalted_users[username] = hash_value
        return hash_value

    def add_user_salted(self, username: str, password: str) -> tuple:
        """Kullanıcıyı salt'lı hash ile ekler (GÜVENLİ).

        Returns:
            (hash_value, salt_hex) tuple'ı
        """
        hash_value, salt = self.hasher.hash_with_salt(password)
        self.salted_users[username] = {
            "hash": hash_value,
            "salt": salt.hex()  # Salt'ı hex olarak saklarız
        }
        return hash_value, salt.hex()

    # ------------------------------------------------------------------ #
    #  Toplu Kullanıcı Ekleme (Demo için)
    # ------------------------------------------------------------------ #
    def populate_demo_users(self, users: Dict[str, str]) -> None:
        """Demo kullanıcıları her iki tabloya da ekler.

        Args:
            users: {username: password} sözlüğü
        """
        for username, password in users.items():
            self.add_user_unsalted(username, password)
            self.add_user_salted(username, password)

    # ------------------------------------------------------------------ #
    #  Giriş Doğrulama
    # ------------------------------------------------------------------ #
    def verify_login_unsalted(self, username: str, password: str) -> bool:
        """Salt'sız tabloda giriş doğrulama."""
        if username not in self.unsalted_users:
            return False
        return self.hasher.verify_without_salt(password, self.unsalted_users[username])

    def verify_login_salted(self, username: str, password: str) -> bool:
        """Salt'lı tabloda giriş doğrulama."""
        if username not in self.salted_users:
            return False
        user_data = self.salted_users[username]
        salt = bytes.fromhex(user_data["salt"])
        return self.hasher.verify_with_salt(password, user_data["hash"], salt)

    # ------------------------------------------------------------------ #
    #  Veritabanı Görüntüleme
    # ------------------------------------------------------------------ #
    def get_unsalted_table(self) -> List[tuple]:
        """Salt'sız tabloyu liste olarak döndürür."""
        return [(user, h) for user, h in self.unsalted_users.items()]

    def get_salted_table(self) -> List[tuple]:
        """Salt'lı tabloyu liste olarak döndürür."""
        return [
            (user, data["hash"], data["salt"])
            for user, data in self.salted_users.items()
        ]

    # ------------------------------------------------------------------ #
    #  Diske Kaydetme / Diskten Yükleme
    # ------------------------------------------------------------------ #
    def save_to_disk(self, path: Optional[str] = None) -> None:
        """Veritabanını JSON dosyasına kaydeder."""
        path = path or self.db_path or "user_db.json"
        data = {
            "unsalted_users": self.unsalted_users,
            "salted_users": self.salted_users,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_disk(self, path: Optional[str] = None) -> None:
        """Veritabanını JSON dosyasından yükler."""
        path = path or self.db_path or "user_db.json"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Veritabanı dosyası bulunamadı: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.unsalted_users = data.get("unsalted_users", {})
        self.salted_users = data.get("salted_users", {})

    # ------------------------------------------------------------------ #
    #  İstatistikler
    # ------------------------------------------------------------------ #
    def find_duplicate_hashes_unsalted(self) -> Dict[str, List[str]]:
        """Salt'sız tabloda aynı hash'e sahip kullanıcıları bulur.

        Bu, salt kullanmamanın kritik zafiyetini gösterir:
        Aynı şifreyi kullanan kullanıcılar aynı hash'e sahip olur!
        """
        hash_to_users: Dict[str, List[str]] = {}
        for username, hash_val in self.unsalted_users.items():
            if hash_val not in hash_to_users:
                hash_to_users[hash_val] = []
            hash_to_users[hash_val].append(username)

        # Sadece birden fazla kullanıcıya sahip hash'leri döndür
        return {h: users for h, users in hash_to_users.items() if len(users) > 1}

    def find_duplicate_hashes_salted(self) -> Dict[str, List[str]]:
        """Salt'lı tabloda aynı hash'e sahip kullanıcıları bulur.

        Salt kullanıldığında, aynı şifreyi kullanan kullanıcılar bile
        farklı hash değerlerine sahip olur!
        """
        hash_to_users: Dict[str, List[str]] = {}
        for username, data in self.salted_users.items():
            h = data["hash"]
            if h not in hash_to_users:
                hash_to_users[h] = []
            hash_to_users[h].append(username)

        return {h: users for h, users in hash_to_users.items() if len(users) > 1}
