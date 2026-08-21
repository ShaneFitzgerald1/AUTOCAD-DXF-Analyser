import tempfile, shutil, os 
from PyQt5.QtGui import QFont, QPixmap, QIcon, QColor
from PyQt5.QtCore import Qt 
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QGridLayout, QLabel, QMessageBox, QFileDialog, QPushButton, QHBoxLayout, QTabWidget, QAction, QListWidget, QListWidgetItem
from backend.autocorrect import *
from gui.UI_backend.base_table import BaseTable
from utils import resource_path
from gui.UI_backend.table_widget import LabeledTableWidget
from gui.Dialogs.add_object_dialog import database_description
from database.database_directory import DatabaseDirectoryDialog
from database.db_models import get_configured_db_path, get_db_path
from backend.convertdwg import convertDWG_DXF
from backend.output_filepaths import dwg_output
from gui.UI_backend.ui_helpers import create_buttons
from gui.Dialogs.Dialog_calls import _open_add_object_dialog, _open_edit_dialog, _open_directory_dialog, _open_output_type_dialog, _open_tolerance_dialog, _open_boundary_dialog
from gui.UI_backend.ui_updates import set_correct_tab_colour, populate_results_table, update_file_loaded_label


class MyWindow(QMainWindow):
    def __init__(self):
        super(MyWindow, self).__init__()
        self.setGeometry(0, 0, 1920, 1000)
        self.setWindowTitle('Drawing Analyser')
        self.setWindowIcon(QIcon(resource_path('mjhlogo.png')))
        self.original_filepath = None
        self.output_file_type = 'DWG'
        self.app_state = 'No File Loaded'
        self.recent_files = []
        self.extract_oda_directory()
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab1 = QWidget()
        self.tab1_grid = QGridLayout()
        vbox_import = QVBoxLayout() #The vbox for hte main import tab, what is seen when GUI is intiially opened

        # Logo in top left
        logo_label = QLabel()
        pixmap = QPixmap(resource_path('mjhlogo.png'))
        scaled_pixmap = pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignLeft)
        self.tab1_grid.addWidget(logo_label, 0, 0, 1, 1)  # row 0, col 0

        #Instruction label 
        Instruction = QLabel(f'Import a DXF/DWG File to Begin Analysis')
        Instruction.setAlignment(Qt.AlignCenter)
        Instruction.setFont(QFont('Roboto', 15, QFont.Bold))
        self.tab1_grid.addWidget(Instruction, 0, 0, 1, 3)

        self.db_path = get_configured_db_path() or get_db_path()

        # Status label — row 0, col 2
        # self.db_path = get_configured_db_path() or get_db_path()
        # self.appstatus_vbox = QVBoxLayout()
        # self.appstatus_vbox.setAlignment(Qt.AlignTop | Qt.AlignRight)
        # self.status_label = QLabel(f'Current File: None\nApp State: No File Loaded\nDatabase: {self.db_path}\n File Output Type: {self.output_file_type}')
        # self.status_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        # self.status_label.setFont(QFont('Roboto', 14))
        # self.appstatus_vbox.addWidget(self.status_label)
        # self.tab1_grid.addLayout(self.appstatus_vbox, 0, 2, 1, 1)

        # Edit buttons — row 1, col 2, fixed position independent of status label
        purple_style = "QPushButton {background-color: #6A006A; color: white;} QPushButton:hover{background-color: #3B0060;}"
        purple_hbox = QHBoxLayout()
        purple_hbox.addStretch()
        purple_vbox = QVBoxLayout()
        purple_vbox.setAlignment(Qt.AlignTop)
        purple_vbox.setSpacing(7)
        purple_vbox.setContentsMargins(0, 0, 20, 0)
        self.Button4 = create_buttons('Edit Object Database',        lambda: _open_edit_dialog(self, 'object'),   purple_vbox, purple_style)
        self.Button5 = create_buttons('Edit Line Category Database', lambda: _open_edit_dialog(self, 'category'), purple_vbox, purple_style)
        self.Button6 = create_buttons('Set Database Directory', lambda: _open_directory_dialog(self), purple_vbox, purple_style)
        self.Button7 = create_buttons('Database Description', lambda: database_description(parent=self).exec_(), purple_vbox, purple_style)
        purple_hbox.addLayout(purple_vbox)
        self.tab1_grid.addLayout(purple_hbox, 1, 0, 1, 3)
        

        #Installing push buttons 
        vbox_t = QVBoxLayout()
        hbox1 = QHBoxLayout()
        hbox1.addStretch()
        self.Button1 = create_buttons('Import AutoCAD File', self.import_dxf_file, hbox1, "QPushButton {background-color: #0000DC; color: white;} QPushButton:hover{background-color: #00008B;}")
        hbox1.addSpacing(100)
        self.Button2 = create_buttons('View Issues', self.fix_errors, hbox1, "QPushButton {background-color: #0000DC; color: white;} QPushButton:hover{background-color: #00008B;}")
        hbox1.addStretch()
        vbox_t.addLayout(hbox1)

        hbox2 = QHBoxLayout()
        self.Button3 = create_buttons('Reset App', self.reset_app, hbox2, "QPushButton {background-color: #0000DC; color: white;} QPushButton:hover{background-color: #00008B;}")
        vbox_t.addLayout(hbox2)
        # vbox_t.setContentsMargins(0, 0, 310, 0)

        self.tab1_grid.addLayout(vbox_t, 2, 0, 1, 3)

        bottom_spacer = QWidget()
        self.tab1_grid.addWidget(bottom_spacer, 3, 0, 2, 3)

        self.tab1_grid.setRowStretch(0, 0)
        self.tab1_grid.setRowStretch(1, 0)
        self.tab1_grid.setRowStretch(2, 0)
        self.tab1_grid.setRowStretch(3, 1)
        self.tab1_grid.setRowMinimumHeight(0, 250)
        self.tab1_grid.setRowMinimumHeight(1, 150)
        self.tab1_grid.setRowMinimumHeight(2, 100)


        # ---- Summary results placeholder in row 2 ----
        self.summary_container = QWidget()
        self.summary_container.setVisible(False)  # hidden until file loads
        self.tab1_grid.addWidget(self.summary_container, 3, 0, 1, 3)

        self.tab1_grid.setRowStretch(0, 0)
        self.tab1_grid.setRowStretch(1, 0)
        self.tab1_grid.setRowStretch(2, 1)  # summary row expands

        self.tab1_grid.setColumnStretch(0, 1)
        self.tab1_grid.setColumnStretch(1, 1)
        self.tab1_grid.setColumnStretch(2, 0)

        self.tab1_grid.setColumnMinimumWidth(2, 220)

        recent_label = QLabel("Recently Accessed Files")
        recent_label.setFont(QFont('Roboto', 10, QFont.Bold))
        recent_label.setAlignment(Qt.AlignCenter)
        recent_label.setStyleSheet("color: black;")
        self.recent_list = QListWidget()
        self.recent_list.setFont(QFont('Roboto', 9))
        self.recent_list.setFixedWidth(210)
        # self.recent_list.itemDoubleClicked.connect(self._load_recent_file)
        recent_vbox = QVBoxLayout()
        self.recent_list.setMaximumHeight(150)
        self.recent_list.setMaximumWidth(150)
        recent_vbox.setAlignment(Qt.AlignTop)
        recent_vbox.setContentsMargins(0, 8, 8, 0)
        recent_vbox.addWidget(recent_label)
        recent_vbox.addWidget(self.recent_list)
        recent_vbox.setContentsMargins(0, 0, 25, 60)
        self.tab1_grid.addLayout(recent_vbox, 0, 2, 1, 1)


        #Setting the tab itself
        self.tab1.setLayout(self.tab1_grid)
        self.tabs.addTab(self.tab1, "Import")

        set_correct_tab_colour(self, self.tab1)


        menubar = self.menuBar()
        self.setStyleSheet("QMainWindow { background-color: black; }")

        
        menubar.setStyleSheet("""
            QMenuBar {background-color: black;
                color: white;}QMenuBar::item:selected {
                background-color: #333333;}""")


        # self.tabs.setStyleSheet("""QTabBar {background-color: black;}
        #                         QTabBar::tab {background-color: #cccccc;color: black;padding: 4px 10px;}
        # QTabBar::tab:selected { background-color: white;color: black;}
        # QTabWidget::pane {background-color: white;}""")

        output_action = QAction('Set Output File Type', self)
        output_action.triggered.connect(lambda: _open_output_type_dialog(self))
        menubar.addAction(output_action)

        tolerance_action = QAction('Adjust Tolerances', self)
        tolerance_action.triggered.connect(lambda: _open_tolerance_dialog(self))
        menubar.addAction(tolerance_action)

        set_boundary_action = QAction('Set Boundary', self)
        set_boundary_action.triggered.connect(lambda: _open_boundary_dialog(self))
        menubar.addAction(set_boundary_action)

        status_widget = QWidget()
        status_layout = QHBoxLayout(status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.status_file_label = QLabel('File: <span style="color: red;">None</span>')
        self.status_file_label.setTextFormat(Qt.RichText)
        self.status_file_label.setFont(QFont('Roboto', 9))
        self.status_file_label.setAlignment(Qt.AlignCenter)
        self.status_file_label.setStyleSheet("color: white;")

        self.status_db_label = QLabel(f"Database: {self.db_path}")
        self.status_db_label.setFont(QFont('Roboto', 9))
        self.status_db_label.setAlignment(Qt.AlignCenter)
        self.status_db_label.setStyleSheet("color: white;")

        self.status_output_label = QLabel(f"Output: {self.output_file_type}")
        self.status_output_label.setFont(QFont('Roboto', 9))
        self.status_output_label.setAlignment(Qt.AlignCenter)
        self.status_output_label.setStyleSheet("color: white;")

        status_layout.addWidget(self.status_file_label, 1)
        status_layout.addWidget(self.status_db_label, 1)
        status_layout.addWidget(self.status_output_label, 1)

        self.statusBar().addPermanentWidget(status_widget, 1)
        self.statusBar().setStyleSheet("QStatusBar { background-color: #000000; padding: 4px; }")

        
    def create_results_tab(self): 
        tab2 = QWidget()
        grid = QGridLayout()

        headers_list_table1 = ['Name', 'x', 'y', 'Angle', 'Wall', 'Type', 'On Line', 'Mistake', 'On Channel Outline']
        headers_list_table2 = ['Length', 'Slope', 'Y Intercepts']
        headers_list_table3 = ['Name', 'X Start', 'Y Start', 'X End', 'Y End', 'On Channel Outline']
        headers_list_table4 = ['X', 'Y']

        vbox1 = LabeledTableWidget('Block Reference Points', headers_list_table1, BaseTable.BLUE)
        vbox2 = LabeledTableWidget('Wall Properties', headers_list_table2, BaseTable.BLUE)
        vbox3 = LabeledTableWidget('Line Properties', headers_list_table3, BaseTable.BLUE)
        vbox4 = LabeledTableWidget('Corner Points', headers_list_table4, BaseTable.BLUE)

        self.table1 = vbox1.table  #pulling the table out of the vbox
        self.table2 = vbox2.table
        self.table3 = vbox3.table
        self.table4 = vbox4.table

        #Defining the layout
        grid.addLayout(vbox1, 0, 0, 2, 1)
        grid.addLayout(vbox4, 2, 0, 1, 1)
        grid.addLayout(vbox2, 0, 1, 1, 1)
        grid.addLayout(vbox3, 1, 1, 2, 1)

        grid.setRowStretch(0, 1)   
        grid.setRowStretch(1, 1)
        grid.setRowStretch(2, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        tab2.setLayout(grid)    
        
        self.tabs.addTab(tab2, "Results") #add tab 2 to the widget
        
        populate_results_table(self)

        #OCD, setting each tab to a specific colour of white 
        set_correct_tab_colour(self, tab2)

    def results_fixation(self): 
        tab3 = QWidget()
        grid = QGridLayout()

        block_ref_headers = ['Name', 'x', 'y']
        line_headers = ['Name', 'x start', 'y start', 'x end', 'y end']

        # print(f'These are the mistake points {self.mistake_points}')
        if self.bed_check == 1: 
            if len(self.bedit_mistake_points) > 0: 
                vbox1 = LabeledTableWidget('Insert Block Reference Errors Located at Points:',block_ref_headers,BaseTable.RED)
                vbox2 = LabeledTableWidget('Suggestion. Fix Block Reference Errors to Points:',block_ref_headers, BaseTable.GREEN)
                self.table5 = vbox1.table
                self.table6 = vbox2.table
                grid.addLayout(vbox1, 0, 0, 1, 1)
                grid.addLayout(vbox2, 0, 1, 1, 1)
                self.table5.populate(self.bedit_mistake_points)
                self.table6.populate(self.bedit_corrected_blocks)

        else:
            if len(self.mistake_points) > 0: 
                vbox1 = LabeledTableWidget('Insert Block Reference Errors Located at Points:',block_ref_headers,BaseTable.RED)
                vbox2 = LabeledTableWidget('Suggestion. Fix Block Reference Errors to Points:',block_ref_headers, BaseTable.GREEN)
                self.table5 = vbox1.table
                self.table6 = vbox2.table
                grid.addLayout(vbox1, 0, 0, 1, 1)
                grid.addLayout(vbox2, 0, 1, 1, 1)
                self.table5.populate(self.mistake_points)
                self.table6.populate(self.corrected_blocks)
       
        if len(self.line_mistakes) > 0: 
            vbox3 = LabeledTableWidget('Insert Line Errors Located at Points: ',line_headers, BaseTable.RED)
            vbox4 = LabeledTableWidget('Suggestion. Fix Insert Insert Errors to Points:',line_headers, BaseTable.GREEN)
            self.table7 = vbox3.table
            self.table8 = vbox4.table
            grid.addLayout(vbox3, 1, 0, 1, 1)
            grid.addLayout(vbox4, 1, 1, 1, 1)
            self.table7.populate(self.line_mistakes)
            self.table8.populate(self.fixed_lines)

        if len(self.line_duplicate_points) > 0: 
            vbox5 = LabeledTableWidget('Suggestion. Remove Duplicate Line at:', line_headers, BaseTable.RED)
            self.tabledup = vbox5.table
            grid.addLayout(vbox5, 2, 0, 1, 2)
            self.tabledup.populate(self.line_duplicate_points)    

        set_correct_tab_colour(self, tab3)
        tab3.setLayout(grid)
        self.tabs.addTab(tab3, "Error Fixation") 

   

    def database_results(self): 
        tab4 = QWidget() 
        grid = QGridLayout() 

        vbox1 = QVBoxLayout() 
        vbox2 = QVBoxLayout()    

        #Object Database 

        tables_hbox1 = QHBoxLayout() 

        if len(self.post_rejected_blocks) > 0: 
            titlelabel1 = QLabel('Object Database') 
            titlelabel1.setAlignment(Qt.AlignCenter)
            titlelabel1.setFont(QFont('Inter', 14, QFont.Bold))

            subtitlelabel1 = QLabel('The Object Database ensures all autocad objects in the file are expected. Objects are checked against the database based on their name, object type, category and weather it should be on the channel outline. Any object with an unexpected name or position are returned below')
            subtitlelabel1.setAlignment(Qt.AlignCenter)
            subtitlelabel1.setFont(QFont('Inter', 10))

            vbox1.addWidget(titlelabel1)
            vbox1.addWidget(subtitlelabel1)
    
            left_vbox = QVBoxLayout()
            left_label = QLabel(f"There was {len(self.post_rejected_blocks)} Rejected Block(s) {self.cross} from the Object Database ")
            left_label.setFont(QFont('Inter', 10))
            left_vbox.addWidget(left_label)

            block_headers = ['Name', 'x', 'y', 'Reason']
            left_vbox_internal = LabeledTableWidget('Unexpected Blocks:',block_headers,BaseTable.RED)
            self.table9 = left_vbox_internal.table
            left_vbox.addLayout(left_vbox_internal)
            tables_hbox1.addLayout(left_vbox)
            self.table9.populate(self.post_rejected_blocks)

        if len(self.post_rejected_lines) > 0:    
            right_vbox = QVBoxLayout() 
            right_label = QLabel(f'There was {len(self.post_rejected_lines)} Rejected Line(s) {self.cross} from the Object Database')    
            right_label.setFont(QFont('Inter', 10))
            right_vbox.addWidget(right_label)
    
            line_headers = ['Name', 'x start', 'y tart', 'x end', 'y end', 'Reason']
            right_vbox_internal = LabeledTableWidget('Unexpected Lines:', line_headers, BaseTable.RED)
            self.table10 = right_vbox_internal.table
            right_vbox.addLayout(right_vbox_internal)
            self.table10.populate(self.post_rejected_lines)
            tables_hbox1.addLayout(right_vbox)

        vbox1.addLayout(tables_hbox1)

        #Category Database 
        if len(self.all_fail) > 0:
            titlelabel2 = QLabel('Category Database')
            titlelabel2.setAlignment(Qt.AlignCenter)
            titlelabel2.setFont(QFont('Inter', 14, QFont.Bold))

            subtitlelabel2 = QLabel('The category Database checks all objects to ensure they start and end on the correct Block/Line.')
            subtitlelabel2.setAlignment(Qt.AlignCenter)
            subtitlelabel2.setFont(QFont('Inter', 10))

            main_label = QLabel(f'There are {len(self.line_name)} Accepted Lines {self.check} and {len(self.all_fail)} Rejected Line(s) {self.cross} by the Category Database.')
            main_label.setFont(QFont('Inter', 10))
            vbox2.addWidget(titlelabel2)
            vbox2.addWidget(subtitlelabel2)
            vbox2.addWidget(main_label)
            
            category_headers = ['Name', 'x start', 'y start', 'Start Object Category', 'x end', 'y end', 'End Object Category', 'Reason']
            vbox_internal = LabeledTableWidget('Failed Lines', category_headers, BaseTable.RED)
            self.table11 = vbox_internal.table
            vbox2.addLayout(vbox_internal)
            self.table11.populate(self.all_fail)

        # Add the vbox into the grid
        grid.addLayout(vbox1, 0, 0)
        grid.addLayout(vbox2, 1, 0)


        #button for adding unmatches line or block names to the database 
        if len(self.blockname_unmatched) > 0 or len(self.linename_unmatched) > 0:
            combined = self.blockname_unmatched + self.linename_unmatched
            seen = set()
            unique_names = [n for n in combined if not (n in seen or seen.add(n))]

            add_btn = QPushButton('Add Missing Objects to Database')
            # add_btn.clicked.connect(lambda: self._open_add_object_dialog(unique_names))
            add_btn.clicked.connect(lambda: _open_add_object_dialog(self, unique_names))
            vbox1.addWidget(add_btn, alignment=Qt.AlignLeft)

        tab4.setLayout(grid)
        set_correct_tab_colour(self, tab4)
        self.tabs.addTab(tab4, "Database Results")
        

    check = "\u2705"      # ✅
    cross = "\u274C"      # ❌
    warning = "\u26A0"    # ⚠

    def results_summary(self): 
        godvbox1 = QVBoxLayout()
        godvbox2 = QVBoxLayout() 

        tab5 = QWidget() 
        grid = QGridLayout() 
        vbox1 = QVBoxLayout()
        vbox2 = QVBoxLayout()
        vboxgeo1 = QVBoxLayout() 
        vboxgeo2 = QVBoxLayout() 
        hboxgeo1 = QHBoxLayout()
        hboxdata = QHBoxLayout() 
        vboxdata1 = QVBoxLayout() 
        vboxdata2 = QVBoxLayout() 

        QMLabel = QLabel('Results Summary')
        QMLabel.setAlignment(Qt.AlignCenter)
        QMLabel.setFont(QFont('Inter', 14, QFont.Bold))

        QtitLabel = QLabel('Geometry Engine') 
        QtitLabel.setAlignment(Qt.AlignCenter)
        QtitLabel.setFont(QFont('Inter', 12, QFont.Bold))

        if self.bed_check == 1: ### if all blocks are inside a module 

            Qbeditlabel = QLabel(f'{self.warning} All contents in the Module are inside a single Block Reference, Error has been fixed {self.warning}')
            Qbeditlabel.setAlignment(Qt.AlignCenter)
            Qbeditlabel.setFont(QFont('Inter', 11, QFont.Bold))
            Qbeditlabel.setStyleSheet('color: red;')
            vbox1.addWidget(Qbeditlabel)

            if len(self.bedit_mistake_points) > 0: 
                QLabel1 = QLabel(f'There were {len(self.on_line_points) - len(self.bedit_mistake_points)} Block(s) Accepted {self.check} and {len(self.bedit_mistake_points)} Block(s) Rejected {self.cross} by the Geometry Engine')
                QLabel1.setAlignment(Qt.AlignCenter)
                QLabel1.setFont(QFont('Inter', 10))
                vboxgeo1.addWidget(QLabel1)

                if len(self.bedit_mistake_points) == 1: #Getting the language correct 
                    QLabel2 = QLabel(f'{len(self.bedit_corrected_blocks)} Block was found to be incorrect {self.warning} by the Geometry Engine')
                else:
                    QLabel2 = QLabel(f'{len(self.bedit_corrected_blocks)} Blocks were found to be incorrect {self.warning} by the Geometry Engine')

                QLabel2.setAlignment(Qt.AlignCenter)
                QLabel2.setFont(QFont('Inter', 10))
                vboxgeo1.addWidget(QLabel2)


            if len(self.bedit_mistake_points) < 1: 
                QLabel1 = QLabel(f'All {len(self.on_line_points)} Blocks were accepted by the Geometry Engine {self.check}')
                QLabel1.setAlignment(Qt.AlignCenter)
                QLabel1.setFont(QFont('Inter', 10))
                vboxgeo1.addWidget(QLabel1)

        else: # if the file is normal 
            if len(self.mistake_points) > 0: 
                QLabel1 = QLabel(f'There were {len(self.on_line_points) - len(self.mistake_points)} Block(s) Accepted {self.check} and {len(self.mistake_points)} Block(s) Rejected {self.cross} by the Geometry Engine')
            

            if len(self.mistake_points) < 1 and len(self.on_line_points) > 0: 
                QLabel1 = QLabel(f'All {len(self.on_line_points)} Blocks were accepted by the Geometry Engine {self.check}')

            if len(self.mistake_points) < 1 and len(self.on_line_points) < 1: 
                QLabel1 = QLabel(f'No Blocks in the drawing are within the set Boundary. {self.warning}')

            QLabel1.setAlignment(Qt.AlignCenter)
            QLabel1.setFont(QFont('Inter', 10))
            vboxgeo1.addWidget(QLabel1)

            ####

        if len(self.line_mistakes) > 0: 
            QLabel3 = QLabel(f'There were {len(self.all_lines_table) - len(self.line_mistakes)} Line(s) Accepted {self.check} and {len(self.line_mistakes)} Line(s) Rejected {self.cross} by the Geometry Engine')
            QLabel3.setAlignment(Qt.AlignCenter)
            QLabel3.setFont(QFont('Inter', 10))

            vboxgeo2.addWidget(QLabel3)

        if len(self.line_duplicate_points) > 0: #If there are any duplicate lines present
            if len(self.line_duplicate_points) == 1:
                QLabeldup = QLabel(f'{self.warning} There was {len(self.line_duplicate_points)} Duplicate Line present {self.warning}') 
            else:
                QLabeldup = QLabel(f'{self.warning} There were {len(self.line_duplicate_points)} Duplicate Lines present {self.warning}.') 
                      
            QLabeldup.setAlignment(Qt.AlignCenter)
            QLabeldup.setFont(QFont('Inter', 10))
            vboxgeo2.addWidget(QLabeldup)    

        if len(self.line_mistakes) < 1 and len(self.all_lines_table) > 0: 
            QLabel3 = QLabel(f'All {len(self.all_lines_table)} Lines were accepted by the Geometry Engine {self.check}')  

        if len(self.all_lines_table) < 1 and len(self.line_mistakes) < 1: 
            QLabel3 = QLabel(f'No Lines in the drawing are within the set Boundary. {self.warning}')  
        QLabel3.setAlignment(Qt.AlignCenter)
        QLabel3.setFont(QFont('Inter', 10))
        vboxgeo2.addWidget(QLabel3)

        vbox1.addWidget(QMLabel)
        vbox1.addWidget(QtitLabel)

        hboxgeo1.addLayout(vboxgeo1)
        hboxgeo1.addLayout(vboxgeo2)

        vbox1.addLayout(hboxgeo1)

        if len(self.corrected_blocks) > 0 or len(self.fixed_lines) > 0: 
            QLabelerr = QLabel(f'{self.warning}See Error Fixation Tab for more details {self.warning}') 
            QLabelerr.setAlignment(Qt.AlignCenter)  # ← you had QLabel3 here by mistake
            QLabelerr.setFont(QFont('Inter', 10))
            vbox1.addWidget(QLabelerr)

        #Database stuff 

        QtitLabel2 = QLabel('Database Rules')
        QtitLabel2.setAlignment(Qt.AlignCenter)
        QtitLabel2.setFont(QFont('Inter', 12, QFont.Bold))
        vbox2.addWidget(QtitLabel2)

        if (len(self.post_accepted_blocks) < 1 and len(self.post_rejected_blocks) < 1 and len(self.post_accepted_lines) < 1 and 
            len(self.post_rejected_lines) < 1 and len(self.line_name) < 1 and len(self.all_fail) < 1):
            Qidklabel = QLabel(f'{self.cross} There are no blocks or lines present to be analysed by the Database')
            Qidklabel.setAlignment(Qt.AlignCenter)
            Qidklabel.setFont(QFont('Inter', 10))
            vbox2.addWidget(Qidklabel)

        else:    

            if len(self.post_accepted_blocks) > 0 or len(self.post_rejected_blocks) > 0 or len(self.post_accepted_lines) > 0 or len(self.post_rejected_lines) > 0:
                QtitLabel3 = QLabel('Object DataBase')
                QtitLabel3.setAlignment(Qt.AlignCenter)
                QtitLabel3.setFont(QFont('Inter', 11, QFont.Bold))
                vboxdata1.addWidget(QtitLabel3)

                if len(self.post_accepted_blocks) > 0 or len(self.post_rejected_blocks):  

                    if (len(self.post_rejected_blocks)) > 0: 
                        QLabel5 = QLabel(f'There were {len(self.post_accepted_blocks)} Block(s) Accepted {self.check} and {len(self.post_rejected_blocks)} Block(s) Rejected {self.cross} by the Object Database')
                    else:     
                        QLabel5 = QLabel(f'All {len(self.post_accepted_blocks)} Blocks were accepted by the Object Database {self.check}')  
            
                    QLabel5.setAlignment(Qt.AlignCenter)
                    QLabel5.setFont(QFont('Inter', 10))
                    vboxdata1.addWidget(QLabel5)

                if len(self.post_accepted_lines) > 0 or len(self.post_rejected_lines) > 0:
                    if len(self.post_rejected_lines) > 0: 
                        QLabel6 = QLabel(f'There were {len(self.post_accepted_lines)} Line(s) Accepted {self.check} and {len(self.post_rejected_lines)} Line(s) Rejected {self.cross} by the Object Database ')  
                        vboxdata1.addWidget(QLabel6)

                    else: 
                        QLabel6 = QLabel(f'All {len(self.post_accepted_lines)} Lines were accepted by the Object Database {self.check} ')    

                    QLabel6.setAlignment(Qt.AlignCenter)
                    QLabel6.setFont(QFont('Inter', 10))
                    vboxdata1.addWidget(QLabel6)

                hboxdata.addLayout(vboxdata1)    
                vbox2.addLayout(hboxdata)

            #Category database 

            if len(self.line_name) > 0 or len(self.all_fail) > 0:
                QtitLabel4 = QLabel(f'Category Database')
                QtitLabel4.setAlignment(Qt.AlignCenter)
                QtitLabel4.setFont(QFont('Inter', 11, QFont.Bold))
                vboxdata2.addWidget(QtitLabel4)

                if len(self.all_fail) > 0: 
                    QLabel7 = QLabel(f'There were {len(self.line_name)} Accepted Line(s) {self.check} and {len(self.all_fail)} Rejected Line(s) {self.cross} from the Category Database ')
                else: 
                    QLabel7 = QLabel(f'All {len(self.line_name)} Lines were accepted by the Category Database {self.check}')

                QLabel7.setAlignment(Qt.AlignCenter)
                QLabel7.setFont(QFont('Inter', 10))
                vboxdata2.addWidget(QLabel7)
            
            if len(self.all_fail) > 0 or len(self.post_rejected_lines) > 0 or len(self.post_rejected_blocks) > 0: 
                dataerror2 = QLabel(f'{self.warning}See Database Results Tab for more details {self.warning}')
                dataerror2.setAlignment(Qt.AlignCenter)
                dataerror2.setFont(QFont('Inter', 10))
                vbox2.addWidget(dataerror2)
        
            hboxdata.addLayout(vboxdata2)

        container_geo = QWidget()
        container_geo.setObjectName("summary_container")
        container_geo.setStyleSheet("#summary_container { border: 1px solid black; border-radius: 5px; }")

        container_cat = QWidget()
        container_cat.setObjectName("summary_container")
        container_cat.setStyleSheet("#summary_container { border: 1px solid black; border-radius: 5px; }")

        container2 = QWidget()
        container2.setObjectName("summary_container")
        container2.setStyleSheet("#summary_container { border: 1px solid black; border-radius: 5px; }")
      
        container_geo.setLayout(vbox1)
        container_cat.setLayout(vbox2)

        #setting the boxses
        container2.setLayout(godvbox2)

        godvbox2.addWidget(container_geo)
        godvbox2.addWidget(container_cat)

        grid.addLayout(godvbox1, 0, 0)  
        grid.addWidget(container2, 1, 0)
        tab5.setLayout(grid)

        # Clear any previous layout on the container
        if self.summary_container.layout():
            QWidget().setLayout(self.summary_container.layout())

        self.summary_container.setLayout(godvbox2)
        self.summary_container.setVisible(True)  

        if len(self.blockname_unmatched) > 0 or len(self.linename_unmatched) > 0:
            combined = self.blockname_unmatched + self.linename_unmatched
            seen = set()
            unique_names = [n for n in combined if not (n in seen or seen.add(n))]
            _open_add_object_dialog(self, unique_names)
   

    def import_dxf_file(self):
        update_file_loaded_label(self, True)
        self.summary_container.setVisible(False)
        self.delete_temp_folder()

        while self.tabs.count() > 1:
            self.tabs.removeTab(1)

        filepath, _ = QFileDialog.getOpenFileName(None, "Select DXF File", "", "DXF Files (*.dxf *.dwg);;All Files (*)")
        ext = filepath[-3:].lower()

        if filepath and ext == 'dxf':
            self.original_filepath = filepath
            self.display_filepath = filepath
            self._run_analysis(filepath, None) 
            self.imported_dwg = False 

        if filepath and ext == 'dwg':
            self.display_filepath = filepath  # shown in status label
            self.temp_dir = tempfile.mkdtemp()
            filename = os.path.basename(filepath)
            temp_filepath = os.path.join(self.temp_dir, filename)
            shutil.copy2(filepath, temp_filepath)
            self.dwg_original_filepath = filepath #setting the original filepath of the dwg for later 

            dxf_paths = convertDWG_DXF(self.temp_dir, self.temp_dir, self.oda_dir)
            self.dwg_conv_dxf_filepath = dxf_paths[0]
            self.original_filepath = filepath  # used for analysis
            self._run_analysis(self.dwg_conv_dxf_filepath, filepath)
            self.imported_dwg = True 

        return filepath    
    
    

    def _add_recent_file(self, filepath):
        if filepath in self.recent_files:
            self.recent_files.remove(filepath)
        self.recent_files.insert(0, filepath)
        self._refresh_recent_list()

    def _refresh_recent_list(self):
        self.recent_list.clear()
        for i, path in enumerate(self.recent_files):
            list_item = QListWidgetItem(os.path.basename(path))
            list_item.setData(Qt.UserRole, path)
            if i == 0:
                list_item.setFont(QFont('Roboto', 10, QFont.Bold))
                list_item.setForeground(QColor('#2E8B57'))
            else:
                list_item.setFont(QFont('Roboto', 9))
                list_item.setForeground(QColor('#000000'))
            self.recent_list.addItem(list_item)

    def _load_recent_file(self, item):
        self.import_dxf_file(filepath=item.data(Qt.UserRole))



    def reload_file(self):
        if getattr(self, 'imported_dwg', False):
            self.delete_temp_folder()
            self.temp_dir = tempfile.mkdtemp()
            filename = os.path.basename(self.dwg_original_filepath)
            temp_filepath = os.path.join(self.temp_dir, filename)
            shutil.copy2(self.dwg_original_filepath, temp_filepath)
            dxf_paths = convertDWG_DXF(self.temp_dir, self.temp_dir, self.oda_dir)
            self.dwg_conv_dxf_filepath = dxf_paths[0]
            self._run_analysis(self.dwg_conv_dxf_filepath, self.dwg_original_filepath)
        elif self.original_filepath:
            self._run_analysis(self.original_filepath, None)


    def _run_analysis(self, filepath, dwgcheck):
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)
        self.summary_container.setVisible(False)

        # result = autocad_points(filepath)
        result = dealing_with_everything(filepath)

        if result is None:
            QMessageBox.warning(None, "Invalid File", "The selected file is missing lines, blocks, or a channel outline. Please check the file and try again.")
            self.original_filepath = None
            return
        
        update_file_loaded_label(self, False)

        self.on_line_points        = result.on_line_points
        self.all_lines_table       = result.all_lines_table
        self.wall_slope_intercept  = result.wall_slope_intercept
        self.filtered_walls        = result.filtered_walls
        self.mistake_points        = result.mistake_points
        self.corrected_blocks      = result.corrected_blocks
        self.line_mistakes         = result.line_mistakes
        self.line_duplicate_points = result.line_duplicates
        self.post_accepted_blocks  = result.post_accepted_blocks
        self.post_accepted_lines   = result.post_accepted_lines
        self.post_rejected_blocks  = result.post_rejected_blocks
        self.post_rejected_lines   = result.post_rejected_lines
        self.line_name             = result.line_name
        self.all_fail              = result.all_fail
        self.bed_check             = result.bedit_check
        self.fixed_lines           = result.fixed_lines
        self.bedit_mistake_points  = result.bedit_mistake_points
        self.bedit_corrected_blocks = result.bedit_corrected_blocks
        self.blockname_unmatched   = result.blockname_unmatched
        self.linename_unmatched    = result.linename_unmatched

        
        if len(self.on_line_points) > 0 or len(self.wall_slope_intercept) > 0 or len(self.all_fail) > 0 or len(self.filtered_walls) > 0: 
            self.create_results_tab()

        if len(self.mistake_points) > 0 or len(self.line_mistakes) > 0:
            self.results_fixation()
        if len(self.post_rejected_blocks) > 0 or len(self.post_rejected_lines) or len(self.all_fail) > 0:
            self.database_results()
        self.results_summary()

        file_name = os.path.splitext(filepath)[0]
        self._add_recent_file(file_name)

    

    def extract_oda_directory(self):
        exe_dir = DatabaseDirectoryDialog.detect_install_location()
        if exe_dir == 'Development (VS Code)':
            self.oda_dir = r'C:\Program Files\ODA\ODAFileConverter 26.12.0\ODAFileConverter.exe'
        else:
            self.oda_dir = os.path.join(exe_dir, 'DO_NOT_TOUCH', 'ODAFileConverter 26.12.0', 'ODAFileConverter.exe')
    
                                                        
    def fix_errors(self):
        if not self.original_filepath: #If there is no file imported 
            QMessageBox.warning(None, "Error", "Please import a file first!")
            return

        if self.imported_dwg: #if a dwg was imported 
            
            if self.output_file_type == 'DWG':
                #call function to output dwg
                dwg_output(self.dwg_original_filepath, self.dwg_conv_dxf_filepath, self.temp_dir, self.oda_dir, 'DWG')

            if self.output_file_type == 'DXF':  #same process just keeping the file as a dxf 
                dwg_output(self.dwg_original_filepath, self.dwg_conv_dxf_filepath, self.temp_dir, self.oda_dir, 'DXF')

        if not self.imported_dwg: 
            if self.output_file_type == 'DXF':
                #This part doesn't use a temporary directory, so its easier to just hard code it then making 
                # a case for it in the function

                output_filepath, _ = QFileDialog.getSaveFileName(
                    None, "View DXF File Issues",
                    self.original_filepath.replace('.dxf', '_potential_issues.dxf'),
                    "DXF Files (*.dxf)")

                if not output_filepath:
                    return

                update_dxf_in_place(self.original_filepath, output_filepath)
                QMessageBox.information(None, "Success", f"Potential mistakes saved to:\n{output_filepath}")

            if self.output_file_type == 'DWG': 
                #call function to output dwg 
                dwg_output(self.original_filepath, self.original_filepath, None, self.oda_dir, 'DWG')

    def reset_app(self):
        self.original_filepath = None
        self.delete_temp_folder()
        
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)

        update_file_loaded_label(self, True)

        self.summary_container.setVisible(False)

    def delete_temp_folder(self):
        if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
        

