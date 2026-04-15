from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from gui.BaseDialog import BaseDialog
from gui.add_object_dialog import Combox


class SetOutputFileType(BaseDialog):

    def __init__(self, current_type='DWG', parent=None):
        self._current_type = current_type
        super().__init__(titleText='Select Output File Type', submitText='Save', parent=parent)

    def buildContent(self, layout: QVBoxLayout) -> None:
        tabs = QTabWidget()
        widget = QWidget()
        widget_layout = QVBoxLayout(widget)

        title_label = QLabel('Select the Output File Type')
        title_label.setFont(QFont('Inter', 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        widget_layout.addWidget(title_label)
        widget_layout.addSpacing(10)

        explain_label = QLabel(
            f'Current output file type: {self._current_type}\n\n'
            'DWG: saves the flagged file as a DWG (default).\n\n'
            'DXF: saves the flagged file as a DXF.'
        )
        explain_label.setFont(QFont('Inter', 10))
        explain_label.setWordWrap(True)
        widget_layout.addWidget(explain_label)
        widget_layout.addSpacing(15)

        options = ['DWG', 'DXF']
        self._type_combo = Combox._add_combo(widget_layout, 'Output File Type:', options)
        self._type_combo.setCurrentText(self._current_type)

        widget_layout.addStretch()
        tabs.addTab(widget, 'File Type')
        layout.addWidget(tabs)

    def collectResult(self):
        return self._type_combo.currentText()
    