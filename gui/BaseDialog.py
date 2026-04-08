from __future__ import annotations

from typing import Any

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal


class BaseDialog(QDialog):
    """
    Base class for simple 'content + submit button' dialogs.

    Subclasses should implement:
      - buildContent(layout): add widgets to `layout`
      - collectResult(): return the value to emit on submit
    """

    submitted = pyqtSignal(object)  # subclasses can emit list, dict, custom obj, etc.

    def __init__(
        self,
        titleText: str,
        submitText: str,
        parent=None,
        *,
        contentAlignment: Qt.Alignment = Qt.AlignCenter,
        submitAlignment: Qt.Alignment | None = None,
    ):
        super().__init__(parent)

        self.setWindowTitle(titleText)

        self.mainLayout = QVBoxLayout(self)
        self.contentAlignment = contentAlignment

        # Let subclass populate UI
        self.buildContent(self.mainLayout)

        # Submit button (shared)
        self.submitButton = QPushButton(submitText)
        self.submitButton.clicked.connect(self._onSubmitClicked)

        if submitAlignment is None:
            self.mainLayout.addWidget(self.submitButton)
        else:
            self.mainLayout.addWidget(self.submitButton, alignment=submitAlignment)

    def buildContent(self, layout: QVBoxLayout) -> None:
        """Override in subclass: add your content widgets to the given layout."""
        raise NotImplementedError

    def collectResult(self) -> Any:
        """Override in subclass: return the value to emit via submitted."""
        raise NotImplementedError

    def _onSubmitClicked(self) -> None:
        result = self.collectResult()
        self.submitted.emit(result)
        self.accept()