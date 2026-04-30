from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QTabWidget, QWidget, QScrollArea, QLineEdit, QCheckBox, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from gui.BaseDialog import BaseDialog
from database.db_models import Session, ObjectID
from database.db_objects import get_catalogue, get_category_catalogue
from gui.table_widget import LabeledTableWidget
from gui.base_table import BaseTable
from gui.add_object_dialog import Combox
from gui.edit_database_dialog import EditDialog
from database.tolerance_config import (
    save_tolerance_set, get_active_set_name, get_all_tolerance_sets, get_all_tolerance_sets_full,
    delete_tolerance_set, _read_tolerances, _write_tolerances, set_active_tolerance_set,
    save_boundary_set, get_active_boundary_set_name, get_all_boundary_sets, get_all_boundary_sets_full,
    delete_boundary_set, set_active_boundary_set, DEFAULT_BOUNDARIES
)


class edit_tolerences(BaseDialog):
    submitted = pyqtSignal(object)

    warning = "\u26A0"

    def __init__(self, parent=None):
        super().__init__(
            titleText='Tolerance Settings',
            submitText='Submit',
            parent=parent,
        )
        self.setFixedSize(420, 450)

    def buildContent(self, layout: QVBoxLayout):
        tabs = QTabWidget()

        # ── Tab 1: Set Tolerances ─────────────────────────────────────────
        set_widget = QWidget()
        set_layout = QVBoxLayout(set_widget)
        set_layout.setSpacing(10)
        set_layout.setContentsMargins(15, 15, 15, 15)

        self.create_label('Set Tolerance', 5, True, 11, set_layout, True)

        self.create_label(f'{self.warning} If you have created a new tolerance set, select it here before running analysis.\n\n'
                               'See Tolerance Settings to view saved tolerance sets and tolerance descriptions. All tolerances are in mm', 5, False,
                               10, set_layout, False)

        btn_settings = QPushButton('Tolerance Settings')
        btn_settings.clicked.connect(lambda: tolerence_settings(parent=self).exec_())
        set_layout.addWidget(btn_settings)
        set_layout.addSpacing(5)

        as_name = get_active_set_name()
        self.current_tol_label = QLabel(f'Current Tolerance Set: {as_name}')
        self.current_tol_label.setFont(QFont('Inter', 10, QFont.Bold))
        self.current_tol_label.setWordWrap(True)
        self.current_tol_label.setAlignment(Qt.AlignCenter)
        set_layout.addWidget(self.current_tol_label)
        set_layout.addSpacing(5)

        tol_set_names = get_all_tolerance_sets()
        self.type_combo = Combox._add_combo(set_layout, 'Change Tolerance to:', tol_set_names)
        set_layout.addSpacing(10)

        set_layout.addStretch()
        submit_btn = QPushButton('Set Tolerances')
        submit_btn.clicked.connect(self.set_tolerances)
        set_layout.addWidget(submit_btn)

        self.feedback_label_set = QLabel('')
        self.feedback_label_set.setAlignment(Qt.AlignCenter)
        set_layout.addWidget(self.feedback_label_set)

        tabs.addTab(set_widget, 'Set Tolerance')

        # ── Tab 2: Create Tolerance ───────────────────────────────────────
        create_widget = QWidget()
        create_layout = QVBoxLayout(create_widget)
        create_layout.setSpacing(10)
        create_layout.setContentsMargins(15, 15, 15, 15)

        self.create_label('Create Custom Tolerance Values', 5, True, 11, create_layout, True)

        self.create_label(f'{self.warning} Once created, select the new set in the Set Tolerance tab before running analysis. All tolerances are in mm',
                          5, False, 10, create_layout, False)

        btn_settings1 = QPushButton('Tolerance Settings')
        btn_settings1.clicked.connect(lambda: tolerence_settings(parent=self).exec_())
        create_layout.addWidget(btn_settings1)
        create_layout.addSpacing(5)

        self.new_tolerance_name = QLineEdit()
        self.new_tolerance_name.setPlaceholderText('e.g. MODULE X Tolerances')
        create_layout.addLayout(self._input_row('Tolerance Set Name:', self.new_tolerance_name))

        self.block_tolerance = QLineEdit()
        create_layout.addLayout(self._input_row('Block Tolerance:', self.block_tolerance))

        self.line_tolerance1 = QLineEdit()
        create_layout.addLayout(self._input_row('Line Tolerance 1:', self.line_tolerance1))

        self.line_tolerance2 = QLineEdit()
        create_layout.addLayout(self._input_row('Line Tolerance 2:', self.line_tolerance2))

        create_layout.addSpacing(10)
        create_layout.addStretch()
        create_btn = QPushButton('Create Tolerances')
        create_btn.clicked.connect(self.add_tolerances)
        create_layout.addWidget(create_btn)

        self.feedback_label_add = QLabel('')
        self.feedback_label_add.setAlignment(Qt.AlignCenter)
        create_layout.addWidget(self.feedback_label_add)

        tabs.addTab(create_widget, 'Create Tolerance')

        # ── Tab 3: Delete Tolerance Sets ───────────────────────────────────────
        delete_widget = QWidget()
        delete_layout = QVBoxLayout(delete_widget)
        delete_layout.setSpacing(10)
        delete_layout.setContentsMargins(15, 15, 15, 15)

        self.create_label('Edit Tolerance Set', 5, True, 11, delete_layout, True)

        self.create_label('This Tab is for editing or deleting created tolerance sets, the default tolerance sets may not be adjusted. All tolerances are in mm.',
                          7, False, 10, delete_layout, False)
        
        btn_settings2 = QPushButton('Tolerance Settings')
        btn_settings2.clicked.connect(lambda: tolerence_settings(parent=self).exec_())
        delete_layout.addWidget(btn_settings2)
        delete_layout.addSpacing(5)
        
        edit_names = []
        for tol_set_name in tol_set_names:
            if tol_set_name == 'Default': 
                continue 
            edit_names.append(tol_set_name) 
        self.edit_combo = Combox._add_combo(delete_layout, 'Select tolerance set:', edit_names)

        self.edit_block_cb = QCheckBox('Block Tolerance')
        self.edit_block_tolerance = QLineEdit()
        self.edit_block_tolerance.setEnabled(False)
        self.edit_block_cb.toggled.connect(self.edit_block_tolerance.setEnabled)

        self.edit_line1_cb = QCheckBox('Line Tolerance 1')
        self.edit_line_tolerance1 = QLineEdit()
        self.edit_line_tolerance1.setEnabled(False)
        self.edit_line1_cb.toggled.connect(self.edit_line_tolerance1.setEnabled)

        self.edit_line2_cb = QCheckBox('Line Tolerance 2')
        self.edit_line_tolerance2 = QLineEdit()
        self.edit_line_tolerance2.setEnabled(False)
        self.edit_line2_cb.toggled.connect(self.edit_line_tolerance2.setEnabled)

        delete_layout.addLayout(self._checkbox_input_row(self.edit_block_cb, self.edit_block_tolerance))
        delete_layout.addLayout(self._checkbox_input_row(self.edit_line1_cb, self.edit_line_tolerance1))
        delete_layout.addLayout(self._checkbox_input_row(self.edit_line2_cb, self.edit_line_tolerance2))


        make_changes_button = QPushButton('Make Changes')
        make_changes_button.clicked.connect(self.make_changes) 
        delete_layout.addWidget(make_changes_button)
        delete_layout.addSpacing(5)

        delete_button = QPushButton('Delete Tolerance Set')
        delete_button.clicked.connect(lambda: self.delete_tolerance()) #dummy clicked for now 
        delete_layout.addWidget(delete_button)
        delete_layout.addSpacing(5)

        self.feedback_label_edit = QLabel('')
        self.feedback_label_edit.setAlignment(Qt.AlignCenter)
        delete_layout.addWidget(self.feedback_label_edit)

        tabs.addTab(delete_widget, 'Edit Tolerance Set')
        layout.addWidget(tabs)


    def create_label(self, text, spacing, bold, fontsize, layout, centre):
        """Function for creating a Label"""
        label = QLabel(text)
        label.setWordWrap(True)
        policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        label.setSizePolicy(policy)
        if bold:
            label.setFont(QFont('Inter', fontsize, QFont.Bold))
        else:
            label.setFont(QFont('Inter', fontsize))
        if centre:
            label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addSpacing(spacing)


    def _input_row(self, label_text, widget):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFont(QFont('Inter', 10))
        lbl.setFixedWidth(160)
        row.addWidget(lbl)
        row.addWidget(widget)
        return row
    
    def _checkbox_input_row(self, checkbox, line_edit):
        row = QHBoxLayout()
        checkbox.setFont(QFont('Inter', 10))
        checkbox.setFixedWidth(160)
        row.addWidget(checkbox)
        row.addWidget(line_edit)
        return row


    def collectResult(self):
        return None
    
    def set_tolerances(self): 
        current_set = get_active_set_name()
        name = self.type_combo.currentText()

        if current_set == name: 
            self.feedback_label_set.setStyleSheet('color: red;')
            self.feedback_label_set.setText(f'{name} is the the already the active tolerance set.')

        else: 
            set_active_tolerance_set(name)
            self.remake_type_combox()
            self.feedback_label_set.setStyleSheet('color: green;')
            self.feedback_label_set.setText(f'Sucesfully set {name} as the active tolerance set.')
            self.current_tol_label.setText(f'Current Tolerance Set: {name}')


    def add_tolerances(self): 
        """Function for adding tolerence sets 
        take the current values in the bxces, ensures they all have values (if not error will appear)
        Values input by the user are saved as a tolerence set 
        Comboxes (Set and Delete tolerance) in the dialog are updated to reflect the new tolerence set"""
        name_input = self.new_tolerance_name.text().strip()
        name = name_input.upper()
        block_tolerance_input = self.block_tolerance.text().strip()
        line_tolerance1_input = self.line_tolerance1.text().strip()
        line_tolerance2_input = self.line_tolerance2.text().strip() 

        if not name_input or not block_tolerance_input or not line_tolerance1_input or not line_tolerance2_input:
            self.feedback_label_add.setStyleSheet('color: red;')
            self.feedback_label_add.setText('Please fill in all boxes.')
            return

        try:
            block_tolerance_input = float(block_tolerance_input)
            line_tolerance1_input = float(line_tolerance1_input)
            line_tolerance2_input = float(line_tolerance2_input)
        except ValueError:
            self.feedback_label_add.setStyleSheet('color: red;')
            self.feedback_label_add.setText('Tolerance values must be numbers.')
            return

        save_tolerance_set(name, block_tolerance_input, line_tolerance1_input, line_tolerance2_input)
        self.feedback_label_add.setStyleSheet('color: green;')
        self.feedback_label_add.setText(f'Saved {name} as a Tolerance set.')
        self.remake_type_combox()
        self.remake_edit_tol_combox()


    def make_changes(self):
        name = self.edit_combo.currentText()

        if not EditDialog._confirm('Confirm Change', f'Are you sure you want to change the {name} tolerance set?', self):
            return

        data = _read_tolerances()

        if not self.edit_block_cb.isChecked() and not self.edit_line1_cb.isChecked() and not self.edit_line2_cb.isChecked():
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText('Select a tolerance to edit')
            return

        try:
            if self.edit_block_cb.isChecked():
                data['sets'][name]['block_tolerance'] = float(self.edit_block_tolerance.text())
            if self.edit_line1_cb.isChecked():
                data['sets'][name]['line_tolerance_1'] = float(self.edit_line_tolerance1.text())
            if self.edit_line2_cb.isChecked():
                data['sets'][name]['line_tolerance_2'] = float(self.edit_line_tolerance2.text())
        except ValueError:
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText('Tolerance values must be numbers.')
            return

        _write_tolerances(data)
        self.feedback_label_edit.setStyleSheet('color: green;')
        self.feedback_label_edit.setText(f'Updated {name} Tolerance set')


    def delete_tolerance(self): 
        name = self.edit_combo.currentText()

        if not EditDialog._confirm('Confirm Delete', f'Are you sure you want to delete the {name} tolerance set?', self):
            return
        
        result = delete_tolerance_set(name) 

        if result:
            self.feedback_label_edit.setStyleSheet('color: green;')
            self.feedback_label_edit.setText(f'Deleted {name} tolerance set')
            self.remake_type_combox() 
            self.remake_edit_tol_combox()

        else: 
            self.feedback_label_edit.setStyleSheet('color: red;')
            self.feedback_label_edit.setText(f'Failed to delete {name} tolerance set')

    def remake_type_combox(self):
        tol_set_names = get_all_tolerance_sets()
        self.type_combo.clear()
        self.type_combo.addItems(tol_set_names)

    def remake_edit_tol_combox(self): 
        """Function for recreating the edit tolerance combox if a tolerance set has been added to the json file 
        or removed from the json file"""

        edit_names = []
        tol_set_names = get_all_tolerance_sets()
        for tol_set_name in tol_set_names: 
            if tol_set_name == 'Default': 
                continue 
            edit_names.append(tol_set_name)

        self.edit_combo.clear()
        self.edit_combo.addItems(edit_names)    



    



class tolerence_settings(BaseDialog):

    def __init__(self, parent=None):
        super().__init__(
            titleText='Tolerence Settings',
            submitText='Close',
            parent=parent,
        )
        self.setFixedSize(650, 450)

    def buildContent(self, layout: QVBoxLayout)-> None:
        tabs = QTabWidget()
        # ── Tab 1: Description ────────────────────────────────────────── 

        desc_widget = QWidget()
        desc_layout = QVBoxLayout(desc_widget)
        desc_layout.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)
        inner_layout.setSpacing(10)

        check = "\u2705"      # ✅
        cross = "\u274C"      # ❌
        warning = "\u26A0"    # ⚠

        def html_label(html: str) -> QLabel:
            lbl = QLabel(html)
            lbl.setFont(QFont('Inter', 10))
            lbl.setWordWrap(True)
            lbl.setTextFormat(Qt.RichText)
            return lbl

        def heading(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setFont(QFont('Inter', 12, QFont.Bold))
            lbl.setAlignment(Qt.AlignCenter)
            return lbl
        

        inner_layout.addWidget(heading('Block Reference Position Errors'))

        inner_layout.addWidget(html_label(
           'In the geometry engine block positions are checked to ensure they are within a certain tolerance of a line. ' \
           'There are two tolerance types when considering blocks.'))
        
        inner_layout.addWidget(html_label(
           '<b>Block Tolerance </b>: This is the tolerance a block must be within a line, to not be considered a mistake. '))
        
        inner_layout.addWidget(heading('Line Position Errors'))

        inner_layout.addWidget(html_label(
           'In the geometry engine lines start/end points are checked against other lines to ensure the start/end points are on the correct position. ' \
           'There are three tolerance types when considering lines.'))
        
        inner_layout.addWidget(html_label(
           '<b>Line Tolerance 1 </b>: Tolerance a line start/end must be below another line for it not be considered a mistake'))
        
        inner_layout.addWidget(html_label(
           '<b>Line Tolerance 2 </b>: If a line start/end falls in the range between tolerance 1 and tolerance 2 of a line this is considered a mistake. ' \
           'If the line start/end is at a distance greater than tolerance 2 from a line, this is not considered a mistake as the distance is likely to large to be a mistake.'))
        
        inner_layout.addStretch()
        scroll.setWidget(inner)
        desc_layout.addWidget(scroll)
        tabs.addTab(desc_widget, 'Description')


        # ── Tab 2: Object Database ──────────────────────────────────────
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        inner_layout = QVBoxLayout(inner)

        sets = get_all_tolerance_sets_full()

        for set in sets:
            name, tolerance1, tolerance2, tolerance3 = set
            set_table = LabeledTableWidget(f'{name} Tolerances', ['Block Tolerance (mm)', 'Line Tolerance 1 (mm)', 'Line Tolerance 2 (mm)'], BaseTable.BLUE)
            set_table.populate([[tolerance1, tolerance2, tolerance3]])
            inner_layout.addLayout(set_table)

        inner_layout.addStretch()
        scroll.setWidget(inner)
        tab2_layout.addWidget(scroll)
        tabs.addTab(tab2, 'Tolerances')
        layout.addWidget(tabs)






        



        
        


