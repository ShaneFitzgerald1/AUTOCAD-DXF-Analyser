import sys
from PyQt5.QtWidgets import QApplication
from gui.runinterface import MyWindow
from database.db_models import get_configured_db_path
from database.database_directory import DatabaseDirectoryDialog
from PyQt5.QtCore import QTimer

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MyWindow()
    win.show()

    # Only prompt for DB selection when running as a packaged app with no config saved yet.
    # Timer fires after the event loop starts so the main window is fully visible first.
    if getattr(sys, 'frozen', False):
        if not get_configured_db_path():
            def _startup_directory_dialog():
                DatabaseDirectoryDialog(parent=win).exec_()
                win.update_status_location()
            QTimer.singleShot(500, _startup_directory_dialog)

    sys.exit(app.exec_())   



    # pyinstaller --onefile --windowed --add-data "objectdatabase.db;." --hidden-import=ezdxf --hidden-import=sqlalchemy --hidden-import=sqlalchemy.dialects.sqlite --exclude-module PySide6 --exclude-module PyQt6 main.py


    #pyinstaller --onefile --windowed --add-data "objectdatabase.db;." --add-data "mjhlogo.png;." --hidden-import=ezdxf --hidden-import=sqlalchemy --hidden-import=sqlalchemy.dialects.sqlite --exclude-module PySide6 --exclude-module PyQt6 main.py

    # pyinstaller --windowed --add-data "objectdatabase.db;." --add-data "mjhlogo.png;." --hidden-import=ezdxf --hidden-import=sqlalchemy --hidden-import=sqlalchemy.dialects.sqlite --exclude-module PySide6 --exclude-module PyQt6 main.py