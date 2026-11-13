
import hashlib
import shutil
from pathlib import Path

from pypdf import PdfReader

from src.core.text_chunker import chunk_text


from src.core.app_paths import (
    DOCUMENT_DIRECTORY,
    ensure_app_directories
)

SUPPORTED_EXTENSIONS = {
    ".txt",
    ".md",
    ".pdf"
}


class DocumentLibrary:

    def __init__(self):
        ensure_app_directories()
        DOCUMENT_DIRECTORY.mkdir(
            parents=True,
            exist_ok=True
        )

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Generate a SHA-256 fingerprint for a file.
        """

        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            for block in iter(
                lambda: file.read(1024 * 1024),
                b""
            ):
                sha256.update(block)

        return sha256.hexdigest()

    def get_existing_hashes(self) -> set[str]:
        """
        Calculate fingerprints for documents already in the library.
        """

        existing_hashes = set()

        for file_path in DOCUMENT_DIRECTORY.iterdir():

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            try:
                existing_hashes.add(
                    self.calculate_file_hash(file_path)
                )

            except OSError:
                continue

        return existing_hashes

    def extract_text(self, file_path: Path) -> str:

        extension = file_path.suffix.lower()

        if extension in {".txt", ".md"}:
            return file_path.read_text(
                encoding="utf-8",
                errors="replace"
            )

        if extension == ".pdf":
            reader = PdfReader(str(file_path))

            pages = []

            for page in reader.pages:
                pages.append(page.extract_text() or "")

            return "\n".join(pages)

        raise ValueError(
            f"Unsupported file extension: {extension}"
        )

    def generate_unique_path(self, filename: str) -> Path:

        original_path = Path(filename)

        destination = DOCUMENT_DIRECTORY / filename

        counter = 1

        while destination.exists():

            new_name = (
                f"{original_path.stem} "
                f"({counter}){original_path.suffix}"
            )

            destination = DOCUMENT_DIRECTORY / new_name

            counter += 1

        return destination

    def add_documents(
        self,
        file_paths: list[str]
    ) -> tuple[list[str], list[str], list[str]]:
        """
        Import documents while detecting duplicates.

        Returns:
            added: Imported filenames.
            skipped: Files skipped because their contents already exist.
            errors: Files that could not be imported.
        """

        added = []
        skipped = []
        errors = []

        existing_hashes = self.get_existing_hashes()

        for file_path_string in file_paths:

            source_path = Path(file_path_string)

            try:

                if source_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    raise ValueError(
                        "Unsupported file type."
                    )

                if not source_path.is_file():
                    raise ValueError(
                        "File does not exist."
                    )

                file_hash = self.calculate_file_hash(
                    source_path
                )

                if file_hash in existing_hashes:
                    skipped.append(source_path.name)
                    continue

                destination = self.generate_unique_path(
                    source_path.name
                )

                shutil.copy2(
                    source_path,
                    destination
                )

                existing_hashes.add(file_hash)

                added.append(destination.name)

            except Exception as error:

                errors.append(
                    f"{source_path.name}: {error}"
                )

        return added, skipped, errors

    def load_documents(
        self
    ) -> tuple[list[dict], list[dict], list[str]]:

        documents = []
        all_chunks = []
        errors = []

        for file_path in sorted(
            DOCUMENT_DIRECTORY.iterdir()
        ):

            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            try:

                text = self.extract_text(file_path)

                chunks = chunk_text(
                    text=text,
                    source=file_path.name
                )

                word_count = len(text.split())

                if chunks:
                    status = "Indexed"
                else:
                    status = "No extractable text"

                documents.append({
                    "filename": file_path.name,
                    "path": str(file_path),
                    "size_bytes": file_path.stat().st_size,
                    "word_count": word_count,
                    "chunk_count": len(chunks),
                    "status": status
                })

                all_chunks.extend(chunks)

            except Exception as error:

                errors.append(
                    f"{file_path.name}: {error}"
                )

        return documents, all_chunks, errors

    def remove_document(self, filename: str) -> bool:
        """
        Remove a document from the library.

        Only filenames are accepted, not arbitrary paths.
        """

        if Path(filename).name != filename:
            return False

        file_path = DOCUMENT_DIRECTORY / filename

        if not file_path.is_file():
            return False

        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False

        file_path.unlink()

        return True
