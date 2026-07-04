"""Credential loading and secure storage.

Credentials can come from three places, in priority order:
1. A `.env` file in the project root (handy for local development).
2. The OS keychain via `keyring` (used when the user ticks "remember me").
3. Manual entry in the login form.
"""
import os
from dataclasses import dataclass, asdict

import keyring
import keyring.errors
from dotenv import load_dotenv

load_dotenv()

SERVICE_NAME = "twitter-bot-gui"
FIELDS = ("consumer_key", "consumer_secret", "access_token", "access_token_secret")


@dataclass
class Credentials:
    consumer_key: str
    consumer_secret: str
    access_token: str
    access_token_secret: str

    def as_dict(self) -> dict:
        return asdict(self)


def load_from_env() -> Credentials | None:
    values = {field: os.getenv(f"TWITTER_{field.upper()}") for field in FIELDS}
    if all(values.values()):
        return Credentials(**values)
    return None


def load_from_keyring(username: str = "default") -> Credentials | None:
    values = {}
    for field in FIELDS:
        values[field] = keyring.get_password(f"{SERVICE_NAME}:{field}", username)
    if all(values.values()):
        return Credentials(**values)
    return None


def save_to_keyring(creds: Credentials, username: str = "default") -> None:
    for field in FIELDS:
        keyring.set_password(f"{SERVICE_NAME}:{field}", username, getattr(creds, field))


def clear_keyring(username: str = "default") -> None:
    for field in FIELDS:
        try:
            keyring.delete_password(f"{SERVICE_NAME}:{field}", username)
        except keyring.errors.PasswordDeleteError:
            pass
