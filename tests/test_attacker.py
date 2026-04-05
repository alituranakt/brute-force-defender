"""
test_attacker.py - BruteForceAttacker birim testleri
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.hasher import BLAKE3Hasher
from src.attacker import BruteForceAttacker


class TestBruteForceAttacker(unittest.TestCase):

    def setUp(self):
        self.hasher = BLAKE3Hasher()
        self.attacker = BruteForceAttacker()
        self.wordlist = ["123456", "password", "qwerty", "admin", "letmein"]

    # --- Sözlük Saldırısı ---
    def test_dictionary_unsalted_found(self):
        """Salt'sız hash sözlükte bulunmalı."""
        target = self.hasher.hash_without_salt("password")
        result = self.attacker.dictionary_attack_unsalted(target, self.wordlist)
        self.assertTrue(result["success"])
        self.assertEqual(result["password"], "password")

    def test_dictionary_unsalted_not_found(self):
        """Sözlükte olmayan şifre bulunammalı."""
        target = self.hasher.hash_without_salt("xyz_not_in_list")
        result = self.attacker.dictionary_attack_unsalted(target, self.wordlist)
        self.assertFalse(result["success"])

    def test_dictionary_salted_found(self):
        """Salt'lı hash sözlükte bulunmalı."""
        target, salt = self.hasher.hash_with_salt("qwerty")
        result = self.attacker.dictionary_attack_salted(target, salt, self.wordlist)
        self.assertTrue(result["success"])
        self.assertEqual(result["password"], "qwerty")

    # --- Brute-Force ---
    def test_bruteforce_unsalted_short(self):
        """Kısa şifre brute-force ile kırılmalı."""
        target = self.hasher.hash_without_salt("ab")
        result = self.attacker.brute_force_unsalted(target, max_length=2)
        self.assertTrue(result["success"])
        self.assertEqual(result["password"], "ab")

    def test_bruteforce_salted_short(self):
        """Kısa salt'lı şifre brute-force ile kırılmalı."""
        target, salt = self.hasher.hash_with_salt("a1")
        result = self.attacker.brute_force_salted(target, salt, max_length=2)
        self.assertTrue(result["success"])
        self.assertEqual(result["password"], "a1")

    # --- Rainbow Table ---
    def test_rainbow_table_build(self):
        """Rainbow table doğru oluşturulmalı."""
        rt, build_time = self.attacker.build_rainbow_table(self.wordlist)
        self.assertEqual(len(rt), len(self.wordlist))
        self.assertGreater(build_time, 0)

    def test_rainbow_table_lookup_found(self):
        """Rainbow table'da var olan şifre bulunmalı."""
        rt, _ = self.attacker.build_rainbow_table(self.wordlist)
        target = self.hasher.hash_without_salt("admin")
        result = self.attacker.rainbow_table_lookup(target, rt)
        self.assertTrue(result["success"])
        self.assertEqual(result["password"], "admin")

    def test_rainbow_table_lookup_not_found(self):
        """Rainbow table'da olmayan şifre bulunamaMALI."""
        rt, _ = self.attacker.build_rainbow_table(self.wordlist)
        target = self.hasher.hash_without_salt("not_in_table")
        result = self.attacker.rainbow_table_lookup(target, rt)
        self.assertFalse(result["success"])


if __name__ == '__main__':
    unittest.main()
