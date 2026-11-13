
# src/ui/main_window.py

from pathlib import Path

from PySide6.QtCore import Signal, QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QStackedWidget,
    QMessageBox,
)

from src.core.document_loader import DocumentLibrary
from src.core.search_worker import SearchWorker
from src.core.settings_manager import SettingsManager

from src.ui.document_preview import DocumentPreviewDialog
from src.ui.library_view import LibraryView
from src.ui.search_view import SearchView
from src.ui.settings_dialog import SettingsDialog


class MainWindow(QMainWindow):

    documents_updated = Signal(list)
    background_search_requested = Signal(str)
    settings_updated = Signal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Semantic Search")
        self.resize(1100, 720)
        self.setMinimumSize(800, 550)

        # Application services and settings.
        self.settings_manager = SettingsManager()
        self.document_library = DocumentLibrary()
        self.chunks = []

        self.setup_ui()
        self.apply_styles()
        self.setup_settings_menu()
        self.setup_worker()

    # =====================================
    # WINDOW LIFECYCLE
    # =====================================

    def closeEvent(self, event):

        if hasattr(self, "worker_thread"):
            self.worker_thread.quit()
            self.worker_thread.wait()

        event.accept()

    # =====================================
    # BACKGROUND WORKER
    # =====================================

    def setup_worker(self):

        self.worker_thread = QThread(self)
        self.search_worker = SearchWorker()

        self.search_worker.moveToThread(
            self.worker_thread
        )

        # Connect requests before starting the worker.
        self.documents_updated.connect(
            self.search_worker.update_documents
        )

        self.background_search_requested.connect(
            self.search_worker.perform_search
        )

        self.settings_updated.connect(
            self.search_worker.update_settings
        )

        # Connect worker responses.
        self.search_worker.status_changed.connect(
            self.handle_worker_status
        )

        self.search_worker.search_finished.connect(
            self.handle_search_finished
        )

        self.search_worker.index_updated.connect(
            self.handle_index_updated
        )

        self.search_worker.error_occurred.connect(
            self.handle_worker_error
        )

        self.worker_thread.finished.connect(
            self.search_worker.deleteLater
        )

        self.worker_thread.start()

        # Send initial application state.
        self.settings_updated.emit(
            self.settings_manager.settings
        )

        self.documents_updated.emit(self.chunks)

    def handle_worker_status(self, message: str):

        self.search_view.set_status(message)

    def handle_search_finished(self, results: list):

        self.search_view.display_results(results)

    def handle_index_updated(self):

        self.search_view.set_status(
            "Document index updated."
        )

    def handle_worker_error(self, message: str):

        self.search_view.finish_loading()

        self.search_view.set_status(
            "An error occurred while processing your request."
        )

        self.search_view.clear_results()

        self.search_view.show_empty_message(
            f"Something went wrong:\n\n{message}"
        )

        QMessageBox.critical(
            self,
            "Processing Error",
            message
        )

    # =====================================
    # MAIN INTERFACE
    # =====================================

    def setup_ui(self):

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------------------
        # SIDEBAR
        # -------------------------------------

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(
            20, 25, 20, 20
        )
        sidebar_layout.setSpacing(10)

        app_title = QLabel("Semantic Search")
        app_title.setObjectName("appTitle")

        sidebar_layout.addWidget(app_title)
        sidebar_layout.addSpacing(25)

        self.search_button = QPushButton("Search")
        self.library_button = QPushButton("Document Library")

        for button in (
            self.search_button,
            self.library_button
        ):
            button.setObjectName("navigationButton")
            button.setCheckable(True)
            button.setAutoExclusive(True)

        sidebar_layout.addWidget(self.search_button)
        sidebar_layout.addWidget(self.library_button)

        sidebar_layout.addStretch()

        # -------------------------------------
        # MAIN CONTENT
        # -------------------------------------

        self.pages = QStackedWidget()
        self.pages.setObjectName("mainPages")

        self.search_view = SearchView()

        self.search_view.result_open_requested.connect(
            self.handle_result_open_requested
        )

        self.library_view = LibraryView(
            self.document_library
        )

        self.pages.addWidget(self.search_view)
        self.pages.addWidget(self.library_view)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages, stretch=1)

        # -------------------------------------
        # NAVIGATION EVENTS
        # -------------------------------------

        self.search_button.clicked.connect(
            lambda: self.switch_page(0)
        )

        self.library_button.clicked.connect(
            lambda: self.switch_page(1)
        )

        # -------------------------------------
        # SEARCH EVENTS
        # -------------------------------------

        self.search_view.search_requested.connect(
            self.perform_search
        )

        # -------------------------------------
        # DOCUMENT LIBRARY EVENTS
        # -------------------------------------

        self.library_view.chunks_changed.connect(
            self.handle_chunks_changed
        )

        # The library performs its initial refresh
        # before the signal connection.
        self.chunks = self.library_view.chunks

        self.switch_page(0)

    # =====================================
    # NAVIGATION
    # =====================================

    def switch_page(self, index: int):

        self.pages.setCurrentIndex(index)

        self.search_button.setChecked(index == 0)
        self.library_button.setChecked(index == 1)

    # =====================================
    # DOCUMENT UPDATES
    # =====================================

    def handle_chunks_changed(self, chunks):

        self.chunks = chunks
        self.documents_updated.emit(self.chunks)

    # =====================================
    # SEARCH
    # =====================================

    def perform_search(self, query: str):

        if not query.strip():
            return

        if not self.chunks:

            self.search_view.set_status(
                "No documents available."
            )

            self.search_view.clear_results()

            self.search_view.show_empty_message(
                "Import some documents before searching."
            )

            return

        self.search_view.set_loading()

        self.background_search_requested.emit(query)

    # =====================================
    # DOCUMENT PREVIEW
    # =====================================

    def handle_result_open_requested(
        self,
        filename: str,
        chunk_index: int,
        passage: str
    ):

        # Only accept a filename, not an arbitrary path.
        if Path(filename).name != filename:

            QMessageBox.warning(
                self,
                "Invalid Document",
                "The requested document name is invalid."
            )
            return

        document = next(
            (
                item for item in self.library_view.documents
                if item["filename"] == filename
            ),
            None
        )

        if document is None:

            QMessageBox.warning(
                self,
                "Document Not Found",
                "This document is no longer in your library."
            )
            return

        try:

            document_text = self.document_library.extract_text(
                Path(document["path"])
            )

            preview = DocumentPreviewDialog(
                filename=filename,
                document_text=document_text,
                passage=passage,
                parent=self
            )

            preview.exec()

        except Exception as error:

            QMessageBox.critical(
                self,
                "Preview Error",
                f"Could not open the document preview:\n\n{error}"
            )

    # =====================================
    # SETTINGS
    # =====================================

    def setup_settings_menu(self):

        settings_menu = self.menuBar().addMenu("Settings")

        settings_action = QAction(
            "Application Settings",
            self
        )

        settings_action.triggered.connect(
            self.open_settings
        )

        settings_menu.addAction(settings_action)

    def open_settings(self):

        dialog = SettingsDialog(
            self.settings_manager.settings,
            self
        )

        if dialog.exec() != SettingsDialog.DialogCode.Accepted:
            return

        new_settings = dialog.get_settings()

        try:
            self.settings_manager.update(new_settings)

        except OSError as error:

            QMessageBox.critical(
                self,
                "Settings Error",
                f"Could not save settings:\n\n{error}"
            )
            return

        self.library_view.confirm_removal = (
            self.settings_manager.get(
                "confirm_document_removal"
            )
        )

        self.settings_updated.emit(
            self.settings_manager.settings
        )

        self.search_view.set_status(
            "Settings saved successfully."
        )

    # =====================================
    # APPLICATION THEME
    # =====================================

    def apply_styles(self):

        self.setStyleSheet("""
            /* =====================================
               GLOBAL
            ===================================== */

            QWidget {
                background-color: #171421;
                color: #F4F0FA;
                font-family: "Segoe UI";
                font-size: 13px;
            }

            QMainWindow {
                background-color: #171421;
            }

            QLabel {
                background: transparent;
                color: #F4F0FA;
            }

            QLabel#pageTitle {
                color: #F4F0FA;
                font-size: 25px;
                font-weight: 700;
            }

            QLabel#pageDescription {
                color: #AAA1BC;
                font-size: 13px;
            }

            /* =====================================
               SIDEBAR
            ===================================== */

            QWidget#sidebar {
                background-color: #1E192B;
                border-right: 1px solid #382E4B;
            }

            QLabel#appTitle {
                color: #D8C4FF;
                font-size: 17px;
                font-weight: 700;
            }

            QPushButton#navigationButton {
                background-color: transparent;
                color: #AAA1BC;
                border: none;
                border-left: 3px solid transparent;
                border-radius: 6px;
                text-align: left;
                padding: 12px 13px;
                font-weight: 600;
            }

            QPushButton#navigationButton:hover {
                background-color: #302743;
                color: #F4F0FA;
            }

            QPushButton#navigationButton:checked {
                background-color: #352943;
                color: #D8C4FF;
                border-left: 3px solid #A78BFA;
            }

            /* =====================================
               MENU BAR
            ===================================== */

            QMenuBar {
                background-color: #211C30;
                color: #E9E2F5;
                border-bottom: 1px solid #352B49;
                padding: 5px;
            }

            QMenuBar::item {
                background: transparent;
                padding: 7px 12px;
                border-radius: 5px;
            }

            QMenuBar::item:selected {
                background-color: #352B49;
            }

            QMenu {
                background-color: #211C30;
                color: #F4F0FA;
                border: 1px solid #493B60;
                padding: 5px;
            }

            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
            }

            QMenu::item:selected {
                background-color: #49366F;
            }

            /* =====================================
               GENERAL BUTTONS
            ===================================== */

            QPushButton {
                background-color: #302743;
                color: #EDE7F6;
                border: 1px solid #493B60;
                border-radius: 7px;
                padding: 9px 16px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #403254;
                border-color: #8062B5;
            }

            QPushButton:pressed {
                background-color: #261E35;
            }

            QPushButton:disabled {
                background-color: #252130;
                color: #716A7E;
                border-color: #302A3C;
            }

            QPushButton#searchButton,
            QPushButton#primaryButton,
            QPushButton#addDocumentsButton {
                background-color: #8055D6;
                color: #FFFFFF;
                border: 1px solid #946DE5;
            }

            QPushButton#searchButton:hover,
            QPushButton#primaryButton:hover,
            QPushButton#addDocumentsButton:hover {
                background-color: #946DE5;
                border-color: #B69AFF;
            }

            QPushButton#searchButton:pressed,
            QPushButton#primaryButton:pressed,
            QPushButton#addDocumentsButton:pressed {
                background-color: #6940B8;
            }

            QPushButton#clearButton {
                background-color: #302743;
                color: #C7BDD7;
                border: 1px solid #493B60;
                border-radius: 8px;
                padding: 9px 17px;
            }

            QPushButton#clearButton:hover {
                background-color: #403254;
                color: #FFFFFF;
            }

            QPushButton#previewSourceButton {
                background-color: #302743;
                color: #D8C4FF;
                border: 1px solid #594477;
                border-radius: 6px;
                padding: 8px 14px;
            }

            QPushButton#previewSourceButton:hover {
                background-color: #49366F;
                border-color: #A78BFA;
            }

            QPushButton#removeDocumentButton {
                background-color: #3A2434;
                color: #F2A6C4;
                border: 1px solid #694054;
            }

            QPushButton#removeDocumentButton:hover {
                background-color: #503044;
                border-color: #A65B7D;
            }

            /* =====================================
               INPUT FIELDS
            ===================================== */

            QLineEdit,
            QPlainTextEdit,
            QTextEdit,
            QSpinBox {
                background-color: #211C30;
                color: #F4F0FA;
                border: 1px solid #493B60;
                border-radius: 7px;
                padding: 9px;
                selection-background-color: #8055D6;
                selection-color: white;
            }

            QLineEdit:focus,
            QPlainTextEdit:focus,
            QTextEdit:focus,
            QSpinBox:focus {
                border: 1px solid #A78BFA;
            }

            QLineEdit:disabled,
            QPlainTextEdit:disabled,
            QTextEdit:disabled,
            QSpinBox:disabled {
                background-color: #1B1825;
                color: #716A7E;
            }

            QLineEdit#searchInput {
                background-color: #211C30;
                color: #F4F0FA;
                border: 1px solid #493B60;
                border-radius: 9px;
                padding: 10px 14px;
                font-size: 14px;
            }

            QLineEdit#searchInput:focus {
                border: 1px solid #A78BFA;
                background-color: #251F35;
            }

            QPlainTextEdit {
                background-color: #171421;
                color: #F4F0FA;
                border: 1px solid #382E4B;
                border-radius: 8px;
                padding: 12px;
                selection-background-color: #8055D6;
                selection-color: #FFFFFF;
            }

            /* =====================================
               SPIN BOX
            ===================================== */

            QSpinBox {
                padding-right: 5px;
            }

            QSpinBox::up-button,
            QSpinBox::down-button {
                background-color: #302743;
                border: none;
                width: 20px;
            }

            QSpinBox::up-button:hover,
            QSpinBox::down-button:hover {
                background-color: #493B60;
            }

            /* =====================================
               CHECKBOXES
            ===================================== */

            QCheckBox {
                color: #E9E2F5;
                spacing: 9px;
                background: transparent;
            }

            QCheckBox::indicator {
                width: 17px;
                height: 17px;
                border-radius: 4px;
                border: 1px solid #716184;
                background-color: #211C30;
            }

            QCheckBox::indicator:hover {
                border-color: #A78BFA;
            }

            QCheckBox::indicator:checked {
                background-color: #8055D6;
                border: 1px solid #A78BFA;
            }

            /* =====================================
               SCROLL AREAS
            ===================================== */

            QScrollArea {
                background-color: transparent;
                border: none;
            }

            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }

            QScrollBar:vertical {
                background-color: #171421;
                width: 10px;
                margin: 0;
            }

            QScrollBar::handle:vertical {
                background-color: #493B60;
                border-radius: 5px;
                min-height: 25px;
            }

            QScrollBar::handle:vertical:hover {
                background-color: #8062B5;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }

            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }

            /* =====================================
               SEARCH STATUS
            ===================================== */

            QLabel#searchStatus {
                color: #B7A9CC;
                font-size: 13px;
                padding: 4px 0;
            }

            /* =====================================
               EMPTY STATES
            ===================================== */

            QFrame#emptyState,
            QFrame#libraryEmptyState {
                background-color: #1E192B;
                border: 1px dashed #493B60;
                border-radius: 12px;
            }

            QLabel#emptyStateIcon,
            QLabel#libraryEmptyIcon {
                color: #A78BFA;
                font-size: 42px;
            }

            QLabel#emptyMessage {
                color: #AAA1BC;
                font-size: 14px;
            }

            QLabel#libraryEmptyTitle {
                color: #F0EAF8;
                font-size: 16px;
                font-weight: 700;
            }

            QLabel#libraryEmptyDescription {
                color: #AAA1BC;
                font-size: 13px;
                padding: 0 30px;
            }

            /* =====================================
               SEARCH RESULT CARDS
            ===================================== */

            QFrame#resultCard {
                background-color: #211C30;
                border: 1px solid #382E4B;
                border-radius: 10px;
            }

            QFrame#resultCard:hover {
                background-color: #251F35;
                border: 1px solid #69518D;
            }

            QLabel#resultPosition {
                color: #C4A7FF;
                font-size: 12px;
                font-weight: 700;
            }

            QLabel#resultSource {
                color: #AAA1BC;
                font-size: 12px;
            }

            QLabel#resultPassageNumber {
                color: #A78BFA;
                font-size: 11px;
                font-weight: 700;
            }

            QLabel#resultPassage {
                color: #E5DFEE;
                font-size: 14px;
                padding: 3px 0;
            }

            /* =====================================
               DOCUMENT LIBRARY
            ===================================== */

            QLabel#documentCount {
                background-color: #302743;
                color: #D8C4FF;
                border: 1px solid #594477;
                border-radius: 7px;
                padding: 8px 13px;
                font-size: 11px;
                font-weight: 700;
            }

            QPushButton#addDocumentsButton {
                border-radius: 8px;
                padding: 10px 18px;
                font-weight: 700;
            }

            QFrame#documentCard {
                background-color: #211C30;
                border: 1px solid #382E4B;
                border-radius: 10px;
            }

            QFrame#documentCard:hover {
                background-color: #251F35;
                border: 1px solid #69518D;
            }

            QLabel#documentFilename {
                color: #F0EAF8;
                font-size: 14px;
                font-weight: 700;
            }

            QLabel#documentDetails {
                color: #AAA1BC;
                font-size: 12px;
            }

            QLabel#documentStatus {
                color: #B69AFF;
                font-size: 11px;
                font-weight: 600;
            }

            /* =====================================
               DOCUMENT PREVIEW
            ===================================== */

            QLabel#previewTitle {
                color: #C4A7FF;
                font-size: 19px;
                font-weight: 700;
            }

            QLabel#previewDescription {
                color: #AAA1BC;
                font-size: 13px;
            }

            /* =====================================
               DIALOGS
            ===================================== */

            QDialog {
                background-color: #171421;
            }

            /* =====================================
               MESSAGE BOXES
            ===================================== */

            QMessageBox {
                background-color: #211C30;
            }

            QMessageBox QLabel {
                color: #F4F0FA;
                min-width: 250px;
            }

            QMessageBox QPushButton {
                min-width: 75px;
            }

            /* =====================================
                SETTINGS DIALOG
            ===================================== */

            QFrame#settingsPanel {
                background-color: #211C30;
                border: 1px solid #382E4B;
                border-radius: 10px;
            }

            QLabel#settingsSectionTitle {
                color: #C4A7FF;
                font-size: 13px;
                font-weight: 700;
            }

            QLabel#settingsPanel QLabel {
                color: #E5DFEE;
            }

            QSpinBox#resultCountInput {
                background-color: #171421;
                color: #F4F0FA;
                border: 1px solid #493B60;
                border-radius: 7px;
                padding: 8px;
            }

            QSpinBox#resultCountInput:focus {
                border-color: #A78BFA;
            }

            QCheckBox#confirmRemovalCheckbox {
                color: #E5DFEE;
                spacing: 10px;
            }

            QPushButton#cancelSettingsButton {
                background-color: #302743;
                color: #C7BDD7;
                border: 1px solid #493B60;
            }

            QPushButton#cancelSettingsButton:hover {
                background-color: #403254;
                color: white;
            }
        """)
