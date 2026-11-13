
from PySide6.QtCore import QObject, Signal, Slot

from src.core.search_engine import SearchEngine


class SearchWorker(QObject):

    # Signals sent back to the main thread.
    status_changed = Signal(str)
    search_finished = Signal(list)
    index_updated = Signal()
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()

        self.search_engine = None
        self.chunks = []
        self.result_count=8

    @Slot(list)
    def update_documents(self, chunks: list[dict]):
        """
        Receive the latest document chunks.

        If the AI engine is already initialized, rebuild its index.
        Otherwise, save the chunks for the first search.
        """

        self.chunks = chunks

        if self.search_engine is None:
            return

        try:
            self.status_changed.emit(
                "Updating document index..."
            )

            self.search_engine.build_index(self.chunks)

            self.index_updated.emit()

        except Exception as error:
            self.search_engine = None
            self.error_occurred.emit(str(error))

    @Slot(str)
    def perform_search(self, query: str):
        """
        Initialize the AI engine if necessary,
        then perform the requested search.
        """

        try:
            if not query.strip():
                self.search_finished.emit([])
                return

            # Initialize the AI engine only once.
            if self.search_engine is None:

                self.status_changed.emit(
                    "Loading AI models..."
                )

                self.search_engine = SearchEngine()

                self.status_changed.emit(
                    "Preparing document index..."
                )

                # Try loading an existing index.
                loaded = self.search_engine.load_index(
                    self.chunks
                )

                # Rebuild only when no valid index exists.
                if not loaded:
                    self.search_engine.build_index(
                        self.chunks
                    )

            self.status_changed.emit(
                "Searching your documents..."
            )

            results = self.search_engine.search(
                query,
                top_k=self.result_count
            )

            self.search_finished.emit(results)

        except Exception as error:
            # Avoid keeping a potentially inconsistent engine.
            self.search_engine = None

            self.error_occurred.emit(str(error))

    @Slot(dict)
    def update_settings(self, settings: dict):

        result_count = settings.get("result_count", 8)

        if (
            isinstance(result_count, int)
            and not isinstance(result_count, bool)
            and 1 <= result_count <= 50
        ):
            self.result_count = result_count
