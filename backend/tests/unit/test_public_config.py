"""Offline startup contract: no database, Redis, private .env or model access."""
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

CONFIG = Path(__file__).resolve().parents[2] / "app" / "config.py"
TEST_ENV = {"JWT_SECRET_KEY": "test-jwt-" + "x" * 40, "DEVELOPER_PASSWORD": "test-developer-" + "x" * 16, "DB_PASSWORD": "test-database-" + "x" * 16}


def load_settings(overrides=None):
    with patch.dict(os.environ, {**TEST_ENV, **(overrides or {})}, clear=True), patch("dotenv.load_dotenv"):
        spec = importlib.util.spec_from_file_location("public_config_under_test", CONFIG)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.settings


class PublicConfigTests(unittest.TestCase):
    def test_debug_and_default_accounts_are_disabled(self):
        settings = load_settings()
        self.assertFalse(settings.DEBUG)
        self.assertFalse(settings.SEED_DEMO_USERS)
        self.assertEqual(settings.DEMO_USER_PASSWORD, "")

    def test_missing_and_short_secrets_prevent_startup(self):
        for key in TEST_ENV:
            for value in ("", "short"):
                with self.subTest(key=key, value=value), self.assertRaisesRegex(ValueError, key):
                    load_settings({key: value})

    def test_documentation_placeholders_prevent_startup(self):
        with self.assertRaisesRegex(ValueError, "JWT_SECRET_KEY"):
            load_settings({"JWT_SECRET_KEY": "your-" + "x" * 48})

    def test_url_special_characters_preserve_credentials(self):
        password = "test-p@ss:/?#% +中文"
        settings = load_settings({"DB_USER": "demo@user", "DB_PASSWORD": password})
        url = urlsplit(settings.DATABASE_URL)
        self.assertEqual(unquote(url.username), "demo@user")
        self.assertEqual(unquote(url.password), password)

    def test_demo_seeding_requires_an_explicit_password(self):
        with self.assertRaisesRegex(ValueError, "DEMO_USER_PASSWORD"):
            load_settings({"SEED_DEMO_USERS": "true"})

    def test_demo_seeding_accepts_an_explicit_password(self):
        settings = load_settings({"SEED_DEMO_USERS": "true", "DEMO_USER_PASSWORD": "test-seed-" + "x" * 16})
        self.assertTrue(settings.SEED_DEMO_USERS)


if __name__ == "__main__":
    unittest.main()
