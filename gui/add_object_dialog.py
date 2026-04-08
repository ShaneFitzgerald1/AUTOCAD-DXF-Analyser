from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QTabWidget, QWidget, QScrollArea, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from gui.BaseDialog import BaseDialog
from database.db_models import Session, ObjectID
from database.db_objects import get_catalogue, get_category_catalogue
from gui.table_widget import LabeledTableWidget
from gui.base_table import BaseTable


class AddObjectDialog(BaseDialog):
    submitted = pyqtSignal(object)

    CHANNEL_OPTIONS = ['Yes', 'No']

    def __init__(self, rejected_names: list[str], parent=None):
        """
        rejected_names: list of object names that failed the object database check.
        The first name is pre-selected in the list.
        """
        self._rejected_names = rejected_names

        catalogue = get_catalogue()
        self.TYPE_OPTIONS     = list(dict.fromkeys(row[1] for row in catalogue if row[1]))
        self.CATEGORY_OPTIONS = list(dict.fromkeys(row[2] for row in catalogue if row[2]))
        self.NAME_OPTIONS = list(dict.fromkeys(row[0] for row in catalogue if row[0]))

        category_catalogue = get_category_catalogue()
        self.CATEGORY_DB_OPTIONS = list(dict.fromkeys(row[0] for row in category_catalogue if row[0]))

        combined_categories = (
            [row[2] for row in catalogue if row[2]] +
            [row[0] for row in category_catalogue if row[0]]
        )
        self.ALL_CATEGORIES = list(dict.fromkeys(combined_categories))

        super().__init__(
            titleText='Add Object to Database',
            submitText='Submit',
            parent=parent,
        )
        self.submitButton.clicked.disconnect()
        self.submitButton.clicked.connect(self.accept)

    # ----------------------------------------------------------
    # BaseDialog interface
    # -----------------------------------------------------------
    warning = "\u26A0"    # ⚠

    def buildContent(self, layout: QVBoxLayout) -> None:
        tabs = QTabWidget()

        # ──----------------- TAB 1 OBJECT ───────────────────────────────────────────
        objectdb_widget = QWidget()
        objectdb_layout = QVBoxLayout(objectdb_widget)
        objectdb_layout.setSpacing(10)

        if len(self._rejected_names) == 1:
            explain_label = QLabel(f'{self._rejected_names[0]} is not present in the object database.')
        else:
            explain_label = QLabel(f'{", ".join(self._rejected_names)} are not present in the object database.')
        explain_label.setFont(QFont('Inter', 10, QFont.Bold))
        explain_label.setWordWrap(True)
        objectdb_layout.addWidget(explain_label)

        explain_label2 = QLabel(
            f'If object should be present in the database please add below.\n\n'
            f'{self.warning} If Object type is a Line type and the category is not present in the Category combo, add it in the Line Category tab first.\n\n'
            'Please read Database description to view instrutions and both Databases.'
        )
        explain_label2.setFont(QFont('Inter', 10))
        explain_label2.setWordWrap(True)
        objectdb_layout.addWidget(explain_label2)

        btn1 = QPushButton('Database Description')
        btn1.clicked.connect(lambda: database_description(parent=self).exec_())
        objectdb_layout.addWidget(btn1)

        list_label = QLabel('Select the object to add:')
        list_label.setFont(QFont('Inter', 10, QFont.Bold))
        objectdb_layout.addWidget(list_label)

        self.name_list = QListWidget()
        self.name_list.addItems(self._rejected_names)
        self.name_list.setCurrentRow(0)
        self.name_list.setMaximumHeight(120)
        objectdb_layout.addWidget(self.name_list)

        self.type_combo     = Combox._add_combo(objectdb_layout, 'Type:', self.TYPE_OPTIONS)
        self.category_combo = Combox._add_combo(objectdb_layout, 'Category:', self.ALL_CATEGORIES)
        self.channel_combo  = Combox._add_combo(objectdb_layout, 'On Channel Outline:', self.CHANNEL_OPTIONS)

        add_obj_btn = QPushButton('Add to Database')
        add_obj_btn.clicked.connect(self._add_object)
        objectdb_layout.addWidget(add_obj_btn)

        self.feedback_label = QLabel('')
        self.feedback_label.setAlignment(Qt.AlignCenter)
        objectdb_layout.addWidget(self.feedback_label)

        tabs.addTab(objectdb_widget, 'Add Object')

        # ──------------ TAB 2 ADD LINE CATEGORY ────────────────────────────────────
        category_widget = QWidget()
        category_layout = QVBoxLayout(category_widget)
        category_layout.setSpacing(10)

        explain_label3 = QLabel(
            f'{self.warning} This tab is for adding new Line Categories.\n\n'
            'If the Line Category is not present for a Line you wish to add, add it here first.\n\n'
            'Please read Database Description to view instrutions and both Databases.'
        )
        explain_label3.setFont(QFont('Inter', 10))
        explain_label3.setWordWrap(True)
        category_layout.addWidget(explain_label3)

        btn2 = QPushButton('Database Description')
        btn2.clicked.connect(lambda: database_description(parent=self).exec_())
        category_layout.addWidget(btn2)

        # Category name input
        name_row = QHBoxLayout()
        name_lbl = QLabel('New Category Name:')
        name_lbl.setFont(QFont('Inter', 10))
        name_lbl.setFixedWidth(200)
        self.new_category_name = QLineEdit()
        self.new_category_name.setPlaceholderText('e.g. NEW LINE TYPE')
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.new_category_name)
        category_layout.addLayout(name_row)

        # Quantity of allowed connections
        quantity_options = [str(i) for i in range(1, len(self.CATEGORY_OPTIONS) + 1)]
        self.quantity_combo = Combox._add_combo(category_layout, 'Allowed Connections:', quantity_options)
        self.quantity_combo.currentIndexChanged.connect(self._rebuild_connection_combos)

        # Container for the dynamic connection combos
        self.connections_container = QVBoxLayout()
        category_layout.addLayout(self.connections_container)

        # Double connection and on channel combos
        self.double_connection_combo = Combox._add_combo(category_layout, 'Double Connection:', self.CHANNEL_OPTIONS)
        self.on_channel_combo        = Combox._add_combo(category_layout, 'On Channel Outline:', self.CHANNEL_OPTIONS)

        self.cat_feedback_label = QLabel('')
        self.cat_feedback_label.setAlignment(Qt.AlignCenter)
        category_layout.addWidget(self.cat_feedback_label)

        add_cat_btn = QPushButton('Add Line Category')
        add_cat_btn.clicked.connect(self._add_line_category)
        category_layout.addWidget(add_cat_btn)

        tabs.addTab(category_widget, 'Add Line Category')

        layout.addWidget(tabs)

        # Build initial connection combos for default quantity (1)
        self._rebuild_connection_combos()

    def _rebuild_connection_combos(self):
        # Clear existing combos from the container
        while self.connections_container.count():
            item = self.connections_container.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

        self._connection_combos = []
        count = int(self.quantity_combo.currentText())
        for i in range(count):
            combo = Combox._add_combo(self.connections_container, f'Allowed Connection {i + 1}:', self.ALL_CATEGORIES)
            self._connection_combos.append(combo)

    def _add_line_category(self):
        from database.db_models import CategoryLineRule
        name_input = self.new_category_name.text().strip()
        name = name_input.upper()
        if not name:
            self.cat_feedback_label.setStyleSheet('color: red;')
            self.cat_feedback_label.setText('Please enter a category name.')
            return

        allowed = ','.join(c.currentText() for c in self._connection_combos)
        double  = self.double_connection_combo.currentText()
        on_chan = self.on_channel_combo.currentText()

        session = Session()
        try:
            exists = session.query(CategoryLineRule).filter_by(category=name).first()
            if exists:
                self.cat_feedback_label.setStyleSheet('color: orange;')
                self.cat_feedback_label.setText(f'"{name}" is already in the category database.')
                return

            session.add(CategoryLineRule(
                category=name,
                allowed_connections=allowed,
                double_connection=double,
                on_channel=on_chan,
            ))
            session.commit()

            # Make new category available in the object tab combo immediately
            self.CATEGORY_OPTIONS.append(name)
            self.ALL_CATEGORIES.append(name)
            self.category_combo.addItem(name)
            self._rebuild_connection_combos()

            self.cat_feedback_label.setStyleSheet('color: green;')
            self.cat_feedback_label.setText(f'"{name}" added successfully.')
            self.new_category_name.clear()
        except Exception as e:
            session.rollback()
            self.cat_feedback_label.setStyleSheet('color: red;')
            self.cat_feedback_label.setText(f'Error: {e}')
        finally:
            session.close()




    def _add_object(self):
        item = self.name_list.currentItem()
        if item is None:
            return

        name     = item.text()
        type_    = self.type_combo.currentText()
        category = self.category_combo.currentText()
        channel  = self.channel_combo.currentText()

        session = Session()
        try:
            exists = session.query(ObjectID).filter_by(name=name).first()
            if exists:
                self.feedback_label.setStyleSheet('color: orange;')
                self.feedback_label.setText(f'"{name}" is already in the database.')
                return

            session.add(ObjectID(name=name, type=type_, category=category, on_channel_outline=channel))
            session.commit()
            self.feedback_label.setStyleSheet('color: green;')
            self.feedback_label.setText(f'"{name}" added successfully.')
            self.name_list.takeItem(self.name_list.currentRow())
        except Exception as e:
            session.rollback()
            self.feedback_label.setStyleSheet('color: red;')
            self.feedback_label.setText(f'Error: {e}')
        finally:
            session.close()

class Combox():
    @staticmethod
    def _add_combo(layout: QVBoxLayout, label_text: str, options: list[str]) -> QComboBox:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setFont(QFont('Inter', 10))
        lbl.setFixedWidth(160)
        combo = QComboBox()
        combo.addItems(options)
        row.addWidget(lbl)
        row.addWidget(combo)
        layout.addLayout(row)
        return combo
    

class database_description(BaseDialog):

    def __init__(self, parent=None):
        super().__init__(
            titleText='Database Description',
            submitText='Close',
            parent=parent,
        )
        self.setFixedSize(700, 550)

    def buildContent(self, layout: QVBoxLayout) -> None:
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

        inner_layout.addWidget(html_label(
            'There are two database <u>types</u> objects are compared to within the App, '
            'the Object and Line Category Databases. Block reference object types are fed into the database to ensure they are recognised and positioned correctly. ' \
            'Line object types are checked to confirm they meet required junction and positioning rules. ' 
        
        ))

        inner_layout.addWidget(heading('The Object Database'))

        inner_layout.addWidget(html_label(
            'The object database has 4 columns including name, type, category, on channel outline.'
        ))
        inner_layout.addWidget(html_label(
            '<b>Name</b>: The objects name extracted from the <u>dxf</u> file.'
        ))
        inner_layout.addWidget(html_label(
            '<b>Type</b>: The type of object extracted from the <u>dxf</u> file, object types can be '
            "one of 'Insert', 'Line', or '<u>LWpolyline</u>'."
        ))
        inner_layout.addWidget(html_label(
            '<b>Category</b>: A further classification of the object, grouping it by its functional '
            'role or purpose within the drawing.'
        ))
        inner_layout.addWidget(html_label(
            f'{warning}Warning: If Object is a Line type and the Line Category is not present in the Line category '
            f'database, please add Line Category in the Line Category tab {warning}.'
        ))
        inner_layout.addWidget(html_label(
            '<b>On Channel Outline</b>: Whether an object only lies on the Channel Outline.'
        ))

        inner_layout.addSpacing(10)
        inner_layout.addWidget(heading('The Line Category Database'))

        inner_layout.addWidget(html_label(
            'The purpose of the Line category database is to ensure all lines have the correct '
            'connections at each end. The Line category database has 4 Columns including Category, '
            'Allowed Connections, Double Connection, On Channel Outline:'
        ))
        inner_layout.addWidget(html_label(
            '<b>Category</b>: Same as in the object database, classifies the functional role or '
            'purpose of a line within the drawing.'
        ))
        inner_layout.addWidget(html_label(
            '<b>Allowed Connections</b>: These are the connections a Line type is allowed to have.'
        ))
        inner_layout.addWidget(html_label(
            '<b>Double Connection</b>: Whether a line should have a connection at each end.'
        ))
        inner_layout.addWidget(html_label(
            '<b>On Channel Outline</b>: Whether a line type should only lie on the channel outline.'
        ))

        inner_layout.addStretch()
        scroll.setWidget(inner)
        desc_layout.addWidget(scroll)
        tabs.addTab(desc_widget, 'Description')

        # ── Tab 2: Object Database ──────────────────────────────────────
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        objects_table = LabeledTableWidget('Object Database', ['Name', 'Type', 'Category', 'On Channel Outline'], BaseTable.BLUE)
        objects_table.populate(get_catalogue())
        tab2_layout.addLayout(objects_table)
        tabs.addTab(tab2, 'Object Database')

        # ── Tab 3: Line Category Database ───────────────────────────────
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        category_table = LabeledTableWidget('Line Category Database', ['Category', 'Allowed Connections', 'Double Connection', 'On Channel'], BaseTable.BLUE)
        category_table.populate(get_category_catalogue())
        tab3_layout.addLayout(category_table)
        tabs.addTab(tab3, 'Line Category Database')

        layout.addWidget(tabs)

    def collectResult(self):
        return None    

