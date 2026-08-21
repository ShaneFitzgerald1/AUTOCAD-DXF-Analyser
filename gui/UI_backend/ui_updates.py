import sys, tempfile, shutil, os 
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt 

from database.db_models import get_configured_db_path, get_db_path



def set_correct_tab_colour(self, tab): 
    tab.setAutoFillBackground(True)
    palette = tab.palette()
    palette.setColor(palette.Window, QtGui.QColor('white'))
    tab.setPalette(palette)


def update_file_loaded_label(self, reset): 
    check = "\u2705"      # ✅
    cross = "\u274C"      # ❌
    warning = "\u26A0"    # ⚠
    display_path = getattr(self, 'display_filepath', self.original_filepath)
    current_file = os.path.basename(display_path) if display_path else 'None'
    name = os.path.splitext(current_file)[0]
    if reset:
        self.status_file_label.setText(f'Current File: <span style="color: #FF0000;">None</span>')
    else:
        self.status_file_label.setText(f'Current File: <span style="color: #90EE90;">{name}{check}</span>')


def update_database_directory_label(self): 
    db_path = get_configured_db_path() or get_db_path()     
    self.status_db_label.setText(f'Database: {db_path}')    

def update_output_file_type(self): 
    self.status_output_label.setText(f'File Output Type: {self.output_file_type}')
         
     
def populate_results_table(self): 
        #populate the results table  
        self.table1.populate(self.on_line_points)
        self.table2.populate(self.wall_slope_intercept)
        self.table3.populate(self.all_lines_table)
        self.table4.populate(self.filtered_walls)  


