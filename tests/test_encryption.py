import unittest
from src.encryption import encrypt_data, decrypt_data

class TestEncryption(unittest.TestCase):
    def test_encrypt_decrypt(self):
        original_data = "This is a test message."
        encrypted = encrypt_data(original_data)
        decrypted = decrypt_data(encrypted)
        self.assertEqual(original_data, decrypted)

    def test_different_encryptions(self):
        data = "This is a test message."
        encryption1 = encrypt_data(data)
        encryption2 = encrypt_data(data)
        self.assertNotEqual(encryption1, encryption2)

if __name__ == '__main__':
    unittest.main()