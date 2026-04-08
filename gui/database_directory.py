import sys
import os
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QWidget, QTabWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from gui.BaseDialog import BaseDialog
from database.db_models import get_configured_db_path, reinitialise_db
from gui.add_object_dialog import database_description


SHARED_DB_PATH = r'S:\General\Shane\objectdatabase.db'


def get_app_db_path():
    """Returns the database path next to the running exe (_internal folder).
    In dev (VS Code), falls back to the project root db."""
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), '_internal', 'objectdatabase.db') #gives the folder hte exe lives in 
    return os.path.join(os.path.dirname(__file__), '..', 'objectdatabase.db')


def detect_install_location():
    """Returns a readable label describing where the app is installed."""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable).upper() #the folder the exe is in 
        if exe_dir.startswith('S:\\') or exe_dir.startswith('S:/'):
            return 'Shared Drive (S:\\)'
        return f'Local Drive ({os.path.dirname(sys.executable)})'
    return 'Development (VS Code)'


class DatabaseDirectoryDialog(BaseDialog):

    def __init__(self, parent=None):
        self._pending_path = get_configured_db_path() or get_app_db_path()
        super().__init__(titleText='Select Database', submitText='Submit', parent=parent)

    def buildContent(self, layout: QVBoxLayout) -> None:
        app_db = get_app_db_path()
        location = detect_install_location()
        tabs = QTabWidget()
        directory_widget = QWidget()
        directory_layout = QVBoxLayout(directory_widget)

        title_label = QLabel('Select the Database to acess')
        title_label.setFont(QFont('Inter', 11, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        directory_layout.addWidget(title_label)
        directory_layout.addSpacing(10)

        btn1 = QPushButton('Database Description')
        btn1.clicked.connect(lambda: database_description(parent=self).exec_())
        directory_layout.addWidget(btn1)

        explain_label = QLabel(
            f'This app is installed at: {location}\n\n'
            'Shared Database: The shared database on the S drive, accessible by all users.\n\n'
            'Local Database: The database stored with this installation on this computer.\n\n'
            'Select Custom Database: Browse to any database file on this computer.'
        )
        explain_label.setFont(QFont('Inter', 10))
        explain_label.setWordWrap(True)
        directory_layout.addWidget(explain_label)
        directory_layout.addSpacing(15)

        btn_shared = QPushButton('Shared Database')
        btn_shared.clicked.connect(self._select_shared)
        directory_layout.addWidget(btn_shared)
        directory_layout.addSpacing(8)

        btn_app = QPushButton('Local Database')
        btn_app.clicked.connect(lambda: self._select_app(app_db))
        directory_layout.addWidget(btn_app)
        directory_layout.addSpacing(8)

        btn_custom = QPushButton('Select Custom Database')
        btn_custom.clicked.connect(self._select_custom)
        directory_layout.addWidget(btn_custom)
        directory_layout.addSpacing(15)

        self._dir_label = QLabel(f'Selected: {self._pending_path}')
        self._dir_label.setFont(QFont('Inter', 10))
        self._dir_label.setWordWrap(True)
        self._dir_label.setAlignment(Qt.AlignCenter)
        directory_layout.addWidget(self._dir_label)

        tabs.addTab(directory_widget, 'Select Directory')
        layout.addWidget(tabs)

    def collectResult(self):
        return self._pending_path

    def _set_pending(self, path):
        self._pending_path = path
        self._dir_label.setText(f'Selected: {path}')

    def _select_shared(self):
        if not os.path.exists(SHARED_DB_PATH):
            QMessageBox.warning(self, 'Not Found',
                f'Shared database not found at:\n{SHARED_DB_PATH}\n\nCheck that the S drive is connected.')
            return
        self._set_pending(SHARED_DB_PATH)

    def _select_app(self, app_db):
        if not os.path.exists(app_db):
            QMessageBox.warning(self, 'Not Found',
                f'No database found at:\n{app_db}\n\nThe app may not have been fully installed.')
            return
        self._set_pending(app_db)

    def _select_custom(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Database File', '', 'Database Files (*.db);;All Files (*)')
        if path:
            self._set_pending(path)

    def _onSubmitClicked(self):
        if not self._pending_path:
            QMessageBox.warning(self, 'No Selection', 'Please select a database before saving.')
            return
        if not os.path.exists(self._pending_path):
            QMessageBox.warning(self, 'Not Found', f'File not found:\n{self._pending_path}')
            return
        reinitialise_db(self._pending_path)
        self.accept()
