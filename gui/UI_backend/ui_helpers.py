from PyQt5.QtWidgets import QVBoxLayout, QLabel, QPushButton, QHBoxLayout

def create_buttons(Text, command, box: QHBoxLayout, Colour): 
        Button = QPushButton()
        Button.setText(Text)
        Button.clicked.connect(command)
        box.addWidget(Button)
        Button.setStyleSheet(Colour)
        Button.setMaximumWidth(221)
        Button.setMinimumWidth(220)
        Button.setMinimumHeight(25)
        return Button 
    
def create_vbox(table, labelname):
        vbox = QVBoxLayout()
        vbox.addWidget(QLabel(labelname))
        vbox.addWidget(table, 1)
        return vbox 