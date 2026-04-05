"""
test_database.py - UserDatabase birim testleri
"""

import unittest
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import UserDatabase


class TestUserDatabase(unittest.TestCase):

    def setUp(self):
        self.db = UserDatabase()
        self.test_users = {
            "user1": "pass1",
            "user2": "pass2",
            "user3": "pass1",  # user1 ile aynı şifre
        }

    def test_add_user_unsalted(self):
        """Salt'sız kullanıcı ekleme."""
        h = self.db.add_user_unsalted("test", "password")
        self.assertIn("test", self.db.unsalted_users)
        self.assertEqual(len(h), 64)

    def test_add_user_salted(self):
        """Salt'lı kullanıcı ekleme."""
        h, salt = self.db.add_user_salted("test", "password")
        self.assertIn("test", self.db.salted_users)
        self.assertEqual(len(h), 64)

    def test_populate_demo_users(self):
        """Toplu kullanıcı ekleme."""
        self.db.populate_demo_users(self.test_users)
        self.assertEqual(len(self.db.unsalted_users), 3)
        self.assertEqual(len(self.db.salted_users), 3)

    def test_duplicate_hashes_unsalted(self):
        """Aynı şifre kullanıcıları salt'sız tabloda aynı hash'e sahip olmalı."""
        self.db.populate_demo_users(self.test_users)
        duplicates = self.db.find_duplicate_hashes_unsalted()
        self.assertGreater(len(duplicates), 0)
        # user1 ve user3 aynı şifreyi kullanıyor
        found = False
        for h, users in duplicates.items():
            if "user1" in users and "user3" in users:
                found = True
        self.assertTrue(found)

    def test_no_duplicate_hashes_salted(self):
        """Salt'lı tabloda duplicate hash olmamalı."""
        self.db.populate_demo_users(self.test_users)
        duplicates = self.db.find_duplicate_hashes_salted()
        self.assertEqual(len(duplicates), 0)

    def test_verify_login_unsalted(self):
        """Salt'sız giriş doğrulama."""
        self.db.add_user_unsalted("test", "secret")
        self.assertTrue(self.db.verify_login_unsalted("test", "secret"))
        self.assertFalse(self.db.verify_login_unsalted("test", "wrong"))

    def test_verify_login_salted(self):
        """Salt'lı giriş doğrulama."""
        self.db.add_user_salted("test", "secret")
        self.assertTrue(self.db.verify_login_salted("test", "secret"))
        self.assertFalse(self.db.verify_login_salted("test", "wrong"))

    def test_save_and_load(self):
        """Diske kaydet ve yükle."""
        self.db.populate_demo_users(self.test_users)
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name

        try:
            self.db.save_to_disk(path)
            new_db = UserDatabase()
            new_db.load_from_disk(path)
            self.assertEqual(len(new_db.unsalted_users), 3)
            self.assertEqual(len(new_db.salted_users), 3)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
