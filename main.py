import sys
from PyQt5.QtWidgets import QApplication
from gui.runinterface import MyWindow
from database.db_models import get_configured_db_path
from database.database_directory import DatabaseDirectoryDialog
from gui.UI_backend.ui_updates import update_database_directory_label
from PyQt5.QtCore import QTimer
from qt_material import apply_stylesheet

if __name__ == '__main__':
    app = QApplication(sys.argv) 
    apply_stylesheet(app, theme='light_dark.xml')
    win = MyWindow()
    win.show()

    # Only prompt for DB selection when running as a packaged app with no config saved yet.
    # Timer fires after the event loop starts so the main window is fully visible first.
    if getattr(sys, 'frozen', False):
        if not get_configured_db_path():
            def _startup_directory_dialog():
                DatabaseDirectoryDialog(parent=win).exec_()
                update_database_directory_label(win)
            QTimer.singleShot(500, _startup_directory_dialog)

    sys.exit(app.exec_())   




    # pyinstaller --windowed --add-data "objectdatabase.db;." --add-data "mjhlogo.png;." --hidden-import=ezdxf --hidden-import=sqlalchemy --hidden-import=sqlalchemy.dialects.sqlite --exclude-module PySide6 --exclude-module PyQt6 main.py




    # Remove-Item "$env:APPDATA\MJHInterface" -Recurse -Force
