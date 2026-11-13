
# src/ui/settings_dialog.py

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QCheckBox,
    QFormLayout,
    QFrame
)


class SettingsDialog(QDialog):

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(460)
        self.setMinimumHeight(330)

        self.setup_ui(settings)

    def setup_ui(self, settings: dict):

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 26, 26, 24)
        layout.setSpacing(18)

        # =====================================
        # HEADER
        # =====================================

        title = QLabel("Application Settings")
        title.setObjectName("pageTitle")

        description = QLabel(
            "Customize how Semantic Search behaves."
        )
        description.setObjectName("pageDescription")
        description.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(description)

        # =====================================
        # SETTINGS PANEL
        # =====================================

        settings_panel = QFrame()
        settings_panel.setObjectName("settingsPanel")

        panel_layout = QVBoxLayout(settings_panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(18)

        section_title = QLabel("Search Preferences")
        section_title.setObjectName("settingsSectionTitle")

        panel_layout.addWidget(section_title)

        form = QFormLayout()
        form.setSpacing(18)

        result_label = QLabel("Search results to display")

        self.result_count_input = QSpinBox()
        self.result_count_input.setObjectName(
            "resultCountInput"
        )
        self.result_count_input.setRange(1, 50)
        self.result_count_input.setValue(
            settings.get("result_count", 8)
        )
        self.result_count_input.setMinimumWidth(100)

        form.addRow(
            result_label,
            self.result_count_input
        )

        panel_layout.addLayout(form)

        # -------------------------------------
        # DOCUMENT PREFERENCES
        # -------------------------------------

        document_section = QLabel("Document Management")
        document_section.setObjectName("settingsSectionTitle")

        panel_layout.addWidget(document_section)

        self.confirm_removal_checkbox = QCheckBox(
            "Ask before removing documents"
        )

        self.confirm_removal_checkbox.setObjectName(
            "confirmRemovalCheckbox"
        )

        self.confirm_removal_checkbox.setChecked(
            settings.get(
                "confirm_document_removal",
                True
            )
        )

        panel_layout.addWidget(
            self.confirm_removal_checkbox
        )

        layout.addWidget(settings_panel, stretch=1)

        # =====================================
        # FOOTER
        # =====================================

        footer = QHBoxLayout()
        footer.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("cancelSettingsButton")
        cancel_button.clicked.connect(self.reject)

        save_button = QPushButton("Save Settings")
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(self.accept)

        footer.addWidget(cancel_button)
        footer.addWidget(save_button)

        layout.addLayout(footer)

    # =====================================
    # SETTINGS RETRIEVAL
    # =====================================

    def get_settings(self) -> dict:

        return {
            "result_count": self.result_count_input.value(),
            "confirm_document_removal":
                self.confirm_removal_checkbox.isChecked()
        }
