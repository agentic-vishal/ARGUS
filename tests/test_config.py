import unittest

from pydantic import ValidationError

from argus.config.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_defaults_are_validated(self) -> None:
        settings = Settings()
        self.assertEqual(settings.app_name, "ARGUS")
        self.assertEqual(settings.min_confidence, 0.75)

    def test_confidence_must_be_between_zero_and_one(self) -> None:
        with self.assertRaises(ValidationError):
            Settings(min_confidence=1.5)


if __name__ == "__main__":
    unittest.main()

