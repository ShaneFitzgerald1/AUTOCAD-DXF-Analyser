from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QListWidget, QPushButton, QTabWidget, QWidget, QScrollArea, QLineEdit, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from gui.BaseDialog import BaseDialog
from database.db_models import Session, ObjectID, CategoryLineRule
from database.db_objects import get_category_catalogue, get_catalogue
from gui.table_widget import LabeledTableWidget
from gui.base_table import BaseTable
from gui.add_object_dialog import database_description, AddObjectDialog, Combox


class EditDialog(AddObjectDialog): 
    warning = "\u26A0"
    def __init__(self, mode='category', parent=None):
        self._mode = mode
        super().__init__(rejected_names=[], parent=parent)
        if self._mode == 'object':
            self.setWindowTitle('Edit Object Database')
        else:
            self.setWindowTitle('Edit Line Category Database')

    def buildContent(self, layout):
        if self._mode == 'object':
            self.create_object_popup(layout)
        else:
            self.create_category_popup(layout)

    def create_object_popup(self, layout: QVBoxLayout):
        tabs = QTabWidget()

        #-------------- TAB 1 ADD OBJECT ---------------
        # 
        #  
        addobject_widget = QWidget()
        addobject_layout = QVBoxLayout(addobject_widget)
        addobject_layout.setSpacing(10)

        explain_label = QLabel(
            f'Add new Object to the Database below.\n\n'
            f'{self.warning} If Object type is a Line type and the category is not present in the Category combox, add it in the Line Category database first.\n\n'
            'Please read Database description to view instructiosn and both Databases.'
        )
        explain_label.setFont(QFont('Inter', 10))
        explain_label.setWordWrap(True)
        addobject_layout.addWidget(explain_label)

        btn1 = QPushButton('Database Description')
        btn1.clicked.connect(lambda: database_description(parent=self).exec_())
        addobject_layout.addWidget(btn1)

        name_row = QHBoxLayout()
        name_lbl = QLabel('New Object Name:')
        name_lbl.setFont(QFont('Inter', 10))
        name_lbl.setFixedWidth(200)
        self.new_object_name = QLineEdit()
        self.new_object_name.setPlaceholderText('e.g. NLB CORNER 50')
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.new_object_name)
        addobject_layout.addLayout(name_row)

        self.type_combo     = Combox._add_combo(addobject_layout, 'Type:',               self.TYPE_OPTIONS)
        self.category_combo = Combox._add_combo(addobject_layout, 'Category:',           self.ALL_CATEGORIES)
        self.channel_combo  = Combox._add_combo(addobject_layout, 'On Channel Outline:', self.CHANNEL_OPTIONS)

        add_obj_btn = QPushButton('Add to Database')
        add_obj_btn.clicked.connect(self._add_object)
        addobject_layout.addWidget(add_obj_btn)

        self.feedback_label_oadd = QLabel('')
        self.feedback_label_oadd.setAlignment(Qt.AlignCenter)
        addobject_layout.addWidget(self.feedback_label_oadd)

        tabs.addTab(addobject_widget, 'Add Object')


        #------------ TAB 2 EDIT OBJECT --------------


        editobject_widget = QWidget()
        editobject_layout = QVBoxLayout(editobject_widget)
        editobject_layout.setSpacing(10)

        explain_label2 = QLabel(
            f'Edit or Remove Object from the Database below.\n\n'
            f'{self.warning} Any change made to the database is permanent, please ensure values are correct.\n\n'
            'Please read Database description to view instructions and both Databases.'
        )

        explain_label2.setFont(QFont('Inter', 10))
        explain_label2.setWordWrap(True)
        editobject_layout.addWidget(explain_label2)

        btn2 = QPushButton('Database Description')
        btn2.clicked.connect(lambda: database_description(parent=self).exec_())
        editobject_layout.addWidget(btn2)

        self.select_object = Combox._add_combo(editobject_layout, 'Object Name:', self.NAME_OPTIONS)

        name, type_options, all_categories, channel_options = self.create_newbox()

        self.type_combo2     = Combox._add_combo(editobject_layout, 'Type:',               type_options)
        self.category_combo2 = Combox._add_combo(editobject_layout, 'Category:',           all_categories)
        self.channel_combo2  = Combox._add_combo(editobject_layout, 'On Channel Outline:', channel_options)

        self.select_object.currentIndexChanged.connect(self.update_combos)

        edit_obj_btn = QPushButton('Make Changes')
        edit_obj_btn.clicked.connect(self.edit_object)
        editobject_layout.addWidget(edit_obj_btn)

        delete_obj_btn = QPushButton('Delete Object')
        delete_obj_btn.clicked.connect(self.delete_object)
        editobject_layout.addWidget(delete_obj_btn)

        self.feedback_label_oedit = QLabel('')
        self.feedback_label_oedit.setAlignment(Qt.AlignCenter)
        editobject_layout.addWidget(self.feedback_label_oedit)

        tabs.addTab(editobject_widget, 'Edit Object')

        layout.addWidget(tabs)


    def create_category_popup(self, layout: QVBoxLayout): 

        tabs = QTabWidget()

        #-------------------TAB 1 ADD CATEGORY LINE----------------------
        

        addcategory_widget = QWidget()
        addcategory_layout = QVBoxLayout(addcategory_widget)
        addcategory_layout.setSpacing(8)

        warning = "\u26A0"

        explain_label = QLabel(
            f'Add new Category to the Database below.\n\n'
            f'{warning} If Category is not available for object insert, add here.\n\n'
            'To view Databases, see Database Description. \n\n'
            'Please read Database Description to view instructions and both Databases.'
        )
        explain_label.setFont(QFont('Inter', 10))
        addcategory_layout.addWidget(explain_label)

        btn1 = QPushButton('Database Description')
        btn1.clicked.connect(lambda: database_description(parent=self).exec_())
        addcategory_layout.addWidget(btn1)


        # Category name input
        name_row = QHBoxLayout()
        name_lbl = QLabel('New Category Name:')
        name_lbl.setFont(QFont('Inter', 10))
        name_lbl.setFixedWidth(200)
        self.new_category_name = QLineEdit()
        self.new_category_name.setPlaceholderText('e.g. NEW LINE TYPE')
        name_row.addWidget(name_lbl)
        name_row.addWidget(self.new_category_name)
        addcategory_layout.addLayout(name_row)

        # Quantity of allowed connections
        quantity_options = [str(i) for i in range(1, len(self.CATEGORY_OPTIONS) + 1)]
        self.quantity_combo = Combox._add_combo(addcategory_layout, 'Number of Allowed Connections:', quantity_options)
        self.quantity_combo.currentIndexChanged.connect(
            lambda: setattr(self, '_connection_combos', self._rebuild_combos(self.connections_container, self.quantity_combo, 'Allowed Connection')))

        # Container for the dynamic connection combos
        self.connections_container = QVBoxLayout()
        addcategory_layout.addLayout(self.connections_container)

        # Double connection and on channel combos
        self.double_connection_combo = Combox._add_combo(addcategory_layout, 'Double Connection:', self.CHANNEL_OPTIONS)
        self.on_channel_combo        = Combox._add_combo(addcategory_layout, 'On Channel Outline:', self.CHANNEL_OPTIONS)

        self.cat_feedback_label_add = QLabel('')
        self.cat_feedback_label_add.setAlignment(Qt.AlignCenter)
        addcategory_layout.addWidget(self.cat_feedback_label_add)

        add_cat_btn = QPushButton('Add Line Category')
        add_cat_btn.clicked.connect(self._add_line_category)
        addcategory_layout.addWidget(add_cat_btn)

        tabs.addTab(addcategory_widget, 'Add Line Category')

        # Build initial connection combos for default quantity (1)
        self._connection_combos = self._rebuild_combos(self.connections_container, self.quantity_combo, 'Allowed Connection')


        #------------- TAB 2, EDIT OR REMOVE CATEGORY LINE -------------- 


        editcategory_widget = QWidget()
        editcategory_layout = QVBoxLayout(editcategory_widget)
        editcategory_layout.setSpacing(10)

        explain_label2 = QLabel(
            f'Edit or Remove Object from the Database below.\n\n'
            f'{warning} Any change made to the database is permanent, please ensure values are correct.\n\n'
            'To view Databases, see Database Description. \n\n'
            'Please read Database description to view instructions and both Databases.'
        )

        explain_label.setFont(QFont('Inter', 10))
        explain_label.setWordWrap(True)
        editcategory_layout.addWidget(explain_label2)

        btn2 = QPushButton('Database Description')
        btn2.clicked.connect(lambda: database_description(parent=self).exec_())
        editcategory_layout.addWidget(btn2)

        self.select_category = Combox._add_combo(editcategory_layout, 'Category Name:', self.CATEGORY_DB_OPTIONS)
        self.select_category.currentIndexChanged.connect(self._update_quantity_remove_options)

        self.allowed_cons_remove = 0
        name = self.select_category.currentText().strip()
        for category, allowed_connections, _, _ in get_category_catalogue():
            if name == category:
                self.allowed_cons_remove_s = [c for c in allowed_connections.split(',') if c.strip()]
                self.allowed_cons_remove = len([c for c in allowed_connections.split(',') if c.strip()])
                break

        self.connect_to_add = list(set(self.ALL_CATEGORIES) ^ set(self.allowed_cons_remove_s))
        edit_connections = QHBoxLayout()
        # Left side — remove connections
        remove_vbox = QVBoxLayout()
        quantity_options_add = [str(i) for i in range(0, len(self.connect_to_add) + 1)]
        quantity_options_rem = [str(i) for i in range(0, self.allowed_cons_remove + 1)]
        self.quantity_remove = Combox._add_combo(remove_vbox, 'Connections to Remove:', quantity_options_rem)
        self.quantity_remove.currentIndexChanged.connect(
            lambda: setattr(self, '_remove_connection_combos', self._rebuild_remove_combos(self.remove_connections_container, self.quantity_remove, 'Remove Connection')))
        self.remove_connections_container = QVBoxLayout()
        remove_vbox.addLayout(self.remove_connections_container)

        # Right side — add connections
        add_vbox = QVBoxLayout()
        self.quantity_add = Combox._add_combo(add_vbox, 'Connections to Add:', quantity_options_add)
        self.quantity_add.currentIndexChanged.connect(
            lambda: setattr(self, '_add_connection_combos', self._rebuild_combos(self.add_connections_container, self.quantity_add, 'Add Connection', filter_existing=True)))
        self.add_connections_container = QVBoxLayout()
        add_vbox.addLayout(self.add_connections_container)

        edit_connections.addLayout(remove_vbox)
        edit_connections.addLayout(add_vbox)
        editcategory_layout.addLayout(edit_connections)

        self._remove_connection_combos = self._rebuild_remove_combos(self.remove_connections_container, self.quantity_remove, 'Remove Connection')
        self._add_connection_combos    = self._rebuild_combos(self.add_connections_container,    self.quantity_add,    'Add Connection', filter_existing=True)


        double_connections, channel_options = self.create_newcat_box()
        self.double_connection_combo = Combox._add_combo(editcategory_layout, 'Double Connection:',  double_connections)
        self.channel_combo  = Combox._add_combo(editcategory_layout, 'On Channel Outline:', channel_options)

        self.select_category.currentIndexChanged.connect(self.update_cat_box)

        edit_obj_btn = QPushButton('Make Changes')
        edit_obj_btn.clicked.connect(self._edit_line_category)
        editcategory_layout.addWidget(edit_obj_btn)

        delete_obj_btn = QPushButton('Delete Line Category')
        delete_obj_btn.clicked.connect(self.delete_category)
        editcategory_layout.addWidget(delete_obj_btn)

        self.cat_feedback_label_edit = QLabel('')
        self.cat_feedback_label_edit.setAlignment(Qt.AlignCenter)
        editcategory_layout.addWidget(self.cat_feedback_label_edit)

        tabs.addTab(editcategory_widget, 'Edit Line Category')

        layout.addWidget(tabs)




    #---------OBJECT CATEGORY POP UP ----------
    #----- ANYTHING BACKEND THAT BUILDS THE OBJECT POPUP --------

    def _add_object(self):
        """This function adds new objects to the database, The function takes values from 
        the combox and inserts them into the database """
      
        name_input = self.new_object_name.text().strip()
        name = name_input.upper()
        if not name:
            self.feedback_label_oadd.setStyleSheet('color: red;')
            self.feedback_label_oadd.setText('Please enter a category name.')
            return

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
            self.feedback_label_oadd.setStyleSheet('color: green;')
            self.feedback_label_oadd.setText(f'"{name}" added successfully.')
            #important to update boxes to refelct the updated database 
            self.select_object.addItem(name)
            # self.name_list.takeItem(self.name_list.currentRow())
        except Exception as e:
            session.rollback()
            self.feedback_label_oadd.setStyleSheet('color: red;')
            self.feedback_label_oadd.setText(f'Error: {e}')
        finally:
            session.close()

    def edit_object(self):
        """If a user wishes to edit objects within the database, User selects the object to be editied
        the new values are set and added to the database in this function """

        name = self.select_object.currentText()
        if not self._confirm('Confirm Edit', f'Are you sure you want to edit {name} in the Object Database?', self):
            return
        
        name     = self.select_object.currentText()
        type_    = self.type_combo2.currentText()
        category = self.category_combo2.currentText()
        channel  = self.channel_combo2.currentText()

        session = Session()
        try:
            row = session.query(ObjectID).filter_by(name=name).first()
            if not row:
                self.feedback_label_oedit.setStyleSheet('color: red;')
                self.feedback_label_oedit.setText(f'"{name}" not found in database.')
                return

            row.type              = type_
            row.category          = category
            row.on_channel_outline = channel
            session.commit()
            self.feedback_label_oedit.setStyleSheet('color: green;')
            self.feedback_label_oedit.setText(f'"{name}" updated successfully.')
        except Exception as e:
            session.rollback()
            self.feedback_label_oedit.setStyleSheet('color: red;')
            self.feedback_label_oedit.setText(f'Error: {e}')
        finally:
            session.close()

    def delete_object(self):

        name = self.select_object.currentText()
        if not self._confirm('Confirm Delete', f'Are you sure you want to delete {name} from the Object Database?', self):
            return
        
        name = self.select_object.currentText()

        session = Session()
        """Function to Delete objects from the database"""
        try:
            row = session.query(ObjectID).filter_by(name=name).first() #setting the row equal to the selected name to delete
            if not row:
                self.feedback_label_oedit.setStyleSheet('color: red;')
                self.feedback_label_oedit.setText(f'"{name}" not found in database.')
                return

            session.delete(row)
            session.commit()
            self.feedback_label_oedit.setStyleSheet('color: green;')
            self.feedback_label_oedit.setText(f'"{name}" deleted successfully.')
            # Remove from the combo so user can't try to delete it again
            idx = self.select_object.findText(name)
            self.select_object.removeItem(idx)
        except Exception as e:
            session.rollback()
            self.feedback_label_oedit.setStyleSheet('color: red;')
            self.feedback_label_oedit.setText(f'Error: {e}')
        finally:
            session.close()
        

        

    #------LINE CATEGORY POP UP ---------
    #---Anything backend that builds the line category popup -----

    def _rebuild_combos(self, container, quantity_combo, label, filter_existing=False):
        """Builds combos populated with ALL_CATEGORIES — used for adding connections.
        filter_existing=True is used in Tab 2 (edit) so the user can only add categories
        not already connected. filter_existing=False (default) shows all categories."""
        while container.count():
            item = container.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

        if filter_existing and hasattr(self, 'select_category'):
            name = self.select_category.currentText().strip()
            existing = []
            for cat in get_category_catalogue():
                category, allowed_connections, _, _ = cat
                if category == name:
                    existing = [c.strip() for c in allowed_connections.split(',') if c.strip()]
                    add_list = list(set(existing) ^ set(self.ALL_CATEGORIES))
                    break
            options = add_list
        else:
            options = self.ALL_CATEGORIES

        combos = []
        count = int(quantity_combo.currentText())
        for i in range(count):
            combo = Combox._add_combo(container, f'{label} {i + 1}:', options)
            combos.append(combo)
        return combos

    def _update_quantity_remove_options(self):
        """When the selected category changes, recalculate its existing connections
        and update both quantity combos — remove capped to what it has, add capped to the remainder."""
        name = self.select_category.currentText().strip()
        self.allowed_cons_remove_s = []
        for category, allowed_connections, _, _ in get_category_catalogue():
            if name == category:
                self.allowed_cons_remove_s = [c.strip() for c in allowed_connections.split(',') if c.strip()]
                break
        self.allowed_cons_remove = len(self.allowed_cons_remove_s)
        self.connect_to_add = list(set(self.ALL_CATEGORIES) - set(self.allowed_cons_remove_s))

        self.quantity_remove.blockSignals(True)
        self.quantity_remove.clear()
        for i in range(0, self.allowed_cons_remove + 1):
            self.quantity_remove.addItem(str(i))
        self.quantity_remove.blockSignals(False)

        self.quantity_add.blockSignals(True)
        self.quantity_add.clear()
        for i in range(0, len(self.connect_to_add) + 1):
            self.quantity_add.addItem(str(i))
        self.quantity_add.blockSignals(False)

        self._remove_connection_combos = self._rebuild_remove_combos(
            self.remove_connections_container, self.quantity_remove, 'Remove Connection')
        self._add_connection_combos = self._rebuild_combos(
            self.add_connections_container, self.quantity_add, 'Add Connection', filter_existing=True)

    def _rebuild_remove_combos(self, container, quantity_combo, label):
        """Builds combos populated only with connections the selected category already has — used for removing"""
        while container.count():
            item = container.takeAt(0)
            if item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
            elif item.widget():
                item.widget().deleteLater()

        name = self.select_category.currentText().strip()
        existing = []
        for cat in get_category_catalogue():
            category, allowed_connections, _, _ = cat
            if category == name:
                existing = [c.strip() for c in allowed_connections.split(',') if c.strip()]
                self.allowed_cons_remove = len(allowed_connections)
                break 

        combos = []
        count = int(quantity_combo.currentText())
        for i in range(count):
            combo = Combox._add_combo(container, f'{label} {i + 1}:', existing if existing else self.ALL_CATEGORIES)
            combos.append(combo)
        return combos
    

    def _add_line_category(self):
        """This function adds line category data, Function takes the inputs from tab1 of the line category popup 
        and ads it to the database 
        Function takes the current values form the comboxes and adds them to the database
        """
        from database.db_models import CategoryLineRule
        name_input = self.new_category_name.text().strip()
        name = name_input.upper()
        if not name:
            self.cat_feedback_label_add.setStyleSheet('color: red;')
            self.cat_feedback_label_add.setText('Please enter a category name.')
            return

        # ','.join(c.currentText() for c in self._connection_combos) 
        #current values in the comboxes 
        # [c.currentText() for c in self._connection_combos]
     
        allowed = ','.join(c.currentText() for c in self._connection_combos)    #joins values into list, if there are multiple
        double  = self.double_connection_combo.currentText()
        on_chan = self.on_channel_combo.currentText()

        session = Session()  #making a connection with the database 
        try:
            exists = session.query(CategoryLineRule).filter_by(category=name).first()
            if exists:
                self.cat_feedback_label_add.setStyleSheet('color: orange;')
                self.cat_feedback_label_add.setText(f'"{name}" is already in the category database.')
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
            self.CATEGORY_DB_OPTIONS.append(name)
            self.select_category.addItem(name)
            self._rebuild_connection_combos()


            self.cat_feedback_label_add.setStyleSheet('color: green;')
            self.cat_feedback_label_add.setText(f'"{name}" added successfully.')
            self.new_category_name.clear()
        except Exception as e:
            session.rollback()
            self.cat_feedback_label_add.setStyleSheet('color: red;')
            self.cat_feedback_label_add.setText(f'Error: {e}')
        finally:
            session.close()

    def _edit_line_category(self):
        """Function that edits values in the database, based on input values of tab 2"""
        from database.db_models import CategoryLineRule

        name = self.select_category.currentText()
        if not self._confirm('Confirm Edit', f'Are you sure you want to edit {name} in the Line Category Database?', self):
            return

        name = self.select_category.currentText().strip()
        if not name:
            self.cat_feedback_label_edit.setStyleSheet('color: red;')
            self.cat_feedback_label_edit.setText('No category selected.')
            return

        to_add    = [c.currentText() for c in self._add_connection_combos]
        to_remove = [c.currentText() for c in self._remove_connection_combos]

        # print(f'Lines to add {to_add}')
        # print(f'Lines to remove {to_remove}')

        session = Session()
        try:
            row = session.query(CategoryLineRule).filter_by(category=name).first()
            if not row:
                self.cat_feedback_label_edit.setStyleSheet('color: red;')
                self.cat_feedback_label_edit.setText(f'"{name}" not found in database.')
                return

            # Parse existing connections, apply removes then adds
            existing = [c.strip() for c in row.allowed_connections.split(',') if c.strip()]
            existing = [c for c in existing if c not in to_remove]
            for c in to_add:
                if c not in existing:
                    existing.append(c)

            row.allowed_connections = ','.join(existing)
            row.double_connection   = self.double_connection_combo.currentText()
            row.on_channel          = self.channel_combo.currentText()

            session.commit()
            self.cat_feedback_label_edit.setStyleSheet('color: green;')
            self.cat_feedback_label_edit.setText(f'"{name}" updated successfully.')
        except Exception as e:
            session.rollback()
            self.cat_feedback_label_edit.setStyleSheet('color: red;')
            self.cat_feedback_label_edit.setText(f'Error: {e}')
        finally:
            session.close()


    def delete_category(self):
        name = self.select_category.currentText()
        if not self._confirm('Confirm Delete', f'Are you sure you want to delete {name} from the Line Category Database?', self):
            return

        session = Session()
        """Function to Delete objects from the database"""
        try:
            row = session.query(CategoryLineRule).filter_by(category=name).first() #setting the row equal to the selected name to delete
            if not row:
                self.cat_feedback_label_edit.setStyleSheet('color: red;')
                self.cat_feedback_label_edit.setText(f'"{name}" not found in database.')
                return

            session.delete(row)
            session.commit()
            self.cat_feedback_label_edit.setStyleSheet('color: green;')
            self.cat_feedback_label_edit.setText(f'"{name}" deleted successfully.')
            # Remove from the combo so user can't try to delete it again
            idx = self.select_category.findText(name)
            self.select_category.removeItem(idx)
        except Exception as e:
            session.rollback()
            self.cat_feedback_label_edit.setStyleSheet('color: red;')
            self.cat_feedback_label_edit.setText(f'Error: {e}')
        finally:
            session.close()     

    from PyQt5.QtWidgets import QMessageBox

    @staticmethod
    def _confirm(title: str, message: str, parent=None) -> bool:
        """Function to confrim a user wants to edit or remove something from database """
        reply = QMessageBox.question(
            parent, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    def define_object(self, object_name):
        for name, type, category, on_channel in get_catalogue():
            if object_name == name:
                return name, type, category, on_channel
        return None, None, None, None

    def create_newbox(self):
        object_name = self.select_object.currentText()
        name, type, category, on_channel = self.define_object(object_name)

        type_options = [t for t in self.TYPE_OPTIONS if t != type]
        type_options.insert(0, type)

        all_categories = [c for c in self.ALL_CATEGORIES if c != category]
        all_categories.insert(0, category)

        channel_options = [ch for ch in self.CHANNEL_OPTIONS if ch != on_channel]
        channel_options.insert(0, on_channel)

        return name, type_options, all_categories, channel_options

    def update_combos(self):
        _, type_options, all_categories, channel_options = self.create_newbox()

        self.type_combo2.blockSignals(True)
        self.type_combo2.clear()
        self.type_combo2.addItems(type_options)
        self.type_combo2.blockSignals(False)

        self.category_combo2.blockSignals(True)
        self.category_combo2.clear()
        self.category_combo2.addItems(all_categories)
        self.category_combo2.blockSignals(False)

        self.channel_combo2.blockSignals(True)
        self.channel_combo2.clear()
        self.channel_combo2.addItems(channel_options)
        self.channel_combo2.blockSignals(False)


    def get_category(self, category_name): 
        """Function for extracting category values to populate comboxes corretly in categories"""
        line_categories = get_category_catalogue() 
        for line_category  in line_categories: 
            category, allowed_connections, double_connection, on_channel = line_category 
            if category_name == category: 
                return double_connection, on_channel    
        return None, None     
    
    def create_newcat_box(self): 
        category_name = self.select_category.currentText()

        double_connection, on_channel = self.get_category(category_name) 

        double_connections = [c for c in self.CHANNEL_OPTIONS if c != double_connection]
        double_connections.insert(0, double_connection)

        channel_options = [ch for ch in self.CHANNEL_OPTIONS if ch != on_channel]
        channel_options.insert(0, on_channel)

        return double_connections, channel_options

    def update_cat_box(self): 
        double_connections, channel_options = self.create_newcat_box()

        self.double_connection_combo.blockSignals(True)
        self.double_connection_combo.clear()
        self.double_connection_combo.addItems(double_connections)
        self.double_connection_combo.blockSignals(False)

        self.channel_combo.blockSignals(True)
        self.channel_combo.clear()
        self.channel_combo.addItems(channel_options)
        self.channel_combo.blockSignals(False)









    



         

    


           

            












