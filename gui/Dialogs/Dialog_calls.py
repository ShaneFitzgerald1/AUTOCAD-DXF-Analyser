import sys, tempfile, shutil, os 
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt 
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QGridLayout, QTableWidget, QLabel, QSizePolicy, QHeaderView, QMessageBox, QFileDialog, QTableWidgetItem, QPushButton, QHBoxLayout, QTabWidget, QAction
from backend.autocorrect import *
from gui.UI_backend.base_table import BaseTable
from utils import resource_path
from gui.UI_backend.table_widget import LabeledTableWidget
from gui.Dialogs.add_object_dialog import AddObjectDialog, database_description
from gui.Dialogs.edit_database_dialog import EditDialog
from database.database_directory import DatabaseDirectoryDialog
from database.db_models import get_configured_db_path, get_db_path
from backend.convertdwg import convertDWG_DXF, convertDXF_DWG
from gui.set_output_file_type import SetOutputFileType
from backend.output_filepaths import dwg_output
from gui.Dialogs.edit_tolerance_dialog import edit_tolerences
from gui.Dialogs.edit_boundary_dialog import edit_boundary
from gui.UI_backend.ui_helpers import create_buttons, create_vbox
from gui.UI_backend.ui_updates import _update_status


def _open_add_object_dialog(self, names):
        dlg = AddObjectDialog(names, parent=self)
        dlg.accepted.connect(self.reload_file)
        dlg.exec_()


def _open_description_dialog(self): 
        dlg = database_description(parent=self)
        dlg.exec_()


def _open_edit_dialog(self, mode):
        EditDialog(mode=mode, parent=self).exec_()
        if self.original_filepath:
            self.reload_file()

def _open_directory_dialog(self):
    dialog = DatabaseDirectoryDialog(parent=self)
    dialog.exec_()
    # self.update_status_location()
    _update_status(self, 'File Loaded ✅' if self.original_filepath else 'No File Loaded', False)


def _open_output_type_dialog(self):
    """Finds out what the selected output path is by the user """
    dialog = SetOutputFileType(current_type=self.output_file_type, parent=self)
    if dialog.exec_() == SetOutputFileType.Accepted:
        self.output_file_type = dialog.collectResult()
        self._update_status()
        if self.original_filepath is None: 
            return
        if self.original_filepath is not None: 
            self.reload_file()

def _open_tolerance_dialog(self):
    dialog = edit_tolerences(parent=self)
    if dialog.exec_() == edit_tolerences.Accepted:
        if self.original_filepath:
            self.reload_file()

def _open_boundary_dialog(self):
    dialog = edit_boundary(parent=self)     
    if dialog.exec_() == edit_boundary.Accepted:
        if self.original_filepath:
            self.reload_file()                 