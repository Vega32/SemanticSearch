
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QFileDialog,
    QMessageBox,
    QScrollArea
)


class LibraryView(QWidget):

    chunks_changed = Signal(list)

    def __init__(self, document_library):
        super().__init__()

        self.document_library = document_library

        self.documents = []
        self.chunks = []
        self.confirm_removal = True

        self.setup_ui()
        self.refresh_documents()

    def setup_ui(self):

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            32, 28, 32, 28
        )

        main_layout.setSpacing(18)

        # =====================================
        # HEADER
        # =====================================

        header_layout = QHBoxLayout()

        heading_layout = QVBoxLayout()
        heading_layout.setSpacing(5)

        title = QLabel("Document Library")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Manage the documents available to your search engine."
        )
        description.setObjectName("pageDescription")

        heading_layout.addWidget(title)
        heading_layout.addWidget(description)

        self.document_count_label = QLabel(
            "0 DOCUMENTS"
        )
        self.document_count_label.setObjectName(
            "documentCount"
        )
        self.document_count_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        header_layout.addLayout(heading_layout)
        header_layout.addStretch()
        header_layout.addWidget(
            self.document_count_label,
            alignment=Qt.AlignmentFlag.AlignTop
        )

        main_layout.addLayout(header_layout)

        # =====================================
        # IMPORT BUTTON
        # =====================================

        import_layout = QHBoxLayout()

        self.add_button = QPushButton(
            "+  Add Documents"
        )
        self.add_button.setObjectName("addDocumentsButton")
        self.add_button.setMinimumHeight(42)
        self.add_button.setCursor(
            Qt.CursorShape.PointingHandCursor
        )

        self.add_button.clicked.connect(
            self.import_documents
        )

        import_layout.addWidget(self.add_button)
        import_layout.addStretch()

        main_layout.addLayout(import_layout)

        # =====================================
        # DOCUMENT LIST
        # =====================================

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("libraryScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(
            QFrame.Shape.NoFrame
        )

        self.document_container = QWidget()
        self.document_container.setObjectName(
            "documentContainer"
        )

        self.document_layout = QVBoxLayout(
            self.document_container
        )

        self.document_layout.setContentsMargins(
            2, 2, 8, 2
        )

        self.document_layout.setSpacing(12)

        self.scroll_area.setWidget(
            self.document_container
        )

        main_layout.addWidget(
            self.scroll_area,
            stretch=1
        )

    # =====================================
    # FILE FORMATTING
    # =====================================

    @staticmethod
    def format_file_size(size_bytes: int) -> str:

        if size_bytes < 1024:
            return f"{size_bytes} B"

        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"

        return f"{size_bytes / (1024 * 1024):.1f} MB"

    # =====================================
    # DOCUMENT IMPORT
    # =====================================

    def import_documents(self):

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Documents",
            "",
            "Supported documents (*.txt *.md *.pdf)"
        )

        if not file_paths:
            return

        added, skipped, errors = (
            self.document_library.add_documents(
                file_paths
            )
        )

        self.refresh_documents()

        summary = []

        if added:
            summary.append(
                f"Imported: {len(added)}"
            )

        if skipped:
            summary.append(
                f"Skipped duplicates: {len(skipped)}"
            )

        if errors:
            summary.append(
                f"Failed: {len(errors)}"
            )

        if not summary:
            summary.append(
                "No documents were imported."
            )

        message = "\n".join(summary)

        if errors:
            message += (
                "\n\nErrors:\n" + "\n".join(errors)
            )

        QMessageBox.information(
            self,
            "Import Results",
            message
        )

    # =====================================
    # DOCUMENT REMOVAL
    # =====================================

    def remove_document(self, filename: str):

        if self.confirm_removal:

            confirmation = QMessageBox.question(
                self,
                "Remove Document",
                f"Are you sure you want to remove '{filename}'?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            )

            if confirmation != QMessageBox.StandardButton.Yes:
                return

        try:

            removed = self.document_library.remove_document(
                filename
            )

            if not removed:

                QMessageBox.warning(
                    self,
                    "Removal Failed",
                    "The document could not be removed."
                )

                return

            self.refresh_documents()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Removal Error",
                str(error)
            )

    # =====================================
    # EMPTY LIBRARY STATE
    # =====================================

    def show_empty_library(self):

        empty_state = QFrame()
        empty_state.setObjectName("libraryEmptyState")

        empty_layout = QVBoxLayout(empty_state)

        empty_layout.setContentsMargins(
            25, 45, 25, 45
        )

        empty_layout.setSpacing(12)

        icon_label = QLabel("▤")
        icon_label.setObjectName(
            "libraryEmptyIcon"
        )

        icon_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        title_label = QLabel(
            "Your library is empty"
        )
        title_label.setObjectName(
            "libraryEmptyTitle"
        )

        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        description_label = QLabel(
            "Import TXT, Markdown, or PDF documents "
            "to start building your searchable library."
        )

        description_label.setObjectName(
            "libraryEmptyDescription"
        )

        description_label.setWordWrap(True)
        description_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        empty_layout.addWidget(icon_label)
        empty_layout.addWidget(title_label)
        empty_layout.addWidget(description_label)

        self.document_layout.addStretch()
        self.document_layout.addWidget(empty_state)
        self.document_layout.addStretch()

    # =====================================
    # DOCUMENT LIST REFRESH
    # =====================================

    def refresh_documents(self):

        (
            self.documents,
            self.chunks,
            errors
        ) = self.document_library.load_documents()

        count = len(self.documents)

        self.document_count_label.setText(
            f"{count} DOCUMENTS"
        )

        # Remove previous document cards.
        while self.document_layout.count():

            item = self.document_layout.takeAt(0)
            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        if not self.documents:

            self.show_empty_library()

        else:

            for document in self.documents:

                card = QFrame()
                card.setObjectName("documentCard")

                card_layout = QHBoxLayout(card)

                card_layout.setContentsMargins(
                    20, 17, 20, 17
                )

                card_layout.setSpacing(16)

                # =====================================
                # DOCUMENT INFORMATION
                # =====================================

                information_layout = QVBoxLayout()
                information_layout.setSpacing(7)

                filename_label = QLabel(
                    document["filename"]
                )

                filename_label.setObjectName(
                    "documentFilename"
                )

                filename_label.setWordWrap(True)

                details = (
                    f"{self.format_file_size(document['size_bytes'])}"
                    f"    •    {document['word_count']:,} words"
                    f"    •    {document['chunk_count']} passages"
                )

                details_label = QLabel(details)
                details_label.setObjectName(
                    "documentDetails"
                )

                status_label = QLabel(
                    document["status"]
                )

                status_label.setObjectName(
                    "documentStatus"
                )

                information_layout.addWidget(
                    filename_label
                )

                information_layout.addWidget(
                    details_label
                )

                information_layout.addWidget(
                    status_label
                )

                card_layout.addLayout(
                    information_layout,
                    stretch=1
                )

                # =====================================
                # REMOVE BUTTON
                # =====================================

                remove_button = QPushButton(
                    "Remove"
                )

                remove_button.setObjectName(
                    "removeDocumentButton"
                )

                remove_button.setCursor(
                    Qt.CursorShape.PointingHandCursor
                )

                remove_button.clicked.connect(
                    lambda checked=False,
                    name=document["filename"]:
                        self.remove_document(name)
                )

                card_layout.addWidget(
                    remove_button,
                    alignment=Qt.AlignmentFlag.AlignVCenter
                )

                self.document_layout.addWidget(card)

            self.document_layout.addStretch()

        # Notify the main window and background worker.
        self.chunks_changed.emit(self.chunks)

        if errors:

            QMessageBox.warning(
                self,
                "Document Loading Warnings",
                "\n".join(errors)
            )
