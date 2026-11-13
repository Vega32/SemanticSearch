
import json
from pathlib import Path


from src.core.app_paths import (
    SETTINGS_PATH,
    ensure_app_directories
)

DEFAULT_SETTINGS = {
    "result_count": 8,
    "confirm_document_removal": True
}


class SettingsManager:

    def __init__(self):
        ensure_app_directories()
        SETTINGS_PATH.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.settings = self.load()

    def load(self) -> dict:
        """
        Load saved settings and fill in missing defaults.
        """

        if not SETTINGS_PATH.exists():
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()
            return self.settings

        try:
            with SETTINGS_PATH.open(
                "r",
                encoding="utf-8"
            ) as file:
                saved_settings = json.load(file)

            settings = DEFAULT_SETTINGS.copy()
            settings.update(saved_settings)

            # Validate supported values.
            result_count = settings.get("result_count")

            if (
                not isinstance(result_count, int)
                or isinstance(result_count, bool)
                or not 1 <= result_count <= 50
            ):
                settings["result_count"] = (
                    DEFAULT_SETTINGS["result_count"]
                )

            if not isinstance(
                settings.get("confirm_document_removal"),
                bool
            ):
                settings["confirm_document_removal"] = True

            self.settings = settings
            self.save()

            return self.settings

        except (OSError, ValueError, TypeError):
            self.settings = DEFAULT_SETTINGS.copy()
            self.save()
            return self.settings

    def save(self) -> None:
        """
        Persist the current settings.
        """

        temporary_path = SETTINGS_PATH.with_suffix(".tmp")

        with temporary_path.open(
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                self.settings,
                file,
                indent=2
            )

        temporary_path.replace(SETTINGS_PATH)

    def update(self, new_settings: dict) -> None:
        """
        Update only recognized settings.
        """

        updated = self.settings.copy()

        if "result_count" in new_settings:
            value = new_settings["result_count"]

            if (
                isinstance(value, int)
                and not isinstance(value, bool)
                and 1 <= value <= 50
            ):
                updated["result_count"] = value

        if "confirm_document_removal" in new_settings:
            value = new_settings["confirm_document_removal"]

            if isinstance(value, bool):
                updated["confirm_document_removal"] = value

        self.settings = updated
        self.save()

    def get(self, key: str):
        return self.settings.get(key)
