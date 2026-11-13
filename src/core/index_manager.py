
import json
import os
from pathlib import Path

import faiss


from src.core.app_paths import (
    INDEX_DIRECTORY,
    ensure_app_directories
)

FAISS_INDEX_PATH = INDEX_DIRECTORY / "faiss.index"
CHUNKS_PATH = INDEX_DIRECTORY / "chunks.json"


class IndexManager:

    def __init__(self):
        ensure_app_directories()
        INDEX_DIRECTORY.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        faiss_index,
        chunks: list[dict],
        embedding_model: str
    ) -> None:

        if faiss_index is None or not chunks:
            self.clear()
            return

        temporary_index_path = INDEX_DIRECTORY / "faiss.tmp"
        temporary_chunks_path = INDEX_DIRECTORY / "chunks.tmp"

        metadata = {
            "embedding_model": embedding_model,
            "chunks": chunks
        }

        try:
            # Save the FAISS index.
            faiss.write_index(
                faiss_index,
                str(temporary_index_path)
            )

            # Save the corresponding chunk metadata.
            with temporary_chunks_path.open(
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    metadata,
                    file,
                    ensure_ascii=False,
                    indent=2
                )

            # Replace the previous files only after both saves succeed.
            os.replace(temporary_index_path, FAISS_INDEX_PATH)
            os.replace(temporary_chunks_path, CHUNKS_PATH)

        finally:
            # Clean up temporary files if something went wrong.
            temporary_index_path.unlink(missing_ok=True)
            temporary_chunks_path.unlink(missing_ok=True)

    def load(
        self,
        expected_chunks: list[dict],
        embedding_model: str
    ):

        if not FAISS_INDEX_PATH.is_file():
            return None

        if not CHUNKS_PATH.is_file():
            return None

        try:
            with CHUNKS_PATH.open(
                "r",
                encoding="utf-8"
            ) as file:
                metadata = json.load(file)

            saved_chunks = metadata["chunks"]
            saved_model = metadata["embedding_model"]

            # Ensure the saved index belongs to the current documents.
            if saved_model != embedding_model:
                return None

            if saved_chunks != expected_chunks:
                return None

            index = faiss.read_index(str(FAISS_INDEX_PATH))

            # FAISS positions must correspond to the saved chunks.
            if index.ntotal != len(saved_chunks):
                return None

            return index

        except (OSError, ValueError, KeyError, TypeError):
            return None

    def clear(self) -> None:
        FAISS_INDEX_PATH.unlink(missing_ok=True)
        CHUNKS_PATH.unlink(missing_ok=True)
