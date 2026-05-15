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

def _update_status(self, app_state=None, reset=False):
        """Function that resets teh status label based on weather there is a file imported"""
        if app_state is not None:
            self.app_state = app_state

        display_path = getattr(self, 'display_filepath', self.original_filepath)
        current_file = os.path.basename(display_path) if display_path else 'None'
        name = os.path.splitext(current_file)[0]
        db_path = get_configured_db_path() or get_db_path()

        if reset:
            self.app_state = 'No File Loaded'
            self.status_label.setText(
                f'Current File: None\n'
                f'App State: No File Loaded\n'
                f'Database: {db_path}\n'
                f'File Output Type: {self.output_file_type}'
            )
        else:
            self.status_label.setText(
                f'Current File: {name}\n'
                f'App State: {self.app_state}\n'
                f'Database: {db_path}\n'
                f'File Output Type: {self.output_file_type}'
            )      

# def update_status_menu(self, reset): 

#     #dont think we need to update the db_label and output_label here 

#     display_path = getattr(self, 'display_filepath', self.original_filepath)
#     current_file = os.path.basename(display_path) if display_path else 'None'
#     name = os.path.splitext(current_file)[0]
#     db_path = get_configured_db_path() or get_db_path()    

#     if reset:
#         self.status_file_label.setText(f'Current File: None')
#         self.status_db_label.setText(f'Database: {db_path}')
#         self.status_output_label.setText(f'File Output Type: {self.output_file_type}')

#     else:
#         self.status_file_label.setText(f'Current File: {name}')
#         self.status_db_label.setText(f'Database: {db_path}')
#         self.status_output_label.setText(f'File Output Type: {self.output_file_type}')


def update_file_loaded_label(self, reset): 
    display_path = getattr(self, 'display_filepath', self.original_filepath)
    current_file = os.path.basename(display_path) if display_path else 'None'
    name = os.path.splitext(current_file)[0]
    if reset:
        self.status_file_label.setText(f'Current File: None')
    else:
        self.status_file_label.setText(f'Current File: {name}')

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


