

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel

class FileInput(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        self.label = QLabel("Selected files: 0")
        self.btn_select = QPushButton("Add Files")
        self.btn_select.clicked.connect(self.parent.on_select_files)
        
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.btn_select)

