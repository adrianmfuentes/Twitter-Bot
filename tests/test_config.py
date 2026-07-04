import unittest
from unittest.mock import patch

import keyring.errors

from twitter_bot import config


class FakeKeyring:
    """In-memory stand-in so tests never touch the real OS credential store."""

    errors = keyring.errors

    def __init__(self):
        self._store = {}

    def set_password(self, service, username, password):
        self._store[(service, username)] = password

    def get_password(self, service, username):
        return self._store.get((service, username))

    def delete_password(self, service, username):
        try:
            del self._store[(service, username)]
        except KeyError as e:
            raise keyring.errors.PasswordDeleteError from e


class ConfigTests(unittest.TestCase):
    def setUp(self):
        self.fake = FakeKeyring()
        patcher = patch("twitter_bot.config.keyring", self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_load_from_env_reads_all_four_fields(self):
        env = {
            "TWITTER_CONSUMER_KEY": "ck",
            "TWITTER_CONSUMER_SECRET": "cs",
            "TWITTER_ACCESS_TOKEN": "at",
            "TWITTER_ACCESS_TOKEN_SECRET": "ats",
        }
        with patch.dict("os.environ", env, clear=False):
            creds = config.load_from_env()

        self.assertIsNotNone(creds)
        self.assertEqual(creds.consumer_key, "ck")

    def test_load_from_env_returns_none_when_incomplete(self):
        with patch.dict("os.environ", {"TWITTER_CONSUMER_KEY": "ck"}, clear=True):
            self.assertIsNone(config.load_from_env())

    def test_keyring_round_trip(self):
        creds = config.Credentials("ck", "cs", "at", "ats")
        config.save_to_keyring(creds, username="alice")

        loaded = config.load_from_keyring(username="alice")

        self.assertEqual(loaded, creds)

    def test_clear_keyring_is_safe_when_nothing_saved(self):
        config.clear_keyring(username="nobody")  # must not raise

    def test_load_from_keyring_returns_none_when_empty(self):
        self.assertIsNone(config.load_from_keyring(username="ghost"))


if __name__ == "__main__":
    unittest.main()
