
import re

from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QPlainTextEdit
)


class DocumentPreviewDialog(QDialog):

    def __init__(
        self,
        filename: str,
        document_text: str,
        passage: str = "",
        parent=None
    ):
        super().__init__(parent)

        self.setWindowTitle(f"Document Preview — {filename}")
        self.resize(850, 650)
        self.setMinimumSize(600, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(14)

        title = QLabel(filename)
        title.setObjectName("previewTitle")
        title.setWordWrap(True)

        description = QLabel(
            "Original document text. The matching passage "
            "is highlighted when it can be located."
        )
        description.setObjectName("previewDescription")
        description.setWordWrap(True)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setObjectName("documentTextPreview")
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(document_text)
        self.text_edit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.WidgetWidth
        )
        self.text_edit.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.TextSelectableByKeyboard
        )

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(self.text_edit, stretch=1)

        footer = QHBoxLayout()
        footer.addStretch()

        close_button = QPushButton("Close")
        close_button.setObjectName("primaryButton")
        close_button.setMinimumWidth(90)
        close_button.clicked.connect(self.accept)

        footer.addWidget(close_button)
        layout.addLayout(footer)

        self.highlight_passage(passage)

    @staticmethod
    def normalize_with_positions(text: str):
        """
        Collapse consecutive whitespace into single spaces.

        Also keep track of where each normalized character
        came from in the original text.
        """

        normalized = []
        positions = []

        previous_was_whitespace = False

        for index, character in enumerate(text):

            if character.isspace():

                if not previous_was_whitespace:
                    normalized.append(" ")
                    positions.append(index)

                previous_was_whitespace = True

            else:
                normalized.append(character)
                positions.append(index)
                previous_was_whitespace = False

        return "".join(normalized), positions

    def highlight_passage(self, passage: str):

        if not passage or not passage.strip():
            return

        document_text = self.text_edit.toPlainText()

        normalized_document, positions = (
            self.normalize_with_positions(document_text)
        )

        normalized_passage = " ".join(passage.split())

        match_position = normalized_document.find(
            normalized_passage
        )

        if match_position == -1:
            return

        original_start = positions[match_position]
        original_end = positions[
            match_position + len(normalized_passage) - 1
        ] + 1

        cursor = self.text_edit.textCursor()

        cursor.setPosition(original_start)
        cursor.setPosition(
            original_end,
            QTextCursor.MoveMode.KeepAnchor
        )

        self.text_edit.setTextCursor(cursor)
        self.text_edit.setFocus()
        self.text_edit.ensureCursorVisible()
