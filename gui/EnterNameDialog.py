from PyQt5.QtWidgets import (
    QLineEdit
)
from gui.BaseDialog import BaseDialog
from PyQt5.QtCore import Qt, pyqtSignal

class EnterNameDialog(BaseDialog):
    submitted = pyqtSignal(str)

    def __init__(self, title_text: str, submit_text: str, parent=None):
        super().__init__(titleText=title_text, submitText=submit_text, parent=parent)
        self.submitButton.setEnabled(False)

    def buildContent(self, layout):
        self.line_edit = QLineEdit()
        self.line_edit.setObjectName("Project Name LE")
        self.line_edit.setAlignment(Qt.AlignCenter)
        self.line_edit.textEdited.connect(self.name_validator) # Editing text outputs signal to validator

        layout.addWidget(self.line_edit)

    def name_validator(self):
        if self.line_edit.text() != "" and self.line_edit.text() != "Unsaved Project":
            self.submitButton.setEnabled(True)
            self.line_edit.setStyleSheet("")
        else:
            self.submitButton.setEnabled(False)
            self.line_edit.setStyleSheet('border: 1px solid red;')

    def collectResult(self):
        return self.line_edit.text()