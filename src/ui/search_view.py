
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QScrollArea
)


class SearchView(QWidget):

    search_requested = Signal(str)
    result_open_requested = Signal(str, int, str)

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(16)

        # =====================================
        # PAGE HEADING
        # =====================================

        title = QLabel("Search Documents")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Find information across your imported documents."
        )
        description.setObjectName("pageDescription")

        main_layout.addWidget(title)
        main_layout.addWidget(description)

        # =====================================
        # SEARCH BAR
        # =====================================

        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText(
            "Ask a question or describe what you're looking for..."
        )
        self.search_input.setMinimumHeight(46)

        self.search_input.returnPressed.connect(
            self.submit_search
        )

        self.search_button = QPushButton("Search")
        self.search_button.setObjectName("searchButton")
        self.search_button.setMinimumHeight(46)
        self.search_button.setMinimumWidth(105)
        self.search_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.search_button.clicked.connect(
            self.submit_search
        )

        self.clear_button = QPushButton("Clear")
        self.clear_button.setObjectName("clearButton")
        self.clear_button.setMinimumHeight(46)
        self.clear_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )
        self.clear_button.clicked.connect(
            self.clear_search
        )

        search_layout.addWidget(self.search_input, stretch=1)
        search_layout.addWidget(self.search_button)
        search_layout.addWidget(self.clear_button)

        main_layout.addLayout(search_layout)

        # =====================================
        # SEARCH STATUS
        # =====================================

        self.status_label = QLabel(
            "Enter a search to explore your documents."
        )
        self.status_label.setObjectName("searchStatus")

        main_layout.addWidget(self.status_label)

        # =====================================
        # SEARCH RESULTS
        # =====================================

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("resultsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.results_container = QWidget()
        self.results_container.setObjectName(
            "resultsContainer"
        )

        self.results_layout = QVBoxLayout(
            self.results_container
        )

        self.results_layout.setContentsMargins(
            2, 2, 8, 2
        )
        self.results_layout.setSpacing(14)

        self.scroll_area.setWidget(
            self.results_container
        )

        main_layout.addWidget(
            self.scroll_area,
            stretch=1
        )

        self.show_empty_message(
            "Your search results will appear here."
        )

    # =====================================
    # SEARCH ACTIONS
    # =====================================

    def submit_search(self):

        query = self.search_input.text().strip()

        if not query:
            self.set_status(
                "Enter a search query first."
            )
            return

        self.search_requested.emit(query)

    def clear_search(self):

        self.search_input.clear()
        self.clear_results()

        self.set_status(
            "Enter a search to explore your documents."
        )

        self.show_empty_message(
            "Your search results will appear here."
        )

        self.search_input.setFocus()

    def set_status(self, message: str):
        self.status_label.setText(message)

    def set_loading(self):

        self.search_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        self.set_status(
            "Searching your documents..."
        )

        self.clear_results()

        self.show_empty_message(
            "Please wait while your documents are being searched."
        )

    def finish_loading(self):

        self.search_button.setEnabled(True)
        self.clear_button.setEnabled(True)

    # =====================================
    # RESULT MANAGEMENT
    # =====================================

    def clear_results(self):

        while self.results_layout.count():

            item = self.results_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

    def show_empty_message(self, message: str):

        empty_state = QFrame()
        empty_state.setObjectName("emptyState")

        empty_layout = QVBoxLayout(empty_state)
        empty_layout.setContentsMargins(
            24, 35, 24, 35
        )
        empty_layout.setSpacing(10)

        icon_label = QLabel("⌕")
        icon_label.setObjectName("emptyStateIcon")
        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        message_label = QLabel(message)
        message_label.setObjectName("emptyMessage")
        message_label.setWordWrap(True)
        message_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(message_label)

        self.results_layout.addStretch()
        self.results_layout.addWidget(empty_state)
        self.results_layout.addStretch()

    def display_results(self, results: list[dict]):

        self.finish_loading()
        self.clear_results()

        if not results:

            self.set_status(
                "No matching passages found."
            )

            self.show_empty_message(
                "No relevant passages were found.\n"
                "Try using different wording or a more specific query."
            )

            return

        self.set_status(
            f"Found {len(results)} relevant passages."
        )

        for position, result in enumerate(results, start=1):

            card = QFrame()
            card.setObjectName("resultCard")

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(
                20, 17, 20, 17
            )
            card_layout.setSpacing(12)

            # =====================================
            # RESULT HEADING
            # =====================================

            heading_layout = QHBoxLayout()
            heading_layout.setSpacing(12)

            position_label = QLabel(
                f"RESULT {position:02d}"
            )
            position_label.setObjectName(
                "resultPosition"
            )

            source_label = QLabel(
                result.get(
                    "source",
                    "Unknown document"
                )
            )
            source_label.setObjectName(
                "resultSource"
            )
            source_label.setWordWrap(True)
            source_label.setAlignment(
                Qt.AlignmentFlag.AlignRight
            )

            heading_layout.addWidget(position_label)
            heading_layout.addStretch()
            heading_layout.addWidget(source_label)

            card_layout.addLayout(heading_layout)

            # =====================================
            # PASSAGE CONTENT
            # =====================================

            chunk_index = result.get("chunk_index", 0)

            passage_number = QLabel(
                f"PASSAGE {chunk_index + 1}"
            )
            passage_number.setObjectName(
                "resultPassageNumber"
            )

            passage = QLabel(
                result.get("text", "")
            )
            passage.setObjectName("resultPassage")
            passage.setWordWrap(True)
            passage.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            card_layout.addWidget(passage_number)
            card_layout.addWidget(passage)

            # =====================================
            # RESULT FOOTER
            # =====================================

            footer_layout = QHBoxLayout()
            footer_layout.addStretch()

            preview_button = QPushButton(
                "Preview Source"
            )
            preview_button.setObjectName(
                "previewSourceButton"
            )
            preview_button.setCursor(
                Qt.CursorShape.PointingHandCursor
            )

            filename = result.get("source", "")
            passage_text = result.get("text", "")

            preview_button.clicked.connect(
                lambda checked=False,
                name=filename,
                index=chunk_index,
                text=passage_text:
                    self.result_open_requested.emit(
                        name,
                        index,
                        text
                    )
            )

            footer_layout.addWidget(preview_button)
            card_layout.addLayout(footer_layout)

            self.results_layout.addWidget(card)

        self.results_layout.addStretch()
