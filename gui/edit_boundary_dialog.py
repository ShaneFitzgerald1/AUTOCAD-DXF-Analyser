from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QTabWidget, QWidget, QScrollArea, QLineEdit, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from gui.BaseDialog import BaseDialog
from database.db_models import Session, ObjectID
from database.db_objects import get_catalogue, get_category_catalogue
from gui.table_widget import LabeledTableWidget
from gui.base_table import BaseTable
from gui.add_object_dialog import Combox
from gui.edit_tolerance_dialog import edit_tolerences
from gui.edit_database_dialog import EditDialog
from database.tolerance_config import (
    save_tolerance_set, get_active_set_name, get_all_tolerance_sets, get_all_tolerance_sets_full,
    delete_tolerance_set, _read_tolerances, _write_tolerances, set_active_tolerance_set,
    save_boundary_set, get_active_boundary_set_name, get_all_boundary_sets, get_all_boundary_sets_full,
    delete_boundary_set, set_active_boundary_set, DEFAULT_BOUNDARIES
)


class edit_boundary(BaseDialog):
    submitted = pyqtSignal(object)

    warning = "\u26A0"

    def __init__(self, parent=None):
        super().__init__(
            titleText='Tolerance Settings',
            submitText='Submit',
            parent=parent,
        )
        self.setFixedSize(420, 500)

    def buildContent(self, layout: QVBoxLayout):
        tabs = QTabWidget()

        # ── Tab 1: Set Tolerances ─────────────────────────────────────────
        set_widget = QWidget()
        set_layout = QVBoxLayout(set_widget)
        set_layout.setSpacing(10)
        set_layout.setContentsMargins(15, 15, 15, 15)

        edit_tolerences.create_label(self, 'Set Boundary', 5, True, 11, set_layout, True)

        edit_tolerences.create_label(self, f'Autocad files may contain unwanted objects away from the drawing itself.\n\n'
                               'To exclude these from the analysis set the boundary in which only the drawing lies.', 5, False,
                               10, set_layout, False)    
        

        ##placholder 
        bound_set1 = QPushButton('Boundary Sets')
        bound_set1.clicked.connect(lambda: Boundary_sets(parent=self).exec_())
        set_layout.addWidget(bound_set1)
        set_layout.addSpacing(5)

        ######
        
        current_name = get_active_boundary_set_name()
        self.current_bound_label = QLabel(f'Current Tolerance Set: {current_name}')
        self.current_bound_label.setFont(QFont('Inter', 10, QFont.Bold))
        self.current_bound_label.setWordWrap(True)
        self.current_bound_label.setAlignment(Qt.AlignCenter)
        set_layout.addWidget(self.current_bound_label)
        set_layout.addSpacing(5)

        bound_set_names = get_all_boundary_sets()
        self.type_combo = Combox._add_combo(set_layout, 'Change Tolerance to:', bound_set_names)
        set_layout.addSpacing(10)

        set_layout.addStretch()
        submit_btn = QPushButton('Set Boundary')
        submit_btn.clicked.connect(self.set_boundaries)
        set_layout.addWidget(submit_btn)

        self.feedback_label_set = QLabel('')
        self.feedback_label_set.setAlignment(Qt.AlignCenter)
        set_layout.addWidget(self.feedback_label_set)

        tabs.addTab(set_widget, 'Set Boundary')

        # ── Tab 2: Create Boundary Set ───────────────────────────────────────
        create_widget = QWidget()
        create_layout = QVBoxLayout(create_widget)
        create_layout.setSpacing(10)
        create_layout.setContentsMargins(15, 15, 15, 15)

        edit_tolerences.create_label(self, 'Create Custom Boundary Values', 5, True, 11, create_layout, True)

        edit_tolerences.create_label(self, f'{self.warning} Once created, select the new set in the Set Boundary tab before running analysis. All Boundary dimensions are in mm',
                          5, False, 10, create_layout, False)
        
        bound_set2 = QPushButton('Boundary Sets')
        bound_set2.clicked.connect(lambda: Boundary_sets(parent=self).exec_())
        create_layout.addWidget(bound_set2)
        create_layout.addSpacing(5)

        self.new_boundary_name = QLineEdit()
        self.new_boundary_name.setPlaceholderText('e.g. MODULE X Boundary')
        create_layout.addLayout(edit_tolerences._input_row(self, 'Boundary Set Name:', self.new_boundary_name))

        self.xmin_boundary = QLineEdit()
        create_layout.addLayout(edit_tolerences._input_row(self, 'X Minimum Boundary:', self.xmin_boundary))

        self.xmax_boundary = QLineEdit()
        create_layout.addLayout(edit_tolerences._input_row(self, 'X Maximum Boundary:', self.xmax_boundary))

        self.ymin_boundary = QLineEdit()
        create_layout.addLayout(edit_tolerences._input_row(self, 'Y Minimum Boundary:', self.ymin_boundary))

        self.ymax_boundary = QLineEdit()
        create_layout.addLayout(edit_tolerences._input_row(self, 'Y Maximum Boundary:', self.ymax_boundary))

        create_layout.addSpacing(5)
        create_layout.addStretch()
        create_btn = QPushButton('Create Boundaries')
        create_btn.clicked.connect(self.add_boundaries)
        create_layout.addWidget(create_btn)

        self.feedback_label_add = QLabel('')
        self.feedback_label_add.setAlignment(Qt.AlignCenter)
        create_layout.addWidget(self.feedback_label_add)

        tabs.addTab(create_widget, 'Create Boundary')


        # ── Tab 3: edit/delete boundary set ───────────────────────────────────────

        delete_widget = QWidget()
        delete_layout = QVBoxLayout(delete_widget)
        delete_layout.setSpacing(10)
        delete_layout.setContentsMargins(15, 15, 15, 15)

        edit_tolerences.create_label(self, 'Edit Boundary Set', 5, True, 11, delete_layout, True)

        edit_tolerences.create_label(self, 'This Tab is for editing or deleting created Boundary sets, the default Boundary conditions may not be adjusted.\n\n' \
        ' All Boundary limits are in mm.',
                          7, False, 10, delete_layout, False)
        
        bound_set3 = QPushButton('Boundary Sets')
        bound_set3.clicked.connect(lambda: Boundary_sets(parent=self).exec_())
        delete_layout.addWidget(bound_set3)
        delete_layout.addSpacing(5)
        
        edit_names = []
        for bound_set_name in bound_set_names:
            if bound_set_name == 'Default': 
                continue 
            edit_names.append(bound_set_name) 
        self.edit_combo = Combox._add_combo(delete_layout, 'Select tolerance set:', edit_names)

        self.edit_xmin_cb = QCheckBox('X Minimum Boundary')
        self.edit_xmin_boundary = QLineEdit()
        self.edit_xmin_boundary.setEnabled(False)
        self.edit_xmin_cb.toggled.connect(self.edit_xmin_boundary.setEnabled)

        self.edit_xmax_cb = QCheckBox('X Maximum Boundary')
        self.edit_xmax_boundary = QLineEdit()
        self.edit_xmax_boundary.setEnabled(False)
        self.edit_xmax_cb.toggled.connect(self.edit_xmax_boundary.setEnabled)

        self.edit_ymin_cb = QCheckBox('Y Minimum Boundary')
        self.edit_ymin_boundary = QLineEdit()
        self.edit_ymin_boundary.setEnabled(False)
        self.edit_ymin_cb.toggled.connect(self.edit_ymin_boundary.setEnabled)

        self.edit_ymax_cb = QCheckBox('X Maximum Boundary')
        self.edit_ymax_boundary = QLineEdit()
        self.edit_ymax_boundary.setEnabled(False)
        self.edit_ymax_cb.toggled.connect(self.edit_ymax_boundary.setEnabled)


        delete_layout.addLayout(edit_tolerences._checkbox_input_row(self, self.edit_xmin_cb, self.edit_xmin_boundary))
        delete_layout.addLayout(edit_tolerences._checkbox_input_row(self, self.edit_xmax_cb, self.edit_xmax_boundary))
        delete_layout.addLayout(edit_tolerences._checkbox_input_row(self, self.edit_ymin_cb, self.edit_ymin_boundary))
        delete_layout.addLayout(edit_tolerences._checkbox_input_row(self, self.edit_ymax_cb, self.edit_ymax_boundary))


        make_changes_button = QPushButton('Make Changes')
        make_changes_button.clicked.connect(self.make_changes) 
        delete_layout.addWidget(make_changes_button)
        delete_layout.addSpacing(5)

        delete_button = QPushButton('Delete Boundary Set')
        delete_button.clicked.connect(lambda: self.delete_boundary()) 
        delete_layout.addWidget(delete_button)
        delete_layout.addSpacing(5)

        self.feedback_label_edit = QLabel('')
        self.feedback_label_edit.setAlignment(Qt.AlignCenter)
        delete_layout.addWidget(self.feedback_label_edit)

        tabs.addTab(delete_widget, 'Edit Boundary Set')
        layout.addWidget(tabs)




    def set_boundaries(self): 
        current_set = get_active_boundary_set_name()
        name = self.type_combo.currentText()

        if current_set == name: 
            self.feedback_label_set.setStyleSheet('color: red;')
            self.feedback_label_set.setText(f'{name} is the the already the active tolerance set.')

        else: 
            set_active_boundary_set(name)
            self.remake_type_combox()
            self.feedback_label_set.setStyleSheet('color: green;')
            self.feedback_label_set.setText(f'Sucesfully set {name} as the active tolerance set.')
            self.current_bound_label.setText(f'Current Tolerance Set: {name}')    

    def add_boundaries(self): 
        """Function for adding tolerence sets 
        take the current values in the bxces, ensures they all have values (if not error will appear)
        Values input by the user are saved as a tolerence set 
        Comboxes (Set and Delete tolerance) in the dialog are updated to reflect the new tolerence set"""
        name_input = self.new_boundary_name.text().strip()
        name = name_input.upper()
        xmin_input = self.xmin_boundary.text().strip()
        xmax_input = self.xmax_boundary.text().strip()
        ymin_input = self.ymin_boundary.text().strip() 
        ymax_input = self.ymax_boundary.text().strip()


        if not name_input or not xmin_input or not xmax_input or not ymin_input or not ymax_input:
            self.feedback_label_add.setStyleSheet('color: red;')
            self.feedback_label_add.setText('Please fill in all boxes.')
            return
        
        try: 
            xmin_input = float(xmin_input)
            xmax_input = float(xmax_input)
            ymin_input = float(ymin_input)
            ymax_input = float(ymax_input)
        except ValueError: 
            self.feedback_label_add.setStyleSheet('color: red;')
            self.feedback_label_add.setText('Boundary values must be numbers.')
            return

        save_boundary_set(name, xmin_input, xmax_input, ymin_input, ymax_input)   
        self.feedback_label_add.setStyleSheet('color: green;')
        self.feedback_label_add.setText(f'Saved {name} as a Tolerance set.')
        self.remake_type_combox()
        self.remake_edit_bound_combox()       


    def make_changes(self):
        name = self.edit_combo.currentText()
        if not EditDialog._confirm('Confirm Change', f'Are you sure you want to delete the {name} Boundary Set?', self):
            return

        data = _read_tolerances()

        if not self.edit_xmin_cb.isChecked() and not self.edit_xmax_cb.isChecked() and not self.edit_ymin_cb.isChecked() and not self.edit_ymax_cb.isChecked():
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText('Select a boundary to edit')
            return

        try: 
            if self.edit_xmin_cb.isChecked():
                data['boundary_sets'][name]['x_min'] = float(self.edit_xmin_boundary.text())
            if self.edit_xmax_cb.isChecked():
                data['boundary_sets'][name]['x_max'] = float(self.edit_xmax_boundary.text())
            if self.edit_ymin_cb.isChecked():
                data['boundary_sets'][name]['y_min'] = float(self.edit_ymin_boundary.text())
            if self.edit_ymax_cb.isChecked():
                data['boundary_sets'][name]['y_max'] = float(self.edit_ymax_boundary.text())
        except ValueError: 
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText('Boundary values must be numbers.')
            return

        _write_tolerances(data)
        self.feedback_label_edit.setStyleSheet('color: green;')
        self.feedback_label_edit.setText(f'Updated {name} boundary set')

    def delete_boundary(self): 
        name = self.edit_combo.currentText()
        if name is str: 
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText(f'Please select a numerical value')
            return 
        if not EditDialog._confirm('Confirm Delete', f'Are you sure you want to delete the {name} Boundary Set?', self):
            return
        result = delete_boundary_set(name) 

        if result:
            self.feedback_label_edit.setStyleSheet('color: green;')
            self.feedback_label_edit.setText(f'Deleted {name} tolerance set')
            self.remake_type_combox() 
            self.remake_edit_bound_combox()

        else: 
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText(f'Failed to delete {name} tolerance set')    


    def remake_type_combox(self):
        bound_set_names = get_all_boundary_sets()
        self.type_combo.clear()
        self.type_combo.addItems(bound_set_names)        

    def remake_edit_bound_combox(self):
        """Function for recreating the edit tolerance combox if a tolerance set has been added to the json file
        or removed from the json file"""

        edit_names = []
        bound_set_names = get_all_boundary_sets()
        for bound_set_name in bound_set_names:
            if bound_set_name == 'Default':
                continue
            edit_names.append(bound_set_name)

        self.edit_combo.clear()
        self.edit_combo.addItems(edit_names)

    def collectResult(self):
        return None



class Boundary_sets(BaseDialog): 
    def __init__(self, parent=None):
        super().__init__(
            titleText='Boundary Sets',
            submitText='Close',
            parent=parent,
        )
        self.setFixedSize(650, 450)

    def buildContent(self, layout: QVBoxLayout)-> None:
        tabs = QTabWidget()

        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        sets = get_all_boundary_sets_full()

        for set in sets:
            name, xmin, xmax, ymin, ymax = set
            set_table = LabeledTableWidget(f'{name} Boundary Conditions', ['X min (mm)', 'X max (mm)', 'Y min (mm)', 'Y max (mm)'], BaseTable.BLUE)
            set_table.populate([[xmin, xmax, ymin, ymax]])
            inner_layout.addLayout(set_table)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        tab2_layout.addWidget(scroll)
        tabs.addTab(tab2, 'Boundary Sets')
        layout.addWidget(tabs)

    def collectResult(self):
        return None
    