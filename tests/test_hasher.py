"""
test_hasher.py - BLAKE3Hasher birim testleri
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hasher import BLAKE3Hasher


class TestBLAKE3Hasher(unittest.TestCase):

    def setUp(self):
        self.hasher = BLAKE3Hasher(salt_length=16)

    # --- Salt'sız Hash Testleri ---
    def test_hash_without_salt_deterministic(self):
        """Aynı girdi her zaman aynı hash üretmeli."""
        h1 = self.hasher.hash_without_salt("test123")
        h2 = self.hasher.hash_without_salt("test123")
        self.assertEqual(h1, h2)

    def test_hash_without_salt_different_inputs(self):
        """Farklı girdiler farklı hash üretmeli."""
        h1 = self.hasher.hash_without_salt("password1")
        h2 = self.hasher.hash_without_salt("password2")
        self.assertNotEqual(h1, h2)

    def test_hash_without_salt_format(self):
        """Hash çıktısı 64 karakter hex string olmalı."""
        h = self.hasher.hash_without_salt("test")
        self.assertEqual(len(h), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in h))

    # --- Salt'lı Hash Testleri ---
    def test_hash_with_salt_different_each_time(self):
        """Aynı şifre farklı salt ile farklı hash üretmeli."""
        h1, s1 = self.hasher.hash_with_salt("test123")
        h2, s2 = self.hasher.hash_with_salt("test123")
        self.assertNotEqual(h1, h2)  # Farklı salt → farklı hash
        self.assertNotEqual(s1, s2)  # Farklı salt

    def test_hash_with_salt_same_salt_deterministic(self):
        """Aynı şifre + aynı salt = aynı hash."""
        salt = self.hasher.generate_salt()
        h1, _ = self.hasher.hash_with_salt("test123", salt=salt)
        h2, _ = self.hasher.hash_with_salt("test123", salt=salt)
        self.assertEqual(h1, h2)

    def test_salt_length(self):
        """Salt doğru uzunlukta olmalı."""
        salt = self.hasher.generate_salt()
        self.assertEqual(len(salt), 16)

        hasher32 = BLAKE3Hasher(salt_length=32)
        salt32 = hasher32.generate_salt()
        self.assertEqual(len(salt32), 32)

    # --- Doğrulama Testleri ---
    def test_verify_without_salt_correct(self):
        """Doğru şifre doğrulanmalı."""
        h = self.hasher.hash_without_salt("secret")
        self.assertTrue(self.hasher.verify_without_salt("secret", h))

    def test_verify_without_salt_wrong(self):
        """Yanlış şifre reddedilmeli."""
        h = self.hasher.hash_without_salt("secret")
        self.assertFalse(self.hasher.verify_without_salt("wrong", h))

    def test_verify_with_salt_correct(self):
        """Salt'lı doğru şifre doğrulanmalı."""
        h, salt = self.hasher.hash_with_salt("secret")
        self.assertTrue(self.hasher.verify_with_salt("secret", h, salt))

    def test_verify_with_salt_wrong(self):
        """Salt'lı yanlış şifre reddedilmeli."""
        h, salt = self.hasher.hash_with_salt("secret")
        self.assertFalse(self.hasher.verify_with_salt("wrong", h, salt))

    def test_verify_with_wrong_salt(self):
        """Yanlış salt ile doğru şifre bile reddedilmeli."""
        h, salt = self.hasher.hash_with_salt("secret")
        wrong_salt = self.hasher.generate_salt()
        self.assertFalse(self.hasher.verify_with_salt("secret", h, wrong_salt))

    # --- Keyed Hash Testleri ---
    def test_keyed_hash(self):
        """Keyed hash çalışmalı."""
        h, key = self.hasher.hash_with_key("test")
        self.assertEqual(len(h), 64)
        self.assertEqual(len(key), 32)

    def test_keyed_hash_same_key_deterministic(self):
        """Aynı key ile aynı hash üretilmeli."""
        _, key = self.hasher.hash_with_key("test")
        h1, _ = self.hasher.hash_with_key("test", key=key)
        h2, _ = self.hasher.hash_with_key("test", key=key)
        self.assertEqual(h1, h2)

    # --- SHA-256 Karşılaştırma ---
    def test_sha256_hash(self):
        """SHA-256 hash doğru formatta olmalı."""
        h = BLAKE3Hasher.sha256_hash("test")
        self.assertEqual(len(h), 64)

    def test_blake3_sha256_different(self):
        """BLAKE3 ve SHA-256 farklı hash üretmeli."""
        b3 = self.hasher.hash_without_salt("test")
        sha = BLAKE3Hasher.sha256_hash("test")
        self.assertNotEqual(b3, sha)


if __name__ == '__main__':
    unittest.main()
