
import os
import shutil
import sys
from pathlib import Path


# Existing project directory, used only to migrate old data.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DATA_DIRECTORY = PROJECT_ROOT / "data"


# Choose a writable application data directory.
if os.name == "nt":
    APP_DATA_DIRECTORY = (
        Path(os.environ.get("LOCALAPPDATA", Path.home()))
        / "SemanticSearch"
    )
else:
    APP_DATA_DIRECTORY = Path.home() / ".semantic-search"


DOCUMENT_DIRECTORY = APP_DATA_DIRECTORY / "documents"
INDEX_DIRECTORY = APP_DATA_DIRECTORY / "index"
SETTINGS_PATH = APP_DATA_DIRECTORY / "settings.json"


def ensure_app_directories():

    DOCUMENT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    INDEX_DIRECTORY.mkdir(parents=True, exist_ok=True)

    # Migrate existing development data without overwriting
    # anything already present in the new location.
    if not getattr(sys, "frozen", False):

        legacy_documents = LEGACY_DATA_DIRECTORY / "documents"

        if legacy_documents.is_dir():
            for source in legacy_documents.iterdir():

                destination = DOCUMENT_DIRECTORY / source.name

                if source.is_file() and not destination.exists():
                    shutil.copy2(source, destination)

        legacy_index = LEGACY_DATA_DIRECTORY / "index"

        if legacy_index.is_dir():
            for source in legacy_index.iterdir():

                destination = INDEX_DIRECTORY / source.name

                if source.is_file() and not destination.exists():
                    shutil.copy2(source, destination)

        legacy_settings = LEGACY_DATA_DIRECTORY / "settings.json"

        if legacy_settings.is_file() and not SETTINGS_PATH.exists():
            shutil.copy2(legacy_settings, SETTINGS_PATH)
