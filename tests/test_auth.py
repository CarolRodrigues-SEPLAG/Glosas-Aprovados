import hashlib
import unittest

from auth import verify_credentials


class VerifyCredentialsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.username = "equipe"
        self.password = "uma-senha-de-teste"
        self.salt = bytes.fromhex("00112233445566778899aabbccddeeff")
        self.password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            self.password.encode("utf-8"),
            self.salt,
            600_000,
        ).hex()

    def test_accepts_correct_credentials(self) -> None:
        self.assertTrue(
            verify_credentials(
                self.username,
                self.password,
                self.username,
                self.salt.hex(),
                self.password_hash,
            )
        )

    def test_rejects_incorrect_username_or_password(self) -> None:
        self.assertFalse(
            verify_credentials(
                "outra-equipe",
                self.password,
                self.username,
                self.salt.hex(),
                self.password_hash,
            )
        )
        self.assertFalse(
            verify_credentials(
                self.username,
                "senha-errada",
                self.username,
                self.salt.hex(),
                self.password_hash,
            )
        )

    def test_rejects_malformed_hash_configuration(self) -> None:
        self.assertFalse(
            verify_credentials(
                self.username,
                self.password,
                self.username,
                "not-hex",
                self.password_hash,
            )
        )


if __name__ == "__main__":
    unittest.main()
